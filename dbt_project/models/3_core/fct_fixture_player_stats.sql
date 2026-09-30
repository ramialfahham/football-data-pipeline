{{
    config(
        materialized='incremental',
        unique_key='fixture_player_stat_sk',
        on_schema_change='sync_all_columns'
    )
}}

{#
  A table built before the cleaned columns existed is re-merged in full, once: the build that
  first finds it without goals_penalty, or with goals_penalty on no row, processes every base row,
  so no row keeps an empty column after on_schema_change adds the new ones. The second case is a
  build that failed after adding the columns and before its merge: they are separate statements.
  Every later build is incremental.
#}
{% set cleaned_columns_present = true %}
{% if is_incremental() %}
{% set existing_columns = adapter.get_columns_in_relation(this) | map(attribute='name') | map('lower') | list %}
{% if 'goals_penalty' in existing_columns %}
{% set cleaned_columns_present = run_query(
    'select countif(goals_penalty is not null) > 0 from ' ~ this
).columns[0].values()[0] %}
{% else %}
{% set cleaned_columns_present = false %}
{% endif %}
{% endif %}

with base as (
    select * from {{ ref('base_apif__fixture_players') }}
),

src as (
    select *
    from base
    {% if is_incremental() and cleaned_columns_present %}
    -- NULL-safe high-water mark: an empty target makes max() NULL and `x > NULL` is
    -- never true, which would trap the table empty forever (see fact-not-empty test).
    -- Coalescing to the epoch lets an empty/zeroed table self-heal on the next run.
    where
        base.raw_ingested_at > (
            select coalesce(max(tgt.raw_ingested_at), timestamp('1970-01-01'))
            from {{ this }} as tgt
        )
    {% endif %}
)

select
    {{ dbt_utils.generate_surrogate_key(['fixture_id', 'league_code', 'team_id', 'player_id']) }}
        as fixture_player_stat_sk,
    cast(fixture_id as int64) as fixture_sk,
    cast(team_id as int64) as team_sk,
    cast(player_id as int64) as player_sk,
    league_code,
    fixture_id as fixture_api_id,
    team_id as team_api_id,
    player_id as player_api_id,
    minutes,
    shirt_number,
    position_code,
    is_captain,
    is_substitute,
    coalesce(minutes, 0) > 0 and not coalesce(is_substitute, false) as is_starter,
    offsides,
    shots,
    shots_on_target,
    goals,
    goals_penalty,
    goals_against,
    assists,
    saves,
    passes,
    passes_key,
    passes_accurate,
    tackles,
    blocks,
    interceptions,
    duels,
    duels_won,
    dribbles,
    dribbles_success,
    dribbles_against,
    fouls,
    fouls_against,
    cards_yellow,
    cards_red,
    penalties_won,
    penalties_committed,
    penalties_scored,
    penalties_missed,
    penalties_saved,
    src.raw_ingested_at
from src
