# Task contract — the completeness gate must know a deliberate skip is not a gap

objective: >
  THE PROD NIGHTLY IS FAILING AGAIN, and this one is ours. The 2026-08-14 04:00 run exited 3
  during INGESTION, before dbt:

      Completeness gate failed: per-team gaps not healing: UCL/TRANSFERS (1 then 1 teams missing)

  `detect_stagnant_per_team_gaps` hard-fails when a (league, entity) pair has missing teams on TWO
  CONSECUTIVE RUNS. Its stated reasoning is that a single bad run "self-heals" on the next night's
  fetch, so two in a row means it is not healing.

  **#33 item 14 invalidated that assumption on 2026-08-11.** It put `transfers` on a 7-day
  per-league re-fetch cadence, skipping the phase ENTIRELY when a league is not due. A skipped
  league cannot heal, by construction — there is no fetch. So a real, pre-existing 1-team gap in
  UCL/TRANSFERS now sits unfetched for up to 7 days and trips a gate designed for a nightly fetch.

  Nothing is wrong with the data. The gate is asking a question that stopped making sense.

  This teaches the gate which (league, entity) pairs were deliberately skipped this run, and makes
  it decline to call those stagnant.
refs: >
  GitLab #33 (items 14 and the completeness work). Regression introduced by !31 (item 14),
  surfaced by the 2026-08-14 nightly.

scope_paths:
  - ingestion/api_football/completeness.py
  - ingestion/api_football/orchestrator.py
  - ingestion/api_football/loads/context.py
  - ingestion/api_football/loads/competition_runner.py
  - tests/test_per_team_completeness.py
  - tests/test_completeness_outcome_and_summary.py
  - tests/test_refetch_cadence.py
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/review_input.patch

impact_map: >
  REQUIRED — `ingestion/**` is the structural surface.

  what fails today, traced end to end:
    `loads/competition_runner.py:200` — `if not should_refetch(...): _skipped_phase(...); return`
      (item 14). No fetch, no write, and NOTHING records that the skip happened.
    `orchestrator.py:281` — `per_team_missing = per_team_missing_by_league_entity(per_team)`
      counts missing teams for `PER_TEAM_GATED = ("PLAYERS", "SQUADS", "TRANSFERS")`.
    `completeness.py:403 detect_stagnant_per_team_gaps(current, prior)` — flags any pair present
      in BOTH, with no knowledge of whether a fetch was even attempted.
    `orchestrator.py:370` — a non-empty result is a hard fail, `exit(3)`, and the dbt build never
      runs. That is why `dbt_analytics` is stale again.

  the near-miss that proves the shape: `COACHES` is in `PER_TEAM_ENTITIES` but deliberately NOT in
    `PER_TEAM_GATED` (`completeness.py:49-53`) — "a permanently-red gate trains everyone to ignore
    the alarm". Item 14 put coaches AND transfers on the same 7-day cadence, but only transfers
    gates, so only transfers breaks. The exclusion that saved coaches was written for a different
    reason and covered this by luck.

  writers: none. No loader, no raw table and no BigQuery write is touched. `should_refetch` itself
    is NOT modified — the cadence is a CPO ruling and stays exactly as it is.

  downstream: no dbt model, no mart, no page. This changes only whether the ingest process exits
    non-zero. Nothing reads the completeness snapshot except the gate itself and the markdown
    summary.

  layer_rules: none engaged — no dbt file is touched.

  deploy_order: nothing breaks at any point. ⚠ THE NIGHTLY RUNS AN IMAGE, so merging does not
    deploy this; it needs `gcloud run jobs deploy fdp-nightly --source . --region europe-west1`
    from `main`. Until that runs, the nightly keeps failing every 04:00.

  blast_radius: **the gate stops firing on deliberately-skipped pairs and keeps firing on
    everything else.** No number changes anywhere.

