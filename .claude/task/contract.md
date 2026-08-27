# Task contract — #92: make the MR singular-test gate read the BRANCH, not production

objective: >
  One flag, one line. `data:build:mr`'s second dbt invocation — the full singular-test suite, the DQ
  gate — runs with `--defer --favor-state`. `--favor-state` tells dbt to resolve every `ref()` to the
  DEFERRED (production) relation **even when the current run has just built that model**. The suite
  therefore tests PRODUCTION on every merge request. Removing `--favor-state` from that ONE
  invocation makes it test the branch. `--defer` stays, so an upstream this MR did not build still
  resolves to prod rather than to nothing.

  ⛔ THE `dbt build` INVOCATION KEEPS `--favor-state` AND MUST. There are two invocations in this
  job and only the second changes. On the BUILD line the flag is correct and load-bearing: the
  shared `ci_*` datasets carry tables left by earlier merge requests, and when a model is being
  BUILT its own upstreams must come from prod, never from another branch's leftovers. A node dbt is
  building in the current run is not deferred at all, so the flag costs that line nothing and buys
  isolation. On the TEST line there is nothing being built, so the same flag has the opposite
  effect: it discards the models this MR just built.

  ⭐ WHAT THIS IS WORTH, stated plainly rather than sold. Today all 30 singular tests are green on an
  MR because production is healthy, not because the branch is. That is a gate reporting on the wrong
  subject. After this change they report on the branch.

  ⚠ AND WHAT IT COSTS, which is the reason #92 was left open rather than fixed on sight. Without
  `--favor-state`, `--defer` resolves a ref to the `ci_*` copy WHEN ONE EXISTS and to prod only when
  it does not. `data:build:mr` builds `state:modified+`, so everything this MR changed and everything
  downstream of it is freshly built and correct; an UNMODIFIED upstream, however, may be read from a
  `ci_*` table an earlier merge request left behind. So the trade is: a gate that currently tests the
  wrong database, against a gate that tests the right one but may read a stale unmodified upstream.
  Both are holes. This one is narrower, and unlike the current one it fails LOUDLY when it is wrong.
  ⛔ It is a trade, not a clean win, and the CPO was told so in those terms before approving.

  ⚠ A FALSE CLAIM IN THE FILE IS CORRECTED IN THE SAME CHANGE. The comment above the test line
  currently reads "On an MR it validates this MR's rebuilt ci_* models layered over prod (via defer)
  — an ISOLATED view, not shared prod state." That is exactly backwards for the rebuilt models,
  which is the half that matters, and it is why the defect survived: the file asserts the behaviour
  the flag prevents. Corrected, with the mechanism named, so the next reader is not misled the same
  way.

refs: >
  **GitLab #92**, open before today: "`--defer --favor-state` makes ALL 28 singular tests read PROD
  on an MR." (28 was the count when it was filed; the suite is 30 today, re-counted from the failing
  job's own output — `Done. PASS=29 WARN=0 ERROR=1 SKIP=0 TOTAL=30`.)

  ⭐ THE CPO'S APPROVAL, this session, in chat. He was shown the choice in these terms: fix the CI
  check — "one flag on one line tells that second run to read live data instead of what the branch
  just built. Remove it and it reads the branch" — together with the cost, that "those checks would
  then read from a workspace shared between branches, so they could pick up leftovers from another
  branch's run", and the alternative of renaming in two passes instead. His answer, verbatim:
  **"do as recommended"**. That is the `protected_override` authority recorded below.

  ⭐ THE FIRST CONCRETE REPRODUCTION, and the reason this stopped being theoretical. Pipeline
  `2796272877`, job `16145201830`, on `!114` (the first column rename of naming-programme step 3):
    · line 836 — `OK created sql table model ci_marts.mart_team_season_insights`, carrying the
      renamed column `points_capture_pct`
    · line 854 — `PASS assert_mart_team_season_insights_metric_consistency [PASS in 0.75s]`,
      INSIDE the build, against that freshly built table
    · line 1021 — the SAME test, in the second invocation:
      `Database Error ... Unrecognized name: points_capture_pct; Did you mean points_capture?`
  The same assertion passed and then failed, ninety seconds apart, in one job, on one branch. The
  only difference is which database the second run was pointed at.

  ⛔ WHY THIS CANNOT BE WAITED OUT. The production table only gains the new column after the rename
  merges, and the rename cannot merge while the gate is red. `!114` can never go green on its own.
  That is the shape of EVERY column rename that a singular test names — and naming-programme step 4
  is 35 more renames.

scope_paths:
  - .gitlab-ci.yml
  - tests/test_ci_data_job_invariants.py
  - dbt_project/tests/assert_metric_meaning_complete.sql
  - dbt_project/tests/assert_metric_direction_lower_is_better_agree.sql
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

