{#
  One row per player per fixture: the provider's player statistics, cleaned once, in our own
  words. The rules are the cleaning_rules doc block in models/docs/cleaning_rules.md; the steps
  below apply them in this order:

  1. the blank rule;
  2. accurate passes as a count;
  3. goals and penalty goals, the results;
  4. match stats checked against the results, then against their whole.

  Every change made by steps 3 and 4 is listed on its row in stat_corrections.
#}

with src as (
    select
        league_code,
        fixture_id,
        team_id,
        player_id,
        minutes_played,
        shirt_number,
        position_code,
        is_captain,
        is_substitute,
        offsides,
        shots_total,
        shots_on,
        goals_total,
        goals_against,
        goals_assists,
        saves,
        passes_total,
        passes_key,
        passes_accuracy_percent,
        tackles_total,
        tackles_blocks,
        tackles_interceptions,
        duels_total,
        duels_won,
        dribbles_attempts,
        dribbles_success,
        dribbles_past,
        fouls_drawn,
        fouls_committed,
        cards_yellow,
        cards_red,
        penalty_won,
        penalty_committed,
        penalty_scored,
        penalty_missed,
        penalty_saved,
        raw_ingested_at
    from {{ ref('stg_apif__fixture_players') }}
    where
        fixture_id is not null
        and team_id is not null
        and player_id is not null
        -- player_id = 0 is the API placeholder for an unknown player (no real id);
        -- it is not a real player and produces phantom cross-team duplicate legs.
        and player_id != 0
),

-- Fixture participants (home/away team ids), used to evaluate the reattribute_if_cohabiting
-- override condition below. base_apif__fixtures_next grain is one row per fixture_id. Only
-- fixtures whose two participants are BOTH known are kept, so the IN / NOT IN participant checks
-- in the reattribute join never hit the NOT IN (value, NULL) -> UNKNOWN trap (a fixture with a
-- missing participant id is a separate defect; the override conservatively does not fire there).
fixture_participants as (
    select
        fixture_id,
        cast(home_team_id as int64) as home_team_id,
        cast(away_team_id as int64) as away_team_id
    from {{ ref('base_apif__fixtures_next') }}
    where
        home_team_id is not null
        and away_team_id is not null
),

-- Hand-curated corrections for known provider team-id defects, from
-- seeds/fixture_team_id_overrides.csv. `alias` = unconditional duplicate-id replacement (one club
-- under two provider ids); `reattribute_if_cohabiting` = replace only when the correct id is a
-- fixture participant and the wrong id is not (a mis-attribution between two DISTINCT clubs, so a
-- club's own legitimate lineups are never touched). Same seed and same two modes the events model
-- has used since #526; it was simply never wired to this feed, which is how one stub team block --
-- id 22722, name null -- put a lineup under a club that does not exist and stopped the nightly.
overrides as (
    select
        cast(wrong_team_api_id as int64) as wrong_team_api_id,
        cast(correct_team_api_id as int64) as correct_team_api_id,
        mode
    from {{ ref('fixture_team_id_overrides') }}
),

-- Corrected BEFORE the qualify below, not after, because both of its window functions partition on
-- team_id: the dedup key, which the model's uniqueness test covers, and the cross-team collision
-- guard. The guard now sees corrected ids, which is the intended direction -- a player appearing
-- under both a wrong id and its correct one was never two players, and dropping that leg as
-- unattributable would discard a real appearance.
corrected as (
    select
        src.* except (team_id),
        coalesce(
            alias_override.correct_team_api_id,
            reattribute_override.correct_team_api_id,
            src.team_id
        ) as team_id,
        (
            select countif(stat is not null)
            from unnest([
                src.minutes_played, src.offsides, src.shots_total, src.shots_on, src.goals_total,
                src.goals_against, src.goals_assists, src.saves, src.passes_total, src.passes_key,
                src.passes_accuracy_percent, src.tackles_total, src.tackles_blocks, src.tackles_interceptions,
                src.duels_total, src.duels_won, src.dribbles_attempts, src.dribbles_success, src.dribbles_past,
                src.fouls_drawn, src.fouls_committed, src.cards_yellow, src.cards_red, src.penalty_won,
                src.penalty_committed, src.penalty_scored, src.penalty_missed, src.penalty_saved
            ]) as stat
        ) as delivered_values
    from src
    left join overrides as alias_override
        on
            src.team_id = alias_override.wrong_team_api_id
            and alias_override.mode = 'alias'
    left join fixture_participants
        on src.fixture_id = fixture_participants.fixture_id
    left join overrides as reattribute_override
        on
            src.team_id = reattribute_override.wrong_team_api_id
            and reattribute_override.mode = 'reattribute_if_cohabiting'
            and reattribute_override.correct_team_api_id in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
            and reattribute_override.wrong_team_api_id not in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
),

-- The provider's values under our names, one row per player per fixture: the latest fetch. A player
-- the provider lists twice in one fetch keeps the row with more values, and the rows' own values
-- break a tie, so every build keeps the same row.
delivered as (
    select
        league_code,
        fixture_id,
        team_id,
        player_id,
        shirt_number,
        position_code,
        is_captain,
        is_substitute,
        raw_ingested_at,
        minutes_played as minutes,
        offsides,
        shots_total as shots,
        shots_on as shots_on_target,
        goals_total as goals,
        goals_against,
        goals_assists as assists,
        saves,
        passes_total as passes,
        passes_key,
        passes_accuracy_percent as passes_accurate,
        tackles_total as tackles,
        tackles_blocks as blocks,
        tackles_interceptions as interceptions,
        duels_total as duels,
        duels_won,
        dribbles_attempts as dribbles,
        dribbles_success,
        dribbles_past as dribbles_against,
        fouls_committed as fouls,
        fouls_drawn as fouls_against,
        cards_yellow,
        cards_red,
        penalty_won as penalties_won,
        penalty_committed as penalties_committed,
        penalty_scored as penalties_scored,
        penalty_missed as penalties_missed,
        penalty_saved as penalties_saved
    from corrected
    qualify
        row_number() over (
            partition by league_code, fixture_id, team_id, player_id
            order by raw_ingested_at desc, delivered_values desc, to_json_string(corrected) asc
        ) = 1
        -- Drop cross-team id-collisions: the provider sometimes reuses one player_id for two
        -- different players in a fixture (one per team, e.g. AFCCL 2016 id 44061), so the id is
        -- unreliable and both legs are unattributable. Extends the player_id = 0 phantom-leg
        -- cleanup above to real-but-collided ids; keeps the (fixture, player) grain unique
        -- downstream (int_legs__player_match / mart_player_match_log).
        and min(team_id) over (partition by league_code, fixture_id, player_id)
        = max(team_id) over (partition by league_code, fixture_id, player_id)
),

fixtures as (
    select
        fixture_id,
        cast(home_team_id as int64) as home_team_id,
        cast(away_team_id as int64) as away_team_id,
        goals_home,
        goals_away
    from {{ ref('base_apif__fixtures_next') }}
),

events as (
    select
        fixture_id,
        team_id,
        player_id,
        event_type,
        event_detail,
        assist_player_name,
        event_comments is distinct from 'Penalty Shootout' as is_in_play
    from {{ ref('base_apif__fixture_events') }}
),

-- The events prove a zero only where they cover more than the goals: a match with at least one
-- substitution or card, which every played match has.
fixtures_with_events as (
    select fixture_id
    from events
    where event_type in ('subst', 'Card')
    group by fixture_id
),

team_events as (
    select
        fixture_id,
        team_id,
        countif(is_in_play and event_type = 'Goal' and event_detail in ('Normal Goal', 'Penalty'))
            as goal_events,
        countif(
            is_in_play and event_type = 'Goal' and event_detail in ('Normal Goal', 'Penalty')
            and player_id is null
        ) as goal_events_without_scorer,
        countif(is_in_play and event_type = 'Goal' and event_detail = 'Normal Goal') as open_play_goal_events,
        countif(
            is_in_play and event_type = 'Goal' and event_detail = 'Normal Goal'
            and assist_player_name is not null
        ) as assisted_goal_events,
        countif(is_in_play and event_type = 'Goal' and event_detail = 'Own Goal') as own_goals,
        countif(is_in_play and event_type = 'Goal' and event_detail = 'Penalty') as penalty_goal_events,
        countif(is_in_play and event_type = 'Goal' and event_detail in ('Penalty', 'Missed Penalty'))
            as penalty_events,
        countif(is_in_play and event_type = 'Goal' and event_detail = 'Missed Penalty') as missed_penalty_events,
        countif(event_type = 'Card') as card_events
    from events
    group by fixture_id, team_id
),

match_assist_names as (
    select
        fixture_id,
        countif(is_in_play and event_type = 'Goal' and assist_player_name is not null) as assisted_goal_events
    from events
    group by fixture_id
),

player_events as (
    select
        fixture_id,
        team_id,
        player_id,
        countif(is_in_play and event_type = 'Goal' and event_detail in ('Normal Goal', 'Penalty')) as goals,
        countif(is_in_play and event_type = 'Goal' and event_detail = 'Penalty') as goals_penalty
    from events
    where player_id is not null
    group by fixture_id, team_id, player_id
),

-- The saves check judges the opponent's shots as the team cleaning judged them, before its own
-- corrections: a figure the cleaning had to correct was never vouched for.
team_lines as (
    select
        fixture_id,
        team_id,
        shots,
        shots_on_target,
        saves,
        offsides,
        coalesce(
            (
                select coalesce(c.provider_value, 0)
                from unnest(stat_corrections) as c
                where c.stat = 'shots'
            ),
            shots
        ) as shots_before_correction,
        coalesce(
            (
                select coalesce(c.provider_value, 0)
                from unnest(stat_corrections) as c
                where c.stat = 'shots_on_target'
            ),
            shots_on_target
        ) as shots_on_target_before_correction
    from {{ ref('base_apif__fixture_statistics') }}
),

in_context as (
    select
        d.*,
        tl.shots as team_shots,
        tl.shots_on_target as team_shots_on_target,
        tl.saves as team_saves,
        tl.offsides as team_offsides,
        ol.shots_before_correction as opponent_shots,
        ol.shots_on_target_before_correction as opponent_shots_on_target,
        pe.goals as event_goals,
        pe.goals_penalty as event_goals_penalty,
        if(d.team_id = f.home_team_id, f.goals_home, f.goals_away) as team_goals_for,
        if(d.team_id = f.home_team_id, f.goals_away, f.goals_home) as team_goals_conceded,
        fe.fixture_id is not null as has_events,
        coalesce(te.goal_events, 0) as team_goal_events,
        coalesce(te.goal_events_without_scorer, 0) as team_goal_events_without_scorer,
        coalesce(te.open_play_goal_events, 0) as team_open_play_goal_events,
        coalesce(te.assisted_goal_events, 0) as team_assisted_goal_events,
        coalesce(te.own_goals, 0) as team_own_goals,
        coalesce(te.penalty_goal_events, 0) as team_penalty_goal_events,
        coalesce(te.penalty_events, 0) as team_penalty_events,
        coalesce(te.card_events, 0) as team_card_events,
        coalesce(ma.assisted_goal_events, 0) as match_assisted_goal_events,
        coalesce(oe.own_goals, 0) as opponent_own_goals,
        coalesce(oe.penalty_goal_events, 0) as opponent_penalty_goal_events,
        coalesce(oe.penalty_events, 0) as opponent_penalty_events,
        coalesce(oe.missed_penalty_events, 0) as opponent_missed_penalty_events
    from delivered as d
    left join fixtures as f
        on d.fixture_id = f.fixture_id
    left join fixtures_with_events as fe
        on d.fixture_id = fe.fixture_id
    left join team_events as te
        on d.fixture_id = te.fixture_id and d.team_id = te.team_id
    left join team_events as oe
        on
            d.fixture_id = oe.fixture_id
            and oe.team_id = if(d.team_id = f.home_team_id, f.away_team_id, f.home_team_id)
    left join match_assist_names as ma
        on d.fixture_id = ma.fixture_id
    left join team_lines as tl
        on d.fixture_id = tl.fixture_id and d.team_id = tl.team_id
    left join team_lines as ol
        on
            d.fixture_id = ol.fixture_id
            and ol.team_id = if(d.team_id = f.home_team_id, f.away_team_id, f.home_team_id)
    left join player_events as pe
        on d.fixture_id = pe.fixture_id and d.team_id = pe.team_id and d.player_id = pe.player_id
),

-- What the provider counted in the match, read from its own values before any change.
counted as (
    select
        *,
        countif(minutes is not null) over fixture > 0 as minutes_counted,
        countif(offsides is not null) over fixture > 0 as offsides_counted,
        countif(shots is not null) over fixture > 0 as shots_counted,
        countif(shots_on_target is not null) over fixture > 0 as shots_on_target_counted,
        countif(goals is not null) over fixture > 0 as goals_counted,
        countif(goals_against is not null) over fixture > 0 as goals_against_counted,
        countif(position_code = 'G' and goals_against is not null) over fixture > 0
            as goals_against_counted_by_keepers,
        countif(assists is not null) over fixture > 0 as assists_counted,
        countif(saves is not null) over fixture > 0 as saves_counted,
        countif(position_code = 'G' and saves is not null) over fixture > 0 as saves_counted_by_keepers,
        countif(passes is not null) over fixture > 0 as passes_counted,
        countif(passes_key is not null) over fixture > 0 as passes_key_counted,
        countif(passes_accurate is not null) over fixture > 0 as passes_accurate_counted,
        countif(tackles is not null) over fixture > 0 as tackles_counted,
        countif(blocks is not null) over fixture > 0 as blocks_counted,
        countif(interceptions is not null) over fixture > 0 as interceptions_counted,
        countif(duels is not null) over fixture > 0 as duels_counted,
        countif(duels_won is not null) over fixture > 0 as duels_won_counted,
        countif(dribbles is not null) over fixture > 0 as dribbles_counted,
        countif(dribbles_success is not null) over fixture > 0 as dribbles_success_counted,
        countif(dribbles_against is not null) over fixture > 0 as dribbles_against_counted,
        countif(fouls is not null) over fixture > 0 as fouls_counted,
        countif(fouls_against is not null) over fixture > 0 as fouls_against_counted,
        countif(cards_yellow is not null) over fixture > 0 as cards_yellow_counted,
        countif(cards_red is not null) over fixture > 0 as cards_red_counted,
        countif(penalties_won is not null) over fixture > 0 as penalties_won_counted,
        countif(penalties_committed is not null) over fixture > 0 as penalties_committed_counted,
        countif(penalties_scored is not null) over fixture > 0 as penalties_scored_counted,
        countif(penalties_missed is not null) over fixture > 0 as penalties_missed_counted,
        countif(penalties_saved is not null) over fixture > 0 as penalties_saved_counted,
        -- A count of accurate passes can never exceed the passes made; a percentage nearly always
        -- does, so the match's values summed against its passes summed tells the two apart.
        sum(if(passes is not null and passes_accurate is not null, passes_accurate, null)) over fixture
        > sum(if(passes is not null and passes_accurate is not null, passes, null)) over fixture
            as passes_accurate_is_percentage,
        sum(if(passes is not null and passes_accurate is not null, passes, null)) over fixture > 0
            as has_pass_data,
        countif(position_code = 'G' and minutes > 0) over team_match as team_keepers_with_minutes,
        greatest(
            coalesce(offsides, 0), coalesce(shots, 0), coalesce(shots_on_target, 0), coalesce(goals, 0),
            coalesce(goals_against, 0), coalesce(assists, 0), coalesce(saves, 0), coalesce(passes, 0),
            coalesce(passes_key, 0), coalesce(tackles, 0), coalesce(blocks, 0), coalesce(interceptions, 0),
            coalesce(duels, 0), coalesce(dribbles, 0), coalesce(dribbles_against, 0), coalesce(fouls, 0),
            coalesce(fouls_against, 0), coalesce(cards_yellow, 0), coalesce(cards_red, 0),
            coalesce(penalties_won, 0), coalesce(penalties_committed, 0), coalesce(penalties_scored, 0),
            coalesce(penalties_missed, 0), coalesce(penalties_saved, 0), coalesce(duels_won, 0),
            coalesce(dribbles_success, 0), coalesce(passes_accurate, 0), coalesce(event_goals, 0)
        ) > 0 as has_positive_stat
    from in_context
    window
        fixture as (partition by league_code, fixture_id),
        team_match as (partition by league_code, fixture_id, team_id)
),

-- 1. The blank rule. A keeper's saves and goals conceded are counted only by another keeper's
-- value, so an outfield player's zero cannot hand a keeper a clean sheet.
filled as (
    select
        *,
        coalesce(minutes, if(minutes_counted and not has_positive_stat, 0, null)) as minutes_filled,
        coalesce(offsides, if(offsides_counted or team_offsides = 0, 0, null)) as offsides_filled,
        coalesce(shots, if(shots_counted or team_shots = 0, 0, null)) as shots_filled,
        coalesce(shots_on_target, if(shots_on_target_counted or team_shots_on_target = 0, 0, null))
            as shots_on_target_filled,
        coalesce(
            goals,
            if(goals_counted or team_goals_for = 0 or (has_events and team_own_goals = team_goals_for), 0, null)
        ) as goals_filled,
        coalesce(
            goals_against,
            if(
                if(position_code = 'G', goals_against_counted_by_keepers, goals_against_counted)
                or team_goals_conceded = 0,
                0, null
            )
        ) as goals_against_filled,
        coalesce(
            assists,
            if(
                assists_counted
                or team_goals_for = 0
                or (
                    has_events
                    and team_goal_events + team_own_goals = team_goals_for
                    and team_assisted_goal_events = 0
                    and (team_open_play_goal_events = 0 or match_assisted_goal_events > 0)
                ),
                0, null
            )
        ) as assists_filled,
        coalesce(
            saves,
            if(if(position_code = 'G', saves_counted_by_keepers, saves_counted) or team_saves = 0, 0, null)
        ) as saves_filled,
        coalesce(passes, if(passes_counted, 0, null)) as passes_filled,
        coalesce(passes_key, if(passes_key_counted, 0, null)) as passes_key_filled,
        coalesce(passes_accurate, if(passes_accurate_counted, 0, null)) as passes_accurate_value_filled,
        coalesce(tackles, if(tackles_counted, 0, null)) as tackles_filled,
        coalesce(blocks, if(blocks_counted, 0, null)) as blocks_filled,
        coalesce(interceptions, if(interceptions_counted, 0, null)) as interceptions_filled,
        coalesce(duels, if(duels_counted, 0, null)) as duels_filled,
        coalesce(duels_won, if(duels_won_counted, 0, null)) as duels_won_filled,
        coalesce(dribbles, if(dribbles_counted, 0, null)) as dribbles_filled,
        coalesce(dribbles_success, if(dribbles_success_counted, 0, null)) as dribbles_success_filled,
        coalesce(dribbles_against, if(dribbles_against_counted, 0, null)) as dribbles_against_filled,
        coalesce(fouls, if(fouls_counted, 0, null)) as fouls_filled,
        coalesce(fouls_against, if(fouls_against_counted, 0, null)) as fouls_against_filled,
        coalesce(cards_yellow, if(cards_yellow_counted or (has_events and team_card_events = 0), 0, null))
            as cards_yellow_filled,
        coalesce(cards_red, if(cards_red_counted or (has_events and team_card_events = 0), 0, null))
            as cards_red_filled,
        coalesce(
            penalties_won, if(penalties_won_counted or (has_events and team_penalty_events = 0), 0, null)
        ) as penalties_won_filled,
        coalesce(
            penalties_committed,
            if(penalties_committed_counted or (has_events and opponent_penalty_events = 0), 0, null)
        ) as penalties_committed_filled,
        coalesce(
            penalties_scored,
            if(
                penalties_scored_counted or team_goals_for = 0
                or (has_events and team_penalty_goal_events = 0),
                0, null
            )
        ) as penalties_scored_filled,
        coalesce(
            penalties_missed, if(penalties_missed_counted or (has_events and team_penalty_events = 0), 0, null)
        ) as penalties_missed_filled,
        coalesce(
            penalties_saved, if(penalties_saved_counted or (has_events and opponent_penalty_events = 0), 0, null)
        ) as penalties_saved_filled
    from counted
),

-- 2. Accurate passes as a count. A percentage cannot be turned into a count without the passes,
-- and neither can a match with no pass data at all, so those stay blank.
as_counts as (
    select
        *,
        case
            when not coalesce(has_pass_data, false) then null
            when passes_accurate_is_percentage
                then cast(round(passes_filled * passes_accurate_value_filled / 100) as int64)
            else passes_accurate_value_filled
        end as passes_accurate_filled
    from filled
),

-- 3. Which source gives the team's goals in this match. The events can be placed only when
-- every scored goal names a player who has a row in the match.
goal_sources as (
    select
        league_code,
        fixture_id,
        team_id,
        coalesce(
            logical_and(goals_filled is not null)
            and sum(goals_filled) + any_value(team_own_goals) = any_value(team_goals_for),
            false
        ) as count_adds_up,
        coalesce(
            any_value(has_events)
            and any_value(team_goal_events_without_scorer) = 0
            and any_value(team_goal_events) + any_value(team_own_goals) = any_value(team_goals_for)
            and sum(coalesce(event_goals, 0)) = any_value(team_goal_events),
            false
        ) as events_add_up,
        countif(goals_filled is distinct from coalesce(event_goals, 0)) > 0 as sources_differ
    from as_counts
    group by league_code, fixture_id, team_id
),

goals_resolved as (
    select
        a.*,
        case
            when s.count_adds_up and s.events_add_up and s.sources_differ then 'events'
            when s.count_adds_up then 'count'
            when s.events_add_up then 'events'
            else 'count'
        end as goal_source
    from as_counts as a
    inner join goal_sources as s
        on a.league_code = s.league_code and a.fixture_id = s.fixture_id and a.team_id = s.team_id
),

goals_chosen as (
    select
        *,
        if(goal_source = 'events', coalesce(event_goals, 0), goals_filled) as goals_clean,
        if(has_events, coalesce(event_goals_penalty, 0), penalties_scored_filled) as goals_penalty_source
    from goals_resolved
),

penalties_chosen as (
    select
        *,
        if(goals_clean is null, goals_penalty_source, least(goals_penalty_source, goals_clean))
            as goals_penalty_clean,
        sum(if(position_code = 'G' and minutes > 0, goals_against_filled, null))
            over (partition by league_code, fixture_id, team_id) as team_keepers_goals_against
    from goals_chosen
),

-- 4a. Match stats against results. Keepers who shared the match share the team's goals conceded;
-- where their figures add up to more, no one of them can be corrected, so all are left blank. A
-- player cannot assist his own goal, so his assists are at most the team's goals minus his own.
-- The opponent's shots on target (plus the penalties it missed, which a keeper can save) cap the
-- saves only when that figure passes its own check: at least the opponent's open-play goals, at
-- most its shots.
against_results as (
    select
        *,
        case
            when shots_on_target_filled is null or goals_clean is null or goals_penalty_clean is null
                then shots_on_target_filled
            when goals_clean - goals_penalty_clean <= shots_on_target_filled then shots_on_target_filled
            when goals_clean - goals_penalty_clean - shots_on_target_filled <= 2
                then goals_clean - goals_penalty_clean
        end as shots_on_target_checked,
        case
            when goals_against_filled is null or team_goals_conceded is null then goals_against_filled
            when
                position_code = 'G' and minutes > 0 and team_keepers_with_minutes > 1
                and team_keepers_goals_against > team_goals_conceded
                then null
            when
                position_code = 'G' and team_keepers_with_minutes = 1 and minutes >= 90
                and goals_against_filled != team_goals_conceded
                then if(abs(goals_against_filled - team_goals_conceded) <= 2, team_goals_conceded, null)
            when goals_against_filled <= team_goals_conceded then goals_against_filled
            when goals_against_filled - team_goals_conceded <= 2 then team_goals_conceded
        end as goals_against_checked,
        case
            when assists_filled is null or team_goals_for is null then assists_filled
            when assists_filled <= greatest(team_goals_for - coalesce(goals_clean, 0), 0) then assists_filled
            when assists_filled - greatest(team_goals_for - coalesce(goals_clean, 0), 0) <= 2
                then greatest(team_goals_for - coalesce(goals_clean, 0), 0)
        end as assists_checked,
        opponent_shots_on_target is not null
        and opponent_shots_on_target
        >= team_goals_conceded - opponent_penalty_goal_events - opponent_own_goals
        and (opponent_shots is null or opponent_shots_on_target <= opponent_shots) as opponent_shots_on_target_verified,
        opponent_shots_on_target + opponent_missed_penalty_events as saves_ceiling
    from penalties_chosen
),

saves_checked as (
    select
        *,
        case
            when saves_filled is null or saves_ceiling is null or saves_filled <= saves_ceiling then saves_filled
            when not coalesce(opponent_shots_on_target_verified, false) then null
            when saves_filled - saves_ceiling <= 2 then saves_ceiling
        end as saves_clean,
        sum(assists_checked) over (partition by league_code, fixture_id, team_id) as team_assists_checked
    from against_results
),

-- A team's assists add up to at most its goals; where they still add up to more, no single assist
-- can be corrected, so the team's positive assists in that match are left blank.
assists_checked_by_team as (
    select
        *,
        if(team_assists_checked > team_goals_for and assists_checked > 0, null, assists_checked) as assists_clean
    from saves_checked
),

-- 4b. A whole the blank rule filled with a zero is only an inference: where the player's own
-- delivered part is above it (key passes with blank passes), the part stands and the whole is raised
-- to it.
wholes as (
    select
        *,
        case
            when passes is not null or passes_filled is null then passes_filled
            when greatest(coalesce(passes_key_filled, 0), coalesce(passes_accurate_filled, 0)) <= passes_filled
                then passes_filled
            when greatest(coalesce(passes_key_filled, 0), coalesce(passes_accurate_filled, 0)) - passes_filled <= 2
                then greatest(coalesce(passes_key_filled, 0), coalesce(passes_accurate_filled, 0))
        end as passes_clean,
        case
            when dribbles is not null or dribbles_filled is null then dribbles_filled
            when coalesce(dribbles_success_filled, 0) <= dribbles_filled then dribbles_filled
            when dribbles_success_filled - dribbles_filled <= 2 then dribbles_success_filled
        end as dribbles_clean,
        case
            when duels is not null or duels_filled is null then duels_filled
            when coalesce(duels_won_filled, 0) <= duels_filled then duels_filled
            when duels_won_filled - duels_filled <= 2 then duels_won_filled
        end as duels_clean
    from assists_checked_by_team
),

-- 4c. A part never above its whole, and the card maximum.
against_whole as (
    select
        *,
        case
            when shots_filled is null or shots_on_target_checked is null then shots_filled
            when shots_filled >= shots_on_target_checked then shots_filled
            when shots_on_target_checked - shots_filled <= 2 then shots_on_target_checked
        end as shots_clean,
        case
            when passes_accurate_filled is null or passes_clean is null then passes_accurate_filled
            when passes_accurate_filled <= passes_clean then passes_accurate_filled
            when passes_accurate_filled - passes_clean <= 2 then passes_clean
        end as passes_accurate_clean,
        case
            when passes_key_filled is null or passes_clean is null then passes_key_filled
            when passes_key_filled <= passes_clean then passes_key_filled
            when passes_key_filled - passes_clean <= 2 then passes_clean
        end as passes_key_clean,
        case
            when dribbles_success_filled is null or dribbles_clean is null then dribbles_success_filled
            when dribbles_success_filled <= dribbles_clean then dribbles_success_filled
            when dribbles_success_filled - dribbles_clean <= 2 then dribbles_clean
        end as dribbles_success_clean,
        case
            when duels_won_filled is null or duels_clean is null then duels_won_filled
            when duels_won_filled <= duels_clean then duels_won_filled
            when duels_won_filled - duels_clean <= 2 then duels_clean
        end as duels_won_clean,
        case
            when cards_yellow_filled is null or cards_yellow_filled <= 2 then cards_yellow_filled
            when cards_yellow_filled - 2 <= 2 then 2
        end as cards_yellow_clean,
        case
            when cards_red_filled is null or cards_red_filled <= 1 then cards_red_filled
            when cards_red_filled - 1 <= 2 then 1
        end as cards_red_clean
    from wholes
)

select
    league_code,
    fixture_id,
    team_id,
    player_id,
    minutes_filled as minutes,
    shirt_number,
    position_code,
    is_captain,
    is_substitute,
    offsides_filled as offsides,
    shots_clean as shots,
    shots_on_target_checked as shots_on_target,
    goals_clean as goals,
    goals_penalty_clean as goals_penalty,
    goals_against_checked as goals_against,
    assists_clean as assists,
    saves_clean as saves,
    passes_clean as passes,
    passes_key_clean as passes_key,
    passes_accurate_clean as passes_accurate,
    tackles_filled as tackles,
    blocks_filled as blocks,
    interceptions_filled as interceptions,
    duels_clean as duels,
    duels_won_clean as duels_won,
    dribbles_clean as dribbles,
    dribbles_success_clean as dribbles_success,
    dribbles_against_filled as dribbles_against,
    fouls_filled as fouls,
    fouls_against_filled as fouls_against,
    cards_yellow_clean as cards_yellow,
    cards_red_clean as cards_red,
    penalties_won_filled as penalties_won,
    penalties_committed_filled as penalties_committed,
    goals_penalty_clean as penalties_scored,
    penalties_missed_filled as penalties_missed,
    penalties_saved_filled as penalties_saved,
    raw_ingested_at,
    array(
        select correction
        from
            unnest([
                struct(
                    'goals' as stat,
                    goals as provider_value,
                    goals_clean as cleaned_value,
                    if(goals_clean is distinct from goals_filled, 'goals_from_events', null) as rule
                ),
                struct(
                    'goals_penalty', goals_penalty_source, goals_penalty_clean,
                    if(
                        goals_penalty_clean is distinct from goals_penalty_source,
                        'penalty_goals_limited_to_goals',
                        null
                    )
                ),
                struct(
                    'penalties_scored', penalties_scored, goals_penalty_clean,
                    if(
                        goals_penalty_clean is distinct from penalties_scored_filled,
                        'penalties_scored_matched_to_penalty_goals', null
                    )
                ),
                struct(
                    'shots_on_target', shots_on_target, shots_on_target_checked,
                    if(
                        shots_on_target_checked is distinct from shots_on_target_filled,
                        'raised_to_open_play_goals',
                        null
                    )
                ),
                struct(
                    'goals_against', goals_against, goals_against_checked,
                    if(
                        goals_against_checked is distinct from goals_against_filled,
                        'matched_to_team_goals_conceded',
                        null
                    )
                ),
                struct(
                    'assists', assists, assists_clean,
                    if(assists_clean is distinct from assists_filled, 'limited_to_team_goals', null)
                ),
                struct(
                    'saves', saves, saves_clean,
                    case
                        when saves_clean is not distinct from saves_filled then null
                        when
                            coalesce(opponent_shots_on_target_verified, false)
                            then 'limited_to_opponent_shots_on_target'
                        else 'opponent_shots_on_target_unverified'
                    end
                ),
                struct(
                    'shots', shots, shots_clean,
                    if(shots_clean is distinct from shots_filled, 'raised_to_shots_on_target', null)
                ),
                struct(
                    'passes', passes, passes_clean,
                    if(passes_clean is distinct from passes_filled, 'raised_to_part', null)
                ),
                struct(
                    'dribbles', dribbles, dribbles_clean,
                    if(dribbles_clean is distinct from dribbles_filled, 'raised_to_part', null)
                ),
                struct(
                    'duels', duels, duels_clean,
                    if(duels_clean is distinct from duels_filled, 'raised_to_part', null)
                ),
                struct(
                    'passes_accurate', passes_accurate_filled, passes_accurate_clean,
                    if(passes_accurate_clean is distinct from passes_accurate_filled, 'limited_to_whole', null)
                ),
                struct(
                    'passes_key', passes_key, passes_key_clean,
                    if(passes_key_clean is distinct from passes_key_filled, 'limited_to_whole', null)
                ),
                struct(
                    'dribbles_success', dribbles_success, dribbles_success_clean,
                    if(dribbles_success_clean is distinct from dribbles_success_filled, 'limited_to_whole', null)
                ),
                struct(
                    'duels_won', duels_won, duels_won_clean,
                    if(duels_won_clean is distinct from duels_won_filled, 'limited_to_whole', null)
                ),
                struct(
                    'cards_yellow', cards_yellow, cards_yellow_clean,
                    if(cards_yellow_clean is distinct from cards_yellow_filled, 'limited_to_card_maximum', null)
                ),
                struct(
                    'cards_red', cards_red, cards_red_clean,
                    if(cards_red_clean is distinct from cards_red_filled, 'limited_to_card_maximum', null)
                )
            ]) as correction
        where correction.rule is not null
    ) as stat_corrections
from against_whole
