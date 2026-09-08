# Review — feat/awarded-and-walkover-count-as-played — 2026-09-08

diff_sha256: d21658469db4a537c2ca6c6fda3179826d7ee32550590cb144519c88d57a9d2f

rounds: 6

rounds_cap_override: >
  CPO, 2026-09-08: **"go ahead, add the not_null tests"**, given after round 3 was brought to him with
  the finding, my partial acceptance, and the measured reason for the half I declined. Recorded in
  `escalations.log`, entry `2026-09-08 — … — ROUND CAP OVERRIDE`.
  ⚠ What the rounds bought, because the cap exists to tell LOOPING from FIXING. Nothing was
  re-argued and no verdict was disputed:
    round 1  FAIL  the sotd gate moved to the new counter, its DIVISOR did not — 15 team-seasons
                   diluted on the metric that feeds the deserved-points regression
    round 2  FAIL  the same class in finishing_efficiency_pct, up to +60%; plus no column descriptions
    round 3  FAIL  every rate enumerated, NO third instance; one missing not_null
    round 4  PASS  ×2 — and a noted asymmetry whose fix exposed a phantom column
    round 5  the delta re-review
    round 6  PASS ×2 — the CI fix, forced by a defect no offline check could reach
  ⭐ Rounds 1 and 2 each found a defect that would have shipped a wrong number to a live elite
  competition, and neither pointed at the other: their victims are DISJOINT, because Ligue 1's
  awarded fixture is the 0-0. Round 3's clean sweep is what actually closed the class.

⚠ **VERDICTS AND HASHES.** `scope-auditor` and `analytics-engineer-reviewer` both PASSed round 4 at
`438ceec…`. Schema files then changed — a `not_null` added on `is_awarded_result`, and the removal of
a phantom column entry that addition exposed — so both were re-run on the delta at `c3fe639…` rather
than carried forward. Recorded rather than implied.

⚠ **ROUND 6 IS THE MR PIPELINE'S FINDING, NOT A READER'S.** `data:build:mr` on pipeline #410 came
back `PASS=471 WARN=0 ERROR=2 SKIP=306`. One error was this branch's: the metric drift guard
`assert_no_uncatalogued_season_metric` read the new coverage counter `games_expecting_team_stats` as
an uncatalogued metric, because its `exempt` list had not been told about it. ⭐ **No check this
branch ran could have found it** — the guard calls `adapter.get_columns_in_relation`, so it needs a
BUILT relation; `dbt parse` does not build, the composed-chain verification queries prod where the
column does not exist yet, and the five offline gates never execute dbt. Both reviewers were re-run
on that delta. The other error is `not_null_dim_team_team_name`, which is not this branch's — see
`escalations` below.

## analytics-engineer-reviewer
VERDICT: PASS (round 4 at `438ceec…`; delta re-reviewed at the hash above)
risks_checked:
- **Round 6, the CI fix.** Traced the counter from `int_team_season__metrics_cumulative.sql:45`
  through `int_team_season__metrics.sql`'s `sf.* except (match_number)` and confirmed it is the ONLY
  column this branch projects into any of the three models the guard scans — the two player models
  are untouched. ⭐ It specifically checked `goals_open_play_in_sot_games`, the other column this
  branch added upstream, and established it appears only inside `case`/`safe_divide` expressions and
  is never given an output column, so no second guard failure is hiding behind the first.
- Ruled on exempting vs cataloguing from evidence rather than convenience: none of the five coverage
  counters appears in `metric_catalogue.csv`, the column has no `direction` and no `interpretation`,
  and the guard's docstring excludes "the coverage counts" by name. Confirmed the edit adds one
  literal and introduces no prefix, suffix or wildcard matching that would widen the exemption.
- Swept all 40 files in `dbt_project/tests/` for `get_columns_in_relation`: two use it, and the other
  (`assert_metric_catalogue_expr_resolvable`) runs in the opposite direction — catalogue tokens must
  resolve to leg-model columns, so a NEW column can never fail it. No sibling guard carries the same
  gap. Two-sided, as required.
- Confirmed the DECLINED half of its own round-3 finding was correct SQL semantics, not a convenient
  measurement: a `SUM` over an all-NULL set is NULL, so `not_null` on `goals_open_play_in_sot_games`
  would fail on real, honest nulls — measured 18,301 of 118,180. It verified the cited precedent
  (`goals_against_in_save_games` untested) is true in the file rather than asserted.
- ⭐ It offered a better alternative rather than just accepting: a CONDITIONAL test
  (`when games_with_sot_stats > 0, the sum is not null`) would hold by construction. Judged worth
  having but not mandated by `engineering_standards.md` §3, and not a shipped defect. Recorded in
  **#109** rather than bolted on here.
- Re-swept both gate files two-sided: exactly 25 `< games_expecting_team_stats` in the cumulative
  model and 10 in the momentum mart, with only the six correct scoreline exceptions still on
  `games_played` / `games_in_window`. No stray unconverted gate.
- Traced every `status_short` reader across `dbt_project/models`, `scripts/export_site_data.py` and
  `site_v2/src` independently, confirming the staging `upper()` cannot regress an unlisted consumer —
  it reproduced the impact-map claim rather than trusting it.
- Verified the three-valued-logic comments on the new tests are actually true: `x < NULL` is NULL, the
  `CASE` takes its `ELSE`, and an ungated rate would be served instead of an honest NULL.
- ⚠ Named an asymmetry without failing on it — `is_awarded_result` untested while the same reasoning
  justified testing its derivative. Acting on that is what exposed the phantom column below.
- **Delta re-review**: verified from the model SQL rather than my claim that `is_awarded_result` is
  consumed in `int_team_season_record`'s `legs` CTE and never reaches its outer select, that the yml
  entry is genuinely gone from the file rather than net-cancelled in the diff, and that both models
  carrying the new `not_null` really do project the column.
