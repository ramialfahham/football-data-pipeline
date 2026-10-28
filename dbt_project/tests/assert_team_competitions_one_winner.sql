-- A competition-season has at most one winner on mart_team_competitions. Returns each
-- competition-season that names more than one.

{{ config(store_failures = true) }}

select
    league_code,
    season_api_year,
    count(*) as winners
from {{ ref('mart_team_competitions') }}
where cup_status = 'winners'
group by league_code, season_api_year
having count(*) > 1
