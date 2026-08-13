# Task contract — #65: clear the stale worktree registration that fails every MR

objective: >
  `data:build:mr` fails on EVERY merge request at `.gitlab-ci.yml:555`:
  `git worktree add --detach /tmp/main-src FETCH_HEAD` exits 128 with "'/tmp/main-src' is a missing
  but already registered worktree". Both open MRs (`!33`, `!27`) are blocked behind it, so nothing
  merges until it clears.

  Cause, read out of two job logs rather than inferred from the error text: the self-hosted runner
  keeps the PROJECT directory between jobs — so `.git/worktrees/` persists — while each job gets a
  FRESH `/tmp`. The registration therefore outlives the directory it points at. Job 15864168006
  (08-12) ran the same command and SUCCEEDED, creating the registration; the 08-13 job on pipeline
  2756651714 hit exit 128 with the registration present and the directory gone.

  This is a consequence of the runner migration. On the previous shared runners every job got a
  clean clone, so the registration never survived a job. The first run after the migration passed
  and every run since has failed.

refs: >
  GitLab #65 (the failure, the two job logs, the fix). Reproduced against real git in
  `scratchpad/wt_repro.py` before any file was edited.
  ⚠ BLOCKS `!33` and `!27`; neither can go green until this merges.
  Context only, NOT in scope: GitLab #66 (prod data stale since 08-09, so this job will still fail
  further down) and the coming GitLab group move.

