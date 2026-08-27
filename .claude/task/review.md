# Review — refactor/metric-rename-team-set-pieces-goalkeeping — 2026-08-27

> Step 3 of the metric catalogue naming programme, MR B of six:
> `corner_kicks_per_match` → `corners_per_match`, `save_ratio` → `saves_pct`.
> Branched from main `a70b7e2`. Closes the transient `!112` opened, where the totals were renamed
> and both rates were left behind.

diff_sha256: e1af7d2656e06de6da7fca2e0a7d7d390ed127a40be7e9e380f36f426a440868

rounds: 1

> Four reviewers, one round, four PASSes. Two non-blocking findings from bi-analyst-reviewer were
> folded into `acceptance_evidence.md` (which is hash-excluded, so no round was needed): that the
> **Goalkeeping group heading disappears entirely** — `saves_pct` was its only row, verified 0
> occurrences of `Goalkeeping` on the built EN page — and that `rendered_page_evidence.md` still
> holds an unrelated earlier task's content, which is named rather than silently left.

## scope-auditor
VERDICT: PASS
risks_checked:
- Diff file set vs `scope_paths`: all 34 touched files (dbt models/ymls, seed, docs, generated `metric_columns.md`, `site/i18n/*.json`, `site/match-preview/metric_bindings.csv` + `metric_definitions.json`, `site_v2/src/lib/metricRows.ts`, `site_v2/src/i18n/strings.ts`, two spec.json files, `MetricSeasonRow.astro`) match entries in `contract.md`'s `scope_paths`; nothing touched outside it.
- Naming authority: cross-checked `corner_kicks_per_match → corners_per_match` and `save_ratio → saves_pct` against `.claude/task/escalations.log:5351-5445` (RULING 1, RULING 3, and item 5/item 3 of the "SIX, ENUMERATED" table) and the "TEAM, 12 REMAINING" list — both renames are verbatim-ruled, not chosen in this diff.
- Frozen `site/` tree edit: verified `metric_bindings.csv` and `metric_definitions.json` keep the old `live_id` (`corner_kicks_per_match_recent`, `save_ratio_recent`) untouched and rename only `catalogue_metric_id`/`home_column`/`away_column`/i18n keys, matching the contract's "only the catalogue-id plumbing, no live_id, no wording" claim.
- `accepted_values` guard sync: confirmed all three 22-name lists (`int_competition_benchmarks.yml` ×2, `shared.yml` ×1) were updated with the new names — the contract flags these as unenforced by an offline gate (#96) and they were checked by eye as required.
- Doc-sync: `docs/wireframes/02_team_profile.md`, `14_team_stats.md`, `metrics_display.md` all updated in the same diff — no stale doc left behind describing the old metric names.
- Secrets/credentials sweep across the full diff: nothing credential-shaped, no widened permissions.
- Threshold declarations: `decisions_taken` states no new mechanism, no recurring cost; confirmed no new file, script, macro, hook, dependency or CI job appears in the diff — every edit is a rename inside existing generators/guards.
- `decisions_reserved`: contract states "none," and nothing in the diff decides a §10-reserved item silently — product wording is explicitly unchanged, verified byte-identical in the i18n label strings, with only the JSON key names shifted.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: both renames stay inside `4_intermediate`/`5_marts` (formulas untouched, only identifiers renamed). `int_team_season__metrics_cumulative.sql`, `int_team_momentum__metrics.sql` and `int_team_season_record.sql` show only comment-text renames where the coverage-count columns themselves (`games_with_save_stats`, `goals_against_in_save_games`) are unrelated to the two renamed metric columns. No staging/base/core file touched, no `ref('mart_*')` introduced upstream. No new formula, no redefinition.
- Catalogue governance (A1): the two seed rows have only `metric_id`/`label_i18n_key` changed; label text, formula, entity, group, direction all byte-identical — a rename, not a redefinition.
- Three 22-name `accepted_values` lists (open gap #96, no offline gate): read all three in the diff — `int_competition_benchmarks.yml` (twice) and `shared.yml` (`mart_team_competition_benchmarks`) — each counted to exactly 22 entries both before and after, with both names swapped in place and nothing dropped or duplicated.
- `mart_team_momentum`'s second computation of both formulas (open #93): confirmed it independently recomputes `safe_divide(...)` for both metrics rather than reading the cumulative model, and that the rename was applied consistently there too, plus in the range test in `shared.yml` (`momentum_team_saves_pct_in_range`). The duplication is pre-existing, disclosed and filed separately — not introduced or worsened here.
- Consumption layer (A5): `metric_bindings.csv`, `metric_definitions.json`, `site/i18n/*.json`, `strings.ts`, `metricRows.ts`, both `*.spec.json` — all changes are identifier renames of existing mapping data (live_id kept, `catalogue_metric_id` and column aliases updated); `mart_matchday_insights.sql` only re-aliases already-computed mart columns (`mh.saves_pct as home_saves_pct_recent`). No new math, filter, ranking or taxonomy logic anywhere in scope.
- Residual old-name sweep: zero hits across `dbt_project/`; in `site_v2/src` only `src/data/**` (the declared out-of-scope transient); in `site/` only the retired MVP's own `live_id`s and the two files explicitly declared out of scope with a stated reason.
- Authority chain: the quoted rulings in `refs:` verified verbatim against the log — RULING 1, RULING 3, enumerated items 3 and 5, and "apply the suggested changes to ensure consistency"; the MR-B grouping is explicit in the log.
- Impact map (A6): the pasted `dbt ls` output cross-checked against the actual edited-file set; `mart_team_momentum`, `int_team_momentum__metrics` and `mart_matchday_insights` correctly called out as edited-but-absent-from-lineage, consistent with what the diff shows.
- No new mechanism, no hardcoded competition identifier, no incremental-model rename hazard (all touched models are `table`/`view`) — checked, none present.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Confirmed both catalogue rows are byte-identical renames — only `metric_id` and `label_i18n_key` changed; formula (`sum(corner_kicks)/count(*)`; `sum(goalkeeper_saves)/sum(goalkeeper_saves+goals_against)`), format, `metric_group`, tier, `direction` and the plain-English interpretation column are untouched. No formula, coverage-gate or denominator change rode along.
- Direction correctness post-rename: `corners_per_match` stays `higher_better` (own corners won — the catalogue honestly flags it "a weak proxy", unchanged), `saves_pct` stays `higher_better`. Both remain correct.
- Edge-case honesty preserved verbatim: `saves_pct`'s description still states the self-bounding denominator and nulls on no save-covered games; `corners_per_match`'s still ties to "available team stats" coverage. Only the doc-block anchor name moved.
- No composite/index smuggling: both remain single transparent ratios over raw provider counts.
- Verified the CPO approval quoted in the contract against the log directly — `save_ratio → saves_pct` is RULING 1 narrowed by RULING 3 plus enumerated item 3; `corner_kicks_per_match → corners_per_match` is enumerated item 5. Quotes match exactly; no fabricated authority.
- Checked all three `accepted_values` lists updated consistently with no stale entries, and that the pairing with the untouched sibling `corners_against_per_match` (still `lower_better`) stays internally consistent — won vs conceded corners correctly diverge in direction.
- Checked no rendered wording changed anywhere in `site/i18n/*.json`, `strings.ts` or `metric_definitions.json` — "Ø Corners", "% Save percentage", "% Gehaltene Torschüsse" etc. are byte-identical; only keys and catalogue ids moved, so no fan-facing meaning shifted.
- No new metric or unrelated addition rode along in the seed — the diff touches exactly the two declared rows.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- **Transient visibility/disclosure.** Read `MetricComparison.astro`: `hasData()` looks up `home?.[def.field]`/`away?.[def.field]` and the group filter drops any group left with zero rows. Since `metricRows.ts` now binds `corners_per_match`/`saves_pct` while the committed sample still carries the old keys (confirmed by grep: 214 hits across `teams/33.json` and 17 fixture files, untouched by this diff), the two rows — and the whole **Goalkeeping** group, since `saves_pct` is its only row — disappear from the built comparison until the sample is regenerated. That is exactly what the contract, the log and the evidence disclose (16→14 rendered names, all 51 fixture pages, three locales), and it is the codebase's existing honest-absent path, matching `14_team_stats.md` §6. The disclosure holds up against the actual component logic and the actual sample contents. Confirmed `scripts/export_site_data.py` selects marts with `select *` rather than naming columns, so nothing blocks the transient from closing on the next refresh.
- **Frozen `site/` tree edits.** Read the full context around the changed keys in `site/i18n/en.json`; `de.json`/`fi.json` confirm the same. Only the JSON key changed; every `"label"`/`"description"` string is byte-identical. `metric_bindings.csv` keeps `live_id` unchanged and renames only `catalogue_metric_id`/`home_column`/`away_column`, consistent with `mart_matchday_insights`' new aliases. `metric_definitions.json` matches (regenerated). `metric_manifest.json`, correctly out of scope, still references only the unchanged `live_id`s — checked directly, no drift.
- **Binding-rule sweep of `site_v2/src/**`.** Search for the two old names returns hits only inside `src/data/**` (the declared transient); `metricRows.ts`, `strings.ts`, `MetricSeasonRow.astro` and both spec files are fully renamed and internally consistent, so `check-metric-labels.test.mjs`'s byte-identity test compares the right keys post-rename rather than silently skipping them.
- **Locked contract / no reordering / no metric creep.** `metricRows.ts` shows `tier`, `group`, `format`, `direction` unchanged for both rows — only `field`/`labelKey` renamed. `metrics_display.md` rows keep their tier/group/position and the tier-shape line is untouched. No new metric on any surface; no naked-percentage or fabricated-zero pattern introduced.
- **Stale-reference sweep of `docs/wireframes/`.** Grepped the whole directory, not just the two files in scope — zero hits, so no wireframe still cites the retired ids.
- **`rendered_page_evidence.md`.** Exists but holds an unrelated earlier task's content and says nothing about this branch. `acceptance_evidence.md` independently supplies genuine built-output evidence for the flagged risk (locale-by-locale rendered-name counts from `site_v2/dist/`, 16→14, methodology disclosed, with a self-caught substring-matching bug corrected mid-task), so the built-output requirement is substantively met — noted rather than treated as a silent gap.

## escalations
(none)
