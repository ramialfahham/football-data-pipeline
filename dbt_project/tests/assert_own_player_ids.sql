{#
  A player the provider holds under the placeholder 0 gets the warehouse's own id: a negative id
  that names one researched player, sourced, and makes him a player like any other. One failing row
  per broken assign_in_fixture row: its id is not negative, its source is not https URLs separated
  by a space, the match's sheet and stat lines do not carry the id at that team, or dim_player has no
  row for it. Named case: Víctor Rodríguez (-1), Navalcarnero shirt 5 in fixture 1644363, has a
  stat line and his yellow card.
#}
{{ config(store_failures = true, severity = 'error') }}

with own_ids as (
    select
        correct_player_api_id as player_id,
        fixture_id,
        team_id,
        source
    from {{ ref('player_id_overrides') }}
    where mode = 'assign_in_fixture'
),

match_players as (
    select
        fixture_id,
        team_id,
        player_id
    from {{ ref('base_apif__lineups') }}
    union distinct
    select
        fixture_id,
        team_id,
        player_id
    from {{ ref('base_apif__fixture_players') }}
),

checked as (
    select
        o.player_id,
        o.fixture_id,
        o.player_id >= 0 as is_not_negative,
        not regexp_contains(coalesce(o.source, ''), r'^https://\S+( https://\S+)*$') as is_not_sourced,
        m.player_id is null as is_off_the_match,
        d.player_api_id is null as is_not_a_player
    from own_ids as o
    left join match_players as m
        on o.fixture_id = m.fixture_id and o.team_id = m.team_id and o.player_id = m.player_id
    left join {{ ref('dim_player') }} as d
        on o.player_id = d.player_api_id
),

named_case as (
    select countif(minutes > 0 and cards_yellow = 1) as rows_found
    from {{ ref('fct_fixture_player_stats') }}
    where player_sk = -1 and fixture_sk = 1644363
)

select
    player_id,
    fixture_id,
    case
        when is_not_negative then 'own id is not negative'
        when is_not_sourced then 'not sourced'
        when is_off_the_match then 'not on the match sheet or stat lines'
        else 'not in dim_player'
    end as failure
from checked
where is_not_negative or is_not_sourced or is_off_the_match or is_not_a_player

union all

select
    -1 as player_id,
    1644363 as fixture_id,
    'named case: Víctor Rodríguez has no stat line with his yellow card' as failure
from named_case
where rows_found = 0