protected_override: >
  **REQUIRED, and granted.** `.gitlab-ci.yml` is a PROTECTED governance path: it decides what CI
  enforces, and it carries the same authority `.github/workflows/**` carried before the migration —
  hence `cto-reviewer` + `platform-reviewer`, both at the opus floor.

  Authority: the CPO, in chat this session, answering the recommendation quoted in `refs` above with
  **"do as recommended"**. He had been given the mechanism, the benefit, the cost (cross-branch
  leftovers in the shared `ci_*` datasets) and the no-CI-change alternative (a two-pass
  expand/contract rename) before answering. Written into `escalations.log` in this same commit, so
  the authority and the change travel together.

  ⛔ THIS IS A GUARD BEING NARROWED IN ONE DIRECTION AND WIDENED IN ANOTHER, and it must be read as
  such rather than as a pure fix. It does not delete an assertion, exclude a test, add a tag or skip
  a path — the same 30 tests run, with the same SQL, and the count in the job output must not drop.
  What changes is which database they read. Judge it on that.

impact_map: >
  This is a PROTECTED path, so the trace is of the GUARD, not of table lineage.

  what fires it: `data:build:mr`, on a merge-request pipeline whose diff touches `*data_paths_mr`.
    Not on schedules (`*not_on_schedule`), not on main. The sibling `data:build:main` (line 736)
    runs `dbt test --select test_type:singular --exclude tag:freshness_check --target prod` with NO
    `--defer` and NO `--favor-state`, so it is untouched by this change and remains the full-strength
    production gate. `data:nightly` likewise unaffected.

  what else imports from it: nothing imports a CI job, but TWO DBT GUARDS DOCUMENT AND DEPEND ON
    THIS FLAG'S SEMANTICS, and an earlier draft of this map said "nothing" and was wrong.
    `dbt_project/tests/assert_metric_meaning_complete.sql` and
    `assert_metric_direction_lower_is_better_agree.sql` each carry a CI note stating that on a PR
    `ref('metric_catalogue')` resolves to MAIN's seed "because `--favor-state` swaps it for the
    state relation", and each derives a WORKFLOW RULE from it — that a change to catalogue VALUES
    and a guard depending on those values cannot land in the same PR — closing with the standing
    instruction **"Do not try to solve this with a CI workflow change."**
    ⛔ This change makes all three of those things false, and overrides that instruction. `dbt seed
    --target ci` runs at `.gitlab-ci.yml:589` before both invocations, so the BRANCH's
    `metric_catalogue` relation always exists in the ci target; with `--favor-state` gone, plain
    `--defer` prefers it. Those two guards now read the BRANCH's seed, and the values-merge-first
    rule they impose is no longer needed. Both notes are corrected in this commit, and the standing
    instruction is re-aimed rather than left contradicting the merged change.
    ⭐ That is not a side effect to tolerate — it is the same defect class this task exists to fix
    ("the file asserted the behaviour the flag prevented"), and correcting it in `.gitlab-ci.yml`
    while leaving it standing in two dbt guards would be the "corrections must replace EVERYWHERE"
    failure. Found by cto-reviewer and platform-reviewer in round 1, independently.
    The other consumer of the same idea is `data:build:main` (`.gitlab-ci.yml:736`, re-measured —
    an earlier draft said 714), which runs the same suite `--target prod` with NO `--defer`, NO
    `--state` and NO `--favor-state`. It is untouched and remains the full-strength prod gate.

  what pins the change itself: `tests/test_ci_data_job_invariants.py` gains an assertion, and it is
    added here rather than argued away. That module exists for exactly this class — its own
    docstring opens "Pin three CI data-job invariants that can be broken while every pipeline stays
    GREEN" — and platform-reviewer's round-1 finding was that re-adding `--favor-state` to the test
    line would restore the whole defect with every offline gate, every test and the pipeline still
    green, leaving only a comment in its way. A comment is precisely what failed here the first
    time. The assertion pins BOTH HALVES of the asymmetry: the `dbt test` invocation must carry
    `--defer` and `--state` and must NOT carry `--favor-state`; the `dbt build` invocation must
    still carry it. Pinning only one half would let someone "restore symmetry" by stripping the flag
    from the build line instead, which breaks isolation in the other direction and would pass.

  what stops being enforced if this is wrong: nothing stops. The failure mode of the change is a
    singular test reading a stale `ci_*` upstream left by an earlier MR, which produces a WRONG
    ANSWER (a spurious red, or a green that should have been red on that one upstream's data). It
    cannot silence a test: the selection `--select test_type:singular --exclude tag:freshness_check`
    is untouched, so the suite size is unchanged. `tests/test_ci_data_job_invariants.py` continues
    to pin the ingest-lock invariant on this job, which this change does not go near.

  what happens on failure: the job exits non-zero exactly as now — the failing invocation above is
    proof that a red here blocks the MR. Fail-closed is preserved; nothing is made conditional,
    nothing gains an `|| true`, no `allow_failure` is introduced.

  blast_radius: every future merge-request pipeline that touches a data path. That is wide, and it
    is why this is a CPO-approved governance task rather than a line edit. The change is confined to
    ONE invocation in ONE job; `git diff` is one line of flags plus the comment above it.

  deploy_order: this must merge BEFORE `!114`, and `!114` must then be rebased onto it — a merge
    request runs the `.gitlab-ci.yml` of its SOURCE branch, so `!114` keeps failing until it carries
    this commit. Rebasing `!114` moves its review hash, so its `review.md` must be rebound; a
    `review.md`-only commit is artifact-exempt, so that rebinding is free.

decisions_taken: >
  The change and its authority are quoted in `refs` and `protected_override`. Nothing here is chosen
  by the builder: the mechanism was recommended, the cost was disclosed, and the CPO said "do as
  recommended".

  THRESHOLD DECLARATIONS.
  · NEW MECHANISM: **none.** No new job, stage, script, tag, selector, allow_failure or exclusion. A
    flag is removed from an existing invocation and a comment above it is corrected. The test added
    in round 2 is an assertion inside `tests/test_ci_data_job_invariants.py`, the module that
    already exists for this exact class and already parses this exact job's script list — no new
    file, no new runner, no new dependency, no new CI step. Adding a case to an existing guard is
    not a new mechanism; had it needed a new harness, that would be a different declaration.
  · RECURRING COST: **none, and this was reasoned rather than waved.** The same 30 tests run on the
    same schedule against the same row counts; only the dataset they read changes, and a `ci_*`
    table is the same size as its prod twin. No job is added, no cadence changes, nothing new is
    scheduled. If anything the queries get marginally cheaper, since `ci_*` holds the MR's slice.
  · GUARD WEAKENED: **no** in the sense that matters — no assertion is removed, no test excluded, no
    path skipped, and the suite count must stay at 30. But see the ⛔ in `protected_override`: this
    is a trade between two holes, not a clean win, and the reviewer should judge it as one.

decisions_reserved:
  - none: the fix, its cost and the alternative were put to the CPO together and he chose this one.
    Whether the REMAINING hole — a singular test able to read a stale unmodified upstream from the
    shared `ci_*` datasets — is worth closing too, and how (an ephemeral per-MR dataset is the
    obvious candidate and a recurring-cost decision), stays open on #92 and is NOT decided here.

done_when:
  - `.gitlab-ci.yml` differs from main by exactly one flag removal on the `dbt test` invocation plus
    the corrected comment above it; the `dbt build` invocation is byte-identical.
  - `python -m pytest -q` passes, including `tests/test_ci_data_job_invariants.py`.
  - The YAML parses and the job's script list is unchanged apart from that one line, shown by
    parsing `.gitlab-ci.yml` and printing `data:build:mr`'s script before and after.
  - The claim is verified by RUNNING it, not by reading it: after merge, `!114` is rebased onto this
    and its pipeline is watched going green on the exact test that failed at job `16145201830`
    line 1021.
  - `.claude/task/escalations.log` carries the CPO's approval verbatim and the reproduction.
  - The new invariant is watched going RED against BOTH mutations before it is trusted: re-adding
    `--favor-state` to the `dbt test` line, and removing it from the `dbt build` line.
  - Neither dbt guard still tells a reader that `ref('metric_catalogue')` resolves to main's seed,
    and neither still carries "Do not try to solve this with a CI workflow change".

amendments: >
  2026-08-27, round 2: `scope_paths` EXTENDED by three files —
  `tests/test_ci_data_job_invariants.py`,
  `dbt_project/tests/assert_metric_meaning_complete.sql` and
  `dbt_project/tests/assert_metric_direction_lower_is_better_agree.sql`.
  Authority: the standing rules the round-1 FAILs invoked, not a new CPO decision. cto-reviewer and
  platform-reviewer independently found that the two dbt guards carry CI notes this change makes
  false, including a standing instruction it overrides — "corrections replace, never accumulate"
  makes fixing them part of THIS change, not a follow-up. platform-reviewer separately found the
  change unpinned by anything but a comment — "verify the test fails" and "never rely on prose where
  a machine can hold the line" put the assertion in the module that already exists for this class.
  Both extensions make the task's own claims true; neither widens what the task decides. Written on
  a clean tree (the code was stashed by explicit path, the contract amended, then popped).

  2026-08-27, round 3: no scope change. `impact_map`'s "what fires it" paragraph still said
  `data:build:main` was at line **714** while the paragraph 23 lines below it already said **736,
  re-measured**. Both numbers for the same line, in one file — the exact "#71 invert the number
  sweep" failure this repo keeps repeating, committed in the very artifact that corrects the same
  number elsewhere. 736 is right; 714 is a comment line inside the job. Caught by cto-reviewer,
  which judged it not worth a round and recommended fixing it in passing; fixed anyway, because a
  correction that lands in one paragraph and not its neighbour is the accumulation this rule exists
  to stop. No code file changed in round 3.
