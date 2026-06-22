# Task contract — Impact-map gate (diagnosis drift, #518)

objective: >
  Make end-to-end diagnosis a precondition of structural change, so the spot-fix /
  diagnosis-drift pattern (#518) stops recurring. Introduce a mandatory, EVIDENCED
  "impact map" in the task contract for any change on the structural surface
  (ingestion/**, dbt_project/models/**, scripts/export_*.py, site*/): every writer
  of the table/model, the downstream lineage to marts/consumption (pasted from
  `dbt ls --select <model>+` or the dbt MCP — evidence, not assertion), the
  CI-enforced layer rules, the shared-warehouse deploy ordering, and the blast
  radius. The contract gate denies a structural edit until the map is present;
  the routed reviewers judge its honesty. Plus: sharpen three reviewer specs to
  hunt the map (and coverage-cut "fixes") and name the anti-pattern (Appendix A6).
  (The bundled merge-on-write/read-all layering.md codification was DE-SCOPED to
  issue #539 after review — see amendments.)

refs: >
  Issue #518 (process retrospective; 3 logged instances #514/#527/#536). CPO §10
  design sign-off in this conversation 2026-06-22 ("OK. Execute."). The design and
  its alternatives were escalated and approved this session. Memory:
  feedback-no-hacky-solutions (mode 5 = end-to-end-map-first).

scope_paths:
  - .claude/task/**
  - .claude/hooks/task_contract_gate.py
  - .claude/agents/scope-auditor.md
  - .claude/agents/data-engineer-reviewer.md
  - .claude/agents/analytics-engineer-reviewer.md
  - tests/test_governance_hooks.py
  - docs/working_agreement.md
  - docs/agent_guardrails.md

protected_override: >
  CPO §10 sign-off 2026-06-22 (this conversation): the impact-map gate is a NEW
  governance mechanism; building it edits the gate hook (.claude/hooks/) and three
  reviewer specs (.claude/agents/), both PROTECTED. The CPO approved the design and
  said "Execute." Routes to cto-reviewer (guard paths) at the opus floor.

decisions_taken: >
  CPO-approved design (this conversation): (1) the impact-map is a presence-gated,
  reviewer-judged section of contract.md — the gate checks PRESENCE, the reviewer
  checks HONESTY (same split as scope_paths). (2) Teeth = "evidence, not assertion":
  the map must paste the lineage output + the RAW/leaf evidence, mirroring the
  existing provider-ID evidence rule. (3) Breadth = the WHOLE structural surface
  (ingestion/** + all dbt_project/models/** + scripts/export_*.py + site*/), not
  just raw/staging — the pattern is general; trivial/leaf/cosmetic changes use a
  one-line evidenced short-form. (4) Enforcement POINT = the edit boundary: the gate
  denies the FIRST structural Edit/Write until the contract carries a non-placeholder
  impact_map (so no structural code exists without the map). This is the robust
  implementation of the approved "contract chokepoint" direction — the PreToolUse
  event cannot reliably read pre-write contract content, so the check reads the
  on-disk contract when a structural file is about to be edited. (5) DEFERRED on
  purpose (not built): the active diagnose-data-issue skill / trace-subagent — add
  only if the evidenced contract + sharpened reviewers prove insufficient (avoid the
  over-build pattern). (6) The bundled merge-on-write/read-all layering.md
  codification was DE-SCOPED to #539 mid-review: the reviewer correctly showed
  RAW_APIF_FIXTURE_DETAILS (delete-on-retry-only, accumulate + base-dedup) is NOT the
  same write-class as RAW_APIF_PLAYERS (per-key upsert), so an accurate codification
  needs its own focused task. CPO directed the follow-up split this session.

decisions_reserved:
  - none. The design (mechanism, teeth, breadth, enforcement point, the deferred
    skill) was settled at §10 sign-off this session. If a reviewer surfaces a
    genuinely new CPO-class question (e.g. the consumption breadth is too wide for
    pure-UI edits), escalate it blinded — do not decide it here.

# Known v1 limits (documented, not defects): the impact-map check fires on the
# Edit/Write authoring path only, not on shell write-operators (those are already
# scope/heredoc-gated); it checks PRESENCE not correctness (honesty is the
# reviewer's job); it cannot govern a diagnosis floated in pure chat before any
# contract exists — it catches it at the latest safe point (before code).

impact_map: >
  Not applicable — no path in scope_paths is on the structural surface. This task
  edits the gate hook, reviewer specs, governance docs (docs/**), and the hook test.
  `_is_structural` matches ingestion/** + dbt_project/models/** + scripts/export_*.py
  + site*/ — none of which this task touches; verified the new gate does not require
  a map for this task's own files.

done_when:
  - task_contract_gate.py: a structural Edit/Write (e.g. dbt_project/models/x.sql,
    ingestion/y.py) is DENIED when the contract has no non-placeholder impact_map,
    ALLOWED when it has one; a non-structural edit (docs/**) is allowed without one.
  - TEMPLATE.md carries the impact_map section + the short-form guidance.
  - The three reviewer specs hunt the impact-map + coverage-cut; working_agreement
    §2 documents the requirement and Appendix A6 names the anti-pattern;
    agent_guardrails.md line for task_contract_gate reflects the new deny.
  - tests/test_governance_hooks.py adds present/absent/non-structural cases; the
    full governance test module passes (`python -m pytest tests/test_governance_hooks.py`).
  - validate-local gates pass (sqlfluff/layer-contract/registry-sync unaffected);
    the routed reviewers PASS (scope-auditor + cto-reviewer; analytics-engineer is
    no longer required after the layering.md de-scope — no dbt_project/** in the diff).
  - Tree matches scope_paths.

amendments:
  - 2026-06-22: REMOVED dbt_project/docs/layering.md from scope (objective + done_when
    trimmed). Authority: CPO directive this session ("fix in follow-up issue") after the
    analytics-engineer reviewer FAILed the bundled merge-on-write codification twice for
    a real accuracy issue (RAW_APIF_FIXTURE_DETAILS delete is retry-only → accumulate +
    base-dedup, NOT per-key upsert like RAW_APIF_PLAYERS). Tracked accurately as #539.
    The #518 gate mechanism is unaffected and stands on its own.
