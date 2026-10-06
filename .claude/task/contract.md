# Task contract — the content architecture no longer quotes the CPO

objective: >
  Delete the CPO's chat words from docs/content_architecture.md, strip only, with the text
  approved in chat, 2026-10-06.

refs: >
  The cleanup of quoted chat words, approved in chat, 2026-10-06.

scope_paths:
  - docs/content_architecture.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  The edit is the approved text, nothing else:
  - Two phrases from the design conversation the header names are deleted: the navigation feel
    and the signature-things line, the latter as a whole line.
  - Kept, as not chat words: the example reads in section 6, the quote of metrics_display.md and
    term names.
  - No word is added or reworded. The file's history-line count does not change, so no pin moves.

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - None.

done_when:
  - grep finds neither phrase in docs/content_architecture.md.
  - pytest (whole suite) and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
