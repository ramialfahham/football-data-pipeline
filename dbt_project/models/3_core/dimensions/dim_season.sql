with historical as (
    select league as league_code, season
    from {{ ref('base_football_data__d1') }}
    union all
    select league as league_code, season
    from {{ ref('base_football_data__e0') }}
),
from_apif as (
    select
        league_code,
        cast(f.league.season as string) as season
    from {{ ref('base_apif__fixtures_next') }},
    unnest(payload_response) as f
),
combined as (
    select * from historical
    union all
    select * from from_apif
),
deduped as (
    select distinct
        league_code,
        season
    from combined
    where season is not null
      and trim(season) != ''
)

select
    {{ dbt_utils.generate_surrogate_key(['league_code', 'season']) }} as season_id,
    league_code,
    season as season_code
from deduped
