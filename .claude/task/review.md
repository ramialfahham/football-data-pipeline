# Review — chore/handover-header — 2026-09-08

diff_sha256: 60f79af64d49efaab11328122424aee7c78c2a06a9d3e203e6566d8b29c4dd6a

rounds: 2

⚠ **BOOKKEEPING MR, reviewed proportionately** (`feedback_review_cost_discipline`): two lines of one
document plus task artifacts, no code. `scope-auditor` is the only routed reviewer.

## scope-auditor
VERDICT: PASS (round 2)
risks_checked:
- ⛔ **ROUND 1 FAILED ON A CLAIM I INTRODUCED WHILE REMOVING ANOTHER ONE.** The replacement header
  said *"nothing was open"* — I meant no open MRs; it reads as nothing outstanding. It cited four
  sections of the same file, unchanged by this branch, that say otherwise: the unresolved round cap,
  the parked dbt profile MR with two open FAILs, the open-defects list, and the DE/FI labels
  awaiting confirmation. ⭐ It failed it against **this contract's own bar** — *"what it states must
  still be TRUE"* — rather than against an external rule, which is the sharpest form of the finding.
- **ROUND 2** re-checked the corrected text against all four of those sections and found the
  contradiction resolved rather than papered over: *"no MR was open"* is narrower and checkable (the
  profile work is a stash on an unpushed branch, not an open MR), and *"Open WORK there is"* now
  matches the file's own open-items sections.
- Confirmed the durability bar: the header is phrased as a dated historical claim, so it survives
  its own merge — which the removed SHA could not, by construction.
- ⭐ **It refused the delta shortcut.** Because round 1 was a FAIL rather than a PASS, it re-read the
  contract in full instead of treating its earlier clearances as given, and re-derived the
  SHA-removal argument, the MR range, the scope and the attribution question.
- ⚠ It tested the one thing that could still have been false — whether *"see the defects and parked
  items below"* is wrong because the DE/FI caveat sits under NEXT ACTION rather than under those
  headings — and ruled it an orientation pointer, not a claim of exhaustive coverage.
- Scope, credentials and `scope_paths` clean.

## ⛔ WHAT THIS BRANCH SHOULD BE REMEMBERED FOR

**1. The header field was self-invalidating, not mistyped.** It records state at WRITE time and is
read after its own merge, so the SHA it names is always its own parent. Three consecutive handover
MRs proved it: `!158` said `4bef954` and merged as `81117ae`; `!160` said `6ae4031` and merged as
`2708dff`; `!162` said `b29f2e0` and merged as `6f296f5`. Each correct when typed. The fix is to
delete the field and point at `git log -1`, not to remember harder.

**2. I replaced a wrong claim with an ambiguous one, inside the two lines written to fix it.**
"Nothing was open" was shorter than "no MR was open" and meant something else. In the one file whose
job is to be unambiguous to a stranger who has no context, brevity that costs precision is not
brevity.
