# Task contract — handover after !18-!21 and the cold audit re-run

> Branch `chore/handover-after-audit-rerun` from `main` (`290bac0`). Bookkeeping. No PROTECTED
> path, so no `protected_override`. Nothing structural, so no `impact_map`. No `site_v2/src/`, so
> no `acceptance_criteria`. `.claude/active_work.md` is NOT scope-exempt and is listed below. A
> commit touching `contract.md` is NEVER artifact-exempt, so this still takes a scope audit.

objective: >
  Bring `.claude/active_work.md` to current state after !18, !19, !20 and !21 merged, and record
  the one thing this session produced that a cold chat cannot re-derive.

  WHAT IS STALE. main is `290bac0`, not `0394e52`. The merge list stops at !15. It lists #25 and
  #29 as OPEN when both are merged and closed. Its test count is 648 (now 665). It says the audit
  stream's open set is #5/#14/#18/#20/#25/#26/#28 when #25 is done. It knows nothing of the linter,
  of `.ruff-ci.toml`, or of the cold audit.

  ⭐ THE ONE THAT MATTERS, and the reason this is not routine bookkeeping. The CPO asked whether
  the audit's findings were replicable or an artifact of one long session. A cold re-run of
  `/audit-agent-setup`, in a fresh context with no knowledge of the first audit's conclusions,
  answered it: **the findings replicate, the prioritisation does not.** Six major findings
  reproduced. The framing did not — the first audit produced 29 issues that all ADD; the cold run's
  first recommendation was DELETION. Same repo, same skill, opposite first move.

  The operative conclusion, which the handover must carry because acting on the wrong one cost this
  session hours: **an audit is an instrument for FINDING, not for DECIDING. Its output is a list of
  leads to verify, never a work list to execute.** Two of the cold run's four deletion targets did
  not survive checking, and it missed a third stale doc entirely.

  A cold chat reading only the old handover would find "FINISH THE AUDIT STREAM" as NEXT step 1 and
  grind through thirteen issues. Two are build items. The rest are decisions.

refs: >
  !18 (#29), !19 (#25), !20 (the CI lint backstop), !21 (delete the stale architecture plan), all
  merged 2026-08-07. Issues CLOSED: #29, #25. Issue FILED: **#30**, the cold audit re-run in full.
  CPO instruction: **"update the handover and file the audit report as an issue"**.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  THRESHOLD DECLARATIONS, stated because no gate parses this field.

  NEW MECHANISM — NO. Prose edits to one handover file.

  RECURRING COST — NO. Nothing executes. The file must stay under its 16,000-CHARACTER cap, which
  it currently sits at 2 characters below, so every addition is paid for by a deletion.

  NEW EXTERNAL SURFACE — NO.

  GUARD INVARIANT — UNCHANGED. No guard, hook, test or routing row is touched.

  WHAT IS DELETED, stated because deletion is the risk in a capped file. Only spent content goes:
  the build detail of #1's parity test and #19's compression percentage (both merged and in git);
  the per-issue note for #25 (merged); the merge list for !6-!15, collapsed to a range; and the
  ingest-cluster verification prose, tightened without losing the pacing numbers, the four fixes'
  gaps or the standing facts. No open decision, no live trap and no CPO ruling is removed.

  ⚠ THAT CLAIM HAS BEEN FALSE BEFORE in this exact file: on 2026-08-07 `scope-auditor` FAILed a
  handover task because #27 had been cut entirely while trimming to the cap, while the same field
  claimed nothing open was lost. It is checked against the file this time, not asserted — see
  `done_when`.

decisions_reserved:
  - "Whether the 16,000-character cap is the right mechanism. Every session pays a compression tax
    to add a line, and #30 names it as a MAJOR finding. Raised in two prior handover tasks and
    still not decided. The CPO's."
  - "The re-ranking of what remains. #30's evidence says the next build item should be a check that
    the contract's factual claims hold against the tree, ahead of the hook telemetry it ranked
    first. NOT decided here — this task records state, it does not re-plan the stream."

done_when:
  - "`.claude/active_work.md` is under 16,000 CHARACTERS measured with Python `len()`, and
    `handover_in.py` injects it with no truncation notice."
  - "main `290bac0`; !18-!21 recorded as merged; #29 and #25 recorded as CLOSED; **#30** present
    with its one-line conclusion that an audit finds but does not decide."
  - "The audit stream's remaining set is stated as it actually is: TWO build items, everything else
    a decision. #25 no longer appears as open."
  - "Every issue open before this edit is still present after it, VERIFIED by diffing the issue
    numbers in the file against `glab issue list` — not asserted. This is the check that FAILed on
    2026-08-07 when #27 was silently dropped."
  - "The test count is **665**, MEASURED with `pytest --collect-only -q`, never predicted. Three
    contracts in one day shipped a wrong count (#904), and #904's own recurrence count is updated
    to SIX with the rule that would have caught them."
  - "The five offline gates pass, `ruff check . --config .ruff-ci.toml` exits 0, and
    `check_task_artifacts.py` runs BARE."

amendments: (none)
