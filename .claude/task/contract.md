# Task contract — sharpen the built-page reviewer (#827)

> Written on a CLEAN tree, branch `fix/827-sharpen-bi-analyst-reviewer` off `main` (`385fda8`).
> See docs/working_agreement.md §2 (contract), §10 (decision rights), §11 (blinded escalation).

objective: >
  Upgrade `.claude/agents/bi-analyst-reviewer.md` per issue #827: default-FAIL and PASS-needs-
  two-verified-risks are already true today; the actual gap is that the reviewer judges the CODE
  diff and never sees the RENDERED page. This session's own foundation-shell PR (#829) proves the
  gap: bi-analyst-reviewer PASSED a diff that contained a real rendering bug (a CSS specificity
  bug meant the >=1010px search-icon button never actually hid), caught only by the builder
  actually building the site and checking computed styles — not by review. Adds a rendered-page-
  evidence requirement so the reviewer has real, auditable rendering evidence to judge, not just
  source code.

refs: >
  Issue #827 (CPO-authored, 2026-07-26): "Upgrade the bi-analyst-reviewer rubric for BUILT
  frontend pages: default verdict FAIL; a PASS requires naming at least two concrete verified
  risks; review the RENDERED page (screenshot / accessibility tree / mobile layout), not the
  code. Small guard-path change (.claude/agents/), independent of the foundation build, so it can
  be done early." CPO chat instruction this session, 2026-07-26: "NOW, Phase B ... #827 ... Do
  this one first." The concrete gap example: PR #829's `.search-m` specificity bug (fixed in that
  PR, but never caught by bi-analyst-reviewer's own pass on that diff).

scope_paths:
  - .claude/agents/bi-analyst-reviewer.md

protected_override: >
  `.claude/agents/` is protected (working_agreement.md §2). Authority: CPO-authored issue #827
  (quoted above, "Upgrade the bi-analyst-reviewer rubric...") plus this session's explicit chat
  instruction to do #827 first, both 2026-07-26.

impact_map: >
  Protected-path form (trace dependents, not table lineage — no dbt/warehouse surface here).
  Fires: bi-analyst-reviewer is spawned cold in step 2 (Blinding) of the review cycle whenever a
  staged diff matches its routed paths in `.claude/review_routing.json`
  (`docs/wireframes/**`, `site/i18n/**`, `site_v2/src/**` — unchanged by this PR, routing itself
  is not touched). Depends on it: the commit gate (`git_discipline.py`) requires its verdict
  section in `review.md` for any diff touching those paths; no verdict or a FAIL denies the
  commit. What stops being enforced if wrong: if the sharpened rubric is too weak, rendering
  defects in built frontend pages keep passing review undetected — the exact gap #829 exposed. If
  too strict (e.g. treating a missing screenshot as automatic FAIL): could block every future
  site_v2 PR in this environment, where the Browser pane's screenshot tool is confirmed broken
  (verified this session) — mitigated by requiring the evidence file to STATE which of
  {screenshot, accessibility tree, mobile layout} were captured, not mandate one specific method.
  Failure mode: malformed reviewer output still fails the commit gate closed (deny) — existing,
  correct behavior for a review gate, unchanged by this PR.

decisions_taken: >
  Scope is exactly issue #827's own stated scope: a small guard-path change to
  `.claude/agents/bi-analyst-reviewer.md` only. No new tool grant to the reviewer (stays
  Read/Grep/Glob, read-only, consistent with every other reviewer) — the rendering evidence is a
  file the reviewer reads via its EXISTING Read tool, the same way it already reads
  `review_input.patch`/`contract.md`. No change to `.claude/review_routing.json` (also protected,
  out of this issue's scope) and no change to any other agent definition. Confirmed (checked, not
  assumed) that `docs/agent_guardrails.md` and `docs/roles/bi_analyst.md` need no matching edit —
  neither describes the review METHOD in a way this change contradicts.

decisions_reserved:
  - None for this narrow change. The rendered-page-evidence FORMAT (exact structure of
    `.claude/task/rendered_page_evidence.md`) is specified loosely by design (state what was
    captured and why) rather than machine-schema'd — if a future PR finds that too loose, that is
    a CPO call, not decided here.

done_when:
  - `.claude/agents/bi-analyst-reviewer.md` YAML frontmatter still parses; structure matches the
    other five reviewer definitions.
  - Diff read back: default-FAIL wording intact, PASS-needs-two-risks intact, new
    rendered-page-evidence Inputs entry present and specific, hunt item added, PASS rule
    tightened (>=1 of the two risks must come from evidence when a site_v2/src/** rendering
    change is in scope).
  - Review cycle: scope-auditor (always) + cto-reviewer, model overridden to opus (this diff
    touches `.claude/agents/**` — the guard-path rule, working_agreement.md §2). bi-analyst-
    reviewer is NOT self-routed (this diff touches none of its own routed paths).
  - ONE commit; review.md hash-locked; pushed with an explicit refspec; PR opened referencing
    #827. CPO merges; I close #827 myself once merged confirmed via `gh`.

amendments: (none)
