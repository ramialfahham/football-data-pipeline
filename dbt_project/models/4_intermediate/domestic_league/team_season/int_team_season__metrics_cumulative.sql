{{ config(materialized='table') }}

{#
  Per-matchday cumulative team-season metrics — the season rate formulas applied to EVERY
  cumulative row of int_team_season_record (not just the final one). This is the single home of
  the team-season rate formulas (#500 one-aggregation philosophy):

    - int_team_season__metrics is the FINAL-ROW PROJECTION of this model (whole-season rollup) —
      byte-identical output, so every downstream consumer (mart_team_season / _insights /
      _profile / _record, the benchmark chain, deserved-vs-actual) is unchanged.
    - int_team_profile__yoy COMPOSES this model at the games-played cutoff N to align two seasons
      by matchday for ALL metrics ("this season through N vs last season through its first N").
      int_team_season_record's header keeps match_number for exactly this.

  Grain: (team_sk, league_code, season_api_year, match_number). All-competitions, like
  int_team_season__metrics (no domestic filter — the YoY consumer applies that).

  NAMING NOTE: the `_sum_season` / `season_games_played` / `stat_coverage_season_games` column
  names are inherited verbatim from the whole-season projection so the projection is a trivial
  final-row select (guaranteeing byte-identity). HERE they mean "cumulative THROUGH THIS matchday",
  not the whole season. Formulas + coverage gates are lifted verbatim from int_team_season__metrics.

  Incomplete-data → NULL (CPO 2026-06-25): a team-feed rate is NULL unless its stat covers every
  game through this matchday (games_with_* == games_played); scoreline + player-derived are not gated.
#}

with rec as (
    select * from {{ ref('int_team_season_record') }}
)

select
    team_sk,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    entity_type,
    -- the matchday cutoff key (this model's grain; the YoY alignment key). games_played is the
    -- same value carried under the season name below for the byte-identical projection.
    match_number,
    games_played as season_games_played,
    games_with_sot_stats as stat_coverage_season_games,
    games_with_player_stats as player_stat_coverage_season_games,
    games_with_team_stats,
    games_expecting_team_stats,
    -- raw cumulative counts (kept under the _sum_season names — the projection's live JSON keys)
    points_won as points_won_sum_season,
    wins as wins_sum_season,
    draws as draws_sum_season,
    losses as losses_sum_season,
    clean_sheet_games as clean_sheets_sum_season,
    goals_for as goals_for_sum_season,
    goals_against as goals_against_sum_season,
    goals_penalty,
    goals_own,
    goals_for - goals_penalty - goals_own as goals_open_play,
    -- team-feed sum columns: NULL ('—') on partial coverage through this matchday.
    case
        when games_with_team_stats < games_expecting_team_stats then null else shots_total
    end as total_shots_sum_season,
    case
        when games_with_opp_stats < games_expecting_team_stats then null else opponent_shots_total
    end as opponent_total_shots_sum_season,
    case
        when games_with_team_stats < games_expecting_team_stats then null else shots_inside_box
    end as shots_inside_box_sum_season,
    case
        when games_with_sot_stats < games_expecting_team_stats then null else shots_on_goal
    end as shots_on_goal_sum_season,
    case
        when games_with_team_stats < games_expecting_team_stats then null else corner_kicks
    end as corner_kicks_sum_season,
    case
        when games_with_opp_stats < games_expecting_team_stats then null else opponent_corner_kicks
    end as opponent_corner_kicks_sum_season,
    case
        when games_with_team_stats < games_expecting_team_stats then null else passes_accurate
    end as passes_accurate_sum_season,
    case
        when games_with_team_stats < games_expecting_team_stats then null else passes_total
    end as passes_total_sum_season,
    case
        when games_with_save_stats < games_expecting_team_stats then null else goalkeeper_saves
    end as goalkeeper_saves_sum_season,
    -- window-specific metrics (stay inline; same as the whole-season model)
    safe_divide(points_won, 3 * games_played) as points_capture_pct,
    case
        when games_with_team_stats < games_expecting_team_stats then null
        when games_with_opp_stats < games_expecting_team_stats then null
        else safe_divide(shots_total, nullif(shots_total + opponent_shots_total, 0))
    end as shots_share_pct,
    safe_divide(clean_sheet_games, games_played) as clean_sheets_pct,
    -- shared per-match / ratio formulas (plain inline SQL; catalogue-id names). Lifted verbatim
    -- from int_team_season__metrics — this model is now their single home.
    safe_divide(goals_for, games_played) as goals_per_match,
    safe_divide(goals_against, games_played) as goals_against_per_match,
    case
        when games_with_team_stats < games_expecting_team_stats then null
        else safe_divide(shots_total, games_with_team_stats)
    end as shots_per_match,
    case
        when games_with_sot_stats < games_expecting_team_stats then null
        when games_with_team_stats < games_expecting_team_stats then null
        else safe_divide(shots_on_goal, shots_total)
    end as shots_on_goal_pct,
    case
        when games_with_team_stats < games_expecting_team_stats then null
        else safe_divide(shots_inside_box, shots_total)
    end as shots_inside_box_pct,
    case
        when games_with_sot_stats < games_expecting_team_stats then null
        else safe_divide(shots_on_goal, games_with_sot_stats)
    end as shots_on_goal_per_match,
    case
        when games_with_opp_sot_stats < games_expecting_team_stats then null
        else safe_divide(opponent_shots_on_goal, games_with_opp_sot_stats)
    end as shots_on_goal_against_per_match,
    case
        when games_with_sot_stats < games_expecting_team_stats then null
        when games_with_opp_sot_stats < games_expecting_team_stats then null
        -- ⚠ NOT games_played, and not either coverage count alone. This is the one two-sided rate
        -- here: the numerator subtracts a sum over the games with OPPONENT SoT from a sum over the
        -- games with OWN SoT, so its denominator must be the games both cover.
        -- It read `games_played` until 2026-09-07, which was correct only while the gate demanded
        -- FULL coverage — both counts then equalled games_played by construction. Once awarded
        -- matches count as played, the gate demands coverage of the non-awarded games only, so
        -- games_played became one larger than the set the numerator spans and quietly diluted the
        -- rate. `least` is byte-identical to the old behaviour wherever the old gate passed, and
        -- correct where it now does not (analytics-engineer-reviewer, 2026-09-07).
        -- It matters more than the other rates: this is the regression input to
        -- int_team_season__deserved_vs_actual, so a diluted value moves a whole league-season's
        -- deserved-points fit, not one cell.
        else safe_divide(
            shots_on_goal - opponent_shots_on_goal,
            least(games_with_sot_stats, games_with_opp_sot_stats)
        )
    end as shots_on_goal_difference_per_match,
    -- ⚠ SAME-WINDOW NUMERATOR. `goals_open_play_in_sot_games` counts open-play goals only in the
    -- games whose shots-on-target the denominator also counts. The full goal sum would include an
    -- awarded result's goals — a 3-0 technical win is three real goals with no shot behind them —
    -- against a denominator that can never see them, inflating the ratio. Before awarded matches
    -- became legs the two spanned the same games and the distinction did not exist
    -- (analytics-engineer-reviewer, 2026-09-07).
    case
        when games_with_sot_stats < games_expecting_team_stats then null
        when goals_open_play_in_sot_games < 0 then null
        when goals_open_play_in_sot_games > shots_on_goal then null
        else safe_divide(goals_open_play_in_sot_games, shots_on_goal)
    end as finishing_efficiency_pct,
    case
        when games_with_team_stats < games_expecting_team_stats then null
        else safe_divide(passes_total, games_with_team_stats)
    end as passes_per_match,
    case
        when games_with_team_stats < games_expecting_team_stats then null
        else safe_divide(passes_accurate, passes_total)
    end as passes_accuracy_pct,
    case
        when games_with_team_stats < games_expecting_team_stats then null
        else safe_divide(corner_kicks, games_with_team_stats)
    end as corners_per_match,
    case
        when games_with_opp_stats < games_expecting_team_stats then null
        else safe_divide(opponent_corner_kicks, games_with_opp_stats)
    end as corners_against_per_match,
    case
        when games_with_save_stats < games_expecting_team_stats then null
        else safe_divide(
            goalkeeper_saves, goalkeeper_saves + goals_against_in_save_games
        )
    end as saves_pct,
    safe_divide(key_passes, games_with_player_stats) as passes_key_per_match,
    safe_divide(tackles, games_with_player_stats) as tackles_per_match,
    safe_divide(interceptions, games_with_player_stats)
        as interceptions_per_match,
    safe_divide(blocks, games_with_player_stats) as blocks_per_match,
    safe_divide(tackles + interceptions + blocks, games_with_player_stats)
        as defensive_actions_per_match,
    safe_divide(duels_total, games_with_player_stats) as duels_per_match,
    safe_divide(duels_won, duels_total) as duels_won_pct
from rec
