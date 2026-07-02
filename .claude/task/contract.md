# Task contract — #480 per-club player-season foundation + per-club career table (Phase C, brick 1)

> Written on a CLEAN tree (branch feat/480-per-club-player-season-foundation off main @ d7c8206).
> Model/data change — went through plan mode; plan approved. See the approved plan
> (majestic-toasting-stroustrup) + docs/working_agreement.md §1.

objective: >
  A player career is club/national-team × competition × season, but we have no model at that grain:
  mart_player_career collapses to per-competition (club axis dropped). CPO ruled (this session): build the
  #480 canonical per-club player-season foundation, CONSOLIDATE onto one per-club grain (option A), and in
  this PR also rebuild the career table (option 2) for a tangible per-club result. Deliver a new per-club
  atoms base; re-express int_player_season__metrics as a byte-stable rollup of it (profile + leaderboards
  numbers unchanged); rebuild mart_player_career to per-club × competition × season; retire the now-redundant
  per-competition career rollup. NO export/screen/live-MVP change; the career SCREEN spec, export wiring, and
  the history backfill are downstream (out of scope).

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_player_club_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/5_marts/shared/mart_player_career.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/4_intermediate/shared/int_player_career__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_career.yml
  - dbt_project/tests/assert_no_uncatalogued_season_metric.sql
  - dbt_project/docs/layering.md
  - .claude/task/**

impact_map: >
  STRUCTURAL SURFACE: a new 4_intermediate model + a grain change on a mart. dbt CLI (1.7.19) is broken
  locally and the dbt-MCP is not connected (documented constraints) — the lineage below is grep-derived from
  ref() calls across dbt_project/models + /tests (target/ excluded); ci-data-build executes the real graph.
  Verified 2026-07-02.

  writers (models changed + what each reads):
    - int_player_club_season__metrics (NEW, table) <- fct_fixture_player_stats, fct_fixture, fct_fixture_event
      (3_core facts; fed by ingestion base_apif__fixture_players / fixtures_next / fixture_events). No new
      raw/ingestion writer.
    - int_player_season__metrics (EDIT; grain (player_sk, season_sk) UNCHANGED) <- now reads
      int_player_club_season__metrics (was: the 3 core facts directly).
    - mart_player_career (REBUILT; grain changed) <- int_player_club_season__metrics + dim_player + dim_team
      + competition_registry + competition_types (seeds).

  downstream (grep of ref('<model>'); comment-only mentions excluded):
    - int_player_club_season__metrics -> int_player_season__metrics:21, mart_player_career:22,
      assert_no_uncatalogued_season_metric (depends_on).
    - int_player_season__metrics -> mart_leaderboards:59, mart_player_profile:25,
      assert_no_uncatalogued_season_metric (depends_on). int_player_season_position__metrics only NAMES it in
      a comment (reads fct directly — NOT a ref).
    - mart_player_career -> NONE. Leaf/orphan: 0 refs in dbt_project, 0 hits in scripts/ (not in
      export_site_data.py). Not exported.
    - int_player_career__metrics (DELETED) -> was consumed ONLY by mart_player_career (now re-sourced).

  layer_rules (check_layer_contract.py, CI-enforced; passes locally): intermediate must NOT ref mart_* — the
    base refs only 3_core facts, the rollup refs only the same-layer base; the mart consumes intermediate +
    core dims + seeds; 2_base unchanged.

  deploy_order (shared warehouse; nightly 04:00 UTC): DAG-resolved (base -> rollup -> {profile, leaderboards,
    career} -> drift test); no manual ordering. All models are `table` (NOT incremental) -> no --full-refresh,
    the incremental column-rename trap does not apply. The rollup output is byte-identical so deployed
    profile/leaderboards do not change across the swap; mart_player_career is an orphan so its grain change
    breaks no live consumer. One atomic PR.

  blast_radius:
    - Shipped NUMBERS changed: NONE. mart_player_profile + mart_leaderboards byte-identical (AE independently
      reconstructed the OLD model from target/compiled and confirmed the additive-atom + per-fixture-ROUND
      passes_accurate re-summation is exact). Rollup team_sk is unused by both consumers (profile uses
      int_player_season__team; leaderboards omits it) and is now deterministic (tiebreak added).
    - New surface: mart_player_career regrained to (player_sk, team_sk, season_sk) — orphan, no live break;
      export wiring is a separate future PR. No RAW/ingestion change.

  supporting (non-model) edits: int_player_club_season.yml (NEW tests); int_team_season.yml
    (int_player_season__metrics description + a team_sk not_null/relationships test, review-added); shared.yml
    (mart_player_career yml regrained to the new grain + an appearance-gate guard `appearances >= 1` + a
    dim_player_team_season_mapping-distinction note; seasons-span test dropped); assert_no_uncatalogued_season_metric.sql
    (base added to the guard + last_kickoff_at exempted); layering.md (mart inventory row ~L299);
    int_player_career.yml (DELETED).

decisions_taken: >
  Layered consolidation, NOT literal re-grain: ratios/per-90 are not summable, so making
  int_player_season__metrics itself per-club would push atom-re-sum + ratio-re-derivation into every consumer
  (duplication + double-count risk = the anti-pattern #480 kills). The base holds summable atoms only; the
  per-competition-season rollup and the career mart both derive from that ONE root. Career mart grain =
  (player, club, competition-season) = the atomic truth; per-club/per-competition/national subtotals are
  derivable (display-side or a thin follow-up), not precomputed here. int_player_career__metrics retired
  (redundant once the base exists). Byte-stability is the safety property — proven CI-side by the unchanged
  profile/leaderboards tests. Layer placement: per-club aggregation = a reusable calc feeding marts →
  4_intermediate (layering.md §4).

decisions_reserved:
  - Career SCREEN (13) doc spec — separate PR (against the rebuilt per-club mart). Not this PR.
  - Export wiring of mart_player_career (new GAP; select/reshape only) — separate PR.
  - History backfill (depth per competition) — separate registry + cost-gated ingest task; §10 cost
    decision. The career table stays thin until it runs; the model is correct regardless.
  - Precomputed subtotal columns (per-club/per-competition/national) — deferred unless CPO wants them.
  - All other §10 (product/UX, metrics, naming beyond this model, new mechanisms) unchanged.

done_when:
  - int_player_club_season__metrics built at grain (player_sk, team_sk, season_sk) with a unique_combination
    grain test + key relationships; atoms match today's formulas.
  - int_player_season__metrics re-expressed as a composition of the base; grain + output columns unchanged;
    profile + leaderboards + drift-guard tests stay green in ci-data-build (byte-stability).
  - mart_player_career rebuilt to the per-club grain + tested (new shared.yml entry); int_player_career__metrics
    + its yml deleted; no dangling ref() (grep).
  - assert_no_uncatalogued_season_metric passes with the base added; layering.md inventory synced.
  - python scripts/check_layer_contract.py passes; ci-data-build green.
  - scope-auditor + analytics-engineer PASS (>=2 risks each); review.md diff_sha256 binds; CPO merges.

amendments:
  - 2026-07-02: impact_map rewritten from a prose per-file list to the TEMPLATE.md labeled format
    (writers / downstream / layer_rules / deploy_order / blast_radius) with grep-derived lineage evidence.
    Authority: analytics-engineer blinded-review finding (impact_map must be evidenced, not asserted; A6).
    No scope_paths added, no §10 decision changed — format/evidence only.
  - 2026-07-02: within already-in-scope files, added a deterministic team_sk secondary sort in
    int_player_season__metrics (tiebreak on last_kickoff_at, though a tie is physically impossible) + a
    team_sk not_null/relationships test in int_team_season.yml. Authority: scope-auditor + analytics-engineer
    finding (team_sk tie determinism + zero coverage). Byte-stable (no real row is a tie); no scope change.
  - 2026-07-02: replaced the mart_player_career tautological test (national_appearances_total >= appearances,
    which can never fail) with a load-bearing appearance-gate assertion (appearances >= 1) + restored the
    dim_player_team_season_mapping distinction (dropped in the rebuild) to the mart header + shared.yml
    description. Authority: analytics-engineer finding (tautology + doc regression). Doc/test only; no
    scope_paths added, no §10 change.
