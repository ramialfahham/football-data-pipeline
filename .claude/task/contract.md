# Task contract — handover: #150 merged as !209; next is #109 step 3

objective: >
  Bring `.claude/active_work.md` to the state after this session: #150 built, reviewed and merged
  as !209 (2026-09-19, after the data build was retried green against the fresh prod table); #155
  filed (the match preview title collision at full scale); the 2026-09-19 nightly green; the next
  unit of work is #109 step 3. Under 16,000 characters. Refresh the tracker snapshot.

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
  - none: !209 is merged, its head was his check; this commit records state.

done_when:
  - `.claude/active_work.md` names !209 as merged, #155 as filed, the 2026-09-19 nightly as green and #109 step 3 as next; `len()` under 16,000.
  - `python -m pytest tests/test_no_dead_issue_refs.py -q` green; `python scripts/snapshot_tracker.py` run and its output committed.

amendments:
  - 2026-09-19, no path added: the CPO merged !209 while this handover was open, so the handover's top paragraph is rewritten from "open, three questions on the head" to "merged"; the copy shipped as drafted and the merge is the ruling on it; the 2026-09-19 nightly succeeded, so #109 step 3 is unblocked.
