# Task contract — incomplete team-feed data → NULL (team-feed stats only)

> CPO-directed, 2026-06-25. Brings the TEAM-FEED stats metrics into compliance with the
> universal "incomplete data → NULL" rule: a team-feed stat metric is "—" (NULL) unless every
> game in its window carries that stat. Two source-of-record findings reshaped the original
> spec (both proven from the warehouse, recorded in escalations.log):
>   1. PLAYER stat nulls mean ZERO, not missing (95.88% scoreline reconciliation) → the player
>      models are CORRECT as-is (coalesce-to-0); the player side is DROPPED. CPO: "for player
>      treat NULL as zero is correct. Do it."
>   2. Missing PLAYER data must NOT affect TEAM stats (CPO, 2026-06-25). Team metrics split by
>      source: team-feed stats (shots/passes/corners/saves) gate on team-feed coverage; the
>      player-DERIVED team metrics (tackles/key_passes/duels) are player data and keep their
>      current average-over-covered behaviour — a player-data hole never blanks a team stat.
> So this task is TEAM-FEED ONLY. See docs/working_agreement.md §2/§7/§10/§11.

objective: >
  Replace the #320 "average over the covered games" behaviour with a coverage gate that NULLs a
  TEAM-FEED stat metric whenever any game in its window is missing that stat (reverse #320, CPO Q2).
  The reference is the existing finishing_efficiency CASE: `when <coverage_count> < <window_games>
  then null … else <safe_divide / sum>`. Each metric gates on ITS OWN team-feed coverage bucket:
  shots/passes/corners/danger-zone → team-stat coverage (games_with_team_stats); shots_on_goal →
  sot coverage (games_with_sot_stats); opponent corners → opp coverage (games_with_opp_stats);
  goalkeeper saves → save coverage (games_with_save_stats, NEW). Scoreline metrics (goals/against,
  points, W-D-L, clean sheets) are always covered → never gated. Player-DERIVED team metrics
  (key_passes/tackles/interceptions/blocks/defensive_actions/duels/duels_won_pct) are LEFT UNCHANGED
  (player data — CPO ruling 2; keep average-over-player-covered). All individual player models are
  LEFT UNCHANGED (null=zero is correct).
refs: >
  CPO rule LOCKED 2026-06-25 + the two source-of-record rulings (escalations.log 2026-06-25):
  player null=zero (drop player side) and "missing player stats must not affect team stats"
  (team-feed only). Q2 = reverse #320 (AskUserQuestion 2026-06-25). The finishing_efficiency CASE
  (int_team_season__metrics / mart_momentum__team / mart_season_record__team, #506/#569) is the
  template. CLAUDE.md: DQ non-negotiable; live MVP must not break (a metric showing "—" is the
  intended product behaviour — the export already renders NULL as "—" for finishing_efficiency).

scope_paths:
  - .claude/task/**
  - .claude/active_work.md
  # --- TEAM builders (unguarded): add the missing save-coverage count to OUTPUT ---
  - dbt_project/models/4_intermediate/shared/int_momentum__team.sql
  - dbt_project/models/4_intermediate/shared/int_season_record__team.sql
  # --- TEAM season model (self-contained): team-feed coverage inline, gate team-feed metrics ---
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics.sql
  # --- TEAM marts: gate each team-feed rate (not just divide); leave player-derived untouched ---
  - dbt_project/models/5_marts/shared/mart_momentum__team.sql
  - dbt_project/models/5_marts/shared/mart_season_record__team.sql
  # --- schema docs for the touched models (document the new games_with_save_stats column;
  #     the existing range tests already cover the gated ratios with NULL tolerance, so no test
  #     additions are needed — verified at build 2026-06-25) ---
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/5_marts/shared/shared.yml

# EXPLICITLY OUT OF SCOPE:
#   - ALL player models (int_player_season__metrics, int_player_season_position__metrics,
#     int_momentum__player, mart_momentum__player) and the player downstream — player null=zero is
#     correct, proven (escalations.log 2026-06-25). NO player edits.
#   - the player-DERIVED team metrics (key_passes/tackles/interceptions/blocks/defensive_actions/
#     duels/duels_won_pct in the team marts + int_team_season__metrics) — player-sourced; LEFT on
#     average-over-covered (CPO: missing player stats must not affect team stats).
#   - metric_catalogue.csv — no metric added/redefined; only NULL behaviour. football-analytics
#     reviewer NOT required.
#   - assert_no_uncatalogued_season_metric.sql (no-drift guard) — UNTOUCHED. int_team_season__metrics
#     outputs NO new columns (team-feed coverage computed inline in the CTE, consumed in the same
#     model's final SELECT). Verified by build.
#   - downstream team consumers (mart_team_profile, mart_team_season, int_competition_benchmarks__team,
#     mart_competition_benchmarks__team, mart_matchday_insights, mart_team_season_insights) — INHERIT
#     the NULLs (pure passthrough / no re-derivation, verified). No edits.
#   - atom / staging / base / core — unchanged.

impact_map: >
  WRITERS (edited — each team-feed metric gated against its own team-feed coverage; scoreline +
  player-derived never gated by this task):
    - int_momentum__team (builder, last_5/tournament window): ADD games_with_save_stats =
      countif(goalkeeper_saves is not null) to OUTPUT (the only team-feed coverage count missing;
      games_with_team_stats / games_with_sot_stats / games_with_opp_stats already present). No gating
      here (builder emits raw sums + counts).
    - int_season_record__team (builder, cumulative): ADD cumulative games_with_save_stats =
      sum(case when goalkeeper_saves is not null then 1 else 0 end) over w.
    - int_team_season__metrics (full-season, self-contained): compute team-stat / opp / save coverage
      counts INLINE in aggregated_season (sot coverage already there as stat_coverage_season_games),
      then GATE the team-feed outputs — the per-match rates (shots_per_match_season,
      passes_per_match_season, corner_kicks_per_match_season, corners_conceded_per_match_season,
      shots_on_goal_per_match_season), the ratios (shot_share_season, danger_zone_ratio_season,
      shot_accuracy_season, pass_accuracy_season, save_ratio_season), AND the team-feed stat-count
      totals shown on the live team-season site (total_shots_sum_season, opponent_total_shots_sum_season,
      shots_inside_box_sum_season, shots_on_goal_sum_season, corner_kicks_sum_season,
      opponent_corner_kicks_sum_season, passes_accurate_sum_season, passes_total_sum_season,
      goalkeeper_saves_sum_season). finishing_efficiency_season already gated. The player-derived
      per-match rates (key_passes/duels/defensive_actions/tackles/interceptions/blocks_per_match_season,
      duels_won_pct_season) are LEFT unchanged. Scoreline rates (points_capture, goals_per_match,
      goals_against_per_match, clean_sheets) unchanged.
    - mart_momentum__team + mart_season_record__team: GATE each team-feed rate — NULL when its
      coverage count < the window total (games_in_window / games_played): shots_per_match,
      shot_accuracy, danger_zone_ratio, shots_on_*_per_match, passes_per_match, pass_accuracy,
      corner_kicks_per_match, corners_conceded_per_match, save_ratio (on the new games_with_save_stats).
      finishing already gated. key_passes/tackles/interceptions/blocks/defensive_actions/
      duels_per_match + duels_won_pct LEFT unchanged (player-derived). goals_per_match /
      goals_against_per_match / clean_sheets / points_won / W-D-L = scoreline → unchanged.
  DOWNSTREAM (dbt ls --select int_team_season__metrics+ mart_momentum__team+ mart_season_record__team+
    --resource-type model, PASTED 2026-06-25): int_competition_benchmarks__team,
    mart_competition_benchmarks__team, mart_matchday_insights, mart_team_profile, mart_team_season,
    mart_team_season_insights. ALL inherit — verified no re-derivation: mart_matchday_insights /
    mart_team_season_insights SELECT the rate/count columns straight through; the benchmark uses
    `where metric_value is not null`. NO downstream edit.
  LAYER_RULES: check_layer_contract (no new staging dir — N/A); check_registry_var_sync (N/A); base
    models stay views; assert_no_uncatalogued_season_metric UNTOUCHED (no new output columns on the
    season model). No atom/staging/base/core change.
  DEPLOY_ORDER: one dbt build rebuilds the writers + their downstream (incl. the two live marts) in a
    single run — no cross-deploy window. Runs in ci-data-build on the shared BQ; do NOT local-build.
  BLAST_RADIUS (measured from the live warehouse, 2026-06-25): the change flips PARTIALLY-covered
    windows from a shown value to "—"; fully-covered and already-zero-coverage windows are unchanged.
    LIVE season page (mart_team_season_insights, 2400 latest-season teams): ~12% (296) flip their
    team-feed shot/passes/corners rates + totals to "—" (47.5% already "—" today = no feed; 40% fully
    covered = unchanged). LIVE match preview (mart_matchday_insights last-5 form): ~17% of windows
    flip. All flips are genuine team-feed gaps — player data is quarantined. Scoreline + player-derived
    metrics unchanged. Before/after deltas captured on both live marts per done_when.

decisions_taken: >
  Q2 = REVERSE #320 for TEAM-FEED rates (AskUserQuestion 2026-06-25): NULL on partial team-feed
  coverage instead of averaging over the covered subset; a deliberate, recorded reversal. Q1 =
  include counts (so the team-feed stat-count totals gate too). Player side DROPPED — player null=zero
  proven correct (escalations.log 2026-06-25), no player edits. Player-DERIVED team metrics LEFT on
  average-over-covered — CPO: "missing player stats must not affect the team stats" — so the player-
  data gap is quarantined to those player-sourced metrics and never blanks a team-feed stat. DESIGN:
  each team-feed metric gates against its own coverage bucket (team-stat / sot / opp / save), modelled
  on the finishing CASE; coverage computed inline in the season model (no new output columns → no-drift
  guard untouched), output by the momentum/record builders (unguarded) for their marts to consume. No
  metric created/redefined → catalogue untouched, football-analytics review not required.

decisions_reserved:
  - D1 (DQ assertion in done_when): the invariant is enforced by construction (the CASE gate); a test
    that re-derives coverage to assert NULL would be CIRCULAR (cf. the 2026-06-17 near-circular test
    FAIL). Satisfy DQ via non-circular range tests (ratios in [0,1], rates/counts >= 0) on the gated
    team-feed metrics; do not add a circular assertion unilaterally. Flag if a stronger guard is wanted.
  - D2 (partial-coverage policy — A/B/C): the CPO chose A (strict NULL / reverse #320) for team-feed
    rates; the measured live impact is ~12% season / ~17% form flips (recorded blast_radius). B (keep
    average-over-covered + caption) and C (coverage threshold) were presented and not chosen. Recorded
    so the decision is locatable; not re-opened.

done_when:
  - Every TEAM-FEED stat metric (momentum, season-record, full-season) is NULL when its team-feed input
    is not present in all window games; player-derived team metrics + individual player metrics + scoreline
    metrics unchanged. int_momentum__team / int_season_record__team carry games_with_save_stats; the team
    marts + season model GATE the team-feed metrics (not just divide).
  - `.venv/Scripts/dbt parse` + `dbt compile` clean (--project-dir dbt_project --profiles-dir "$HOME/.dbt");
    `.venv/Scripts/sqlfluff lint` clean on the touched SQL; the no-drift guard + existing range/non-negative
    tests pass; any added range tests pass. NO local full BQ build (shared warehouse → ci-data-build).
  - Before/after deltas recorded on mart_matchday_insights + mart_team_season_insights (old vs new),
    proving the team-feed stats that flip are exactly the partial-coverage ones and scoreline +
    player-derived metrics are unchanged.
  - G3 review (Scope-Auditor + analytics-engineer-reviewer; football-analytics NOT required); PR opened;
    CPO merges (never self-merge).

amendments:
  - 2026-06-25: + dbt_project/models/4_intermediate/shared/int_season_record.yml — authority: the
    contract's CPO-approved scope category "schema docs for the touched models" (scope_paths above).
    int_season_record.yml is the schema doc for the touched builder int_season_record__team, omitted
    from the explicit scope list by oversight; surfaced by the scope-auditor's blinded FAIL. content:
    document the new games_with_save_stats output column alongside the sibling coverage columns
    (mirrors the int_momentum.yml edit). No new logic, no metric change.
