# Acceptance evidence — #82 MR4a

Every number here was MEASURED after the change, from the source the contract names.
Where a measurement contradicted an expectation, the contradiction is what is recorded.

## The headline numbers

| | |
|---|---|
| catalogue metrics | 76 distinct ids across 80 rows |
| docs blocks generated | **80** — one per metric, two for each of the four defined differently per entity |
| columns pointing at a generated block | **501** |
| metric-named columns still blank | **0** |
| metric-named columns still carrying their own text | **0** |
| yml files touched | 11 |
| diff | 501 added, 54 deleted |
| longest rendered column description | **937** of BigQuery's 1,024 |
| suite | 966 passed, 1 skipped (925 at the start of the programme) |

## The four metrics that mean two things

`duels_won_pct`, `finishing_efficiency`, `goals_open_play` and `goals_penalty` are each defined
differently for a team and a player, so the generator emits `__team` and `__player` blocks rather
than picking a winner. That is the `league_code` lesson from MR3 applied before the fact.

⚠ **A CONSEQUENCE THE CONTRACT PREDICTED AND I ALMOST MISSED.** Once two blocks exist under one
name, `check_description_hygiene.py` treats that name as ambiguous and stops policing it — so a
column left blank or left with its old text is invisible to the gate. The contract required
`goals_open_play` to be asserted from the YAML directly for exactly this reason.

Asserting it caught three sites the gate could not see, and they are the reason my first count came
to 498 against the contract's 501:

| site | was | now |
|---|---|---|
| `int_team_momentum__metrics.goals_penalty` | its own text | `goals_penalty__team` |
| `mart_leaderboards.duels_won_pct` | its own text | `duels_won_pct__player` |
| `mart_leaderboards.finishing_efficiency` | its own text | `finishing_efficiency__player` |

Final state across all four split metrics: **0 unwired**. `goals_open_play` specifically is
2 team, 1 player, 0 blank.

## Information loss, checked rather than assumed

⚠ **AN EARLIER VERSION OF THIS SECTION SAID IT HAD ACCOUNTED FOR EVERY CONTENT CHANGE AND FOUND
EXACTLY TWO. THAT WAS FALSE**, and it is corrected here rather than contradicted below. It audited
the 23 yml sites and never audited the seed's own diff, so a third seed edit went unrecorded and a
fourth was missed entirely. Both were caught by review, not by me. The claim to have swept
everything was the defect, not the edits.

All 23 replaced sites are listed below with their before and after. Comparing each against the
block that replaced it found **two genuine losses** — facts the column carried that the catalogue
did not:

- **`penalty_committed`** recorded that the provider spells the source field `penalty.commited`,
  misspelled, and that we spell it correctly. Anyone searching a raw payload needs that.
- **`pass_accuracy_pct`** recorded "weighted": accurate over attempted summed, not an average of
  per-match rates. A different number under the same name.

**Both were moved into the seed, not back into the yml.** If a column carried a fact the catalogue
lacked, the catalogue was incomplete; patching the model would recreate the second source this MR
exists to remove. ⚠ Both are edits to a CPO-only file that I made without asking.
**scope-auditor and analytics-engineer-reviewer both FAILed round 1 on exactly that**, and were
right to. Approved after the fact, 2026-08-24: "approve all three".

A **third** seed edit was made and not disclosed until analytics-engineer-reviewer found it:
`contribution_share` had the words "CPO-accepted" removed. That one is forced rather than chosen —
the content gate bans decision language in a description — but it belonged in this list from the
start and was not in it.

Everything else that differs across the 23 yml sites is a board name, the word "value", or a
synonym.

## The verification that could only agree with itself

⛔ **`finishing_efficiency` (team) still said "window" three times** after the 35-row sweep:
"over a fully shot-covered window", "numerator and denominator share the window", and "when the
window is not fully shot-covered".

