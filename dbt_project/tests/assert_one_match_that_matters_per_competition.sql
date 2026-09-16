-- is_match_that_matters is exactly "the fixture of the next matchday whose two teams have the
-- lowest sum of table positions, ties to the earlier kickoff": at most one flagged fixture per
-- competition, it is the one the rule picks, and no fixture is flagged where either side has no
-- position (a team in zero or several standings sections that season).
--
-- Recomputed from fct_fixture and fct_standings with the mart's own window definition, not from
-- the mart's CTEs, so a rewrite of the mart that flags by a different rule, flags twice, or
-- flags a knockout tie fails here even when the schema tests stay green.
--
-- Returns a row (= fails) per competition where the property does not hold.
with upcoming as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        round_name,
        fixture_date,
        kickoff_datetime,
        home_team_sk,
        away_team_sk
    from {{ ref('fct_fixture') }}
    where
        status_short in ('NS', 'TBD')
        and fixture_date >= current_date()
),

next_round as (
    select
        league_code,
        season_api_year,
        round_name
    from upcoming
    qualify row_number() over (
        partition by league_code
        order by fixture_date asc, kickoff_datetime asc, fixture_sk asc
    ) = 1
),

positions as (
    select
        league_code,
        season_api_year,
        team_sk,
        standing_rank
    from {{ ref('fct_standings') }}
    qualify count(*) over (partition by league_code, season_api_year, team_sk) = 1
),

expected as (
    select
        u.league_code,
        u.fixture_sk
    from upcoming as u
    inner join next_round as n
        on
            u.league_code = n.league_code
            and u.season_api_year = n.season_api_year
            and u.round_name = n.round_name
    inner join positions as h
        on
            u.league_code = h.league_code
            and u.season_api_year = h.season_api_year
            and u.home_team_sk = h.team_sk
    inner join positions as a
        on
            u.league_code = a.league_code
            and u.season_api_year = a.season_api_year
            and u.away_team_sk = a.team_sk
    qualify row_number() over (
        partition by u.league_code
        order by
            h.standing_rank + a.standing_rank asc,
            u.fixture_date asc,
            u.kickoff_datetime asc,
            u.fixture_sk asc
    ) = 1
),

served as (
    select
        league_code,
        countif(is_match_that_matters) as n_flagged,
        max(if(is_match_that_matters, fixture_sk, null)) as flagged_fixture_sk
    from {{ ref('mart_next_matchday') }}
    group by league_code
)

select
    s.league_code,
    s.n_flagged,
    s.flagged_fixture_sk,
    e.fixture_sk as expected_fixture_sk
from served as s
left join expected as e
    on s.league_code = e.league_code
where
    s.n_flagged > 1
    or (e.fixture_sk is null and s.n_flagged != 0)
    or (e.fixture_sk is not null and s.flagged_fixture_sk is distinct from e.fixture_sk)
