# Task contract — hosting deploy job (Firebase Hosting, launch group 3)

> Written on a CLEAN tree (branch `feat/deploy-site-v2-firebase` off main at 33662ae).
> Plan: C:\Users\Rami\.claude\plans\rosy-juggling-quill.md (CPO-approved via ExitPlanMode 2026-07-24).

objective: >
  Build the export->build->deploy automation for the v2 site (launch group 3). A CI workflow
  that runs the full export, builds the ~15k-page site with a raised Node heap, and deploys to
  Firebase Hosting (the CPO's chosen vendor, 2026-07-24). Ships MANUAL-DISPATCH ONLY and deploys
  to the Firebase `.web.app` URL with NO custom domain: the recurring run is gated on the CPO's
  cost+schedule confirmation, and going public is gated on the open imprint question. Both gates
  stay closed in this PR; opening each is a later one-line change.

refs: >
  Plan file above. Verified this session: `dbt-scheduled.yml` (cron 0 4 * * *) is the daily
  pipeline; it and `pages-match-preview.yml` auth to GCP via WIF secrets GCP_WORKLOAD_IDENTITY_PROVIDER
  + GCP_SERVICE_ACCOUNT (reused here, no new secret). `scripts/export_site_data.py` already emits the
  full per-entity layout via `--entities`/`--out` and always writes competitions.json (line ~1155);
  no export code change is needed. #818 proved the full build needs NODE_OPTIONS=--max-old-space-size=8192
  and OOMs at default heap. `astro.config.mjs` base is "/v2/" only for the earlier GitHub Pages subpath
  layout; its own comment anticipates the flip to root.

scope_paths:
  - .github/workflows/deploy-site-v2.yml
  - site_v2/firebase.json
  - site_v2/astro.config.mjs
  - docs/site_architecture.md
  - .claude/active_work.md

protected_override: >
  CPO go for this task, 2026-07-24 (session prompt): "build the export->build->deploy job ...
  deploys to the chosen vendor" with the explicit note that `.github/workflows/` "is a PROTECTED
  path — needs a protected_override in the task contract + cto review at the opus floor." Plan
  CPO-approved via ExitPlanMode same day. Only the ONE new workflow file is added under the
  protected prefix; no existing workflow, hook, agent or setting is touched.

impact_map: >
  writers: NONE. No warehouse/dbt/seed/ingestion change. The export step READS marts only
    (`select *` from consumption marts) and writes JSON into `site_v2/src/data/` at build time;
    it does not write BigQuery. No prod-warehouse write, so no need for the `prod-warehouse-write`
    concurrency group.
  downstream (protected workflow — trace what depends on it, not table lineage):
    - Fires ONLY on `workflow_dispatch` (manual). No `schedule`, no `workflow_run`, no `push`/`pull_request`
      trigger, so it runs on nothing automatically and cannot fire on this PR. No existing workflow
      calls or needs it; it is a new leaf. If it is wrong, a manual dispatch fails and nothing else
      breaks — no recurring run, no prod write, no other job, no live URL (custom domain not attached).
    - On failure: the deploy step is the only externally-visible action; it targets the Firebase
      `.web.app` URL. Until the two GCP prerequisites (enable Firebase, grant roles/firebasehosting.admin
      to GCP_SERVICE_ACCOUNT) are done, the deploy step fails there and the build steps still pass.
  downstream (site_v2 config): `astro.config.mjs` base "/v2/" -> "/" changes only internal link/asset
    prefixes; the `dist/` file layout is unchanged, so `ci-site-v2.yml` (asserts dist/index.html,
    dist/{de,en,fi}/index.html) still passes. `firebase.json` is consumed only by the new workflow's
    firebase deploy step.
  layer_rules: consumption boundary (Appendix A5) — the export selects/enumerates, derives no fact;
    unchanged here (no export edit). check_layer_contract stays green (no model/staging change).
  deploy_order: none in the warehouse sense. Conceptually the deploy runs AFTER the 04:00 nightly so
    it exports fresh marts, but it is manual-only now, so timing is manual; the recurring chain
    (`workflow_run` on dbt-scheduled, or a later cron) is deferred to the cost+schedule confirmation.
    Read-only marts access means no serialization vs the nightly is required.
  blast_radius: bounded / additive. One new workflow (manual-only), one new hosting config, one
    reversible base flip, one handover edit. No warehouse object, no runtime service, no secret value
    touched (secrets referenced by name only), no recurring run enabled, nothing public.

decisions_taken: >
  (1) Vendor = Firebase Hosting (CPO decision 2026-07-24, AskUserQuestion this session).
  (2) Manual `workflow_dispatch` only in this PR (honours "confirm cost+schedule before any recurring run").
  (3) Deploy to the Firebase `.web.app` URL, custom domain NOT attached (honours "don't flip public until I say so").
  (4) Reuse the existing WIF secrets for GCP auth; deploy via ADC, no long-lived key committed or printed.
  (5) Flip astro `base` "/v2/" -> "/" — required for correct root serving; the "/v2/" base was for the
      earlier GitHub Pages subpath layout, and the config comment already anticipates the flip. CPO-approved in the plan.
  (6) Export only the built pages' entities (teams,fixtures) to minimise scan + build; add more when
      player/competition pages ship.

decisions_reserved:
  - The recurring schedule and its cost: measured exact bytes (via a free `--dry_run`) and the trigger
    shape (`workflow_run` vs cron) go to the CPO before any automatic run is enabled. Not decided here.
  - Custom domain, DNS at IONOS, and announcement (go-live) — the CPO's call, also blocked on the
    imprint operator/address question. Not decided here.
  - Whether firebase-tools accepts WIF/ADC for hosting deploys in CI: verified at first dispatch; the
    fallback (a firebasehosting.admin key as a secret) would be raised to the CPO, not adopted silently.

done_when:
  - `.github/workflows/deploy-site-v2.yml` exists, triggers on `workflow_dispatch` only, auths via the
    existing WIF secrets, runs the export, builds with NODE_OPTIONS=--max-old-space-size=8192, and
    deploys `--only hosting` to project football-data-pipeline-gcp. No schedule/workflow_run present.
  - `site_v2/firebase.json` points hosting at `dist` with trailingSlash true.
  - `site_v2/astro.config.mjs` base is "/".
  - `python scripts/check_layer_contract.py` green; `validate-local` Tier 1 green; the sample Astro
    build is clean in de/en/fi after the base flip.
  - Workflow YAML parses (actionlint if available, else a YAML load).
  - ONE commit; review.md covers the full diff with cto-reviewer (opus) + scope-auditor PASS; pushed
    with an explicit refspec; PR opened. The CPO merges. Deploy is verified only after the CPO does the
    two GCP prerequisites and dispatches manually — that result is reported, not claimed.

amendments:
  - 2026-07-24: + docs/site_architecture.md — authority: doc-sync rule (working_agreement §2,
    scope-auditor FAIL this branch). content: the v2-hosting references (data-flow, tech-stack row,
    deploy paragraph, decisions-log row) synced from GitHub Pages to Firebase, per the CPO vendor
    decision 2026-07-24. Mechanical sync of an already-CPO-decided fact, not a new decision. The doc's
    pre-existing MVP-lifecycle / #377 wording is deliberately NOT touched — this PR is the new-website
    deploy job; any MVP cleanup is a separate task (CPO directive 2026-07-24, "we work on the new
    website").
