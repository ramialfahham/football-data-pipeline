# Task contract — the UI design brief no longer quotes the CPO

objective: >
  Delete the CPO's chat words from docs/ui_design_brief.md, strip only, with the text approved in
  chat, 2026-10-06.

refs: >
  The cleanup of quoted chat words, approved in chat, 2026-10-06.

scope_paths:
  - docs/ui_design_brief.md
  - tests/test_no_decision_history_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  The edit is the approved text, nothing else:
  - One quote is deleted (the browse block).
  - The line the edit touches also loses its CPO name and date; the history gate refuses a changed
    line that keeps them. No word is added or reworded.
  - Kept, as not chat words: the "CPO note" line, which quotes nothing, and the brief's own labels
    and mood names.
  - The file's pin in tests/test_no_decision_history_in_docs.py moves down from 9 to 8.

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - None.

done_when:
  - grep finds no chat quote left in docs/ui_design_brief.md.
  - pytest (whole suite) and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
