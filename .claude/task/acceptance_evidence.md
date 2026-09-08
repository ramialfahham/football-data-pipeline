# Acceptance evidence — an awarded match is a RESULT without a STAT LINE

Branch `feat/awarded-and-walkover-count-as-played`, from main `5bc1934`.

Everything below is measured against **LIVE PROD DATA**. `dbt build` is banned here (it writes and
bills); a SELECT over compiled SQL is not.
⚠ **THE CHANGE SPANS FOUR MODELS IN A LINE**, so no single compiled model can be run —
`dbt compile` emits each one referencing the DEV tables of its upstreams, which do not exist. Each
compiled model is nested as a CTE and every dev reference rewritten either to the CTE now holding it
or to the live prod table. Recorded because "I ran the compiled model" would be untrue here.

⭐ **RE-MEASURED AFTER THE REBASE ONTO `!157` (main `809041a`), because the shared input moved.**
`!157` reattributed 21 player-stat rows and 1 team-stat row between teams. It changed no fixture's
status and touched no awarded match, but it did change data this branch measures, so the headline
comparison was run again rather than argued about:

    pairs   lost_shots  lost_passes  lost_sotd  lost_saves  games_moved  points_moved
    13,664  0           0            0          0           32           23

Byte-identical to the pre-rebase result below. That is the expected outcome and the reason is
structural: every number here is a DIFFERENCE between main's chain and this one composed into a
single query over identical inputs at the same instant, so a change to the shared input moves both
sides equally. Recorded because "it should not have changed" and "it did not change" are different
claims, and this MR has already twice reported a difference that was really a moving baseline.

