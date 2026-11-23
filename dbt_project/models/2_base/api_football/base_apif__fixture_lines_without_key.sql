{#
  The matches where base loses a value to its team-id filter. A statistics line or a line-up the
  provider sent with a fixture id and no team id is dropped by base_apif__fixture_statistics and
  base_apif__lineup_fetches; the match is here when a team of it has a value, or a sheet, that
  line could have given and no line with a team id gives (the macro lines_without_key says how).
  A line with no fixture id names no match. One row per match, line table and missing key.
#}
with participants as (
    select
        fixture_id,
        cast(home_team_id as int64) as home_team_id,
        cast(away_team_id as int64) as away_team_id
    from {{ ref('base_apif__fixtures_next') }}
    where
        home_team_id is not null
        and away_team_id is not null
),

overrides as (
    select
        cast(wrong_team_api_id as int64) as wrong_team_api_id,
        cast(correct_team_api_id as int64) as correct_team_api_id,
        mode,
        cast(fixture_id as int64) as fixture_id
    from {{ ref('fixture_team_id_overrides') }}
)

select distinct
    cast(fixture_id as int64) as fixture_id,
    line_table,
    missing_key
from (
    {{ lines_without_key(
        ref('stg_apif__fixture_statistics'),
        ref('stg_apif__lineups'),
        ref('base_apif__lineup_sheets'),
        'participants',
        'overrides'
    ) }}
)
