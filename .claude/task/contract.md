# Task contract — G1: decision rights, blinded escalation, anti-patterns appendix

objective: >
  Governance PR G1 (approved plan, CPO 2026-06-11): codify the decision-rights
  table, the Blinded Escalation Protocol, and the Historical Anti-Patterns
  appendix in docs/working_agreement.md; add the CLAUDE.md pointer; add the
  compact decision-rights pointer to existing hook messages.
refs: governance plan (fuzzy-launching-meadow), PR sequence G1

scope_paths:
  - docs/working_agreement.md
  - CLAUDE.md
  - .claude/hooks/dbt_layer_gate.py        # message-text pointer only (G1 scope per plan)
  - .claude/task/contract.md

decisions_taken: >
  All content was specified and approved in the governance plan (CPO-approved
  2026-06-11, incl. two Gemini review rounds and the CPO's exact-text revision):
  CPO-only decision classes, the meta-rule, premise_check + two-conflicting-paths
  escalation format, the five anti-pattern entries (A1-A5).

decisions_reserved:
  - None known. Any wording question that changes MEANING (not phrasing) of a
    decision class escalates to the CPO.

done_when:
  - working_agreement.md carries the three new sections (decision rights,
    blinded escalation, Appendix A anti-patterns)
  - CLAUDE.md working-agreement section points to them
  - dbt_layer_gate.py messages reference the decision-rights section
  - python hook still passes its path-matrix self-test
  - validate-local tier-1 gates green; PR open

amendments: (none)
