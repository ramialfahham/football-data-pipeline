# Task contract — the agent guardrails document states the current state only

objective: >
  Replace docs/agent_guardrails.md with the text approved in chat, 2026-10-06: what exists and
  where it lives, every line true against the code, no history, rules pointed to their owner.

refs: >
  The cleanup of the core documents, approved in chat, 2026-10-06.

scope_paths:
  - docs/agent_guardrails.md
  - tests/test_no_decision_history_in_docs.py
  - tests/test_governance_doc_parity.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  The document is the approved text, nothing else. Its two test companions follow from it:
  - tests/test_no_decision_history_in_docs.py: the document has no history line left, so its
    pin row is removed.
  - tests/test_governance_doc_parity.py: the document no longer states the reviewer counts
    (working_agreement.md section 2 owns them), so its three count anchors are removed, and a
    prose-subset entry whose run no longer exists in the document is removed.

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - None.

done_when:
  - docs/agent_guardrails.md equals the approved text.
  - pytest (whole suite) and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
