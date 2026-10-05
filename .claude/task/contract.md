# Task contract — the comment-history gate refuses issue numbers and story phrases

objective: >
  `.claude/hooks/comment_history_gate.py` also refuses, in code comments and Markdown documents, a
  new issue number and a new story phrase ("used to", "an earlier version", "caught in review",
  a review "round N"). Lines already in the tree are counted by the two pin tests; the counts only
  fall.

refs: >
  #199 (how-we-work documents carry no decision history). Handover step 2.

scope_paths:
  - .claude/hooks/comment_history_gate.py
  - tests/test_no_decision_history_in_code.py
  - tests/test_no_decision_history_in_docs.py
  - dbt_project/docs/engineering_standards.md
  - docs/agent_guardrails.md
  - docs/working_agreement.md
  - .claude/task/TEMPLATE.md
  - .claude/task/REVIEW_TEMPLATE.md
  - .gitlab/merge_request_templates/Default.md
  - .claude/agents/scope-auditor.md
  - .claude/agents/cto-reviewer.md
  - .claude/agents/data-engineer-reviewer.md
  - .claude/agents/football-analytics-expert-reviewer.md
  - .claude/agents/bi-analyst-reviewer.md
  - .claude/hooks/task_contract_gate.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - docs/tracker/**

protected_override: >
  Approved by the CPO in chat, 2026-10-05: the hook change, with the go for this MR; and an approval
  is named (where and when), never quoted, in the five reviewer briefs and the docstring of
  task_contract_gate.py, with the exact edits shown to him.

impact_map: >
  fires: PreToolUse on Edit|Write|MultiEdit|NotebookEdit (`.claude/settings.json`), every edit inside
  the repo; code files under its TREES and Markdown outside `.claude/task/`, `docs/tracker/`, `site/`.
  imported by: tests/test_no_decision_history_in_code.py and tests/test_no_decision_history_in_docs.py
  only (`git grep comment_history_gate`); nothing else reads it.
  stops being enforced if wrong: a pattern too narrow lets history in (the pins still count what it
  matches); a pattern too wide refuses ordinary edits. Measured over the tree before building: every
  issue-number hit read; known false positives excluded and pinned by tests (the hex token of a
  colour-taking CSS declaration such as "color: #111;", "rule/step/item/check #1", an HTML entity,
  ", used to" / "is used to" / "had used to", "the earlier version stays").
  on failure: fails open (any exception → allow), unchanged.
  baseline: code 784 flagged lines in 196 files (pin today 0); documents 704 lines in 46 (pin today
  383 in 41); measured with the new markers on the branch base. The code pin is 783 in 195: this
  branch rewords the one history line in tests/test_no_decision_history_in_code.py.
  blast radius: agent edits only; no pipeline, model, CI or site code changes.
  The five reviewer briefs are prompts: each FAIL condition on a missing quote becomes one on a
  missing named approval; read at spawn time, nothing imports them. task_contract_gate.py: one
  docstring line; no gate parses the approval's wording (`grep protected_override` in the hooks and
  scripts/check_task_artifacts.py: only presence is checked).

decisions_taken: >
  Readings, under the delegation of 2026-10-02:
  - Code comments, like documents, refuse only lines an edit ADDS. With hundreds of existing lines
    counted, refusing every re-included line would block ordinary edits, and the task is to refuse
    new history. For the markers already in force the tree holds zero lines, so nothing changes for
    them.
  - Issue numbers are refused in every document (today only in CLAUDE.md).
  - In documents a "round N" is a review round only when its line also says review, caught,
    flagged, FAIL, branch or opus: a football round stays allowed.
  - engineering_standards.md section 1.2: the clauses that describe the gate are corrected to it
    (the CLAUDE.md-only issue rule, the marker list).
  - docs/working_agreement.md section 11, the locked-file row: the CPO's approved text, approved in
    chat, 2026-10-05. Its other sentences that say "quoted" or "quoting" for an approval say
    "named" or "naming", as do the two task templates and the MR template.

  Threshold declarations. NEW MECHANISM: none (an existing hook gains patterns). RECURRING COST: none.

decisions_reserved:
  - docs/agent_guardrails.md is a core document: its row for this hook changes only with the CPO's
    approved text. Approved in chat, 2026-10-05: the row now in the file; engineering_standards.md
    then points to the hook's docstring.

done_when:
  - The two pin tests carry the measured baselines and pass; pytest (whole suite), ruff and the
    offline gates pass.
  - The review cycle passes (scope-auditor; cto-reviewer and platform-reviewer at opus;
    analytics-engineer-reviewer), review.md bound to --staged-hash; the MR pipeline is green.
