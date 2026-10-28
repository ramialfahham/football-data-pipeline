# Verification — the Team page enters the approved-designs list

No file under `site_v2/src/` changes, so no acceptance criteria apply. The checks of the contract's
done_when:

criteria_demonstrated:
  - Tests: `pytest tests -q` passes, the shipped-list test included (every entry parses).
  - Diff: one line added to `docs/wireframes/approved_designs.yml`, `team: 134`.
