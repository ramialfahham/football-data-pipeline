{{ config(materialized='table') }}

{#
  Per (player, competition) CAREER rollup — the across-seasons sum of int_player_season__metrics over all
  of a player's finished seasons in a competition. One row per (player_sk, league_code): career
  appearances / goals / assists, plus the season span (first / last / count). Counts only — NO minutes
  (CPO); career-long rates are not meaningful and stay on the season views. league_sk identifies the
  competition; entity_type (club vs national) is added downstream in mart_player_career.

  Grain: (player_sk, league_code). Powers the Player Career tab.
#}

with player_seasons as (
    select * from {{ ref('int_player_season__metrics') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['player_sk', 'league_code']) }} as player_career_sk,
    player_sk,
    league_code,
    -- league_sk is 1:1 with league_code (a competition's provider id is stable); any_value keeps the
    -- group-by grain equal to the surrogate-key grain (player_sk, league_code).
    any_value(league_sk) as league_sk,
    count(distinct season_sk) as seasons_played,
    min(season_api_year) as first_season,
    max(season_api_year) as last_season,
    sum(appearances) as appearances,
    sum(goals) as goals,
    sum(assists) as assists
from player_seasons
group by player_sk, league_code
