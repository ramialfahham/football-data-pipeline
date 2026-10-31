-- Every team with a Team page has its row in mart_team_index, so the Teams page lists it.

with team_pages as (
    select distinct team_sk
    from {{ ref('mart_team_profile') }}
),

team_index as (
    select team_sk
    from {{ ref('mart_team_index') }}
)

select p.team_sk
from team_pages as p
left join team_index as i
    on p.team_sk = i.team_sk
where i.team_sk is null
