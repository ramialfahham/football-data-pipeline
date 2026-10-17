# Verification — no page changes without an approved design

No file under `site_v2/src/` changes, so no acceptance criteria apply. The checks of the contract's
done_when:

criteria_demonstrated:
  - Tests: `pytest tests -q` passes 1584, 2 skipped; the gate's own tests drive the real hook and CI scripts, and each guarded line was removed once to show its test fails.
  - Hook: a page-surface edit or shell write is denied without `approved_design`, and allowed with an issue line or a `none:` sentence; a bare `none`, `none:`, a placeholder, an empty block or a comment does not count.
  - CI: a page-surface diff fails without the field, with a named issue lacking `design::approved`, or when the labels cannot be read.
  - Label: `git_discipline.py` denies a glab command that adds `design::approved` and allows `glab issue list` and `view`.
