# Task contract — a real case for each cleaning rule left without one

objective: >
  The second player-stats fetch took the only answer-key case of three team rules and three player
  rules. Add, for each, a real match where the rule fires on the latest fetch, worked by hand from
  the provider's raw values. Step 2 of #203.

refs: >
  #203.

acceptance_criteria:
  - Every cleaning rule keeps at least one real case in its answer key (the second fetch took the only case of three team rules and three player rules)

scope_paths:
  - dbt_project/seeds/player_match_cleaning_answer_key.csv
  - dbt_project/seeds/team_match_cleaning_answer_key.csv
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  Readings, under the delegation of 2026-10-02:
  - Each case is a match with one fetch, in the format that carries goals conceded, so a later
    fetch or the fix of #205 cannot move it. Each value is worked from the raw payload, never from
    a model, and equals the model.
  - Team opponent_shots_on_target_unverified fires on no match in prod, so it has no real case to
    add; the MR head says so.
  - Both keys go in one MR, as the four keys did in step 1.

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - None.

done_when:
  - The MR data build runs both cleaning answer-key tests and they pass.
  - pytest (whole suite) and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
