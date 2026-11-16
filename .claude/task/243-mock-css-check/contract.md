# Task contract — mock CSS check

objective: >
  Issue #243. A standalone design mock carries its own copy of the site's styles, and a mock's
  "Today" side drifted from main's system.css unreviewed. design-mocks/check_mock_css.py compares
  the mock's rule set with main's system.css as the browser serializes both: every rule not under
  html.prop must equal main's, and every html.prop rule is listed for the CPO.

refs: "#243 (the component system), part of; coordinator brief, 16 Nov 2026."

scope_paths:
  - design-mocks/check_mock_css.py
  - tests/test_check_mock_css.py
  - tests/fixtures/mock_css/*
  - .claude/task/243-mock-css-check/contract.md
  - .claude/task/243-mock-css-check/review.md
  - .claude/task/243-mock-css-check/review_input.patch

depends_on:
  - none: a new standalone script and its tests; reads main's system.css through git

shared_files:
  - none: no design baseline, component registry, font coverage or chart screenshot file changes

decisions_taken: >
  The check is the coordinator's engineering call (mechanical Today = main, Proposed listed rule
  by rule). No new dependency: Playwright is already pinned in requirements-ui.txt. No recurring
  cost and no CI job: the script is run by hand on a mock before it goes to the CPO.

decisions_reserved:
  - none: the check publishes no page and decides no product question

done_when:
  - "pytest tests/test_check_mock_css.py passes: clean mock, changed main rule, new unscoped rule and missing main rule behave as stated; html.prop rules listed, .mock-* rules ignored"
  - "python design-mocks/check_mock_css.py <mock> exits 0 on a clean mock and 1 on a drifted one"
  - "python scripts/ci_local.py --mr is green; full pytest is green"

amendments: (none)
