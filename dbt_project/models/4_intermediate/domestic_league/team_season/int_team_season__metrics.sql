{{ config(materialized='table') }}

{#
  Per (league_code, season_api_year, team_sk) advanced metrics over all finished legs in that season.
  Full window, no five-game cap. Reads from int_legs__team_match (the shared building-block leg,
  cross-competition by design — group by league_code naturally scopes to one competition) plus
  int_legs__team_from_players for the player-derived team metrics (GAP-13 — the same five
  metrics the window marts carry; they inherit player-stat coverage gaps and divide over
  player_stat_coverage_season_games, the same-window rule).
  Grain: (league_code, season_api_year, team_sk). mart_team_season_insights keeps latest season per league.

  Note: the original per-match rates divide by season_games_played (pre-coverage-rule
  convention, consumed by the live MVP) — left unchanged deliberately; see GAP-17.
#}

with legs as (
    select * from {{ ref('int_legs__team_match') }}
),

player_legs as (
    select * from {{ ref('int_legs__team_from_players') }}
),

joined as (
    select
        l.*,
        pl.key_passes,
        pl.tackles,
        pl.interceptions,
        pl.blocks,
        pl.duels_total,
        pl.duels_won,
        pl.fixture_sk is not null as has_player_stats
    from legs as l
    left join player_legs as pl
        on
            l.fixture_sk = pl.fixture_sk
            and l.team_sk = pl.team_sk
),

aggregated_season as (
    select
        league_code,
        season_api_year,
        team_sk,
        any_value(league_sk) as league_sk,
        any_value(season_sk) as season_sk,
        count(distinct fixture_sk) as season_games_played,
        count(distinct round_name) as season_matchdays_used,
        count(distinct case when shots_on_goal is not null then fixture_sk end)
            as stat_coverage_season_games,
        count(distinct case when has_player_stats then fixture_sk end)
            as player_stat_coverage_season_games,
        sum(
            case upper(trim(result))
                when 'W' then 3
                when 'D' then 1
                else 0
            end
        ) as points_won_sum_season,
        countif(upper(trim(result)) = 'W') as wins_sum_season,
        countif(upper(trim(result)) = 'D') as draws_sum_season,
        countif(upper(trim(result)) = 'L') as losses_sum_season,
        sum(goals_for) as goals_for_sum_season,
        sum(goals_against) as goals_against_sum_season,
        -- open-play goal components (CPO Option A): goals_open_play = goals_for − goals_penalty
        -- − goals_own. Event-derived components subtracted from the authoritative scoreline.
        sum(goals_penalty) as goals_penalty_sum_season,
        sum(goals_own) as goals_own_sum_season,
        sum(shots_total) as total_shots_sum_season,
        sum(opponent_shots_total) as opponent_total_shots_sum_season,
        sum(shots_inside_box) as shots_inside_box_sum_season,
        sum(shots_on_goal) as shots_on_goal_sum_season,
        sum(corner_kicks) as corner_kicks_sum_season,
        sum(opponent_corner_kicks) as opponent_corner_kicks_sum_season,
        sum(passes_accurate) as passes_accurate_sum_season,
        sum(passes_total) as passes_total_sum_season,
        sum(goalkeeper_saves) as goalkeeper_saves_sum_season,
        -- player-derived sums (GAP-13; null when no player-stat coverage)
        sum(key_passes) as key_passes_sum_season,
        sum(tackles) as tackles_sum_season,
        sum(interceptions) as interceptions_sum_season,
        sum(blocks) as blocks_sum_season,
        sum(duels_total) as duels_total_sum_season,
        sum(duels_won) as duels_won_sum_season,
        countif(goals_against = 0) as clean_sheets_count_season
    from joined
    group by league_code, season_api_year, team_sk
)

select
    {{ dbt_utils.generate_surrogate_key(['team_sk', 'season_sk']) }} as team_season_sk,
    team_sk,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    season_games_played,
    season_matchdays_used,
    stat_coverage_season_games,
    player_stat_coverage_season_games,
    points_won_sum_season,
    wins_sum_season,
    draws_sum_season,
    losses_sum_season,
    clean_sheets_count_season as clean_sheets_sum_season,
    goals_for_sum_season,
    goals_against_sum_season,
    -- open-play goal components as season-total counts (catalogued metrics; CPO Option A)
    goals_penalty_sum_season as goals_penalty_season,
    goals_own_sum_season as goals_own_season,
    goals_for_sum_season - goals_penalty_sum_season - goals_own_sum_season
        as goals_open_play_season,
    total_shots_sum_season,
    opponent_total_shots_sum_season,
    shots_inside_box_sum_season,
    shots_on_goal_sum_season,
    corner_kicks_sum_season,
    opponent_corner_kicks_sum_season,
    passes_accurate_sum_season,
    passes_total_sum_season,
    goalkeeper_saves_sum_season,
    safe_divide(points_won_sum_season, 3 * season_games_played) as points_capture_season,
    safe_divide(goals_for_sum_season, season_games_played) as goals_per_match_season,
    safe_divide(goals_against_sum_season, season_games_played) as goals_against_per_match_season,
    safe_divide(total_shots_sum_season, season_games_played) as shots_per_match_season,
    safe_divide(
        total_shots_sum_season,
        nullif(total_shots_sum_season + opponent_total_shots_sum_season, 0)
    ) as shot_share_season,
    safe_divide(shots_inside_box_sum_season, total_shots_sum_season) as danger_zone_ratio_season,
    safe_divide(shots_on_goal_sum_season, total_shots_sum_season) as shot_accuracy_season,
    -- finishing efficiency (CPO Option A): open-play conversion =
    -- (goals_for − goals_penalty − goals_own) / shots_on_goal. NULL ('—') unless the season is
    -- fully shot-covered AND the numerator is valid [0, shots_on_goal] — never partial, never >100%.
    case
        when stat_coverage_season_games < season_games_played then null
        when (goals_for_sum_season - goals_penalty_sum_season - goals_own_sum_season) < 0 then null
        when
            (goals_for_sum_season - goals_penalty_sum_season - goals_own_sum_season)
            > shots_on_goal_sum_season then null
        else safe_divide(
            goals_for_sum_season - goals_penalty_sum_season - goals_own_sum_season,
            shots_on_goal_sum_season
        )
    end as finishing_efficiency_season,
    safe_divide(passes_accurate_sum_season, passes_total_sum_season) as pass_accuracy_season,
    safe_divide(passes_total_sum_season, season_games_played) as passes_per_match_season,
    safe_divide(corner_kicks_sum_season, season_games_played) as corner_kicks_per_match_season,
    safe_divide(opponent_corner_kicks_sum_season, season_games_played) as corners_conceded_per_match_season,
    safe_divide(
        goalkeeper_saves_sum_season,
        nullif(goalkeeper_saves_sum_season + goals_against_sum_season, 0)
    ) as save_ratio_season,
    -- GAP-13: the five locked-contract season variants. Coverage denominators
    -- (the window marts' same-window rule): shots over stat-covered games,
    -- player-derived over player-stat-covered games.
    safe_divide(shots_on_goal_sum_season, stat_coverage_season_games)
        as shots_on_target_per_match_season,
    safe_divide(key_passes_sum_season, player_stat_coverage_season_games)
        as key_passes_per_match_season,
    safe_divide(duels_total_sum_season, player_stat_coverage_season_games)
        as duels_per_match_season,
    safe_divide(duels_won_sum_season, duels_total_sum_season)
        as duels_won_pct_season,
    safe_divide(
        tackles_sum_season + interceptions_sum_season + blocks_sum_season,
        player_stat_coverage_season_games
    ) as defensive_actions_per_match_season,
    -- GAP-13 follow-on (benchmark): the catalogued team metrics the season model still lacked.
    -- clean_sheets is benchmarked as a RATE (the "x/y" count display lives on mart_team_season).
    safe_divide(clean_sheets_count_season, season_games_played) as clean_sheets_season,
    safe_divide(tackles_sum_season, player_stat_coverage_season_games) as tackles_per_match_season,
    safe_divide(interceptions_sum_season, player_stat_coverage_season_games)
        as interceptions_per_match_season,
    safe_divide(blocks_sum_season, player_stat_coverage_season_games) as blocks_per_match_season
from aggregated_season
