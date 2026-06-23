# Task contract — leaderboards rate boards + qualification rule (#506)

objective: >
  Add the 5 deferred RATE boards to mart_leaderboards (pass% / duels% / dribble% /
  finishing% / save%), with a CPO-set qualification rule that keeps boards populated
  early-season yet sample-safe. Warehouse-only (mart + metric layer); export wiring is
  out of scope per the issue (and #391 paused).
refs: >
  #506. CPO design rulings recorded live this session (2026-06-23): minutes gate,
  position scoping, finishing sample floor, and "finishing_efficiency is not a new
  metric — extend the existing one to the player entity".

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/shared.yml

impact_map: >
  writers:
    - finishing_efficiency (player) = safe_divide(goals, shots_on_target) — computed ONLY
      in int_player_season__metrics (alongside the 4 rate columns already there:
      pass_accuracy_pct, duels_won_pct, dribbles_success_pct, save_pct).
    - the 5 rate boards — emitted ONLY by mart_leaderboards (the LONG per-board mart).
  downstream (pasted, `dbt ls`):
    - int_player_season__metrics+ → int_player_career__metrics, mart_leaderboards,
      mart_player_career, mart_player_profile. VERIFIED by reading each: mart_player_profile
      (named SELECT, lines 61-113) and int_player_career__metrics (named sums of
      appearances/goals/assists, lines 17-31) select named columns — the new
      finishing_efficiency column does NOT leak into them; their schemas/numbers are
      unchanged. mart_player_career reads int_player_career__metrics, not the season model.
    - mart_leaderboards+ → (leaf; no downstream dbt models).
    - metric_catalogue+ → the catalogue's own accepted_values / not_null / uniqueness tests
      + assert_no_uncatalogued_season_metric (which REQUIRES the finishing_efficiency player
      row — see layer_rules).
  consumption (outside dbt lineage):
    - scripts/export_site_data.py reads mart_leaderboards but filters metric_key to
      _LEADERBOARD_METRICS (the 9 count boards). The 5 rate keys are NOT added there, so the
      live export is unchanged. sort_value widens INT64→FLOAT64 (see blast_radius); value is
      identical (25 ≡ 25.0), reaches the export only on the next Pages run, JSON-numeric-equal.
      Export wiring of the rate boards is deferred (out of scope, #391 paused).
  layer_rules:
    - assert_no_uncatalogued_season_metric: every metric column in int_player_season__metrics
      must have a metric_catalogue row (entity='player', metric_id=column). Adding the
      finishing_efficiency column REQUIRES the catalogue row — both land in this PR.
    - marts are consumption-only: the rates are precomputed in the int model; the mart selects
      + ranks + floors, it does not derive new facts. No logic in the export.
  deploy_order:
    - shared warehouse; ci-data-build rebuilds seed (metric_catalogue) → int_player_season__metrics
      (table) → mart_leaderboards (view) → tests, in one run. Additive column + additive rows +
      new board rows; no migration hazard. Not run against the 04:00 nightly (CI builds on the PR).
  blast_radius:
    - mart_leaderboards: +5 board types (rate), +5 documented rate columns, metric_key
      accepted_values +5, sort_value type INT64→FLOAT64 (union of count+rate; value unchanged).
    - int_player_season__metrics: +1 column (finishing_efficiency).
    - metric_catalogue: +1 row (finishing_efficiency, player).
    - NO change to mart_player_profile / int_player_career__metrics / mart_player_career
      (named selects — verified). NO change to the live export (rate keys not listed).

decisions_taken: >
  CPO rulings recorded live this session (2026-06-23), grounded in 2025-season distributions
  pulled from intermediate.int_player_season__metrics:
  - finishing_efficiency is NOT a new metric: extend the existing (team) metric to the player
    entity, same definition goals/shots_on_target, uncapped (verbatim: "finishing_efficiency is
    not a new metric ... we already have this"). New catalogue row entity='player', mirroring the
    team row; label_i18n_key playerMetrics.finishingEfficiency.label (player-namespace convention).
  - Qualification rule, all 5 rate boards: minutes >= 270 (3 full matches) — fills boards by
    ~matchday 3-4 yet sample-safe.
  - Position scoping: pass% / duels% / dribble% → outfield (player_position not null and
    != 'Goalkeeper'); finishing% → outfield ("otherwise we would exclude offensive midfielders");
    save% → player_position = 'Goalkeeper'.
  - Extra sample floor: finishing% → shots_on_target >= 10 (data: minutes alone leaves 46% of
    finishing qualifiers at <=3 SoT, top gamed by 100%-on-tiny-sample; SoT>=10 cleans it). save%
    → GK filter alone, no shots-faced floor.
  - Scope is warehouse-only per #506 (export wiring deferred).

decisions_reserved:
  - Export wiring (adding the 5 rate keys to _LEADERBOARD_METRICS / rate columns to _LB_KEEP) —
    a product/site decision under paused #391; NOT decided here. Flagged to CPO.
  - The player finishing label STRING/i18n translation — added at export-wiring time (no test binds
    label_i18n_key today; key declared now). The KEY spelling is a naming detail CPO can override.

done_when:
  - `.venv/Scripts/dbt parse` clean; `.venv/Scripts/sqlfluff lint` clean on the changed SQL.
  - mart_leaderboards compiles; metric_key accepted_values lists 14 boards; the 4 bounded rates have
    0-1 range tests, finishing_efficiency is EXCLUDED from the range test (uncapped, mirrors team).
  - assert_no_uncatalogued_season_metric still green (finishing_efficiency player row present).
  - validate-local passes (offline gates + dbt parse + sqlfluff). The BQ data-build runs in CI.

amendments: (none)
