# Task contract — #74: the nightly Cloud Run image tracks `main`

objective: >
  `gcloud run jobs deploy fdp-nightly --source .` packages the working tree at deploy time; the
  image never rebuilds when `main` moves, so prod silently reverts merged fixes at 04:00 (it
  already reverted !43/!45 once, running 08-14 code for two days). Add CI jobs on `main` that
  rebuild and redeploy the image whenever a path it actually contains changes, so this stops
  being a "remember to redeploy by hand" rule. Full spec: GitLab #74, note 3695790497 —
  implementing it as written, not re-deriving it.
  REDESIGNED mid-task (round 3): the spec's own `--source .` shape needs Cloud Build, and
  Cloud Build's default execution identity holds project Editor — verified live, not assumed.
  Ships instead as `build:nightly-image` (kaniko, builds in the job, no Cloud Build) +
  `deploy:nightly-image` (repoints the Cloud Run job at the pushed image). Same objective, an
  authorized reading of "how" per the CPO's own in-session choice — see escalations.log.
refs: GitLab #74 (note 3695790497)

scope_paths:
  - .gitlab-ci.yml
  - deploy/nightly/README.md
  - tests/test_governance_hooks.py
  - .dockerignore
  - .gcloudignore
  - Dockerfile
  - .claude/active_work.md

