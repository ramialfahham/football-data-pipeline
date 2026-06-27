# Task contract — macro-usage engineering standard (when / when-not to use a dbt macro)

> Governance G2/G3 contract. Written on a clean tree BEFORE any edit.
> CPO-directed (2026-06-27): "we should establish a best practice when and when not to use macros."

objective: >
  Add a concise "Macros" standard to dbt_project/docs/engineering_standards.md codifying the CPO's
  stated rule — a macro that does not bring value is not used, because the price is lower
  maintainability (readability + debuggability). The standard states: default to plain SQL; a macro
  must give value that plain SQL or a model cannot; do NOT use a macro to hold a static list, to wrap
  a metric formula for DRY (use the COMPOSE pattern — compute once in an int_ model, marts select the
  result), or to scaffold for an unshipped policy; macros are justified for dbt framework hooks and
  genuinely cross-cutting transforms that can't be a model. Documentation only — no code/model change.

refs: >
  CPO request 2026-06-27 to establish the macro best-practice. Grounds the rule the team + player
  benchmark-list macro removals will follow. Builds on docs/feedback (macros decrease maintainability;
  prefer inline SQL + COMPOSE). This PR is the standard ONLY — the team benchmark de-macro is a separate
  follow-up PR; the player benchmark macro (encodes position eligibility, not just a list) and the
  unused-looking scaffolding macros (playoff-policy round names, etc.) are NOT touched here.

scope_paths:
  - dbt_project/docs/engineering_standards.md

decisions_taken: >
  Documentation only. Codifies the CPO's already-stated principle into the engineering standards as a
  new subsection (1.3 Macros), in the doc's existing terse/bulleted voice. No product, metric, naming,
  or mechanism decision; no model or macro is added/removed in this PR.

decisions_reserved:
  - Whether/how to remove the team benchmark-list macro (team_benchmark_metrics) — separate follow-up PR
    (number-sensitive; COMPOSE refactor).
  - The player benchmark macro (player_benchmark_metrics) — encodes position eligibility (CPO B3), so it
    is more than a list; its disposition is a separate, careful CPO-directed call.
  - The dormant scaffolding macros (bl1/bl2/l1 round names, union_all, domestic_league_codes_in_clause,
    team_name_key, apif_latest_source_partition) — tied to the playoff policy / layer contract / protected
    workflow / uncertain; deletion is a CPO call, not done here.

done_when:
  - engineering_standards.md carries a new "Macros" subsection stating the default-to-plain-SQL rule, the
    when-justified / when-not list (incl. static lists, formula DRY -> COMPOSE, no pre-ship scaffolding),
    and the one-line test ("does it give value plain SQL or a model can't?").
  - Required reviewers (scope-auditor, analytics-engineer-reviewer) PASS with >=2 named risks each;
    review.md diff_sha256 binds the staged diff; CI green. The CPO merges.

amendments: (none)
