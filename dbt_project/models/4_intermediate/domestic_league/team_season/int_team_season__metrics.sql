{#
  Whole-season team rollup — the FINAL-ROW PROJECTION of int_team_season__metrics_cumulative,
  where the catalogue formulas are applied at every matchday. Per (league_code, season_api_year,
  team_sk): the last cumulative row of the season (max match_number) + the whole-season-only
  extras — team_season_sk and season_matchdays_used — re-attached here. mart_team_season_insights
  exposes only the latest season_api_year per league_code.

  A team-season whose results disagree with the provider's standings (team_seasons_off_standings)
  has every season value blank and counts_withheld true: the results or the standings are wrong and
  nothing here says which. The keys and entity_type stay, so the team and the row stay.

  Grain: (team_sk, season_sk).
#}

with cumulative as (
    select * from {{ ref('int_team_season__metrics_cumulative') }}
),

-- the season's final cumulative row = its greatest match_number (= latest kickoff, since
-- match_number is row_number over kickoff asc; the whole-season totals live here).
season_final as (
    select * from cumulative
    qualify row_number() over (
        partition by team_sk, league_code, season_api_year
        order by match_number desc
    ) = 1
),

-- distinct matchdays used across the whole season (round_name lives on the leg, not the
-- cumulative row) — a whole-season-only field, so it is attached here, not in the base model.
matchdays as (
    select
        team_sk,
        league_code,
        season_api_year,
        count(distinct round_name) as season_matchdays_used
    from {{ ref('int_legs__team_match') }}
    group by team_sk, league_code, season_api_year
),

season_counts as (
    select
        team_sk,
        season_sk,
        season_games_played,
        wins_sum_season as wins,
        draws_sum_season as draws,
        losses_sum_season as losses,
        goals,
        goals_against,
        points_won
    from season_final
),

off_standings as (
    {{ team_seasons_off_standings('season_counts', ref('fct_standings'), ref('standings_points_adjustments')) }}
),

withheld as (
    select distinct
        team_sk,
        season_sk
    from off_standings
),

season_row as (
    select
        {{ dbt_utils.generate_surrogate_key(['sf.team_sk', 'sf.season_sk']) }} as team_season_sk,
        -- everything from the final cumulative row except its per-matchday grain key; the
        -- _sum_season / season_games_played names denote the whole season (final matchday).
        sf.* except (match_number),
        md.season_matchdays_used,
        w.team_sk is not null as counts_withheld
    from season_final as sf
    left join matchdays as md
        on
            sf.team_sk = md.team_sk
            and sf.league_code = md.league_code
            and sf.season_api_year = md.season_api_year
    left join withheld as w
        on
            sf.team_sk = w.team_sk
            and sf.season_sk = w.season_sk
)

