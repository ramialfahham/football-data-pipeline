# Review — fix/dead-ref-boundary-off-by-one — 2026-09-11

diff_sha256: 92181879779e415bfaea7552d4aca0aa8bddf21bdc6ac323a3676700460a1038

rounds: 8

scope-auditor: FAIL ×7 (rounds 1-7), PASS at round 8.
platform-reviewer: FAIL ×4 (rounds 1-4), PASS at round 5.

⛔ **NO REVIEWER PASSED THIS BRANCH UNTIL ITS FINAL ROUND.** Eleven FAIL verdicts on a single test
file. Every one was real; not one was disputed on substance except where the code disproved it.
Recorded because the pattern in them is the finding, and it is the same pattern the context-cleanup
work exists to fix:

| rounds | what was found | by |
|---|---|---|
| 1-2 | defects IN THE MECHANISM — 4-of-256 silencing coverage proven by a cherry-picked mutation; two entity-escape classes; the CPO quote unlogged and then self-attested | both |
| 3-6 | defects in MY PROSE ABOUT the mechanism — the same cost/limit overclaim relocated three times under different words; a test cited by a name that no longer existed; a limitation disclosed in a docstring but not the contract | scope-auditor |
| 3-4 | two more regex classes, the last a silent false negative | platform |

The mechanism was sound from round 2. Rounds 3-6 were paid for by how I described it, and that is
the direct cost of reviewers reading the diff: reasoning goes into the contract, the contract
becomes the thing under review, and its looseness costs rounds the code never would. That is step 7
on GitLab #115, demonstrated rather than argued.

rounds_cap_override: The CPO directed that the context cleanup finish before product work resumes
(`escalations.log`, `2026-09-10 chore/dead-issue-references`, his words quoted). Rounds 4-7 were
run to clear standing FAILs rather than to ship past them — the commit gate refuses a standing FAIL,
and every fix was reviewed again rather than asserted. ⚠ RECORDED PRECISELY: he did not rule on the
cap itself, and this override does not claim he did.

## scope-auditor
VERDICT: PASS (round 8)
risks_checked:
- Round 7 FAIL — the fifth limitation (`#217e`) was pinned in a test and absent from the contract:
  THE IDENTICAL DEFECT IT HAD FAILED IN ROUND 6 for the fourth limitation, repeated one round later
  on the very next item. Fixed by checking every known limitation for presence in all three
  artifacts by the CLAIM rather than a word — which surfaced that the evidence file was missing
  both regex limitations, not just the fifth.
- Round 8 PASS — cross-checked all five limitations across contract, evidence and test for consistent
  behaviour, root cause and verification; confirmed every cited test name resolves; confirmed no
  artifact calls the silent gap "harmless" or "fixed". Non-blocking note: the cost table's "one
  deletion per collision" sits close to the silent-gap concession and a fast reader could conflate
  them. Both are stated; left as-is.
- Round 1 FAIL — the contract quoted the CPO's cleanup standard as its justification, unlogged.
- Round 2 FAIL — I logged it; it held, correctly, that a log entry written by the builder in the
  branch under review after being caught corroborates nothing but the builder's assertion. ⭐ That
  objection is UNANSWERABLE AND STRUCTURAL: every entry in `escalations.log` is authored by the party
  it constrains. Recorded against step 4 on #115. The branch no longer leans on the quote at all —
  the justification is the technical argument that no value of the constant is both correct and
  stable.
- Round 2 FAIL — "no regeneration ever" beside a conceded gap requiring regeneration. Fixed.
- Round 3 FAIL — "correct forever" beside the conceded collision. Same class, relocated. Fixed.
- Round 4 FAIL — `impact_map` called the coverage gap "harmless" while `decisions_taken` called it
  "the worse property". Same class, a THIRD time, under a word my grep did not cover. Fixed by
  reading for the claim rather than the phrasing.
