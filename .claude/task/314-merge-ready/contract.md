# Task contract — merge readiness, contract fields, review-round rule, parallel streams

objective: >
  Issue 314, MR 3: add scripts/merge_ready.py (is a green MR still ready after main moved),
  the contract fields depends_on and shared_files enforced by the contract gate, the rule that a
  merge of main leaving the review hash unchanged is not a review round, and a "Parallel streams"
  section of docs/working_agreement.md.

refs: >
  Issue 314 (How, step 3). Requested by the coordinating session; go-live gate issue 290.

scope_paths:
  - scripts/merge_ready.py
  - tests/test_merge_ready.py
  - .claude/hooks/task_contract_gate.py
  - tests/test_governance_hooks.py
  - tests/test_governance_doc_parity.py
  - tests/test_hooks_resolve_worktree.py
  - tests/test_task_folders.py
  - docs/agent_guardrails.md
  - .claude/task/TEMPLATE.md
  - .claude/task/REVIEW_TEMPLATE.md
  - docs/working_agreement.md
  - .claude/task/314-merge-ready/contract.md
  - .claude/task/314-merge-ready/review.md
  - .claude/task/314-merge-ready/review_input.patch

protected_override: >
  .claude/hooks/task_contract_gate.py is edited for the depends_on and shared_files fields, which
  issue 314 lists under What exactly; the CPO approved that issue in chat on 15 Nov 2026.

impact_map: >
  writers: only task_contract_gate._parse_contract produces the parsed contract dict; its readers
    are _gate_file_edit in the same file and the tests under tests/.
  downstream: PreToolUse Edit|Write|MultiEdit events of every session in the repo. merge_ready.py
    is a new read-only script that nothing imports; it imports _parse_contract's sibling helper.
    No dbt model changes (scripts and docs only), so `dbt ls` lineage of the change is empty.
  layer_rules: none apply; check_layer_contract.py does not read scripts or hooks.
  deploy_order: none; nothing writes the warehouse. A contract written before this MR lacks the
    two fields, so the gate asks for a one-line amendment on its next non-task edit.
  blast_radius: if the gate is wrong it either blocks every edit (fails open on a parse error, as
    before) or lets a shared file change unlisted. A test per case pins both.

approved_design:
  - none: no page output changes

depends_on:
  - !455

shared_files:
  - none: no design baseline, chart manifest or chart pin changes

decisions_taken: >
  Everything in issue 314 What exactly for steps merge_ready.py, the review-round rule, the
  contract fields and the Parallel streams section, approved in chat, 15 Nov 2026. The
  Parallel streams text is committed only after the CPO approves its exact wording through the
  coordinating session. The gate requires both fields in every contract; the shared-file list is
  the design baselines, the chart manifest and pins. No new dependency, no spend, no new
  recurring mechanism beyond what issue 314 names.

decisions_reserved:
  - none: the Parallel streams text is approved in chat, 16 Nov 2026, and committed word for word.

done_when:
  - Full pytest is green.
  - merge_ready.py on a real green MR prints ready, or the overlap, using glab and git only.
  - The gate denies an edit when a contract lacks depends_on or shared_files, and denies a shared
    file edit not listed in shared_files.

amendments:
  - + tests/test_hooks_resolve_worktree.py and tests/test_task_folders.py: their literal contracts need the two new fields or the gate denies their edits. Authority: issue 314 What exactly, task contract fields, approved in chat, 15 Nov 2026. Content: add depends_on and shared_files to those fixtures only.
  - + docs/agent_guardrails.md: the guardrails row for task_contract_gate.py lists the new denials. Authority: issue 314 What exactly, task contract fields, approved in chat, 15 Nov 2026.
  - The Parallel streams section of docs/working_agreement.md is committed word for word as approved in chat, 16 Nov 2026, with the round rule owned by section 2. Its Dependent work block reads: work that needs an open MR's code starts from the latest gitlab/main after that MR has merged. Approved in chat, 16 Nov 2026.
  - The section 12 heading "Before every push." reads "Before every review round and every push."; its bullet is unchanged. Approved in chat, 16 Nov 2026.
