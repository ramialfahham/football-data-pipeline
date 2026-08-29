# Review — refactor/metric-rename-team-finishing-efficiency — 2026-08-29

> Step 3 of the metric catalogue naming programme, MR **F of six and the LAST of the twelve team
> renames**: `finishing_efficiency` → `finishing_efficiency_pct`, TEAM entity only. The PLAYER row
> of the same `metric_id` is deliberately untouched (step 4). Branched from main `cdd2218`
> (after `!122`).

diff_sha256: bef67750e60b02c74b74e09915c54af32ed89809652434a689271d7c81983bd2

rounds: 1

> All five required reviewers returned PASS with **no open findings** in round 1. Each was given the
> contract, the cumulative branch diff and `escalations.log`, and each was pointed at the specific
> hazards this batch carries — the doc-block merge, the six-of-seven `*_in_range` split, and the
> player `accepted_values` lists — so that a PASS means those were looked at rather than missed.

## scope-auditor
VERDICT: PASS
risks_checked:
- Verified every quoted ruling in `contract.md` against `escalations.log` — RULING 1's verbatim
  clause, the "⛔ TEAM, 12 REMAINING" row, the "THE SIX, ENUMERATED" exclusion, "THE RULED PATTERN",
  and the disclosed-transient quote from the PLAYER list. All present verbatim. No plan-file
  citation and no line-number citation into the log.
- Confirmed the `escalations.log` change is a PURE APPEND: the only hunk adds the new
  `2026-08-29 STEP 3, MR F` block after unchanged context; no merged block was edited in place.
- Reconciled the mechanical counts against the diff rather than the prose: exactly 6
  `doc('finishing_efficiency__team')` → `doc('finishing_efficiency_pct')` and exactly 3
  `doc('finishing_efficiency__player')` → `doc('finishing_efficiency')` rewrites, matching the
  claimed 6/3.
- Confirmed the 6 named range tests renamed with the column and
  `mart_leaderboards_finishing_efficiency_in_range` does not appear in the diff at all.
- Confirmed the seed renames only the TEAM row; the PLAYER row immediately below it is byte-identical.
- Confirmed every file in the diff appears in `scope_paths`, no scoped file was left undone, and the
  threshold declarations (no new mechanism, cost or dependency) match what the diff actually does.
- Confirmed `decisions_reserved` honestly carries #96, #98 and the deferred
  `contribution_share` → `contribution_player_pct` question rather than silently deciding it.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Swept all 20 files under `dbt_project/models/` carrying the stem and confirmed each occurrence is
  either correctly renamed (team) or correctly left bare (player). No team surface missed, no player
  surface renamed.
- Enumerated all 15 `doc('finishing_efficiency…')` call sites against the blocks the generator now
  emits: 6 resolve to `finishing_efficiency_pct`, 3 to the re-pointed bare `finishing_efficiency`,
  6 to the surviving `*__team` yoy blocks. **Zero dangling `doc()`**; the three `*__player` yoy
  blocks were dropped with 0 remaining references.
- Confirmed all three 22-name TEAM `accepted_values` lists carry `finishing_efficiency_pct` at
  exactly 22 values with no duplication, and all three PLAYER lists still carry the bare name.
- Found exactly 7 `*_finishing_efficiency*_in_range` tests tree-wide: 6 renamed,
  `mart_leaderboards_finishing_efficiency_in_range` correctly left as the player board's test.
- Diffed every renamed `case` / `safe_divide` expression against its pre-rename form — logic
  unchanged, only the output alias moved. Formula, floor, null policy, direction and tier are all
  byte-identical on the catalogue row.
- Confirmed no touched model is `materialized='incremental'`, so no `--full-refresh` was owed.
- Confirmed the export script carries no hardcoded reference to this metric and no derivation was
  moved into the consumption layer.
- Confirmed no step-4 leakage: `finishing_efficiency_player_pct` appears only in contract and
  handover prose, never in code.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Confirmed the naming authority independently in the log: RULING 1 verbatim, the "TEAM, 12
  REMAINING" row, absence from "THE SIX, ENUMERATED", and THE RULED PATTERN (`_form` = `_pct` for a
  percentage) all supporting the name. No manufactured gap.
