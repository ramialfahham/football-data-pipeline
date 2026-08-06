# Task contract — GitLab CI Phase 3: the nightly prod build and the site deploy

> Branch `chore/gitlab-ci-phase3` from `main`. `.gitlab-ci.yml` is a protected path and
> `ingestion/**` is the structural surface, so `protected_override` and `impact_map` are
> both declared. No `site_v2/src/` path is in scope, so no `acceptance_criteria`.

objective: >
  Finish the GitHub -> GitLab migration. MR !4 moved the six quality gates and proved the
  keyless WIF credential chain end to end (pipeline 2738001325 green, including the
  singular DQ suite). What remains is the work that keeps the PROJECT running rather than
  the CI: the nightly prod warehouse build, and the v2 site deploy.

  Two workflows are TRANSLATED (`dbt-scheduled.yml`, `deploy-site-v2.yml`) and three are
  DELIBERATELY NOT (`pages-match-preview.yml`, `board-request-sync.yml`,
  `ci-failure-watchdog.yml`). The non-ports are decisions, not omissions, and are argued
  in `decisions_taken` — porting a workflow whose product was retired would resurrect it.

refs: >
  CPO instruction, 2026-08-06: "Finish migration. AGAIN: I must be able to continue with
  the project." That sentence sets the bar this contract is written against — the nightly
  build is what makes the data keep flowing, so it is the centre of this task, and
  anything not required for the CPO to keep working is deferred rather than bundled.

  `.gitlab-ci.yml`'s guard status (routing + PROTECTED_FILES) was ruled on 2026-08-06 and
  is recorded in `.claude/task/escalations.log`. That ruling still governs; this task
  changes the file again under the same authority.

scope_paths:
  - .gitlab-ci.yml
  - ingestion/api_football/completeness.py
  - ingestion/api_football/orchestrator.py
  - tests/test_governance_hooks.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

protected_override: >
  CPO instruction of 2026-08-06 ("Finish migration"), which cannot be carried out without
  editing `.gitlab-ci.yml` — the file that holds every job being added. This is the same
  file, the same migration and the same authority as MR !4, whose guard-status ruling is
  recorded durably in `.claude/task/escalations.log` under "GitHub -> GitLab migration:
  guard status for the CI config".

  Stated plainly rather than inferred: the CPO has not separately ruled on WHICH workflows
  get ported. That judgement is the builder's and is argued in `decisions_taken`; the
  three non-ports are the part most worth challenging, and each cites the record it rests
  on rather than a preference.

