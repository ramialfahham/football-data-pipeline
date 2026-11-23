-- The team's line in a match, cleaned once and named in our own words: one row per team with a
-- statistics line and per team of every finished match, so the goal split and the card zeros the
-- events prove are cleaned here for a team-match with no line too. The rules are the cleaning_rules
-- doc block (models/docs/cleaning_rules.md); the pivot of the long-format staging rows is business
-- reshaping and lives here too.
with stat_lines as (
    select
        league_code,
        raw_ingested_at,
        fixture_id,
        team_id,
        stat_type,
        stat_value_raw
    from {{ ref('stg_apif__fixture_statistics') }}
    where
        fixture_id is not null
        and team_id is not null
),

pivoted as (
    select
        league_code,
        raw_ingested_at,
        fixture_id,
        team_id,
        max(case when stat_type = 'Shots on Goal' then safe_cast(stat_value_raw as int64) end)
            as shots_on_target,
        max(case when stat_type = 'Shots off Goal' then safe_cast(stat_value_raw as int64) end)
            as shots_off_target,
        max(case when stat_type = 'Total Shots' then safe_cast(stat_value_raw as int64) end)
            as shots,
        max(case when stat_type = 'Blocked Shots' then safe_cast(stat_value_raw as int64) end)
            as shots_blocked,
        max(case when stat_type = 'Shots insidebox' then safe_cast(stat_value_raw as int64) end)
            as shots_inside_box,
        max(case when stat_type = 'Shots outsidebox' then safe_cast(stat_value_raw as int64) end)
            as shots_outside_box,
        max(case when stat_type = 'Fouls' then safe_cast(stat_value_raw as int64) end)
            as fouls,
        max(case when stat_type = 'Corner Kicks' then safe_cast(stat_value_raw as int64) end)
            as corners,
        max(case when stat_type = 'Offsides' then safe_cast(stat_value_raw as int64) end)
            as offsides,
        max(case when stat_type = 'Free Kicks' then safe_cast(stat_value_raw as int64) end)
            as free_kicks,
        max(case
            when stat_type = 'Ball Possession'
                then safe_cast(regexp_replace(stat_value_raw, r'%', '') as int64)
        end) as possession_pct,
        max(case when stat_type = 'Yellow Cards' then safe_cast(stat_value_raw as int64) end)
            as cards_yellow,
        max(case when stat_type = 'Red Cards' then safe_cast(stat_value_raw as int64) end)
            as cards_red,
        max(case when stat_type = 'Goalkeeper Saves' then safe_cast(stat_value_raw as int64) end)
            as saves,
        max(case when stat_type = 'Total passes' then safe_cast(stat_value_raw as int64) end)
            as passes,
        max(case when stat_type = 'Passes accurate' then safe_cast(stat_value_raw as int64) end)
            as passes_accurate
    from stat_lines
    group by league_code, raw_ingested_at, fixture_id, team_id
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
-- club's own legitimate statistics are never touched); `reattribute_in_fixture` = replace inside
-- the one fixture named, where two clubs share the id, and it outranks the other two.
overrides as (
    select
        cast(wrong_team_api_id as int64) as wrong_team_api_id,
        cast(correct_team_api_id as int64) as correct_team_api_id,
        mode,
        cast(fixture_id as int64) as fixture_id
    from {{ ref('fixture_team_id_overrides') }}
),

-- Every (fixture, provider team id) the statistics lines name, mapped once to the team id they are
-- kept under.
team_id_pairs as (
    select distinct
        fixture_id,
        team_id as provider_team_id
    from pivoted
),

team_id_map as (
    select
        pairs.fixture_id,
        pairs.provider_team_id,
        coalesce(
            fixture_override.correct_team_api_id,
            alias_override.correct_team_api_id,
            reattribute_override.correct_team_api_id,
            pairs.provider_team_id
        ) as team_id
    from team_id_pairs as pairs
    left join overrides as fixture_override
        on
            pairs.provider_team_id = fixture_override.wrong_team_api_id
            and pairs.fixture_id = fixture_override.fixture_id
            and fixture_override.mode = 'reattribute_in_fixture'
    left join overrides as alias_override
        on
            pairs.provider_team_id = alias_override.wrong_team_api_id
            and alias_override.mode = 'alias'
    left join fixture_participants
        on pairs.fixture_id = fixture_participants.fixture_id
    left join overrides as reattribute_override
        on
            pairs.provider_team_id = reattribute_override.wrong_team_api_id
            and reattribute_override.mode = 'reattribute_if_cohabiting'
            and reattribute_override.correct_team_api_id in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
            and reattribute_override.wrong_team_api_id not in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
),

-- Corrected BEFORE the dedup below, not after: the dedup key contains team_id and the model
-- carries a uniqueness test on (league_code, fixture_id, team_id). Remapping afterwards would emit
-- two rows for one (fixture, team) whenever the correct id already has one of its own; remapping
-- first lets the newest-value rule resolve that collision.
corrected as (
    select
        pivoted.* except (team_id),
        pivoted.team_id as provider_team_id,
        team_id_map.team_id
    from pivoted
    inner join team_id_map
        on pivoted.fixture_id = team_id_map.fixture_id and pivoted.team_id = team_id_map.provider_team_id
),

-- A fetch can file one team's line under its wrong id and its correct id: the line under the
-- correct id comes first.
ranked as (
    select
        *,
        row_number() over (
            partition by league_code, fixture_id, team_id
            order by raw_ingested_at desc, provider_team_id = team_id desc, provider_team_id asc
        ) as fetch_rank
    from corrected
),

-- The events of a match bound a team's card count only where none is filed under a team that did
-- not play the match: such a card counts against no team of the match.
matches_with_events as (
    select events.fixture_id
    from {{ ref('base_apif__fixture_events') }} as events
    left join fixture_participants as participants
        on events.fixture_id = participants.fixture_id
    group by events.fixture_id
    having
        logical_or(events.has_full_events)
        and not coalesce(
            logical_or({{ team_not_in_fixture(
                'events.team_id', 'participants.home_team_id', 'participants.away_team_id'
            ) }}),
            false
        )
),

-- The events that bound a team's card count of each colour: those that are certainly that colour,
-- and those that could be it.
card_events as (
    select
        fixture_id,
        team_id,
        countif(event_type = 'Card' and event_detail = 'Yellow Card') as yellow_certain,
        countif(
            (event_type = 'Card' and coalesce(event_detail, '') != 'Red Card')
            or (event_type = 'Var' and event_detail = 'Card reviewed')
        ) as yellow_possible,
        countif(event_type = 'Card' and event_detail = 'Red Card') as red_certain,
        countif(
            (event_type = 'Card' and coalesce(event_detail, '') != 'Yellow Card')
            or (
                event_type = 'Var'
                and (
                    starts_with(event_detail, 'Card upgrade')
                    or event_detail in ('Red card cancelled', 'Card reviewed')
                )
            )
        ) as red_possible
    from {{ ref('base_apif__fixture_events') }}
    where team_id is not null
    group by fixture_id, team_id
),

-- Each stat is the newest value any fetch's line carried, so a stat a later fetch leaves out keeps
-- the value an earlier one gave.
newest_values as (
    select
        league_code,
        fixture_id,
        team_id,
        max(raw_ingested_at) as raw_ingested_at,
        array_agg(shots_on_target ignore nulls order by fetch_rank limit 1)[safe_offset(0)]
            as shots_on_target,
        array_agg(shots_off_target ignore nulls order by fetch_rank limit 1)[safe_offset(0)]
            as shots_off_target,
        array_agg(shots ignore nulls order by fetch_rank limit 1)[safe_offset(0)] as shots,
        array_agg(shots_blocked ignore nulls order by fetch_rank limit 1)[safe_offset(0)]
            as shots_blocked,
        array_agg(shots_inside_box ignore nulls order by fetch_rank limit 1)[safe_offset(0)]
            as shots_inside_box,
        array_agg(shots_outside_box ignore nulls order by fetch_rank limit 1)[safe_offset(0)]
            as shots_outside_box,
        array_agg(fouls ignore nulls order by fetch_rank limit 1)[safe_offset(0)] as fouls,
        array_agg(corners ignore nulls order by fetch_rank limit 1)[safe_offset(0)] as corners,
        array_agg(offsides ignore nulls order by fetch_rank limit 1)[safe_offset(0)] as offsides,
        array_agg(free_kicks ignore nulls order by fetch_rank limit 1)[safe_offset(0)] as free_kicks,
        array_agg(possession_pct ignore nulls order by fetch_rank limit 1)[safe_offset(0)]
            as possession_pct,
        array_agg(cards_yellow ignore nulls order by fetch_rank limit 1)[safe_offset(0)]
            as cards_yellow,
        array_agg(cards_red ignore nulls order by fetch_rank limit 1)[safe_offset(0)] as cards_red,
        array_agg(saves ignore nulls order by fetch_rank limit 1)[safe_offset(0)] as saves,
        array_agg(passes ignore nulls order by fetch_rank limit 1)[safe_offset(0)] as passes,
        array_agg(passes_accurate ignore nulls order by fetch_rank limit 1)[safe_offset(0)]
            as passes_accurate,
        array_agg(struct(cards_yellow, cards_red) order by fetch_rank limit 1)[offset(0)] as latest_cards
    from ranked
    group by league_code, fixture_id, team_id
),

-- A card count from an earlier fetch stands only where the match's events allow it: no fewer cards
-- than those certainly of that colour, no more than those that could be.
delivered as (
    select
        n.* except (cards_yellow, cards_red, latest_cards),
        if(
            n.latest_cards.cards_yellow is null
            and n.cards_yellow not between coalesce(c.yellow_certain, 0) and coalesce(c.yellow_possible, 0)
            and m.fixture_id is not null,
            null,
            n.cards_yellow
        ) as cards_yellow,
        if(
            n.latest_cards.cards_red is null
            and n.cards_red not between coalesce(c.red_certain, 0) and coalesce(c.red_possible, 0)
            and m.fixture_id is not null,
            null,
            n.cards_red
        ) as cards_red
    from newest_values as n
    left join matches_with_events as m
        on n.fixture_id = m.fixture_id
    left join card_events as c
        on n.fixture_id = c.fixture_id and n.team_id = c.team_id
),

fixtures as (
    select
        fixture_id,
        league_code,
        goals_home,
        goals_away,
        raw_ingested_at,
        cast(home_team_id as int64) as home_team_id,
        cast(away_team_id as int64) as away_team_id,
        is_finished
        and goals_home is not null and goals_away is not null
        and home_team_id is not null and away_team_id is not null as is_finished
    from {{ ref('base_apif__fixtures_next') }}
),

finished_teams as (
    select
        league_code,
        fixture_id,
        home_team_id as team_id
    from fixtures
    where is_finished
    union all
    select
        league_code,
        fixture_id,
        away_team_id
    from fixtures
    where is_finished
),

team_matches as (
    select
        d.* except (league_code, fixture_id, team_id, raw_ingested_at),
        d.raw_ingested_at as line_ingested_at,
        coalesce(
            d.shots_on_target, d.shots_off_target, d.shots, d.shots_blocked, d.shots_inside_box,
            d.shots_outside_box, d.fouls, d.corners, d.offsides, d.possession_pct, d.cards_yellow,
            d.cards_red, d.saves, d.passes, d.passes_accurate
        ) is not null as has_stat_line,
        coalesce(d.league_code, ft.league_code) as league_code,
        coalesce(d.fixture_id, ft.fixture_id) as fixture_id,
        coalesce(d.team_id, ft.team_id) as team_id
    from delivered as d
    full outer join finished_teams as ft
        on d.fixture_id = ft.fixture_id and d.team_id = ft.team_id
),

-- The provider files an own goal under the team it counts for. A card event of no colour, and a
-- video review of a card, count against a zero of either colour they could be; an upgrade or a
-- cancelled red counts as red.
events as (
    select
        fixture_id,
        team_id,
        event_type,
        event_detail,
        raw_ingested_at,
        is_goal,
        is_own_goal,
        is_missed_penalty,
        has_full_events
    from {{ ref('base_apif__fixture_events') }}
),

-- A card event filed under a team that did not play the match has no team to count against, so a
-- match with one proves no team's card count to be zero.
match_events as (
    select
        events.fixture_id,
        logical_or(events.has_full_events) as events_delivered,
        coalesce(
            logical_or({{ team_not_in_fixture('events.team_id', 'fixtures.home_team_id', 'fixtures.away_team_id') }}),
            false
        ) as has_misfiled_event,
        max(events.raw_ingested_at) as events_ingested_at
    from events
    left join fixtures
        on events.fixture_id = fixtures.fixture_id
    group by events.fixture_id
),

team_events as (
    select
        fixture_id,
        team_id,
        countif(is_goal) as goal_events,
        countif(is_goal and event_detail = 'Penalty') as penalty_goal_events,
        countif(is_goal and is_own_goal) as own_goal_events,
        countif(is_missed_penalty) as missed_penalty_events,
        countif(
            (event_type = 'Card' and coalesce(event_detail, '') != 'Red Card')
            or (event_type = 'Var' and event_detail = 'Card reviewed')
        ) as events_against_no_yellow,
        countif(
            (event_type = 'Card' and coalesce(event_detail, '') != 'Yellow Card')
            or (
                event_type = 'Var'
                and (
                    starts_with(event_detail, 'Card upgrade')
                    or event_detail in ('Red card cancelled', 'Card reviewed')
                )
            )
        ) as events_against_no_red
    from events
    where team_id is not null
    group by fixture_id, team_id
),

-- The most offsides a player of the team has in the match: the value the player keeps in
-- base_apif__fixture_players, from the picked fetch or the one that fills it, under the team id the
-- players are kept under.
player_offsides as (
    select
        fixture_id,
        team_id,
        max(coalesce(offsides, donated_offsides)) as player_offsides_max
    from {{ ref('base_apif__fixture_player_lines') }}
    group by fixture_id, team_id
),

in_context as (
    select
        t.*,
        po.player_offsides_max,
        o.shots_on_target as opponent_shots_on_target,
        o.shots_off_target as opponent_shots_off_target,
        o.shots as opponent_shots,
        o.shots_blocked as opponent_shots_blocked,
        o.shots_inside_box as opponent_shots_inside_box,
        o.shots_outside_box as opponent_shots_outside_box,
        o.fouls as opponent_fouls,
        o.corners as opponent_corners,
        o.offsides as opponent_offsides,
        o.free_kicks as opponent_free_kicks,
        o.cards_yellow as opponent_cards_yellow,
        o.cards_red as opponent_cards_red,
        o.saves as opponent_saves,
        o.passes as opponent_passes,
        o.passes_accurate as opponent_passes_accurate,
        coalesce(f.is_finished, false) as is_finished,
        if(t.team_id = f.home_team_id, f.goals_home, f.goals_away) as goals_for,
        if(t.team_id = f.home_team_id, f.goals_away, f.goals_home) as goals_conceded,
        coalesce(me.events_delivered, false) as events_delivered,
        coalesce(me.has_misfiled_event, false) as has_misfiled_event,
        coalesce(te.goal_events, 0) as goal_events,
        coalesce(te.penalty_goal_events, 0) as penalty_goal_events,
        coalesce(te.own_goal_events, 0) as own_goal_events,
        coalesce(te.events_against_no_yellow, 0) as events_against_no_yellow,
        coalesce(te.events_against_no_red, 0) as events_against_no_red,
        coalesce(oe.penalty_goal_events, 0) as opponent_penalty_goal_events,
        coalesce(oe.own_goal_events, 0) as opponent_own_goal_events,
        coalesce(oe.missed_penalty_events, 0) as opponent_missed_penalty_events,
        greatest(
            coalesce(t.line_ingested_at, timestamp('1970-01-01')),
            coalesce(o.raw_ingested_at, timestamp('1970-01-01')),
            coalesce(me.events_ingested_at, timestamp('1970-01-01')),
            coalesce(f.raw_ingested_at, timestamp('1970-01-01'))
        ) as raw_ingested_at
    from team_matches as t
    left join fixtures as f
        on t.fixture_id = f.fixture_id
    left join delivered as o
        on
            t.fixture_id = o.fixture_id
            and o.team_id = if(t.team_id = f.home_team_id, f.away_team_id, f.home_team_id)
    left join player_offsides as po
        on t.fixture_id = po.fixture_id and t.team_id = po.team_id
    left join match_events as me
        on t.fixture_id = me.fixture_id
    left join team_events as te
        on t.fixture_id = te.fixture_id and t.team_id = te.team_id
    left join team_events as oe
        on
            t.fixture_id = oe.fixture_id
            and oe.team_id = if(t.team_id = f.home_team_id, f.away_team_id, f.home_team_id)
),

-- 1. The blank rule: a blank count is a zero where the other team's line, as delivered, has a value
-- for the stat; a card where the match's events were delivered and none of them stands against that
-- zero; saves where the opponent had no shot on target. Every other blank stays blank, possession
-- always: it is a share, not a count. An offsides count of a team that has a player with an offside
-- is never 0: a 0 the provider sent is blank, and a blank the other team's line or the team's own
-- full line would zero stays blank.
-- 2. The goal split: penalty and own goals are the team's goal events where the match's events
-- were delivered and they add up to its score, 0 where it scored none, blank otherwise.
filled as (
    select
        *,
        coalesce(shots_on_target, if(opponent_shots_on_target is not null, 0, null)) as shots_on_target_filled,
        coalesce(shots_off_target, if(opponent_shots_off_target is not null, 0, null)) as shots_off_target_filled,
        coalesce(shots, if(opponent_shots is not null, 0, null)) as shots_filled,
        coalesce(shots_blocked, if(opponent_shots_blocked is not null, 0, null)) as shots_blocked_filled,
        coalesce(shots_inside_box, if(opponent_shots_inside_box is not null, 0, null)) as shots_inside_box_filled,
        coalesce(shots_outside_box, if(opponent_shots_outside_box is not null, 0, null)) as shots_outside_box_filled,
        coalesce(fouls, if(opponent_fouls is not null, 0, null)) as fouls_filled,
        coalesce(corners, if(opponent_corners is not null, 0, null)) as corners_filled,
        case
            when player_offsides_max > 0 then nullif(offsides, 0)
            else coalesce(
                offsides,
                if(opponent_offsides is not null or (fouls is not null and possession_pct is not null), 0, null)
            )
        end as offsides_filled,
        coalesce(free_kicks, if(opponent_free_kicks is not null, 0, null)) as free_kicks_filled,
        coalesce(
            cards_yellow,
            if(
                opponent_cards_yellow is not null
                or (events_delivered and not has_misfiled_event and events_against_no_yellow = 0),
                0,
                null
            )
        ) as cards_yellow_filled,
        coalesce(
            cards_red,
            if(
                opponent_cards_red is not null
                or (events_delivered and not has_misfiled_event and events_against_no_red = 0),
                0,
                null
            )
        ) as cards_red_filled,
        coalesce(
            saves,
            if(
                opponent_saves is not null
                or coalesce(opponent_shots_on_target, if(shots_on_target is not null, 0, null)) = 0,
                0,
                null
            )
        ) as saves_filled,
        coalesce(passes, if(opponent_passes is not null, 0, null)) as passes_filled,
        coalesce(passes_accurate, if(opponent_passes_accurate is not null, 0, null)) as passes_accurate_filled,
        coalesce(opponent_shots_on_target, if(shots_on_target is not null, 0, null))
            as opponent_shots_on_target_filled,
        coalesce(opponent_shots, if(shots is not null, 0, null)) as opponent_shots_filled,
        case
            when not is_finished then null
            when goals_for = 0 then 0
            when events_delivered and goal_events = goals_for then penalty_goal_events
        end as goals_penalty,
        case
            when not is_finished then null
            when goals_for = 0 then 0
            when events_delivered and goal_events = goals_for then own_goal_events
        end as goals_own
    from in_context
),

-- 3. Against the results: shots on target are at least the open-play goals, and shots at least
-- both. The opponent's shots on target (plus the penalties it missed, which a
-- keeper can save) cap the saves only when that figure passes its own check: at least the
-- opponent's open-play goals, at most its shots. Only a gap of at most 2 is corrected; a larger
-- one leaves the stat blank.
against_results as (
    select
        *,
        case
            when shots_on_target_filled is null or goals_penalty is null or goals_own is null
                then shots_on_target_filled
            when goals_for - goals_penalty - goals_own <= shots_on_target_filled then shots_on_target_filled
            when goals_for - goals_penalty - goals_own - shots_on_target_filled <= 2
                then goals_for - goals_penalty - goals_own
        end as shots_on_target_clean,
        opponent_shots_on_target_filled is not null
        and opponent_shots_on_target_filled
        >= goals_conceded - opponent_penalty_goal_events - opponent_own_goal_events
        and (opponent_shots_filled is null or opponent_shots_on_target_filled <= opponent_shots_filled)
            as opponent_shots_on_target_verified,
        opponent_shots_on_target_filled + opponent_missed_penalty_events as saves_ceiling
    from filled
),