criteria_demonstrated:

  - **⭐ NO TEAM-SEASON LOSES A STATISTICAL METRIC. This is the criterion the first design failed**,
    and the whole reason `games_expecting_team_stats` exists. Measured under the CONTROLLED
    comparison described below — main's chain and this one in a single query over identical inputs:

        pairs   lost_shots  lost_passes  lost_sotd  lost_saves
        13,664  0           0            0          0

    Without the new counter the gate `games_with_team_stats < games_played` would have fired for
    every team in an awarded match — measured beforehand at ~16 team-seasons, and cascading to
    withhold the ENTIRE Ligue 1 2025 deserved-vs-actual read, because that model needs full SoT
    coverage for every team in a league-season.

  - **AWD and WO now count for RESULTS: 32 team-seasons gain a match, 23 of them gain points**
    (the rest were awarded losses). Baseline 13,664 rows against 13,669 — the 5 extra are teams whose
    only counted match in that competition-season is now an awarded one, so they had no row at all
    before. Every competition that moves contains an AWD/WO fixture and no other does:

        LIBER 2026 · WCQAS 2026 · AFCON 2025 · L1 2025 · LIBER 2025 · CAFCL 2024
        CAFCL 2023 · WCQAF 2023 (10) · BPL 2022 (4) · UEL 2021 · CAFCL 2020

    ⛔ **THESE NUMBERS REPLACE AN EARLIER SET I REPORTED — 37 team-seasons and 13,630/13,635 — WHICH
    WERE WRONG.** See "the baseline was stale" below. The old figures are struck, not annotated.

    The elite case, both teams in the same fixture:

        L1 2025   Toulouse FC   33 → 34 games   23 → 24 points   keeps stats
        L1 2025   FC Nantes     33 → 34 games   44 → 45 points   keeps stats

    ⚠ **+1 EACH BECAUSE THAT MATCH REALLY WAS A 0-0 DRAW.** The provider labels it `AWD`
    "Technical loss" while recording 0-0, and I proposed excluding it on the grounds that a technical
    loss must have a winner. **The CPO checked the actual match and it finished 0-0**, so both teams
    earned that point and crediting a draw is correct. My objection was an inference from a status
    label; his was the result. No exclusion rule was added.

  - **The new counter behaves.** 13,598 rows have
    `games_expecting_team_stats = season_games_played` (no awarded match), 31 are exactly one lower,
    6 are more than one lower — a team carrying several awarded fixtures, which WCQAF 2023 and
    CAFCL 2020 both do.
    ⚠ It can also be HIGHER than the number of stat-covered games: AFCON 2025 shows
    `expecting 6, with 7`, because the single walkover in the warehouse that DOES carry a stat line is
    there. Harmless — the gate is `games_with < games_expecting`, so a surplus never fires it — but
    recorded, because the column's name implies a ceiling it does not enforce.

  - **⭐ THE FORM WINDOW MOVES NOTHING, under a CONTROLLED comparison:**

        pairs  goals_moved  points_moved  window_size_moved  lost_shots/passes/sot/saves
        9,784  0            0             0                  0 / 0 / 0 / 0

    ⛔ **My first comparison of this half was invalid and said 2,917 rows moved.**
    `int_team_momentum_window.sql:46` filters `fixture_date >= current_date()`, so the window is
    defined relative to WHEN THE MODEL RUNS — comparing a mart built 2026-09-06 12:47 against a query
    run a day later measures the calendar. The tell was in the breakdown: movement in PD, TSL, ED,
    BL1, PL and eleven others, **none of which contains a single AWD/WO fixture**. The valid control
    is main's own chain evaluated in the SAME query at the SAME instant, and against that the change
    moves nothing at all today, because no awarded match currently falls inside a last-5 window.
    ⚠ Same lesson as `!155`'s 253-vs-252 float baseline, walked into a second time: a difference is
    not evidence until the unchanged code is measured beside it.

  - ⛔ **THE FORM-WINDOW HALF IS INERT ON TODAY'S DATA, SO IT WAS FORCED.** Measured: **0 of 9,784**
    current windows contain an AWD/WO match, which means its counter always equals `games_in_window`
    and a bug in that half would be invisible. Real data cannot exercise it, so the behaviour was
    synthesised — every team's earliest leg in each window marked awarded and stripped of its team
    stats, which is exactly the shape of a real awarded match, then main's chain and this one
    compared over that same synthetic input:

        windows with shots_per_match NULL     baseline 2,087   changed 1,910
        rescued by the change                                          177

    177 windows where an awarded match with no stat line WOULD have nulled the rate under
    `< games_in_window` and correctly does not under `< games_expecting_team_stats`. That is the
    distinction the change exists to make, demonstrated rather than asserted.
    ⚠ The remaining 1,910 are windows whose rates are NULL for unrelated reasons — sparse coverage in
    lower competitions — and are unaffected in both directions.

  - **`dbt parse` exits 0. SQLFluff exits 0** on all seven changed models.
    ⚠ Linted with `--templater jinja` from the repo root — the route `CLAUDE.md` documents — because
    `.sqlfluff` pins `profiles_dir = ~/.dbt`, which OVERRIDES `DBT_PROFILES_DIR` and so cannot see
    this session's profile. That interaction is documented in the parked profile MR.

  - **Offline gates all exit 0**: `check_layer_contract`, `check_registry_var_sync`,
    `check_description_hygiene`, `sync_metric_docs_blocks --check`, `check_competition_type_seed`.

## ⛔ ROUND 1 FAILED ON A CORRECTNESS BUG I INTRODUCED, and it was in the worst possible metric

`scope-auditor` PASS, **`analytics-engineer-reviewer` FAIL**, on two findings, both accepted.

**1. The gate moved and the divisor did not.**
`int_team_season__metrics_cumulative.sql`'s `shots_on_goal_difference_per_match` gated on
`games_expecting_team_stats` while still dividing by `games_played`. Those were equal while the gate
demanded full coverage; once awarded matches count as played they diverge by exactly the number of
awarded matches, so a numerator spanning the stat-covered games was divided by one more game.

⛔ **It feeds the OLS regression in `int_team_season__deserved_vs_actual`**, so a diluted value moves
a whole league-season's deserved-points fit rather than one cell. Mutation-measured — the shipped
chain against the same chain with only the divisor reverted:

        15 team-seasons diluted, including both Ligue 1 sides:
        L1 2025 team 83    fixed -1.5455    bugged -1.5
        L1 2025 team 96    fixed  0.2727    bugged  0.2647

