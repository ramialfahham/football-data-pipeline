# Task contract — the component checks cover every page and mock

objective: >
  Complete step 1 of the component-system plan: the gap-count checks cover every page and mock,
  today's and every future one, with no exception, and no visual change. Every built file each
  Pages-table row matches is checked; a built file no row matches, a mock generator that fails, a
  generator page no row names and a language a mock lacks are each counted as a gap. Every
  design-mocks/gen_*.py is found on disk and run with one interface, --out DIR, which writes all
  its pages. The element measurements run at the six count widths, and a miss is counted in the
  baseline. A test fails when a baseline count rises above main's or a new entry starts above
  zero.

refs: >
  #243, the component-system plan, approved in chat, 2026-11-01. This task completes its How
  step 1.

scope_paths:
  - scripts/check_page_css.py
  - scripts/check_design_inventory.py
  - scripts/design_inventory.py
  - tests/test_design_inventory.py
  - tests/fixtures/design_inventory/*
  - tests/test_no_decision_history_in_docs.py
  - tests/test_sentence_length_in_docs.py
  - design-mocks/gen_*.py
  - design-mocks/README.md
  - docs/wireframes/block_standard.md
  - .claude/skills/validate-local/SKILL.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

approved_design:
  - "none: no page output changes"

decisions_taken: >
  Approved in chat, 2026-11-02, with this task's plan: the check finds every page and mock on
  disk; anything it cannot check is counted as a gap, never skipped; a count may only fall; a new
  page or mock enters with zero gaps. A file matched by two rows belongs to the row with the
  literal path. The --out DIR option changes nothing else in a generator; its output is
  byte-identical. A mock without German or without the Finnish toggle is one gap per missing
  language. The 1px overflow margin and the 20% line trim are written into the block standard as
  the check's fixed rules. The six widths run in parallel processes. Not in this task, each its
  own later task: the font (How step 2), text written by scripts and generators, the build date
  the squad ages count from, and making the check files protected paths. NEW MECHANISM: the
  never-rises test and the generator interface. RECURRING COST: validate:ui renders every built
  page; measured on the MR pipeline and reported in the MR.

decisions_reserved:
  - "none: every decision of this task is approved, see decisions_taken"

done_when:
  - check_page_css.py and check_design_inventory.py --dist site_v2/dist pass against the baseline, and every built file and every generator is rendered or counted.
  - A planted page with no row, a planted failing generator and a raised pin each turn the tests red.
  - Every generator that runs today writes byte-identical output with --out.
  - The full pytest, npm run build in site_v2 (sample data), the offline gates and pre-commit pass.
  - The baseline's rendered counts are the ones measured by validate:ui on the MR pipeline.

amendments:
  - "The validate-local skill's Tier 1b describes what the measured check renders; it is added to scope_paths so it states the check as changed by this task. Doc-sync of the approved plan (approved in chat, 2026-11-02); no new decision."