-- Shots are at least the shots on target and at least the open-play goals, each where known: a
-- shots figure is checked against the result even when the shots on target were left blank.
shots_floors as (
    select
        *,
        greatest(coalesce(shots_on_target_clean, 0), coalesce(goals_for - goals_penalty - goals_own, 0))
            as shots_floor
    from against_results
),

checked as (
    select
        *,
        case
            when shots_filled is null then shots_filled
            when shots_filled >= shots_floor then shots_filled
            when shots_floor - shots_filled <= 2 then shots_floor
        end as shots_clean,
        case
            when saves_filled is null or saves_ceiling is null or saves_filled <= saves_ceiling then saves_filled
            when not coalesce(opponent_shots_on_target_verified, false) then null
            when saves_filled - saves_ceiling <= 2 then saves_ceiling
        end as saves_clean,
        case
            when passes_accurate_filled is null or passes_filled is null then passes_accurate_filled
            when passes_accurate_filled <= passes_filled then passes_accurate_filled
            when passes_accurate_filled - passes_filled <= 2 then passes_filled
        end as passes_accurate_clean
    from shots_floors
),

-- 4. A part never above its whole, and a split of shots that does not add up to the total leaves
-- that split blank, apart from shots on target, which its own check vouches for. Where the inside
-- and outside the box exceed the total by exactly the own goals credited to the team, the provider
-- counted each own goal as a shot of the team's (its convention up to 2018): inside the box, where
-- an own goal is scored, loses them.
own_goals_in_split as (
    select
        *,
        coalesce(
            goals_own between 1 and 2
            and shots_inside_box_filled >= goals_own
            and shots_inside_box_filled + coalesce(shots_outside_box_filled, 0) - shots_clean = goals_own,
            false
        ) as own_goals_counted_as_shots
    from checked
),