Fixed to `least(games_with_sot_stats, games_with_opp_sot_stats)` — the games BOTH sides of the
subtraction cover, and byte-identical to the old behaviour wherever the old gate passed.
⭐ **Two-sided:** four divisors still use `games_played` (`points_capture_pct`, `clean_sheets_pct`,
`goals_per_match`, `goals_against_per_match`) and all four are CORRECT — scoreline metrics, and an
awarded match is a real played game with a real scoreline. One moved, four stay.
⚠ Controlled against main, `shots_on_goal_difference_per_match` moves on exactly **2** of 13,664
rows, both AFCON 2025 — the one walkover in the warehouse that DOES carry a stat line, so a seventh
covered match legitimately joins both numerator and denominator (5.6667 → 5.4286, 4.5 → 3.2857).
Ligue 1 does NOT move, because its awarded match has no stats and the fix stops it diluting.

**2. The test this contract promised and I never wrote.** `acceptance_criteria` said "A new test
fails when the gate is reverted to `games_played`. Watched RED under that mutation." No such test
existed — a plain reversion at any of the 35 sites would have passed CI. Two singular tests added,
one per surface, and the predicate measured both ways:

        shipped chain                          0 rows
        gate reverted to games_played         15 rows   RED

⛔ Declaring an acceptance criterion and not meeting it is worse than not declaring it: the contract
asserted coverage that did not exist, and only a reviewer's grep found the gap.

## ⛔ ROUND 2 FAILED ON THE SAME CLASS AGAIN, in a metric neither of us had checked

**`finishing_efficiency_pct` — open-play goals over shots-on-target.** The goal sums are UNGATED
window totals and now include an awarded match's goals; `shots_on_goal` is a null-skipping sum that
never can. A 3-0 technical win therefore added three real goals with no shot behind them. Measured by
re-introducing the numerator:

        LIBER 2025 team 154   correct 0.1724   bugged 0.2759     (+60%)
        LIBER 2026 team 127   correct 0.2241   bugged 0.2759
        BPL   2022 team 266   correct 0.2667   bugged 0.3
        WCQAS 2026 team 12    correct 0.4706   bugged 0.5

⛔ **BOTH BUILDERS CARRIED A COMMENT STATING THE PROPERTY I BROKE** — *"finishing is NULL unless the
window is fully shot-covered, so no coverage-restricted goals sum is needed"* — and I changed what
the gate compares against without reading either. The fix is the pattern three lines below it in the
same file: a coverage-restricted sum, `goals_open_play_in_sot_games`, exactly as
`goals_against_in_save_games` already does for `saves_pct`. Both comments are corrected rather than
left contradicting the code.
⚠ Ligue 1 is absent from that table, correctly — its awarded match is the 0-0, so there are no
phantom goals. **The two bugs have disjoint victims**, which is why finding the divisor bug did not
surface this one and why "I fixed the same-window problem" was not the same as "I checked every
same-window formula".

**And the new columns had no descriptions.** `engineering_standards.md:82` requires them on
business-facing columns in core, intermediate and marts; `check_description_hygiene.py` polices
model-level coverage only, so CI was silent. Now documented in five schema files.
⚠ `scope-auditor` had examined exactly this at round 1 and called it consistent with existing
convention. It was — `games_with_team_stats` is itself undescribed. **A precedent is not a
permission**, and one reviewer clearing something is not evidence for another.
⭐ The hygiene gate then rejected my first description for carrying an ISO date, which is banned
because the text is persisted into BigQuery and git holds the history losslessly. Caught in the
gate, not in review.

## ⭐ ROUND 3: THE RATIO HUNT CAME BACK CLEAN, and one finding was accepted only in part

`analytics-engineer-reviewer` enumerated every rate in both changed builders and both consumers —
`points_capture_pct`, `shots_share_pct`, `clean_sheets_pct`, `goals_per_match`,
`goals_against_per_match`, `shots_per_match`, `shots_on_goal_pct`, `shots_inside_box_pct`,
`shots_on_goal_per_match`, `shots_on_goal_against_per_match`, `passes_per_match`,
`passes_accuracy_pct`, `corners_per_match`, `corners_against_per_match`, `saves_pct`, the
player-derived rates and the `_sum_season` columns — and found **no third instance** of the
same-window class. It also confirmed the round-2 fixes hold, including that the window-function
references in `goals_open_play_in_sot_games` resolve to the leg columns rather than to sibling SELECT
aliases of the same name.

