# Task contract — reviewer model pinning

> Governance economy change. Pins each reviewer subagent to an explicit model so
> the blinded review cycle runs cheaply, with top-tier scrutiny kept exactly where
> bypasses hurt most. See docs/working_agreement.md §2/§10/§11, Appendix A.

objective: >
  Pin each reviewer subagent to an explicit model so the blinded review cycle is
  economical: scope-auditor stays haiku; the five specialist reviewers are pinned
  to sonnet; a documented orchestrator rule spawns cto-reviewer on opus when the
  staged diff touches a guard path. G3 ran the specialists on the session's top
  model (Fable/Opus) every round — needless cost for contract-bound review work.
refs: governance program (C:\Users\Rami\.claude\plans\fuzzy-launching-meadow.md);
  CPO model-tiering ruling 2026-06-12 ("Sonnet + opus-on-guards"); G3
  decisions_taken already blessed "model tiering (scope-auditor on haiku)".

scope_paths:
  - .claude/agents/analytics-engineer-reviewer.md
  - .claude/agents/cto-reviewer.md
  - .claude/agents/data-engineer-reviewer.md
  - .claude/agents/bi-analyst-reviewer.md
  - .claude/agents/football-analytics-expert-reviewer.md
  - .claude/review_routing.json
  - docs/working_agreement.md
  - docs/agent_guardrails.md
  - .claude/active_work.md

protected_override: >
  .claude/agents/** is a PROTECTED path (CPO ruling, G3 escalation 2026-06-12).
  Edited here under the CPO's explicit model-tiering ruling in this session
  ("Sonnet + opus-on-guards", 2026-06-12) plus the standing G3 decisions_taken
  item "model tiering (scope-auditor on haiku)". scope-auditor.md is NOT touched
  (already pinned to haiku).

decisions_taken: >
  Tier map (CPO ruling 2026-06-12 "Sonnet + opus-on-guards"): scope-auditor =
  haiku (unchanged); analytics-engineer-reviewer, cto-reviewer,
  data-engineer-reviewer, bi-analyst-reviewer, football-analytics-expert-reviewer
  = sonnet, pinned via the `model:` frontmatter line. Documented orchestrator
  rule: when the staged diff touches a guard path (.claude/hooks/**,
  .claude/agents/**, .claude/settings.json, .claude/review_routing.json,
  .github/workflows/**), cto-reviewer is spawned with its model overridden to
  opus — guard bypasses are the highest-stakes findings (empirically, G3 review
  rounds 2-5). This is a PROCEDURAL rule (the orchestrator passes the model
  override to the Agent tool at spawn time), not hook-enforced — documented
  honestly as such. The model frontmatter is the floor; the orchestrator may
  override upward for a hard diff.

decisions_reserved:
  - RESOLVED by amendment A1 (below): the question "should `.claude/agents/**`
    be routed to cto-reviewer" was escalated blinded; CPO answered Path A (add
    the routing row) on 2026-06-12. Now implemented in scope, not reserved.

done_when:
  - each of the five specialist agent files carries `model: sonnet` in its
    frontmatter; scope-auditor.md still reads `model: haiku`
  - cto-reviewer.md body documents the opus-on-guards spawn rule
  - working_agreement.md §2 review-cycle block and the agent_guardrails.md reviewer
    subagent section document the tier map + the opus-on-guards rule
  - review cycle run: scope-auditor (haiku) + cto-reviewer (opus, guard diff)
    spawned cold; review.md written with a matching staged hash; the routing-row
    question escalated with a recorded CPO ANSWER
  - commit passes the gate; PR opened with the governance block

amendments:
  - 2026-06-12: + .claude/review_routing.json — authority: CPO blinded escalation
    answer (Path A, this session). The cto-reviewer ESCALATED that `.claude/agents/**`
    is named a guard path in the docs but is not routed to cto-reviewer, leaving
    reviewer-definition changes reviewed only by scope-auditor (haiku) with no
    gate/CI back-stop. CPO ruled "Add routing row (mechanical)". Content: add
    `.claude/agents/** -> cto-reviewer` to review_routing.json so agent-definition
    changes gate-require platform review; the opus-on-guards rule then overrides
    that cto review to opus.
  - 2026-06-12: + .claude/active_work.md — authority: standing handover practice
    (working_agreement.md §2 names .claude/active_work.md an artifact_only path;
    the handover is refreshed at task close). Content: update the handover status
    line (G3 merged #403; reviewer-pinning open #405; next = G4). Artifact-only,
    review-exempt.
