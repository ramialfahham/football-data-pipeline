# Task contract — GAP-22: wire mart_player_career into the v2 player export

> Written on a CLEAN tree (branch feat/391-gap22-career-wiring off main @ 522115b).
> Code (export) change — went through plan mode; plan approved (recommended default: atomic rows + frontend
> grouping). Mirrors GAP-21 (#627) + GAP-20 (#619). No dbt/model change.

objective: >
  mart_player_career (per-club career log, #630) is built + the Career screen spec'd (#632), but the v2 player
  export does not carry it. Wire it into shape_player_payload as a TOP-LEVEL career[] block (one member per
  club×competition×season) + a top-level national_appearances_total, so the Career screen (13) has a payload.
  Export-only, select/reshape only (consumption-layer contract) — no derivation. Closes GAP-22.

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - dbt_project/models/5_marts/shared/mart_player_career.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - .claude/task/**

impact_map: >
  STRUCTURAL SURFACE: scripts/export_*.py (consumption layer) + a small mart column add on
  mart_player_career (dbt) — see amendment 3. ci-data-build is the gate for the mart change (dbt broken
  locally). No RAW/ingestion change. Verified 2026-07-02.
  writers (what this edit makes the export read): shape_player_payload + fetch_player_payloads now read
    `mart_player_career` (grain player×team×season, built #630) in ADDITION to the existing mart_player_profile
    + mart_player_match_log + mart_player_competition_benchmarks reads. No new mart/model/RAW writer.
  downstream (who consumes the player payload): scripts/export_site_data.py -> data/players/{id}.json (the v2
    payload) -> site_v2/ build -> GitHub Pages. site_v2/ is an EMPTY scaffold (v2 frontend not built, #366/#368)
    so there is NO live consumer of the v2 export today. The LIVE MVP uses a DIFFERENT script
    (export_pages_data.py) + mart_matchday_insights — NOT touched here.
  layer_rules: consumption-layer contract (layering.md "Consumption layer") — select/filter/group/rename/
    reshape ONLY; NEVER metric math, ranking, window selection, or entity derivation. Enforced by the
    dbt_layer_gate EDIT-HOOK (injects the contract on export edits) + the blinded reviewers (analytics-engineer
    + cto) — NOT by check_layer_contract.py, which scans dbt models only.
  deploy_order: the export runs post-dbt (reads the marts). Additive — adds career[] + national_appearances_total
    to the player payload; changes/removes NO existing key. No migration; no live v2 consumer to break. One PR.
  blast_radius: adds a top-level career[] block + national_appearances_total to data/players/{id}.json; every
    existing key unchanged. No shipped NUMBERS change (select/reshape only). No RAW/dbt/ingestion change; the
    live MVP is untouched. Fully additive, no live break.

decisions_taken: >
  Per the approved plan. NEW _shape_career_row(row): one mart_player_career row -> {season (season_api_year),
  competition (league_code), entity_type, team (REUSE _player_team_block -> {team_id,name,crest,country}),
  appearances, goals, assists}; internal keys + player identity dropped. shape_player_payload gains a
  career_rows param -> TOP-LEVEL career[] (most-recent-season first: season_api_year DESC, then league_code +
  team_sk as deterministic tie-breakers — a display sort on a real temporal column, so the frontend's
  group-by-club yields clubs in recency order per wireframe 13 §4, no frontend derivation; omit null-team_name
  rows = broken FK, DQ-guarded, mirrors squad) + top-level national_appearances_total
  (per-player constant from any career row; None when no rows). fetch_player_payloads fetches mart_player_career
  scoped to the sampled players (mirrors the benchmark fetch), groups by player_sk, passes career_rows. 2 unit
  tests mirror the benchmark/squad tests. RESERVED subtotal call resolved to the CONSUMPTION-CONTRACT DEFAULT
  (CPO-approved at plan): export carries the ATOMIC rows + the precomputed national total; per-club/career
  subtotals are frontend display-grouping — the export computes nothing.

decisions_reserved:
  - Precomputed per-club/career subtotal columns (if ever preferred over frontend grouping) — a separate mart PR.
  - The history backfill (§10 cost) — the career stays thin until it runs; separate.
  - Career club-link slugs (GAP-19) + per-fixture deep-links — separate.
  - All §10 unchanged (no new metric; no ranking; no derivation).

done_when:
  - _shape_career_row + the career[] / national_appearances_total attachment + the fetch wired; the payload
    carries a top-level career[] (atomic, byte-stable, null-team omitted) + national_appearances_total.
  - 2 new unit tests added; `python -m pytest tests/test_export_site_data.py -q` GREEN locally; validate-local
    (ruff + pytest) green; no derivation in the export (select/reshape only).
  - scope-auditor + analytics-engineer-reviewer + cto-reviewer PASS (>=2 risks each); review.md diff_sha256
    binds; CPO merges.

amendments:
  - 2026-07-02: changed the career[] sort from (team_sk, season desc, league_code) to season_api_year
    DESC-primary (+ league_code + team_sk tie-break) so it matches wireframe 13 §4 ("clubs by most-recent
    season descending") — a surrogate-key sort is not a recency order. Test expectation + comment updated.
    Authority: analytics-engineer FAIL. Also corrected the impact_map layer_rules "(CI-enforced)" label (the
    export contract is dbt_layer_gate-hook + reviewer enforced, not check_layer_contract.py) — cto nit.
    Code/doc only; no scope_path added, no §10 change.
  - 2026-07-02: scope-auditor FAILed on doc-sync — wireframe 13 + the gaps register (GAP-22) go stale
    post-merge (this PR closes GAP-22, which they call "not yet wired / pending"). **CPO ANSWER: reconcile
    SEPARATELY** — this PR stays CODE-ONLY, matching the #627 (GAP-21) / #619 (GAP-20) wiring-PR precedent
    (both left their wireframes "proposed / not yet wired" on main) + the prior content_architecture ruling
    this session; the wireframe 11/12/13 "proposed→wired" + gaps-register GAP-20/21/22 "→shipped" flips are
    folded into the reconciliation task. No scope_path added to this PR.
  - 2026-07-02: analytics-engineer + cto round-2 FAIL — the season_api_year-only sort can't order clubs
    correctly for a mid-season transfer / return spell (season alone can't disambiguate two clubs in one
    season; a flat sort also splits a returning club's rows). **CPO ANSWER: fix properly — add the mart
    column.** Scope widened (this amendment) to add `last_kickoff_at` to mart_player_career (projected from
    int_player_club_season__metrics, which already computes it) + shared.yml; the export orders career[] by
    it so clubs sort by recency AND a club's rows stay contiguous. Authority: CPO ruling 2026-07-02.
    ci-data-build is now the gate (dbt change). scope_paths += mart_player_career.sql + shared.yml.
  - 2026-07-02: analytics-engineer round-3 FAIL — the per-club recency MAX was computed in the EXPORT
    (a client-side aggregation driving the order = the banned "ordering that encodes a business rule"; the
    mart_leaderboards.rank / mart_team_fixtures.recency_rank pattern ships the order signal FROM the mart).
    Fix: moved the club-recency signal into the mart — mart_player_career now also carries
    club_latest_kickoff_at = max(last_kickoff_at) over (partition by player_sk, team_sk); the export is now a
    PURE sort by (club_latest_kickoff_at, last_kickoff_at, team_sk) desc — select + sort over mart columns,
    zero client-side aggregation. Added multi-national-row test coverage (AE finding 2). Same scope files as
    amendment 3 (mart already in scope); no §10 change. Authority: consumption-layer contract + the CPO
    "add the mart column" ruling (same intent — the ordering signal belongs in the mart).
