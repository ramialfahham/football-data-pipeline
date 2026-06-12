# Review — governance/reviewer-model-pinning — 2026-06-12

> Step 4 (Lock). Two iterations: iteration 1 returned scope-auditor PASS +
> cto-reviewer ESCALATE (agents/** named a guard path but not routed to
> cto-reviewer — no gate/CI back-stop for reviewer-definition changes). The CPO
> ruled Path A (add the routing row); the diff now routes `.claude/agents/**` ->
> cto-reviewer (contract amendment A1). Iteration 2 (this artifact): both
> reviewers PASS on the fixed diff. cto-reviewer ran on opus both iterations
> (guard diff — opus-on-guards).

diff_sha256: 78a540739141502c5f0642cdb4d3cef484db887c6ea2808d385c5f006b3147ba

## scope-auditor
VERDICT: PASS
risks_checked:
- Protected-path enforcement and CPO authority: the contract carries
  protected_override naming the G3 escalation authority (2026-06-12); amendment
  A1 records the CPO Path A ruling for the `.claude/agents/**` routing row;
  scope-auditor.md is deliberately excluded (already pinned to haiku in G3). All
  eight staged files are within scope_paths.
- Doc-sync across four locations: working_agreement.md §2, agent_guardrails.md,
  cto-reviewer.md and the routing _doc all name the same five guard paths and
  describe the opus-on-guards override identically as procedural (not
  hook-enforced); the routing `paths` block now contains all five guard paths.

## cto-reviewer
VERDICT: PASS
risks_checked:
- fnmatch semantics of the new row: `_required_reviewers` (git_discipline.py)
  uses Python `fnmatch`, where `*`/`**` both match `/`, so `.claude/agents/**`
  matches `.claude/agents/cto-reviewer.md` — cto-reviewer is now a REQUIRED
  reviewer for any agents/** diff at both the commit gate and the CI backstop;
  staged paths are forward-slash normalized so it fires on Windows too. Same
  proven mechanism as the existing `.claude/hooks/**` row.
- review_routing.json structural integrity: the four new `_doc` strings are
  appended inside the existing array; `.claude/agents/**` adds no duplicate key;
  file is valid JSON so `_load_routing` does not fall to its fail-open path.
- Documented↔mechanical inconsistency closed: no guard path named in the docs is
  missing from the routing → cto-reviewer set (the iteration-1 gap is gone).
- Protected-path authority quoted, not asserted (contract protected_override +
  amendment A1); scope-auditor unchanged at `model: haiku`; the opus-on-guards
  override is honestly documented as procedural; the gate's fail-closed direction
  is tightened, not inverted.

## escalations
- question: `.claude/agents/**` is a PROTECTED guard path named in the
  opus-on-guards docs, but it was not routed to cto-reviewer — so a change to a
  reviewer definition was reviewed only by the always-on scope-auditor (haiku),
  with no commit-gate or CI back-stop (unlike the other guard paths, which the
  routing table back-stops). Add the routing row (mechanical enforcement) or keep
  it procedural and qualify the docs?
  CPO ANSWER: Add the routing row (mechanical) — blinded escalation 2026-06-12.
  Implemented: `.claude/agents/** -> cto-reviewer` added to review_routing.json
  (contract amendment A1); iteration-2 reviewers verified the fix.
