{#
  A team is never settled on a row with no provider attributes while another of its competition
  rows has them, whatever order the competitions were ingested in. Chelsea (49) is the named case:
  its UESC row carries only a name, and its other rows say England, CHE and Stamford Bridge. Each
  failing row is a team settled on an empty row, or Chelsea settled on anything but its filled one.
#}
{{ config(store_failures = true, severity = 'error') }}

with competition_rows as (
    select
        team_api_id,
        logical_or(
            coalesce(
                team_code, team_country, cast(team_founded_year as string), team_logo_url,
                cast(venue_api_id as string), venue_name, venue_address, venue_city,
                cast(venue_capacity as string)
            ) is not null
        ) as has_a_filled_row
    from {{ ref('base_apif__teams') }}
    group by team_api_id
),

settled as (
    select
        team_api_id,
        team_country,
        team_code,
        venue_name,
        coalesce(
            team_code, team_country, cast(team_founded_year as string), team_logo_url,
            cast(venue_api_id as string), venue_name, venue_address, venue_city,
            cast(venue_capacity as string)
        ) is null as is_empty
    from {{ ref('dim_team') }}
),

named_case as (
    select 49 as team_api_id
)

select
    s.team_api_id,
    s.team_country,
    s.team_code,
    s.venue_name,
    'settled on an empty row' as failure
from settled as s
inner join competition_rows as c
    on s.team_api_id = c.team_api_id
where s.is_empty and c.has_a_filled_row

union all

select
    n.team_api_id,
    s.team_country,
    s.team_code,
    s.venue_name,
    'Chelsea is not on its filled row' as failure
from named_case as n
left join settled as s
    on n.team_api_id = s.team_api_id
where
    s.team_country is distinct from 'England'
    or s.team_code is distinct from 'CHE'
    or s.venue_name is distinct from 'Stamford Bridge'