decisions_taken: >
  CPO ruling, in-thread 2026-08-14, after being shown the two options in plain language: **"Do as
  recommended"**, i.e. option 1 — teach the check to ignore nights where we skipped on purpose.
  Recorded in `escalations.log` before this contract.

  THE REJECTED OPTION AND WHY IT MATTERS: option 2 was to drop `TRANSFERS` from `PER_TEAM_GATED`,
  matching the existing COACHES precedent. It is a smaller diff and it would work. It was
  recommended AGAINST and the CPO agreed, because it removes real coverage — transfers gaps would
  stop failing the run permanently — to work around an assumption WE broke. The repo's standing
  rule is to narrow a guard to where it still holds, not to delete the assertion.

  # THRESHOLD DECLARATIONS
  NEW MECHANISM — no. One field on an existing dataclass, one argument on an existing function.
    No new service, dependency, table or lifecycle step.
  RECURRING COST — none. No extra API call, query or storage; this is process-exit logic.
  GUARD LOOSENED — ⚠ **YES, NARROWLY, AND THIS IS THE DECLARATION THAT MATTERS.** The gate will
    no longer fail on a (league, entity) pair that was deliberately skipped this run. That is
    precisely the case where it is currently WRONG, and the repo's rule is to narrow a guard to
    where it still holds rather than delete it. What it must keep catching, and what the tests
    must prove it still catches: a pair that was FETCHED on both runs and is still missing teams.
    A skip must never be silent — it is logged, so a permanently-skipped league cannot hide a real
    gap unnoticed.
  SHIPPED NUMBERS — no.

decisions_reserved:
  - Whether a league whose transfers are skipped for many consecutive runs should eventually be
    force-fetched so a real gap cannot hide behind the cadence indefinitely. The 7-day cadence
    bounds it to 7 days, which is why this is not urgent, but it is a genuine question and it is
    the CPO's.
  - Whether `TRANSFERS` belongs in `PER_TEAM_GATED` at all. Left exactly as it is here.
  - The UCL/TRANSFERS 1-team gap itself. This task makes the gate correct; it does not
    investigate whether that one team is a real ingestion defect. Filed separately if it persists
    once transfers are next due.

done_when:
  - `pytest tests/ -q` exits 0 (baseline on this branch's base, main @ a13c16e: 789 passed,
    1 skipped).
  - `ruff --config .ruff-ci.toml ingestion/ tests/` exits 0.
  - ⚠ VERIFIED BY BREAKING THE SUBJECT, both directions, because a gate that stops failing is
    exactly the change that must be proven to still fail:
      · a pair skipped this run and missing on both runs -> NOT flagged (the fix)
      · a pair FETCHED on both runs and missing on both -> STILL flagged (the guard survives)
      · a pair skipped this run but flagged for a DIFFERENT league/entity -> still flagged
    Each confirmed by running the tests against the pre-fix behaviour and watching them go red.
  - The skip is VISIBLE: the run logs which pairs were exempted, so a permanently-skipped league
    cannot hide a real gap silently. Asserted by a test on the emitted text, not by eye.
  - POST-MERGE, and NOT satisfiable from this branch: redeploy the image from `main`, then confirm
    the next 04:00 run reaches the dbt build with `ERROR=0` instead of `exit(3)`.

amendments:
  - 2026-08-14: `tests/test_completeness_outcome_and_summary.py` -> `tests/test_per_team_completeness.py`
    in `scope_paths`. No widening: one test path swapped for another, same count. Authority: none
    needed — the first draft named the wrong file from its title alone. `detect_stagnant_per_team_gaps`
    and `evaluate_completeness_outcome`'s per-team behaviour are covered in
    `tests/test_per_team_completeness.py` (it imports both at lines 26-29 and exercises the gate at
    318-324); the file originally listed covers a different part of the module and is not touched.
    Caught by the contract gate on the first test edit, which is the gate doing its job.
  - 2026-08-14: + `tests/test_completeness_outcome_and_summary.py` (so BOTH test files are now in
    scope, not a swap). Authority: the STANDING CPO RULE of 2026-08-08 in `escalations.log` —
    "Updating a reference that an approved change itself breaks is part of that change ... provided
    the update is confined to the reference and changes no behaviour."
    WHAT BROKE AND WHY IT IS RIGHT THAT IT DID: `test_skipped_report_returns_no_failures` asserts
    the outcome dict by EXACT EQUALITY, and its own comment says that is deliberate — "kept inside
    the exact-equality assertion rather than relaxed to a subset". Adding the
    `skipped_per_team_exempt` key therefore failed it. That is the guard working exactly as
    designed: a new key in the outcome contract must be a conscious act, not something that slips
    in. The edit adds that one key to the expected dict and changes nothing else.
