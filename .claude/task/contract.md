# Task contract — metrics_display.md: one window per team on the match page

objective: >
  Rule 3 of the "Window & scope display contract" in docs/wireframes/metrics_display.md still
  describes a W1/W2 window switch the approved match page no longer has. Replace it with the
  CPO-approved text: one window per team, no switch, as metrics_context_model.md §3–4 gives it.

refs: >
  #166, the next match page build
  (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/166), its "Written rules"
  criterion; the design on #132. The text: approved in chat, 2026-10-17.

scope_paths:
  - docs/wireframes/metrics_display.md
  - tests/test_sentence_length_in_docs.py
  - tests/test_no_decision_history_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

decisions_taken: >
  Approved in chat, 2026-10-17: rule 3 is replaced by exactly "3. **One window per team, no
  switch.** The match page shows each team the window that `docs/metrics_context_model.md` §3–4
  gives it, flagged by the warehouse." Nothing else in the file changes.

decisions_reserved:
  - none: the CPO approved the exact replacement text, and this task writes it unchanged.

done_when:
  - The full pytest suite passes.
  - git diff shows only rule 3 replaced in metrics_display.md.
  - Reviewers per review_routing.json pass.

amendments: (none)
