-- A side shows the previous season only before its team has played the fixture's competition this
-- season, awarded results not counted; once it has, the side shows this season or nothing. One row
-- per side that shows the previous season although its team has played.
with played as (
    select distinct
        team_sk,
        league_code,
        season_api_year
    from {{ ref('int_legs__team_match') }}
    where not is_awarded_result
),

previous_season_sides as (
    select distinct
        r.upcoming_fixture_sk,
        r.team_sk,
        f.league_code,
        f.season_api_year
    from {{ ref('mart_player_season_record') }} as r
    inner join {{ ref('fct_fixture') }} as f
        on r.upcoming_fixture_sk = f.fixture_sk
    where r.window_type = 'prev_season'
)

select
    s.upcoming_fixture_sk,
    s.team_sk,
    s.league_code,
    s.season_api_year
from previous_season_sides as s
inner join played as p
    on
        s.team_sk = p.team_sk
        and s.league_code = p.league_code
        and s.season_api_year = p.season_api_year
