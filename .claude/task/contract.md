# Task contract — handover: the #69 dims are merged (bookkeeping)

objective: >
  `active_work.md` still reads "NEXT: `dim_country` + `dim_region`, then FKs". Both are built,
  reviewed and merged (`!61`). That is a WRONG LIVE INSTRUCTION, not stale trivia — a fresh session
  is handed this file and nothing else, and would set out to build what already exists. Correct it
  to name step 5 (the four foreign keys) as the next action.
refs: GitLab #69 step 3 (`!61`), #62 step 3 (still blocked on step 5)

scope_paths:
  - .claude/active_work.md

impact_map: >
  Bookkeeping short-form. `.claude/active_work.md` is read by the session-start hook and by humans;
  no job, model, test or script reads it (`grep -rn "active_work" .gitlab-ci.yml scripts/
  dbt_project/` returns nothing outside the governance hooks that only enforce its character cap).
  Blast radius: what the next session is told to do. No code, no data, no cost.

decisions_taken: >
  No decision. This records an already-merged state.

  ⚠ WHY THIS IS A SEPARATE MR RATHER THAN PART OF `!61`: another chat has been editing this file
  throughout the day and owns the #75 thread in it. `!61` deliberately left it out to avoid racing
  a 16,000-character capped file, which had already produced two rebase conflicts. There are ZERO
  open MRs at the time of writing, so this is the safe window.

  ⚠ A COMMIT TOUCHING `contract.md` IS NEVER ARTIFACT-EXEMPT (`artifact_only_never`), so this
  bookkeeping change takes a review round it would otherwise skip. That is the rule working as
  intended, not overhead to route around: `active_work.md` must be in `scope_paths` to be edited,
  and putting it there means editing the contract.

decisions_reserved:
  - Nothing. #69 step 5 (the four foreign keys) and #62 step 3 (`mart_competition_index`, still
    parked in the stash) are named as next actions, not decided here.

done_when:
  - The `NEXT:` line names step 5, not the merged dims.
  - `dim_country` / `dim_region` are recorded as merged, with what they do and do not guarantee.
  - The file stays under 16,000 CHARACTERS, measured with Python `len()`.

amendments: (none)
