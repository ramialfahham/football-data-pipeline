# Acceptance evidence — the freshness guard is fixed; point the handover at what is left

Branch `chore/handover-freshness-done`, from main `6ae4031`.

criteria_demonstrated:

  - **The freshness guard is gone from the next actions and appears nowhere as unfixed.** It was
    candidate (a) of two, with a paragraph arguing it should be taken first. `!159` did that, so the
    entry is REPLACED by one sentence of what changed in prod, in the section that already exists for
    that — not annotated as done, because a struck-through line is still a line to read.

  - **The top of the file is now two sentences**: build #40 MR B, and #110 is blocked on the CPO.
    Everything else moved below. That is a direct response to *"you all constantly flooding the zone
    with shot"* and *"you expecting me to remember that? or even understand what it is about?"* —
    both said today, the second after I put four paragraphs of round-cap process in front of him.
    ⭐ The handover now carries that warning explicitly, so the next session starts with it rather
    than learning it the way I did.

  - **Header facts re-derived**: `main 6ae4031` from `git log gitlab/main`, "no open MRs" from
    `glab mr list` after `!159` merged, and the range `!154 through !159` from the merge commits. The
    previous version said `4bef954` and named four MRs — true when written, wrong by two merges now.

  - **Nothing dropped for space; history compressed instead.** The `!156`/`!157` prod paragraphs are
    cut to two sentences each, and the lessons section is merged and re-pointed at the three MRs it
    now covers. Every trap survives — the incremental-fact trap, the diff3 fourth marker, CP1252, the
    `--review-patch` redirect, the push guard on main, the `criteria_demonstrated:` column-0 parser.

  - **⚠ THE LENGTH CRITERION WAS WRONG AND IS CORRECTED, NOT QUIETLY MET.** It said the file must be
    SHORTER than the 12,198 it replaces. It is **14,492 of 16,000**. Compression did happen, but this
    update adds state that did not exist before: `!159`'s outcome, `#110` written out so a cold
    session need not reconstruct it from an issue tracker, and the communication warning. Getting
    under 12,198 would have meant deleting warnings, which this contract's own `decisions_taken`
    forbids. Recorded because a criterion silently dropped is exactly what reviewers caught twice on
    `!159`.

## What this does NOT do

- **It does not decide #110** — it states the question and the 463-team-season consequence so the
  next session can put it to the CPO in two sentences instead of rebuilding the analysis.
- **It does not resolve the round cap.** `!156` reached round 9 and `!159` round 4; the handover now
  says to write an honest override and carry on rather than ask him again.
- **It touches no code.** One tracked document plus the task artifacts.
