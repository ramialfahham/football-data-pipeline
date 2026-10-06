# Task contract — the north star no longer quotes the CPO

objective: >
  Delete the CPO's chat words from docs/north_star.md and its repeat in
  docs/roles/growth_expert.md, strip only, with the text approved in chat, 2026-10-06.

refs: >
  The cleanup of quoted chat words, approved in chat, 2026-10-06.

scope_paths:
  - docs/north_star.md
  - docs/roles/growth_expert.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  The edit is the approved text, nothing else:
  - The milestone line in the CPO's first person is deleted from docs/north_star.md, with its
    blank line; the line after it stays.
  - Its repeat in docs/roles/growth_expert.md is deleted from the Quality over growth bullet.
  - No word is added or reworded. Neither file's history-line count changes, so no pin moves.

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - None.

done_when:
  - grep finds the quote in neither file.
  - pytest (whole suite) and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
