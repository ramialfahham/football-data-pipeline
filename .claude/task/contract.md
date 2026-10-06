# Task contract — the working agreement no longer quotes the CPO; core documents change only with approved text

objective: >
  Delete the CPO's chat words from docs/working_agreement.md, strip only, and add the rule that the
  core documents change only with text the CPO approved, with the text approved in chat,
  2026-10-06.

refs: >
  The cleanup of quoted chat words, approved in chat, 2026-10-06.

scope_paths:
  - docs/working_agreement.md
  - tests/test_no_decision_history_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  The edit is the approved text, nothing else:
  - Two quotes are deleted (the issue carve-out, the frozen log). A line the edit touches also
    loses its CPO name, date and MR number, and the review-round story that carried the MR number.
    No word is added or reworded; "the exceptions" starts its sentence with a capital.
  - One row is added to the section 10 table: core document text, every edit to the seven core
    documents, the exact text approved before the edit.
  - The file's pin in tests/test_no_decision_history_in_docs.py moves down from 21 to 20.

  Threshold declarations. NEW MECHANISM: none; the row is a rule, no gate enforces it. RECURRING
  COST: none.

decisions_reserved:
  - None.

done_when:
  - grep finds no chat quote left in docs/working_agreement.md.
  - pytest (whole suite) and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
