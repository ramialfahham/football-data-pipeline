# Review — refactor/metric-rename-team-goals-outcomes — 2026-08-27

> Step 3 of the metric catalogue naming programme, MR A of six:
> `clean_sheets_share` → `clean_sheets_pct`, `points_capture` → `points_capture_pct`.
> Branched from main `1804a64`.

diff_sha256: 3fd9bfcf430248ac3805b97306aae94e7b9fa2d7292681ab7ee8d0cfed6b3208

rounds: 2

> ROUND 1 → ROUND 2, and what changed: **no code file**. The cumulative code diff is byte-identical
> between the two rounds. bi-analyst-reviewer's round-1 PASS carried a precision finding it
> explicitly declined to fail on — the `decisions_taken` paragraph described the declared transient
> as the row "renders its label correctly and its value as the en-dash", which is true of the
> vs-last-season panel only; the vs-the-league panel OMITS an unbenchmarked metric entirely via
> `benchByKey.has(keyOf(r))`. The paragraph was corrected in place rather than annotated, because
> MRs B–F of this step reuse it. Correcting `contract.md` moves the hash, so the two reviewers whose
> territory the change touches were re-run; **analytics-engineer-reviewer and
> football-analytics-expert-reviewer carry their round-1 verdicts forward unchanged**, their
> territories (the models, the catalogue seed) being byte-identical across the two rounds.

