# Task contract — #61: the alert-policy apply recipe under-deploys

objective: >
  `deploy/nightly/README.md` documents how to create the Cloud Monitoring alert policies. Its
  apply step ends in `for i in 0 1`, a HARDCODED index list, over a generator that writes one
  payload per policy declared in `deploy/nightly/alert-policy.json`. The file has since grown to
  three policies, so index 2 was written and never POSTed.

  This was not theoretical. `fdp freshness sentinel itself stopped` — the watcher that detects
  the monitoring itself having died — was declared and never deployed. Found 2026-08-11 while
  deleting the superseded 25h bridge policy; the two together would have left the "nightly and
  sentinel both dead" case with no alert at all.

  It FAILS OPEN, and that is the whole character of the bug: the dropped policy is the one whose
  absence is invisible, so nothing about the broken state looks broken.

  Two defects, one cause. (a) the count is hardcoded where it should be derived; (b) the prose
  one line above still says the file "holds BOTH policies". Both are the same rot: a literal
  standing in for something the file already knows.
refs: GitLab #61. Found under #33 / #39 Stage 2.

scope_paths:
  - deploy/nightly/README.md
  - tests/test_alert_policy_recipe.py
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/review_input.patch

impact_map: >
  Not gate-required — neither `deploy/**` nor `tests/**` is on the structural surface
  (`ingestion/**`, `dbt_project/models/**`, `scripts/export_*.py`, `site*/`, protected paths).
  Written short-form and evidenced anyway, because the subject is a PRODUCTION MONITORING
  recipe and "it is only a README" is the reading that let the bug ship.

  what executes this: nothing automated. `grep -rln "alertPolicies" --include=*.py --include=*.sh
    --include=*.yml .` returns ZERO files — the recipe is run BY HAND by the operator, which is
    exactly why nothing caught the dropped policy. `.gitlab-ci.yml` and
    `deploy/nightly/entrypoint.sh` never touch Cloud Monitoring.

  blast_radius: none at runtime. No pipeline, no dbt model, no ingest and no deployed job reads
    `deploy/nightly/README.md`. Changing it cannot alter a number, a table or a schedule. The
    effect is entirely on what a human does the NEXT time policies are applied.

  layer_rules: none engaged. No dbt model, no seed, no `league_code`.

  deploy_order: irrelevant — nothing is deployed by this change. ⚠ AND NOTHING NEEDS TO BE: the
    missing policy was already created by hand on 2026-08-11 (`alertPolicies/751471063453009885`)
    and live state already matches `alert-policy.json`. This task fixes the RECIPE so the gap
    cannot recur; it does not re-fix the instance.

decisions_taken: >
  ⚠ THE AUTHORITY, STATED EXACTLY, because a first draft of this contract overstated it and
  `scope-auditor` FAILed that correctly. The CPO ruling is **"go ahead"**, and it was given to
  GitLab #61 as filed — NOT to a three-part plan, which the builder described only AFTERWARDS.
  The earlier wording ("approved in-thread after being shown the three proposed fixes") reversed
  that order and dressed a builder decision as a quoted ruling. It is corrected here and the
  ruling is recorded in `.claude/task/escalations.log` (entry "2026-08-12 — #61"), which is
  visible to reviewers precisely so a claimed authority can be checked against something other
  than this file.

  Items 1 and 2 of #61 (derive the loop, correct the stale prose) ARE the filed bug and need no
  authority beyond "go ahead".

  ITEM 3 (IDEMPOTENCY) IS A BUILDER DECISION, not a ruling. #61 lists it as "consider", and the
  builder took it. Declared as builder-derived so it can be attacked on its merits:
  the README today DOCUMENTS the hazard rather than removing it — it warns that re-running
  creates duplicate policies and that duplicates are "how people learn to ignore alerts". A
  recipe that must be run carefully is the same class of defect as a count that must be updated
  carefully, and this task exists because that class already failed once in production. It
  crosses no §10 line: no new mechanism, no cost, no product or naming decision, nothing
  permanent. If the CPO disagrees, item 3 can be reverted on its own without touching items 1
  and 2.

  A TEST IS ADDED, and this is the point of the task rather than a nicety. The repo's standing
  rule is that a prose rule which recurs needs a mechanism; this one rotted silently and cost a
  real monitoring gap. `tests/test_nightly_entrypoint_parity.py` is the precedent — it pins a
  deploy artefact's step list against its twin, so pinning a deploy recipe against the file it
  is supposed to enumerate is an established pattern here, not a new one.

  # THRESHOLD DECLARATIONS
  NEW MECHANISM — no. One test file in an existing suite, run by the existing `test:python` job.
  No new service, dependency, lifecycle hook or workflow step. Deliberately NOT taken: turning
  the recipe into a `scripts/apply_alert_policies.py`. That would be a new operational mechanism
  and is the CPO's call, not the builder's; the test closes the same hole without one.
  RECURRING COST — no. No new job, schedule, API call or storage. The test is offline.
  GUARD LOOSENED — no; this ADDS one. Nothing today checks the recipe against the policy file.
  SHIPPED NUMBERS — no. Nothing downstream of a number is touched.

decisions_reserved:
  - Whether the apply step should become a real script (testable end to end, idempotent by
    construction) instead of a documented shell recipe. That is a new operational mechanism and
    therefore CPO-class. Noted, not taken.
  - Whether `deploy/**` should route to `platform-reviewer` in `review_routing.json`. It does
    not today, so this diff reaches Platform only via `tests/**`. Changing routing is a
    protected-path governance event and is not attempted here.
  - Whether the notification-channel creation step (same section, same non-idempotent shape)
    should get the same treatment. Out of scope for #61 as filed.

done_when:
  - `pytest tests/ -q` exits 0.
  - `ruff --config .ruff-ci.toml tests/` exits 0.
  - ⚠ THE NEW TEST IS VERIFIED BY BREAKING ITS SUBJECT — restore `for i in 0 1` in the README
    and confirm the test goes RED, then restore the fix. A test that has never failed is
    decoration, and this repo has shipped ten of those.
  - The corrected recipe's ANTI-DUPLICATION half is verified against the LIVE API, read-only:
    run only its existence-check step and confirm it resolves all three declared policies to
    already-present, i.e. it would take the update path and POST none.
  - ⚠ THE POST PATH IS DELIBERATELY NOT EXECUTED. Running it would create duplicate live alert
    policies, which is the exact defect being fixed. The same request shape was executed
    successfully by hand on 2026-08-11 when the missing policy was created.
  - No `gcloud`/Monitoring WRITE is issued from this branch.

amendments: (none)
