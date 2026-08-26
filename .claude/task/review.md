# Review — fix/90-clean-sheets-count-vs-share — 2026-08-26

> The machine-checked review artifact (governance G3). Written in step 4 (Lock) of the review
> cycle, AFTER staging and AFTER the blinded reviewers returned.

diff_sha256: 46732ef0bde7768ab84090100be63690678655b938455131d8c7561d1647a45a

rounds: 2

<!--
WHAT CHANGED BETWEEN ROUND 1 AND ROUND 2, so the three standing PASSes are auditable rather than
assumed. The CODE IS BYTE-IDENTICAL: `git diff --cached --stat -- dbt_project docs site_v2` reads
19 files, +165/-76 in both rounds. The only substantive delta is `contract.md`'s `impact_map`
`downstream:` block, which now PASTES the `dbt ls --select <model>+` output for all three renamed
writers instead of asserting the lineage from a hand-trace — the round-1 scope-auditor FAIL.
That paste ADDED a fact rather than changing one: `int_team_season__deserved_vs_actual` is in the
lineage and was missing from the hand-traced map. It is unaffected (explicit column list at
`:70-79`, no clean-sheet column), verified by reading the model.
scope-auditor is re-spawned for round 2. The other three verdicts stand: each examined the code and
the contract's substance, the code has not moved, and strengthening the evidence under a claim
cannot invalidate a PASS that was given over the weaker version of it.
-->


