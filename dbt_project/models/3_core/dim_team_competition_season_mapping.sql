{{ config(materialized='table') }}

{#
    Conformed team↔competition↔season membership. One row per team per competition per
    season in which the team has at least one fixture — finished OR scheduled. A
    relationship (mapping) dimension, not an entity dim and not a fact: no measures, no
    descriptive attributes — only the participating keys. Grain is one row per association
    occurrence, so joining on a single participating key (e.g. team_sk) resolves a
    many-to-many and returns many rows by design. See the "relationship (mapping)
    dimensions" clause in dbt_project/docs/layering.md.

    Membership is derived from FIXTURES, not the /teams roster. Unlike a player (a squad
    member may never play, so membership must be asserted by the roster), a team that is in
    a competition always plays fixtures in it — so the fixture schedule is a complete,
    timing-stable source. Scheduled (not-yet-played) fixtures are INCLUDED, so a team is a
    member from the moment its fixtures are published. Use this to answer "which teams are
    in competition X, season Y"; per-match facts live in fct_fixture. (Known scope of the
    fixtures source: a team listed only in a standings table whose fixtures fall outside the
    ingested window is not a member here — see base_apif__teams; rare and out of scope for
    the membership question, which the CPO scoped to fixtures.)

    Grain is enforced by the final GROUP BY on (league_code, season, team_sk), so it cannot
    split. league_api_id is 1:1 with league_code by registry design; max(league_api_id)
    collapses it to the single value per group, so league_sk/season_sk stay well-defined even
    if that registry invariant were ever violated (the group key never depends on it).

    league_sk and season_sk are derived from the fixtures base exactly as fct_fixture and
    dim_competition_season derive them (the base carries league_api_id), so the keys conform
    to the fixtures fact and the season dim by construction. This deliberately differs from
    dim_player_team_season_mapping, which resolves them via a nullable dim_competition_season
    lookup ONLY because the roster source lacked league_api_id.
#}

with fixtures as (
    select
        league_code,
        league_api_id,
        season,
        home_team_id,
        away_team_id
    from {{ ref('base_apif__fixtures_next') }}
),

team_sides as (
    select
        league_code,
        league_api_id,
        season,
        home_team_id as team_id
    from fixtures
    union distinct
    select
        league_code,
        league_api_id,
        season,
        away_team_id as team_id
    from fixtures
),

memberships as (
    select
        league_code,
        season,
        cast(team_id as int64) as team_sk,
        max(league_api_id) as league_api_id
    from team_sides
    where team_id is not null
    group by league_code, season, team_sk
)

select
    {{ dbt_utils.generate_surrogate_key([
        'team_sk',
        'league_code',
        'season'
    ]) }} as team_competition_season_sk,
    team_sk,
    cast(league_api_id as int64) as league_sk,
    {{ dbt_utils.generate_surrogate_key(['league_api_id', 'season']) }} as season_sk,
    league_code,
    season as season_api_year
from memberships
