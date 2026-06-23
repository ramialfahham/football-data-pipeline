# Task contract — mart_player_career (Player Career tab)

objective: >
  Build the player career surface (content_architecture: Player "Career" tab = clubs + per-competition
  totals + caps; powers `mart_player_career`, on the backfill). Two NEW additive models:
  (1) int_player_career__metrics — across-seasons rollup of int_player_season__metrics, one row per
  (player, competition): career appearances / goals / assists (NO minutes — CPO), first/last season,
  seasons_played. (2) mart_player_career — consumption: + dim_player identity + competition entity_type
  (club/national). National-entity rows = the honest "national appearances in covered competitions"
  (NOT true career caps — we only ingest a subset of national comps); the per-player national total is
  computed in dbt (denormalized onto the mart), never derived in the export. Clubs list stays with the
  existing dim_player_team_season_mapping — not duplicated here.

refs: >
  content_architecture.md §3 (block↔mart: mart_player_career) + §4 (Player Career tab) + §7 (new-mart
  list). CPO this session: career first (then coaches); grain per (player, competition); counts only,
  no minutes; "national appearances" not "caps". Website #391 PAUSED — this builds the DATA, not UI copy.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_player_career__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_career.yml
  - dbt_project/models/5_marts/shared/mart_player_career.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/docs/layering.md
  - .claude/task/**

impact_map: >
  writers: TWO NEW models, both additive. int_player_career__metrics (4_intermediate/shared) groups
    int_player_season__metrics by (player_sk, league_code, league_sk) and sums appearances/goals/assists
    + min/max season + count(distinct season_sk). mart_player_career (5_marts/shared) reads that +
    dim_player (identity) + competition_registry -> competition_types (entity_type club/national), and
    denormalises a per-player national_appearances_total. NO existing model is modified.
  downstream: NONE — both are new LEAF models; nothing ref()s them (the website that will consume them is
    PAUSED, #391). `dbt ls --select mart_player_career+` would return only itself once built. Sources
    (all exist, verified this session): int_player_season__metrics, dim_player, competition_registry,
    competition_types.
  layer_rules: the across-seasons rollup (aggregation) belongs in 4_intermediate — mirrors
    int_player_season__metrics (the season-level agg) per the #480 pattern; the mart is 5_marts
    consumption (entity lookup + denormalisation + identity). league_code flows through; no
    per-competition business logic. No staging/core touched. check_layer_contract unaffected.
  deploy_order: purely additive — two NEW relations, no existing model changed, nothing depends on them,
    so no ordering risk and no shipped-number change. ci-data-build creates them.
  blast_radius: NONE — additive only; no existing mart/number moves. New data = player career rollups.
    Source depth confirmed this session (int_player_season__metrics: 10-season career for top leagues +
    continental; national comps WC/WCQ/EURO/AFCON/CNL present for the national-appearances rows).
    source evidence (bq, this session): per-league player-season counts — top leagues at 10-season
    depth (PD/SA/L1/PL/BL1 2016-2025; UCL/UEL 2017-2025); national comps present (WC 1242, WCQEU 1966,
    CNL 2405, AFCON 652, EURO 621 player-seasons); and the new grain is unique — 0 league_codes map to
    >1 league_sk, so (player_sk, league_code) is safe (re-run after the GROUP-BY alignment).

decisions_taken: >
  CPO this session: (a) sequence — mart_player_career first, dim_coach/coaches second; (b) grain = one
  row per (player, competition); (c) counts only — appearances, goals, assists — explicitly NO minutes;
  (d) the national figure is labelled honestly as national appearances in covered competitions, NOT
  "caps" (DQ — we don't ingest a player's full international history); (e) int + mart layering. The
  consumption-layer rule ([[feedback-consumption-layer-contract]]): the per-player national total is a
  fact computed in dbt (denormalised), never summed in the export.
  Catalogue governance: NO new/uncatalogued metric. `appearances` is an exempt playing-time FACT
  (assert_no_uncatalogued_season_metric exempts it as "dimensions, not metrics"); `goals`/`assists`
  are catalogued player metrics (metric_catalogue.csv), and the catalogue is WINDOW-AGNOSTIC (metric
  ids carry no window suffix) — so career totals are the SAME catalogued atoms over a career window,
  exactly as int_player_season__metrics exposes them at season grain and mart_team_season at team. The
  new career model is a fresh surface, not added to the season drift-test (that governs only the two
  SEASON canonical models).

decisions_reserved:
  - Career tab DISPLAY copy / i18n (the "national appearances" wording, the tab layout) is a
    bi-analyst / §10 display-contract item — deferred (website #391 PAUSED); this PR is data-only.
  - Career-long RATES (pass% etc.) excluded by CPO (counts only); a follow-up if ever wanted.
  - The "team-history equivalent" (content_architecture §3) is a separate later mart, not this PR.

done_when:
  - int_player_career__metrics: grain (player_sk, league_code) unique-tested; appearances/goals/assists
    summed across seasons; first_season/last_season/seasons_played present.
  - mart_player_career: one row per (player, competition) with entity_type + national_appearances_total;
    player identity from dim_player; documented in shared.yml with grain + not-null + relationship tests.
  - validate-local (sqlfluff + dbt parse) green; ci-data-build green (new models build, tests pass).

amendments:
  - 2026-06-23: + dbt_project/docs/layering.md — authority: analytics-engineer reviewer FAIL (the
    "Canonical mart inventory (exhaustive)" in layering.md must list every mart) + the standing
    doc-sync rule. Content: add the mart_player_career row to the §5_marts inventory table.
