# Task contract — trim the §1.3 macro standard to a calibrated default (not a rulebook)

> Governance G2/G3 contract. Written on a clean tree BEFORE any edit.
> CPO-directed (2026-06-27): the §1.3 macro standard (merged #592) over-reached by dressing judgment as a
> rule/test. CPO chose option 1 — trim it to the kernel and frame it honestly as a default, not a rulebook.

objective: >
  Rewrite engineering_standards.md §1.3 (Macros) to the kernel the CPO judged useful: open by stating it is
  a calibrated DEFAULT, not a rulebook (this project's habit was over-reaching for macros); default to plain
  SQL; the common trap (a shared list/formula in a macro) -> build it once as a model the others read or
  aggregate (COMPOSE, §5); where a macro genuinely earns it (the two verified examples — override hook,
  expression that must sit inside other queries); then close: beyond that there is no formula, an experienced
  analytics engineer judges. REMOVE the filler "test" line (judgment dressed as a rule) and the tangential
  "don't scaffold ahead of need" bullet. Documentation only — no code/model change.

refs: >
  CPO call 2026-06-27 ("1." = trim it). Revises §1.3 from #592. Keeps the parts that PASSED review there
  (the COMPOSE framing, generate_schema_name + JSON-expansion examples) and drops the over-reaching "test"
  line. No new mechanism; codifies the CPO's own framing that this is judgment, not rules.

scope_paths:
  - dbt_project/docs/engineering_standards.md

decisions_taken: >
  Documentation only. Reframes §1.3 as a calibrated default + the COMPOSE trap + when a macro genuinely
  earns it + an explicit "this is judgment, not a decision procedure" close. No product/metric/naming/
  mechanism decision; no model or macro change.

decisions_reserved:
  - Whether to keep a macro standard at all is the CPO's; this PR implements the chosen option (trim, not drop).

done_when:
  - §1.3 opens by framing itself as a default not a rulebook, keeps the plain-SQL default + the COMPOSE
    alternative + the two verified justified examples, drops the "test" line, and closes that beyond those
    cases it is the engineer's judgment.
  - Required reviewers (scope-auditor, analytics-engineer-reviewer) PASS with >=2 risks each; review.md
    diff_sha256 binds the staged diff; CI green. The CPO merges.

amendments: (none)
