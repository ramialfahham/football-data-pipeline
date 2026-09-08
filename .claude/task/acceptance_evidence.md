# Acceptance evidence — the handover header names the commit before its own merge

Branch `chore/handover-header`, from main `6f296f5`.

criteria_demonstrated:

  - **The header no longer pins a SHA, so it cannot be wrong on arrival.** It said
    `main b29f2e0` — accurate when written, and stale the instant `!162` merged, because a file that
    merges as a commit can only ever name its own parent. What replaces it is what a reader actually
    uses and what survives the merge: the date, the merged MR range, that nothing was open, and the
    platform.

  - **Verified against the failure it fixes.** Three consecutive handover MRs shipped a header that
    was true at write time and false at read time:

        !158  header said main 4bef954   -> merged as 81117ae
        !160  header said main 6ae4031   -> merged as 2708dff
        !162  header said main b29f2e0   -> merged as 6f296f5

    Each was correct when typed. The field is self-invalidating by construction, which is why the
    fix removes it rather than adding a reminder to update it.

  - **The range states its own bound honestly.** `!154`–`!162` are the MERGED ones; the MR carrying
    this change is not counted, because a range including its own MR is a claim about the future.

  - **⛔ AND THE REPLACEMENT INTRODUCED ITS OWN FALSE CLAIM, WHICH THE REVIEW CAUGHT.** I wrote
    *"nothing was open"* meaning no open MRs. Read plainly it says nothing is outstanding — and the
    same file, unchanged by this branch, has four sections saying otherwise: the unresolved round
    cap, the parked dbt profile MR with two open FAILs, the open-defects list (#110, #111, #109,
    #108 and more), and the DE/FI labels awaiting confirmation. It failed this contract's own bar —
    *"what it states must still be TRUE"* — in the two lines written to satisfy it.
    Corrected to *"no MR was open. Open WORK there is — see the defects and parked items below."*
    ⚠ The lesson is small and exact: I removed one self-invalidating claim and replaced it with an
    ambiguous one, in a file whose whole job is to be unambiguous to a stranger.

  - **The header now says where to look instead.** `git log -1` and `glab mr list` answer "where is
    main" and "what is open" correctly and instantly — the two questions the removed fields were
    trying to answer and could not.

  - **Two lines changed, nothing else.** No section moved, no trap touched, no content rewritten.
    15,445 of 16,000 characters, measured with Python `len()`.

## Why this is a class, not a typo

The header records state at WRITE time; the file is READ after its own MR merges. Any fact about the
repository's current position is therefore guaranteed stale by one commit. A rule that asks the
author to predict the hash they are about to create is the wrong shape — the durable fix is to stop
recording the field and point at the command that is always right.

⚠ The date, the merged range and "nothing was open" are all safe: each is a statement about a moment
that has already passed, not about the state the reader arrives in.

## What this does NOT do

- **It does not touch anything below the header.** The next action, the traps, the open defects and
  the reserved decisions are all unchanged.
- **It does not fix `#110` or build `#111`.**
