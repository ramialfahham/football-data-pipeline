-- A team knocked out of a competition has no fixture in a later round of it that season, and a
-- winner neither; a third-place match is not a later round, as the mart leaves it out of the
-- round reached. Returns each such team with the later fixture.

{{ config(store_failures = true) }}

with competitions as (
    select
        team_sk,
        league_code,
        season_api_year,
        reached_round_name,
        cup_status
    from {{ ref('mart_team_competitions') }}
    where cup_status in ('knocked_out', 'winners')
),

round_kinds as (
    select
        league_code,
        season_api_year,
        round_name,
        round_stage_kind
    from {{ ref('int_round_names') }}
),

fixtures as (
    select
        f.fixture_sk,
        f.league_code,
        f.season_api_year,
        f.round_name,
        f.round_sequence,
        f.home_team_sk,
        f.away_team_sk
    from {{ ref('mart_competition_fixtures') }} as f
    left join round_kinds as rk
        on
            f.league_code = rk.league_code
            and f.season_api_year = rk.season_api_year
            and f.round_name = rk.round_name
    where coalesce(rk.round_stage_kind, '') != 'placement'
),

reached_sequence as (
    select distinct
        c.team_sk,
        c.league_code,
        c.season_api_year,
        c.cup_status,
        f.round_sequence
    from competitions as c
    inner join fixtures as f
        on
            c.league_code = f.league_code
            and c.season_api_year = f.season_api_year
            and c.reached_round_name = f.round_name
)

select
    r.team_sk,
    r.league_code,
    r.season_api_year,
    r.cup_status,
    f.fixture_sk as later_fixture_sk,
    f.round_name as later_round_name
from reached_sequence as r
inner join fixtures as f
    on
        r.league_code = f.league_code
        and r.season_api_year = f.season_api_year
        and r.team_sk in (f.home_team_sk, f.away_team_sk)
        and r.round_sequence < f.round_sequence
