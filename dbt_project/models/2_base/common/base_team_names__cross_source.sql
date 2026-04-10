with football_data_names as (
    select
        'football_data_co_uk' as source_system,
        league as league_code,
        home_team as source_team_name
    from {{ ref('base_football_data__d1') }}
    union all
    select
        'football_data_co_uk' as source_system,
        league as league_code,
        away_team as source_team_name
    from {{ ref('base_football_data__d1') }}
    union all
    select
        'football_data_co_uk' as source_system,
        league as league_code,
        home_team as source_team_name
    from {{ ref('base_football_data__e0') }}
    union all
    select
        'football_data_co_uk' as source_system,
        league as league_code,
        away_team as source_team_name
    from {{ ref('base_football_data__e0') }}
),
apif_names as (
    select
        'api_football' as source_system,
        league_code,
        cast(f.teams.home.name as string) as source_team_name
    from {{ ref('base_apif__fixtures_next') }}, unnest(payload_response) as f
    union all
    select
        'api_football' as source_system,
        league_code,
        cast(f.teams.away.name as string) as source_team_name
    from {{ ref('base_apif__fixtures_next') }}, unnest(payload_response) as f
),
all_names as (
    select * from football_data_names
    union all
    select * from apif_names
),
cleaned as (
    select distinct
        source_system,
        league_code,
        trim(source_team_name) as source_team_name,
        {{ team_name_key("source_team_name") }} as normalized_team_key
    from all_names
    where source_team_name is not null
      and trim(source_team_name) != ''
),
ranked as (
    select
        *,
        case
            when source_system = 'api_football' then 1
            else 2
        end as source_priority
    from cleaned
),
canonical as (
    select
        league_code,
        normalized_team_key,
        array_agg(source_team_name order by source_priority, length(source_team_name) desc limit 1)[offset(0)] as canonical_team_name
    from ranked
    group by league_code, normalized_team_key
)

select
    r.source_system,
    r.league_code,
    r.source_team_name,
    r.normalized_team_key,
    c.canonical_team_name
from ranked r
left join canonical c
    on r.league_code = c.league_code
   and r.normalized_team_key = c.normalized_team_key
