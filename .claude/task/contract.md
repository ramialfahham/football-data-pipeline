# Task contract — player competition benchmark PR2 (engine + mart)

> See docs/working_agreement.md §2 (contract), §10 (decision rights), §11 (escalation), Appendix A.

objective: >
  Build the player competition benchmark (content_architecture §6 — the per-90 vs-position-peers engine;
  player analog of the team benchmark #511/#512). Composes the #559 per-90/rate metrics into a per-position
  distribution and ranks each qualifying (player, season, position) against its competition peers
  (rank + percentile + value-median). Three additive models + one macro; modifies NO existing model.
refs: >
  content_architecture.md §6; player analog of #511/#512; consumes the #559 metric layer.
  CPO design rulings: .claude/task/escalations.log 2026-06-23 ("player competition benchmark — UP-FRONT
  CPO DESIGN RULINGS" D1-D8 + the two source/floor rulings logged this session).

scope_paths:
  - dbt_project/macros/player_benchmark_metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks__player.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/5_marts/shared/mart_competition_benchmarks__player.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - .claude/task/**

impact_map: >
  writers: THREE NEW models only — int_player_season_position__metrics (table; per (player, season,
    position_code) atoms + 18 in-position metrics from fct_fixture_player_stats + fct_fixture),
    int_competition_benchmarks__player (table; per (league_code, season_api_year, position_group,
    metric_key) distribution), mart_competition_benchmarks__player (view; LONG per (player, season,
    position_group, metric_key)). NO existing model is modified (int_player_season__metrics from #559 is
    untouched; the position-split model reads the per-fixture leg directly, not that model).
  downstream: ADDITIVE LEAF. mart_competition_benchmarks__player has no downstream (the v2 export /
    website is #391-PAUSED, no consumer built). Evidence: `dbt ls --select int_player_season__metrics+
    --resource-type model` (venv dbt 1.7.19) → int_player_career__metrics, mart_leaderboards,
    mart_player_career, mart_player_profile — i.e. the #559 model's consumers; this PR touches NONE of
    them and adds a separate position-split branch. New models compile to leaves (verify post-build with
    `dbt ls --select mart_competition_benchmarks__player+` → only itself).
  layer_rules: 4_intermediate = feature aggregation (the per-position metrics + the distribution engine);
    5_marts = consumption (the ranked LONG mart). All in 4_intermediate/shared + 5_marts/shared (cross-
    league, league_code partition column flows through; no per-competition files — check_layer_contract
    stays green). Materialization set in-file (table/table/view); no dbt_project.yml change.
  deploy_order: purely additive — the three new objects build after their upstream core facts
    (fct_fixture_player_stats, fct_fixture, dim_player) in the 04:00 nightly DAG; no existing model's
    build or order changes; nothing breaks pre-merge (new objects only, no contract change to a live model).
  blast_radius: NONE on shipped numbers — additive; no existing mart SQL changes. Grain evidence PASTED
    (live BQ, not asserted — §2/A6). position_code coverage at the 270-min qualifier grain, by season
    (`SELECT season_api_year, COUNT(*) qualifiers, COUNTIF(season_position_code IS NULL) null_poscode FROM
    season_pos JOIN int_player_season__metrics WHERE minutes>=270` over the modal position_code per
    player-season):
      2026: 3435 q / 0 null    2025: 10836 / 0    2024: 11315 / 0    2023: 9993 / 0    2022: 9804 / 0
      2021: 6293 / 0    2020: 4313 / 0    2019: 4280 / 0    2018: 3628 / 0    2017: 3465 / 0    2016: 2564 / 0
    => 100% coverage every season (0 null), vs dim_player.player_position null 0.1%/0.5%/5.6%/.../58% (2026..
    2016) — the premise behind B1. Qualifying (player, season, position) rows = 60,375 single-position +
    6,561 two-position + 67 three-position (`GROUP BY player,season HAVING COUNTIF(min_in_pos>=270)=N`).
    Junk position_codes ('-'/'SUB'/null = 142 of 1.67M legs) are excluded (not G/D/M/F).

decisions_taken: >
  ALL CPO-locked; do not re-litigate (escalations.log 2026-06-23 D1-D8 + the two rulings this session):
  - Structure mirrors team #512: metrics model -> engine (distribution) -> mart (rank), + a
    player_benchmark_metrics() macro shared engine<->mart (like team_benchmark_metrics()).
  - Metric set = 18 (D8): 13 per-90 (goals/assists/scorer_points/shots_on_target/key_passes/
    dribbles_success/passes/tackles/interceptions/blocks/defensive_actions/duels_won/saves) + 5 rates
    (pass_accuracy_pct/duels_won_pct/dribbles_success_pct/finishing_efficiency/save_pct). All already in
    metric_catalogue with direction populated (verified live) — PR2 makes NO catalogue change.
  - Peers = position group GK/DEF/MID/ATT (D2). SOURCE = season-level position_code from
    fct_fixture_player_stats (G/D/M/F -> GK/DEF/MID/ATT), NOT dim_player.player_position (CPO ruling this
    session, "B"): the bio-snapshot null is 0.5% only in 2025 but 18-58% in historical seasons (the
    "0.5% null" premise held only for 2025); position_code is recorded at match time -> 100% qualifier
    coverage every season AND is season-accurate (the role actually played that season).
  - Floor = 270 minutes IN THE POSITION (CPO ruling this session, "Yes, I agree"): the >=270 rule applies
    per position_code, which both qualifies AND assigns position — NO modal/mode step. A player who clears
    270 in two positions (~10%) appears in BOTH benchmarks, each on the per-90 he produced IN that role
    (the value grain is per (player, season, position); the whole-season per-90 in #559 stays the profile
    metric, it is NOT the benchmark value source). finishing_efficiency ALSO needs shots_on_target >= 10
    IN the position (D4). save_pct populates only where position = G (null elsewhere -> falls out).
  - METRIC ELIGIBILITY PER POSITION (CPO ruling this session, "I agree") — Path B (per-position relevant
    set), NOT compute-all-x-all. Rule: benchmark a metric for a position group only when non-degenerate for
    that group; because the peer pool is already position-specific, the only dead boards are at the
    GK<->outfield boundary. MAP: GK = {saves_per90, save_pct, passes_per90, pass_accuracy_pct} (4); DEF =
    MID = ATT = the other 16 (everything except the 2 GK-only metrics). No finer DEF/MID/ATT split (the
    peer pool already makes within-outfield comparisons position-relative; splitting would bake display into
    the benchmark). 52 position x metric boards, not 72. Eligibility lives as a per-metric position list in
    the player_benchmark_metrics() macro (shared engine<->mart); an ineligible metric x position emits no
    row (null -> excluded), no schema change.
  - Carry BOTH rank-of-N AND percentile (D3) + peer_count + minutes + appearances (sample visible).
  - ALL competitions, no league-only scoping (D5). NO prev-season fallback — each competition-season on
    its own data (D6). DIRECTION-AGNOSTIC mart — rank by value desc; good/bad read from catalogue
    direction at display (D7). Two lenses kept separate from leaderboards (coherence ruling).

decisions_reserved:
  - The benchmark ELIGIBILITY per position is now LOCKED (the map above). What remains reserved: WHICH of
    a position's eligible metrics a PAGE surfaces, and in what order, is a page-composition / display
    decision (§10) — OUT OF SCOPE for PR2. The mart carries all eligible (position, metric) boards;
    display picks and orders later. Flag, do not decide.

done_when:
  - `dbt parse` clean; `dbt build --select int_player_season_position__metrics
    int_competition_benchmarks__player mart_competition_benchmarks__player` green (incl. the new yml tests:
    unique grain, not_null keys, accepted_values on metric_key + position_group, rank in 1..peer_count).
  - `dbt ls --select mart_competition_benchmarks__player+ --resource-type model` -> only itself (leaf).
  - Spot-check (live): a multi-position player shows distinct per-90 per position; a single-position player
    with NO junk-position legs has a benchmark value equal to his #559 whole-season per-90 (the position
    filter excludes '-'/'SUB'/null legs, so a player with such legs differs by that fraction — measured: 9
    of 137,417 single-position seasons); percentile in [0, 1] (percent_rank: 0 = bottom/tied-bottom),
    rank in 1..peer_count.
  - SQLFluff clean on the new SQL. Full G3 review cycle: scope-auditor + analytics-engineer-reviewer PASS.

amendments: (none)
