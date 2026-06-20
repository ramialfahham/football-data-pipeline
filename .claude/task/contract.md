# Task contract — Make history_seasons authoritative + backfill PL to BL1 parity (2016)

objective: >
  Refactor the season-depth config so the per-competition `history_seasons` (registry) is the
  authoritative depth knob, not silently clamped by a global v1 constant; retire that constant
  (`V1_SEASON_WINDOW_YEARS` -> `DEFAULT_SEASON_WINDOW_YEARS`) to a default-only role. Then apply it
  to PL: hs=11 -> 2016-2025 finished (true BL1 parity) + 2026 in-progress, deterministically (no
  July-1 date dependency). This is the robust fix replacing the fragile date-dependent hs=11 patch.
refs: >
  #479 (deep-season backfill); docs/content_architecture.md §8/§9; CPO Path-A decision in this
  conversation (2026-06-20): "make history_seasons authoritative + retire the v1 constant, then PL
  -> 2016 cleanly". The CPO flagged V1_SEASON_WINDOW_YEARS as an unacceptable v1 artifact and the
  season-depth config as not robust.

scope_paths:
  - ingestion/api_football/settings.py
  - ingestion/api_football/season_inference.py
  - ingestion/api_football/seasons.py
  - ingestion/api_football/orchestrator.py
  - tests/test_season_inference.py
  - tests/test_seasons_for_ingestion.py
  - docs/data_contract.md
  - docs/working_agreement.md
  - docs/competition_registry.yml
  - .claude/task/**

decisions_taken: >
  CPO chose Path A (2026-06-20). (1) BEHAVIOUR: in seasons._seasons_for_ingestion, when
  history_seasons is set the band lower bound becomes lo = resolved_current - (history_seasons - 1)
  with NO max(global_lo, ...) clamp — history_seasons fully determines depth (can now exceed the
  default window, and is date-independent). When history_seasons is UNSET, the default window floor
  (effective_season_min) still applies. (2) RENAME: V1_SEASON_WINDOW_YEARS -> DEFAULT_SEASON_WINDOW_YEARS
  (internal constant, default-only role). (3) Economy/default profile output is UNCHANGED for existing
  configs — the MAX_SEASONS cap is a separate, later branch (verified: a wider band is still truncated
  to the last MAX_SEASONS). (4) PL history_seasons 10 -> 11 (offsets the provider's current_season=2026,
  one ahead of BL1's 2025) -> reaches 2016. (5) Re-run the PL backfill to fetch 2016 (incremental).
  Authority: working_agreement §2 (amendment, clean tree) + the CPO's explicit Path-A approval; the
  constant change is pre-confirmed in-thread per working_agreement §156.

decisions_reserved:
  - Phantom-current-season hardening (anchor depth to the latest FINISHED season, so PL could use
    hs=10 like BL1) — CPO ruled SEPARABLE (2026-06-20); filed as a follow-up, NOT in this PR.
    Documented consequence: PL uses hs=11 vs BL1's hs=10 to reach the same finished depth.
  - PD/SA/L1 + Phase 2 per-type depths — deferred; a separate cost decision after PL.
  - The new constant name (DEFAULT_SEASON_WINDOW_YEARS) is agent-chosen (internal, not user-visible);
    CPO may override.

done_when:
  - history_seasons authoritative: new tests in tests/test_seasons_for_ingestion.py prove (a) under the
    full profile an explicit history_seasons reaches below the default floor (monkeypatched), and
    (b) unset history_seasons still clamps to the default window. Existing season tests pass under the
    renamed constant.
  - V1_SEASON_WINDOW_YEARS fully retired: `git grep V1_SEASON_WINDOW_YEARS` returns 0 (code + docs).
  - Registry PL history_seasons = 11; check_registry_var_sync.py green.
  - validate-local gates (ruff/pytest/sqlfluff/dbt parse) green locally before push.
  - Backfill re-run (full profile, LEAGUE_CODES=PL): PL RAW shows 2016-2026 (2016-2025 finished),
    fanout 100%; measured call delta captured and reported.
  - ci-data-build green on the PR (relationship/orphan tests against the new RAW).

amendments:
  - 2026-06-20: EXPANDED from the one-line PL history_seasons=10 change to the season-depth config
    refactor (Path A). Authority: CPO Path-A approval in this conversation. Added scope_paths:
    ingestion/api_football/{settings,season_inference,seasons,orchestrator}.py, tests/test_season_inference.py,
    tests/test_seasons_for_ingestion.py, docs/data_contract.md, docs/working_agreement.md.
    PL history_seasons target changed 10 -> 11.
