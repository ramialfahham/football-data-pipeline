# Task contract — the component checks that count today's gaps

objective: >
  Step 1 of the component-system plan: checks that count the site's and the mocks' design gaps,
  with no visual change. Static counts: CSS in a mock generator touching an element's class (every
  generator is read, not only the block standard's pages), CSS outside system.css, width rules at
  a width outside today's set, banned line-break and cut-off properties, and literal text in
  components and pages. Rendered counts on the built sample site and the block standard's mocks at
  280, 320, 360, 375, 700 and 1010px: sideways scroll, text overflowing its box, split words,
  overlapping text and classes no block-standard row names. Each count is stored in a baseline
  and the check fails when a count differs from it.

refs: >
  #243, the component-system plan, approved in chat, 2026-11-01. This task is its How step 1.

scope_paths:
  - scripts/check_page_css.py
  - scripts/check_design_inventory.py
  - scripts/design_inventory.py
  - tests/test_design_inventory.py
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/counts_red.html
  - tests/test_no_decision_history_in_docs.py
  - docs/wireframes/block_standard.md
  - design-mocks/README.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

approved_design:
  - "none: no page output changes"

decisions_taken: >
  Approved in chat, 2026-11-01 (the plan of #243) and 2026-11-02 (this step's plan): the checks
  listed in the objective, their widths and languages, the baseline that may only fall, and these
  readings. `overflow-wrap: break-word` and `word-break: break-word` are banned with the four named
  properties, because they split a word. A break after a hyphen inside a word counts as a split
  word. A count is stored per page, summed over widths and languages; classes are counted as
  distinct names per page. The existing element measurements keep their three widths. The
  rendered counts depend on the font (`system-ui`), so the baseline holds the numbers measured in
  CI's Playwright image and a run on another platform prints its counts without comparing them.
  NEW MECHANISM: the count baseline, the "each count only falls" line of #243's checklist, read
  by the two existing checks; no new CI job, no CI file change, no new dependency. RECURRING
  COST: validate:ui renders 183 more pages per run; measured on the MR pipeline and reported in
  the MR.

decisions_reserved:
  - "none: every decision of this task is approved, see decisions_taken"

done_when:
  - check_page_css.py and check_design_inventory.py --dist site_v2/dist print every count and pass against the baseline; the planted-defect page counts each defect kind.
  - The full pytest, npm run build in site_v2 (sample data), the offline gates and check_design_inventory.py pass.
  - The baseline's rendered counts are the ones measured by validate:ui on the MR pipeline.

amendments: (none)