against_whole as (
    select
        *,
        case
            when shots_inside_box_filled is null or shots_clean is null then shots_inside_box_filled
            when own_goals_counted_as_shots then shots_inside_box_filled - goals_own
            when shots_inside_box_filled <= shots_clean then shots_inside_box_filled
            when shots_inside_box_filled - shots_clean <= 2 then shots_clean
        end as shots_inside_box_limited
    from own_goals_in_split
),

splits as (
    select
        *,
        coalesce(shots_on_target_clean + shots_off_target_filled + shots_blocked_filled != shots_clean, false)
            as on_off_blocked_split_fails,
        coalesce(shots_inside_box_limited + shots_outside_box_filled != shots_clean, false)
            as inside_outside_split_fails
    from against_whole
),

cleaned as (
    select
        *,
        if(on_off_blocked_split_fails, null, shots_off_target_filled) as shots_off_target_clean,
        if(on_off_blocked_split_fails, null, shots_blocked_filled) as shots_blocked_clean,
        if(inside_outside_split_fails, null, shots_inside_box_limited) as shots_inside_box_clean,
        if(inside_outside_split_fails, null, shots_outside_box_filled) as shots_outside_box_clean
    from splits
),

participants as (
    select
        fixture_id as participant_fixture_id,
        cast(home_team_id as int64) as home_team,
        cast(away_team_id as int64) as away_team
    from {{ ref('base_apif__fixtures_next') }}
),

