# Task contract — #500 PR-d step 6 (teardown, partial): dead-seed trigger ref + stale doc model-name globs

> Governance G2/G3 contract. Written on a clean tree BEFORE any edit.
> Step 6 is CPO-directed. The CPO approved a TWO-candidate scope (candidates 1 + 4 of five)
> this session (2026-06-27) and delegated unattended execution; candidates 3 + 5 are DEFERRED.

objective: >
  Remove two residual references left by the #500 PR-d migration:
  (1) the GitHub Pages deploy workflow still triggers on the DELETED seed
      `dbt_project/seeds/metric_definitions.csv` (removed in PR-d step 2). Repoint that one
      trigger path to the seed that now carries the metric definitions,
      `dbt_project/seeds/metric_catalogue.csv`. The catalogue seed is covered by no existing
      path glob, whereas `site/match-preview/metric_bindings.csv` is ALREADY covered by the
      `site/**` glob — so only the catalogue needs adding, and nothing else in the trigger
      block is touched.
  (2) two docs still use the pre-rename shorthand `mart_fixture_stats__{team,player}` and
      `mart_fixture_stats__*` for the marts now named `mart_team_fixture_stats` /
      `mart_player_fixture_stats` (entity-first, per the #500 rename sweep). Update both refs
      to the canonical names (matching the `site_architecture.md` convention).

refs: >
  #500 PR-d step 6 (teardown). Scope = candidates 1 + 4 ONLY (CPO-approved 2026-06-27).
  Candidate 3 (benchmark-macro (key,column) seam) and candidate 5 (metric_catalogue
  description enrichment) DEFERRED to the CPO. Out-of-scope trigger-block rot discovered
  during exploration — a dead `scripts/build_metric_glossary_json.py` trigger path (older
  glossary work, not #500 PR-d) and stale flat mart paths (lines 18-23, from the mart-reorg
  refactor that moved marts into 5_marts/{domestic_league,shared}/) — is NOT touched here and
  is flagged separately for the CPO to scope.

scope_paths:
  - .github/workflows/pages-match-preview.yml
  - docs/content_architecture.md
  - docs/wireframes/99_gaps_register.md

protected_override: >
  `.github/workflows/pages-match-preview.yml` is a PROTECTED governance path. CPO (Rami)
  approved step-6 candidate 1 in this session (2026-06-27) and delegated unattended execution.
  cto-reviewer is the required platform reviewer for the workflow change (review_routing.json).

decisions_taken: >
  Faithful migration of an existing trigger's intent (a change to the metric-definitions seed
  should rebuild + redeploy the Pages site) across the #500 seed rename. metric_catalogue.csv
  (not metric_bindings.csv) is the correct new trigger: bindings is already covered by `site/**`,
  the catalogue seed is otherwise untriggered, and line 129 of the workflow regenerates
  metric_definitions.json from the catalogue on every run. The doc edits are a pure name update
  to marts that already exist on main. No product, metric, naming, or mechanism decision is made.

decisions_reserved:
  - Candidate 3 (collapse the benchmark-macro (metric_key, season_column) pairs now that they are
    identical) — this drops a deliberate abstraction seam; a design call for the CPO, not cleanup.
  - Candidate 5 (enrich metric_catalogue.csv descriptions with provider semantics) — domain-semantic;
    CPO + football-analytics.
  - Whether/under which refactor the remaining trigger-block rot (dead build_metric_glossary_json.py
    path; stale flat mart paths) is fixed. Flagged for the CPO; not pre-decided here.

done_when:
  - pages-match-preview.yml triggers on `dbt_project/seeds/metric_catalogue.csv` in place of the
    deleted `dbt_project/seeds/metric_definitions.csv`; no other trigger path is added or removed.
  - docs/content_architecture.md and docs/wireframes/99_gaps_register.md use
    `mart_team_fixture_stats` / `mart_player_fixture_stats`; no other doc content changes.
  - Required reviewers (scope-auditor, cto-reviewer, bi-analyst-reviewer) PASS with >=2 named risks
    each; review.md diff_sha256 binds the staged diff; CI is green. The CPO merges (never self-merge).

amendments: (none)
