{#
  A delivery that leaves an identity field empty never blanks it: a player's birth date or
  nationality, or a team's country, is filled in base wherever any stored delivery holds one,
  unless player_bio_corrections left it blank because the sources disagree. A team's country that
  changed between deliveries is the exception: it is withheld, blank and flagged, until a
  team_country_corrections row settles it.
  Named case: H. Abe (33085), whose latest delivery is blank and an earlier one says Japan and
  1999-01-28, has both.
#}
{{ config(store_failures = true, severity = 'error') }}

with player_deliveries as (
    select
        safe_cast(player_id as int64) as player_api_id,
        logical_or({{ possible_birth_date('birth_date', 'raw_ingested_at') }} is not null) as has_birth_date,
        logical_or(nullif(trim(nationality), '') is not null) as has_nationality
    from {{ ref('stg_apif__players') }}
    where player_id is not null
    group by player_api_id
),

checked_fields as (
    select
        player_api_id,
        corrected_field
    from {{ ref('player_bio_corrections') }}
),

team_deliveries as (
    select
        team_api_id,
        logical_or(team_country is not null) as has_country
    from {{ ref('base_apif__teams') }}
    group by team_api_id
),

changed_countries as (
    select d.team_id as team_api_id
    from {{ ref('stg_apif__team_deliveries') }} as d
    left join {{ ref('country_name_overrides') }} as o
        on d.team_country = o.provider_country
    where d.team_country is not null
    group by d.team_id
    having count(distinct coalesce(o.country_name, d.team_country)) > 1
),

named_case as (
    select 33085 as player_api_id
)

select
    'player' as entity,
    p.player_api_id as entity_id,
    'birth date blank though a delivery holds one' as failure
from {{ ref('base_apif__players') }} as p
inner join player_deliveries as d
    on p.player_api_id = d.player_api_id
left join checked_fields as c
    on p.player_api_id = c.player_api_id and c.corrected_field = 'player_birth_date'
where d.has_birth_date and p.player_birth_date is null and c.player_api_id is null

union all

select
    'player' as entity,
    p.player_api_id as entity_id,
    'nationality blank though a delivery holds one' as failure
from {{ ref('base_apif__players') }} as p
inner join player_deliveries as d
    on p.player_api_id = d.player_api_id
left join checked_fields as c
    on p.player_api_id = c.player_api_id and c.corrected_field = 'player_nationality'
where d.has_nationality and p.player_nationality is null and c.player_api_id is null

union all

select
    'team' as entity,
    t.team_api_id as entity_id,
    'country blank though a competition row holds one' as failure
from {{ ref('base_apif__teams_global') }} as t
inner join team_deliveries as d
    on t.team_api_id = d.team_api_id
left join changed_countries as c
    on t.team_api_id = c.team_api_id
where d.has_country and t.team_country is null and c.team_api_id is null

union all

select
    'team' as entity,
    t.team_api_id as entity_id,
    'country withheld after a change is not blank or not flagged' as failure
from {{ ref('base_apif__teams_global') }} as t
inner join changed_countries as c
    on t.team_api_id = c.team_api_id
left join {{ ref('team_country_corrections') }} as k
    on t.team_api_id = k.team_api_id
where k.team_api_id is null and (t.team_country is not null or not t.country_needs_research)

union all

select
    'player' as entity,
    n.player_api_id as entity_id,
    'named case: H. Abe is not Japanese and born 1999-01-28' as failure
from named_case as n
left join {{ ref('base_apif__players') }} as p
    on n.player_api_id = p.player_api_id
where
    p.player_nationality is distinct from 'Japan'
    or p.player_birth_date is distinct from date '1999-01-28'
