# Task contract — cut the review friction: delta re-review, a round cap, consult before building

> Written on a CLEAN tree (branch `chore/review-economics` off main @ ddbb911).

protected_override: >
  `.claude/hooks/**` and `.claude/agents/**` are PROTECTED: changing the commit gate or what a
  reviewer is told to do is a governance event. CPO-directed 2026-07-22 after #806 merged, in his
  words: *"the process has a lot of friction now. it has to be more economic. otherwise we will not
  build the website in time."* The shape was then chosen discretely (AskUserQuestion): **"Delta
  re-review, round cap, consult first"**, over a mechanical-only option, a full recast, and doing
  nothing. Routes to cto-reviewer; the opus-on-guards rule applies.

objective: >
  THE COST, measured on this session rather than asserted. #805 took 4 review rounds, #806 took 4,
  and the guardrails PR before them took 9. Of the 8 rounds across the two PRs today: 3 were purely
  "the CPO never approved this", 2 were football facts a domain reviewer knew before a line was
  written, 2 were the builder weakening a test so his own change would pass, 1 was a partial sweep.

  That is two separate problems and this change attacks both.

  (1) ROUND COST. Every round re-ran every required reviewer over the ENTIRE branch diff, even when
  one file had changed. Late in #806 the reviewers were scoped by hand to just the delta; they came
  back far faster and still caught a real defect. That was the builder improvising, not the system.
  Fix: a DELTA RE-REVIEW brief is a first-class thing every reviewer understands, legitimate only
  after that same reviewer has already passed an earlier hash of the same branch, with an explicit
  escape hatch when the delta is too large for the earlier pass to still stand.

  (2) ROUND COUNT. Nothing bounded the loop, and nothing made the builder gather knowledge before
  writing code. Fix: `review.md` declares its round count and the commit gate caps it at 3, after
  which the open findings go to the CPO instead of round 4; and a contract on the structural surface
  must record who was consulted BEFORE the build, or state plainly that nobody was and why.

refs: >
  Verified this session, not recalled:
  - The commit gate already parses `review.md` for `diff_sha256`, FAIL, ESCALATE/CPO ANSWER pairing
    and the two-risk quota (`.claude/hooks/git_discipline.py:199-244`), so the round check is one
    more read of the same file, not a new mechanism.
  - The contract gate already computes `_is_structural(rel)` and demands `impact_map` on exactly
    that surface (`.claude/hooks/task_contract_gate.py:188-196, 363-389, 442-443`). `consulted:`
    reuses that same trigger, so no new surface definition is invented.
  - The review artifact's required fields are described in 14 files. The LIVE ones, enumerated by
    grep rather than memory: `REVIEW_TEMPLATE.md`, `git_discipline.py`, `check_task_artifacts.py`,
    `docs/agent_guardrails.md`, `review_routing.json`'s `_doc`, `tests/test_governance_hooks.py`,
    and the six agent briefs. `docs/audits/2026-06_alignment_audit.md` is a historical record and is
    deliberately NOT edited.

scope_paths:
  - .claude/hooks/git_discipline.py
  - .claude/hooks/task_contract_gate.py
  - .claude/agents/scope-auditor.md
  - .claude/agents/cto-reviewer.md
  - .claude/agents/analytics-engineer-reviewer.md
  - .claude/agents/bi-analyst-reviewer.md
  - .claude/agents/data-engineer-reviewer.md
  - .claude/agents/football-analytics-expert-reviewer.md
  - .claude/task/REVIEW_TEMPLATE.md
  - .claude/task/TEMPLATE.md
  - scripts/check_task_artifacts.py
  - docs/working_agreement.md
  - docs/agent_guardrails.md
  - tests/test_governance_hooks.py
  - .claude/active_work.md
  - .claude/task/escalations.log

consulted: >
  NOBODY, and that is the right answer here rather than an omission. The expertise this change needs
  is platform and governance, which is the cto-reviewer's own territory, so consulting it before the
  build and then having it review the build is the same agent twice. There is no football, display
  or ingestion surface in scope. Stated explicitly because from this commit on, a structural
  contract that leaves this blank is denied.

