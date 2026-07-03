# Review — docs/readme-design-decisions — 2026-07-03

> G3 Lock artifact. Docs-only task: add a "## Design decisions" section to README.md (five rationale-level
> bullets on the WHY/trade-offs behind the architecture) between "## Highlights" and "## BigQuery layout".
> Anti-drift by design: rationale only, no inventory, facts linked to authoritative sources. Required set
> (routing): **scope-auditor only** — README.md matches no path pattern. Round 1 (hash d2cf0091) —
> scope-auditor PASS with risks checked-and-held.

diff_sha256: d2cf00914f9d3bec7b091a2f69270124655150bab9f3bcd67bc4a396d261edf5

## scope-auditor
VERDICT: PASS  (round 1)
risks_checked:
- Drift-resistance via link-not-copy: the new section links outbound to four authoritative in-repo sources
  (docs/competition_registry.yml, scripts/check_layer_contract.py, dbt_project/docs/layering.md,
  dbt_project/docs/engineering_standards.md — all verified to exist) and restates no inventory (no model/
  competition counts, no version numbers), so it stays true as the underlying facts change. Directly
  addresses the #505 doc-clutter/drift risk that motivated folding this into the README instead of a 4th doc.
- Factual accuracy of the five claims: each was checked against the real system and holds — the unified-raw/
  league_code + zero-file rule (CLAUDE.md architecture), the strict layer contract (layering.md), DQ-as-a-
  build-gate (engineering_standards testing policy), "metrics defined once" (metric_catalogue.csv is
  referenced by multiple models and guarded by assert_no_uncatalogued_season_metric), and identity-vs-
  affiliation (dim_player / dim_team + the *_season_mapping models). Voice is neutral and factual with no
  self-praise (per the #640 tone ruling); "foundation for a future semantic layer" reads as rationale, not a
  commitment. Scope is exactly README.md + .claude/task/**; no existing README content altered or dropped;
  no §10 decision (fold-into-README + the exact copy were CPO-approved in-session).

## escalations
(none)
