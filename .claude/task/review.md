# Review — feat/team-metric-directions — 2026-07-20

> Machine-checked review artifact (G3). Written after staging and after the blinded
> reviewers returned. The commit gate binds diff_sha256 to the live staged diff.

diff_sha256: 2902772682e2f4a8aeccc64fc2e17a4652389f7abc0947c6b121ef76979356f6

## scope-auditor
VERDICT: PASS
risks_checked:
- Every staged code/contract path is inside scope_paths (metric_catalogue.csv, metricRows.ts, contract.md; escalations.log + review_input.patch are artifact-only). The diff matches the contract, including the new decisions_taken #5 (CPO-directed interpretation sweep). No scope creep, no unauthorized extra edits.
- All §10 direction + interpretation-wording decisions are recorded (contract decisions_taken #1-5 + escalations.log 2026-07-20, incl. the CPO "badge all five" ruling and the interpretation-sweep note); decisions_reserved (player per-90 analogs) held open, not decided here.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- CSV well-formed: the 6 changed rows are each 14 fields against the header, and the reworded interpretation strings use semicolons/parentheses (no raw comma in the trailing unquoted field), so no field-shift on seed load.
- Benchmark marts (team + player) never select/join `direction` (rank is by metric_value DESC; the team benchmark metric set is a hardcoded UNPIVOT list, not direction-derived) so the flip moves no number and trips no benchmark DQ test; assert_team_metric_meaning_complete + the accepted_values test still pass; the LIVE MVP export reads lower_is_better (untouched), so the live site is byte-identical.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- First pass FAILed two reworded interpretations as overclaims (duels "proactive front-foot side"; passes "more control of the ball"); after the fix, re-checked both: duels now reads "high = a physically engaged side (volume; can also reflect a side under sustained pressure)" and passes reads "high = sees more of the ball; low = a more direct style (accuracy shows how securely it is kept)" — both drop the unsupported narrative, mirror the honest defensive_actions caveat, and passes no longer collides with pass_accuracy's "control" framing.
- Re-verified direction/interpretation internal consistency across all 6 rows (the 4 higher_better rows read "high = …", corners_against reads "low = …"), and confirmed the other style rows kept their honest caveats ("a weak proxy", "volume not shot quality"). Directions themselves are the CPO's settled ruling, not re-litigated.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Type-safe: the 5 written values are existing members of the Direction union ("higher_better"/"lower_better"), MetricRowDef gives each object literal contextual typing so the astro build type-checks; catalogue<->metricRows.ts direction values match 1:1 for all 5 rows.
- Only `direction` values changed in site_v2; bars.ts (betterSide/barWidth) and MetricRow.astro are byte-unchanged, so the frontend still consumes a served enum for a green-highlight decision and computes no facts (display config, not computation); no src-level test or sample-fixture JSON references these rows or assumes `neutral`.

## escalations
- question: The `direction` values for the 5 team style metrics (a §10 metric-meaning choice) rest on a CPO ruling, and the football-analytics-expert-reviewer had (in the prior commit's review) escalated whether volume metrics should carry a verdict at all, citing the 2026-06-28 correlation sweep.
  CPO ANSWER: "Give each a direction" then "Badge all five as decided" (AskUserQuestion, 2026-07-20) — proceed with all 5 team metrics directional, per the direction-is-judgement principle (direction = "all else equal, is more better?", not a rank/results correlation). Full record in escalations.log 2026-07-20. This round's four reviewers returned no open ESCALATE.
