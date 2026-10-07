-- A team has at most one next match: returns every team flagged on more than one fixture.
with flagged as (
    select home_team_sk as team_sk
    from {{ ref('mart_competition_fixtures') }}
    where is_home_team_next_match
    union all
    select away_team_sk as team_sk
    from {{ ref('mart_competition_fixtures') }}
    where is_away_team_next_match
)

select
    team_sk,
    count(*) as next_matches
from flagged
group by team_sk
having count(*) > 1
