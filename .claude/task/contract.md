# Task contract — the design gate reads the approved designs on main

objective: >
  The approved-design gate stops depending on a GitLab label and a CI token, which need manual
  steps from the CPO. Each page and issue a contract names in approved_design must stand in
  docs/wireframes/approved_designs.yml as that file is on main. The contract gate checks it before
  a page-surface edit, CI checks it on the MR, and the copy in the branch does not count.

refs: >
  #218, no page changes without an approved design
  (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/218). The plan: approved
  in chat, 2026-10-17.

scope_paths:
  - .claude/hooks/task_contract_gate.py
  - .claude/hooks/git_discipline.py
  - scripts/check_task_artifacts.py
  - tests/test_governance_hooks.py
  - .claude/task/TEMPLATE.md
  - docs/working_agreement.md
  - docs/agent_guardrails.md
  - docs/wireframes/00_overview.md
  - docs/wireframes/approved_designs.yml
  - tests/test_sentence_length_in_docs.py
  - tests/test_no_decision_history_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

protected_override: >
  .claude/hooks/task_contract_gate.py and .claude/hooks/git_discipline.py: approved in chat,
  2026-10-17, as the plan for the label-free design gate.

impact_map: >
  writers: none; no data, model or page changes.
  guard: task_contract_gate.py fires on every PreToolUse Edit/Write/MultiEdit and every PreToolUse
  Bash in this repo. Its page-surface deny (site_v2/src/**, scripts/export_site_data.py) gains one
  condition: each page and issue named in approved_design must stand in
  docs/wireframes/approved_designs.yml on gitlab/main (origin/main when no gitlab remote), read
  with git show. When the file cannot be read there, the edit is denied with the reason. The rest of
  the hook, and its fail-open rule on an unexpected error, are unchanged.
  check_task_artifacts.py runs in CI job validate:governance on every MR and push; design_errors
  drops the GitLab API label read and the DESIGN_GATE_TOKEN variable, and checks the same pairs
  against the file on the --base ref the job already passes (origin/main), failing closed. It
  imports the hook's parser and reader, so the two cannot drift.
  git_discipline.py loses its deny for a glab command that adds design::approved; its other
  denies are unchanged.
  downstream: a later contract on the page surface needs its page on main's list; a design MR adds
  the line and the CPO's merge approves it. Contracts off the page surface are unaffected.
  blast_radius: governance only; no published output changes.

approved_design:
  - none: no page output changes

decisions_taken: >
  Approved in chat, 2026-10-17: the plan. The list is docs/wireframes/approved_designs.yml, one line
  per page, page key and issue number, parsed by regex with no YAML dependency. It is read from the
  base ref only. The seed is competitions 128, competition 129, matches 130, match 132; Home stays
  out until its recheck closes. The label check, the token and the label block go. The
  working_agreement.md text is the exact text in the plan. THRESHOLD: a changed guard mechanism,
  approved in the plan; it removes a CI credential and adds no recurring cost.

decisions_reserved:
  - none: the plan fixed the list file, its seed, its page keys and the core-document text, and this task builds them unchanged.

done_when:
  - The full pytest suite passes.
  - The live hook denies a page-surface edit whose page is not on main's list.
  - grep for design::approved and DESIGN_GATE_TOKEN outside .claude/task/ finds nothing.
  - Reviewers cto-reviewer, platform-reviewer and scope-auditor pass.

amendments: (none)
