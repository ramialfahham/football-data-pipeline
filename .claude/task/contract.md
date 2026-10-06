# Task contract — the site architecture no longer quotes the CPO

objective: >
  Delete the CPO's chat words from docs/site_architecture.md, strip only, with the text approved
  in chat, 2026-10-06.

refs: >
  The cleanup of quoted chat words, approved in chat, 2026-10-06.

scope_paths:
  - docs/site_architecture.md
  - tests/test_no_decision_history_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  The edit is the approved text, nothing else:
  - Five quotes are deleted (the team slug, the navigation note's three, the browse block).
  - A line the edit touches also loses its CPO name, date and issue number; the history gate
    refuses a changed line that keeps them. No word is added or reworded.
  - The file's pin in tests/test_no_decision_history_in_docs.py moves down from 44 to 40.

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - None.

done_when:
  - grep finds no chat quote left in docs/site_architecture.md.
  - pytest (whole suite) and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
