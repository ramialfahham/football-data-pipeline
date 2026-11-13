{#
  A provider team sheet that names two people under one player id cannot say which of them played,
  so its match's line-up is not confirmed. Reads the provider's latest sheet of each team from
  staging and returns each such match that base_apif__lineups confirms.
#}
{{ config(store_failures = true, severity = 'error') }}

with latest_sheets as (
    select
        league_code,
        fixture_id,
        team_id,
        start_xi_json,
        substitutes_json
    from {{ ref('stg_apif__lineups') }}
    where fixture_id is not null and team_id is not null
    qualify row_number() over (
        partition by league_code, fixture_id, team_id
        order by raw_ingested_at desc
    ) = 1
),

listed as (
    select
        s.league_code,
        s.fixture_id,
        s.team_id,
        {{ player_id_override("nullif(safe_cast(json_value(player_el, '$.player.id') as int64), 0)") }}
            as player_id,
        {{ decode_html_entities("json_value(player_el, '$.player.name')") }} as player_name
    from latest_sheets as s,
        unnest(array_concat(json_query_array(s.start_xi_json), json_query_array(s.substitutes_json)))
            as player_el
),

shared_id_players as (
    select
        league_code,
        fixture_id,
        team_id,
        player_id
    from listed
    where player_id is not null
    group by league_code, fixture_id, team_id, player_id
    having count(distinct player_name) > 1
),

shared_ids as (
    select distinct
        league_code,
        fixture_id
    from shared_id_players
),

confirmed as (
    select distinct
        league_code,
        fixture_id
    from {{ ref('base_apif__lineups') }}
    where lineup_state = 'confirmed'
)

select
    shared_ids.league_code,
    shared_ids.fixture_id
from shared_ids
inner join confirmed
    on
        shared_ids.league_code = confirmed.league_code
        and shared_ids.fixture_id = confirmed.fixture_id
