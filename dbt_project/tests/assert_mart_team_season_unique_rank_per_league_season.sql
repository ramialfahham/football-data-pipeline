-- In any (league_code, season_api_year) group, every team should have a
-- distinct non-null latest_rank. Two teams sharing the same rank means the
-- mart is surfacing stale snapshot rows (see mart_team_season fct_standings
-- dedup), which breaks the matchday preview's home/away rank pair.
-- dbt singular test: returns rows when the assertion fails.

select
    league_code,
    season_api_year,
    latest_rank,
    count(*) as duplicate_team_count,
    array_agg(team_name order by team_name) as duplicate_teams
from {{ ref('mart_team_season') }}
where latest_rank is not null
group by league_code, season_api_year, latest_rank
having count(*) > 1