select
    * replace (
        if(counts_withheld, null, season_games_played) as season_games_played,
        if(counts_withheld, null, stat_coverage_season_games) as stat_coverage_season_games,
        if(counts_withheld, null, player_stat_coverage_season_games) as player_stat_coverage_season_games,
        if(counts_withheld, null, games_with_team_stats) as games_with_team_stats,
        if(counts_withheld, null, games_expecting_team_stats) as games_expecting_team_stats,
        if(counts_withheld, null, wins_sum_season) as wins_sum_season,
        if(counts_withheld, null, draws_sum_season) as draws_sum_season,
        if(counts_withheld, null, losses_sum_season) as losses_sum_season,
        if(counts_withheld, null, total_shots_sum_season) as total_shots_sum_season,
        if(counts_withheld, null, opponent_total_shots_sum_season) as opponent_total_shots_sum_season,
        if(counts_withheld, null, shots_on_goal_sum_season) as shots_on_goal_sum_season,
        if(counts_withheld, null, opponent_corner_kicks_sum_season) as opponent_corner_kicks_sum_season,
        if(counts_withheld, null, passes_accurate_sum_season) as passes_accurate_sum_season,
        if(counts_withheld, null, passes_total_sum_season) as passes_total_sum_season,
        if(counts_withheld, null, points_won) as points_won,
        if(counts_withheld, null, goals) as goals,
        if(counts_withheld, null, goals_against) as goals_against,
        if(counts_withheld, null, clean_sheets) as clean_sheets,
        if(counts_withheld, null, goals_penalty) as goals_penalty,
        if(counts_withheld, null, goals_own) as goals_own,
        if(counts_withheld, null, goals_open_play) as goals_open_play,
        if(counts_withheld, null, corners) as corners,
        if(counts_withheld, null, saves) as saves,
        if(counts_withheld, null, shots_inside_box) as shots_inside_box,
        if(counts_withheld, null, cards_yellow) as cards_yellow,
        if(counts_withheld, null, cards_red) as cards_red,
        if(counts_withheld, null, goals_per_match) as goals_per_match,
        if(counts_withheld, null, goals_against_per_match) as goals_against_per_match,
        if(counts_withheld, null, shots_per_match) as shots_per_match,
        if(counts_withheld, null, shots_on_goal_pct) as shots_on_goal_pct,
        if(counts_withheld, null, shots_inside_box_pct) as shots_inside_box_pct,
        if(counts_withheld, null, shots_on_goal_per_match) as shots_on_goal_per_match,
        if(counts_withheld, null, finishing_efficiency_pct) as finishing_efficiency_pct,
        if(counts_withheld, null, passes_per_match) as passes_per_match,
        if(counts_withheld, null, passes_accuracy_pct) as passes_accuracy_pct,
        if(counts_withheld, null, corners_per_match) as corners_per_match,
        if(counts_withheld, null, corners_against_per_match) as corners_against_per_match,
        if(counts_withheld, null, saves_pct) as saves_pct,
        if(counts_withheld, null, passes_key_per_match) as passes_key_per_match,
        if(counts_withheld, null, tackles_per_match) as tackles_per_match,
        if(counts_withheld, null, interceptions_per_match) as interceptions_per_match,
        if(counts_withheld, null, blocks_per_match) as blocks_per_match,
        if(counts_withheld, null, defensive_actions_per_match) as defensive_actions_per_match,
        if(counts_withheld, null, duels_per_match) as duels_per_match,
        if(counts_withheld, null, duels_won_pct) as duels_won_pct,
        if(counts_withheld, null, shots_on_goal_against_per_match) as shots_on_goal_against_per_match,
        if(counts_withheld, null, shots_off_target_per_match) as shots_off_target_per_match,
        if(counts_withheld, null, shots_blocked_per_match) as shots_blocked_per_match,
        if(counts_withheld, null, shots_inside_box_per_match) as shots_inside_box_per_match,
        if(counts_withheld, null, passes_accurate_per_match) as passes_accurate_per_match,
        if(counts_withheld, null, passes_share_pct) as passes_share_pct,
        if(counts_withheld, null, dribbles_attempts_per_match) as dribbles_attempts_per_match,
        if(counts_withheld, null, dribbles_success_per_match) as dribbles_success_per_match,
        if(counts_withheld, null, dribbles_success_pct) as dribbles_success_pct,
        if(counts_withheld, null, duels_won_per_match) as duels_won_per_match,
        if(counts_withheld, null, saves_per_match) as saves_per_match,
        if(counts_withheld, null, free_kicks_per_match) as free_kicks_per_match,
        if(counts_withheld, null, fouls_per_match) as fouls_per_match,
        if(counts_withheld, null, offsides_per_match) as offsides_per_match,
        if(counts_withheld, null, cards_yellow_per_match) as cards_yellow_per_match,
        if(counts_withheld, null, cards_red_per_match) as cards_red_per_match,
        if(counts_withheld, null, clean_sheets_pct) as clean_sheets_pct,
        if(counts_withheld, null, points_capture_pct) as points_capture_pct,
        if(counts_withheld, null, shots_share_pct) as shots_share_pct,
        if(counts_withheld, null, shots_on_goal_difference_per_match) as shots_on_goal_difference_per_match,
        if(counts_withheld, null, season_matchdays_used) as season_matchdays_used
    )
from season_row