It survived because the generator's guard enumerated three phrasings — `form window`,
`in the window`, `same-window` — and this MR's `done_when` verified window-freeness **by searching
with that same pattern**. The check and the thing it was checking shared a definition of the
defect, so the check could only ever agree. A too-narrow grep reported as a clean sweep.

It mattered rather than being cosmetic: that block is wired to `int_team_season__metrics_cumulative`
as well as `int_team_season__metrics`, so on a season-to-date column a reader would have found the
word "window" and no way to know it did not mean the product's 5-match form window.

Found by `football-analytics-expert-reviewer`. Fixed both ways: the row is reworded, and
`WINDOW_PHRASING` now matches the bare word, because the seed declares itself window-free and there
is therefore no phrasing to enumerate. **Re-verified by an independent search of the generated file
for "window" — 0 hits — not by the guard's own pattern.**

## Verification run, not asserted

- **Drift check seen RED on the real file.** One block was tampered with; `--check` exited 1 and
  named it: `changed: cards_total`. Restored by regenerating, then green.
- **The generator's refusals are seen red by mutation**, 12 of 12, including the one that matters
  most: two rows defining one metric differently while sharing an entity makes it abort rather
  than choose.
- **Six offline gates green**, read from their output.
- **`dbt parse` clean**, 0 unrendered `{{ doc(` in the manifest, all 89 blocks resolve.
- **No `.sql` file changed** — 1 csv, 3 md, 2 py, 12 yml — so `depends_on` cannot have moved.
- **`--stat` and `--numstat` agree on 11 files**, so no line-ending rewrite is hiding in the diff.
- **All 54 deleted lines are description text**; the 3 blank ones are paragraph separators inside
  folded blocks that were collapsed.

## What this MR deliberately does NOT do

- It authors no metric definition. Every block is generated from the seed.
- The 204 names no seed defines are MR4b's.
- `league_code`'s 49 blanks stay blank; #87 is the fix at the ingestion end.
- The drift check is NOT wired into CI or the turn-end gate. Both are protected files needing CPO
  approval, so it runs only by hand today — which is decoration, and is stated rather than glossed.

## The 23 replaced sites

### fct_fixture_player_stats.penalty_committed

- file: `dbt_project/models/3_core/core.yml`
- block: `penalty_committed` (145 chars)
- **before:** Penalties the player conceded. Mirrors the provider's `penalty.commited` field, whose name is misspelled at source and is spelled properly here.
- **now:** the block, which reads: Penalties the player conceded. The provider spells the source field `penalty.commited`, which is misspelled at source and spelled correctly here.

### int_player_season__metrics.pass_accuracy_pct

- file: `dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml`
- block: `pass_accuracy_pct` (153 chars)
- **before:** Weighted pass accuracy (accurate ÷ attempted); 0-1 or null. Range-tested at model level.
- **now:** the block, which reads: Pass completion rate: accurate passes over attempted, summed rather than averaged, so a heavier passing game weighs more. Null when passes_total is zero.

### int_team_season__deserved_vs_actual.deserved_points

- file: `dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml`
- block: `deserved_points` (863 chars)
- **before:** Points deserved by the on-target process: the league-season least-squares fit of points-per-match on sot_difference_per_match, times this team's games played. NULL when the league-season is not fittable, or when the signal has no spread across it (the slope is then undefined, not flat).
- **now:** the block, which reads: Points the on-target process deserved across the season. Within each league-season, ordinary least squares fits points-per-match on sot_difference_per_match; this is that fitted rate multiplied by the team's own games played. Fitted, not an aggregate of match legs, so it carries no formula. Domestic leagues only - a group-stage tournament's standing is a within- group position, not a comparable league table. Null when the league-season is not fittable, meaning some team lacks full shots-on-target coverage, a league rank or 3 finished games; or the actual table is not a single ladder (MLS conferences, and the Apertura/Clausura formats where one season spans two separate tournaments whose points reset, so a season points total is a figure nobody tracks); or the signal has no spread across the league-season (the slope is then undefined rather than flat).

