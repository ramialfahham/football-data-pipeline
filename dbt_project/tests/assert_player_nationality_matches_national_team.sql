{#
  A player who appeared for a national team holds that team's nationality. Each row is a player
  whose nationality is none of the national teams he appeared for; most are dual nationals, the
  rest are provider errors to research. Named case: Lionel Messi (154), Argentina, appeared for
  Argentina and is never listed.
#}
{{ config(store_failures = true, severity = 'warn') }}

with appearances as (
    select
        player_sk,
        team_sk
    from {{ ref('fct_fixture_lineup') }}
    union distinct
    select
        player_sk,
        team_sk
    from {{ ref('fct_fixture_player_stats') }}
),

national_teams_played as (
    select
        a.player_sk,
        array_agg(distinct t.team_country ignore nulls order by t.team_country) as national_countries
    from appearances as a
    inner join {{ ref('dim_team') }} as t
        on a.team_sk = t.team_sk
    where t.is_national_team
    group by a.player_sk
),

compared as (
    select
        p.player_api_id,
        p.player_name,
        p.player_nationality,
        n.national_countries,
        p.player_nationality not in unnest(n.national_countries) as is_mismatch
    from national_teams_played as n
    inner join {{ ref('dim_player') }} as p
        on n.player_sk = p.player_sk
    where p.player_nationality is not null
),

named_case as (
    select 154 as player_api_id
)

select
    player_api_id,
    player_name,
    player_nationality,
    array_to_string(national_countries, ', ') as national_teams,
    'nationality is none of the national teams played for' as failure
from compared
where is_mismatch

union all

select
    n.player_api_id,
    c.player_name,
    c.player_nationality,
    array_to_string(c.national_countries, ', ') as national_teams,
    'named case: Messi is not an Argentina player with Argentinian nationality' as failure
from named_case as n
left join compared as c
    on n.player_api_id = c.player_api_id
where c.is_mismatch is distinct from false
