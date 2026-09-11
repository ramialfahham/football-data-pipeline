# Acceptance evidence — sweep 3 of 4: decision history out of the tests

criteria_demonstrated:
  - EVERY FLAGGED LINE IN `tests/` IS GONE. Before: `count_tree` over `tests/` → 245 lines in 28
    files (`test_governance_hooks.py` 103, `test_export_landing.py` 18, then 26 files with 1–10;
    by marker: date 102, review credit 86, product owner 23, round 24, MR 10). After: **0 lines,
    0 files** (`sweep_size.py tests` → `total: 0`). Every line was rewritten by hand, every edit
    passing the edit-time hook. The rule applied: keep what the test pins and why the case
    exists; drop who found it and in which round. Examples: `test_governance_hooks.py`'s
    fixture comment keeps "a one-sided test passes while broken" and loses "(cto-reviewer,
    <date>)"; the acceptance-gate docstrings keep "the test would have passed with
    `ACCEPTANCE_TRIGGER = ''`, i.e. firing on everything" and lose "Caught by platform-reviewer
    at opus, round 1"; `test_refetch_cadence.py` keeps "It looked like a stagger and was a silent
    cadence cut, and the rule is 'every 7 days'" and loses "the CPO's ruling was";
    `test_no_dead_issue_refs.py` keeps "a test that would still pass with the change reverted is
    not coverage" and loses "`platform-reviewer` FAILed round 4 on exactly that". The lines the
    guard cannot see were swept by eye: both split-line credits
    (`test_nightly_entrypoint_parity.py` "each found by a / reviewer" → "none found by anything
    mechanical"; `test_incomplete_snapshot_not_written.py` "Found in review round 1 by / two
    reviewers independently" → removed) and both plural rounds (`test_governance_hooks.py`
    "#370 rounds 6-12" → "spent seven rounds that way"; "CTO findings, rounds 2-3" → removed).
    Routing-key mentions in docstrings (11, e.g. "routes to `cto-reviewer`") are reworded to the
    role ("routes to the CTO", "the display reviewer") — the keys stay exact in the code lines
    that use them. Two stale facts corrected because the why was false as written:
    `test_refetch_cadence.py` said nothing read the freshness thresholds and named an unmerged
    branch — `scripts/check_raw_freshness.py` (the hourly `fdp-freshness` sentinel) reads them
    and is named now; `test_export_site_data.py`'s fixture-date comment keeps the ordering
    argument with month names instead of ISO dates that read as history.
  - NO BEHAVIOUR CHANGE, PROVEN ON EVERY TOUCHED FILE. `prove_py_comments_only.py` (docstrings
    by `ast`, comments by `tokenize`, blank lines dropped) over the 28 modified test files
    (the pin file was measured before its constants changed): **27 identical, 1 differs** — the
    one is `GOOD_BODY` in `test_governance_hooks.py`, a review.md FIXTURE string re-joined from
    implicit-concatenation parts so its `## analytics-engineer-reviewer` header no longer starts
    a source line (the guard read it as a comment line); its VALUE is byte-identical to HEAD's
    (`ast.literal_eval` of both: `True`), declared in the contract's amendment. `ruff check
    --config .ruff-ci.toml tests/` → All checks passed. `pytest tests/` → **1,057 passed, 1 skipped, 14 subtests
    passed** in 11:08 — the same count as `main` (measured in this session before the sweep).
  - THE PIN MOVES BY EXACTLY THE LINES REMOVED. Whole-tree `count_tree` before: (495, 84); after:
    **(250, 56)** — 495 − 245 = 250 and 84 − 28 = 56, measured, not computed. `PINNED_LINES =
    250`, `PINNED_FILES = 56`.
  - NOTHING LOAD-BEARING LOST. Every docstring that named a defect class still names it: the
    one-sided-coverage class (`test_governance_hooks.py`, six sites), the "passed either way"
    class (acceptance gate, base resolution), the hand-copied-list class (routing enumeration,
    doc parity), the double-count (`test_dropped_call_visibility.py`), the shortened cadence
    (`test_refetch_cadence.py`), the truncate-at-open hazard (`test_declare_missing_columns.py`),
    the shape-test-beaten-by-rewrites (`test_alert_policy_recipe.py`). Numbers kept where they
    were the why: 26 dropped calls, 3,539 team-seasons, 25 → 0 players, 48 tracked files, 1,024
    / 16,384 characters, 4 of 256 members.
  - THE HANDOVER STATES THE CURRENT STATE OF #115: sweeps 1–2 merged, sweep 3 this branch, sweep
    4 sized (250 lines, 56 files), step 9 remaining.

## What is NOT demonstrated
- The remaining 250 lines (`site_v2/src` 99 / 18 files, `site_v2/scripts` 17 / 5, `ingestion`
  62 / 18, `design-mocks` 72 / 15) are untouched — sweep 4.
- Narrative lines with no marker and no credit ("both caught in review", "caught in review, not
  by any static check", "reviewers drew the false inference three times") stay: they name the
  class of failure, not a person or a round.
