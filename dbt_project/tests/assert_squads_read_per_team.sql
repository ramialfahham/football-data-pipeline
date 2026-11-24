{#
  Every team RAW_APIF_SQUADS holds a block for is in stg_apif__squads, and every team of
  base_apif__squads has the players of its newest block. Returns one row per team the raw table
  carries that staging lacks, and one row per team whose base players differ from those of its
  newest staging block (a stale list, or an older list read in place of an empty newest one).
#}
{{ config(store_failures = true, severity = 'error') }}

with raw_teams as (
    select distinct safe_cast(json_value(team_block, '$.team_id') as int64) as team_id
    from {{ source('api_football', 'raw_apif_squads') }} as src,
        unnest(json_query_array(json_query(src.payload, '$.response'), '$')) as team_block
    where json_value(team_block, '$.team_id') is not null
),

staged_teams as (
    select distinct team_id
    from {{ ref('stg_apif__squads') }}
),

dropped_by_staging as (
    select
        'raw team missing from staging' as failure,
        cast(r.team_id as string) as grain
    from raw_teams as r
    left join staged_teams as s
        on r.team_id = s.team_id
    where s.team_id is null
),

newest as (
    select
        {{ team_id_override('team_id') }} as team_id,
        max(raw_ingested_at) as raw_ingested_at
    from {{ ref('stg_apif__squads') }}
    where team_id is not null
    group by 1
),

staged as (
    select
        {{ team_id_override('team_id') }} as team_id,
        {{ player_id_override('player_id') }} as player_id,
        raw_ingested_at
    from {{ ref('stg_apif__squads') }}
    where team_id is not null and player_id is not null
),

expected as (
    select distinct
        s.team_id,
        s.player_id
    from staged as s
    inner join newest as n
        on s.team_id = n.team_id and s.raw_ingested_at = n.raw_ingested_at
),

held as (
    select
        team_api_id as team_id,
        player_api_id as player_id
    from {{ ref('base_apif__squads') }}
),

differs as (
    select
        'base squad differs from the newest block' as failure,
        concat(
            cast(coalesce(e.team_id, h.team_id) as string), ' ', cast(coalesce(e.player_id, h.player_id) as string)
        ) as grain
    from expected as e
    full outer join held as h
        on e.team_id = h.team_id and e.player_id = h.player_id
    where e.team_id is null or h.team_id is null
)

select * from dropped_by_staging
union all
select * from differs
