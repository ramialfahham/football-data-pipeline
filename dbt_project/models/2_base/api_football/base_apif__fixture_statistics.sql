-- Pivot the long-format staging rows (one per statistic line) into one wide row
-- per (fixture, team), then keep the latest ingest snapshot per (fixture, team).
-- The pivot is business reshaping and lives here in base, not in staging.
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
            as shots_on_goal,
        max(case when stat_type = 'Shots off Goal' then safe_cast(stat_value_raw as int64) end)
            as shots_off_goal,
        max(case when stat_type = 'Total Shots' then safe_cast(stat_value_raw as int64) end)
            as shots_total,
        max(case when stat_type = 'Blocked Shots' then safe_cast(stat_value_raw as int64) end)
            as shots_blocked,
        max(case when stat_type = 'Shots insidebox' then safe_cast(stat_value_raw as int64) end)
            as shots_inside_box,
        max(case when stat_type = 'Shots outsidebox' then safe_cast(stat_value_raw as int64) end)
            as shots_outside_box,
        max(case when stat_type = 'Fouls' then safe_cast(stat_value_raw as int64) end)
            as fouls,
        max(case when stat_type = 'Corner Kicks' then safe_cast(stat_value_raw as int64) end)
            as corner_kicks,
        max(case when stat_type = 'Offsides' then safe_cast(stat_value_raw as int64) end)
            as offsides,
        max(case
            when stat_type = 'Ball Possession'
                then safe_cast(regexp_replace(stat_value_raw, r'%', '') as int64)
        end) as ball_possession_percent,
        max(case when stat_type = 'Yellow Cards' then safe_cast(stat_value_raw as int64) end)
            as yellow_cards,
        max(case when stat_type = 'Red Cards' then safe_cast(stat_value_raw as int64) end)
            as red_cards,
        max(case when stat_type = 'Goalkeeper Saves' then safe_cast(stat_value_raw as int64) end)
            as goalkeeper_saves,
        max(case when stat_type = 'Total passes' then safe_cast(stat_value_raw as int64) end)
            as passes_total,
        max(case when stat_type = 'Passes accurate' then safe_cast(stat_value_raw as int64) end)
            as passes_accurate,
        max(case
            when stat_type = 'Passes %'
                then safe_cast(regexp_replace(stat_value_raw, r'%', '') as int64)
        end) as passes_accuracy_percent
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

-- CPO-owned corrections for known provider team-id defects, from
-- seeds/fixture_team_id_overrides.csv. `alias` = unconditional duplicate-id replacement (one club
-- under two provider ids); `reattribute_if_cohabiting` = replace only when the correct id is a
-- fixture participant and the wrong id is not (a mis-attribution between two DISTINCT clubs, so a
-- club's own legitimate statistics are never touched). Same seed and same two modes the events
-- model has used since #526; it was simply never wired to this feed, which is why WCQAS fixture
-- 1100382 still carries a Mação row that #53 had already diagnosed and registered.
overrides as (
    select
        cast(wrong_team_api_id as int64) as wrong_team_api_id,
        cast(correct_team_api_id as int64) as correct_team_api_id,
        mode
    from {{ ref('fixture_team_id_overrides') }}
),

-- Corrected BEFORE the dedup below, not after: the dedup key contains team_id and the model
-- carries a uniqueness test on (league_code, fixture_id, team_id). Remapping afterwards would emit
-- two rows for one (fixture, team) whenever the correct id already has one of its own; remapping
-- first lets the model's existing latest-ingest-wins rule resolve that collision.
corrected as (
    select
        pivoted.* except (team_id),
        coalesce(
            alias_override.correct_team_api_id,
            reattribute_override.correct_team_api_id,
            pivoted.team_id
        ) as team_id
    from pivoted
    left join overrides as alias_override
        on
            pivoted.team_id = alias_override.wrong_team_api_id
            and alias_override.mode = 'alias'
    left join fixture_participants
        on pivoted.fixture_id = fixture_participants.fixture_id
    left join overrides as reattribute_override
        on
            pivoted.team_id = reattribute_override.wrong_team_api_id
            and reattribute_override.mode = 'reattribute_if_cohabiting'
            and reattribute_override.correct_team_api_id in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
            and reattribute_override.wrong_team_api_id not in (
                fixture_participants.home_team_id, fixture_participants.away_team_id
            )
),

deduped_fixture_statistics as (
    select *
    from corrected
    qualify row_number() over (
        partition by league_code, fixture_id, team_id
        order by raw_ingested_at desc
    ) = 1
)

select
    league_code,
    fixture_id,
    team_id,
    shots_on_goal,
    shots_off_goal,
    shots_total,
    shots_blocked,
    shots_inside_box,
    shots_outside_box,
    fouls,
    corner_kicks,
    offsides,
    ball_possession_percent,
    yellow_cards,
    red_cards,
    goalkeeper_saves,
    passes_total,
    passes_accurate,
    passes_accuracy_percent,
    raw_ingested_at
from deduped_fixture_statistics
