select
    status_short,
    count(*) as fixtures,
    count(distinct home_team_sk) + count(distinct away_team_sk) as rough_team_refs
from `football-data-pipeline-gcp.core.fct_fixture`
where league_code = 'WC'
group by status_short
order by fixtures desc
