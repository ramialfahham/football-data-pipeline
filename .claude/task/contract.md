# Task contract — the design checks become protected paths

objective: >
  The three design-check scripts and the test that refuses a rising pin become protected paths,
  so an edit that weakens a check needs a CPO-approved governance task and the CTO's review. The
  protected-path list, the routing rows and every document that states them change together.

refs: >
  #243, the component-system plan, approved in chat, 2026-11-02 (step 1, its governance part).

scope_paths:
  - .claude/hooks/task_contract_gate.py
  - .claude/review_routing.json
  - .claude/agents/cto-reviewer.md
  - .claude/agents/platform-reviewer.md
  - .claude/task/TEMPLATE.md
  - docs/working_agreement.md
  - docs/roles/platform_reliability.md
  - docs/north_star.md
  - tests/test_governance_doc_parity.py
  - tests/test_governance_hooks.py
  - tests/test_sentence_length_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

protected_override: >
  Approved in chat, 2026-11-02: the CPO approved this governance task's plan, which makes
  scripts/check_design_inventory.py, scripts/check_page_css.py, scripts/design_inventory.py and
  tests/test_design_inventory.py protected paths, routed to cto-reviewer and platform-reviewer.

impact_map: >
  fires_on: task_contract_gate.py runs on every Edit/Write/Bash PreToolUse event; `_is_protected`
  is its only protected-path test. Only its PreToolUse Edit and Bash-write paths refuse an
  ordinary task's edit to the four files, and treat them as structural (impact_map required).
  The other readers of `_is_protected` refuse nothing: .claude/hooks/stop_gate.py:170 and the
  Bash post-command check at task_contract_gate.py:691 use it to exempt a protected file from the
  out-of-scope list when the contract carries protected_override. So in any governance task the
  four files are now exempt from that out-of-scope net even when scope_paths does not list them,
  as the nine guard paths already are. scripts/check_task_artifacts.py imports the module but
  never calls `_is_protected`.
  routing_readers: git_discipline.py (the commit gate's required-reviewer set),
  check_task_artifacts.py (CI recompute), report_process_health.py, handover_in.py,
  test_governance_doc_parity.py and test_governance_hooks.py. Four new `paths` rows add
  cto-reviewer to those four files; platform-reviewer is already required on them through
  scripts/** and tests/**. CI's fail-closed cover is these rows: check_task_artifacts.py fails an
  MR whose review.md lacks a cto-reviewer verdict for an edit to the four files.
  stops_being_enforced_if_wrong: a misspelt path protects nothing and fails open; the new hook
  test (an ordinary contract's edit to each of the four is denied) catches it. The parity test
  fails if any document's count or list disagrees with the gate and the routing.
  on_failure: the hook denies the edit with the PROTECTED message; nothing else changes.
  blast_radius: no open MR or task edits the four files (`glab mr list` → none open). Every later
  task that edits them needs protected_override and an impact_map. baseline.json stays ordinary;
  no CI job, page or data changes. `.gitlab-ci.yml` is not edited: `.ui_paths` already holds
  tests/fixtures/design_inventory/*, which matches baseline.json.

approved_design:
  - "none: no page output changes"

decisions_taken: >
  Approved in chat, 2026-11-02: protect the three scripts and tests/test_design_inventory.py;
  baseline.json stays an ordinary path, because compare_counts fails CI on any pin that differs
  from the measurement and the protected test refuses any pin above main's, so a gap fix that
  lowers a pin stays an ordinary task. The `.ui_paths` change in the plan's draft is not needed:
  the existing tests/fixtures/design_inventory/* entry already matches baseline.json.
  RECURRING COST, approved in chat, 2026-11-02 with the plan: the four new rows route to both
  cto-reviewer and platform-reviewer, so both run at opus on an edit to them; measured 14 of 529
  commits since 2026-09-01 touched the four files. The guard-path counts become 13, 7 shared with
  platform, 6 the CTO reviews alone. NEW MECHANISM: none; four entries in the existing list.

decisions_reserved:
  - "none: every decision of this task is approved, see decisions_taken"

done_when:
  - An ordinary contract's Edit to each of the four files is denied by task_contract_gate.py with the PROTECTED message (new hook test).
  - With protected_override and no impact_map, each of the four is denied for the missing impact_map.
  - tests/test_governance_hooks.py, tests/test_governance_doc_parity.py and tests/test_design_inventory.py pass.
  - The offline gates and pre-commit pass; an MR is open, never merged.

amendments:
  - "+ tests/test_sentence_length_in_docs.py — authority: the standing rule that a pin only moves down; content: cto-reviewer.md's long-sentence pin falls from 20 to 19, because its edited sentence on opus coverage was split to pass the sentence-length gate."
  - "impact_map corrected after review round 1 — authority: cto-reviewer's FAIL; content: only the PreToolUse paths refuse the edit, CI's cover is the routing rows, and the out-of-scope net now exempts the four files in any task with protected_override. No scope or code change."
