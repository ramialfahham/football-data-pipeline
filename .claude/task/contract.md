# Task contract — handover: #1 is done, five new issues, and a wrong stash index

> Branch `chore/handover-1-done` from `main` (`6238dc4`). Bookkeeping. No protected path, so no
> `protected_override`. Nothing on the structural surface, so no `impact_map`. No `site_v2/src/`
> path, so no `acceptance_criteria`. A commit touching `contract.md` is NEVER artifact-exempt, so
> this still takes a scope audit.

objective: >
  Bring `.claude/active_work.md` back to current state after !11 and !12 merged, and fix one live
  defect in it.

  WHAT IS STALE. It says main is GREEN at `9987184` with nothing in flight; main is now `6238dc4`
  and both MRs merged. It lists #1 as the next thing to pick up; #1 shipped in !12. It knows
  nothing of the five issues filed 2026-08-07 (#20-#24). Its test count is `583 python`, measured
  2026-08-03; the suite is now 645.

  THE DEFECT, which is the one this file warns about in its own FIRST ACTIONS block. Line 143 says
  the player Overview is "UNCOMMITTED in `stash@{0}`", while lines 48-52 say to MATCH BY MESSAGE,
  NEVER BY INDEX, and record that it had already shifted to `{1}`. Verified 2026-08-07: `stash@{0}`
  is the 367 landing page and `stash@{1}` is the player Overview. A session trusting line 143 pops
  the wrong stash. The file contradicts itself, and the correct half is the half nobody reads
  second. Fixed by naming the stash by MESSAGE, so no index can go stale again.

  ONE TRAP MOVED IN, because it will bite the next session. The governance base is spelled
  `origin/main` everywhere, and `origin` is the DORMANT GITHUB remote locally while it is GitLab in
  CI. Running `check_task_artifacts.py` locally therefore FALSE-FAILS, naming three reviewers that
  are not required. Observed this session. Filed as #24; the workaround belongs in REVIEW MECHANICS
  until it is fixed.

  THE CAP IS THE CONSTRAINT. The file is at 15,975 characters against a hard 16,000
  (`handover_in.py:46`) that DROPS THE TAIL SILENTLY. Everything added is paid for by compressing
  spent history in the same file, never by cutting live state.

refs: >
  Follows MR !12 (GitLab #1) and !11, both merged 2026-08-07. Issues filed this session and
  recorded here: #20, #21, #22, #23, #24. CPO instruction in this session: *"go ahead as
  recommended"*, against a stated recommendation to update the handover before starting #19,
  because #19 is a compression pass across every governing artifact and is the task most likely to
  be interrupted mid-way.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

decisions_taken: >
  THRESHOLD DECLARATIONS, stated because no gate parses this field.

  NEW MECHANISM — NO. Prose edits to one handover file. No hook, script, test, job, dependency or
  config surface is added or changed.

  RECURRING COST — NO. Nothing executes. No CI job, no runner minute, no BigQuery byte, no API
  call. The file shrinks rather than grows.

  NEW EXTERNAL SURFACE — NO. Nothing is published or deployed.

  GUARD INVARIANT — UNCHANGED. No guard is edited. #24 records that a guard's DEFAULT BASE is
  wrong locally; this task writes down the workaround and does not touch the guard, because
  `scripts/**` and `.gitlab-ci.yml` are not in scope and changing a gate's base is guard-class.

  WHAT IS DELETED, stated explicitly because deletion is the risk in a capped file: only history
  that is already durable elsewhere. The audit's 12-item plan breakdown (spent, and in `git log` +
  the tracker) and the full text of #547's ranked cost list (which the same paragraph already says
  lives in GitLab #3). No live state, no trap, no open decision is removed.

decisions_reserved:
  - Whether the 16,000-character cap is the right mechanism at all. Every session now pays a
    compression tax to add a line, and the file has been at 95%+ of cap for three sessions running.
    That is adjacent to #19 and is the CPO's, not something to solve by trimming again here.

done_when:
  - "`.claude/active_work.md` is under 16,000 CHARACTERS measured with Python `len()`, not `wc -c`,
    and `handover_in.py` injects it with no truncation notice."
  - "The player Overview stash is named by MESSAGE, with no bare `stash@{n}` index anywhere that a
    session could act on."
  - "main `6238dc4`, !11 + !12 merged, #1 DONE, #19 next, and #20-#24 all appear."
  - "The five fast offline gates pass, using `--base gitlab/main` for the artifact gate."

amendments: (none)
