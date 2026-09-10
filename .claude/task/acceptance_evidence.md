# Acceptance evidence — dead issue references in the files that instruct

Measured with grep and pytest against the committed state.

criteria_demonstrated:
  - BOTH INSTRUCTING FILES ARE CLEAN. `CLAUDE.md` = **0** references to `#115+` (was 5);
    `.claude/active_work.md` = **0** (was 1, `#526`).
  - ⭐ THE ONE THAT MATTERED: `CLAUDE.md:32` read **"Next: player insights chain (#153 → #156)."**
    The file every session is told to read first, naming its next work as two issues that resolve to
    nothing. It now names no issue at all and points at `glab issue list`, which cannot rot.
  - THE GUARD FIRES WHEN A DEAD REF RETURNS. Mutation: re-inserted `#153` into `CLAUDE.md`'s next
    line → `assert not {'CLAUDE.md': [153]}`, 1 failed. Restored → green.
  - THE GUARD ALSO FIRES IF IT IS MADE VACUOUS. `test_the_boundary_is_not_vacuous` exists because a
    guard whose threshold sits above every real number passes on any content at all. Mutation:
    `FIRST_DEAD = 115` → `99999` → that test failed while the first one still passed, which is
    exactly the hole it covers. Restored → both green.
  - THE FAILURE MESSAGE TEACHES. It states that GitHub's tracker did not migrate, tells the reader
    to say the fact rather than the number, gives the recovery command
    (`git log --all --grep='#N'`, which finds 180 of the 257 as merged PRs), and says explicitly
    NOT to satisfy the test by deleting the sentence.
  - NOTHING OUTSIDE SCOPE IS TOUCHED. The 292 references under `docs/` are deliberately left.
  - `pytest tests/test_no_dead_issue_refs.py` 2 passed; `ruff check` clean.

## The measurement, since the decision rests on it

| | count |
|---|---|
| references to `#115+` across `CLAUDE.md` + `docs/` + memory | **767** |
| distinct dead issue numbers | **257** |
| of those, appearing in a commit message — recoverable as merged PRs | **180** |
| gone entirely | **77** |

GitLab's highest issue is **#114**, so `>=115` is the boundary. It was CHECKED rather than assumed:
`#33` in `CLAUDE.md` reads like a GitHub-era audit reference, and resolves to a real GitLab issue —
"Pipeline cost/scalability: diagnosis and ordered plan" — which is exactly what the sentence means.

## Why this is a test and not a sentence

The memory index already carries, in bold: *"any GitHub number in these files is a pointer to
nothing — re-derive from code."* That index loads every session. I read it, then followed a memory
file to "the authority is issue #753's design-state comment, trust its sections, never a summary of
them", and #753 does not exist. The warning was in place and did not work.

That is also what makes this different from the 292 in `docs/`: a reference in an archive is
provenance, a reference in `CLAUDE.md` is an instruction.

## What is NOT demonstrated

- **The 292 `docs/` references and the 470 in memory are untouched**, so most of the 767 remains.
  This branch fixes 6 and guards against new ones in the two files where a dead pointer causes
  action. Whether the rest is worth a sweep is in `decisions_reserved`.
- The guard cannot tell a LIVE `#115+` from a dead one if GitLab ever passes issue 115. At that
  point `FIRST_DEAD` has to move, and `test_the_boundary_is_not_vacuous` is what will make that a
  deliberate edit rather than a silent one.
