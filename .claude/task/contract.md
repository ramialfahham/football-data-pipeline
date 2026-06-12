# Task contract — G3: role reviewers, review routing, commit gate, CI backstop

objective: >
  Governance PR G3 (approved plan + CPO cast/spec rulings 2026-06-12): refresh
  the two stale role briefs, define the reviewer subagents (2 core + dormant
  cast), the CPO-approved review routing table, the 4-step review cycle with
  the SHA-256 commit gate in git_discipline.py, the artifact-only exemption,
  the CI backstop and PR template.
refs: governance plan (fuzzy-launching-meadow) G3; CPO rulings in-session
  2026-06-12 (cast 2+4+2+advisors; FAE+Legal narrow triggers; friction package
  all four; routing as committed protected file; DE samples rule +
  registry/onboarding routing)

scope_paths:
  - .claude/agents/scope-auditor.md
  - .claude/agents/analytics-engineer-reviewer.md
  - .claude/agents/cto-reviewer.md
  - .claude/agents/data-engineer-reviewer.md
  - .claude/agents/bi-analyst-reviewer.md
  - .claude/agents/football-analytics-expert-reviewer.md
  - .claude/review_routing.json
  - .claude/task/contract.md
  - .claude/task/REVIEW_TEMPLATE.md
  - .claude/hooks/git_discipline.py          # the commit gate
  - .claude/hooks/task_contract_gate.py      # + review_routing.json to PROTECTED_FILES
  - docs/roles/analytics_engineer.md         # pre-refactor staleness fix
  - docs/roles/bi_analyst.md                 # catalogue-location staleness fix
  - docs/working_agreement.md                # §2: the 4-step review cycle
  - docs/agent_guardrails.md                 # G3 hook/agent documentation
  - scripts/check_task_artifacts.py          # CI backstop
  - .github/workflows/ci-validate.yml        # wire the backstop
  - .github/pull_request_template.md         # governance block
  - tests/test_governance_hooks.py           # commit-gate test cases
  - .claude/skills/validate-local/SKILL.md   # amendment A1 — CI-mirror sync
  - .claude/active_work.md                   # handover (standing rule)

protected_override: >
  .claude/hooks/, .github/workflows/ and (once protected) .claude/
  review_routing.json are protected paths; edited here under the explicit CPO
  approval of governance plan G3 ("changes to the guards are their own
  CPO-approved task with the gate consciously lifted").

decisions_taken: >
  Cast: always-on scope-auditor (small model) + analytics-engineer-reviewer;
  dormant defined now: cto, data-engineer, bi-analyst,
  football-analytics (catalogue only); dormant defined LATER with their
  surfaces: ui-expert, data-journalist, legal-counsel (narrow — crest/logo/
  photo asset policy, per CPO "yes to both" narrow-trigger ruling); advisors
  not reviewers: CFO, Growth, Product Analyst. [Legal classification corrected
  by amendment A2.] Gemini amendments: scope-auditor judges the CUMULATIVE
  branch diff; AE treats seeds/dbt_project.yml as config-as-code; doc-sync
  judgment item; export cross-trigger (scripts/export_* -> AE + CTO).
  Friction: routing; artifact-only commits (.claude/task/** +
  .claude/active_work.md) exempt from review; model tiering (scope-auditor on
  haiku); one-substantive-commit rhythm. DE rules: parser/merge changes FAIL
  without sample-based tests (fixtures task gets its own contract when
  ingestion work resumes); registry/onboarding changes need ID evidence +
  explicit cost fields + verify-competition-ingest gate. Review artifact
  format machine-checkable; routing file JSON (stdlib-parseable, no yaml
  dependency). The dirty-tree check uses `git status --porcelain -uall`
  (amendment A3).

decisions_reserved:
  - Any additional deny class, reviewer, or routing row beyond the above (rule
    extension -> CPO). [Two such questions raised by the blinded reviews are
    ESCALATED in review.md: (1) protect .claude/agents/**, (2) confirm the
    commit -a/pathspec deny as enforcement of the approved review gate.]

done_when:
  - reviewer agent files + routing committed; briefs refreshed
  - commit gate: deny on missing review.md / hash mismatch / FAIL / unanswered
    ESCALATE / missing required-reviewer verdict / PASS without two risks;
    artifact-only commits pass without review; commit -a/--include/--only/
    pathspec forms denied (stage-then-plain-commit only); all covered in
    tests/test_governance_hooks.py, green
  - check_task_artifacts.py wired into ci-validate; PR template carries the
    governance block
  - G3's OWN commit passes through the full 4-step cycle (first live review)
  - validate-local tier-1 green; PR open

amendments:
  - A1 2026-06-12: + .claude/skills/validate-local/SKILL.md — authority: the
    skill's own standing rule ("If a CI workflow adds or changes a gate,
    update this list"), triggered by the new ci-validate gate; surfaced by
    scope-auditor finding 1 (doc-sync FAIL). Content: add the
    check_task_artifacts gate row to the CI-mirror table (+ the pre-existing
    missing check_competition_type_seed row, same table, declared here).
  - A2 2026-06-12: decisions_taken text corrected — Legal is a dormant FUTURE
    REVIEWER (narrow trigger: asset/crest policy), not an advisor. Authority:
    the CPO's recorded in-session ruling ("Narrow dormant triggers: FAE …
    Legal …? -> yes to both", 2026-06-12); surfaced by scope-auditor finding 2
    (contract text contradicted the committed docs; the docs match the
    ruling).
  - A3 2026-06-12: declare the `-uall` flag added to the dirty-tree check in
    task_contract_gate.py (untracked directories are collapsed by plain
    porcelain output and could not match per-file scope entries — fail-closed
    enumeration fix, found live during G3). Authority: within G3's
    protected_override scope; surfaced as undeclared by both reviewers (CTO
    finding 3); now declared and tested.
