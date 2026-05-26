{{ config(materialized='table') }}

{#
    Per-player, per-season rollup. Joins fct_fixture_player_stats to fct_fixture
    to resolve the season_sk and filter to finished matches. A player who moves
    clubs mid-season produces a single row per season; team attribution for a
    specific fixture lives in fct_fixture_player_stats.
#}

with fct_fixture as (
    select * from {{ ref('fct_fixture') }}
),

fct_fixture_player_stats as (
    select * from {{ ref('fct_fixture_player_stats') }}
),

dim_player as (
    select * from {{ ref('dim_player') }}
),

finished as (
    select
        fixture_sk,
        league_sk,
        season_sk,
        season_api_year
    from fct_fixture
    where status_short in ('FT', 'AET', 'PEN')
),

per_fixture as (
    select
        fps.player_sk,
        fps.league_code,
        f.league_sk,
        f.season_sk,
        f.season_api_year,
        fps.minutes_played,
        fps.is_starter,
        fps.is_substitute,
        fps.goals_total,
        fps.goals_assists,
        fps.shots_total,
        fps.shots_on,
        fps.passes_key,
        fps.passes_accuracy_percent,
        fps.cards_yellow,
        fps.cards_red,
        fps.rating
    from fct_fixture_player_stats as fps
    inner join finished as f on fps.fixture_sk = f.fixture_sk
),

agg as (
    select
        player_sk,
        league_sk,
        season_sk,
        league_code,
        season_api_year,
        count(*) as appearances,
        countif(is_starter) as starts,
        countif(coalesce(is_substitute, false)) as substitute_appearances,
        sum(coalesce(minutes_played, 0)) as minutes,
        sum(coalesce(goals_total, 0)) as goals,
        sum(coalesce(goals_assists, 0)) as assists,
        sum(coalesce(shots_total, 0)) as shots,
        sum(coalesce(shots_on, 0)) as shots_on_target,
        sum(coalesce(passes_key, 0)) as key_passes,
        avg(passes_accuracy_percent) as pass_accuracy_avg_percent,
        avg(rating) as rating_avg,
        sum(coalesce(cards_yellow, 0)) as yellow_cards,
        sum(coalesce(cards_red, 0)) as red_cards
    from per_fixture
    group by
        player_sk,
        league_sk,
        season_sk,
        league_code,
        season_api_year
)

select
    {{ dbt_utils.generate_surrogate_key(['agg.player_sk', 'agg.season_sk']) }} as player_season_sk,
    agg.player_sk,
    agg.season_sk,
    agg.league_sk,
    agg.league_code,
    agg.season_api_year,
    p.player_name,
    p.player_first_name,
    p.player_last_name,
    p.player_nationality,
    p.player_birth_date,
    agg.appearances,
    agg.starts,
    agg.substitute_appearances,
    agg.minutes,
    agg.goals,
    agg.assists,
    agg.shots,
    agg.shots_on_target,
    agg.key_passes,
    agg.pass_accuracy_avg_percent,
    agg.rating_avg,
    agg.yellow_cards,
    agg.red_cards
from agg
left join dim_player as p on agg.player_sk = p.player_sk