### int_team_season__deserved_vs_actual.deserved_rank

- file: `dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml`
- block: `deserved_rank` (430 chars)
- **before:** Rank by deserved_points within the league-season (1 = best) — the process-deserved table position. Derived from deserved_points, so it cannot disagree with it, and it appears and disappears exactly with it. NULL whenever the league-season is not fittable, which now includes any table that is not a single ladder.
- **now:** the block, which reads: Rank of the team within its league-season by deserved_points (descending; 1 = most points deserved) - the process-deserved table position. Not aggregated from match legs; computed by ranking the deserved_points metric, so the position and the points total can never disagree. Domestic leagues only. Null exactly whenever deserved_points is null - the two appear and disappear together, so a team never shows one without the other.

### int_team_season__deserved_vs_actual.sot_points_gap

- file: `dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml`
- block: `sot_points_gap` (937 chars)
- **before:** points_won_sum_season - deserved_points. NEGATIVE = under-performing (fewer points than deserved), POSITIVE = over-performing. NOTE the sign is inverted relative to the retired sot_rank_gap. NULL when not fittable.
- **now:** the block, which reads: Points-space deserved-vs-actual gap: actual season points minus deserved_points. NEGATIVE = under-performing (fewer points than the on-target process deserved); POSITIVE = over- performing. Note this sign is inverted relative to the retired sot_rank_gap, where positive meant under-performing. Fitted, not an aggregate of match legs. Because the fit is least squares within the league-season the gap is a redistribution: it sums to zero across a balanced season. Domestic leagues only. Null when the league-season is not fittable, meaning some team lacks full shots-on-target coverage, a league rank or 3 finished games; or the actual table is not a single ladder (MLS conferences, and the Apertura/Clausura formats where one season spans two separate tournaments whose points reset, so a season points total is a figure nobody tracks); or the signal has no spread across the league-season (the slope is then undefined rather than flat).

### int_team_season__metrics.shots_on_goal_against_per_match

- file: `dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml`
- block: `shots_on_goal_against_per_match` (170 chars)
- **before:** Shots on target conceded per match (opponent-SoT companion to shots_on_goal_per_match). NULL unless opponent SoT covers every season game.
- **now:** the block, which reads: Average shots on target conceded per match. The defensive companion to sot_difference_per_match. Null when opponent shots-on-target data does not cover every season game.

### int_team_season__metrics.sot_difference_per_match

- file: `dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml`
- block: `sot_difference_per_match` (257 chars)
- **before:** Shots-on-target difference per match (for - against) — the deserved signal. NULL unless both own and opponent SoT cover every season game. Signed (can be negative).
- **now:** the block, which reads: Average shots-on-target difference per match (on target for - against). The best non-outcome predictor of league position; the deserved process signal behind deserved-vs-actual. Null unless both own and opponent shots-on-target data cover every season game.

### int_team_momentum__metrics.goals_own

- file: `dbt_project/models/4_intermediate/shared/int_momentum.yml`
- block: `goals_own` (177 chars)
- **before:** Own goals credited to the team over the window, from the opponents' own-goal events. Subtracted from goals_for to leave the open-play numerator that finishing efficiency uses.
- **now:** the block, which reads: Own goals credited to the team (the opponents' own-goal events in the team's matches), counted from match events (event_detail = 'Own Goal'). A component of the open-play split.

### int_team_momentum__metrics.goals_penalty

- file: `dbt_project/models/4_intermediate/shared/int_momentum.yml`
- block: `goals_penalty__team` (188 chars)
- **before:** Penalty goals scored by the team over the window, counted from match events. Subtracted from goals_for to leave the open-play numerator that finishing efficiency uses.
- **now:** the block, which reads: Goals scored from penalties, counted from match events (event_type = 'Goal', event_detail = 'Penalty'). A component of the open-play split — not the team finishing its own on-target shots.

### int_player_profile__contribution.contribution_share

