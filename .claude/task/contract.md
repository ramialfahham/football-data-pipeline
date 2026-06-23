# Task contract — player per-90 metrics + benchmark-metric classification (benchmark PR1)

objective: >
  Add the 13 per-90 player metrics (the minutes-normalised comparison layer) to the
  metric_catalogue + compute them in int_player_season__metrics; classify direction +
  interpretation for those 13 AND the 5 existing benchmark rate metrics, so the whole
  player-benchmark metric set carries good/bad semantics and auto-narrative meaning. This is
  the metric-layer foundation (PR1) for the player competition benchmark (PR2). Additive only.
refs: >
  Player competition benchmark — the per-90 vs-peers surface (content_architecture §6), the v1.x
  follow-up to the team benchmark (#511/#512). Designed + ruled live this session (2026-06-23):
  per-90 via the proper catalogue route (reverses the A1 unapproved-invention removal); the
  13-metric list CPO-confirmed; direction classified (ruling "A": classify now, like the team);
  interpretations written player-native for website auto-content generation.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/5_marts/shared/mart_player_profile.sql

impact_map: >
  writers:
    - 13 per-90 columns (goals/assists/scorer_points/shots_on_target/key_passes/dribbles_success/
      passes/tackles/interceptions/blocks/defensive_actions/duels_won/saves _per90) =
      safe_divide(count * 90, minutes) — computed ONLY in int_player_season__metrics (the canonical
      player-season model, mirroring the per-match rates in int_team_season__metrics). 13 matching
      metric_catalogue rows (entity='player'), each carrying direction + interpretation.
    - direction + interpretation also filled on the 5 existing player benchmark RATES
      (pass_accuracy_pct, duels_won_pct, dribbles_success_pct, finishing_efficiency, save_pct) —
      additive catalogue-field updates (previously empty), no formula change.
  downstream (pasted, `dbt ls --select int_player_season__metrics+`):
    - int_player_season__metrics → int_player_career__metrics, mart_leaderboards, mart_player_career,
      mart_player_profile. VERIFIED (during #506) all four use named SELECTs — the new per-90 columns
      do NOT leak; schemas/numbers unchanged. PR2 (the benchmark) is the intended consumer.
    - metric_catalogue: the direction/interpretation columns are NOT consumed by any current model
      (leaderboard/profile select named atoms, not direction); filling them is inert until PR2's
      display. accepted_values/not_null/uniqueness + assert_no_uncatalogued_season_metric apply.
  layer_rules:
    - assert_no_uncatalogued_season_metric: every metric column in int_player_season__metrics must
      have a player catalogue row (metric_id = column). The 13 new columns REQUIRE the 13 rows.
    - accepted_values: format in {integer,decimal_0,decimal_1,percent,points_fraction,count_fraction}
      → per-90 use decimal_1. direction in {higher_better,lower_better,neutral}. metric_group in the
      closed set → each per-90 inherits its base metric's group. lower_is_better not_null → false on
      all 13 (none are lower-better; neutral metrics carry false + direction=neutral, like the team).
    - metrics live in the canonical season model; PR2 references them via a macro, like
      team_benchmark_metrics() references int_team_season__metrics.
  deploy_order:
    - shared warehouse; ci-data-build rebuilds seed → int_player_season__metrics (table) → tests.
      Additive columns + rows + a new non-negative range test; no migration hazard, no nightly tie-in.
  blast_radius:
    - int_player_season__metrics: +13 columns. metric_catalogue: +13 rows; +direction/interpretation
      on 5 existing rate rows. int_team_season.yml: +1 model-level non-negative test for the per-90s.
      mart_player_profile.sql: header-comment touch-up only (no SQL change).
    - NO change to mart_player_profile / mart_leaderboards / int_player_career__metrics /
      mart_player_career output (named selects — verified #506). NO shipped-number change. The per-90
      columns are unconsumed until PR2 (metric-layer-first split).

decisions_taken: >
  CPO rulings recorded live this session (2026-06-23):
  - Introduce per-90 player metrics via the proper route (catalogue + football-analytics). The A1
    anti-pattern was per-90 invented WITHOUT approval (#325). Explicit CPO sign-off given.
  - 13-metric list CPO-confirmed (the 11 + defensive_actions_per90 + scorer_points_per90, both added
    on CPO request for parity with the team's aggregate + the leaderboard's scorer_points). Formula =
    count * 90 / minutes (safe_divide → null when minutes is zero). format=decimal_1.
  - Direction classified now (ruling "A": "classify them as we did with the other metrics"): output/
    quality = higher_better (goals/assists/scorer_points/shots_on_target/key_passes/dribbles_success
    per90 + the 5 rates); volume/style = neutral (passes/tackles/interceptions/blocks/
    defensive_actions/duels_won per90) — mirrors the team catalogue's classification of the same stats.
    lower_is_better stays false for all (the team's convention for neutral metrics).
  - Interpretations written PLAYER-NATIVE (not the team labels) for the website's automated content
    generation; neutral metrics carry the "style not quality" signal. CPO-approved the full table.
  - DQ non-negative guard on the 13 per-90 columns (a per-90 can never be negative; catches a
    formula sign-flip) — addresses the analytics-engineer review. mart_player_profile header comment
    touched up (its "no per-90 ... await a CPO-approved extension" note is now stale) — addresses
    the scope-auditor review.

decisions_reserved:
  - The per-90 / rate label i18n STRINGS (added at display-wiring time; KEY spelling follows the
    player-namespace convention, CPO can override).
  - decimal_2 display precision for per-90 (decimal_2 not in the accepted format set; revisit with
    bi-analyst if finer precision is wanted).
  - The benchmark engine + mart + floor (270; finishing also SoT>=10) + position peers + percentile — PR2.

done_when:
  - `.venv/Scripts/dbt parse` + `compile` clean; `sqlfluff lint` clean on the int model.
  - metric_catalogue.csv well-formed (13 columns/row); accepted_values satisfied (decimal_1, valid
    groups, direction in the enum); the 13 new int columns exactly match the 13 new metric_ids.
  - assert_no_uncatalogued_season_metric green; the new non-negative per-90 test parses.
  - validate-local passes. The BQ data-build runs in CI.

amendments:
  - 2026-06-23: + dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
    (non-negative per-90 DQ test) + dbt_project/models/5_marts/shared/mart_player_profile.sql (stale
    comment touch-up) — authority: CPO approval this session (2026-06-23, "good now") of the full plan
    that explicitly named the DQ guard + the comment touch-up (the CPO ruling is also recorded in
    decisions_taken above); the analytics-engineer + scope-auditor reviews surfaced the need. Clean-
    tree amendment (the branch was reset to origin/main before this contract was written).
