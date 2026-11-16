{#
  In a match whose line-up is confirmed or researched, every player on a team sheet appears in
  mart_player_fixture_stats under the team that sheet gives him, and under no other team. Returns one
  row per player row of the mart whose team differs from his sheet's.
#}
{{ config(store_failures = true, severity = 'error') }}

with sheets as (
    select
        fixture_sk,
        team_sk,
        player_sk,
        lineup_state
    from {{ ref('fct_fixture_lineup') }}
    where lineup_state in ('confirmed', 'researched')
),

player_rows as (
    select
        fixture_sk,
        team_sk,
        player_sk,
        team_name,
        player_name
    from {{ ref('mart_player_fixture_stats') }}
)

select
    player_rows.fixture_sk,
    player_rows.player_sk,
    player_rows.player_name,
    sheets.lineup_state,
    sheets.team_sk as sheet_team_sk,
    player_rows.team_sk as shown_team_sk,
    player_rows.team_name as shown_team_name
from player_rows
inner join sheets
    on
        player_rows.fixture_sk = sheets.fixture_sk
        and player_rows.player_sk = sheets.player_sk
where player_rows.team_sk != sheets.team_sk