protected_override: >
  CPO, in session 2026-08-13, recorded in `.claude/task/escalations.log` BEFORE this contract was
  written: asked to take #65 next, answered **"yes"**, then interrogated the premise — **"Does it
  conflict with the other worktree?"** — and approved the plan once that was answered by
  measurement rather than argument.
  `.gitlab-ci.yml` is a PROTECTED FILE (`task_contract_gate.py:77` — "the file that decides what CI
  enforces"), so it may not be edited inside an ordinary contract.
  ⚠ THE AUTHORITY IS NARROW, and the log says so: it covers ONE line added to `data:build:mr` and
  the test that pins it. It does NOT extend to any other job, the `rules:`/`changes:` path anchors,
  the resource groups, the runner configuration, or the group move. None of those is touched. It
  also does not licence editing `.github/workflows/ci-data-build.yml:191`, which carries the same
  line and is deliberately kept unedited.

scope_paths:
  - .gitlab-ci.yml
  - tests/test_ci_data_job_invariants.py
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/review_input.patch

impact_map: >
  ⚠ REQUIRED HERE BECAUSE THE PATH IS PROTECTED, not because a model moved
  (`task_contract_gate.py:195` — a guard's blast radius is every future task in the repo).
  `protected_override` answers "may you"; this answers "do you know what breaks".

  who RUNS the changed line: exactly one job, `data:build:mr`, and only on a merge request whose
    diff matches `.data_paths_mr`. `git worktree` appears nowhere else in `.gitlab-ci.yml` —
    verified from PARSED YAML across all 11 jobs' `before_script`/`script`/`after_script`, not by
    grep. `data:build:main` and `data:nightly` do not use a worktree, which is why #66's remedy
    (a prod build on main) does not depend on this fix.

  who is AFFECTED BY the prune: nothing but stale registrations, and this was measured, not
    assumed. `git worktree prune` removes only registrations whose directory is GONE.
    - On the CPO's machine three worktrees are registered (`football-data-pipeline`,
      `fdp-pipeline`, `fdp-product`); `git worktree prune --dry-run -v` removes NONE of them. The
      change also runs on the runner, in a different clone, so it cannot reach that machine.
    - Concurrently in CI: `data:build:mr` carries `resource_group: ci-data-build-write-ci`, so two
      never run at once, and it is the only job holding a worktree.
    - Within the job: prune runs immediately before the add, when `/tmp/main-src` does not exist.

  what does NOT change: no dbt model, macro, seed, snapshot or test; no mart, no shipped number, no
    page, no export. `.data_paths_mr` and `.data_paths_prod` are untouched, so WHICH changes
    trigger a build is exactly as before. No BigQuery object is created, dropped or rebuilt.

  ⚠ RECURRING COST: none. The added command is a local git metadata operation on the runner. It
    does not add a job, a trigger, a schedule or a BigQuery scan.

  deploy_order: none. It takes effect on the next pipeline; there is no image, schedule or
    warehouse object to sequence.

  layer_rules: none engaged. `check_layer_contract.py` judges `dbt_project/models/**`, untouched.

decisions_taken: >
  1. `git worktree prune` BEFORE the add, as its own script line. Prune is the purpose-built
     command for this exact state — it drops registrations whose directory is gone and is a no-op
     otherwise. Its own line rather than `prune && add` so each step shows separately in the job
     trace, which is how this defect was diagnosed in the first place.

  2. ⚠ NOT `git worktree add -f`. `-f` clears the same error, so it is the tempting one-character
     fix, and it is wrong: it ALSO overrides a worktree whose directory genuinely exists, turning a
     real collision into a silent overwrite. Prune fixes the state that actually occurs and leaves
     the state that must not occur still failing loudly.

  3. THE MECHANISM WAS RUN, NOT REASONED FROM THE MANUAL. `scratchpad/wt_repro.py` models the two
     jobs against real git and prints:
       worktree add (UNFIXED)       exit=128  ... 'prune' or 'remove' to clear   <- reproduces CI
       worktree prune               exit=0
       worktree add (FIXED)         exit=0    Preparing worktree (detached HEAD ...)
       prune again (nothing stale)  exit=0    <- idempotent, safe on a clean runner
     This matters beyond politeness: it is what rules out "prune is a no-op here and the real cause
     is something else".

  4. THE TEST PINS THE CLASS, NOT THE INSTANCE. It scans every job's script and requires that ANY
     job running `git worktree add` runs `git worktree prune` earlier in the SAME script. A second
     worktree call added later is therefore covered without editing the test. Written this way
     because a one-line-number assertion is the repeated failure mode here (a word list holing four
     review rounds).

  5. VALUES COME FROM PARSED YAML, NEVER RAW FILE TEXT — the module's own stated rule, and it binds
     concretely: the fix carries a comment naming `worktree` and `prune`, so a text grep would read
     the documentation of the fix as the defect. The existing module says exactly this about
     `API_FOOTBALL_SKIP_INGEST_LOCK`.

  6. ⚠ `.claude/active_work.md` IS DELIBERATELY OUT OF SCOPE, stated rather than silently omitted.
     `main`'s copy is stale (last written 08-07); the CURRENT handover lives on `!33`, already
     documents #65, and will land when `!33` merges. Editing the stale copy here would add nothing
     a reader gets, and would manufacture a merge conflict for `!33` in the one file that is hardest
     to resolve mechanically. If the CPO would rather it be updated here, that reverses cleanly.

  7. THE DORMANT GITHUB WORKFLOW IS LEFT ALONE. `.github/workflows/ci-data-build.yml:191` carries
     the identical line, but `.github/workflows/` is both a PROTECTED prefix and deliberately kept
     as an unedited snapshot (`CLAUDE.md`, `.github/workflows/README.md`). Fixing it would be scope
     drift into a tree that runs nothing.

done_when:
  - `data:build:mr` runs `git worktree prune` before `git worktree add`, and no other job or path
    anchor in `.gitlab-ci.yml` is touched.
  - NEW TEST pins it for ANY job, from parsed YAML. ⚠ It must be SEEN RED against the unfixed file
    before it is trusted green — a test only ever observed passing proves nothing (#63 shipped
    three such tests and each passed against the very defect it was written to catch).
  - `python -m pytest tests/test_ci_data_job_invariants.py -q` green, then the full suite green.
  - The offline gates pass (`validate-local`).
  - END TO END, and the only proof that counts: this branch's own pipeline gets PAST the worktree
    step. ⚠ The job is still expected to FAIL further down on #66 (stale prod data, 10 rows from
    `assert_event_team_in_fixture_participants`). That is a different defect and is NOT evidence
    this fix failed — read the log, not the colour.

amendments: []
