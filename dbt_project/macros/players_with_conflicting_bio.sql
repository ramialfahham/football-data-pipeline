{#
  The players whose newest delivery of a bio field holds two real values, read from
  stg_apif__players alone: one row per player_api_id. `value` is the SQL of the field as base
  reads it, over the staged columns birth_date, nationality and raw_ingested_at. The tests use this
  to find a conflict without reading the flag that base_apif__players sets for it.
#}
{% macro players_with_conflicting_bio(value) -%}
select distinct player_api_id
from (
    select
        season_row.raw_ingested_at,
        {{ season_player_id(
            'safe_cast(season_row.player_id as int64)', 'season_row.league_code', 'season_row.season_year',
            'season_row.team_id'
        ) }} as player_api_id,
        {{ value }} as field_value
    from {{ ref('stg_apif__players') }} as season_row
    where season_row.player_id is not null
)
where field_value is not null
qualify
    raw_ingested_at = max(raw_ingested_at) over (partition by player_api_id)
    and count(distinct field_value) over (partition by player_api_id, raw_ingested_at) > 1
{%- endmacro %}
