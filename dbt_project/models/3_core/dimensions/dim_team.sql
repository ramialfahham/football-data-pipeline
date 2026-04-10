with base as (
    select
        league_code,
        normalized_team_key,
        canonical_team_name
    from {{ ref('base_team_names__cross_source') }}
),
deduped as (
    select distinct
        league_code,
        normalized_team_key,
        canonical_team_name
    from base
)

select
    {{ dbt_utils.generate_surrogate_key(['league_code', 'normalized_team_key']) }} as team_id,
    league_code,
    normalized_team_key,
    canonical_team_name as team_name
from deduped
