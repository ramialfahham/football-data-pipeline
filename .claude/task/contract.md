# Task contract — GitLab CI translation + guard parity for the CI config

> Branch `chore/gitlab-ci-pipelines` from `main`. Protected paths ARE in scope
> (`.claude/review_routing.json`, `.claude/agents/**`, `.claude/hooks/**`,
> `.gitlab-ci.yml`), so `protected_override` and `impact_map` are both declared
> below. No `site_v2/src/` path is in scope, so no `acceptance_criteria`.

objective: >
  The GitHub account is suspended, so CI has no host. Translate the six quality-gate
  workflows (`python-ci`, `ci-validate`, `security-secrets`, `ci-ui`, `ci-site-v2`,
  `ci-data-build`) into a single `.gitlab-ci.yml` so the commit -> pipeline -> MR loop
  works on GitLab.

  Second, closely-coupled objective: the CI config is a GUARD. `.github/workflows/**`
  is both a protected path (contract gate) and a two-reviewer opus guard path (review
  routing). Its replacement `.gitlab-ci.yml` matched NEITHER, so migrating the CI gate
  to a new host would have silently dropped `cto-reviewer` + `platform-reviewer` and
  the `protected_override` requirement from the one file that decides what CI enforces.
  That downgrade is repaired here, in the same commit that creates the file — not left
  as follow-up, because the window between them is exactly when an unreviewed CI edit
  lands.

refs: >
  Migration MRs already open: !2 (`.githooks/post-commit` -> glab), !3 (agent
  governance docs -> glab/MR). This is the third. All three were committed while the
  repo's local hooks were inert (the session's `CLAUDE_PROJECT_DIR` pointed at a
  different project), which is why review artifacts are being written after the fact
  rather than at commit time. `check_task_artifacts.py` caught it — the CI backstop
  did its job.

  Phase 3 (dbt-scheduled, deploy-site-v2, pages-match-preview) is deliberately NOT
  here: those need GCP Workload Identity Federation repointed at GitLab's OIDC issuer,
  which is a GCP IAM change requiring the CPO's sign-off.

scope_paths:
  - .gitlab-ci.yml
  - .claude/review_routing.json
  - .claude/hooks/task_contract_gate.py
  - .claude/agents/cto-reviewer.md
  - .claude/agents/platform-reviewer.md
  - docs/working_agreement.md
  - docs/agent_guardrails.md
  - tests/test_governance_hooks.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  # THE FOUR PATHS BELOW WERE ADDED MID-TASK. Authority: CPO ruling of 2026-08-06,
  # recorded in `.claude/task/escalations.log` under "scope amendment authority for
  # the four restatement files" — read it there; this is a pointer, not the record.
  #
  # `scope-auditor` ESCALATED precisely because the earlier version of these lines
  # cited a reviewer's FAIL as the authority. A reviewer FAIL is not amendment
  # authority; `working_agreement.md:79` says an amendment records the CPO's. Same
  # shape as the 2026-06-23 precedent (`escalations.log:145`), where the same
  # reviewer held the same line and the CPO granted it explicitly.
  #
  # HONEST FRAMING, and the CPO named it when ruling: these are not four independent
  # extensions that each happened to be justified. They are ONE sweep that was
  # UNDER-SCOPED WHEN THIS CONTRACT WAS FIRST WRITTEN. All eleven restatement sites
  # (seven on axis 1, four on axis 2) were knowable from the routing table before the
  # first edit; listing four of them only after a reviewer pointed at each in turn is
  # the defect. The amendment is granted; the under-scoping is not excused by it.
  - .claude/task/escalations.log      # the durable record of the ruling itself
  - .claude/task/TEMPLATE.md          # carries a 4th copy of the protected-path list
  - docs/roles/platform_reliability.md   # platform-reviewer.md's third Input
  - docs/north_star.md                   # CTO row count + Platform's "Wakes on"

