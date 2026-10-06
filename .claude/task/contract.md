# Task contract — answer keys re-worked from the provider's latest fetch

objective: >
  The 6 Oct nightly failed four answer-key tests (39 rows): the second player-stats fetch replaced
  the provider data the keys were worked from. Re-work each failing value by hand from the latest
  fetch and update the four seeds. Step 1 of #203; the cases for rules left without one are step 2.

refs: >
  #203.

acceptance_criteria:
  - The four answer-key tests pass on prod: every failing value re-worked by hand from the provider's latest fetch

scope_paths:
  - dbt_project/seeds/player_season_answer_key.csv
  - dbt_project/seeds/team_season_answer_key.csv
  - dbt_project/seeds/player_match_cleaning_answer_key.csv
  - dbt_project/seeds/team_match_cleaning_answer_key.csv
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - docs/tracker/**

decisions_taken: >
  Readings, under the delegation of 2026-10-02:
  - The keys' own definition is "worked out by hand from the provider's raw match data", and base
    keeps the newest fetch, so a key follows the latest fetch. Each value is worked from the raw
    payloads (first and latest fetch compared), never from a model; every one equals the model.
  - A player's rows that use a changed total (his minutes or passes) are updated even where the
    value happens not to change (a zero numerator), so no working names a stale total.
  - Where a cleaning case's rule no longer fires on the latest fetch, its rule column is blank and
    its working says why; replacing the lost cases is step 2 of #203.

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - None.

done_when:
  - The MR data build runs the four answer-key tests and they pass.
  - pytest (whole suite) and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
