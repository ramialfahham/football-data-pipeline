{#
  Every stored fetch of a team's sheet, under the team id after fixture_team_id_overrides.
  provider_team_id is the id the provider filed the sheet under, team_id the id it is kept under.
  base_apif__lineup_fetch_ties, base_apif__lineup_sheets and base_apif__fixture_players read it.
  Grain: one row per provider sheet fetch, (league_code, fixture_id, provider_team_id, raw_ingested_at).
#}
with src as (
    select
        league_code,
        fixture_id,
        team_id as provider_team_id,
        formation,
        start_xi_json,
        substitutes_json,
        raw_ingested_at
    from {{ ref('stg_apif__lineups') }}
    where
        fixture_id is not null
        and team_id is not null
),

fixture_participants as (
    select
        league_code,
        fixture_id,
        season,
        fixture_date,
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

select
    src.league_code,
    src.fixture_id,
    src.provider_team_id,
    src.formation,
    src.start_xi_json,
    src.substitutes_json,
    src.raw_ingested_at,
    coalesce(
        fixture_override.correct_team_api_id,
        alias_override.correct_team_api_id,
        reattribute_override.correct_team_api_id,
        src.provider_team_id
    ) as team_id
from src
left join overrides as fixture_override
    on
        src.provider_team_id = fixture_override.wrong_team_api_id
        and src.fixture_id = fixture_override.fixture_id
        and fixture_override.mode = 'reattribute_in_fixture'
left join overrides as alias_override
    on
        src.provider_team_id = alias_override.wrong_team_api_id
        and alias_override.mode = 'alias'
left join fixture_participants
    on src.fixture_id = fixture_participants.fixture_id
left join overrides as reattribute_override
    on
        src.provider_team_id = reattribute_override.wrong_team_api_id
        and reattribute_override.mode = 'reattribute_if_cohabiting'
        and reattribute_override.correct_team_api_id in (
            fixture_participants.home_team_id, fixture_participants.away_team_id
        )
        and reattribute_override.wrong_team_api_id not in (
            fixture_participants.home_team_id, fixture_participants.away_team_id
        )
