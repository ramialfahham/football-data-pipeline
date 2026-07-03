# Task contract — README "Design decisions" section (docs-only)

> Written on a CLEAN tree (branch docs/readme-design-decisions off main @ 5c4ad28).
> Portfolio work: add the reasoning/judgment narrative an external reader wants, WITHOUT a new
> document (CPO rejected a standalone design_notes.md as doc-clutter / drift surface; the facts already
> live in north_star / layering / CLAUDE / the registry). Docs-only; no dbt/SQL/Python.

objective: >
  Add a tight "## Design decisions" section to README.md, immediately after "## Highlights" and before
  "## BigQuery layout (datasets)". Five rationale-level bullets (unified raw + league_code / strict layer
  contract / DQ as a build gate / metrics defined once / identity-vs-affiliation) that explain the WHY and
  the trade-offs — the one thing written nowhere else. Every FACT links out to its authoritative source
  (competition_registry.yml, check_layer_contract.py, layering.md, engineering_standards.md); the section
  restates no inventory (no counts, no competition lists), so it does not drift.
refs: portfolio/visibility request 2026-07-03; anti-clutter ruling (fold into README, no 4th doc); complements north_star (internal) vs README (external)

scope_paths:
  - README.md
  - .claude/task/**

impact_map: >
  writers: README.md gains one new "## Design decisions" section (text only) between the existing
    "## Highlights" and "## BigQuery layout (datasets)" sections. No other README content altered. No code,
    models, scripts, CI, seeds, or other docs touched.
  downstream: none — documentation only. No dbt graph, export, or build behaviour change.
  layer_rules: not applicable (no dbt models).
  deploy_order: not applicable — docs merge; GitHub renders the new section on push.
  blast_radius: README.md presentation only; five outbound links to existing in-repo paths. No numbers,
    data, or behaviour. Staleness is mitigated by design: rationale altitude + links-not-copies (no
    inventory to drift), per the CPO's "facts live in one place and get linked" rule.

decisions_taken: >
  Fold the reasoning narrative into README (NOT a standalone doc) — CPO ruling this session: a 4th document
  restating architecture facts is exactly the drift/clutter risk (#505). north_star stays the INTERNAL
  compass (vision/business model/roles/roadmap + terse tech rules); README stays the EXTERNAL face and now
  carries the curated WHY. Voice = neutral, factual, honest that this is a personal project whose central
  constraint is sideways scale (no self-praise, per the tone ruling on #640). Five decisions chosen for
  judgment signal; each links to the authoritative source rather than copying facts. Exact copy pre-approved
  by the CPO in-session ("go").

decisions_reserved:
  - No formal "architecture PRs must review this section" governance rule added — staleness is handled by
    altitude + links; a process rule would be over-engineering for a README section (can revisit if it drifts).
  - Future portfolio items (dbt docs site, semantic-layer demo) remain separate later work.

done_when:
  - README.md carries the "## Design decisions" section in the right place; existing sections intact; the
    five outbound links resolve to existing repo paths.
  - No inventory/counts in the new section (drift-resistant by construction).
  - scope-auditor PASS (docs-only, links resolve, no scope creep); review.md binds; CPO merges.

amendments:
  - 2026-07-03: fresh contract (prior task add-MVP-screenshot merged as #641). CPO chose option A (fold the
    reasoning into the README, no standalone doc) and approved the exact copy in-session ("go").