- ⭐ It then swept EVERY column this branch added across all six schema files against each model's
  actual select list, looking for another instance of the same phantom-projection defect, and found
  none. That is the check I should have run before documenting anything.
- Confirmed the flag cannot be NULL under the leg filter's five-value `status_short` restriction, so
  the new tests are sound rather than assumed.
- ⚠ Noted without reopening: `int_team_season.yml`'s two `games_expecting_team_stats` entries carry no
  `not_null`. It is a passthrough of a column already guarded at its origin, predates this delta, and
  was in scope at its earlier PASS.

## scope-auditor
VERDICT: PASS (round 4 at `438ceec…`; delta re-reviewed at the hash above)
risks_checked:
- **Round 6, the CI fix.** Held the scope-path addition legitimate rather than self-authorising: the
  column that broke the guard is produced by a model already in `scope_paths` and already covered by
  the CPO's *"same MR"* ruling, so registering it in an exemption list is a mechanical consequence of
  authorised work, not a new scope decision.
- Checked the edit against the A6 pattern — loosening a guard to dodge a defect. The guard's purpose
  is to catch uncatalogued METRICS; adding one coverage counter to an existing, already-justified
  exemption category narrows nothing and silences no real metric gap.
- Re-read `decisions_reserved` in full at the delta: the freshness guard, the `INT`-match question
  and the handover correction are all still open, and the new `dim_team` entry is a reservation with
  falsifiable evidence rather than a parked defect — a team with zero fixtures cannot be reached by
  this branch's fixture-status logic or by any model in scope.
- Confirmed the delta quotes no NEW CPO ruling, so it needs no `escalations.log` backing.
- All five CPO rulings quoted across the contract verified verbatim against `escalations.log`
  (lines 8098-8207): "let's do it", "another input to standardize", "same MR", "As simple Google
  search says it was a 0:0", "go ahead, add the not_null tests".
- Every path in the diff checked against `scope_paths` — all 16 non-task files listed, none edited
  outside it, across five rounds of growth.
- ⭐ **Scope creep across four rounds, checked specifically**: each addition — the counter, the
  coverage-restricted sum, two singular tests, a mart column, five schema files — traced to a
  reviewer finding or a CPO ruling, and each round's fix confirmed present in the diff and DISJOINT
  from the others, supporting the override's claim that nothing was re-argued.
- The DECLINED half of round 3 confirmed recorded as a decision with its evidence, in the contract
  AND as an inline comment in the schema files — not quietly dropped.
- `decisions_reserved` untouched: the freshness guard, the INT-match question and the handover
  correction are all still open and none is silently resolved.
- Credential sweep of the full diff: none.

## escalations
- **RULED: count `AWD` and `WO` as played for results** — *"let's do it"*, on the measured table of
  24 fixtures that count nowhere today.
- **RULED: normalise the status casing** — *"another input to standardize"*, unprompted.
- **RULED: the enlarged gate change stays in one MR** — *"same MR"*, after my first plan was shown to
  destroy ~16 team-seasons' statistics.
- **RULED: the 0-0 technical loss counts as a draw** — *"As simple Google search says it was a 0:0"*.
  ⛔ My recommendation to exclude it was WRONG and no exclusion was built.
- **RULED: the round-cap override** — *"go ahead, add the not_null tests"*.
- **FILED, not fixed:** GitLab **#109**, the end-to-end test strategy, at his instruction
  (*"do we have a consistent test strategy? … If not file it first"*).
- **⛔ OPEN, needs a ruling:** `not_null_dim_team_team_name` fails the MR pipeline and is NOT this
  branch's. API-Football sent a stub team block — `{"id":22722,…,"name":null}` — inside one BSA
  fixture's lineups, and `base_apif__teams` mints a `dim_team` key from an id-only source while only
  drawing the name from rows that have one. Traced in full in `decisions_reserved`. Fixing it here
  would put an unrelated entity fix inside an MR about awarded matches; leaving it keeps `!156` red.

## ⛔ WHAT THIS BRANCH SHOULD BE REMEMBERED FOR

**1. Two bugs of the same class with disjoint victims.** The divisor bug hit teams whose awarded
match has NO stat line; the finishing bug hit teams whose awarded match SCORED. Ligue 1 is in the
first set only, because its awarded fixture is a 0-0. Fixing one told me nothing about the other, and
"I fixed the same-window problem" was never the same claim as "I checked every same-window formula".

**2. I compared against a moving baseline twice, in one MR.** The form window because
`int_team_momentum_window` filters on `current_date()`; the season chain because the nightly failed
and left the intermediate layer a day behind `fct_fixture`. Both produced large phantom differences
in competitions containing no awarded fixture at all — 2,917 rows and 39 rows — and I reported the
second set to the CPO before catching it.

**3. A documented phantom column passed `dbt parse`, five offline gates and two full reviews.**
`int_team_season_record` uses `is_awarded_result` internally and never emits it. Only a verification
query failed. The checker the handover names for this class does not exist.

**4. The MR pipeline found a defect that five offline gates, `dbt parse`, a composed-chain
verification against prod and five review rounds all missed** — and it could not have been otherwise.
The guard reads a BUILT relation's schema, so it exists in a layer none of those checks occupies. The
lesson is not "check harder"; it is that a guard keyed on `adapter.get_columns_in_relation` is
invisible to every pre-build check by construction, and a branch that adds a column to a scanned
model must go and read that guard's exemption list on purpose.

**5. Two reviewer findings were accepted in part, not whole.** The `not_null` on the restricted sum
would have broken the build on 15% of rows. A finding is accepted on its reasoning, not its
authorship — and the measurement is what settles which half is right.
