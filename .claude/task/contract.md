# Task contract — derive the guard-path counts and protected-path list, and test the prose against them

> Branch `test/1-guard-path-doc-parity` from `main` (`9987184`). NO protected path is in scope, so
> no `protected_override`. `tests/` is not on the structural surface
> (`task_contract_gate.py:94` — `ingestion/`, `dbt_project/models/`, `site/`, `site_v2/`), so no
> `impact_map`. No `site_v2/src/` path, so no `acceptance_criteria`.

objective: >
  Make it impossible for a hand-copied guard-path count or protected-path list to drift from the
  source without a test failing.

  THE PROBLEM. `.claude/review_routing.json` is the source of truth for which paths confer which
  reviewers, and `task_contract_gate.py` for which paths are protected. Neither the count nor the
  list is derived anywhere. Both are restated as English prose, by hand, across eleven sites. MR !4
  added exactly one routing row and that one-line change cost eleven prose edits and three review
  rounds. The failure mode is not carelessness: nothing can tell you a hand-copied list is
  incomplete, because a stale "eight" is valid prose.

  WHAT THIS TASK IS NOT. #1's body describes the prose as saying "eight guard paths" / "two of the
  eight". That was the pre-migration state. All eleven sites were corrected during !4 and are
  consistent with the source today (nine, three, six), verified site by site while planning. So
  this task edits NO prose and NO guard. It is purely additive: it adds the test that catches the
  next drift.

refs: >
  GitLab issue #1 ("Guard-path count and protected-path list are hand-copied into 11 prose sites").

  AUTHORITY: `.claude/task/escalations.log`, entry `2026-08-07 test/1-guard-path-doc-parity`, which
  records the CPO's up-front instruction verbatim and the ruling on the incomplete list the test
  found. Logged there rather than only quoted here, per the CPO ruling at `escalations.log:112`
  (2026-06-17): *"Path A — LOG IT ... the contract's decisions_taken is not, by itself, the sole
  record."* `scope-auditor` FAILed round 1 because that entry was missing; it was right.

  Plan approved in plan mode 2026-08-07 (`~/.claude/plans/splendid-tickling-bumblebee.md`).
  Follow-ups filed: GitLab #22 (the incomplete list), #23 (a stale claim in `.gitlab-ci.yml`).

scope_paths:
  - tests/test_governance_doc_parity.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

decisions_taken: >
  THRESHOLD DECLARATIONS, stated because no gate parses this field.

  NEW MECHANISM — YES. It introduces a class of enforcement the repo does not have: PROSE must
  agree with CODE. Declared as a mechanism rather than argued down to "just another test".
  AUTHORITY IS LOGGED, NOT ASSERTED HERE: `.claude/task/escalations.log`, entry `2026-08-07
  test/1-guard-path-doc-parity`, carries the CPO's instruction verbatim and the plan-mode approval
  that preceded any file being written. This contract cites a locatable ruling; it is not itself
  the record.

  RECURRING COST — NO NEW JOB. The tests run inside the existing `test:python` CI job and the
  existing local pytest suite. No new job, stage, runner, schedule, dependency or external service.
  The added cost is the runtime of four offline tests that read files already in the repo.

  NEW EXTERNAL SURFACE — NO. Nothing is published, deployed or exposed.

  GUARD INVARIANT — UNCHANGED, AND NONE IS LOOSENED. No hook, agent brief, routing row or
  protected-path list is edited. `task_contract_gate.py` and `.claude/review_routing.json` are READ
  by the new test and not modified; neither appears in `scope_paths`.

  COUNTS STAY IN PROSE. #1 offered replacing every count with a pointer to `review_routing.json`
  (its option 2). The approved plan keeps the counts and tests them instead, and the CPO approved
  that plan with the alternative stated in it explicitly.

decisions_reserved:
  - Whether this same derive-and-test pattern is extended to the rest of the hand-copied facts in
    the repo (#19, "compile, don't append"). Deliberately NOT started here. #19 is a compression
    pass over every governing artifact and is its own session; folding it in would make this diff
    unreviewable and would be scope drift.
  - Whether a future guard path that is protected but deliberately unrouted (or routed but
    deliberately unprotected) is legitimate. `test_the_guard_path_set_is_exactly_the_protected_path_set`
    asserts the two sets are identical, which is true today for all nine. If a real case ever needs
    them to differ, that is a §10 call about the governance model and not a licence to widen the
    test — the test should be narrowed to where it still holds, with the exception named.

done_when:
  - "Every one of the four tests has been made to FAIL against a deliberately broken source, with
    the red pytest output pasted, and every break reverted. A passing test proves nothing."
  - "`.venv/Scripts/python.exe -m pytest tests/ -q` is green, with no reduction in the pre-existing
    test count."
  - "`git diff --stat main...HEAD` shows exactly one non-artifact file,
    `tests/test_governance_doc_parity.py`."
  - "The five fast offline gates pass (the Stop hook runs them)."

amendments: (none)
