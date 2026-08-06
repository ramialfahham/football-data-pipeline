# Task contract — a web dispatch must not auto-start the full prod build

> Branch `chore/gitlab-ci-manual-prod-build` from `main`. `.gitlab-ci.yml` is a protected
> path, so `protected_override` and `impact_map` are both declared. No `site_v2/src/` path
> is in scope, so no `acceptance_criteria`.

objective: >
  Make `data:build:main` MANUAL on a web-dispatched pipeline, leaving it automatic on a
  push to main. One line of `rules:`, plus the test that pins it.

  THE PROBLEM, found by evaluating the rules before triggering anything rather than after
  paying for it. `data:nightly` is reachable only from a web dispatch (by design — no
  schedule exists, per the CPO's decision to defer it). But on that same web pipeline
  `data:build:main` matches `if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH` and runs
  `when: on_success`, i.e. AUTOMATICALLY. Its `changes: *data_paths` filter does not hold
  it back: GitLab evaluates `changes:` as TRUE on any pipeline that is not a push or an
  MR — the same mechanic this file already guards against for schedules.

  So asking for a manual nightly silently also starts a FULL PROD WAREHOUSE BUILD. The CPO
  asked for the nightly to be run; carrying that out as the file stands would have spent a
  prod build they did not ask for, on a day that already had two.

refs: >
  Phase 3 (MR !5, merged `636f4ab`) added `data:nightly` and admitted `schedule` into
  `workflow:rules`, guarding every other job against schedules. It did NOT consider the
  same mechanic on `web`, because `data:build:main`'s `if: web` rule predates it — MR !4
  added it meaning "I deliberately want a full prod build now", which was reasonable when
  web dispatch had no other purpose. Phase 3 gave web a second purpose and conflated the
  two intentions. This is the correction.

scope_paths:
  - .gitlab-ci.yml
  - tests/test_governance_hooks.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

protected_override: >
  CPO instruction of 2026-08-06, recorded durably in `.claude/task/escalations.log` under
  "CPO INSTRUCTION: RUN THE NIGHTLY — and what it cost to carry out". Read it there; this
  is a pointer, not the record. `platform-reviewer` flagged an earlier version of this
  field for quoting CPO dialogue that appeared nowhere a reviewer could check — the same
  failure class `scope-auditor` failed the Phase 3 contract on, and worth heeding the
  moment it is named rather than after a second FAIL.

  THE AUTHORITY IS NARROW AND THIS CONTRACT DOES NOT CLAIM MORE. "ok do it" authorised
  RUNNING THE NIGHTLY; it did not authorise this edit. The justification is that the edit
  is a PRECONDITION to executing that instruction without unrequested spend — carrying it
  out as the file stood would have started a third full prod build that day, immediately
  after the CPO twice objected to that spend.

  Same file, same migration and same authority as MR !4 and !5, whose guard-status ruling
  is recorded in `.claude/task/escalations.log` under "GitHub -> GitLab migration: guard
  status for the CI config".

  CLASSIFICATION, stated rather than assumed: this is NOT a §10 decision. It removes no
  capability — `data:build:main` remains available on a web dispatch, as a button instead
  of an automatic start — and changes nothing about pushes to main. "An expensive job
  should not auto-start on a manual dispatch" is an implementation judgement aligned with
  a cost position the CPO has stated repeatedly.

impact_map: >
  - `.gitlab-ci.yml`, `data:build:main` rules. The `if: $CI_PIPELINE_SOURCE == "web"`
    clause gains `when: manual`, and the branch clause gains an explicit
    `$CI_PIPELINE_SOURCE == "push"` guard so a web dispatch cannot satisfy it.
    CONSUMERS: nobody in-repo; it takes effect when GitLab builds a pipeline.
    EFFECT BY SOURCE, which is the whole point:
      · push to main  -> UNCHANGED, still automatic on a data-path change.
      · web dispatch  -> becomes a BUTTON. Previously auto-started.
      · schedule      -> unchanged, still excluded by `*not_on_schedule`.
      · merge request -> unchanged, still never (that is `data:build:mr`).
    BLAST RADIUS IF WRONG: the failure direction is safe. A mistake here means prod is
    not rebuilt when someone expected it — visible, recoverable with one click, and
    costing nothing. The direction being prevented is the expensive one: spending a full
    prod build nobody asked for.
    NOT CHANGED: `resource_group: prod-warehouse-write`, so `data:build:main` and
    `data:nightly` still cannot MERGE the bare prod tables concurrently (#667) even when
    both are started from the same pipeline.

  - `tests/test_governance_hooks.py`: extends the CI-reachability pins to model a WEB
    pipeline as well as a scheduled one, asserting that no job costing warehouse spend
    auto-starts on a manual dispatch. The existing recogniser is reused, which already
    RAISES on an unrecognised condition rather than assuming it harmless — `push` is added
    to its classified set deliberately, not silently.

decisions_taken: >
  1. `when: manual` on the web clause, NOT removal of the clause. Deliberate full prod
     builds must stay possible — that is what MR !4 added it for. The defect is that it
     was automatic, not that it existed.

  2. The branch clause is additionally pinned to `$CI_PIPELINE_SOURCE == "push"`. Without
     that, a web pipeline on main still matches `$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH`
     FIRST (rules are first-match-wins) and runs on_success — the `when: manual` on a
     later clause would never be reached. Fixing only the web clause would have LOOKED
     right and changed nothing, which is the failure mode this task exists to correct.

  3. NOT applied to `deploy:export` / `deploy:site-v2`: they are already `manual` and
     `web`-scoped, and `deploy:site-v2` cannot start until the manual export is triggered.

  THRESHOLD DECLARATIONS. NEW MECHANISM: no — an existing job's trigger condition is
  narrowed. RECURRING COST: a REDUCTION, and no figure is asserted. Per the CPO
  instruction of 2026-08-06 recorded in `.claude/task/escalations.log`,
  `report_bq_cost.py` has not been run; the saving is argued from what the job does (one
  full prod build per unintended web dispatch) rather than from measured bytes.

decisions_reserved:
  - Whether merge-to-main should trigger a full prod build AT ALL is NOT decided here.
    That is GitLab issue #2, filed as an observation with evidence for the CPO's cost
    work, and this task deliberately leaves the push path untouched.
  - The nightly SCHEDULE is still not created, per the CPO's decision that scheduling
    makes no sense while nothing reads the data.

done_when:
  - `glab ci lint` reports the config valid.
  - On a WEB pipeline, no job that spends warehouse money auto-starts: `data:build:main`
    is `manual`, verified by parsing the merged YAML rather than by reading it.
  - On a PUSH to main with a data-path change, `data:build:main` still runs automatically
    — the fix must not silently disable prod builds.
  - `python -m pytest tests/test_governance_hooks.py` is green, and the new pin has been
    demonstrated to FAIL against the pre-fix rules, not merely to pass against the fixed
    ones.
