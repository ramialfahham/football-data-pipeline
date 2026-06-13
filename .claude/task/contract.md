# Task contract — governance gate integrity (#409 F10/F11 + #421 F12)

> CPO gate-lift granted 2026-06-13 ("Do it") to edit the protected gate machinery, plus
> the reserved fix-mechanism picks: F10 = stop exempting contract.md; F11 = hash the
> branch-diff-excluding-artifacts (CI recomputes); F12 = demote the redundant global check.
> Touches PROTECTED paths (.claude/review_routing.json, .claude/hooks/git_discipline.py) +
> the CI backstop scripts/check_task_artifacts.py → protected_override below.
> See docs/working_agreement.md §2; memory governance_artifact_commit_ordering.md.

objective: >
  Close the three gate-integrity findings:
  - F10: a contract-only commit reaches main with zero review (the artifact_only lane
    exempts contract.md, which authorizes scope). FIX (CPO pick a): contract.md is NEVER
    artifact-exempt — any commit containing it requires the routed reviewers (scope-auditor).
    Implemented via a new `artifact_only_never` routing key honoured by both the local
    commit gate and the CI backstop.
  - F11: CI cannot bind review.md to the PR code (it can't recompute a staged hash). FIX
    (CPO pick a): the canonical review hash becomes sha256 of the diff EXCLUDING the
    bookkeeping artifacts (a new `hash_exclude_paths` routing key) — contract.md + code are
    hashed; review.md/patch/escalations/templates/active_work are not. The local gate hashes
    the STAGED such diff; the CI backstop recomputes `git diff <base>...HEAD` over the same
    exclusion and compares — so the review is now bound to the PR's code+contract.
  - F12 (#421): demote the redundant global count(ESCALATE)>count(ANSWER) in
    check_task_artifacts.py to a clearly-commented SECONDARY backstop; document that the
    per-section loop is authoritative.
  CONSEQUENCE of F11(a) (intended): contract.md + code must be final in the substantive
  (commit-1) diff; a later commit that changes contract.md or code alters the branch-diff
  hash and no longer matches review.md → CI fails. So no post-commit contract amendments;
  the contract must be complete before the reviewed commit.
refs: #409 (F10/F11), #421 (F12); memory governance_artifact_commit_ordering.

protected_override: >
  CPO gate-lift 2026-06-13 (conversation): "Do it" — explicit authorization to edit the
  protected gate machinery for the #409 + #421 gate-integrity bundle, with fix mechanisms
  F10=(a) stop exempting contract.md and F11=(a) hash branch-diff-excluding-artifacts
  (both chosen by the CPO via AskUserQuestion, 2026-06-13).

scope_paths:
  - .claude/review_routing.json
  - .claude/hooks/git_discipline.py
  - scripts/check_task_artifacts.py
  - tests/test_governance_hooks.py
  - docs/working_agreement.md
  - docs/agent_guardrails.md
  - .claude/task/contract.md
  - .claude/active_work.md

decisions_taken: >
  CPO gate-lift + fix-mechanism picks recorded above and in .claude/task/escalations.log
  (2026-06-13). One config-driven design: review_routing.json gains `artifact_only_never`
  (F10) and `hash_exclude_paths` (F11); both hooks + the CI check read them so the local
  gate and CI agree. The artifact_only glob (.claude/task/**) is unchanged except contract.md
  is carved out via artifact_only_never (review.md/patch/escalations/etc. stay exempt).

decisions_reserved:
  - Self-modification ordering: this PR edits the gate that gates its own commit. The commit
    is verified by the NEW logic (live hook). I will (1) update tests, (2) run the full hook
    suite, (3) manually verify the new --staged-hash + that the new gate accepts this commit,
    BEFORE committing. If self-verification fails, STOP and escalate rather than force.
  - Docs: working_agreement §2 commit-discipline + agent_guardrails get the new
    contract-finality rule. memory governance_artifact_commit_ordering updated separately.

done_when:
  - review_routing.json: artifact_only_never=[contract.md], hash_exclude_paths=[bookkeeping
    set], _doc updated. git_discipline.py: _artifact_only honours artifact_only_never;
    --staged-hash + _commit_gate hash over the hash_exclude exclusion. check_task_artifacts.py:
    artifact-only honours artifact_only_never; RECOMPUTES the branch-diff hash and compares;
    F12 global check demoted to a commented secondary backstop.
  - tests/test_governance_hooks.py: existing tests pass; NEW tests for (F10) contract.md not
    exempt, (F11) hash excludes bookkeeping / contract.md is bound.
  - validate-local Tier 1 green (pytest all-green incl the governance hook suite).
  - manual self-check: `python .claude/hooks/git_discipline.py --staged-hash` matches what
    review.md will carry; the gate accepts the staged commit.
  - reviewers: scope-auditor (always) + cto-reviewer (hooks/, scripts/, review_routing.json) — PASS.

amendments: (none)
