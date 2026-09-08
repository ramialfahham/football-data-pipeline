# Review — feat/awarded-and-walkover-count-as-played — 2026-09-08

diff_sha256: c3fe6393f2126a2a7574628bdeb385518eccd4de6a8c306f6be697bdfa329e83

rounds: 5

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
  ⭐ Rounds 1 and 2 each found a defect that would have shipped a wrong number to a live elite
  competition, and neither pointed at the other: their victims are DISJOINT, because Ligue 1's
  awarded fixture is the 0-0. Round 3's clean sweep is what actually closed the class.

⚠ **VERDICTS AND HASHES.** `scope-auditor` and `analytics-engineer-reviewer` both PASSed round 4 at
`438ceec…`. Schema files then changed — a `not_null` added on `is_awarded_result`, and the removal of
a phantom column entry that addition exposed — so both were re-run on the delta at `c3fe639…` rather
than carried forward. Recorded rather than implied.

## analytics-engineer-reviewer
VERDICT: PASS (round 4 at `438ceec…`; delta re-reviewed at the hash above)
risks_checked:
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

**4. Two reviewer findings were accepted in part, not whole.** The `not_null` on the restricted sum
would have broken the build on 15% of rows. A finding is accepted on its reasoning, not its
authorship — and the measurement is what settles which half is right.
