select
    group_description,
    count(distinct team_sk) as teams
from `football-data-pipeline-gcp.core.fct_standings`
where league_code = 'WC'
group by group_description
order by group_description