protected_override: >
  CPO ruling of 2026-08-06, recorded durably in `.claude/task/escalations.log` under
  "GitHub -> GitLab migration: guard status for the CI config" — read it there; this
  is a pointer, not the record. The question was put with both options named (match
  `.github/workflows/**`'s reviewers, or leave `.gitlab-ci.yml` on scope-auditor only
  and accept lighter review on CI config). CPO ANSWER: "Yes, match the old coverage."

  ROUND 1 FAILED HERE and the correction is the point: that version cited the approval
  as "approved in-thread" with no entry in escalations.log. `cto-reviewer` grepped the
  log, found zero occurrences of "gitlab" and nothing dated after 2026-08-03, and
  failed it — the "does the claimed ruling actually exist" check firing exactly as
  `review_routing.json` says it has before. A `contract.md` does not survive the next
  task, so an authority recorded only there disappears with it.

  The protected-path half (contract gate) is the same ruling applied to the same file
  for the same reason. The CPO ruled on review routing explicitly and on the contract
  gate by implication; that inference is stated plainly here and in the summary rather
  than left for a reader to discover.

impact_map: >
  END-TO-END TRACE of each guard edit.

  - `.claude/review_routing.json`: adds one row, `.gitlab-ci.yml` -> [cto-reviewer,
    platform-reviewer]. CONSUMERS: `git_discipline._required_reviewers` (local commit
    gate) and `check_task_artifacts.py` (CI backstop) both read `paths` and both now
    demand two specialist verdicts for any MR touching `.gitlab-ci.yml`. Additive:
    no existing row is narrowed or removed, so no surface loses a reviewer. Verified
    by `test_real_routing_still_covers_every_pre_existing_surface`, which is
    parametrised over every pre-existing pin and still passes.

  - `.claude/hooks/task_contract_gate.py`: appends `.gitlab-ci.yml` to
    `PROTECTED_FILES`. CONSUMER: `_is_protected`, reached from the Edit/Write gate and
    the shell-redirect gate. EFFECT: editing `.gitlab-ci.yml` now denies unless the
    contract carries `protected_override` AND a non-placeholder `impact_map` — this
    contract is the first to satisfy it. A FILE entry, not a prefix: `.gitlab-ci.yml`
    is the whole surface and a prefix would match nothing. RISK CONSIDERED: this makes
    routine CI edits costlier. Accepted — it is precisely the cost `.github/workflows/`
    already carried, and the migration should not be a discount on it.

  - PROSE RESTATEMENTS, and this is the part the review cycle kept failing. The
    change invalidates sentences on TWO independent axes, and each axis has its own
    scattered set of copies:

    AXIS 1 — guard-path COUNTS (eight -> nine, platform's share two -> three), in
    SEVEN files: `.claude/agents/cto-reviewer.md` (two sites), 
    `.claude/agents/platform-reviewer.md`, `.claude/review_routing.json` `_doc`,
    `docs/working_agreement.md`, `docs/agent_guardrails.md`,
    `docs/roles/platform_reliability.md`, `docs/north_star.md` (CTO row count AND
    Platform's "Wakes on" list).

    AXIS 2 — PROTECTED-path enumerations, in FOUR files:
    `.claude/agents/cto-reviewer.md` (hunt item 7), `docs/working_agreement.md`,
    `docs/agent_guardrails.md`, `.claude/task/TEMPLATE.md`.

    Round 1 swept axis 1 in five files and declared it complete. `cto-reviewer`
    failed it twice: round 1 for missing axis 2 entirely (the two lists were
    identical eight-item sets, which is exactly why one grep looked exhaustive), and
    round 2 for missing two more axis-1 files, because that round's grep was scoped
    to files already open rather than the repo. The lesson is mechanical, not
    attitudinal: a count restated in prose must be re-derived from the rows and
    swept REPO-WIDE, not from the set of files already in hand. `docs/north_star.md`
    line 118 attaches an explicit duty to keeping its "Wakes on" column honest, and
    `docs/roles/platform_reliability.md` is `platform-reviewer.md`'s third Input, so
    a stale count there is fed to the reviewer on every future run.

    The 12-row CTO count was RE-DERIVED by counting the routing table
    programmatically, not copied from the reviewer that reported it —
    `escalations.log` records a prior incident where taking a reviewer's arithmetic
    on trust put an off-by-one into two documents.

    Deliberately LEFT unchanged, each checked: `working_agreement.md` line 157 and
    `escalations.log` line 327 narrate PAST review rounds and their counts were
    correct then; `platform-reviewer.md`'s "other six" is still six (nine minus
    three); `review_routing.json`'s "matches exactly two" is about the dependency
    threshold, a different subject.

  - `tests/test_governance_hooks.py`: adds two pins for the new routing row (one per
    conferred reviewer, matching how the `.github/workflows/**` row is pinned) and
    `.gitlab-ci.yml` to the protected-path parametrisation. NOT cosmetic —
    `test_every_routing_pattern_is_pinned_by_the_test_above` FAILED on the first run
    of this task with `unpinned routing patterns: ['.gitlab-ci.yml']`, which is the
    guard-the-guard test doing its job.

  - `.gitlab-ci.yml` itself: new file, no consumer inside the repo. It becomes live
    only when GitLab runs a pipeline. Until the WIF provider exists the `data:*`
    jobs are created, run, and FAIL — `.gcp_auth` exits 1 before `dbt deps`,
    `sqlfluff lint`, `dbt build` or the singular DQ suite can run, so an unwired
    data-quality gate reddens the pipeline instead of vanishing from it. Their
    `rules:` consult path and trigger conditions ONLY; no credential variable is
    among them. See `decisions_taken` #6 for why the reverse (rules-gating on the
    variable) was removed as a defect in review round 2 — if you are reading this
    bullet to decide how to handle red pipelines on an unwired runner, the answer is
    to finish the GCP setup, never to reinstate that clause. OBSERVED, not predicted:
    pipeline 2737720717 on MR !4 ran with no credentials configured and did exactly
    this — `validate:governance`, `validate:secrets`, `test:python` and
    `build:site-v2` green, `data:build:mr` red on the guard's own message.

  - AUTH SURFACE (`.gcp_auth`, `id_tokens:` on `.data_build_base`). CONSUMERS: every
    Python process the data jobs start. dbt-bigquery's `method: oauth` resolves through
    `google.auth.default()`, as do `google-cloud-bigquery` in `scripts/` and the
    `ingestion.api_football` package, so ALL of them pick up
    `GOOGLE_APPLICATION_CREDENTIALS` without a line of code changing — which is why
    `decisions_taken` #4 kept `method: oauth` verbatim. EFFECT: the credential is a
    short-lived token minted per job, not a stored secret. BLAST RADIUS IF WRONG: the
    data jobs cannot authenticate and fail closed (loudly), which is the same state
    they are in today — this cannot silently degrade to a passing DQ gate.
    NOT CHANGED: the service account, its IAM roles, and the two variable NAMES, all
    carried over from the GitHub workflows unchanged.

