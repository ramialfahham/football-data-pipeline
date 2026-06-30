# Task contract — #391 GAP-16: player team affiliation (current team + per-season history)

> Written on a CLEAN tree (branch off main @ b840e6b). dbt build + export wiring + folded doc-sync.
> See docs/working_agreement.md §2 (contract), §10 (decision rights), §11 (escalation), App. A.

objective: >
  Surface the player's CURRENT team + per-season team on the v2 player page. mart_player_profile carries
  no team today (correct at its grain; players transfer). Per the CPO ruling this session, "team" is the
  club of the player's MOST RECENT finished match (Option B — deterministic, byte-stable, matches the
  profile's played-seasons grain), derived in dbt, DQ-tested vs dim_team. A new intermediate computes the
  per-(player, competition-season) most-recent-match team + a single current-team flag; mart_player_profile
  joins it + dim_team identity; the export reshapes (no derivation). The directly-coupled wireframe + gaps
  register are synced in the same PR (CPO chose FOLD at plan approval). Closes GAP-16.

refs: >
  #391 (un-paused, data-first) · GAP-16 (Phase B; register "approved CPO 2026-06-11", scope = current team
  + history) · CPO source ruling this session: Option B (most-recent-match team, dbt-derived) — DEVIATES
  from the register's literal "affiliation" (roster) wording, which lacks a transfer date so cannot give a
  stable "latest team that season". Doc-sync FOLD chosen by CPO at plan approval. backlog in .claude/active_work.md.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_player_season__team.sql
  - dbt_project/models/4_intermediate/shared/int_player_season__team.yml
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - docs/wireframes/03_player_profile.md
  - docs/wireframes/99_gaps_register.md
  - .claude/task/**

# Structural surface (dbt_project/models/** + scripts/export_*.py) in scope -> impact_map required.
impact_map: >
  writers: NEW `int_player_season__team` (grain player_sk, league_code, season_api_year — 1:1 with the
    mart's player_sk+season_sk) from `int_legs__player_match` (the conformed finished player-match leg;
    carries player_sk, team_sk, league_code, season_api_year, fixture_sk, kickoff_datetime — same source
    + finished-only filter as the profile, so grains align). Per (player, competition-season): team_sk of
    the max-kickoff leg (qualify row_number, tiebreak fixture_sk). is_current_team = the season-row holding
    the player's GLOBAL max-kickoff (row_number over player). mart_player_profile (materialized=TABLE ->
    full rebuild each run, NO incremental/full-refresh dance) LEFT JOINs it on (player_sk, league_code,
    season_api_year) + LEFT JOINs dim_team for identity (team_name/team_logo_url/team_country), mirroring
    its existing dim_player identity join.
  downstream: mart_player_profile is consumed ONLY by the v2 player export (scripts/export_site_data.py,
    `select * from mart_player_profile`) + documented in shared.yml. (`int_player_season__metrics.sql:5`
    names it in a COMMENT, not a ref() — verified; no inverted dependency.) The new intermediate is
    consumed only by mart_player_profile.
  layer_rules: intermediate = the recency BUSINESS LOGIC (which team is "most recent"); mart = assembly +
    dim_team identity join; export = reshape ONLY (dbt owns is_current_team + team_sk; the export selects
    by the flag, never re-ranks). check_layer_contract; consumption-layer contract.
  deploy_order: mart_player_profile is table-materialized -> rebuilt on the next nightly run after the new
    intermediate; no incremental rename, no --full-refresh. The export is wired into NO workflow (only
    export_pages_data.py, the live-MVP export, runs in pages/ci-ui) -> zero live-MVP impact. ci-data-build
    builds + DQ-tests the new model + the mart relationships test on this PR.
  blast_radius: +1 intermediate (+ its yml), ~5 new columns on mart_player_profile (team_sk,
    is_current_team, team_name, team_logo_url, team_country), +1 relationships DQ test (team_sk -> dim_team)
    + the int grain test. Player payload gains top-level `current_team` + a per-season `team` block. NO
    change to any existing metric/number. Live MVP (`site/`) untouched. Docs are non-executed.

decisions_taken: >
  Source = Option B (most-recent-finished-match team), CPO-ruled this session — deterministic + byte-stable
  where the register's literal roster source cannot be (no transfer date). "current team" = club of the
  player's single most-recent finished match overall (dbt flag is_current_team); per-season "team" = club
  of their most-recent finished match that competition-season. dbt owns the ranking; the export selects by
  the flag + reshapes (consumption-layer honored). DQ = relationships test team_sk -> dim_team. The mart
  carries team identity (joined from dim_team) so it stays self-describing. Source = int_legs__player_match
  (the tested conformed leg, finished-only) — modular, mirrors int_player_season_record. Doc-sync FOLDED in
  per the CPO's choice at plan approval (GAP-16's wireframe §5 is substantively wrong — wrong source + wrong
  layer — so shipping code-≠-spec is worse than for GAP-14); this also records the Option-B ruling in the
  register. Naming (int_player_season__team, is_current_team, payload current_team + per-season team block)
  proposed in the plan, approved by the CPO at ExitPlanMode.

decisions_reserved:
  - is_current_team uniqueness (exactly one per player) is GUARANTEED by the deterministic row_number()=1
    window (every player in the int has >=1 leg) — relying on construction + the grain test, NOT adding a
    separate singular test (would expand scope to dbt_project/tests/ + the FROM-clause gotcha). Documented.
  - HOW current team / age etc. render is a frontend (§10) concern, deferred to Phase E; the wireframe stays
    descriptive.

done_when:
  - `int_player_season__team` (+ yml: grain unique_combination + not_null cols) builds; mart_player_profile
    carries team_sk + is_current_team + team identity; shared.yml documents them + the relationships DQ test
    (team_sk -> dim_team) — both run in ci-data-build.
  - shape_player_payload emits top-level `current_team` (from the is_current_team row, NOT re-ranked) + a
    per-season `team` block; `pytest tests/test_export_site_data.py` green incl. new asserts.
  - wireframe 03_player_profile.md no longer says "latest match-log row"/export-side (§5 dbt-derived
    most-recent-match; §4/§8 updated; §10 GAP-16 removed); 99_gaps_register.md GAP-16 marked shipped + Option-B note.
  - `python scripts/check_layer_contract.py` passes; dbt build + DQ in ci-data-build (dbt CLI broken locally).
  - scope-auditor + analytics-engineer + cto + bi-analyst PASS (>=2 risks each); review.md binds the staged
    diff; CPO merges (never self-merge).

amendments: (none)