**Its finding: `games_expecting_team_stats` had no `not_null` test** in the two intermediate schema
files, though its siblings do and the mart copy does. The reasoning is exact: every gate reads
`x < games_expecting_team_stats`, and a NULL there is not FALSE — the comparison yields NULL, the
CASE falls to its ELSE, and an **ungated rate is served instead of an honest NULL**. Added.
⚠ Severity stated plainly rather than inflated: the column cannot be NULL today, because a
`countif` / `sum(case …)` never is. This guards a future change to how it is derived.

⛔ **THE SAME FINDING ASKED FOR `not_null` ON `goals_open_play_in_sot_games` TOO, AND THAT WAS
DECLINED.** It is a coverage-RESTRICTED sum: where a team has no shots-on-target data at all it sums
nothing and is legitimately NULL, which is what makes `finishing_efficiency_pct` null out honestly.
Measured on prod rather than argued, over the 118,180 rows of the season record:

        games_expecting_team_stats    NULLs:      0    → the test added, and it passes
        goals_open_play_in_sot_games  NULLs: 18,301    → a not_null test would have failed at once

Its precedent sibling `goals_against_in_save_games` is untested for exactly that reason. A reviewer
finding is accepted on its reasoning, not its authorship — and half of this one would have shipped a
test that broke the build on 15% of rows.

## ⛔ ROUND 4 PASSED, AND CLOSING ITS ONE NOTE FOUND A PHANTOM COLUMN

Both reviewers PASSed. `analytics-engineer-reviewer` confirmed the decline was correct SQL semantics
(a `SUM` over an all-NULL set is NULL) and that the cited precedent is genuinely untested rather than
asserted; it also re-swept both gate files and found exactly 25 and 10 gates on the new counter with
only the six correct scoreline exceptions left on `games_played` / `games_in_window`.

It named one asymmetry without failing on it: `is_awarded_result` had no `not_null`, though the
reasoning used to justify one on `games_expecting_team_stats` applied equally. Closing that found a
real error of mine:

⛔ **`int_team_season_record` USES the flag and never emits it.** It derives the counter from it
inside a CTE; the final SELECT does not project it. So the `is_awarded_result` entry I added to
`int_season_record.yml` documented a column that does not exist, and the new test would have failed
only when it reached BigQuery. `dbt parse` is happy with a phantom column. So is every offline gate.
The entry is removed and the test stands on the two models that genuinely emit it, where it measures:

        int_legs__team_match:  118,180 legs, 0 nulls, 46 awarded legs

46 = 23 fixtures × 2 sides — the 24th, the score-less CAFCL walkover, correctly excluded by the
pre-existing `goals_home is not null` filter.

⚠ The handover names a checker for exactly this class, `check_yml_vs_projection`. **There is no such
script in `scripts/`**, and `declare_missing_columns.py` covers only the reverse direction. Found
because a verification query failed with `Unrecognized name`, not by any guard.
⭐ The CPO asked whether a consistent end-to-end test strategy exists. It does not — §3 gives
per-layer minimums with no rule for when a NULL is a defect versus the honest answer, no severity
principle, and no projection check. Filed as **GitLab #109**, deliberately not attempted here.

## ⛔ THE BASELINE WAS STALE, AND I REPORTED WRONG NUMBERS BEFORE CATCHING IT

The first season-chain comparison was against the LIVE `int_team_season__metrics`, and it is a day
older than the `core.fct_fixture` it is derived from. **The 2026-09-07 05:11 nightly FAILED** — on the
freshness guard, as it has roughly one night in three — and a severity=error failure inside
`dbt build` marks every dependent skipped. So the ingest landed and the intermediate layer never
rebuilt.

⭐ **THE TELL, and it is the same shape both times: movement where the change cannot reach.** The
naive diff produced 39 "new" rows in **FAC 2026** — the FA Cup, which contains no AWD or WO fixture
at all. Checked directly: the live table holds 216 FAC 2026 team-seasons while 224 teams have a
finished FA Cup match in the current `fct_fixture`. Eight teams missing, because the table is stale.

