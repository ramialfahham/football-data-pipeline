{#
  A player's surname is the same in every /players delivery, and a team's name is the same in every
  competition. Surnames are compared without accents, so "M. Pašalić" and "Mario Pasalic" agree.
  Each row is a player or team named two ways, to research. Named case: player 419517, delivered
  as "T. Rajmund" and as "R.Tóth", is listed.
#}
{{ config(store_failures = true, severity = 'warn') }}

with player_names as (
    select distinct
        player_name,
        safe_cast(player_id as int64) as entity_id,
        regexp_extract(
            regexp_replace(normalize(lower(player_name), nfd), r'\pM', ''),
            r'([a-z][a-z\'-]*)\s*$'
        ) as surname
    from {{ ref('stg_apif__players') }}
    where player_id is not null and player_name is not null
),

players_named_twice as (
    select
        'player' as entity,
        entity_id,
        string_agg(distinct player_name, ' | ' order by player_name) as names
    from player_names
    group by entity_id
    having count(distinct surname) > 1
),

teams_named_twice as (
    select
        'team' as entity,
        team_api_id as entity_id,
        string_agg(distinct team_name, ' | ' order by team_name) as names
    from {{ ref('base_apif__teams') }}
    where team_name is not null
    group by team_api_id
    having count(distinct regexp_replace(normalize(lower(team_name), nfd), r'\pM', '')) > 1
),

listed as (
    select * from players_named_twice
    union all
    select * from teams_named_twice
),

named_case as (
    select
        'player' as entity,
        419517 as entity_id
)

select
    entity,
    entity_id,
    names,
    'named two ways' as failure
from listed

union all

select
    n.entity,
    n.entity_id,
    cast(null as string) as names,
    'named case: player 419517 is not listed' as failure
from named_case as n
left join listed as l
    on n.entity = l.entity and n.entity_id = l.entity_id
where l.entity_id is null
