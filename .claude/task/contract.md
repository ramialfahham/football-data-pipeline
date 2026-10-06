# Task contract — a gate holds documents to the sentence-length limit

objective: >
  Enforce working_agreement.md section 9 for documents: a hook refuses an edit that adds a
  Markdown sentence over 25 words, or over 20 in a numbered step; a per-document pin keeps the
  long sentences left from growing; scope-auditor checks the parts no pattern catches.

refs: >
  The enforcement of the writing standards, approved in chat, 2026-10-06.

scope_paths:
  - .claude/hooks/sentence_length_gate.py
  - .claude/settings.json
  - .claude/agents/scope-auditor.md
  - docs/agent_guardrails.md
  - tests/test_sentence_length_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

protected_override: >
  Approved by the CPO in chat, 2026-10-06: the sentence-length hook, its wiring in
  .claude/settings.json, the per-document pin test, and item 9 of the scope-auditor brief, with
  the brief item and the guardrails row in the exact text approved.

impact_map: >
  fires on: PreToolUse Edit, Write and MultiEdit (the existing Edit-family matcher in
  .claude/settings.json); it acts only on a Markdown document as comment_history_gate.is_doc_path
  defines it (every tracked .md except .claude/task/, docs/tracker/ and site/).
  imports: is_doc_path from comment_history_gate.py and resulting_text from
  memory_budget_gate.py, so the document scope and the edit arithmetic have one definition each.
  what it blocks: an edit whose resulting document holds a long sentence the document on disk
  did not hold. A long sentence left as it is never blocks; a changed one must meet the limit.
  failure: fails open on any error, like every hook here; a shell write bypasses it, and
  tests/test_sentence_length_in_docs.py catches that in CI with a per-document count that only
  goes down.
  what stops being enforced if it is wrong: nothing existing; it adds denies only. No other
  hook, gate, test or CI job reads it.
  blast_radius: every agent edit of a Markdown document from now on. No dataset, model, export
  or page changes.

decisions_taken: >
  The design and texts approved in chat, 2026-10-06:
  - A sentence in a numbered list item is a procedure step, at most 20 words; every other
    sentence is a description, at most 25 words.
  - An inline code span counts as one word; a link counts its visible text; headings, code
    blocks, HTML comments and front matter are not prose; table cells are; a sentence ends at
    a full stop, an exclamation or question mark, or a semicolon.
  - scope-auditor gains item 9 and docs/agent_guardrails.md gains the hook's row, both in the
    exact text approved.
  Readings: the document on disk is read with its line endings normalised, so an Edit written
  with plain newlines applies to a CRLF working tree.

  Threshold declarations. NEW MECHANISM: the sentence-length hook, approved in chat, 2026-10-06.
  RECURRING COST: none.

decisions_reserved:
  - None.

done_when:
  - The hook's own tests drive every deny and pass; the pin matches the tree in both directions.
  - pytest (whole suite) and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
