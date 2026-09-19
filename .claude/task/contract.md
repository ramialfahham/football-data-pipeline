# Task contract — handover: #150 is built and open as !209; next is #109 step 3 after a green nightly

objective: >
  Bring `.claude/active_work.md` to the state after this session: #150 built, reviewed and open as
  MR !209 with three questions on its head (the copy, whether it waits on #155, the two deferred
  prod tests to retry after the 04:00 nightly); #155 filed (the match preview title collision at full
  scale); the next unit of work is #109 step 3 once the 2026-09-19 nightly is green. Under 16,000
  characters. Refresh the tracker snapshot.

refs: >
  The CPO's rulings in chat 2026-09-18 (the plan for #150 approved; the slug from the warehouse;
  played rows inert until the report page exists) are recorded on !209's head and in its contract.
  #155 filed 2026-09-19 by the build; `tests/test_no_dead_issue_refs.py` lists 155 as a dead number
  and its own assertion text prescribes the fix: remove a number only when GitLab has genuinely issued
  it, and move the self-test pin to the next dead number.

scope_paths:
  - .claude/active_work.md
  - tests/test_no_dead_issue_refs.py
  - docs/tracker/gitlab_snapshot.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  None. The handover's top section rewritten to what was built and what is open; the dead-issue
  guard's set loses 155 because GitLab issued it (the guard's own rule), the count, digest and floor
  follow, the self-test that pins the guard fires moves to 156. No other change to the test.

decisions_reserved:
  - none: every open question is on !209's head for the CPO; this commit records state.

done_when:
  - `.claude/active_work.md` names !209 as open with its three questions, #155 as filed, #109 step 3 as next after a green nightly; `len()` under 16,000.
  - `python -m pytest tests/test_no_dead_issue_refs.py -q` green; `python scripts/snapshot_tracker.py` run and its output committed.

amendments: (none)
