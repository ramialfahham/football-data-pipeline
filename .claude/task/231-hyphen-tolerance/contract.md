# Task contract — the split count excuses a hyphen break by the word's real width

objective: >
  The design check excuses a club name broken at its hyphens when the whole name cannot fit on
  one line of its box. It decides "cannot fit" by comparing the sum of the characters' widths
  with the line width plus one pixel. A name wider than its line by less than a pixel, such as
  Montigny-lès-Metz (134.6px) in a 134px box at 280px on the Coupe de France match page, is
  counted as a split although it breaks only at its hyphens. Measure the word's real width on
  one line instead of adding slack, and pin both cases with tests.
refs: "#231; false rise found by the #297 session; the hyphen exemption: !493"

scope_paths:
  - scripts/check_design_inventory.py
  - tests/test_design_inventory.py
  - .claude/task/231-hyphen-tolerance/contract.md
  - .claude/task/231-hyphen-tolerance/review.md
  - .claude/task/231-hyphen-tolerance/review_input.patch

protected_override: >
  The coordinating session set this change in its session message of 2026-11-21, as an
  engineering decision under the CPO's visual-details mandate of 2026-11-16 (the counter was
  wrong, not the page), the same basis as the earlier change to this guard. The MR head
  declares the locked files, scripts/check_design_inventory.py and
  tests/test_design_inventory.py; the CPO's merge is the approval.

impact_map: >
  writers: none. No table or model is written. The two files are a check and its tests.
  downstream: `scripts/check_design_inventory.py` runs in `ci_local --mr` and in the MR pipeline
  (job validate:ui, the design check against tests/fixtures/design_inventory/baseline.json and
  baseline_quick*.json) and in the main sweep; `tests/test_design_inventory.py` runs in
  validate:ui after the check. Nothing else imports the check's COUNT_JS (grep over scripts,
  tests and design-mocks).
  layer_rules: none apply (no dbt).
  deploy_order: none. No deployed system reads these files; the nightly never runs them.
  blast_radius: what stops being counted is a break at the hyphens of a word inside a part
  marked `breaks: hyphens`, when the word is wider than its line by less than a pixel. A word
  that fits its line and still wraps at a hyphen, a break inside a segment, and a break
  outside the marked part all still count. A pin may only fall; a fall is lowered in the
  baseline in this MR only if validate:ui reports one.

approved_design:
  - none: no page output changes

depends_on:
  - none: no open MR touches the check or its tests

shared_files:
  - none: no baseline file is expected to change; an amendment adds one if validate:ui reports a count that fell

decisions_taken: >
  The coordinating session's message of 2026-11-21 sets the fix: drop the one-pixel tolerance in
  hyphenBreak and measure the word's real width on one line, with a pytest pinning a word just
  over its line that breaks at its hyphens (excused) and a word that fits but wraps at a hyphen
  (still counted). The loop in hyphenBreak already proves that every break falls after a
  hyphen; the width test only has to show that the word cannot fit on one line.

decisions_reserved:
  - none: the change corrects a counter and decides nothing about a page, a metric or a name

done_when:
  - "python -m pytest tests/test_design_inventory.py passes locally in Chromium, with both new tests"
  - "the Montigny-lès-Metz case measured at 280px reads split 0 and the existing hyphen tests still read as before"
  - "python scripts/ci_local.py --mr passes, validate:ui included"
  - "the MR pipeline is green and python scripts/merge_ready.py <iid> says ready"

amendments: (none)
