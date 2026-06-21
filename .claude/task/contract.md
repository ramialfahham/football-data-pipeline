# Task contract — Recover null event team_id from sibling events (DQ fix)

objective: >
  Fix the real DQ defect surfaced by the deep backfill: some old API-Football /fixtures/events
  records carry team.name but a null team.id (mostly Card events), so fct_fixture_event.team_sk is
  null -> the not_null_fct_fixture_event_team_sk test fails (broke main's 2026-06-21 nightly + #524).
  Recover the null team_id in base_apif__fixture_events from the SAME team's other events in the same
  fixture (the team has a valid id on its goals/subs), keyed by (league_code, fixture_id, team_name).
  This is CPO-chosen Option A (recover, not drop) — preserves the events (cards stay attributed).
refs: >
  This conversation 2026-06-21 (CPO: Option A — recover). Failure: not_null_fct_fixture_event_team_sk
  (11 events, PD/SA 2016-era; e.g. Eibar id 545 valid on goals, null on cards in fixture 27411).
  Traced to RAW. Surfaced by the #520/#523 deep backfill.

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__fixture_events.sql
  - dbt_project/models/3_core/fct_fixture_event.sql
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - .claude/task/**

decisions_taken: >
  CPO chose Option A (recover) over dropping, in this conversation (2026-06-21). Layer: base
  (raw cleanup / first logic) — the recovery is a within-source derivation (no cross-entity join,
  no schema change). Mechanism: coalesce(team_id, max(team_id) over (partition by league_code,
  fixture_id, team_name)) applied only when team_id is null and team_name is not null, AFTER the
  existing dedup. Verified this session: all current null-id (fixture, team_name) groups have exactly
  ONE sibling non-null id, so recovery is unambiguous. Non-null team_id rows are unchanged (no impact
  on existing events). The existing not_null_fct_fixture_event_team_sk test (core.yml) stays as the
  regression guard for the outcome; recovery correctness rests on the per-fixture name->team uniqueness
  invariant (a fixture has two distinct teams with distinct names).

decisions_reserved:
  - A team whose events in a fixture are ALL null-id (no goal/sub with a valid id) is not recoverable
    within-events and would still null -> the not_null test would catch it. If the Phase 2a deep data
    surfaces such a case, extend with a fixture-home/away-team fallback (needs team names in the
    fixtures chain) — NOT built now (no current case; the test is the guard).
  - dbt 1.7.19 has no unit-test framework, so no unit test is added; the singular not_null test guards.
  - Finding 1 (wrong-id guard): a broad "event team_api_id in {fixture home, away}" test is NOT added
    — it fails on 38 PRE-EXISTING non-null events (team not in the fixture's two teams), unrelated to
    this recovery (which only fills NULLs). The recovery cannot create a wrong id beyond the negligible
    two-teams-share-a-name case; not_null + relationships(team_sk -> dim_team) guard the outcome. The 38
    pre-existing rows are a separate DQ defect to file as a follow-up issue.

done_when:
  - base_apif__fixture_events recovers null team_id as specified; non-null rows unchanged.
  - dbt parse + sqlfluff clean; recovery verified empirically (all 11 current null events recover to
    the correct team id).
  - HEALING (finding 2): fct_fixture_event is incremental on raw_ingested_at, so already-committed null
    rows are NOT healed by the base fix alone. A SELF-HEAL clause in fct_fixture_event's incremental
    filter re-processes any fixture currently holding a null team_sk, so the next NORMAL ci-data-build
    heals the committed rows via the unique_key merge (no manual --full-refresh — that op is blocked by
    the no-local-build rule). Self-limiting once healed; also resilient to future stray nulls.
  - not_null_fct_fixture_event_team_sk PASSES on the fix PR's ci-data-build. Unblocks main; then #524 is
    rebased on the merged fix and re-runs green.
  - Standings: base_apif__standings ALREADY drops null team_id (`where team_id is not null`) and
    fct_standings.team_sk ALREADY has not_null + relationships(dim_team) — the cleaned layer is guarded.
    The failing not_null_stg_apif__standings_team_id test is MIS-PLACED on FAITHFUL staging (which the
    provider can leave null, e.g. UEL 2017), inconsistent with events staging (no such test). Fix:
    remove that one staging-layer test. DQ preserved at core; no base/core SQL change.
  - Player id-collision: base_apif__fixture_players drops player legs where one player_id appears under
    >1 team in a fixture (provider id-reuse; both legs unattributable; verified surgical — 2 pairs / 4
    rows, AFCCL 2016). This prevents NEW collisions entering fct_fixture_player_stats. The ALREADY-
    committed rows (fct is incremental; a merge cannot delete — unlike the events self-heal which is an
    UPDATE) are removed by a one-time CPO-authorized (Option B) `dbt run --select base_apif__fixture_players
    fct_fixture_player_stats --full-refresh` — EXECUTED 2026-06-21 (1.7M rows rebuilt from the clean base;
    verified 0 remaining collisions). int_legs__player_match + mart_player_match_log (both materialized
    tables, full-rebuilt from the clean fct) (fixture,player) grain tests then PASS on ci-data-build.

amendments:
  - 2026-06-21: analytics-engineer FAIL on the player-collision — base_apif__fixture_players prevents NEW
    collisions but does NOT heal the 4 ALREADY-committed rows in the incremental fct_fixture_player_stats
    (merge cannot delete; the events self-heal pattern is an UPDATE, this is a DELETE). Both failing grain
    tests (int_legs__player_match, mart_player_match_log) read fct directly. CPO chose Option B (one-time
    full-refresh) over dropping in the two full-rebuild consumers. EXECUTED the CPO-authorized
    `dbt run --select base_apif__fixture_players fct_fixture_player_stats --full-refresh` (1.7M rows; 0
    remaining collisions). No int_legs/mart change. Authority: CPO "Execute B" (2026-06-21).
  - 2026-06-21: enumerated the COMPLETE deep-backfill defect set via one clean build (backfill stopped,
    stable RAW). Result: bounded — events (recovered), standings (test relocated), and a player id-collision
    in base_apif__fixture_players (the provider reused one player_id for two different players in a fixture,
    one per team — e.g. AFCCL 2016 id 44061; verified surgical: exactly 2 (fixture,player) pairs / 4 rows,
    no false positives). Recent seasons are CLEAN (0 dupes across 280k+ legs/season) — disproving any
    "just don't ingest old data" framing; these are ~15 specific fixable rows, fixed properly, all deep
    history kept. FIX: extend base_apif__fixture_players's existing cross-team phantom-leg cleanup (today
    only player_id=0) to drop real-id collisions too (player under >1 team in a fixture -> both legs
    dropped, unattributable). Added base_apif__fixture_players to scope. Authority: CPO "yes" to the
    rigorous fix-all-defects plan (2026-06-21); existing player_id=0 cleanup precedent.
  - 2026-06-21: analytics-engineer FAIL (2 findings). FIX: (a) finding 2 (incremental heal) — added the
    one-time fct_fixture_event --full-refresh deployment step to done_when; the base fix alone does not
    heal already-committed incremental rows. (b) finding 1 (wrong-id guard) — recorded why the broad
    integrity test is deferred (38 pre-existing non-null violations) + to file separately. No base-model
    change (it is correct). Authority: the reviewer FAIL + standing DQ rules (clean-tree amendment;
    code change stashed during the edit).
  - 2026-06-21: CPO chose Option 1 (self-heal) over the manual full-refresh — the full-refresh is blocked
    by the no-local-build rule (and ci-data-build only builds incrementally). Added scope_path
    dbt_project/models/3_core/fct_fixture_event.sql + a self-heal clause in its incremental filter
    (re-process fixtures with a null team_sk) so the heal runs via the normal ci-data-build, no manual
    shared-warehouse op. Authority: CPO directive this conversation (2026-06-21).
  - 2026-06-21: the deep backfill surfaced the SAME null-team_id quirk in old standings (UEL 2017, 2
    rows), blocking #527 at the staging step. Investigation: base_apif__standings ALREADY filters
    `where team_id is not null` and fct_standings.team_sk ALREADY has not_null + relationships(dim_team)
    — the cleaned layer was always guarded. The only defect is the not_null test mis-placed on the
    FAITHFUL staging column (which the provider legitimately leaves null), inconsistent with events
    staging (no such test). Fix = remove the staging-layer not_null on stg_apif__standings.team_id (a
    yml change; NO SQL change). Scope corrected: stg_apif__generic.yml (not the .sql). Enumerated the
    class as bounded (fixture_players 0 nulls, fixture_lineups no team_id). Folded into #527. Authority:
    layering rule (staging = faithful flatten; cleanliness tests live on the cleaned layer) + DQ preserved
    at core; CPO directed resolving #527 (2026-06-21).
