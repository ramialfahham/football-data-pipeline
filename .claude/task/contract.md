# Task contract — G4 retroactive alignment audit

> Governance program §5 (retroactive audit). Findings only — every disposition
> for a violation/unapproved-decision is a CPO ruling; findings become issues
> only after the CPO rules. Blinded reviewers generate findings per domain; the
> builder compiles and never re-judges its own past work.
> See docs/working_agreement.md §2 (contract), §10 (decision rights),
> §11 (blinded escalation), Appendix A (anti-patterns).

objective: >
  Produce docs/audits/2026-06_alignment_audit.md: a current-state alignment
  audit of the codebase against its locked contracts. Findings only — every
  disposition for a violation/unapproved-decision is a CPO ruling; findings
  become issues only after the CPO rules. Builder compiles; blinded reviewers
  generate the findings per domain.
refs: governance plan §5 (C:\Users\Rami\.claude\plans\fuzzy-launching-meadow.md);
  CPO kickoff rulings 2026-06-12.

scope_paths:
  - docs/audits/2026-06_alignment_audit.md
  - .claude/active_work.md   # artifact-only (handover write-out); see amendment A1

decisions_taken: >
  CPO kickoff rulings 2026-06-12 — DEPTH: current-state + per-finding provenance
  (no full commit-history walk). SURFACES: the plan's five passes (dbt models;
  scripts/export_*; seeds/macros; docs-vs-reality; metric values) PLUS ingestion
  code and CI workflows; the live MVP site is EXCLUDED (frozen/record-only).
  FINDING SOURCE: each blinded domain reviewer runs its pass independently and
  emits findings; the builder aggregates them verbatim into the table and never
  re-judges its own past work. ROUTING: dbt -> analytics-engineer-reviewer;
  scripts/tooling/seeds/macros/CI -> cto-reviewer; ingestion -> data-engineer-
  reviewer; decisions/provenance/doc-faithfulness -> scope-auditor.

decisions_reserved:
  - Every finding's disposition (violation / unapproved-decision) is a CPO
    ruling — the audit proposes, never decides; escalate blinded (§11).
  - Any finding implying a change to shipped numbers (GAP-17 frozen) — reserved.
  - The two parked slug rulings, if a finding surfaces them — reserved for the Pilot.

done_when:
  - 7 passes run via the four blinded reviewers (cold, read-only); findings table
    populated: columns = class | evidence (file:line / commit) | proposed
    disposition | CPO ruling (blank until ruled).
  - scope-auditor faithfulness pass = PASS (doc aggregates the reviewer findings;
    no finding silently resolved as a CPO-class decision).
  - review.md written with a staged-diff hash matching the doc; commit gate passes.
  - PR opened with the governance block.

amendments:
  - 2026-06-12: + .claude/active_work.md — authority: standing handover practice
    (working_agreement.md §2 names .claude/active_work.md an artifact_only path;
    the handover is refreshed at task close). Content: update the handover status
    to "G4 audit shipped" + next actions. Artifact-only, review-exempt. NOTE: this
    amendment is itself an instance of finding F10 (contract scope widened via the
    review-exempt artifact lane) — done here under the sanctioned clean-tree +
    recorded-authority mechanism, surfaced honestly in the audit it accompanies.
# On amendment (clean tree only):
#   - <date>: + <path> — authority: <CPO answer / standing rule>; content: <what>
