# Task contract — metric_layer.md joins the core documents

objective: >
  docs/working_agreement.md §10's Core document text row lists metric_layer.md, so every edit to it
  needs the CPO's approved exact text first.

refs: >
  The row's exact text: approved in chat, 2026-10-09.

scope_paths:
  - docs/working_agreement.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

acceptance_criteria:
  - working_agreement.md §10's Core document text row reads exactly the approved line, metric_layer.md last in its list; no other line changes.

decisions_taken: >
  metric_layer.md is a core document, and the §10 row's exact text: approved in chat, 2026-10-09.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - Any other change to the working agreement.

done_when:
  - pytest tests/ passes.
  - The criterion is shown in .claude/task/acceptance_evidence.md.

amendments: (none)