impact_map: >
  END-TO-END TRACE of each change.

  - `.gitlab-ci.yml`, `schedule` added to `workflow:rules`. THIS IS THE DANGEROUS EDIT and
    it is why the previous contract deliberately withheld it. A scheduled pipeline runs
    with `CI_COMMIT_BRANCH == main`, so it satisfies every existing `if: $CI_COMMIT_BRANCH
    == $CI_DEFAULT_BRANCH` rule — `validate:ui`, `build:site-v2` and, critically,
    `data:build:main`. Worse, GitLab evaluates `changes:` as TRUE on any pipeline that is
    not a push or MR, so `data:build:main`'s `changes: *data_paths` filter does NOT hold
    it back on a schedule. Admitting schedules naively would therefore run a SECOND full
    prod warehouse build every night, doubling the most expensive job in the file.
    MITIGATION: a `.not_on_schedule` anchor (`if: $CI_PIPELINE_SOURCE == "schedule"`,
    `when: never`) is placed FIRST in the rules of every job except the nightly. Rules are
    first-match-wins, so the guard cannot be outvoted by a later matching clause. Pinned
    by a test (below) because the failure is silent and expensive: nothing goes red, the
    bill just doubles.

  - `.gitlab-ci.yml`, new job `data:nightly` (was `dbt-scheduled.yml`). Runs ONLY on
    `$CI_PIPELINE_SOURCE == "schedule"` plus manual `web`. Joins `resource_group:
    prod-warehouse-write`, shared with `data:build:main`, so the two prod writers can
    never MERGE the bare prod tables concurrently (#667) — the same guarantee the GitHub
    `concurrency: prod-warehouse-write` group gave across workflows.
    CONSUMER: the warehouse itself. This is the job that keeps `dbt_analytics` current,
    so its absence is what "I must be able to continue with the project" is about.

  - `ingestion/api_football/completeness.py::write_github_output` -> `write_ci_output`.
    CONSUMER: exactly one call site, `orchestrator.py:313`, which emits
    `new_data=true|false` after ingestion. The GitHub workflow gated `dbt deps`, `dbt
    seed`, both contract checks and `dbt build` on `steps.ingest.outputs.new_data ==
    'true'` — i.e. a NIGHT WITH NO NEW DATA COSTS NOTHING. GitLab has no step outputs, so
    the signal must survive as a file the next command reads.
    WHY NOT just set `GITHUB_OUTPUT` in the GitLab job: it works, and it is a lie in a
    filename — a GitLab runner writing a variable named for a platform this repo is
    leaving. The helper now reads `CI_STEP_OUTPUT` first and falls back to
    `GITHUB_OUTPUT`, so the frozen `.github/workflows/` copies keep working unchanged and
    neither platform's name is hardcoded into the other's path.
    BLAST RADIUS: the function is a no-op when neither variable is set, which is every
    local run and every test. Renaming it cannot change ingestion behaviour; the worst
    case is the nightly always seeing `new_data` unset and SKIPPING the build, which is
    the safe direction (no spend, visible as an idle nightly), not a silent overspend.

  - `.gitlab-ci.yml`, new job `deploy:site-v2` (was `deploy-site-v2.yml`). BOTH gates the
    original documents as deliberately closed are preserved: `when: manual` with no
    schedule and no push trigger (the original's only trigger was `workflow_dispatch`),
    and no custom-domain step (the deploy targets Firebase `.web.app`; going public is a
    separate CPO decision, still blocked on the imprint question). It does NOT join
    `prod-warehouse-write` — the export only SELECTs marts and writes no prod table,
    which is why the original kept it in its own concurrency group.

  - `tests/test_governance_hooks.py`: pins TWO invariants, both verified to fail against
    the broken form rather than merely to pass against the fixed one.
    (i) the schedule guard, per the bullet above.
    (ii) `id_tokens` on every job that expands `*gcp_auth`. GitLab populates
    `$GITLAB_OIDC_TOKEN` ONLY for a job declaring `id_tokens:` itself — not inherited
    from `default:`, not implied by the anchor. `data:nightly`, `deploy:export` and
    `deploy:site-v2` were all written without it and would have died at the auth guard
    on every run, the nightly never building prod once a schedule existed.
    `data-engineer-reviewer` caught it; `glab ci lint` passed it, the YAML parsed, and
    both other tests passed, because the config was well-formed and simply wrong — the
    same shape as MR !4's profile-location defect. The declaration is now a single
    `.gcp_job` anchor merged into every consumer, so there is one definition to audit
    instead of a copy per job.

decisions_taken: >
  1. PORTED: `dbt-scheduled.yml` -> `data:nightly`. This is the reason the task exists.

  2. PORTED: `deploy-site-v2.yml` -> `deploy:site-v2`, manual-only, both gates intact.

  3. NOT PORTED: `pages-match-preview.yml`. Its product is RETIRED. `docs/north_star.md:37`
     records the legacy card MVP as taken offline on 2026-07-21, "its Pages deployment
     deleted, `site/` frozen. There is no parity requirement, no cutover and no restore."
     Porting it would resurrect a deliberately retired product AND reinstate a daily
     07:30 UTC build — which `.claude/active_work.md` ranks as #547's open cost item 3
     ("rebuilds unconditionally, no `new_data` gate", explicitly NEVER MEASURED). Not
     porting is the only reading consistent with the retirement, and it happens to be the
     cheaper one. If the CPO wants the MVP back that is a product decision, not a
     migration step.

  4. NOT PORTED: `board-request-sync.yml`. It drives a GitHub Projects v2 board over
     GraphQL. That board died with the account, and the 114-issue tracker did not migrate
     — GitLab currently holds ONE issue. The CPO has chosen "rewrite against GitLab Issue
     Boards", but there is no board to sync yet, so building the sync now would be
     writing an integration against a thing that does not exist. Deferred, not dropped.
     `project-status-sync.yml` is already in `.github/workflows/_paused/` and inactive, so
     it is not a migration item at all.

  5. NOT PORTED: `ci-failure-watchdog.yml`. It opened a GitHub Issue when CI failed.
     GitLab emails the pipeline's author on failure natively, so porting it would rebuild
     a notification that already exists, and would need the issue tracker that does not.

  6. THE SCHEDULE GUARD IS A `when: never` ANCHOR PLACED FIRST, not a `!=` condition
     appended to each existing rule. Both work; the anchor is one definition to audit
     instead of five edited conditions, and first-match-wins means it cannot be defeated
     by a later clause. The alternative would have required getting five separate boolean
     expressions right, which is exactly the hand-copied-in-N-places pattern that cost
     MR !4 three review rounds.

  THRESHOLD DECLARATIONS. NEW MECHANISM: yes, two — a scheduled pipeline trigger (which
  needs a GitLab pipeline schedule created in the UI or API; see `decisions_reserved`) and
  a Firebase deploy job. Both are translations of mechanisms that already ran on GitHub,
  not new capabilities.

  RECURRING COST — the honest accounting, and it is a REDUCTION:
  (a) The nightly prod build is NOT new spend: it is the GitHub nightly moving hosts, and
      it has been absent since the account was suspended. Restoring it restores the prior
      baseline. It stays gated on `new_data`, so a night with no new data still costs
      nothing.
  (b) NOT porting `pages-match-preview.yml` REMOVES a daily 07:30 UTC unconditional
      rebuild from the platform's recurring cost. Its size was never measured, so no
      figure is claimed here.
  (c) `deploy:site-v2` is manual, so it adds no recurring cost.
  (d) NO COST FIGURE IS ASSERTED for any of this. The CPO instructed on 2026-08-06 that
      `report_bq_cost.py` not be run — recorded durably in `.claude/task/escalations.log`
      under "CPO INSTRUCTION: DO NOT RUN THE COST TOOLING", with the verbatim wording;
      read it there, this is a pointer and not the record. `scope-auditor` FAILED an
      earlier version of this contract for citing that instruction with no entry a
      reviewer could check — the same defect that failed MR !4's round 1, held to
      correctly a second time. Cost effects are therefore argued from what the workflows
      DO, never from bytes, and the ranked list in `.claude/active_work.md` is cited
      as-is where relevant.

decisions_reserved:
  - The GitLab PIPELINE SCHEDULE ITSELF IS NOT CREATED by this task. A schedule is
    project configuration, not repository content — it cannot be committed. Creating it
    starts a recurring prod warehouse build, which is a cost commitment and therefore the
    CPO's to make, with the cron (04:00 UTC, matching the GitHub original) and target
    branch stated when they do. Until it exists `data:nightly` simply never fires, which
    is the safe default.
  - Phase 4 (board sync) is deferred per `decisions_taken` #4, pending a GitLab board and
    a migrated tracker.
  - Whether to DELETE `.github/workflows/` remains undecided, unchanged from MR !4. It is
    still the reference this task translates FROM, and `review_routing.json` records that
    retiring it returns the guard counts to eight and TWO.
  - Going public with the v2 site (custom domain, announcement) is untouched and remains
    blocked on the imprint question.
  - The slim MR build path (`dbt build --select state:modified+ --defer --favor-state`)
    is STILL unexercised on GitLab: MR !4 changed no dbt models, so it reported "Nothing
    to do". The first MR touching a model remains its real test. Nothing here changes it.

done_when:
  - `glab ci lint` reports the config valid.
  - `data:nightly` exists, runs only on `schedule`/`web`, and joins
    `resource_group: prod-warehouse-write`.
  - The deploy chain requires a human click and cannot run on a schedule or a push.
    STATED PRECISELY, because an earlier wording named the wrong job: the `when: manual`
    gate sits on `deploy:export`, and `deploy:site-v2` carries `needs: ["deploy:export"]`
    — GitLab will not start a `needs:`-dependent job until its manual upstream is
    triggered, so one click still gates the whole export -> build -> deploy chain, which
    is what the original single-job `workflow_dispatch` guaranteed. `cto-reviewer` caught
    the imprecision and correctly judged the guarantee intact.
  - EVERY job except `data:nightly` carries the `.not_on_schedule` guard as its FIRST
    rule, verified by parsing the merged YAML rather than by reading it — a scheduled
    pipeline must not fire `data:build:main`.
  - The `new_data` signal survives the platform change: `write_ci_output` reads
    `CI_STEP_OUTPUT` then `GITHUB_OUTPUT`, and the nightly skips the build when it is
    false.
  - `python -m pytest tests/test_governance_hooks.py` is green, and the schedule-guard
    pin has been demonstrated to FAIL against an unguarded job, not merely to pass.