## scope-auditor
VERDICT: PASS
risks_checked:
- Verified the stated round-1→round-2 delta is exactly what it claims: diffed `contract.md`'s `decisions_taken` correction against `site_v2/src/components/team/TeamPerformance.astro` (lines 31-131) — `leagueGroups` does filter with `benchByKey.has(keyOf(r))` (row 67, omits absent metrics entirely from the vs-league panel) while the vs-last-season panel renders all rows with a possibly-null delta; both panels sit inside the same `hasBench` gate, so on the current sample (PL 2026, 1 game played) neither state is reachable and the whole tab shows the absent state — the corrected paragraph is factually accurate and no code changed alongside it.
- Confirmed the naming authority for both renames (`clean_sheets_share`→`clean_sheets_pct`, `points_capture`→`points_capture_pct`) exists verbatim in `.claude/task/escalations.log` lines 5351-5445 — RULING 1 and RULING 3 quote the CPO directly, and both names appear in the "TEAM, 12 REMAINING" table exactly as the contract cites them; this is not a builder reconstruction.
- Checked every file touched in the cumulative diff against `contract.md`'s `scope_paths` — all 26 non-task-artifact files (seeds, intermediate/mart models+ymls, wireframes, i18n strings, metricRows/types/spec, Astro components) are listed in scope; no drift-by-addition found.
- Checked `impact_map` against the diff: the `dbt ls --select int_team_season__metrics_cumulative+` lineage list matches the models actually edited (`int_team_competition_benchmark_metrics_long`, `int_team_profile__yoy`, `mart_team_profile`, `mart_team_season_insights`), and the disclosed guard gap (accepted_values lists not offline-enforced) is filed as an open finding rather than silently dropped or smuggled as "fixed" — this satisfies the evidence bar, it is not hand-waved.
- Checked `decisions_taken`'s threshold declarations against the diff: no new script/macro/hook/test/CI job appears anywhere in the patch, and no cadence or query-volume change is present — the "no new mechanism, no recurring cost" claim holds up against the actual file list.
- Swept the full diff text for credential-shaped strings (keys, tokens, connection strings, widened permissions) — none found; all changes are metric-id renames across SQL, yml, csv, docs and TS/Astro source.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- This is a legitimate delta re-review: I previously passed an earlier hash of this same branch, and the round-1 finding (`decisions_taken` paragraph wrongly generalizing the transient's on-page appearance) is the only thing that changed — no code file differs from the version I already reviewed.
- Verified the corrected paragraph against the actual code in `site_v2/src/components/team/TeamPerformance.astro`. Line 67, `leagueGroups`, filters `METRIC_ROWS` with `benchByKey.has(keyOf(r))` — a metric with no benchmark row is omitted entirely from the vs-the-league panel, exactly as the corrected text now says. Line 69–72, `seasonGroups`, applies no such filter — all `METRIC_ROWS` render in the vs-last-season panel regardless of benchmark presence, matching "renders all 16." Traced `MetricSeasonRow.astro` and `signedDelta()`/`formatValue()` in `site_v2/src/lib/format.ts`: a null/undefined delta or value renders the en-dash (`DASH`) rather than a fabricated zero, confirming "lets a null delta dash out honestly" is accurate, not merely asserted.
- Checked the corrected paragraph's citation, `14_team_stats.md §6's "metric-absent = omitted, never a zero bar"`, against the actual wireframe. `docs/wireframes/14_team_stats.md:169`, in section "6. States," reads "Metric absent | no row for that `metric_key` … | that row omitted (not a zero bar)" — a faithful paraphrase, not a fabricated citation.
- Confirmed the paragraph's closing claim — that neither panel state is reachable on any built page today because the sample's featured season (team 33, PL 2026, 1 game played) is below the `>= 3 finished games` benchmark floor, so `hasBench` is false and the whole tab renders the absent state (`TeamPerformance.astro` lines 35, 75–131) — is consistent with the code path: `hasBench = benchByKey.size > 0`, and when false the component renders only the `notRankable` absent-state branch, never reaching either `leagueGroups` or `seasonGroups`.
- No other file in the cumulative diff changed since my prior pass, per the task framing (dbt models, wireframes, `metricRows.ts`, `strings.ts`, `types.ts`, `team.spec.json`, `MetricLeagueRow.astro`, `MetricSeasonRow.astro`), so no re-audit of the binding rule, locked metric order, naked-percentage rule, or i18n label parity was performed this round — those were the substance of the prior PASS and remain unchanged.

## analytics-engineer-reviewer
VERDICT: PASS
> Verdict from ROUND 1, carried forward: this reviewer's territory (`dbt_project/**`) is
> byte-identical between round 1 and round 2. Only `contract.md` prose changed.
risks_checked:
- Catalogue governance (A1): both renames (`clean_sheets_share`→`clean_sheets_pct`, `points_capture`→`points_capture_pct`) are quoted verbatim from `escalations.log`'s RULING 1/RULING 3 and appear in the 2026-08-27 "COMPLETE RENAME LIST" table; `dbt_project/seeds/metric_catalogue.csv` rows updated accordingly — no uncatalogued rename found.
- Formula/value equivalence (same-window rule): diffed `int_team_season__metrics_cumulative.sql` — both `safe_divide(...)` expressions are byte-identical before/after, only the `as` alias changed. No computation, coverage gate or denominator touched.
- Layer placement: the metric stays computed in `4_intermediate/.../int_team_season__metrics_cumulative.sql` exactly where it already lived (not moved layers); `int_team_season__metrics` still projects via `select sf.* except (...)`, confirmed by reading the model — no new logic introduced at any layer.
- Consumption layer (A5): read all touched `site_v2/` files (`metricRows.ts`, `types.ts`, `i18n/strings.ts`, `TeamPerformance.astro`, `MetricSeasonRow.astro`, `MetricLeagueRow.astro`, `team.spec.json`) — every change is a field-name/label-key rename or comment update, no metric math, ranking, or derivation added.
- Tests kept in lockstep: range tests (`int_team_season.yml` ×2), consistency test (`assert_mart_team_season_insights_metric_consistency.sql`), and all three `accepted_values` lists (`int_competition_benchmarks.yml` ×2, `shared.yml` ×1) were all updated to the new names — verified via grep that no old name remains in `dbt_project/`.
- Downstream completeness: grepped the live repo tree (post-diff) for `clean_sheets_share`/`points_capture` — zero hits anywhere under `dbt_project/`, confirming the rename is complete for every warehouse consumer, including `mart_team_season.sql`, `mart_team_season_record.sql` and `int_team_competition_benchmarks.sql`, which the contract claims propagate by `select *` and were correctly left unedited.
- Declared transient: `site_v2/src/data/teams/33.json` (the generated export sample) still carries the old names — matches the contract's disclosed, scoped-out transient (regenerated post-merge against prod marts); not a silent gap.
- Impact map: downstream lineage list cross-checked by grepping for `ref('int_team_season__metrics_cumulative')` and `ref('int_team_season__metrics')` — matches the contract's pasted `dbt ls` output.
- Hardcoded competition identifiers: none introduced in this diff.

## football-analytics-expert-reviewer
VERDICT: PASS
> Verdict from ROUND 1, carried forward: this reviewer's trigger
> (`dbt_project/seeds/metric_catalogue.csv`) is byte-identical between round 1 and round 2.
risks_checked:
- Formula integrity: confirmed both renamed metrics carry byte-identical formulas pre/post rename. `clean_sheets_pct` = `countif(goals_against = 0) / count(*)` and in `int_team_season__metrics_cumulative.sql` = `safe_divide(clean_sheet_games, games_played)`. `points_capture_pct` = `sum(case result when 'W' then 3 when 'D' then 1 else 0 end) / (3*count(*))` and cumulative model `safe_divide(points_won, 3 * games_played)`. Both are standard, well-understood football ratios (share of matches shut out; share of available points won) — no defect.
- Direction correctness: both rows retain `higher_better`. Correct on football grounds — more clean sheets and more points captured relative to available are both unambiguously good; neither is a "conceded/cards/lower-is-better" class metric. No direction flip introduced.
- Zero-denominator / coverage honesty: both use `safe_divide`/`count(*)` unchanged, no new caps or silent zero-fill introduced; description text (`clean_sheets_pct` and `points_capture_pct` doc blocks in `dbt_project/models/docs/metric_columns.md`) is untouched apart from the name substitution — still plain and accurate for a fan.
- No composite/index introduced: both remain single transparent ratios, not scores; no fabricated probability or blended index appears anywhere in the diff.
- Cross-reference consistency: the sibling `clean_sheets` (count) row's description was correctly updated to point at the new name, so the count/share pairing documented in `docs/wireframes/14_team_stats.md` and `metrics_display.md` stays internally consistent — no orphaned reference to the old name left in a description a reader would see.
- CPO approval: verified directly in `.claude/task/escalations.log` (not just via the contract's quote) — lines 5352-5353 "points_capture becomes points_capture_pct / ... / clean_sheets_share becomes clean_sheets_share_pct" (RULING 1) and lines 5369-5370 "use the shorter as recommended" (RULING 3), which is why `clean_sheets_share_pct` shortened to `clean_sheets_pct`. Both renamed rows in this diff match that ruling exactly — no unapproved metric change slipped in under cover of the ruling.
- Scope check for a smuggled formula/direction change riding along with the rename: read every hunk touching `metric_catalogue.csv`, `schema.yml`, `int_team_season.yml`, `int_team_season__metrics_cumulative.sql`, `int_competition_benchmarks.yml`, `int_team_competition_benchmark_metrics_long.sql`, `int_team_profile.yml`/`.sql`, `mart_team_profile.sql`, `shared.yml`, `domestic_league.yml`, `mart_team_season_insights.sql`, the consistency test, wireframes and site_v2 files — every hunk is a 1:1 identifier substitution; no numeric literal, comparison operator, join, or filter condition changed anywhere in the diff.

## escalations
(none)
