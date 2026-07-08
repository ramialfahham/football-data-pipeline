# Review — chore/dbt-warehouse-env-isolation — 2026-07-08

> Machine-checked review artifact (governance G3). Written in step 4 (Lock), after staging and after the
> blinded reviewers returned. Required reviewers for the staged paths (review_routing.json): scope-auditor
> (always), analytics-engineer-reviewer (dbt_project/**), cto-reviewer (.github/workflows/**). Final round:
> the two prior-round FAILs are fixed — push-path `dbt seed` target split, and the concurrent-PR `ci_*` MERGE
> race guarded — and the pre-existing cross-workflow PROD race is CPO-accepted as a residual (issue #667).

diff_sha256: 3e531b2d6f54016a8025bc4436f0bc1c63b9787c19c4cb3490cc9fccf16d66d9

## scope-auditor
VERDICT: PASS
risks_checked:
- All modified paths are within scope_paths; the three protected `.github/workflows/` edits are covered by the contract's protected_override + the 2026-07-08 amendment, and every decision is CPO-locked or reserved (no silent §10 call). The #667 residual is a correctly-classified, disclosed deferral, not scope drift.
- The PR-build defer chain depends on the CI profile carrying a `prod` output before the baseline compile; verified the "Create dbt profile" step writes both `ci` and `prod` outputs before `dbt compile --target prod`, so deferred refs resolve to prod's bare datasets, not `ci_*`.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Push-path `dbt seed --target prod` writes the same `dbt_analytics` dataset that core/marts/base read seeds from via generate_schema_name's unprefixed fallback; verified no `seeds:` schema-override block exists and that the `staging`/`downstream` selectors structurally exclude seeds — so the single prod seed write is sufficient and not stale (the prior-round defect is fixed).
- The `--defer --favor-state` baseline is compiled with `--target prod` (not ci), so unselected upstream refs deferred during a PR build resolve to prod's real bare-dataset relation names, not a `ci_*` copy that would break the defer chain — traced against generate_schema_name's prefix logic.
- Consumption layer unaffected: export_site_data.py / export_pages_data.py hardcode bare `marts`/`core`, and the only workflow invoking an exporter (pages-match-preview) pins `--target prod` (the sole unprefixed target) — export needs no change, verified from source.

## cto-reviewer
VERDICT: PASS
risks_checked:
- The in-scope `concurrency:` guard on the data-build job (`ci-data-build-write-${{ pull_request && 'ci' || 'prod' }}`, cancel-in-progress:false) serialises concurrent PR writes to the shared `ci_*` dataset (closing the fct_fixture_* MERGE race) while isolating the PR and push lanes; checked against all three event types and the step-level `if:` predicates.
- The cross-workflow prod-vs-prod race is pre-existing: the three prod-writers' `on:` triggers are byte-for-byte untouched, so trigger cardinality/collision probability is unchanged from pre-PR state; it is disclosed and CPO-accepted in decisions_reserved with a named follow-up (#667) — a correctly-scoped deferral, not a cover for a new defect.
- Guard-path governance integrity intact: the patch touches no path-filter, no ingest skip-if-exists logic (`new_data`/`get_new_league_codes`), and not the terminal `gate` job body; permissions/secrets/requirements untouched — matching the protected_override's stated scope.

## escalations
(none)