<!--
Required reviewer set, computed from .claude/review_routing.json against the 21 staged
non-bookkeeping paths (not guessed):
  scope-auditor                        always
  analytics-engineer-reviewer          dbt_project/** + dbt_project/seeds/metric_catalogue.csv
  football-analytics-expert-reviewer   dbt_project/seeds/metric_catalogue.csv
  bi-analyst-reviewer                  site_v2/src/** + docs/wireframes/**
No guard path is staged, so no specialist is promoted to opus; all four run on the pinned sonnet.
Verdict sections are appended below as each blinded reviewer returns. Nothing here is written by
the builder.
-->

## scope-auditor
VERDICT: PASS
risks_checked:
- Round-1 FAIL basis (missing `dbt ls`-pasted lineage/leaf-count evidence in `impact_map`, §A6):
  `contract.md` now pastes raw `dbt ls --select <model>+` output for all three renamed writers
  (`int_team_season__metrics_cumulative`, `int_team_profile__yoy`,
  `int_team_competition_benchmark_metrics_long`), classifies all 11 downstream models by reading
  their SQL rather than by name, and discloses the initially-missed
  `int_team_season__deserved_vs_actual` — independently confirmed that model has no clean-sheet
  column, and confirmed `mart_team_momentum` is genuinely a separate, untouched chain
  (`b.clean_sheet_games`, a count). Evidence is genuine, not fabricated.
- Rename completeness: grepped `dbt_project/` for the bare quoted string `"clean_sheets"` (the form
  used in `accepted_values` lists) — zero hits, confirming all three lists moved together with the
  UNPIVOT list, so no benchmark row silently disappears.
- Scope: every file touched in the diff (`dbt_project/models/**`, the seed, the generated docs, the
  six `site_v2/src/**` files, the `docs/wireframes/**` files) matches an entry in `scope_paths`;
  `site_v2/src/data/**` is untouched in the diff, consistent with the contract's claim that the
  sample is not hand-edited.
- §10/threshold check: the `teamBinding()` helper is a plain in-repo TS function/type addition with
  no new dependency, script, CI step or service — not a "new mechanism" in the §10 sense, and it is
  declared and argued for rejection in `decisions_taken` rather than smuggled past silently.
- `decisions_reserved` items (sample-set refresh, `mart_team_momentum`/#93, catalogue-drives-SQL
  /#91, the ~40 blank columns of #82, the `_sum_season` grain wording, no new range tests) — none
  are actioned in the diff; verified none of the corresponding files or mechanisms were touched
  beyond what is declared.
- Credentials/secrets: swept the full diff text for key/token/password-shaped strings — none found.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Football validity of both new/changed rows in `dbt_project/seeds/metric_catalogue.csv`:
  `clean_sheets_share` (`countif(goals_against = 0)` / `count(*)`, format `percent`) and
  `clean_sheets` (`countif(goals_against = 0)`, blank denominator, format `count_fraction`) both
  measure the standard football notion of a clean sheet (a match finished with zero goals
  conceded); the underlying `goals_against` column is the authoritative scoreline, filtered to
  non-null in `int_legs__team_match.sql:69-72,94-97`, so no coverage-gap caveat is owed and none
  was fabricated or omitted.
- Direction/format correctness: both rows carry `direction: higher_better` /
  `lower_is_better: false`, which is football-correct (more clean sheets, and a higher share of
  them, is strictly better defensively); `clean_sheets_share` is range-tested `[0,1]`
  (`int_team_season.yml:186`) while the raw count is range-tested `[0, games_played]` /
  `[0, games_in_window]` in the untouched `shared.yml:127,883` — the count was correctly *removed*
  from the 0–1 ratio-range assertions rather than left there, which would have been a false
  constraint.
- No composite/fabricated metric introduced: both rows are a transparent countif over a real
  column, no index, no invented probability.
- Edge-case honesty: the count row's `interpretation` explicitly flags "a raw count, so it rises
  with matches played", matching the convention used elsewhere in the catalogue for other uncapped
  team totals (`corner_kicks`, `shots_inside_box`); this is the caveat this role exists to demand,
  and it is present.
- Display-name provenance and convention: confirmed against `escalations.log:5202-5203` that the
  objective's quoted CPO ruling ("use clean_sheets… and clean_sheets_share…") is verbatim;
  confirmed the later `% Clean sheets` / `% Zu-Null-Spiele` / `% Nollapelit` naming is disclosed on
  its face as a CPO *selection* between builder-authored options, not misattributed as a verbatim
  ruling; verified against `strings.ts` that the "every percent-format team label carries a `% `
  prefix" claim (7 of 7 prior rows) is true in all three locales, so the new label is a consistent
  extension, not an invented exception.
- Rename completeness/no dangling stale value: grepped `dbt_project/` for the bare quoted string
  `"clean_sheets"` post-patch — zero hits, confirming all three `accepted_values` lists
  (`int_competition_benchmarks.yml` ×2, `shared.yml`) and the unpivot list in
  `int_team_competition_benchmark_metrics_long.sql:34` were updated together, so no benchmark row
  silently disappears from a stale accepted-values check.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement of the renamed ratio: verified the `safe_divide` computation stays in
  `int_team_season__metrics_cumulative.sql` (intermediate) and only the alias changes; no logic
  moved into core/marts/frontend.
- Contract's corrected premise (`mart_team_profile.clean_sheets` is a count, not the rate):
  independently re-traced the CTE join (`ts` = `mart_team_season`) rather than trusting the
  citation — confirmed true.
- Catalogue governance for both the renamed and newly-created metric rows (label_en uniqueness,
  metric_id uniqueness, direction/lower_is_better lockstep) — checked against the actual CSV rows.
- Completeness of the rename across the warehouse: grepped all of `dbt_project/` for
  `clean_sheets`, classified every remaining bare reference as count vs share by reading the model
  SQL, found none stale.
- All three `accepted_values` lists carrying the benchmark metric set, confirmed all three updated
  in lockstep.
- Frontend consumption-layer boundary (`metricRows.ts`, `MetricLeagueRow.astro`,
  `MetricSeasonRow.astro`, `TeamPerformance.astro`): confirmed the binding logic selects between
  two already-computed served fields and maps a display-format enum, computing no new fact;
  confirmed the export script (`scripts/`) is untouched and contains no `clean_sheets` logic.
- Same-window rule on the ratio's numerator/denominator (`clean_sheet_games`, `games_played`): both
  sourced from `int_team_season_record` at the same cumulative grain, arithmetic unchanged.
- Test coverage: confirmed the two `dbt_utils.expression_is_true` range tests in
  `int_team_season.yml` and `int_team_profile.yml` were updated to the new column name, not
  deleted.
- ⚠ This reviewer read the A6/impact-map question the opposite way to scope-auditor, and said so:
  "this change is a column alias rename, not a grain change, raw-write change, or staging-model
  change, so the strict `dbt ls`-pasted-lineage requirement doesn't trigger; the manual
  writer/downstream enumeration in the contract was independently spot-checked and matches the
  code." Recorded, not arbitrated — the FAIL was fixed by pasting the lineage rather than by
  arguing the exemption.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Field-binding rule for the renamed/split metric: traced `clean_sheets_share` from
  `int_team_season__metrics_cumulative.sql:91` through `int_team_season__metrics`
  (`sf.* except (match_number)`) → `int_team_competition_benchmark_metrics_long.sql:34`
  (`metric_key='clean_sheets_share'`), and separately confirmed `mart_team_profile.sql:86` still
  reads `ts.clean_sheets` from the `mart_team_season` CTE, and that `mart_team_season.sql:41` and
  `mart_team_momentum.sql:44` are genuinely counts. No fabricated field.
- Export path for the new field name: `scripts/export_site_data.py` has no hardcoded
  `clean_sheets` string at all — `select *` plus a denylist `_strip_identity`, and
  `_shape_team_benchmark_member` passes `metric_key`/`metric_value` straight through with no
  allowlist, so the renamed columns flow automatically once the warehouse rebuilds. No
  export-script change is needed or missing.
- Committed sample under `site_v2/src/data/` (not in scope_paths): confirmed
  `teams/33.json` still carries the OLD names untouched — the sample was NOT hand-edited to fake
  the split, consistent with the disclosed "one build stale" reservation.
- Rendered page evidence: present, built from `site_v2/dist/` after `npm run build` rather than
  source or `outerHTML` — the built-output check #827 requires. 16 season rows / 15 league rows in
  all three locales, row 3 rendering the three locale labels with a dash for value and delta, and
  the fixture page still rendering `1/4 Clean sheets`. No `<style>` block is touched in any of the
  three components, so viewport/breakpoint checks are not applicable and their absence is not a gap.
- Locked contract (order/tier/group): row 3 keeps position, `tier: 2`, `group: "Goals"` and its
  fixture `denom`; the `team` override changes only what the TEAM surface binds. Sixteen rows,
  order and tiers otherwise untouched. All three `accepted_values` lists updated.
- Labels/wording provenance: RULING 2 (`escalations.log:5202-5203`) verbatim-matches the contract's
  quoted CPO text; the `% Clean sheets` entry discloses itself as a CPO *selection* between
  builder-authored options rather than a verbatim ruling, and matches the unanimous `% `-prefix
  convention verified in `metric_catalogue.csv` and `strings.ts`.
- Naked-percentage / duplicate-number check: `% Clean sheets` has no adjacent count row in the
  Goals block (same as the accepted `save_ratio` GAP-11-family gap). This PREDATES the branch — the
  team page already coerced `clean_sheets` to a percent via the deleted hack — and the count and the
  share never render on the same screen, so there is no duplicate-number defect.
- Noted but not actioned: `docs/wireframes/02_team_profile.md:137` still conflicts with
  `14_team_stats.md` row 3. The conflict predates the branch, is disclosed in BUILDER'S CALL 5 as
  out of scope, and has no live consequence — only `TeamPerformance.astro` renders `METRIC_ROWS`.

## escalations
(none)

<!--
Two CPO decisions were taken during this task and neither reached a reviewer as an open question,
so neither is an escalation: both were SELECTIONS between builder-authored naming options, made
before the code was staged, and both are recorded with that exact provenance in `escalations.log`.
The football-analytics and bi-analyst reviewers each independently verified that provenance rather
than taking the contract's word for it.
-->