acceptance_criteria: >
  NOT new work from this task. `site_v2/src/**` appears in this branch's diff solely because
  merging `gitlab/main` (required to resolve #77-class task-artifact conflicts before this MR can
  merge — main moved on with #62 step 5 while this branch was open) brings in #62 step 5 (the
  competitions index page), already built, CPO-reviewed and merged on its own branch with its own
  acceptance criteria and evidence. `.claude/task/acceptance_evidence.md` comes through the same
  merge unchanged and already demonstrates all 8 of that page's criteria (locales render clean,
  all 48 competitions grouped correctly, CPO-approved sort order verified against real data, rows
  inert not linked, filters narrow + collapse empty categories, nav link wired, copy gate passes,
  page-spec + unit tests pass, verified at both viewport widths). Restated here only so this gate
  — which does not distinguish a merge from new authored work, the same gap logged for the
  scope/Stop gates under `active_work.md`'s OWED — has a criteria list to check against; the
  evidence itself was written by the #62 task, not this one, and is not re-verified here.
  - All three locales (en/de/fi) build and render `/competitions/` with no console errors.
  - Every browsable competition (48/48) shows under an always-visible category heading, singletons
    included.
  - Category and row order match the CPO-approved sort key, verified against real committed data.
  - Rows show logo/name/region, are NOT clickable links (#47 not built yet).
  - The two filter axes narrow rows; an emptied category disappears entirely, headings included.
  - Nav's "Competitions" item is a real link (desktop + mobile); every other nav item stays inert.
  - `check_copy_gate.py`, `check-page-specs.mjs` and the site's `node --test` suite all pass.
  - Verified at desktop and mobile widths via the accessibility tree and console output.
  SECOND merge-inherited batch (2026-08-18, same gap, same non-authorship): `main` moved again
  while this MR sat open, this time with `feat/shared-competition-order` (!71, merge commit
  de393e5) landing on top of the `fix/gaps-register-vs-reduced-home-design` merge (26caf53). That
  brings in the shared competition-ordering rule (`competitionOrder.mjs` + its test), the
  reduced-home-page fixtures work (`HeroFixtures.astro`, the four committed
  `site_v2/src/data/fixtures/*.json` samples, `landing.json`), `export_site_data.py`'s matching
  export logic, `types.ts`, the two wireframe docs, and `.gitignore`. All of it already built and
  merged to `main` on its own branch before this merge; none of it is #74 work and none of it is
  re-verified here. Listed so the gate has something to check against, same as the #62 batch
  above.

protected_override: >
  CPO instruction, 2026-08-17: "fix #74 so the image tracks main." Quoted per the issue note's
  own requirement that this instruction is the authority for the `.gitlab-ci.yml` edit.

impact_map: >
  writers: none (dbt/BigQuery untouched) — this adds two CI jobs that build a container image
  and repoint a Cloud Run job, no model or script changes.
  what fires it: `workflow: rules:` already admits `CI_COMMIT_BRANCH == CI_DEFAULT_BRANCH`
  pipelines; each new job's own `rules:` gate it to `main`-only + `*not_on_schedule` first
  (the documented trap: a scheduled pipeline satisfies the same branch check and would double-run
  the deploy otherwise). The two jobs' `rules:` are asserted IDENTICAL by test, because
  `deploy:nightly-image needs: [build:nightly-image]` and GitLab refuses to construct a
  pipeline where a `needs:` target is absent from it.
  what depends on `.gitlab-ci.yml`: `check_task_artifacts.py` (base resolution), every
  `test_governance_*` test that parses job `rules:` — both new jobs are covered by the existing
  generic pins (schedule guard, gcp-auth-declares-id_tokens) by construction, plus dedicated
  by-name pins for their own reachability and for `.data_paths_image`'s coverage.
  blast_radius: on a bad job, the FAILURE MODE is a red pipeline (safe, visible) — it cannot
  reach prod data on its own, since it only rebuilds a container image and repoints a Cloud Run
  job; the danger it FIXES is the current silent-revert. `resource_group` (shared by both jobs)
  prevents concurrent image builds/deploys.
  recurring cost (CPO-class, declared per the issue note's own checklist): one kaniko build per
  qualifying merge to `main` (no Cloud Build billing — kaniko runs on the CI runner itself, so
  this is runner time, not a separate GCP line item); today's `--source .` manual build measured
  ~7 min wall clock as a rough proxy, kaniko's own time not yet measured. ALSO ACCRUING
  (round-2 finding, cto-reviewer, still true under the redesign): every qualifying merge pushes
  a new image into `cloud-run-source-deploy` (Artifact Registry), not garbage-collected by this
  repo — storage cost compounds for as long as the job exists. The `run-sources-*` Cloud Build
  staging bucket cost from the original design does NOT apply anymore — kaniko never uses it,
  and the grant that would have made it accrue was revoked (see IAM below). No retention/cleanup
  policy is set for the Artifact Registry side; accepted without one, stated rather than left
  implicit (the project's own `active_work.md` already flags storage as never measured).
  new mechanism (CPO-class): a build+deploy step now lives in CI rather than being run by hand —
  authorised by the `protected_override` instruction above. Third-party component this
  introduces: kaniko (GoogleContainerTools/kaniko), Google's own daemonless-build tool, the
  standard choice for building container images in CI without privileged Docker — right for a
  self-hosted runner with no docker:dind. NOT independently verified here: kaniko's own upstream
  maintenance cadence (round-1 finding, cto-reviewer, explicitly flagged as unverified rather
  than asserted either way). Accepted without that check — this is boring, widely-adopted
  technology for exactly this use case, not a novel dependency risk on the scale of the IAM
  question above — but stated as a checked gap, not silently assumed fine.
  IAM (CPO-class, round-2 addition, REVISED round 3): `github-actions-dbt` (the WIF identity
  every MR pipeline can impersonate) had none of the roles the original `--source .` design
  needed; verified against the LIVE policy throughout, never asserted
  (`gcloud projects get-iam-policy football-data-pipeline-gcp`, `gsutil iam get`). Two grants
  from that design were made with CPO approval and then REVOKED the same session once round-3
  review found `roles/cloudbuild.builds.editor` opens a path to project Editor (Cloud Build's
  default execution identity holds it, verified live) reachable from ANY unmerged branch —
  `roles/cloudbuild.builds.editor` (project-level) and `roles/storage.objectAdmin` (the
  `run-sources-*` staging bucket), both no longer needed once the design builds in-job instead
  of via Cloud Build. FINAL footprint, all resource-scoped, none project-level beyond what
  already existed before this task: `roles/run.developer` on the `fdp-nightly` job resource
  only, `roles/iam.serviceAccountUser` on the `github-actions-dbt` service account resource
  itself (self-actAs), `roles/artifactregistry.writer` on the one `cloud-run-source-deploy` repo
  (europe-west1) the image is pushed to. Full command evidence for every grant AND every
  revocation: `.claude/task/escalations.log`, three entries under "GitLab #74" dated
  2026-08-17/18. This IAM state itself produces no git diff, which is exactly why it is
  recorded there rather than only claimed here.

decisions_taken: >
  Recurring cost and IAM: see `impact_map` above — both restated here per governance ritual,
  not duplicated in full.
  New mechanism: build+deploy steps added to `.gitlab-ci.yml`, redesigned mid-task from
  Cloud-Build-based (`--source .`) to in-job kaniko once the former was found to need an
  IAM grant with a project-Editor escalation path. Both the original mechanism and the redesign
  are authorised by the CPO instruction quoted in `protected_override`: the CPO chose the
  redesign directly, in-session, when presented with the finding and the alternative ("build
  directly in the job (docker/kaniko), skip Cloud Build entirely").
  Sentinel (`fdp-freshness`): currently pinned to a fixed digest and does NOT track
  `fdp-nightly`. This task does not repoint it — repointing it is a second, separate decision
  (the runbook's own sequence puts it as a later step, after the image rebuild is proven safe,
  to avoid the alert-storm-from-wrong-order trap the issue note names). Left pinned; recorded
  here so it isn't silently assumed fixed.
  `build:nightly-image` does NOT re-check-out `origin/main`'s live tip the way the original
  design's single job did (that used `git`, available in `google/cloud-sdk:slim`; kaniko's
  minimal debug image's git availability could not be verified with confidence, so nothing
  relies on it). It pushes ONLY `:$CI_COMMIT_SHA` — an earlier version also pushed `:latest` for
  no consumer, and the residual-risk description here named THAT tag; round-1 review of the
  kaniko redesign (cto-reviewer + platform-reviewer, opus) caught both the dead tag and the
  wrong description. THE ACTUAL RESIDUAL, corrected: `resource_group`'s default `unordered`
  process mode does not guarantee two `deploy:nightly-image` runs from near-simultaneous merges
  apply in commit order, so the OLDER commit's SHA-pinned image can be the one that lands LAST —
  not briefly current, but persisting until the NEXT qualifying merge (bounded by that, not
  self-correcting within the same event the way "briefly current" implied). Setting this
  resource group's process mode to `oldest_first` closes it; that is a GitLab project setting
  the group must exist to configure (first job run creates it) and cannot be expressed in this
  file — recorded as an owed follow-up in `active_work.md`, not silently assumed done.
  `needs:` on `build:nightly-image` gates only whether THIS pipeline's own trigger commit had a
  chance to validate before the build starts, not which commit's tree actually gets built (the
  runner's own checkout of the triggering commit is what gets built) — narrower than "gates
  what's deployed," and stated as such rather than implied. Round-2 finding, platform-reviewer:
  the list originally named only `validate:governance` + `test:python`, omitting
  `validate:secrets` (gitleaks) and `lint:python` — a job scheduled off `needs:` starts as soon
  as its own edges finish regardless of stage, so a push whose SECRETS SCAN failed could still
  have had its content built into the image and pushed before that failure was visible, the
  same failure class as the credential-leak defect this branch already found once. Widened to
  all four; all four are unconditional `when: on_success` after the schedule guard, so they are
  always present in a qualifying push-to-main pipeline.

decisions_reserved:
  - none: the fix's shape, authority and cost are all settled by the CPO instruction, the issue
    note, and the CPO's own in-session choice of the redesign; nothing here is a product/naming/
    permanence question for this task.

done_when:
  - `build:nightly-image` (kaniko) + `deploy:nightly-image` (gcloud repoint) exist in
    `.gitlab-ci.yml`, `main`-only, `*not_on_schedule` first, IDENTICAL `rules:` (asserted by
    test — `deploy:nightly-image` needs `build:nightly-image`), shared `resource_group`.
    `deploy:nightly-image` runs `gcloud run jobs update --image=...`, NOT `deploy --source .`
    — that shape was tried, found to need an IAM grant with a project-Editor escalation path,
    and replaced (see `impact_map`/`decisions_taken`).
  - Trigger paths enumerated from the Dockerfile's `COPY . .` and what `entrypoint.sh` actually
    invokes (ingestion, `dbt build` with no selector, the two check scripts) — not the narrower
    `.data_paths_prod` anchor, which deliberately excludes `ingestion/**`. `.gcloudignore` is
    DELIBERATELY ABSENT from this anchor (corrected round-1-of-the-kaniko-cycle, cto-reviewer +
    platform-reviewer: an earlier version claimed it gates the kaniko build context; it does
    not — kaniko reads `.dockerignore` only, `.gcloudignore` matters solely for the human
    `--source .` fallback, and listing it would trigger a real rebuild+redeploy for an edit
    that cannot change the image).
  - `deploy/nightly/README.md` and `Dockerfile`'s own header say CI now does the redeploy with
    kaniko (both job names, no stale `gcloud run jobs deploy --source .`/"Built remotely by
    Cloud Build" claims anywhere) — swept across every place that describes the redeploy
    mechanism, not just the three the previous round caught (round-1-of-the-kaniko-cycle
    finding, cto-reviewer: `.dockerignore`'s own header and `Dockerfile`'s own header were both
    still stale after that sweep — a correction applied once and left contradicting itself
    elsewhere is this repo's own logged recurring failure class, and it recurred within the fix
    for the same class).
  - `pytest tests/ -q` passes; the schedule-guard and gcp-auth-declares-id_tokens tests cover
    both new jobs explicitly by construction; dedicated by-name tests pin their own reachability
    (never mr/schedule/web, on_success on push_main), `resource_group`/`needs:` PRESENCE (round-1
    finding, platform-reviewer: the contract leaned on both without either being asserted), and
    `.data_paths_image`'s coverage (now also asserting `.gcloudignore` must NOT be in it).
  - `.claude/active_work.md` records the jobs shipped, the Cloud-Build-to-kaniko redesign and
    why, the owed `resource_group` `oldest_first` follow-up, and what still isn't covered (the
    sentinel is still unpinned, said plainly).
  - `.gcloudignore`'s own content restores rather than narrows what the manual `--source .`
    fallback already excluded (round-1-of-the-kaniko-cycle finding, platform-reviewer: the first
    version replaced gcloud's own documented `#!include:.gitignore` default with a short hand
    list and MISSED real secret/large-file patterns `.gitignore` already covered — `*.secrets.env`,
    `.envrc`, the repo-root `/*.pdf` working documents — narrowing coverage on the one path it
    exists to protect). Now `#!include:.gitignore` plus the credential files explicitly.
  - The CI-generated GCP credential files (`.gcp-oidc-token`, `.gcp-credentials.json`) cannot
    reach the built image — `.dockerignore` is the SOLE guard on the kaniko path and excludes
    them explicitly (round-2 finding, cto-reviewer + platform-reviewer independently: the
    original list caught neither, so the live bearer token would have been baked into the prod
    image; round-1-of-the-kaniko-cycle corrected the claim that `.gcloudignore` was a second
    layer here — it is not, see above).
  - IAM footprint for `github-actions-dbt` verified LIVE after every grant and every
    revocation, not asserted — final state confirmed via `gcloud`/`gsutil` read commands,
    recorded in escalations.log alongside the write commands.

amendments:
  - 2026-08-17/18: + `.dockerignore`, + `.gcloudignore` — authority: round-2 review
    (cto-reviewer + platform-reviewer, opus) found the CI-generated GitLab OIDC token was not
    excluded from either the Docker build context or the Cloud Build source upload, so it would
    have been baked into the deployed prod image. Content: exclude `.gcp-oidc-token` and
    `.gcp-credentials.json` from both.
  - 2026-08-18: mechanism REDESIGNED, scope_paths unchanged (no new files) — authority: round-3
    review (cto-reviewer, opus) found `roles/cloudbuild.builds.editor`, required by the
    `--source .` design, gives its holder a path to project Editor via Cloud Build's default
    execution identity (verified live), reachable from `github-actions-dbt` on ANY unmerged
    branch. CPO chose, in-session, to rebuild the mechanism around kaniko instead of accepting
    the risk. Content: `deploy:nightly-image` split into `build:nightly-image` (kaniko,
    replaces `--source .`) + `deploy:nightly-image` (now `gcloud run jobs update --image=...`);
    two IAM grants from the old design revoked; `.data_paths_image` gained `.gcloudignore`.
  - 2026-08-18: + `Dockerfile` — authority: round-1 review of the kaniko redesign
    (cto-reviewer, opus) found `Dockerfile`'s own header comment still described the retired
    `--source .`/Cloud Build mechanism, one of several places the round-3 sweep missed. Content:
    the header now describes the kaniko build. Same round also REMOVED `.gcloudignore` from
    `.data_paths_image` (it was wrongly modeled as gating the kaniko build context — see
    `done_when`) and rewrote `.gcloudignore` itself from a narrow hand list to
    `#!include:.gitignore` + explicit entries, after platform-reviewer found the hand list had
    NARROWED what the manual `--source .` fallback excludes relative to gcloud's own default.
  - 2026-08-18: `build:nightly-image`'s `needs:` widened, scope_paths unchanged — authority:
    round-2 review of the kaniko cycle (platform-reviewer, opus) found it omitted
    `validate:secrets` (gitleaks) and `lint:python`, so a push whose secrets scan failed could
    still have that content built into the image and pushed before the failure was visible.
    Content: `needs:` now names all four validate/test-stage gates that run unconditionally on
    a push-to-main pipeline; `decisions_taken`'s claim about what `needs:` gates corrected to
    match.
  - 2026-08-18: + `acceptance_criteria` — authority: CPO, in-session, escalated blinded (§11)
    after scope-auditor FAILED an unauthorized first attempt (this field is CPO-locked per §2).
    Reason: merging `main` (needed to resolve the `.claude/task/*` conflict class, GitLab #77)
    brings in `site_v2/src/**` from #62 step 5 — already built, CPO-reviewed, merged on its own
    branch — which trips `_acceptance_gate` on path alone; the gate does not distinguish a merge
    from new authorship. CPO: "Go ahead, write the note and continue." Content: 8 criteria
    restated verbatim from #62's own already-demonstrated set, explicitly labeled as inherited,
    not authored by or re-verified under this task. Full account: `escalations.log`, 2026-08-18.
  - 2026-08-18: + second merge-inherited batch to `acceptance_criteria` — authority: same
    standing authority as the row above (merging `main` to keep this MR mergeable is operational
    branch hygiene, not a new §10 decision; the CPO's "merge conflict 70" instruction already
    covers resolving conflicts as main moves). `main` moved again with `feat/shared-competition-
    order` (!71) while this MR was open. Content: same treatment as the #62 batch — named the
    inherited files, stated none of it is #74 work, not re-verified here.