- Diffed the seed row byte for byte: only `metric_id` and `label_i18n_key` moved. `label_en`
  ("% Goals per shot on target"), the description, base relation, numerator
  (`sum(goals_for - goals_penalty - goals_own)`), denominator (`sum(shots_on_goal)`), format, group,
  tier and `direction: higher_better` are all unchanged — and `higher_better` remains football-correct
  for a conversion rate.
- Confirmed the "on target" → "on goal" wording is correctly deferred to step 5 and not taken here,
  in the seed and in all three locale files.
- Confirmed the team/player divergence is football-coherent and disclosed twice — in the programme
  block's own transient note and again in this MR's appended block.
- Traced the two renamed prose mentions to the TEAM description via the log's
  `feat/82-metric-docs-blocks-generated` DEFECT 1 entry, and confirmed the player-side
  `goals_open_play` mention was correctly left bare.
- Confirmed no composite or fabricated metric is introduced; this is a pure identifier rename.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Traced `asked = rowKeys ∪ heroKeys` in `check-metric-labels.test.mjs:36-38` and confirmed
  `metricRows.ts:93` still feeds `rowKeys`, so the re-pointed EN exemption at `:99` keys off a name
  that IS in `asked` — the guard exercises it rather than passing vacuously. The exemption narrows on
  exactly one id in one locale, exactly as before: **not widened**.
- Verified the generated `metric_columns.md` merge — both blocks bare, the three `*__player` yoy
  blocks deleted, the three `*__team` yoy blocks renamed — and cross-checked all 9 moved `doc()`
  sites as consistent and non-dangling.
- Checked `metric_bindings.csv` and `metric_definitions.json` against `check_ui_i18n_metrics.py`,
  which reads by `DictReader` column name: the `live_id` `finishing_efficiency_recent` is unchanged
  in both while `catalogue_metric_id` / `home_column` / `away_column` moved — the required shape.
- Checked the batch-E LT05 risk on every changed `.sql` file's longest touched line — none crosses
  120 characters. The one very long line is a YAML `expression_is_true` string, which sqlfluff does
  not lint and which was already over-length before this branch.
- Confirmed `tests/test_sync_metric_docs_blocks.py` runs against the real seed and the real generated
  file, so a wrong merge or a leftover suffixed block would fail it generically, not by convention.
- Swept the full patch for credential-shaped content — no matches.
- Checked the gate table in `acceptance_evidence.md`: every exit code is a bare number alongside a
  concrete count, none of the banner / "see below" / piped-exit forms that can mask a failing run.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Binding rule: traced `finishing_efficiency_pct` from `metricRows.ts:93` back through the mart chain
  to the models that emit it, and confirmed the export selects generically rather than from a
  hardcoded field list — the field is genuinely real, not typed only into a sample.
- Honest absence: read `MetricComparison.astro`'s `hasData()` and `asNumber()`; with the sample still
  keyed on the old name both sides resolve to `null` and the row is **dropped from the group**, so it
  is omitted — never blank, never a fabricated zero.
- Wording: diffed all three `METRIC_LABELS_*` blocks and all three `site/i18n/*.json` entries — only
  the KEYS moved; every label string is byte-identical. Same for the seed's `label_en`.
- Specs: both `team.spec.json` and `fixture.spec.json` moved to the new key in the same ordered
  position as `metricRows.ts`, so the spec/label cross-check will not drift.
- Wireframes: the four team documents renamed; `metrics_display.md`'s five-ratio-metric list was
  correctly left bare because it documents the PLAYER row contract, and `12_player_stats.md` /
  `99_gaps_register.md` are player surfaces and correctly untouched.
- Swept `site_v2/src` outside `src/data` for the old key — zero hits; every remaining occurrence is
  inside the disclosed sample transient.
- Checked `rendered_page_evidence.md`'s 13 → 12 claim against what the source code actually does,
  independently rather than on faith.

## escalations
(none)
