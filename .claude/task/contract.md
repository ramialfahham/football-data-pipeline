# Task contract — documents follow three writing standards

objective: >
  Working agreement section 9 and its Cursor mirror say that documents follow ISO 24495-1, that
  every term, table row and rule in them follows ISO/IEC 11179-4, and that sentences follow
  ASD-STE100, with the text approved in chat, 2026-10-06.

refs: >
  The writing standards for documents, approved in chat, 2026-10-06.

scope_paths:
  - docs/working_agreement.md
  - .cursor/rules/agent-behavior.mdc
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  The edit is the approved text, nothing else:
  - The ISO 24495-1 line in section 9 now covers documents, and two lines follow it: one for
    ISO/IEC 11179-4, one for ASD-STE100.
  - The Cursor rule file mirrors section 9, so its same line changes the same way.
  - The enforcement (a sentence-length gate, its pin and a reviewer item) is a separate MR.

  Threshold declarations. NEW MECHANISM: none in this MR. RECURRING COST: none.

decisions_reserved:
  - None.

done_when:
  - Both files carry the three approved lines.
  - pytest (whole suite) and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
