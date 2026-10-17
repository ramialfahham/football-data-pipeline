# Verification — the design gate reads the approved designs on main

No file under `site_v2/src/` changes, so no acceptance criteria apply. The checks of the contract's
done_when:

criteria_demonstrated:
  - Tests: `pytest tests -q` passes 1593, 2 skipped. The gate's tests drive the real hook and the CI script; the non-UTF-8 and multi-pair fixes were each reverted once to show their test fails.
  - Hook: a page-surface edit or shell write is denied when a named page and issue are not in `docs/wireframes/approved_designs.yml` on the base ref, when only the branch's copy holds them, or when the list cannot be read; a `none:` line needs no list.
  - Live: on this machine the base is `gitlab/main`, which does not hold the list yet, so `home: #127` and `competition: #129` are both refused until this MR merges.
  - CI: `design_errors` fails a named design missing from the base ref's list and fails closed on an unreadable list; end to end through `main()`, a list only in the branch fails.
  - Grep: `git grep "design::approved\|DESIGN_GATE_TOKEN"` outside `.claude/task/` finds nothing.