impact_map: >
  writers: none. No data, no model, no table, no warehouse object.
  downstream: dbt lineage is not applicable — nothing dbt touches is in scope. The real blast radius
    is EVERY FUTURE TASK, which is why a protected path demands this trace. Enumerated by grep over
    the repo, models AND tests AND scripts:
      `.claude/hooks/git_discipline.py` is the PreToolUse commit gate. Adding a `rounds:` requirement
        means EVERY future substantive commit is denied until `review.md` carries that line. That is
        the point, and it lands on the very next task.
      `.claude/hooks/task_contract_gate.py` gates the first edit to a structural path. Adding
        `consulted:` means every future structural contract is denied until it carries that field.
      `scripts/check_task_artifacts.py` is the CI backstop applying the same rules; it must learn
        both fields or CI and the local gate disagree, which is the failure mode where a commit
        passes locally and bounces in CI.
      The six agent briefs are read by the reviewers themselves; the delta rule has no other home.
      `tests/test_governance_hooks.py` is the only thing that proves any of it works, since these
        hooks cannot be exercised by dbt or by the site build.
  layer_rules: none apply. No dbt model, no SQL, no seed.
  deploy_order: none. No warehouse object. Takes effect on the next commit after merge.
  blast_radius: bounded and deliberate, in BOTH directions. The intended effect is fewer and cheaper
    review rounds. The risk in the other direction is that a new required field is one more thing to
    fill in on every task, which is friction added by a change whose purpose is removing it —
    mitigated by scoping `consulted:` to the structural surface only (reusing `_is_structural`, so
    a docs-only or bookkeeping task never sees it) and by allowing an explicit "nobody, because ..."
    as this very contract does. The `rounds:` field is one line. Second risk: a DELTA RE-REVIEW
    brief could become a way to smuggle a change past a reviewer that already passed. Mitigated in
    the brief itself — a delta review is legitimate only after that reviewer's own PASS on an
    earlier hash of the SAME branch, and every brief instructs the reviewer to refuse and demand a
    full review when the delta is large enough that its earlier pass no longer stands.

decisions_taken: >
  (1) DO THIS BEFORE THE TEAM PAGE. CPO 2026-07-22: the process "has to be more economic. otherwise
      we will not build the website in time." The team page is three tabs with a display reviewer
      newly routed at it, so it is the change most likely to loop; fixing the loop first is cheaper
      than paying it there.
  (2) THE SHAPE. CPO (AskUserQuestion, 2026-07-22): "Delta re-review, round cap, consult first",
      chosen over mechanical-only, a full recast of the roles, and doing nothing.
  (3) The round cap is THREE, taken from the option text the CPO approved ("Rounds are capped at
      three, after which I stop and bring you the open findings instead of looping").
  (4) Engineering calls, not §10: `consulted:` reuses `_is_structural` rather than defining a new
      surface; the cap denies at the gate rather than warning, because a warning is what the current
      unbounded loop already effectively is.

decisions_reserved:
  - The rest of the owed guardrail-economics item is NOT done here and is not decided away: putting
    the reviewer model in the routing file instead of the builder's head, and recasting the roles so
    reviewers are peers rather than one reviewer reading every diff. The CPO chose the smaller
    option over that recast; it stays owed.
  - Whether consultants (`football-analytics-expert`, `data-journalist`, a fan probe) become real
    pre-build agents. This change only records THAT a consult happened; it does not create the
    consultant roster, which is part of the deferred agent set.

done_when:
  - `review.md` without a `rounds:` line is denied by the commit gate, and `rounds: 4` or higher is
    denied unless a CPO answer is recorded. Both proved by tests that drive the real hook.
  - A structural-path edit whose contract has no `consulted:` is denied by the contract gate, and a
    placeholder does not satisfy it. Proved by tests that drive the real hook.
  - A non-structural edit is NOT asked for `consulted:` — the cry-wolf direction, also tested.
  - `scripts/check_task_artifacts.py` enforces the same two rules, so CI and the local gate cannot
    disagree.
  - All six agent briefs carry the same delta-re-review section, including the refusal clause.
  - Every live description of the review artifact's required fields agrees, swept from the grep
    enumeration in `refs` rather than from memory.
  - The full governance suite passes.
  - ONE commit, pushed with an explicit refspec, PR opened. The CPO merges.

amendments: (none)
