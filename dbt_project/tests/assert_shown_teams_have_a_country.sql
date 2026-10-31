-- Every team with a page (one row in mart_team_profile) has a country, or the Teams page lists it
-- under "no recorded country". Reported, not fatal: the fix is a row in team_country_corrections.
{{ config(severity = 'warn', store_failures = true) }}

with shown_teams as (
    select distinct team_sk
    from {{ ref('mart_team_profile') }}
),

teams as (
    select * from {{ ref('dim_team') }}
)

select
    teams.team_sk,
    teams.team_name
from shown_teams
inner join teams
    on shown_teams.team_sk = teams.team_sk
where nullif(trim(teams.team_country), '') is null
