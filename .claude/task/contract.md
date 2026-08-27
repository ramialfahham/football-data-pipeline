# Task contract — #92: make the MR singular-test gate read the BRANCH, not production

objective: >
  TWO HALVES, and the second exists because CI proved the first insufficient. Both are in this MR.

  **HALF ONE — one flag.** `data:build:mr`'s second dbt invocation — the full singular-test suite,
  the DQ gate — ran with `--defer --favor-state`. `--favor-state` tells dbt to resolve every `ref()`
  to the DEFERRED (production) relation **even when the current run has just built that model**. The
  suite therefore tested PRODUCTION on every merge request. Removing `--favor-state` from that ONE
  invocation makes it test the branch. `--defer` stays, so an upstream this MR did not build still
  resolves to prod rather than to nothing.

  **HALF TWO — one dataset set per merge request.** Half one alone is not enough, and this is
  measured from a real pipeline, not argued. Every merge request built into the SAME five `ci_*`
  datasets. While the tests read production that was invisible; the moment they read the ci datasets
  instead, a merge request that rebuilt nothing began reading whatever another branch had left
  there. `!115` — this branch, which changes no models — went red on THREE tests against tables
  `!114` had built an hour earlier, headline error `Unrecognized name: points_capture; Did you mean
  points_capture_pct?`, the exact mirror of the failure that started #92.
  `macros/generate_schema_name.sql` already prefixes every non-prod dataset with `target.name`, so
  isolation was ALWAYS keyed on the target name — it simply was not unique per branch. The profile
  anchor now derives `DBT_CI_TARGET=ci_mr${CI_MERGE_REQUEST_IID}` and names its output that, so each
  merge request writes `ci_mr<IID>_marts` / `_core` / `_staging` / `_intermediate` and bare
  `ci_mr<IID>`, and `--defer` falls back to PROD for everything it did not build.
  ⭐ **`generate_schema_name.sql` IS NOT TOUCHED.** Putting the uniqueness in the target name is what
  let the macro stay put, so local `dev` behaviour and the prod path are unchanged.

  ⛔ NOTHING HERE DELETES ANYTHING. This change only CREATES datasets. No expiry, no TTL, no drop,
  no cleanup step, and no path by which a mis-scoped rule could reach production — that was
  considered as a way to bound the storage and DELIBERATELY REFUSED, on the CPO's explicit
  instruction that nothing in this work go near a mechanism that could delete the warehouse.

  ⭐ PRE-FLIGHT, checked before building rather than discovered in CI: the change requires dbt to
  CREATE datasets, which it never had to before. The CI service account is
  `github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com` and it holds
  `roles/bigquery.user` (read from the live project IAM policy with
  `gcloud projects get-iam-policy`), which grants `bigquery.datasets.create`. So the mechanism has
  the permission it needs.

  ⛔ THE `dbt build` INVOCATION KEEPS `--favor-state`, AND ITS REASON IS NARROWER THAN IT WAS.
  It used to be "another merge request's leftovers", and after half two that state cannot occur —
  no other branch can write into `ci_mr<IID>_*`. ⚠ An earlier draft of this contract kept the old
  wording in the present tense while the same change abolished it; platform-reviewer caught it, and
  it is the exact defect class this task exists to remove.
  THE SURVIVING REASON, and it is real: an EARLIER PIPELINE OF THE SAME merge request can leave a
  superseded table in that merge request's own datasets. Build a model, then push a commit that
  reverts it to match main — it drops out of `state:modified+`, so the next pipeline does not
  rebuild it, and `--defer` alone would prefer the stale table that is still sitting there.
  `--favor-state` forces prod for it. On the TEST line nothing is being built, so the identical flag
  has the opposite effect: it discards the models this merge request just built.

  ⭐ WHAT THIS IS WORTH, stated plainly rather than sold. Today all 30 singular tests are green on an
  MR because production is healthy, not because the branch is. That is a gate reporting on the wrong
  subject. After this change they report on the branch.

  ⚠ AND WHAT IT COSTS. ⛔ REWRITTEN — this paragraph described half one's cost as "an UNMODIFIED
  upstream may be read from a `ci_*` table AN EARLIER MERGE REQUEST left behind", which half two
  abolishes: no other branch can write into `ci_mr<IID>_*`. platform-reviewer caught that the sweep
  had stopped one paragraph short of this one, twice.
  WHAT THE COST ACTUALLY IS, after both halves. Without `--favor-state`, `--defer` resolves a ref to
  a relation in the current target WHEN ONE EXISTS, and to prod only when it does not. Everything
  this merge request changed, and everything downstream, is freshly built and correct. The residual
  is one case: an EARLIER PIPELINE OF THIS SAME merge request can leave a SUPERSEDED table — build a
  model, then push a commit reverting it to match main, and it drops out of `state:modified+` so the
  next pipeline does not rebuild it. The gate then reads a table this branch no longer produces.
  ⚠ TWO PATHS REACH THAT STATE, not one — cto-reviewer added the second. A build-then-revert inside
  one merge request, AND a REBASE onto a main that has since absorbed the change (this very MR's
  `deploy_order` does exactly that to `!114`): either way the model drops out of `state:modified+`
  while its table survives.
  ⚠ FREQUENCY, NOT ONLY SEVERITY — the discipline this task's own record now demands: both paths
  need a specific sequence inside one merge request, so this is occasional, where the hole it
  replaces fired on EVERY merge request. It is not benign, and it is ACCEPTED because the only way
  to remove it is to restore `--favor-state` on the test line, which is #92 itself.

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
  - docs/operations_guide.md
  - dbt_project/docs/layering.md
  - dbt_project/profiles.example.yml
  - tests/test_ci_data_job_invariants.py
  - tests/test_persist_docs_policy.py
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
    --target "$DBT_CI_TARGET"` runs before both invocations, so the BRANCH's
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

  what pins the change: `tests/test_ci_data_job_invariants.py` — the module whose docstring opens
    "Pin three CI data-job invariants that can be broken while every pipeline stays GREEN" — gains
    TWO assertions, because both halves are silently revertible. Half one: re-adding `--favor-state`
    to the test line restores the whole defect with every gate and the pipeline still green. Half
    two: putting a literal `--target ci` back, or dropping `CI_MERGE_REQUEST_IID` from the
    derivation, restores the shared workspace just as silently. Each is asserted from BOTH sides —
    the test line must NOT carry `--favor-state` while the build line MUST, and every dbt invocation
    must use `$DBT_CI_TARGET` while the profile's `dataset:` must be `${DBT_CI_TARGET}` too.
    ⛔ THE `dataset:` HALF IS NOT DECORATION, and an earlier draft of this pin omitted it.
    `generate_schema_name` returns bare `target.schema` for any model with no `+schema` — which is
    the whole `2_base` layer AND every seed, `metric_catalogue` included. Their isolation rests
    entirely on the profile's `dataset:` line, so pinning only the target name would leave the base
    tables and the seed sharing one dataset again, reinstating the exact `!115` failure on the very
    relation the two rewritten dbt guards depend on. platform-reviewer found that omission.

  blast_radius: every future merge-request pipeline that touches a data path. That is wide, and it
    is why this is a CPO-approved governance task rather than a line edit. ⚠ REWRITTEN — this said
    "confined to ONE invocation in ONE job; `git diff` is one line of flags plus the comment above
    it", which was true of half one and false of what ships. What ships touches FOUR lines of
    `data:build:mr`: the `.dbt_profile` anchor (deriving `DBT_CI_TARGET` and naming its output
    that), and the `dbt seed` / `dbt build` / `dbt test` invocations, all three now
    `--target "$DBT_CI_TARGET"`. Plus two dbt guard comment blocks, two docs and two assertions.
    Every merge-request pipeline now writes its OWN dataset set instead of the five shared `ci_*`
    ones — which are left exactly where they are and simply stop being written to.

  deploy_order: this must merge BEFORE `!114`, and `!114` must then be rebased onto it — a merge
    request runs the `.gitlab-ci.yml` of its SOURCE branch, so `!114` keeps failing until it carries
    this commit. Rebasing `!114` moves its review hash, so its `review.md` must be rebound; a
    `review.md`-only commit is artifact-exempt, so that rebinding is free.

decisions_taken: >
  The change and its authority are quoted in `refs` and `protected_override`. Nothing here is chosen
  by the builder: the mechanism was recommended, the cost was disclosed, and the CPO said "do as
  recommended".

  THRESHOLD DECLARATIONS.
  ⚠ REWRITTEN AFTER HALF TWO. These declarations described half one and were carried forward
  unchanged when half two landed, so they said "none" to both questions while the diff created a
  per-merge-request dataset set. cto-reviewer and scope-auditor both failed on it. Corrected:

  · NEW MECHANISM: **none, and this was tested against the definition rather than asserted.** No new
    job, stage, script, file, runner, dependency, CI step, tag, selector, `allow_failure` or
    exclusion. Half one removes a flag. Half two exports ONE shell variable and lets the EXISTING
    `macros/generate_schema_name.sql` do the isolating — the macro is deliberately untouched, which
    is the whole reason this counts as configuration rather than machinery. The two assertions live
    inside a module that already exists for this class and already parses this job's script list.
  · RECURRING COST: **yes, small, and MEASURED rather than estimated.** Each merge request now
    leaves its own BigQuery tables instead of overwriting a shared set, and nothing deletes them.
    Measured on the live project with `bq query ... __TABLES__`: the five shared `ci_*` datasets
    hold **6.0 GB** in total today (`ci_staging` 2.4 GB, `ci_marts` 1.4 GB, `ci_intermediate`
    1.1 GB, `ci_core` 0.7 GB, `ci_analytics` 0.5 GB) — and that is the FULL set accumulated across
    many branches, where a single merge request builds only `state:modified+` and leaves a fraction
    of it. At EU BigQuery active-storage rates (~$0.02/GB/month) a whole 6 GB set is about **12
    cents a month**. No job is added, no cadence changes, nothing is scheduled.
    ⚠ QUERY VOLUME IS **NOT** UNCHANGED, and an earlier draft of this line said it was — twice,
    after cto-reviewer had already flagged it once. Three models are incremental
    (`fct_fixture_team_stats`, `fct_fixture_player_stats`, `fct_fixture_event`), and
    `is_incremental()` keys on `{{ this }}` — the model's own relation in the CURRENT target, which
    is never deferred. Under the shared datasets that relation persisted between merge requests, so
    a selected fact ran as a MERGE above a high-water mark. With a fresh `ci_mr<IID>_core` it does
    not exist on that merge request's FIRST pipeline, so the model does a FULL build instead.
    That fires for any merge request whose `state:modified+` reaches one of those three or anything
    upstream of them. Magnitude, measured rather than feared: the whole `ci_core` dataset is 0.7 GB,
    so it is sub-cent per pipeline plus some `data:build:mr` wall time against a 2h timeout.
    ⛔ Disclosed because this branch's own record says to describe the cost of the mechanism you are
    BUILDING, not the one you imagined. It is small; it is not zero, and it is not "unchanged".
    ⛔ AN AUTOMATIC EXPIRY WOULD BOUND IT AND IS DELIBERATELY NOT DONE. A mis-scoped expiry reaches
    `prod` and deletes the warehouse; the CPO's instruction on this work is explicit that nothing go
    near that class of mechanism. Storage is left to accumulate and filed instead. ⚠ I first
    described this cost to him as "storage for a few days, which self-deletes" — that was FALSE of
    what ships and cto-reviewer caught it. The number above is what he is actually approving.
  · GUARD WEAKENED: **no** in the sense that matters — no assertion is removed, no test excluded, no
    path skipped, and the suite count must stay at 30. But see the ⛔ in `protected_override`: this
    is a trade between two holes, not a clean win, and the reviewer should judge it as one.

decisions_reserved:
  - none. ⚠ THIS FIELD PREVIOUSLY RESERVED THE PER-MR DATASET as "the obvious candidate and a
    recurring-cost decision … NOT decided here", and then the same MR built it. Both reviewers were
    right to fail that: a contract cannot reserve as open the exact thing it ships. It is now
    DECIDED, on the CPO's "fix it" recorded in `escalations.log`, and declared under
    `decisions_taken` with its measured cost. Nothing about this change is left open.
  - The only genuinely open follow-on is BOUNDING the storage those datasets accumulate. It is not
    reserved here because it is refused here: the CPO's instruction is that nothing in this work go
    near a mechanism that could delete the warehouse, and an expiry is exactly that class. Filed, not
    reserved.

done_when:
  - `.gitlab-ci.yml`'s `dbt test` invocation carries `--defer --state` and NOT `--favor-state`,
    while the `dbt build` invocation still carries `--favor-state` — the asymmetry is the fix.
  - Every dbt invocation in `data:build:mr` targets `"$DBT_CI_TARGET"`, that variable is derived
    from `CI_MERGE_REQUEST_IID`, and the profile's `dataset:` is `${DBT_CI_TARGET}` — so the layer
    datasets AND the base models and seeds are all per merge request.
  - `macros/generate_schema_name.sql` does NOT appear in the diff.
  - Nothing in the diff deletes, expires or drops a dataset or a table. `git diff` contains no
    `expiration`, no `bq rm`, no `drop dataset`, no cleanup step.
  - `python -m pytest -q` passes, including `tests/test_ci_data_job_invariants.py`.
  - The YAML parses and `data:build:mr`'s script list is still 13 steps.
  - Both new invariants are watched going RED against every mutation before being trusted:
    `--favor-state` re-added to the test line; `--favor-state` removed from the build line; a
    literal `--target ci` restored; `CI_MERGE_REQUEST_IID` dropped from the derivation; and the
    profile's `dataset:` reverted to a shared literal.
  - Neither dbt guard still tells a reader that `ref('metric_catalogue')` resolves to main's seed,
    neither still carries "Do not try to solve this with a CI workflow change", and neither names a
    `ci` target that no longer exists.
  - No comment left in `.gitlab-ci.yml` still describes the shared workspace as current.
  - The claim is verified by RUNNING it, not by reading it: this branch's own pipeline goes green —
    the same pipeline that went red on three tests against another branch's tables — and then `!114`
    is rebased onto this and watched going green on the exact test that failed at job
    `16145201830` line 1021.
  - `.claude/task/escalations.log` carries both CPO rulings verbatim and both reproductions.

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

  2026-08-27, round 4 — ⛔ CI PROVED HALF ONE INSUFFICIENT ON THE FIRST PIPELINE, and the fix grew
  a second half. Authority: the CPO, shown the failure and the recommendation "give each merge
  request its own workspace instead of sharing one", answered **"fix it"**; and, after I raised an
  automatic expiry as a way to bound the resulting storage, instructed that nothing in this work go
  near anything that could delete the warehouse. Both are recorded in `escalations.log`.
  `scope_paths` EXTENDED by `dbt_project/docs/layering.md` and `dbt_project/profiles.example.yml`,
  which document the `ci` target's dataset names that this round changes — leaving them saying
  `ci_marts` would be the same stale-comment defect this whole task exists to fix.
  ⚠ WHAT ROUND 4 CORRECTS IN THIS CONTRACT, all found by reviewers rather than by me:
  `decisions_taken`'s threshold declarations still said NEW MECHANISM none / RECURRING COST none,
  written for half one and carried forward unchanged over a diff that creates a dataset set per
  merge request (cto-reviewer, scope-auditor); `decisions_reserved` reserved as undecided the exact
  mechanism the same commit builds (cto-reviewer); `blast_radius` and `done_when` still described
  the one-line version (platform-reviewer); and `impact_map` cited `dbt seed --target ci`, a command
  this round removes (platform-reviewer, analytics-engineer-reviewer). All corrected in place.
  ⚠ AND ONE FACT I GOT WRONG TO THE CPO'S FACE: I described the storage cost to him as "a few days
  per branch, which self-deletes". Nothing in this change makes that true — the datasets persist.
  cto-reviewer caught it. The real figure is measured and declared under RECURRING COST above, and
  it is ~12 cents a month for a full set. The approval now rests on the true number.

  2026-08-27, LAST ROUND: `scope_paths` extended by `tests/test_persist_docs_policy.py` — a SIXTH
  copy of the shared-workspace claim, in the docstring of the test that pins where `dbt docs
  generate` runs, hand-mirroring a `.gitlab-ci.yml` comment this same MR corrected. Same doc-sync
  authority as the two before it. Found by platform-reviewer, in its own territory, one file over.
  ⚠ AND THE COST LINE WAS WRONG A SECOND TIME. `RECURRING COST` closed with "query volume is
  unchanged"; it is not. A fresh per-merge-request dataset means the three incremental fact models
  have no `{{ this }}` on an MR's first pipeline and FULL-build instead of merging. cto-reviewer
  raised this in an earlier round and I did not fold it in; platform-reviewer had to raise it again.
  Now measured and declared. ⭐ Twice now the cost sentence has described something other than what
  is being built — the exact rule this task's record already carries.

  2026-08-27, FINAL ROUND: `scope_paths` extended by `docs/operations_guide.md`, which carries a
  DUPLICATE of the environment-isolation table already corrected in `dbt_project/docs/layering.md`
  and still described a shared `ci` target writing `ci_*`. Authority: the same doc-sync rule that
  brought `layering.md` in — consistency is both rows or neither. Found by platform-reviewer.
  ⚠ THE REST OF THIS ROUND IS ME FIXING THE SAME DEFECT CLASS FIVE MORE TIMES, and the count is the
  point. Half two abolished the shared workspace; five separate comments still called it current —
  in `.gitlab-ci.yml` (three), in the new pin's docstring and assertion message, and in this
  contract's own objective. I swept where I was looking and not where I was not, which IS the
  "corrections replace, never accumulate" failure, committed inside the fix for it.
  ⚠ AND ONE DEFECT I INTRODUCED WHILE FIXING THEM: a string replace spliced a sentence mid-line and
  left "HERE" dangling with no antecedent inside the paragraph about the BUILD line, so the comment
  read the asymmetry backwards. platform-reviewer caught it. Fixed.
  ⭐ ONE THING A REVIEWER WORKED OUT THAT I HAD NOT, and it is now load-bearing documentation: with
  per-merge-request datasets, "another branch's leftovers" is impossible, so `--favor-state` on the
  BUILD line looked like it guarded nothing — and the next reader would rightly have deleted it,
  which is the exact mutation the pin exists to stop. The surviving case is an earlier pipeline of
  the SAME merge request holding a superseded table after a revert. That reason is now stated in
  `.gitlab-ci.yml`, both places in the pin, and this contract.

  2026-08-27, round 3: no scope change. `impact_map`'s "what fires it" paragraph still said
  `data:build:main` was at line **714** while the paragraph 23 lines below it already said **736,
  re-measured**. Both numbers for the same line, in one file — the exact "#71 invert the number
  sweep" failure this repo keeps repeating, committed in the very artifact that corrects the same
  number elsewhere. 736 is right; 714 is a comment line inside the job. Caught by cto-reviewer,
  which judged it not worth a round and recommended fixing it in passing; fixed anyway, because a
  correction that lands in one paragraph and not its neighbour is the accumulation this rule exists
  to stop. No code file changed in round 3.
