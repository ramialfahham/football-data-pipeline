select
    season_api_year,
    round_name,
    status_short,
    count(*) as fixtures,
    count(distinct home_team_sk) as home_teams
from `football-data-pipeline-gcp.core.fct_fixture`
where league_code = 'WC'
group by 1, 2, 3
order by fixtures desc
limit 40
