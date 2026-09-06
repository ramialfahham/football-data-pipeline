# Acceptance evidence — the current-season pick and the board DQ guard (#40, warehouse half)

Branch `feat/40-leaderboards-current-season-and-board-dq`, from main `8af4b45`.

⚠ **THIS IS HALF OF #40.** The split is recorded in `.claude/task/escalations.log`, entry
`2026-09-04 — feat/40-leaderboards-current-season-and-board-dq — SPLITTING #40`, which carries the
three options put to the CPO, which one he chose, and what he explicitly did NOT rule. Cited here
rather than restated.
⛔ This sentence previously asserted "SPLIT ON THE CPO'S CALL" with nothing behind it.
`scope-auditor` FAILed that in `contract.md` (round 1), I corrected it THERE and left it standing
HERE, and round 2 failed the residue. Fixing the instance a reviewer names instead of sweeping the
class is its own logged failure (`feedback_fix_the_class_not_the_instance`) and it happened inside
the fix for an attribution failure.
The reason for the split: the block cannot render until this column is in prod (merge + the 04:00
nightly), so shipping the export and component alongside would have left their criteria
undemonstrable. The export, component, player scaffold and copy are BUILT and PARKED in the stash
`TEMP-40-mrB`.

Everything below is measured against **LIVE PROD DATA** by compiling the model and running it
read-only. The ban is on `dbt build`, which writes and bills a materialisation; a SELECT over the
compiled SQL is neither. Same approach `!145` used.
⚠ The compiled SQL exceeds Windows' command-line limit ("Die Befehlszeile ist zu lang"), so every
query is fed to `bq` on **stdin**. Recorded because the first attempt failed on it.

criteria_demonstrated:

  - **`is_current_season` is true for exactly one season per league, on prod.** 45 leagues, 45 with
    exactly one flagged season, **0 violations**. Measured, not read off the SQL.

  - **It is true for EVERY row of that season, not one row of it.** This is the criterion that
    separates `rank()` from `row_number()`, which look interchangeable here:

        BL1  2026   flagged 712 of 712 rows   ALL
        PD   2026   flagged 792 of 792 rows   ALL
        PL   2026   flagged 832 of 832 rows   ALL

    With `row_number()` each would read `1 of 712`, and a consumer filtering on the flag would get
    one player per league across ALL FOUR boards instead of one per league per board.

  - **The column changes nothing else.** Row count of the LIVE table vs the compiled model carrying
    the new column: **189,116 and 189,116**. Additive, as the impact map claims.

  - **Every home board has a rank-1 in every elite league, today.** The guard's own predicate run
    over prod: **0 missing (league, board) pairs** across 4 boards × the elite group.

  - **`assert_one_current_season_per_league` is RED under all three mutations**, measured on prod,
    and GREEN unmutated:

        healthy model                                        GREEN (0 rows)
        MUTATED: order asc (flags the OLDEST season)         RED   (34 rows)
        MUTATED: two seasons flagged (dense_rank <= 2)       RED   (34 rows)
        MUTATED: row_number (one ROW flagged, not a season)  RED   (45 rows)

    ⛔ **The third was GREEN until `analytics-engineer-reviewer` FAILed the test for missing it**,
    and it is the mutation the whole design rests on. See below.

  - **`assert_mart_leaderboards_every_home_board_has_a_leader` is RED under both**, GREEN unmutated:

        healthy model                          GREEN (0 rows)
        MUTATED: the Assists board vanishes    RED   (7 rows)   <- the failure the page hides
        MUTATED: no rank-1 anywhere            RED   (28 rows)

  - **`dbt parse` exits 0 and SQLFluff exits 0** under the dbt templater CI actually uses, run from
    `dbt_project/` with the venv's Python. ⚠ Both exit codes read BARE, never through a pipe — the
    repo's own rule, and the local `--templater jinja` run is NOT the check (it reports
    `dbt_utils`-unresolvable TMP/PRS noise on this model that CI does not see).

## ⛔ Mutation testing changed the shipped code, twice

**1. It proved my own guard was weaker than its name.** `assert_one_current_season_per_league`
originally asserted only HOW MANY seasons carried the flag. Flipping the window's `ORDER BY` to
ascending flags the OLDEST season — still exactly one per league — and the test stayed **GREEN**.
The block would have shown last season's leaders under a heading reading "Season totals to date",
and nothing else in the repo would have noticed. The test now also asserts the flagged season is
`max(season_api_year)`; that mutation now fails with 34 rows.

**2. It caught a mutation of mine that tested nothing.** My first attempt mutated `rank() = 1` to
`rank() <= 2` expecting two flagged seasons. It is INERT: `rank()` skips, so every latest-season row
shares rank 1 and the next season's rank jumps far past 2. Had I not checked the result, I would
have recorded a "surviving mutation" that never mutated anything. `dense_rank() <= 2` is the form
that actually flags two seasons.

**3. And a reviewer found the gap BOTH of my mutations left.** `analytics-engineer-reviewer` FAILed
the test by reading it rather than running it: revert the model's `rank()` to `row_number()` and
exactly ONE row per league carries the flag, yet `count(distinct flagged season)` is still 1 and
that row's season is still the max — so cardinality-plus-recency stayed **GREEN while the flag was
false on 711 of 712 rows.** It also noted the board-leader test only covers the 6 `elite` leagues,
so it gave no cover for the other 39.

⛔ **That is the mutation this contract itself calls the whole reason for choosing `rank()`** — and
I had not run it. I ran the two I thought of (ascending order, two seasons) and neither changes the
season SET, which is the only thing the test could see. The test now also asserts a flagged season
is flagged ENTIRELY (`flagged_rows = season_rows`), and `row_number()` fails it with 45 rows.

⭐ All three are the same lesson in different clothes, and it is the one `!151` ended on: **a
mutation that cannot distinguish two implementations tests neither of them.** Verifying that a
guard fails is not enough — the mutation has to be capable of changing the answer, and the
mutations worth running are the ones the design is defended against, not the ones that come to mind.

## What this does NOT do

- **Nothing renders.** No consumer reads the column yet — the export reads this mart but not this
  field, by design. The frontend is byte-identical.
- **It does not ask whether a season has STARTED.** "Latest" is by `season_api_year` alone. #101's
  in-season gate (">= 3 finished games") is a group-level question for the rotation MR, and
  conflating them would bake a rotation rule into a column that answers a simpler question. A league
  whose latest season has not kicked off is therefore "current" and its boards are empty — which #40
  already rules is simply not rendered. Recorded in `decisions_reserved` as a real question for that
  MR, not a defect here.
- **It does not verify the block.** Four boards rendering, no truncation at 375px, per-board
  stacking, links resolving — all MR B's, on data that does not exist until the nightly runs.
