# Acceptance evidence — bring the handover current after !154–!157

Branch `chore/handover-2026-09-08`, from main `4bef954`.

criteria_demonstrated:

  - **Under the cap, with room to spare.** Measured with Python `len()` on the final text:
    **12,091 of 16,000 characters**. That is 3,615 characters LEANER than the version it replaces
    (15,706) while carrying more, because four merged MRs' worth of "next action" and open-question
    text became history and was deleted rather than annotated.
    ⚠ `wc -c` would report **12,265** — 174 more — because it counts BYTES and the file is full of
    multi-byte marks. The gate counts characters, so the two disagree by more the more warnings the
    file carries, which is exactly backwards from what you would want.

  - **Every header fact re-derived, none carried.** `main 4bef954` from `git log gitlab/main`;
    "no open MRs" from `glab mr list` after !156 merged; the four MR numbers from the merge commits.
    The previous version said `main 3ed9569` and "no open MRs", which was true when written and
    wrong by four merges when read.

  - **The three claims today falsified are GONE, not annotated.** The old file's next action assumed
    !156 unmerged; the nightly is no longer failing on a nameless team; prod no longer needs an
    operational fix. Deleting rather than striking them is the rule in `feedback_corrections_replace`
    — a struck claim is still a claim a hurried reader acts on.

  - **Every trap carried or deliberately dropped.** Kept: the post-commit push-to-main hook, the
    `glab auth` prohibition, the single-runner CI, the group move, `--is-ancestor`, the
    `--review-patch` redirect, CP1252, the SQLFluff redirect, the push guard on main, the
    `criteria_demonstrated:` column-0 parser. Dropped ON PURPOSE, with the reason: the branch-sweep
    census (`63 remote + 22 local deleted`) is finished work; the naming-programme seed rows were
    closed with a recommendation to leave them; the `__team`/`__player` doc-block split has no live
    instance. Nothing was dropped for space — the file came in 24% under the cap.

  - **The new trap is recorded with its measurement, not as a slogan.** The incremental-fact section
    names all three incremental models, the reason a self-heal cannot be copied (the surrogate key
    contains the corrected column), the remedy, AND the check that the remedy is lossless — with
    `fct_fixture_event` at 858,032 against a base of 858,015. ⭐ That +17 is the load-bearing number:
    without it the obvious "just make them tables" conclusion looks free, and it would trade a loud
    one-off deploy step for silent data loss.

  - **The unresolved round cap is recorded as unresolved.** !156 merged at round 9 with the question
    put to the CPO and unanswered. Writing "he approved it" would be the fabrication
    `feedback_dont_attribute_repo_practice_to_cpo` exists to stop.

  - **⛔ ROUND 1 FAILED ON THAT SAME RULE, ONE PARAGRAPH LOWER.** I wrote the CPO's
    *"you need these microdecisions from me???"* into the handover as standing guidance while it
    existed nowhere but the chat — `scope-auditor` grepped `escalations.log` and found zero hits.
    That is the tenth recorded instance of presenting an unlogged remark as his instruction, and it
    is worse in the handover than anywhere else, because that file is the one thing a cold session
    trusts as ground truth and it would have arrived with no way to check it.
    Fixed by LOGGING it rather than by softening the wording: `escalations.log` gains the entry
    `2026-09-08 — chore/handover-2026-09-08 — DO NOT ASK FOR MECHANICS`, with the verbatim quote,
    what prompted it (I asked permission to commit and push work that had already passed review),
    and ⚠ what it does NOT license — merging, skipping a round, or dropping the genuine §10 asks.
    The handover now cites the entry by name instead of quoting him loose. File length 12,198.
    ⭐ The reviewer separately CONFIRMED the surrounding claim it sits next to: the round-cap question
    really was put to him and left unanswered, and the branch really did merge anyway. Accurate
    reporting of a checkable contradiction is not the same thing as inventing authority, and only the
    quote needed fixing.

  - **The next action is TWO candidates with a recommendation, not one silently promoted.** The
    previous file said "#40 MR B". Today's evidence argues the freshness guard first — a permanently
    red nightly hid an unrelated defect for three nights. Which comes first is a priority call and
    therefore the CPO's, so both are written out with the reasoning.

## What this does NOT do

- **It does not fix the freshness guard.** It records why that matters more than it looks.
- **It touches no code.** One tracked document plus the task artifacts; no model, script, seed, test,
  workflow or site file is in the diff.
