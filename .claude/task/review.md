# Review — docs/readme-portfolio-polish — 2026-07-03

> G3 Lock artifact. Docs-only portfolio task: README top-of-funnel rewrite (headline, badges,
> labelled "Live preview" MVP link, Mermaid architecture diagram, Highlights) + NEW docs/assets/README.md
> (screenshot / social-preview spec) + contract replacement (prior Phase C brick 1 merged as #638).
> Required set (routing): **scope-auditor only** — README.md and docs/assets/** match no path pattern,
> so no analytics-engineer / cto / bi-analyst / data-engineer is triggered. No dbt/scripts/CI/site path touched.
>
> Round 1 (hash from the 13-workflows copy) — scope-auditor FAIL: one finding — the Highlights claimed
> "CI/CD across 13 GitHub Actions workflows" but only 10 are active (3 paused in .github/workflows/_paused/),
> a misleading number for public portfolio copy. Fix: dropped the count entirely →
> "CI/CD on GitHub Actions — lint, validation, data build, security scanning, and scheduled deployment."
> Round 2 (hash e47ec73c) — scope-auditor PASS with two risks checked-and-held.

diff_sha256: e47ec73ca6a67820c0a15a9deca5d2ba427bb05272fbfb23717e458ca9fe0c87

## scope-auditor
VERDICT: PASS  (round 2; round-1 FAIL finding — the "13 workflows" overstatement — resolved)
risks_checked:
- Factual accuracy of user-visible, permanent portfolio copy: the round-1 finding (claimed "13 GitHub
  Actions workflows" vs 10 active + 3 paused) is resolved by dropping the count and describing the pipeline
  categories instead (README line 34 of the patch). Remaining factual surface verified: both badge targets
  (ci-validate.yml, ci-data-build.yml) point to workflow files that exist; the Mermaid diagram matches the
  documented layer flow (API-Football → BigQuery raw → staging → base → core → intermediate → marts →
  GitHub Pages) per layering.md and is a faithful conceptual view; the MVP link is honestly labelled
  "Live preview" with v2 noted as in active development — no overstatement of the MVP-vs-v2 status.
- Scope + decision-rights containment: the cumulative diff touches only README.md, docs/assets/README.md,
  and .claude/task/** — all within the contract's scope_paths; nothing below the new funnel ("## BigQuery
  layout (datasets)" onward) is altered or dropped. All §10-class choices in the copy (framing option A,
  the no-self-praise tone revision, the "Football Data Platform" headline, the badge subset) were CPO-approved
  in-session and recorded in decisions_taken. Two advisory boundaries named and held: (a) the screenshot
  reference renders a broken-image placeholder until the CPO uploads docs/assets/screenshot.png — an accepted,
  documented manual step, not a merge-blocking defect; (b) the badges show 2 of the 5 CI categories the prose
  lists — an intentional "keep the funnel clean" presentation choice, with the prose remaining accurate.

## escalations
(none)
