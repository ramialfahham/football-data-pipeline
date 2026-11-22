{#
  One row per player per fixture, before the blank rule: the player's line in the match's picked
  fetch, his goals, assists, cards and minutes settled by the match's events where the fetches
  disagree, and the newest value of each blank stat from another fetch that gives him the same
  results (step 0 of the cleaning_rules doc block). It is its own model so that the team
  statistics read the player's offsides without a cycle: the players model reads the statistics
  for its shots fill and its zero fill.
#}
with stat_lines as (
    select
        stat_line.*,
        {{ fixture_player_id(
            'stat_line.player_id', 'stat_line.fixture_id', 'stat_line.team_id', 'stat_line.shirt_number'
        ) }} as kept_player_id
    from {{ ref('stg_apif__fixture_players') }} as stat_line
    where
        stat_line.fixture_id is not null
        and stat_line.team_id is not null
),

src as (
    select
        league_code,
        fixture_id,
        team_id,
        kept_player_id as player_id,
        minutes_played,
        shirt_number,
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
        raw_ingested_at,
        if(position_code in ('G', 'D', 'M', 'F'), position_code, null) as position_code
    from stat_lines
    where
        kept_player_id is not null
        -- player_id = 0 is the API placeholder for an unknown player (no real id);
        -- it is not a real player and produces phantom cross-team duplicate legs.
        and kept_player_id != 0
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
-- `reattribute_in_fixture` replaces the id inside the one fixture named, where two clubs share it.
overrides as (
    select
        cast(wrong_team_api_id as int64) as wrong_team_api_id,
        cast(correct_team_api_id as int64) as correct_team_api_id,
        mode,
        cast(fixture_id as int64) as fixture_id
    from {{ ref('fixture_team_id_overrides') }}
),

-- The player's team where his row and his events disagree, decided in base_apif__fixture_events.
resolved_teams as (
    select
        fixture_id,
        player_id,
        {{ one_value('resolved_player_team_id') }} as team_id
    from {{ ref('base_apif__fixture_events') }}
    where resolved_player_team_id is not null
    group by fixture_id, player_id
),

-- The player's team on a researched line-up, which an official source settles.
researched_teams as (
    select distinct
        fixture_id,
        player_id,
        team_id
    from {{ ref('fixture_lineup_corrections') }}
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
            researched_teams.team_id,
            resolved_teams.team_id,
            fixture_override.correct_team_api_id,
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
        ) as delivered_values,
        logical_or(src.goals_against is not null)
            over (partition by src.league_code, src.fixture_id, src.raw_ingested_at) as fetch_is_complete
    from src
    left join overrides as fixture_override
        on
            src.team_id = fixture_override.wrong_team_api_id
            and src.fixture_id = fixture_override.fixture_id
            and fixture_override.mode = 'reattribute_in_fixture'
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
    left join resolved_teams
        on
            src.fixture_id = resolved_teams.fixture_id
            and src.player_id = resolved_teams.player_id
    left join researched_teams
        on
            src.fixture_id = researched_teams.fixture_id
            and src.player_id = researched_teams.player_id
),

-- The provider's values under our names, one row per player per fixture and fetch. A player the
-- provider lists twice in one fetch keeps the row with more values, and the rows' own values break a
-- tie, so every build keeps the same row. A match's picked fetch is its newest fetch in the
-- provider's complete format, else its newest fetch. The newer format leaves goals conceded and
-- dribbled past blank for every player, so a fetch counts as complete when any player in it has goals
-- conceded. A fetch whose accurate passes add up to more than its passes sent percentages.
fetch_rows as (
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
        penalty_saved as penalties_saved,
        raw_ingested_at = coalesce(
            max(if(fetch_is_complete, raw_ingested_at, null)) over per_match,
            max(raw_ingested_at) over per_match
        ) as is_picked,
        sum(if(passes_total is not null and passes_accuracy_percent is not null, passes_accuracy_percent, null))
            over per_fetch
        > sum(if(passes_total is not null and passes_accuracy_percent is not null, passes_total, null))
            over per_fetch as fetch_sent_percentages
    from corrected
    qualify
        row_number() over (
            partition by league_code, fixture_id, team_id, player_id, raw_ingested_at
            order by delivered_values desc, to_json_string(corrected) asc
        ) = 1
    window
        per_match as (partition by league_code, fixture_id),
        per_fetch as (partition by league_code, fixture_id, raw_ingested_at)
),

-- One row per player per fixture: his row in the picked fetch, and his rows in the other fetches,
-- newest first.
player_fetches as (
    select
        league_code,
        fixture_id,
        team_id,
        player_id,
        array_agg(if(fetch_row.is_picked, fetch_row, null) ignore nulls limit 1)[offset(0)] as picked,
        array_agg(if(fetch_row.is_picked, null, fetch_row) ignore nulls order by fetch_row.raw_ingested_at desc)
            as others
    from fetch_rows as fetch_row
    group by league_code, fixture_id, team_id, player_id
    having logical_or(fetch_row.is_picked)
    -- Drop cross-team id-collisions: the provider sometimes reuses one player_id for two
    -- different players in a fixture (one per team, e.g. AFCCL 2016 id 44061), so the id is
    -- unreliable and both legs are unattributable. Extends the player_id = 0 phantom-leg
    -- cleanup above to real-but-collided ids; keeps the (fixture, player) grain unique
    -- downstream (int_legs__player_match / mart_player_match_log).
    qualify
        min(team_id) over (partition by league_code, fixture_id, player_id)
        = max(team_id) over (partition by league_code, fixture_id, player_id)
),

events as (
    select
        fixture_id,
        team_id,
        player_id,
        minute_elapsed,
        event_type,
        event_detail,
        event_comments,
        assist_player_name,
        assist_player_id,
        is_goal,
        is_own_goal,
        is_missed_penalty,
        has_full_events,
        is_goal and not is_own_goal as is_scorer_goal
    from {{ ref('base_apif__fixture_events') }}
),

fixtures_with_events as (
    select fixture_id
    from events
    where has_full_events
    group by fixture_id
),

-- The provider marks a coach's card "Not on pitch".
player_cards as (
    select
        fixture_id,
        player_id,
        {{ one_value('team_id') }} as team_id,
        countif(event_detail = 'Yellow Card') as yellow_cards,
        countif(event_detail = 'Red Card') as red_cards
    from events
    where
        event_type = 'Card'
        and coalesce(event_comments, '') != 'Not on pitch'
        and has_full_events
        and player_id is not null
    group by fixture_id, player_id
),

event_results as (
    select
        fixture_id,
        player_id,
        sum(goal) as goals,
        sum(assist) as assists
    from (
        select
            fixture_id,
            player_id,
            1 as goal,
            0 as assist
        from events
        where is_scorer_goal and player_id is not null
        union all
        select
            fixture_id,
            assist_player_id as player_id,
            0 as goal,
            1 as assist
        from events
        where is_scorer_goal and assist_player_id is not null
    )
    group by fixture_id, player_id
),

-- The minute a substitution brought the player on.
minutes_on as (
    select
        fixture_id,
        assist_player_id as player_id,
        max(minute_elapsed) as minute_on
    from events
    where event_type = 'subst' and assist_player_id is not null
    group by fixture_id, assist_player_id
),

-- 0. Results where the fetches disagree: where another fetch gives a player the goals, assists or
-- cards of the match's events and the picked fetch does not, the events' count is his. Where the
-- picked fetch leaves his minutes blank, another fetch's minutes stand when a substitution brought
-- him on that many minutes before the 90th, the minute of entry counted or not.
{%- set event_counts = {
    'goals': 'r.goals', 'assists': 'r.assists', 'cards_yellow': 'c.yellow_cards', 'cards_red': 'c.red_cards'
} %}
decided as (
    select
        p.picked.* except (is_picked, minutes, goals, assists, cards_yellow, cards_red),
        p.others,
        coalesce(
            p.picked.minutes,
            (
                select o.minutes
                from unnest(p.others) as o with offset as fetch_order
                where o.minutes between 90 - s.minute_on and 91 - s.minute_on
                order by fetch_order
                limit 1
            )
        ) as minutes,
        {%- for result, event_count in event_counts.items() %}
        if(
            e.fixture_id is not null
            and coalesce(p.picked.{{ result }}, 0) != coalesce({{ event_count }}, 0)
            and exists (
                select 1
                from unnest(p.others) as o
                where coalesce(o.{{ result }}, 0) = coalesce({{ event_count }}, 0)
            ),
            coalesce({{ event_count }}, 0),
            p.picked.{{ result }}
        ) as {{ result }},
        {%- endfor %}
        e.fixture_id is not null as has_match_events
    from player_fetches as p
    left join fixtures_with_events as e
        on p.fixture_id = e.fixture_id
    left join event_results as r
        on e.fixture_id = r.fixture_id and p.player_id = r.player_id
    left join player_cards as c
        on e.fixture_id = c.fixture_id and p.player_id = c.player_id
    left join minutes_on as s
        on p.fixture_id = s.fixture_id and p.player_id = s.player_id
),

-- The other fetches that give the player the same results, blank counted as 0, newest first.
donors as (
    select
        d.* except (others),
        array(
            select as struct o.*
            from unnest(d.others) as o with offset as fetch_order
            where
                coalesce(o.goals, 0) = coalesce(d.goals, 0)
                and coalesce(o.assists, 0) = coalesce(d.assists, 0)
                and coalesce(o.cards_yellow, 0) = coalesce(d.cards_yellow, 0)
                and coalesce(o.cards_red, 0) = coalesce(d.cards_red, 0)
                and coalesce(o.minutes, 0) = coalesce(d.minutes, 0)
                and coalesce(o.goals_against, 0) = coalesce(d.goals_against, 0)
                and coalesce(o.saves, 0) = coalesce(d.saves, 0)
                and coalesce(o.penalties_won, 0) = coalesce(d.penalties_won, 0)
                and coalesce(o.penalties_committed, 0) = coalesce(d.penalties_committed, 0)
                and coalesce(o.penalties_scored, 0) = coalesce(d.penalties_scored, 0)
                and coalesce(o.penalties_missed, 0) = coalesce(d.penalties_missed, 0)
                and coalesce(o.penalties_saved, 0) = coalesce(d.penalties_saved, 0)
            order by fetch_order
        ) as donor_fetches
    from decided as d
),

-- The newest value of each blank stat such a fetch carries; accurate passes only from a fetch that
-- sent them in the picked fetch's form.
{%- set fillable = [
    'shirt_number', 'position_code', 'offsides', 'shots', 'shots_on_target', 'passes', 'passes_key',
    'tackles', 'blocks', 'interceptions', 'duels', 'duels_won', 'dribbles', 'dribbles_success',
    'dribbles_against', 'fouls', 'fouls_against'
] %}
donated as (
    select
        d.* except (donor_fetches),
        {%- for stat in fillable %}
        (
            select o.{{ stat }}
            from unnest(d.donor_fetches) as o with offset as fetch_order
            where o.{{ stat }} is not null
            order by fetch_order
            limit 1
        ) as donated_{{ stat }},
        {%- endfor %}
        (
            select o.passes_accurate
            from unnest(d.donor_fetches) as o with offset as fetch_order
            where o.passes_accurate is not null and o.fetch_sent_percentages = d.fetch_sent_percentages
            order by fetch_order
            limit 1
        ) as donated_passes_accurate
    from donors as d
)

select * from donated
