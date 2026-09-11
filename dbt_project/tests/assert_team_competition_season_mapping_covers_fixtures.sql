-- Consistency guard for dim_team_competition_season_mapping.
-- The mapping must hold EXACTLY the team↔competition↔season set that the fixtures fact holds
-- — no missing members, no extras. A cross-model invariant between the core mapping and
-- fct_fixture (the canonical fixtures fact): it catches the membership logic drifting from
-- "every team with any fixture, finished OR scheduled, is a member" — e.g. a future status
-- filter that silently dropped scheduled fixtures, or a join that dropped rows. Competition-
-- agnostic: no league codes hardcoded, so it covers BL1/BL2 and every other league.
-- (The join-path regression — a member that does not resolve to a real team — is guarded
-- separately by the team_sk relationships test in core.yml.) Returns offending rows in
-- either direction; expect zero.

with fixture_membership as (
    select distinct
        league_code,
        season_api_year,
        home_team_sk as team_sk
    from {{ ref('fct_fixture') }}
    where home_team_sk is not null

    union distinct

    select distinct
        league_code,
        season_api_year,
        away_team_sk as team_sk
    from {{ ref('fct_fixture') }}
    where away_team_sk is not null
),

mapping as (
    select
        league_code,
        season_api_year,
        team_sk
    from {{ ref('dim_team_competition_season_mapping') }}
)

select
    'missing_from_mapping' as defect,
    fm.league_code,
    fm.season_api_year,
    fm.team_sk
from fixture_membership as fm
left join mapping as m
    on
        fm.league_code = m.league_code
        and fm.season_api_year = m.season_api_year
        and fm.team_sk = m.team_sk
where m.team_sk is null

union all

select
    'extra_in_mapping' as defect,
    m.league_code,
    m.season_api_year,
    m.team_sk
from mapping as m
left join fixture_membership as fm
    on
        m.league_code = fm.league_code
        and m.season_api_year = fm.season_api_year
        and m.team_sk = fm.team_sk
where fm.team_sk is null
