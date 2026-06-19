# Task contract — fix: idle-mode fixtures snapshot completeness (PR1 of 2 — the ingestion fix)

> The append-complete-snapshot contract (data_contract.md "Append-only writes": every appended fixtures
> snapshot is COMPLETE, so the latest row carries full history) is honored in full ingest mode but broken
> in poll/idle mode: a finished/idle league writes a current-season-only snapshot, which becomes "latest",
> so the full-refresh fct_fixture rebuilds down to one season (verified: BL1 308 in fct_fixture vs 3075 in
> fct_fixture_player_stats). PR1 fixes the ingest WRITE path so every snapshot stays complete. NO dbt
> materialization change (fct_fixture stays full-refresh — CPO-confirmed: incremental would be an
> anti-pattern here). The ALARM (restore the suppressed fanout FK tests + fix their descriptions) is PR2,
> a follow-up AFTER the post-merge recovery — CI-timing forces the split (see decisions_reserved).
> Design + 2-PR split settled with CPO this conversation 2026-06-19. See working_agreement.md §2/§10/§11.

objective: >
  Enforce the "every fixtures snapshot is complete" invariant at the WRITE boundary in
  fetch_merge_and_persist_fixtures: carry forward the cached historical seasons (from the previous
  snapshot it already reads for the #283 cache-skip) into the written snapshot, so poll/idle runs no
  longer thin it. Squad-catch-up team scoping is preserved — team_ids/fixture_ids are derived from the
  freshly-fetched current season BEFORE the carry-forward (the documented "latest-season team list"
  behavior in run_poll_phases / select_squad_catchup_team_ids). Full mode is unaffected (its season list
  already covers everything → carry-forward is a no-op). Plus unit tests and a one-sentence accuracy fix
  to the data_contract.md "Append-only writes" paragraph (poll/idle now carries forward rather than
  re-fetching).

refs: >
  This conversation 2026-06-19. Root cause: catalog.py poll_mode collapses seasons_list to [current];
  fetch_merge_and_persist_fixtures then writes a current-season-only snapshot. Fix at the write boundary
  in fixtures.py (keep the poll collapse — it provides the documented latest-season team scoping). The
  suppressed FK tests are core.yml lines 593/543/~676 ("No FK test: fct_fixture covers current-season
  snapshots only") — PR2 restores them. Emerged while investigating NEXT #1 (the backfill); prerequisite.

scope_paths:
  - ingestion/api_football/loads/fixtures.py
  - tests/test_fixtures_snapshot_completeness.py
  - tests/fixtures/apif/**
  - docs/data_contract.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO-confirmed this conversation: fct_fixture STAYS full-refresh table (incremental is an anti-pattern —
  a full-refresh would re-lose history; no perf need at this volume); the dbt read path is unchanged; the
  fix belongs in ingestion (the append-complete-snapshot contract was violated by idle mode). The 2-PR
  split is CPO-approved: PR1 = this ingestion fix; PR2 = the alarm. Alarm severity = HARD-FAIL (PR2).
  Storage hygiene (expiring old snapshots) = DEFERRED. The PL/PD/SA/L1 deep-season backfill = DEFERRED.

decisions_reserved:
  - PR2 (the alarm): restore the three fanout FK relationship tests (fixture_sk -> fct_fixture on
    fct_fixture_player_stats / _team_stats / _event) + correct the "current-season snapshots only"
    descriptions. Deferred to a follow-up PR AFTER recovery, because ci-data-build runs `dbt test` on the
    PR against the warehouse, which stays thin until recovery — so the restored tests would fail on a same-PR.
  - One-time RECOVERY (run BL1 full-mode once so a complete snapshot lands; verify PL/PD/SA/L1) is a
    POST-MERGE operational step, NOT in this diff. ~10 provider calls (BL1 season lists; fanout untouched) —
    the one budget spend, only after merge with CPO go.
  - The carry-forward reads the LATEST snapshot for history; if it is thin (pre-recovery) it carries
    nothing — recovery re-establishes a complete latest snapshot, after which poll runs keep it complete.
    If the fix is found to need reading the last COMPLETE snapshot instead, STOP and escalate (larger change).

done_when:
  - fixtures.py: the written fixtures snapshot includes every season from the previous snapshot it reads
    (carry-forward), so a poll/idle run never reduces season coverage; team_ids/fixture_ids computed from
    the freshly-fetched seasons (pre-carry-forward) so squad catch-up stays latest-season-scoped; full-mode
    behavior unchanged (carry-forward no-op when the season list already covers all prior seasons).
  - fixtures.py (data-engineer Finding 2): when the FRESH fetch returns no fixtures (e.g. quota exhausted
    before the current season is fetched), the run writes NO new snapshot — the prior complete snapshot
    stays "latest" — so a failed run never re-stamps a stale/empty snapshot as today's. Error still logs.
  - tests/test_fixtures_snapshot_completeness.py: (a) a poll-style single-season fetch with a complete
    cached snapshot writes a COMPLETE snapshot; (b) team_ids exclude carried-forward-only seasons' teams;
    (c) full-mode no-op; (d) empty/thin cache carries nothing; (e) an empty/quota-exhausted fresh fetch
    writes NOTHING (Finding 2). The carry-forward + completeness tests exercise a REAL committed /fixtures
    payload under tests/fixtures/apif/ (CPO sample-payload rule 2026-06-12), not inline dicts.
    Run: python -m pytest tests/test_fixtures_snapshot_completeness.py -q.
  - docs/data_contract.md "Append-only writes": the paragraph reflects that poll/idle runs keep the
    snapshot complete by carrying forward prior seasons (not by re-fetching them).
  - validate-local passes (sqlfluff / dbt parse / offline pytest gates).
  - Commit on branch fix/idle-snapshot-completeness; post-commit opens the PR.
  - reviewers: scope-auditor + data-engineer (ingestion + data_contract) + cto (tests) PASS (each >=2 named
    risks); no FAIL; no ESCALATE. (analytics-engineer NOT required — PR1 touches no dbt model/test.)

amendments:
  - 2026-06-19: + tests/fixtures/apif/** — authority: data-engineer reviewer FAIL (Finding 1: the CPO
    sample-payload rule 2026-06-12 requires offline tests against committed sample payloads under
    tests/fixtures/apif/, which never existed) + CPO ruling this conversation to bootstrap it minimally
    (option a). Content: a REAL BL1 /fixtures snapshot slice extracted from RAW_APIF_FIXTURES_NEXT (no
    fabrication, no API spend) that the carry-forward / completeness tests exercise. Also folded in the
    Finding 2 fix (no write on an empty fresh fetch) — within the existing fixtures.py scope, no new path.