⚠ I had already made this exact mistake once in this same MR, on the form window, where
`current_date()` made the live mart a moving target and 2,917 rows appeared to move across La Liga,
the Eredivisie and the Bundesliga. I fixed that half and did not go back and ask whether the season
half had the same disease. It did, for a different reason.

**Both halves are now measured the only valid way**: main's chain and this one composed into ONE
query, over identical inputs, at the same instant. The mutation that produces the baseline is
asserted rather than assumed — both leg filters reverted, all 25 cumulative gates and all 10 momentum
gates back on the old denominator.

⭐ The lesson is `!155`'s, third instance: **a difference is not evidence until the unchanged code is
measured beside it.** Twice here the "before" was moving on its own.

## ⛔ TWO DEFECTS FOUND BY RUNNING IT, NEITHER VISIBLE BY READING

**1. A bug shipped into the stash.** `int_team_season_record` projects columns from the legs
EXPLICITLY, and I added `is_awarded_result` to the leg model and to the final SELECT while never
carrying it through that projection. The chain did not compile: `Unrecognized name:
is_awarded_result`. It had passed `dbt parse` — parse checks the graph, not a column's existence
through a hand-written projection.

**2. The form-window comparison described above.** Recorded as a defect in my METHOD rather than in
the code, because the code was fine and the measurement was not.

## What this does NOT do

- **It does not touch the STAT surfaces.** `mart_team_fixture_stats` and every player-side filter
  keep `('FT','AET','PEN')`: an awarded match has no stat line, so adding it there would add empty
  rows for nobody.
- **It does not change what counts as finished anywhere else.** `INT`, `ABD`, `PST` and `CANC`
  produced no result and stay excluded — including the Utrecht `INT` fixture that started this whole
  investigation, which still counts nowhere and still leaves FC Utrecht a game short of its league.
- **It does not fix the freshness guard**, which is what the investigation was originally about and
  which is still failing the nightly roughly one night in three.

## ⛔ THE MR PIPELINE CAUGHT A DEFECT NO OFFLINE CHECK COULD REACH

`data:build:mr` on pipeline **#410** returned `PASS=471 WARN=0 ERROR=2 SKIP=306 TOTAL=779`. One of
the two errors is this branch's, and nothing available offline could have found it:

  - `assert_no_uncatalogued_season_metric` failed. It is the metric-layer drift guard: every
    metric-bearing column of the three canonical season models must exist in `metric_catalogue`,
    and anything not catalogued and not explicitly exempted is read as a metric that crept in.
  - `games_expecting_team_stats` is a COVERAGE COUNT, not a metric — it is the denominator the
    gates compare against, it has no `direction` and no `interpretation`, and its four siblings
    (`games_with_team_stats`, `stat_coverage_season_games`, `player_stat_coverage_season_games`,
    `season_games_played`) are all already exempt. The guard's own docstring says the coverage
    counts are excluded. The list simply had not been told about the new one.
  - It reaches the guarded model invisibly: `int_team_season_record` → explicit projection in
    `int_team_season__metrics_cumulative` → `sf.* except (match_number)` in
    `int_team_season__metrics`. No file in the guard's own directory mentions it.
  - ⚠ **Unreachable by every check this branch ran.** The guard calls
    `adapter.get_columns_in_relation`, so it reads a BUILT relation's schema. `dbt parse` does not
    build. The composed-chain verification queries prod, whose relation does not have the column
    yet. The five offline gates never execute dbt. Only building the model on a real warehouse
    surfaces it — which is precisely what `data:build:mr` is for.
  - Fix: one literal added to the guard's `exempt` list. Confirmed by
    `analytics-engineer-reviewer` as the only new column this branch projects into any of the three
    scanned models — `goals_open_play_in_sot_games` is consumed only inside expressions and never
    given an output column, so no second failure is hiding behind this one.

**The second error is NOT this branch's** — `not_null_dim_team_team_name`, diagnosed in
`decisions_reserved` and left there deliberately.
