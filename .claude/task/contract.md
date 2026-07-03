# Task contract — README portfolio polish (docs-only)

> Written on a CLEAN tree (branch docs/readme-portfolio-polish off main @ baef982).
> Supersedes the prior contract (Phase C brick 1 player YoY, MERGED #638). This is a NEW,
> CPO-assigned presentation task — not inferred from the handover. Docs-only; no dbt/SQL/Python.

objective: >
  Improve the repository's first impression as a portfolio / "business card" without overstating.
  Replace the top of README.md with a professional, to-the-point funnel: a platform headline, status
  badges, a clearly-labelled "Live preview" link to the MVP (with a note that the full v2 web app is in
  active development), a Mermaid architecture diagram, and a factual Highlights list. All EXISTING
  technical sections (BigQuery layout, dbt setup, DQ, layer contract, operations) stay unchanged below
  the new funnel. Add docs/assets/README.md documenting the screenshot / social-preview image spec.
  Tone: understated and factual (no self-praise); technical keywords carry SEO naturally.
refs: portfolio/visibility request 2026-07-03; live app = MVP preview, v2 in active development (site_architecture.md / epic #361)

scope_paths:
  - README.md
  - docs/assets/**
  - .claude/task/**

impact_map: >
  writers: README.md top section replaced (H1 + intro through just before "## BigQuery layout (datasets)");
    NEW docs/assets/README.md (guidance only). No code, no models, no scripts, no CI, no seeds touched.
  downstream: none — documentation only. No dbt graph, no export, no build behaviour changes.
  layer_rules: not applicable (no dbt models).
  deploy_order: not applicable — docs merge; GitHub renders the README + Mermaid on push.
  blast_radius: README.md presentation only. The referenced image docs/assets/screenshot.png is
    supplied by the CPO later; until then the README shows a broken-image placeholder on this branch
    (acceptable pre-merge; CPO adds the screenshot before/at merge). No numbers, no data, no behaviour.

decisions_taken: >
  Framing = option A (MVP link near the top, clearly labelled "Live preview", v2 noted as in active
  development). Tone corrected per CPO: dropped "Built solo, end to end" and any boast; factual only.
  Headline = "Football Data Platform". Badges = ci-validate, ci-data-build, MIT, dbt 1.7, BigQuery,
  Python 3.11. Architecture = Mermaid flowchart (API-Football -> BigQuery raw -> staging/base/core/
  intermediate/marts -> GitHub Pages). Screenshot left for the CPO to supply (a real app capture beats a
  placeholder); docs/assets/README.md records the spec + the social-preview reuse. Topics already set on
  the repo this session (14, via gh api) — outside the diff, no file change.

decisions_reserved:
  - The actual screenshot.png image and the GitHub social-preview upload are CPO manual steps (Settings UI).
  - Any further README restructuring of the existing lower sections is out of scope for this PR.
  - Future portfolio items (case study, dbt docs site, semantic-layer demo) are separate later work.

done_when:
  - README.md top funnel renders on GitHub (headline, badges, labelled MVP link, Mermaid diagram, Highlights);
    all existing sections below remain intact and unchanged.
  - docs/assets/README.md documents the screenshot / social-preview spec.
  - validate-local (offline gates) passes; no dbt/SQL/Python touched so the data gates are N/A.
  - scope-auditor PASS (docs-only, no scope creep beyond scope_paths); review.md binds; CPO merges.

amendments:
  - 2026-07-03: contract replaced (prior task Phase C brick 1 merged as #638). CPO assigned this docs-only
    portfolio task in-session and approved scope, framing (A), tone revision, and final copy ("Good to go").
