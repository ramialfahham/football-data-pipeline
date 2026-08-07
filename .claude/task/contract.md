# Task contract — handover after !15: five issues closed, four filed, one trap retired

> Branch `chore/handover-after-22-23-24` from `main` (`0394e52`). Bookkeeping. No protected path,
> so no `protected_override`. Nothing on the structural surface, so no `impact_map`. No
> `site_v2/src/` path, so no `acceptance_criteria`. A commit touching `contract.md` is NEVER
> artifact-exempt, so this still takes a scope audit.

objective: >
  Bring `.claude/active_work.md` back to current state after !12, !13, !14 and !15 merged, and
  retire one instruction in it that is now actively wrong.

  WHAT IS STALE. It says main is green at `9987184` (now `0394e52`); its merge list stops at !12;
  it says "#1 is DONE, #19 IS NEXT" when both are done and closed; its test count is 645 (now 648);
  and it knows nothing of #25 through #28.

  THE ONE THAT MATTERS. Its REVIEW MECHANICS section carries a trap I added yesterday:
  "⚠ LOCALLY THE ARTIFACT GATE NEEDS `--base gitlab/main`". That was true when written and !15
  fixed it — `check_task_artifacts.py` now resolves the live remote by itself. Leaving it would
  teach every future session to work around a defect that no longer exists, which is the same
  add-and-never-retire pattern the audit found in three other media. Retiring it also pays for the
  additions, since the file has 76 characters of headroom.

  ⚠ GITHUB IS DORMANT, NOT RETIRED. The replacement wording keeps that distinction rather than
  implying `origin` is gone.

refs: >
  Follows !12 (#1), !13 (handover), !14 (#19) and !15 (#22/#23/#24), all merged 2026-08-07.
  Issues CLOSED on the CPO's instruction *"merged, close #1 and #19 and update the handover"*:
  #1, #19, and — on the same rule, their fix having merged in !15 — #22, #23, #24. Issues FILED
  and still open: #25, #26, #27, #28.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

decisions_taken: >
  THRESHOLD DECLARATIONS, stated because no gate parses this field.

  NEW MECHANISM — NO. Prose edits to one handover file.

  RECURRING COST — NO. Nothing executes. The file shrinks.

  NEW EXTERNAL SURFACE — NO.

  GUARD INVARIANT — UNCHANGED. No guard is edited. One INSTRUCTION about a guard is retired
  because !15 made it false; the guard itself is not touched and is not in `scope_paths`.

  WHAT IS DELETED, stated because deletion is the risk in a capped file: the `--base gitlab/main`
  workaround, which !15 made unnecessary; merge/issue lines superseded by their own closure; and
  the #14-#18 issue TITLES, which are one `glab issue list` away and which this file's own policy
  says belong on the tracker. No open decision, no trap that still holds, and no live state is
  removed.

  ⚠ THAT CLAIM WAS FALSE ONCE ALREADY IN THIS TASK. `scope-auditor` FAILed round 1 because #27 had
  been cut entirely while trimming to the cap, while this very field claimed nothing open was lost.
  Restored. The claim above is now checked against the file rather than asserted, which is what
  `done_when`'s "#25-#28 present" line exists to force.

decisions_reserved:
  - Whether the 16,000-character cap is the right mechanism. Every session now pays a compression
    tax to add a line, and the file has sat above 95% of cap for four sessions. Raised in the
    previous handover task and still not decided; it is adjacent to #26 and is the CPO's.

done_when:
  - "`.claude/active_work.md` is under 16,000 CHARACTERS measured with Python `len()`, and
    `handover_in.py` injects it with no truncation notice."
  - "No instruction to pass `--base` by hand survives anywhere in the file."
  - "main `0394e52`; !12-!15 merged; #1/#19/#22/#23/#24 closed; #25-#28 present with #21, #27 and
    #28 marked as the CPO's."
  - "The test count is 648, MEASURED with `pytest --collect-only -q`, not predicted. The previous
    two contracts each shipped a wrong predicted count."
  - "The five offline gates pass, the artifact gate run BARE to exercise !15's fix."

amendments: >
  ONE amendment, 2026-08-07. NO PATH IS ADDED — `.claude/active_work.md` and `escalations.log` were
  already in `scope_paths`. What widens is the OBJECTIVE, from bookkeeping to bookkeeping plus one
  live cost incident.

  AUTHORITY: `.claude/task/escalations.log`, entry `2026-08-07 chore/handover-after-22-23-24`,
  block `⭐ CPO ESCALATION AND INSTRUCTION: THE COST INCIDENT GOES IN THE HANDOVER`. It records the
  CPO's question, the evidenced answer, and his instruction verbatim.

  WHAT WIDENED. Mid-task the CPO asked whether the warehouse had been rebuilt again. It had:
  merging !15 fired `data:build:main` because `data_paths` includes `.gitlab-ci.yml` and
  `scripts/check_*.py`, both of which !15 touched for a comment and a governance script. That is
  GitLab #2 firing in production. The handover gains a `⚠ #2 IS LIVE` block naming the mechanism
  and the file:line.

  WHY IT BELONGS HERE RATHER THAN IN THE NEXT TASK. It is CURRENT STATE, which is this file's whole
  job, and a session that does not know it will repeat it — !15 was a governance MR and it rebuilt
  prod. Leaving it out and fixing it later would mean the next governance MR does the same thing in
  the meantime.

  BOUNDED: this RECORDS the incident. It does not fix #2, does not touch `data_paths`, and does not
  decide what to do about it. That is the next task and is not authorised by this amendment.

  ⚠ THE PROCEDURE, not just the content: this entry and this block were written in the SAME action,
  which is the class fix recorded at `escalations.log` for the four prior instances. `scope-auditor`
  FAILed round 2 because the widening happened before either existed — the fifth instance. It was
  right every time, and the count is the point: four fixes that each added one missing entry did not
  change the behaviour, and only writing them together does.

  SECOND AMENDMENT, 2026-08-07, same procedure: the `escalations.log` blocks and this block were
  written together, before the handover edit they authorise. NO PATH IS ADDED.

  AUTHORITY: `.claude/task/escalations.log`, same entry, blocks `⭐ CPO RULING: TWO STREAMS, AND
  THEIR ORDER`, `⭐ CPO RULING: THE MEASUREMENT STOP IS LIFTED` and `⭐ CPO CORRECTION: FILING TO
  THE TRACKER IS STANDING PRACTICE`.

  WHAT WIDENED. The CPO ruled at the end of the session that the AI-collaboration audit stream is
  NOT finished and is to be completed in a new chat BEFORE the cost work, and separately lifted the
  2026-08-06 measurement stop for that cost work. The handover's `NEXT` section is rewritten to
  carry both, because a ruling about what to do next that does not reach the handover does not
  reach the next session — which is the continuity failure this repo keeps having.

  BOUNDED: it records the order and the lifted stop. It starts neither stream, runs no measurement
  (the CPO stopped the run and deferred it), and decides nothing about cost.
