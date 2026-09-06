# Review — feat/40-leaderboards-current-season-and-board-dq — 2026-09-04

diff_sha256: f090d023545a5a9556e22737caa4300e8659270255da10e5b75e095edd95b869

rounds: 4

rounds_cap_override: >
  CPO, 2026-09-04, when the gate stopped the commit and the position was put to him — both
  reviewers PASS, nothing open, and a round-by-round account of what each round was spent on:
  *"go ahead, all rounds were fixes not disagreements"*.
  ⚠ That is the distinction the cap exists to test, so it is worth stating what it means here. The
  cap guards against LOOPING — the same finding re-argued, or reviewers and builder disagreeing
  about whether something is a defect. Neither happened. Every round accepted its finding in full
  and fixed it: an unrecorded ruling (round 1), the same claim left standing in the sibling artifact
  (round 2), a guard that would have passed a broken model (round 3), and a re-run because the code
  moved after a verdict (round 4). Round 3 alone justified the budget: it was a real code defect in
  the exact property this change exists to guarantee.

⚠ **ROUNDS DIFFER PER REVIEWER AND THAT MATTERS HERE**: `scope-auditor` 4, `analytics-engineer-reviewer` 2.
Both PASS at the hash above. The analytics verdict was obtained at `3beb10f…`; the only change since
is one `contract.md` paragraph fixing a model citation IT raised, and `scope-auditor` re-read the
whole diff at `f090d02…` afterwards. Recorded rather than implied.

⚠ **THE CODE FAILED REVIEW ONCE AND IT WAS THE MOST VALUABLE FINDING OF THE BRANCH.** Every other
FAIL was my prose. See the closing note.

## scope-auditor
VERDICT: PASS
risks_checked:
- `assert_one_current_season_per_league.sql`'s new `partly_flagged_seasons` predicate matches the
  briefed change exactly — groups to (league_code, season_api_year), fails when a flagged season is
  not flagged entirely; no unrelated logic smuggled in.
- Attribution language in the `decisions_reserved` correction and the test's own header: both credit
  `analytics-engineer-reviewer` for finding the gap, not the CPO and not my own insight. Checked
  specifically against the five-instance pattern this session logged; this delta adds no sixth.
- `scope_paths`: both delta-touched files were already listed, so `amendments: (none)` is honest and
  no path was touched that needed one.
- The split citation and the DE/FI item: one cites a real logged ruling by exact key, the other is
  still marked as pending the CPO — neither smuggled in as decided.
- Acceptance criteria unchanged in substance. The criterion "fails when the flag is made per-player"
  PREDATES the new predicate, and the predicate is what finally makes the test satisfy it — the
  criterion was not loosened to fit the test, which is the direction that would have been a defect.
- Credentials sweep of the delta; threshold declarations unchanged and still accurate (one more SQL
  predicate, no new mechanism, no recurring cost).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Traced the row-completeness predicate BY HAND against a `row_number()` model rather than trusting
  the description: confirmed it cannot stay green (`flagged_rows=1`, `season_rows>1` fires for every
  league with more than one row), and confirmed the healthy model passes all three predicates.
- Checked it for FALSE failures: a league whose latest season legitimately has one row
  (`flagged_rows == season_rows == 1`, not counted as partial); `is_current_season` derives from
  `rank()=1` and is never NULL, so `countif` behaves as a plain boolean count.
- Worked through further hypothetical defects — stuck-true, stuck-false, dropped `partition by`, two
  full seasons flagged, extra rows flagged in an unrelated season — all caught by the three
  predicates together.
- Searched for a FOURTH weakness and reported plainly that it found none, rather than manufacturing
  one to justify a verdict.
- Verified the board-leader test's `elite`-only scope against `10_home.md:225,247` and the registry:
  the blocks render `elite` only, so the scope tracks the render surface rather than convenience.
  ⚠ It corrected my count — **7** elite leagues (BL1, PL, PD, SA, L1, LP, ED), not 6. The error was
  in my review prompt; the evidence arithmetic (28 = 7 × 4) was already right.
- Re-traced the `decisions_reserved` finished-matches claim through `int_player_club_season__metrics`
  and `int_player_season__metrics` and confirmed the conclusion holds transitively.
- Checked every mutation count in the evidence for internal consistency against 7 elite leagues, 4
  boards and 45 total leagues — 28 / 7 / 45 / 34 / 34 all reconcile; no arithmetic overclaim.
- Confirmed the diff is additive only: one boolean column, two new test files, no other model or
  existing test touched, no hardcoded league identifier, no new metric needing catalogue
  registration.

## escalations
(none)

⭐ **THE ONE FINDING THAT CHANGED THE PRODUCT, and it was found by reading, not running.**
`analytics-engineer-reviewer` FAILed round 1 because `assert_one_current_season_per_league` asserted
how MANY seasons carried the flag and WHICH one, but never that the flagged season was flagged
ENTIRELY. Revert the model's `rank()` to `row_number()` and exactly one row per league is flagged —
the distinct-season count is still 1, that row's season is still the max — so the test stayed GREEN
while the flag was false on 711 of 712 rows. That is the mutation this contract itself calls the
whole reason for choosing `rank()`, and I had not run it: I ran the two that occurred to me
(ascending order, two seasons flagged), and neither can change the season SET, which is the only
thing the test could see.

⚠ Same shape as `!151`'s closing lesson, one level deeper. There, a fixture that could not
distinguish `max` from `min` tested neither. Here, a guard that could not distinguish `rank` from
`row_number` guarded nothing — and I had verified it "fails under mutation", truthfully, against
mutations that were never going to catch it.