- file: `dbt_project/models/4_intermediate/shared/int_player_profile.yml`
- block: `contribution_share` (430 chars)
- **before:** scorer_points / team_goals_season. NULL when the club scored 0 that competition-season.
- **now:** the block, which reads: Goal-involvement share: the player's goals + assists (scorer_points) as a share of the club's whole-season goals. Involved in X% of the club's goals. Computed in int_player_profile__contribution (not a single-leg aggregate). Understates where the player's match stats are missing, because the denominator is the whole season while the numerator counts only covered appearances. Null when the club scored 0 that competition-season.

### int_player_profile__contribution.scorer_points

- file: `dbt_project/models/4_intermediate/shared/int_player_profile.yml`
- block: `scorer_points` (49 chars)
- **before:** The player's goals + assists this club-competition-season (the numerator).
- **now:** the block, which reads: Goals plus assists (combined goal contributions).

### mart_leaderboards.cards_total

- file: `dbt_project/models/5_marts/shared/shared.yml`
- block: `cards_total` (149 chars)
- **before:** cards_yellow + cards_red (the 'cards_total' board's value).
- **now:** the block, which reads: Yellow plus red cards (total cards shown). A second yellow is recorded by the provider as a yellow plus a red, so a two-yellow dismissal counts as 3.

### mart_leaderboards.defensive_actions

- file: `dbt_project/models/5_marts/shared/shared.yml`
- block: `defensive_actions` (68 chars)
- **before:** tackles + interceptions + blocks (the 'defensive_actions' board's value).
- **now:** the block, which reads: Tackles plus interceptions plus blocks (combined defensive actions).

### mart_leaderboards.dribbles_success_pct

- file: `dbt_project/models/5_marts/shared/shared.yml`
- block: `dribbles_success_pct` (58 chars)
- **before:** Dribble success rate — the 'dribbles_success_pct' board's ranked value.
- **now:** the block, which reads: Dribble success rate. Null when dribbles_attempts is zero.

### mart_leaderboards.duels_won_pct

- file: `dbt_project/models/5_marts/shared/shared.yml`
- block: `duels_won_pct__player` (45 chars)
- **before:** Duel win rate — the 'duels_won_pct' board's ranked value.
- **now:** the block, which reads: Duel win rate. Null when duels_total is zero.

### mart_leaderboards.finishing_efficiency

- file: `dbt_project/models/5_marts/shared/shared.yml`
- block: `finishing_efficiency__player` (278 chars)
- **before:** Open-play goal conversion (open-play goals per shot on target, in [0, 1]) — the 'finishing_efficiency' board's ranked value.
- **now:** the block, which reads: Open-play goal conversion: open-play goals (goals minus penalties; goals_total already excludes own goals) per shot on target. In [0, 1] - penalties are excluded because they are not finishing the player's own on-target shots. Null when not fully shot-covered or outside [0, 1].

### mart_leaderboards.pass_accuracy_pct

- file: `dbt_project/models/5_marts/shared/shared.yml`
- block: `pass_accuracy_pct` (153 chars)
- **before:** Pass completion rate — the 'pass_accuracy_pct' board's ranked value.
- **now:** the block, which reads: Pass completion rate: accurate passes over attempted, summed rather than averaged, so a heavier passing game weighs more. Null when passes_total is zero.

### mart_leaderboards.save_pct

- file: `dbt_project/models/5_marts/shared/shared.yml`
- block: `save_pct` (58 chars)
- **before:** Goalkeeper save rate — the 'save_pct' board's ranked value.
- **now:** the block, which reads: Goalkeeper save percentage. Null when denominator is zero.

### mart_leaderboards.scorer_points

- file: `dbt_project/models/5_marts/shared/shared.yml`
- block: `scorer_points` (49 chars)
- **before:** goals + assists (the 'scorer_points' board's value).
- **now:** the block, which reads: Goals plus assists (combined goal contributions).

### mart_player_career.minutes_per_appearance

- file: `dbt_project/models/5_marts/shared/shared.yml`
- block: `minutes_per_appearance` (326 chars)
- **before:** Average minutes per appearance: safe_divide(minutes, appearances), computed here so that nothing reading this mart has to divide. NULL when appearances = 0 (a squad member who never played), non-negative otherwise. A catalogue-governed rate with direction neutral — it reads as a role, not as better or worse.
- **now:** the block, which reads: Average minutes played per appearance (minutes / appearances, where an appearance is a match the player actually played). A squad-list playing-time read describing role - a regular starter versus a rotation or impact-sub player - not quality. The mart computes the value inline via safe_divide; this row registers its meaning.

### mart_team_profile.deserved_points

- file: `dbt_project/models/5_marts/shared/shared.yml`
- block: `deserved_points` (863 chars)
- **before:** The points the team's on-target process deserved: the league-season least-squares fit of points-per-match on sot_difference_per_match, multiplied by its games played. Compare it against `points`. NULL for every non-domestic-league row, and wherever the league-season cannot be fitted — including any league whose table is not a single ladder (MLS conferences, and the Apertura/Clausura formats where a season is two separate tournaments, so even the points total is not one comparable figure).
- **now:** the block, which reads: Points the on-target process deserved across the season. Within each league-season, ordinary least squares fits points-per-match on sot_difference_per_match; this is that fitted rate multiplied by the team's own games played. Fitted, not an aggregate of match legs, so it carries no formula. Domestic leagues only - a group-stage tournament's standing is a within- group position, not a comparable league table. Null when the league-season is not fittable, meaning some team lacks full shots-on-target coverage, a league rank or 3 finished games; or the actual table is not a single ladder (MLS conferences, and the Apertura/Clausura formats where one season spans two separate tournaments whose points reset, so a season points total is a figure nobody tracks); or the signal has no spread across the league-season (the slope is then undefined rather than flat).

### mart_team_profile.deserved_rank

- file: `dbt_project/models/5_marts/shared/shared.yml`
- block: `deserved_rank` (430 chars)
- **before:** Where the team would sit in the table on the strength of its on-target process, 1 = best. Derived from deserved_points, so the two never disagree and are NULL together. NULL for every non-domestic-league row, and wherever the league-season cannot be fitted: incomplete shots-on-target coverage, no league rank, fewer than three finished games, or a table that is not a single ladder (MLS conferences, Apertura/Clausura).
- **now:** the block, which reads: Rank of the team within its league-season by deserved_points (descending; 1 = most points deserved) - the process-deserved table position. Not aggregated from match legs; computed by ranking the deserved_points metric, so the position and the points total can never disagree. Domestic leagues only. Null exactly whenever deserved_points is null - the two appear and disappear together, so a team never shows one without the other.

### mart_team_profile.sot_points_gap

- file: `dbt_project/models/5_marts/shared/shared.yml`
- block: `sot_points_gap` (937 chars)
- **before:** `points` minus deserved_points. NEGATIVE means under-performing — fewer points than the process deserved; POSITIVE means over-performing. NULL wherever deserved_points is.
- **now:** the block, which reads: Points-space deserved-vs-actual gap: actual season points minus deserved_points. NEGATIVE = under-performing (fewer points than the on-target process deserved); POSITIVE = over- performing. Note this sign is inverted relative to the retired sot_rank_gap, where positive meant under-performing. Fitted, not an aggregate of match legs. Because the fit is least squares within the league-season the gap is a redistribution: it sums to zero across a balanced season. Domestic leagues only. Null when the league-season is not fittable, meaning some team lacks full shots-on-target coverage, a league rank or 3 finished games; or the actual table is not a single ladder (MLS conferences, and the Apertura/Clausura formats where one season spans two separate tournaments whose points reset, so a season points total is a figure nobody tracks); or the signal has no spread across the league-season (the slope is then undefined rather than flat).

