# Task contract — no page changes without an approved design

objective: >
  A task contract that touches the page surface (site_v2/src/**, scripts/export_site_data.py)
  names, for every page it changes, the GitLab issue where the CPO approved that page's design,
  or states in one line that no page output changes. The local contract gate refuses page-surface
  edits until it does; CI fails the MR when a named issue lacks the label design::approved;
  scope-auditor checks a "none" line against the diff.

refs: >
  #218, no page changes without an approved design
  (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/218). The plan: approved
  in chat, 2026-10-17.

scope_paths:
  - .claude/hooks/task_contract_gate.py
  - .claude/hooks/git_discipline.py
  - .claude/agents/scope-auditor.md
  - scripts/check_task_artifacts.py
  - tests/test_governance_hooks.py
  - .claude/task/TEMPLATE.md
  - docs/working_agreement.md
  - docs/agent_guardrails.md
  - tests/test_sentence_length_in_docs.py
  - tests/test_no_decision_history_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

protected_override: >
  .claude/hooks/task_contract_gate.py, .claude/hooks/git_discipline.py and
  .claude/agents/scope-auditor.md: approved in chat, 2026-10-17, as the plan for #218 and its
  amendment.

impact_map: >
  writers: none; no data, model or page changes.
  guard: task_contract_gate.py fires on every PreToolUse Edit/Write/MultiEdit and every PreToolUse
  Bash in this repo; the new rule adds one deny on the page surface (site_v2/src/**,
  scripts/export_site_data.py) when the contract's approved_design field is missing, empty, a
  placeholder or a bare "none", beside the existing impact_map deny. The hook fails open on an
  unexpected error, as today. check_task_artifacts.py runs in CI job validate:governance on every
  MR and push; it gains a parse of the same field and, for each named issue, a read of its labels
  from the GitLab API with the masked CI variable DESIGN_GATE_TOKEN, failing closed when a label is
  missing or the API cannot be reached. It imports the hook's parser, so the two cannot drift.
  scope-auditor gains one hunt item; its other items are unchanged.
  downstream: every later task contract that touches the page surface needs the field; contracts
  that do not are unaffected. Until the CPO sets the label and the variable, a page-surface MR
  fails validate:governance by design.
  blast_radius: governance only; no published output changes.

decisions_taken: >
  Approved in chat, 2026-10-17: the plan for #218. The page surface is site_v2/src/** and
  scripts/export_site_data.py; marts are out of scope, since a mart reaches a page only through the
  export. The label is design::approved, set only by the CPO. The CI token is a GitLab project
  access token with read_api scope, created by the CPO and held in the masked CI variable
  DESIGN_GATE_TOKEN, masked and not protected, because merge-request pipelines run on unprotected
  branches. THRESHOLD: a new guard mechanism and a new CI credential, both approved in the plan; no
  recurring cost. git_discipline.py denies a glab command that adds design::approved, beside the
  merge block; glab api has many spellings, so the block is best-effort and the label otherwise
  rests on the CPO being the only one who sets it. A "none" line is checked by scope-auditor alone,
  no machine, and agent_guardrails.md names it as the gate's weakest link (both approved in chat,
  2026-10-17).

decisions_reserved:
  - Which issues carry design::approved, and the competitions index's issue (#128 or #54): the CPO sets the labels.

done_when:
  - pytest tests/test_governance_hooks.py and the full suite pass.
  - The live hook denies a page-surface edit without the field and allows it with one.
  - Reviewers cto-reviewer, platform-reviewer and scope-auditor pass.

amendments: >
  2026-10-17: + .claude/hooks/git_discipline.py — authority: approved in chat, 2026-10-17, on the
  CTO reviewer's escalation; content: a deny for a glab command that adds design::approved.
