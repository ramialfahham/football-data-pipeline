# Task contract — the five wrong or duplicated lines the #186 change left in docs and comments

objective: >
  Step 1 of the cleanup the CPO approved on 2026-10-05: correct what the #186 change (player stats
  fetched a second time) wrote wrongly. Two false sentences in docs/data_contract.md, the second-fetch
  rule written out again in docs/operations_guide.md, measured figures in a coverage.py comment, and the
  stale table name in the orchestrator comment next to the line #186 changed.

refs: >
  #186 (closed); the cleanup plan approved 2026-10-05, step 1: "MR: fix my 6 errors from #186
  (data_contract.md x2, operations_guide.md, coverage.py, orchestrator.py:209, #186 How step 1)".
  The sixth (#186 How step 1) was an issue edit, already made. #196 holds the rest of the ingestion
  findings.

scope_paths:
  - docs/data_contract.md
  - docs/operations_guide.md
  - ingestion/api_football/coverage.py
  - ingestion/api_football/orchestrator.py
  - ingestion/api_football/loads/batch_fixtures.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  Comment-only change in ingestion/**: one comment line in coverage.py above SECOND_FETCH_DELAY and one in
  orchestrator.py above the Phase 2 call; no code token changes (`git diff --word-diff` shows only `#`
  lines). No table, model or mart is written or read differently; no dbt file changes; blast radius none.

decisions_taken: >
  The approved step 1, quoted in refs. Corrections, each checked against the code:
  - data_contract.md "fixture_id is not a uniqueness key": `read_coverage` is not "the one coverage read per
    run" — the orchestrator reads it before Phase 2 and completeness reads it again after (orchestrator.py,
    completeness.py); the clause goes.
  - data_contract.md "Second fetch": player stats are not covered only from the moment the second fetch is
    due until it is made (`second_fetch_due`), not from the first fetch.
  - operations_guide.md: the rule is owned by data_contract.md "Fixture details"; the guide keeps the
    coverage exception as a link, without restating the timing.
  - coverage.py: the measured percentages belong in #186; the comment keeps the reason in one line.
  - orchestrator.py: the details table is the unified RAW_APIF_FIXTURE_DETAILS (batch_fixtures writes
    `raw_table("FIXTURE_DETAILS")`).

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - none: every correction restores agreement with the code; the wider ingestion findings are #196.

done_when:
  - pytest tests/test_coverage.py tests/test_batch_fixtures.py, ruff with .ruff-ci.toml and the offline
    gates pass; tests/test_no_decision_history_in_docs.py passes.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.

amendments:
  - 2026-10-05: + ingestion/api_football/loads/batch_fixtures.py — authority: the approved step 1 (the
    #186 change's own wrong lines); content: the module docstring and the step's docstring call
    `read_coverage` "the run's single" read, the same false claim as data_contract.md; both docstrings
    lines only, no code token.