flagged as (
    select
        c.*,
        {{ team_not_in_fixture('c.team_id', 'p.home_team', 'p.away_team') }} as team_needs_research
    from cleaned as c
    left join participants as p
        on c.fixture_id = p.participant_fixture_id
)

select
    league_code,
    fixture_id,
    team_id,
    has_stat_line,
    shots_on_target_clean as shots_on_target,
    shots_off_target_clean as shots_off_target,
    shots_clean as shots,
    shots_blocked_clean as shots_blocked,
    shots_inside_box_clean as shots_inside_box,
    shots_outside_box_clean as shots_outside_box,
    fouls_filled as fouls,
    corners_filled as corners,
    offsides_filled as offsides,
    free_kicks_filled as free_kicks,
    possession_pct,
    cards_yellow_filled as cards_yellow,
    cards_red_filled as cards_red,
    saves_clean as saves,
    passes_filled as passes,
    passes_accurate_clean as passes_accurate,
    goals_penalty,
    goals_own,
    raw_ingested_at,
    team_needs_research,
    array(
        select correction
        from
            unnest([
                struct(
                    'shots_on_target' as stat,
                    shots_on_target as provider_value,
                    shots_on_target_clean as cleaned_value,
                    if(
                        shots_on_target_clean is distinct from shots_on_target_filled,
                        'raised_to_open_play_goals',
                        null
                    ) as rule
                ),
                struct(
                    'shots', shots, shots_clean,
                    case
                        when shots_clean is not distinct from shots_filled then null
                        when
                            coalesce(goals_for - goals_penalty - goals_own, 0) > coalesce(shots_on_target_clean, 0)
                            then 'raised_to_open_play_goals'
                        else 'raised_to_shots_on_target'
                    end
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
                    'passes_accurate', passes_accurate, passes_accurate_clean,
                    if(passes_accurate_clean is distinct from passes_accurate_filled, 'limited_to_whole', null)
                ),
                struct(
                    'shots_inside_box', shots_inside_box, shots_inside_box_clean,
                    case
                        when shots_inside_box_clean is not distinct from shots_inside_box_filled then null
                        when inside_outside_split_fails then 'split_does_not_add_up'
                        when own_goals_counted_as_shots then 'own_goals_left_out'
                        else 'limited_to_whole'
                    end
                ),
                struct(
                    'shots_outside_box', shots_outside_box, shots_outside_box_clean,
                    if(
                        shots_outside_box_clean is distinct from shots_outside_box_filled,
                        'split_does_not_add_up',
                        null
                    )
                ),
                struct(
                    'shots_off_target', shots_off_target, shots_off_target_clean,
                    if(
                        shots_off_target_clean is distinct from shots_off_target_filled,
                        'split_does_not_add_up',
                        null
                    )
                ),
                struct(
                    'shots_blocked', shots_blocked, shots_blocked_clean,
                    if(shots_blocked_clean is distinct from shots_blocked_filled, 'split_does_not_add_up', null)
                )
            ]) as correction
        where correction.rule is not null
    ) as stat_corrections
from flagged