decisions_taken: >
  1. NO `gate` jobs. Every GitHub workflow ended in a terminal `gate` job so branch
     protection had one check name to require even when the real job was
     path-filter-skipped. GitLab has no per-check requirement — "Pipelines must
     succeed" gates the whole pipeline, and a rules-skipped job is ABSENT rather than
     failed. Porting the gate jobs would add nine no-op jobs enforcing nothing.

  2. Jobs that branched on `github.event_name` inside steps are SPLIT into `:mr` and
     `:main` variants. GitLab has no step-level `if:`; the alternative was wrapping
     every command in a shell conditional.

  3. The `ingest` path-filter is dropped and `get_new_league_codes.py` runs on every
     data build. GitLab rules cannot express two independent change-flags for one job.
     The script is a BigQuery metadata lookup that returns empty — and ingests
     nothing — whenever every league already has raw tables, so behaviour is preserved
     at the cost of one cheap query.

  4. `method: oauth` is kept verbatim in the CI profiles. dbt-bigquery's oauth method
     resolves through `google.auth.default()`, which honours
     `GOOGLE_APPLICATION_CREDENTIALS`, so the same profile works for a service-account
     key file now and for WIF/OIDC in Phase 3 with no edit.

  5. AUTH IS KEYLESS — Workload Identity Federation, NOT a service account key. The
     four GCP-touching GitHub workflows all used `google-github-actions/auth@v2` with
     `workload_identity_provider` + `service_account` and `permissions: id-token: write`.
     NOTHING SECRET WAS EVER STORED: both values are identifiers (a provider resource
     path and an SA email), and the credential was minted per job from a signed OIDC
     token. GitLab reaches the same architecture with `id_tokens:` + an `external_account`
     credential config, so the migration keeps the property rather than trading it away.

     This REPLACES an earlier draft of this contract that specified a downloaded
     `GCP_SA_KEY` JSON. That draft was written without checking what the GitHub
     workflows did, and it was a real downgrade: a long-lived key does not expire, sits
     in CI variable storage and must be rotated by hand. `deploy-site-v2.yml:89` states
     the repo's standing position outright — a key is the FALLBACK, and "raise it, do
     not adopt it silently". Choosing WIF is therefore not a new mechanism needing
     approval; it is the status quo, and the key would have been the deviation.

     No `gcloud` install is needed. The data jobs run `python:3.11` and shell out to
     `gcloud`/`bq` NOWHERE — dbt, `google-cloud-bigquery` and the ingestion package all
     authenticate through `google.auth.default()`, which handles `type: external_account`
     natively, performing the STS exchange and SA impersonation itself. VERSIONS, stated
     with their source because the two disagree and an unqualified number invites a
     false correction: CI resolved google-auth 2.56.3 (pipeline 2737720717's pip install
     log); the local `.venv` has 2.49.2. `google-auth` is a TRANSITIVE dependency and is
     not pinned in `requirements.txt` — true before this branch as well, so it is not a
     risk this change introduces. Either version works: `external_account` support, and
     the `credential_source: {file: ...}` text-format default the script relies on,
     predate both by years. Writing the credential config directly is what
     `gcloud iam workload-identity-pools create-cred-config` emits anyway, without
     adding an SDK download to every data job.

     CONTINUITY: `GCP_WORKLOAD_IDENTITY_PROVIDER` and `GCP_SERVICE_ACCOUNT` keep the
     GitHub secret NAMES and take the same VALUES, so the existing service account and
     its IAM roles are untouched. What must be created in GCP is one new OIDC provider
     in the pool, trusting GitLab's issuer instead of GitHub's.

  6. The data jobs FAIL CLOSED on missing credentials. Round 1 gated them with
     `rules: when: never` on the variable being absent, reasoning that an unwired
     credential should not redden every MR. `platform-reviewer` failed it, correctly:
     a rules-excluded job leaves NO entry in the pipeline UI, so the pipeline went
     GREEN having run no SQL lint, no dbt build and none of the singular DQ suite —
     the suite the original annotates "DQ is non-negotiable". The GitHub original
     could not reach that state (no credential guard: missing secrets errored the
     auth action and reddened the gate). Red is the signal that the gate is unwired,
     and the translation must not convert it to silence. Now an explicit check in
     `.gcp_auth` exits 1 with the remediation. This also removes an assumption
     nobody could verify — whether GitLab resolves a File-type variable inside
     `rules:if` at all — since the variable is no longer consulted there.

     Under WIF the guard checks THREE things, because there are three distinct
     failure modes and they need different remedies: the two identifiers being unset
     (the CI/CD variables were never added), and `$GITLAB_OIDC_TOKEN` being empty
     (the job is missing its `id_tokens:` block — a YAML defect, not a config one, and
     one that would otherwise surface as an opaque STS rejection).

  7. `schedule` is NOT in `workflow:rules`. A schedule created in the UI runs with
     `CI_COMMIT_BRANCH == main`, which would satisfy `data:build:main`'s rule and fire
     a full prod warehouse build — work reserved below to Phase 3.

  9. THE dbt PROFILE LIVES AT `~/.dbt`, the default — not a custom directory. An
     earlier draft wrote it to `$CI_PROJECT_DIR/.dbt-ci` and pointed `DBT_PROFILES_DIR`
     there. That worked for dbt and BROKE `sqlfluff lint`, because the two resolve the
     profile differently: dbt honours `DBT_PROFILES_DIR`, while sqlfluff's dbt templater
     reads `profiles_dir` from `dbt_project/.sqlfluff`, which is committed as `~/.dbt`.
     So `dbt deps` succeeded and the very next command failed with "Could not find
     profile named 'football_data_pipeline'".

     The draft's stated reason was FALSE and is corrected rather than left standing: it
     claimed the runner home directory "does not exist on a GitLab runner image". It
     does — the jobs run as root on `python:3.11`, so `~` is `/root` and `mkdir -p`
     creates `/root/.dbt` without complaint. There was never a reason to move the file.

     Writing to the default location means dbt, sqlfluff and the committed `.sqlfluff`
     all agree with no environment variable coordinating them, and it matches what
     `ci-data-build.yml` did (`mkdir -p /home/runner/.dbt`, that runner's `~`). The
     alternative — editing `profiles_dir` in `.sqlfluff` — was rejected: that file is
     used by local development too, so a CI-shaped path there would break every
     developer's `sqlfluff lint`.

     FOUND BY A REAL RUN, not by review. Three rounds of review and a YAML parse check
     all passed over it, because nothing static can see that two tools disagree about
     where a file lives. Recorded because it bounds what the other `done_when` entries
     are worth: they establish the config is well-formed, not that it works.

     PINNED BY A TEST, on `platform-reviewer`'s FAIL. The first version of this fix was
     correct and complete but nothing in the suite would have failed if someone restored
     the override — a guard-the-guard gap on an opus-routed guard path, for a mistake the
     YAML's own comment admits is non-obvious and invites under a future "cleanup" edit.
     `test_ci_writes_the_dbt_profile_where_sqlfluff_looks_for_it` now asserts (a) no
     `DBT_PROFILES_DIR` in `variables:`, (b) the directory `.dbt_profile` writes to
     matches `.sqlfluff`'s `profiles_dir` textually, and (c) EVERY job running dbt or
     sqlfluff writes the profile first — (c) because a complete-looking fix that leaves
     one job unpinned fails identically. Textual only: no credentials, no dbt run, so it
     belongs in the offline suite. VERIFIED AGAINST THE REGRESSION rather than assumed —
     the test was run against the pre-fix `.gitlab-ci.yml` at HEAD and FAILED with the
     intended message, then passed once restored. A pinning test that has never been seen
     to fail pins nothing.

  8. Every job carries `needs: []`. The six GitHub workflows were independent; stages
     alone would serialise them so a failing lint stops the test suite from ever
     reporting. Stages are kept only as pipeline-UI grouping.

  THRESHOLD DECLARATIONS. NEW MECHANISM: yes — `.gitlab-ci.yml` is a new CI surface,
  and `PROTECTED_FILES` gains an entry. Both are declared above with their consumers.

  RECURRING COST, two items, the first added after round 1 because `cto-reviewer`
  failed its omission:
  (a) REVIEWER COST. This widens `platform-reviewer` from two guard rows to three, so
      an MR touching `.gitlab-ci.yml` spawns TWO opus specialists. `review_routing.json`
      carries a standing rule that widening those rows is CPO-class and needs "a cost
      approval quoted in decisions_taken" — round 1 quoted the ruling in
      `protected_override` instead, which is not where the rule says to put it. Quoted
      here now: CPO, 2026-08-06, "Yes, match the old coverage" (escalations.log).
      Net against the pre-migration baseline this is ZERO — it restores the cost
      `.github/workflows/**` already carried rather than creating a new one.
  (b) QUERY COST. One `get_new_league_codes.py` BigQuery metadata query per data build
      (decision 3), reading table existence only.

decisions_reserved:
  - Phase 3 (dbt-scheduled, deploy-site-v2, pages-match-preview) is NOT started. Its
    JOBS are reserved; its AUTH is not — the WIF wiring lands here, so Phase 3 adds
    workflows against an auth surface that already works rather than doing both at once.
  - The GCP-side setup (a GitLab OIDC provider in the workload identity pool, plus the
    `principalSet` binding) is NOT done and CANNOT be done from this repo. It is a
    change in the CPO's Google Cloud console, handed over as a step list. Until it
    exists the `data:*` jobs fail closed, which is the designed state, not a defect.
  - Phase 4 (GitHub Projects board sync, ci-failure-watchdog) is NOT started. The CPO
    has chosen "rewrite against GitLab Issue Boards"; the design is not written yet.
  - Whether to DELETE `.github/workflows/` is not decided here. Both rows stay in the
    routing table and the protected list while the GitHub repo exists as a frozen
    mirror. The routing `_doc` records that retiring it returns the counts to eight
    and TWO, in the same commit that deletes the row.
  - WHAT THE PIPELINE HAS AND HAS NOT PROVEN. Pipeline 2737720717 ran on MR !4: four
    jobs green, `data:build:mr` red on the credential guard. So the YAML parses on a
    real runner, the anchors expand, the path rules fire and the fail-closed guard
    works. NOT proven, because no run has yet reached them: the WIF token exchange,
    `dbt build`, `sqlfluff lint` and the singular DQ suite. Those stay unexercised
    until the GCP provider exists, and the review should read every claim about them
    as static validation only.

done_when:
  - `.gitlab-ci.yml` exists and `glab ci lint` reports it valid.
  - No long-lived credential is required by any job: `.gcp_auth` mints a short-lived
    token via `id_tokens:` + an `external_account` config, matching the keyless
    property the four GitHub workflows had. `git grep GCP_SA_KEY` returns hits ONLY
    inside `.claude/task/**`, where they narrate the rejected design — no executable
    file references it. (Stated this way deliberately: "no hits anywhere" would be
    false, and a `done_when` that cannot pass is worse than none.)
  - `data:build:mr` gets PAST `.gcp_auth` on a live runner — the WIF exchange is
    exercised, not merely constructed — and `sqlfluff lint`, `dbt build` and the
    singular DQ suite all run. Nothing short of a green `data:build:mr` demonstrates
    this: the profile-location defect proved that a well-formed config and a working
    config are different claims.
  - The `.gcp_auth` block is verified by PARSING the merged YAML, not by reading it:
    the heredoc terminator sits at column 0 (otherwise the shell swallows the rest of
    the script), the body parses as JSON after variable substitution with no
    unsubstituted `$VAR` left, and both `data:build:mr` and `data:build:main` carry an
    `id_tokens:` block — without which `$GITLAB_OIDC_TOKEN` is empty and every run
    dies on the third guard.
  - The six quality-gate workflows each have a corresponding job, with path filters,
    MR/main split and resource groups preserved.
  - `.gitlab-ci.yml` confers `cto-reviewer` + `platform-reviewer` via
    `review_routing.json` and is in `PROTECTED_FILES`.
  - Every prose restatement agrees with the rows, on BOTH axes (guard-path counts
    and protected-path enumerations), verified by a REPO-WIDE grep rather than by
    re-reading the files already open.
  - `python -m pytest tests/test_governance_hooks.py` is green, and the profile-location
    pin has been demonstrated to FAIL against the pre-fix config, not merely to pass
    against the fixed one.
