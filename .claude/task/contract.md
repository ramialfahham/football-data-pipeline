# Task contract — publish dbt docs lineage site on GitHub Pages

> Written on a CLEAN tree (branch feat/dbt-docs-pages off main @ current main).
> Portfolio artifact: a public, explorable dbt docs site (model lineage graph + descriptions + columns),
> folded into the EXISTING Pages deployment as a /dbt-docs/ subfolder. Approved plan:
> C:\Users\Rami\.claude\plans\hazy-imagining-pascal.md. No dbt models, no data changes.

objective: >
  Serve dbt's self-contained static docs at
  https://ramialfahham.github.io/football-data-pipeline/dbt-docs/ by (1) generating them in the existing
  pages-match-preview workflow (which already authenticates to BigQuery and runs dbt), and (2) copying the
  single static HTML into the Pages artifact assembled by build_match_preview_site.sh, and (3) linking the
  site from the README. Reuses the existing single Pages deployment — no second Pages site, no new workflow.
refs: portfolio/visibility request 2026-07-03; approved plan hazy-imagining-pascal.md

protected_override: >
  CPO approved editing the PROTECTED CI workflow .github/workflows/pages-match-preview.yml in plan mode this
  session (2026-07-03): the plan (hazy-imagining-pascal.md) explicitly lists this workflow as a file to touch
  and was approved unchanged via ExitPlanMode ("do it"). Change = ONE additive, continue-on-error
  `dbt docs generate --static` step; no existing step altered; routed to cto-reviewer per review_routing.json.

scope_paths:
  - .github/workflows/pages-match-preview.yml
  - scripts/build_match_preview_site.sh
  - README.md
  - .claude/task/**

impact_map: >
  writers: (1) pages-match-preview.yml gains ONE step `dbt docs generate --static` (continue-on-error:true)
    after the existing dbt test step, before Pages assembly. (2) build_match_preview_site.sh gains a guarded
    block copying dbt_project/target/static_index.html -> _site/dbt-docs/index.html. (3) README.md gains one
    link under the Live-preview block.
  downstream: the deployed Pages artifact gains a /dbt-docs/ path. The match-preview app path is unchanged.
  layer_rules: not applicable (no dbt models; this is CI + build-script + docs).
  deploy_order: additive. The docs step is continue-on-error and the copy is `-f`-guarded, so a docs failure
    can NEVER block or break the existing app deploy. No change to run cadence (existing schedule + push paths).
  blast_radius: the pages-match-preview workflow runs one extra warehouse metadata (catalog) query per build
    and publishes one extra static page. No dbt model, no seed, no data row, no app behaviour changes. The
    match-preview build/test/export/deploy steps are untouched.

decisions_taken: >
  Fold into the EXISTING Pages workflow + _site folder (NOT a new workflow) — GitHub Pages serves one
  deployment per repo; two deploy-pages jobs would race. `dbt docs generate --static` (dbt 1.7.2 supports it)
  bundles manifest+catalog into ONE self-contained target/static_index.html — cleanest for static hosting.
  Docs step is continue-on-error and the copy is file-guarded so docs are strictly best-effort and cannot
  regress the app. Triggers left as-is: the daily schedule refreshes docs within 24h; broadening push paths
  would add warehouse-touching runs (avoided on cost grounds). Cost = one catalog metadata query per existing
  build, negligible next to the dbt run/test already in the job; no new cadence. Exposure = none new (repo is
  public; static docs carry schema metadata, not warehouse data).

decisions_reserved:
  - No `dbt docs serve` local tooling, no custom theming, no per-model description backfill (later content pass).
  - The landscape social-preview image remains a separate CPO manual step.
  - If the docs ever need to be strictly fresh per-merge, broadening triggers is a separate cost decision.

done_when:
  - pages-match-preview.yml has the `dbt docs generate --static` step (continue-on-error) in the right place;
    the existing app build/test/export/deploy steps are unchanged.
  - build_match_preview_site.sh copies target/static_index.html -> _site/dbt-docs/index.html, guarded by -f.
  - README.md links the dbt-docs site once, under the Live-preview block.
  - validate-local offline gates pass (YAML/shell are not dbt-built locally; CI is the real e2e gate).
  - scope-auditor + cto-reviewer PASS (>=2 named risks each); review.md binds; CPO merges.
  - POST-MERGE (real e2e gate, not blocking this PR): the workflow log shows the docs step produced
    target/static_index.html and the copy landed; .../dbt-docs/ loads the lineage graph; .../match-preview/
    still deploys and loads.

amendments:
  - 2026-07-03: fresh contract (prior task add-MVP-screenshot merged as #641). CPO approved the plan
    (hazy-imagining-pascal.md) in plan mode this session ("do it" -> ExitPlanMode approved unchanged).
