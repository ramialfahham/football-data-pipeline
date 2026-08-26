# Evidence — `corner_kicks` to `corners`, `goalkeeper_saves` to `saves`

Step 2 of the catalogue naming programme. Measured on this branch against merged main `2dddf38`, which is main after !111 merged.

## The headline

| | |
|---|---|
| catalogue rows | 86, unchanged |
| rows changed | 2, two fields each (`metric_id`, `label_i18n_key`) |
| formula, direction, group, tier, description, interpretation | byte-identical on both |
| generated docs blocks | **182 → 179** |
| description references repointed | **24** (12 team, 12 player) |
| dangling `{{ doc() }}` after the change | **0** |
| model SQL files changed | **0** |
| columns renamed | **0** |

## The block split, predicted before starting rather than discovered

After the rename `saves` exists for both entities with different formulas, team
`sum(goalkeeper_saves)` against player `sum(saves)`, so the generator applied its
one-name-two-meanings rule and replaced the bare `saves` block with `saves__team` and
`saves__player`. That was written into the contract before the first edit, with the reference
counts, because the same mechanism was discovered mid-flight in step 1 and forced a contract
amendment there.

Three derived blocks also dropped, and each was counted first: `corner_kicks_sum_season__team`,
`goalkeeper_saves_sum_season__team`, `opponent_corner_kicks__team`. All three had **0 references**,
so nothing dangled. 182 − 6 + 3 = 179, which is what the generator reports.

## Why no column moves

Both old names are per-match provider columns flowing up the layers, declared in
`fct_fixture_team_stats`, `int_legs__team_match`, `int_team_momentum__metrics`,
`int_team_momentum_window`, `int_team_season_record` and `mart_team_fixture_stats`. The METRICS are
season totals whose model column is `corner_kicks_sum_season` / `goalkeeper_saves_sum_season`, a
different grain under a different name. Same shape as `goals_for` in step 1.

Every remaining occurrence of both old names in the repo was listed and read: all are column names
in model SQL and yml, or the formula and description text inside the seed that refers to those
columns. Neither is a `metric_id` any more, asserted directly against the seed.

## Offline verification

| check | result |
|---|---|
| `sync_metric_docs_blocks.py --check` | OK, 179 blocks match the seed and the model YAML |
| `check_description_hygiene.py` | ok, 1604 descriptions, 241 blocks resolved, all within limits |
| `dbt parse` | clean, 0 errors, 0 dangling references |
| seed tests re-derived offline | 86 rows, 15 fields, no duplicate `(metric_id, entity)`, no duplicate `label_i18n_key`, no duplicate `(entity, label_en)` |
| `python -m pytest tests/` | 1007 passed, 1 skipped, 14 subtests |

## Mutation, watched failing

A reference pointed back at `doc('goalkeeper_saves')`, the block the rename deleted, produced a
**Compilation Error** from `dbt parse`. Restored; the reference count returned to 6.

## A transient this MR creates on purpose

`corner_kicks_per_match` is NOT renamed here, so after this merges the total reads `corners` while
its own per-match rate still reads `corner_kicks_per_match`. It is a computed column and belongs
with the eleven column renames in the next step. The alternative was dragging a column rename into
a catalogue-only diff, which is the seam this split exists to keep clean.

⚠ Found while auditing my own contract, not by a reviewer: the reserved list had said "ten column
renames" and had not named `corner_kicks_per_match` at all. Corrected to eleven before commit.

## Round 1 failed on all three reviewers, and neither defect was in the rename

**Defect 1, found by all three independently: the cited ruling was not on this branch.** The branch
was cut from main BEFORE `!111` merged, so `escalations.log` here was 5337 lines while the entry
lived at line 5352 of the 5407-line version on the `!111` branch. The record was real and
committed; this diff simply could not see it. One reviewer called it "apparently fabricated", which
is the correct reading from where it stood. Fixed by moving the work onto post-`!111` main, not by
rewording the citation.

⚠ Moving it was not a rebase: the branch had no commits, all the work was uncommitted. A first
attempt restored the work wholesale from a stash taken against the OLD main, which silently
reverted `!111`'s edits in every file both changes touch. Caught by the contract gate on
`domestic_league.yml`, then discarded and the change re-applied from its own script on the new
base. That is the "a stash snapshots the whole index" trap, hit again.

**Defect 2, found only by analytics-engineer: the per-file reference tally was wrong** in five of
nine files. Total 24 correct and every reference individually correct, but the distribution was
copied from the pre-split count and never re-measured. Re-derived and corrected in the contract.

## A correction to the approved plan's packaging

The plan bundled `sot_points_gap` with these two as catalogue-only. Measured, that is wrong: it IS
a model column, declared in `int_team_season__deserved_vs_actual` and `mart_team_profile`, so it
moved to the column-rename group. The names the CPO ruled are unchanged; only which MR carries this
one moved.
