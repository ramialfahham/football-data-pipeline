select
    s.team_sk,
    any_value(t.team_name) as team_name,
    any_value(t.team_country) as team_country,
    count(distinct s.standings_group_description) as group_count,
    string_agg(distinct s.standings_group_description, ', ') as group_labels
from `football-data-pipeline-gcp.core.fct_standings` as s
left join `football-data-pipeline-gcp.core.dim_team` as t on s.team_sk = t.team_sk
where s.league_code = 'WC'
group by s.team_sk
order by team_name
