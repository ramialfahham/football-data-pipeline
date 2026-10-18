# Verification — Home enters the approved-designs list

No file under `site_v2/src/` changes, so no acceptance criteria apply. The checks of the contract's
done_when:

criteria_demonstrated:
  - Tests: `pytest tests -q` passes 1593, 2 skipped; the shipped list's five entries all parse.
  - Diff: one line added to `docs/wireframes/approved_designs.yml`, `home: 127`, and the shipped-list test rewritten.