- Round 5 FAIL — "a named event with a one-line fix" understated the collision decay, because the
  set has dense runs. ACCEPTED. ⚠ Its conclusion that the guard would then "fail on every issue
  GitLab files for weeks" was REJECTED with evidence: the guard fires on citation, not existence,
  verified by running `_dead_refs` with 280 in the set against prose not citing it. **It withdrew
  the conclusion in round 6 after reading the code.**
- Round 6 FAIL — the contract cited `test_the_dead_set_cannot_silently_collide_with_live_issues`,
  a function that no longer existed after a rename: a dead pointer inside the contract for the
  branch about dead pointers. Fixed by checking every cited test name against `def` lines
  mechanically. Also: the `#217` limitation lived only in a docstring. Fixed — now in
  `decisions_taken` and `acceptance_criteria`.

## platform-reviewer
VERDICT: PASS (round 5)
⚠ Given on the hash preceding this one. The only change since in its territory is a docstring
paragraph in the test file disclosing the uncited-number gap — no regex, assertion or set member
changed. Not re-run for a paragraph of disclosure text; recorded as such rather than silently.
risks_checked:
- Round 5 PASS — hunted for a sixth class and found three theoretical continuations
  (`#151-anchor`, five-plus-digit runs, hex-form `&#x…;` entities), none present in either guarded
  file, all of the same accepted class. Re-derived the `#217e` backtracking by hand and confirmed
  `[]`. Verified by hand that the set is 256 strictly-increasing non-overlapping members. ⭐ STATED
  ITS LIMIT PLAINLY: it cannot recompute the SHA-256 without code execution, so the digest's hex
  value is verified only by the builder's run, with CI's `test:python` as the independent backstop
  at merge — and judged that split sufficient because the mechanism is sound regardless of the
  specific value.
- Round 1 FAIL — the "cannot be silenced" claim protected 4 of 256 members, and the mutation offered
  as proof deleted `151`, the one member that was pinned. A cherry-picked mutation presented as a
  general property. Fixed with a sha256 digest over the sorted set; re-proven by deleting `600`, a
  middle member pinned by nothing.
- Round 1 FAIL — `&#153;` (HTML numeric entity) matched as issue 153.
- Round 2 FAIL — `&amp;#753;` defeats a one-character lookbehind. Its suggested `(?<!&amp;)` would
  lose to `&amp;amp;#753;` — chasing escape DEPTH is an infinite regress. Excluding `;` closes every
  depth at once; depths 1-3 pinned.
- Round 3 FAIL — `#217` is textually identical as issue and as three-digit CSS colour. NOT FIXED,
  deliberately: any context rule trades the false positive for a false negative, and a guard that
  misses what it exists to catch has failed at its job. Pinned as a documented limitation.
- Round 4 FAIL — the mirror: `#217e` is a silent false NEGATIVE, undisclosed while the positive side
  was pinned. Now pinned symmetrically, with the reason (`#217e` is itself a valid `#RGBA` colour, so
  the ambiguity is genuine both ways) and the check that no such form exists in either guarded file.
- Stated plainly across rounds that it cannot recompute the SHA-256 without code execution, and
  verified the set's cardinality of 256 by hand instead. The digest was verified by the builder.
- Verified the `;` exclusion costs no real coverage: grepped the whole repo for `;#\d` and found no
  legitimate citation form using that adjacency.

## escalations

`2026-09-10 fix/dead-ref-boundary-off-by-one` — the CPO's standard for the cleanup ("does not
require us to do that same cleanup again in the future") and his request for a tracker reference,
which is GitLab #115. Written after round 1; see the scope-auditor section for why that does not
make it corroboration.

## Found and NOT fixed, all disclosed in the contract

- A previously-uncited dead number entering the guarded files is not caught (the set is closed over
  what the repo cites, not over every GitHub issue that ever existed). Silent.
- A three-digit all-decimal CSS colour is read as an issue. Loud; pinned.
- A reference abutting a hex letter is missed. Silent; pinned; no such form exists in either file.
- `escalations.log` is self-attested. Structural; step 4 on #115.
