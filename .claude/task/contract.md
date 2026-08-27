# Task contract — rename the team metrics `clean_sheets_share` to `clean_sheets_pct` and `points_capture` to `points_capture_pct`

objective: >
  Step 3 of the catalogue naming programme, MR A of six. Two renames from the `goals` and
  `outcomes` metric groups, both of the same shape: a share metric gains the `_pct` suffix the
  programme's pattern requires, and `clean_sheets_share` loses the now-doubled `share` word.

  ⛔ THIS STEP IS NOT LIKE STEPS 1 AND 2, and that is the whole reason it is split into six MRs.
  `!111` (`goals_for` → `goals`) and `!112` (`corner_kicks` → `corners`, `goalkeeper_saves` →
  `saves`) were catalogue-only: the metric moved, the model column stayed, because the column was a
  provider name that read correctly beside its siblings. Here the metric IS the column. Both names
  are computed in `int_team_season__metrics_cumulative`, so each runs through model SQL, the ymls,
  the marts and the site.

  ⭐ THE COLUMN MUST FOLLOW, AND THAT IS MACHINE-CHECKED, NOT TASTE.
  `dbt_project/tests/assert_no_uncatalogued_season_metric.sql` requires every metric-bearing column
  of `int_team_season__metrics` to be a registered `metric_id`. Renaming the `metric_id` and leaving
  the column would fail that test on the next build. The same test is why the reverse — renaming the
  column without the metric — is also not an option.

  MEASURED ON THIS BRANCH BEFORE ANY EDIT, so no number here is copied from an earlier count:
  **105 occurrences across 25 files** (`git grep -o -E 'clean_sheets_share|points_capture'` over the
  scope set below). Of those, 7 are in the GENERATED `models/docs/metric_columns.md` and are
  produced by `scripts/sync_metric_docs_blocks.py`, never hand-edited.

  ⭐ NO DESCRIPTION-BLOCK SPLIT IS EXPECTED, and it was checked rather than assumed — the mechanism
  that surprised `!111` mid-flight. Both metrics are team-only in the catalogue (verified: the seed
  holds one row each, `entity=team`), and neither `clean_sheets_pct` nor `points_capture_pct` exists
  for any entity today, so `sync_metric_docs_blocks.py` emits a bare block for each new name and no
  `__team`/`__player` pair appears. `doc('clean_sheets_share')` → `doc('clean_sheets_pct')` and
  `doc('points_capture')` → `doc('points_capture_pct')`, one for one. The regeneration is the proof,
  not this sentence.

refs: >
  **`.claude/task/escalations.log`, the block "THE METRIC CATALOGUE NAMING PROGRAMME"** — its
  rulings section dated 2026-08-26, and the complete rename tables appended 2026-08-27 under
  "⭐⭐ THE COMPLETE RENAME LIST, WRITTEN INTO THE RECORD 2026-08-27 SO IT CANNOT BE LOST". Both
  renames appear verbatim in that entry's "⛔ TEAM, 12 REMAINING" table:
  `clean_sheets_share → clean_sheets_pct` and `points_capture → points_capture_pct`.

  Their authority is RULING 1, quoted in the same entry in the CPO's own words: "points_capture
  becomes points_capture_pct / ... / clean_sheets_share becomes clean_sheets_share_pct / ...",
  narrowed by RULING 3 on doubled suffixes, also verbatim: "use the shorter as recommended" — which
  is why `clean_sheets_share_pct` became `clean_sheets_pct`. The log records the shortening as
  already applied, so this contract asserts nothing the record does not hold.

  ⛔ NO PLAN FILE IS CITED, DELIBERATELY. `feat/metric-rename-goals` and
  `feat/metric-rename-catalogue-only` were each FAILed by scope-auditor for citing a plan file
  outside the repo for a naming decision. The tables now live in the log itself.

  Branched from main **`1804a64`**, clean tree — the merge commit of `!113`, which is the first
  commit on main carrying the 2026-08-27 rename tables this contract cites. Branching from
  `dd01215` (the previous main, and what the local checkout was stale at) would have reproduced the
  session's own recorded failure variant: a citation that points at nothing when read from the
  branch's own diff.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics_cumulative.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_team_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_team_profile.yml
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/5_marts/domestic_league/mart_team_season_insights.sql
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/tests/assert_mart_team_season_insights_metric_consistency.sql
  - docs/wireframes/02_team_profile.md
  - docs/wireframes/10_home.md
  - docs/wireframes/14_team_stats.md
  - docs/wireframes/metrics_display.md
  - site_v2/src/lib/metricRows.ts
  - site_v2/src/lib/types.ts
  - site_v2/src/i18n/strings.ts
  - site_v2/src/specs/teams/team.spec.json
  - site_v2/src/components/team/TeamPerformance.astro
  - site_v2/src/components/team/MetricSeasonRow.astro
  - site_v2/src/components/team/MetricLeagueRow.astro
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

# ⚠ NOT IN SCOPE, each for a stated reason rather than by omission:
#  · site_v2/src/data/** — the GENERATED export sample. It is regenerated by
#    scripts/export_site_data.py against the PROD marts and cannot carry the new keys until
#    data:build:main has materialised them, i.e. after this merges. Never hand-edited (the fake
#    that motivated bi-analyst-reviewer's routing was two metrics typed into this sample). The
#    resulting transient is declared under decisions_taken and closes in the step's final MR.
#  · site/** — neither name appears in the retired MVP's bindings, i18n corpus or manifest
#    (verified: `git grep -l -E 'clean_sheets_share|points_capture' -- site/` is empty), so no
#    frozen file is touched by this MR at all.
#  · docs/audits/**, docs/match_preview_pages_refinement.md, docs/working_agreement.md — records of
#    HISTORY. Renaming inside a record of what happened falsifies the record.

protected_override: >
  none required. No file in scope_paths is protected.

impact_map: >
  writers: `int_team_season__metrics_cumulative` is the single home of both formulas —
    `safe_divide(points_won, 3 * games_played) as points_capture` and
    `safe_divide(clean_sheet_games, games_played) as clean_sheets_share`. Nothing else computes
    either; `int_team_season__metrics` is its final-row projection and carries them through
    `select sf.* except (match_number)`, so it is not edited and cannot drift.

  downstream: pasted from `dbt ls --select int_team_season__metrics_cumulative+ --resource-type
    model` run on this branch (dbt 1.7.19, `.venv/Scripts/dbt.exe`), not asserted from memory:
      4_intermediate.shared.int_team_competition_benchmark_metrics_long
      4_intermediate.shared.int_team_competition_benchmarks
      4_intermediate.shared.int_team_profile__yoy
      4_intermediate.domestic_league.team_season.int_team_season__deserved_vs_actual
      4_intermediate.domestic_league.team_season.int_team_season__metrics
      4_intermediate.domestic_league.team_season.int_team_season__metrics_cumulative
      5_marts.shared.mart_team_competition_benchmarks
      5_marts.shared.mart_team_profile
      5_marts.shared.mart_team_season
      5_marts.domestic_league.mart_team_season_insights
      5_marts.shared.mart_team_season_record
    Of those, four name a column and are edited: `int_team_competition_benchmark_metrics_long`
    (the UNPIVOT list), `int_team_profile__yoy`, `mart_team_profile`, `mart_team_season_insights`.
    `int_team_season__metrics`, `int_team_competition_benchmarks`, `mart_team_season`,
    `mart_team_competition_benchmarks` and `mart_team_season_record` propagate by `select *` /
    `select * except`, so their OUTPUT changes while their SQL does not.
    `int_team_season__deserved_vs_actual` reads neither name (verified by grep) — it is downstream
    of the model, not of these two columns.

  layer_rules: `scripts/check_layer_contract.py` — no per-competition staging subdirectory is
    created and no model overrides its layer materialisation; both names stay inside
    4_intermediate/5_marts, so no layer boundary moves. `assert_no_uncatalogued_season_metric`
    (column ⇄ catalogue identity) and the THREE `accepted_values` lists of the 22 benchmark
    metric_keys — two in `int_competition_benchmarks.yml` (lines 27 and 66) and a third in
    `shared.yml` (line 2080, on `mart_team_competition_benchmarks`) — are the guards that MUST move
    with the rename or the build goes red; that is the intended coupling, not collateral.
    ⚠ The count is THREE, not the two an earlier draft of this contract asserted. The `shared.yml`
    copy was found by grepping for the list rather than by recalling where it lived, and the number
    is corrected here rather than left for a reviewer to catch.
    ⛔ AND NO OFFLINE GATE ENFORCES THAT COUPLING — measured, not assumed. Reverting one entry of the
    `int_competition_benchmarks.yml` list to the old name left `dbt parse`, the docs-block check,
    description hygiene and the metric/benchmark/catalogue pytest selection ALL GREEN. The only
    guard that fires is the warehouse `accepted_values` test inside `data:build:mr`. That gap is a
    real finding of this task, it is NOT closed here (a new guard is out of this contract's scope),
    and it is filed rather than folded in.

  deploy_order: none needed, and this was checked rather than waved through. No touched model is
    incremental — `int_team_season__metrics_cumulative`, `int_team_season__metrics`,
    `int_team_profile__yoy`, `mart_team_profile` and `mart_team_season_insights` are all
    `materialized='table'`; `mart_team_season_record` and `mart_team_competition_benchmarks` are
    views; `dbt_project.yml` declares no `incremental` anywhere. So the recorded
    "renaming a column on an incremental fact NULLs history without --full-refresh" hazard does not
    fire here. `data:build:main` rebuilds every affected table in one pass on merge. There is no
    nightly SCHEDULE on GitLab today, so nothing races the merge.

  blast_radius: two columns change name on `int_team_season__metrics_cumulative`,
    `int_team_season__metrics`, `mart_team_season`, `mart_team_season_insights`,
    `mart_team_season_record` and `mart_team_profile` (the last also via its three yoy forms
    `_this_season`, `_prev_season`, `_delta_yoy`); two `metric_key` VALUES change on
    `int_team_competition_benchmark_metrics_long`, `int_team_competition_benchmarks` and
    `mart_team_competition_benchmarks`. **No number changes.** Every formula, coverage gate and
    denominator is byte-identical before and after; this is a rename, and the value-equivalence
    checker parked as #91 exists to prove exactly that class of claim once it ships.
    Consumption: `scripts/export_site_data.py` copies mart keys through unchanged, so the committed
    sample keeps the OLD keys until it is regenerated after merge — the declared transient below.

acceptance_criteria:
  - Every metric name the BUILT site renders reads in the same words after the rename as before it, in all three locales, shown by extracting the rendered metric labels from the pages under `site_v2/dist/` and reading them back — a rename must be invisible in the words a reader sees.
  - No built page and no `site_v2/src` source file outside the generated sample contains the string `clean_sheets_share` or `points_capture`, shown by a grep over `site_v2/dist/` and over `site_v2/src/` excluding `src/data/`.
  - `npm test` passes in `site_v2/`, including the metric-label cross-check that compares at least 27 CPO-validated MVP labels against `site/i18n/` and reports zero wording drift, AND that same check is watched going RED against a deliberately stale key — a green guard nobody has broken proves nothing.
  - The BUILT team page shows the "not enough games to rank" absent state where the clean-sheet share row would sit, in all three locales, shown by reading the built page's rendered text — recorded so that the missing row is read as the sample's 1-game featured season, never as a defect of this rename.

# ⚠ AMENDED MID-TASK, WITH THE CPO'S AUTHORITY — see `amendments:` at the foot. Criteria 1 and 4
# originally asked for the clean-sheet row's LABEL and VALUE to be read off the built page. Both
# were undemonstrable and had been from the start: team 33's featured season is PL 2026 with ONE
# game played, below `int_team_competition_benchmark_metrics_long`'s `>= 3 finished games` floor, so
# `season.benchmarks` is empty and `TeamPerformance.astro`'s `hasBench` guard renders the absent
# state for the WHOLE tab. `% Clean sheets` occurs 0 times across all 61 built pages, on main
# exactly as on this branch. I drafted those two without checking the sample carried benchmarks.
# A first replacement — "build main, build the branch, diff the two dist trees" — was put to the
# CPO and he rejected it, correctly: identical output is also what doing nothing produces, so that
# check cannot tell a correct rename from a missing one. It was dropped rather than argued.

decisions_taken: >
  Both names come from the record and neither is chosen here. Quoted in refs above: RULING 1 for
  `points_capture` → `points_capture_pct`, RULING 1 as narrowed by RULING 3 ("use the shorter as
  recommended") for `clean_sheets_share` → `clean_sheets_pct`.

  ⭐ WHICH METRICS TRAVEL TOGETHER IS THE BUILDER'S CALL, and the record says so in terms: the
  twelve "must be split by family, not shipped as one diff", and that split "is the builder's call,
  already taken". The grouping used across step 3 keys on the seed's own `metric_group` column so
  that "family" has a definition in the repo rather than in my taste — this MR is `goals` +
  `outcomes`. It goes first because it is the smallest of the six and touches no frozen file, while
  still exercising every layer the other five will touch.

  ⭐ `label_i18n_key` FOLLOWS `metric_id`, as it did in `!111` and `!112` (`metrics.goals_for.label`
  → `metrics.goals.label`; `metrics.corner_kicks.label` → `metrics.corners.label`). That is the
  form the file already follows, not a new rule. The catalogue's ONE deliberate id≠key
  disagreement — `shots_on_goal_per_match` declaring `metrics.shots_on_target_per_match.label` — is
  not in this set and is not touched.

  ⛔ A LIVE TRANSIENT IS CREATED AND IS DECLARED HERE RATHER THAN DISCOVERED LATER. The committed
  export sample under `site_v2/src/data/` can only be regenerated against the prod marts, which do
  not carry the new columns until `data:build:main` runs on merge. So between this merge and the
  step's closing refresh MR the sample serves the OLD keys while the page asks for the new ones.
  Precedent: `!109` ("refresh the committed export sample after #90") did the same sequencing. The
  site is unlisted and `deploy:site-v2` is manual-only, so nothing public degrades. This joins the
  two transients the record already carries and is written into `escalations.log` in the same commit.

  ⚠ WHAT THAT LOOKS LIKE ON THE PAGE DIFFERS BY PANEL, and an earlier draft of this contract had it
  wrong: it said the row "renders its label correctly and its value as the en-dash", which is true
  of ONE of the two panels only. `TeamPerformance.astro` builds `leagueGroups` with
  `benchByKey.has(keyOf(r))`, so in the **vs-the-league** panel a metric with no benchmark row is
  OMITTED ENTIRELY — 14_team_stats.md §6's "metric-absent = omitted, never a zero bar". The
  **vs-last-season** panel renders all 16 and lets a null delta dash out honestly. Corrected in
  place rather than annotated beside the wrong sentence.
  ⭐ Neither state can occur on any built page today in any case: the sample's featured season is
  PL 2026 with one game played, so `hasBench` is false and the whole tab renders its absent state.
  Found by bi-analyst-reviewer in round 1, which read the mechanism and declined to FAIL on it. The
  wording is fixed anyway because MRs B–F reuse this paragraph — a wrong sentence here is a wrong
  sentence six times.

  THRESHOLD DECLARATIONS. No NEW MECHANISM: no new script, macro, hook, test or dependency — every
  guard and generator involved already exists and is re-run, not written. No RECURRING COST: no new
  CI job, no extra build, no schedule; `data:build:main` rebuilds the same models it rebuilds for
  any model edit, and the renamed columns are the same width and count as the ones they replace.

decisions_reserved:
  - none: both names are ruled in `escalations.log` and quoted above, and the only judgement this
    contract makes — which metrics ride together — is the builder's call the record assigns.

done_when:
  - `python scripts/sync_metric_docs_blocks.py --check` passes with no drift after regeneration.
  - `python scripts/check_description_hygiene.py`, `python scripts/check_layer_contract.py` and
    `python scripts/check_ui_i18n_metrics.py` all pass.
  - `python -m pytest -q` passes with no new failures against the count on `1804a64`.
  - `DBT_PROFILES_DIR=C:/Users/Rami/.dbt .venv/Scripts/dbt.exe parse` is clean, with zero dangling
    `doc()` references.
  - `python -m sqlfluff lint` is clean on every changed model, run from the repo root with the full
    rule set.
  - `cd site_v2 && npm test && node scripts/check-page-specs.mjs` passes.
  - `git grep -n -E 'clean_sheets_share|points_capture[^_]' ` returns hits ONLY in the excluded
    history/record paths named above and in the not-yet-regenerated `site_v2/src/data/`.
  - Each acceptance criterion is demonstrated in `.claude/task/acceptance_evidence.md` under
    `criteria_demonstrated:`, read from the BUILT site, never from source.
  - At least two mutations are watched going RED and then restored. Run and recorded: a stale
    `label_i18n_key` in the seed turns `check-metric-labels.test.mjs` red; a stale `metric_id` in
    the seed turns `sync_metric_docs_blocks.py --check` red; a dangling `doc()` in
    `domestic_league.yml` turns BOTH `check_description_hygiene.py` and `dbt parse` red. A fourth,
    a stale `accepted_values` entry, SURVIVED the whole offline suite — reported as a survivor, not
    quietly dropped, and recorded in `impact_map` above.

amendments: >
  2026-08-27: acceptance_criteria 1 and 4 REPLACED — authority: the CPO, in chat this session,
  asked plainly ("Before I started you approved a short list... I want to swap those two for two I
  can actually prove — yes or no?") and answered "then go ahead". Content: both original criteria
  asked for the clean-sheet row's label and value to be READ OFF THE BUILT PAGE. The row renders on
  no built page, and did not before this branch either — team 33's featured season is PL 2026 with
  one game played, under the `>= 3 finished games` benchmark floor, so `hasBench` is false and the
  Performance tab renders its absent state. `% Clean sheets` occurs 0 times across all 61 built
  pages. Criterion 1 now asks that no rendered metric wording changed anywhere; criterion 4 records
  the absent state so the missing row is never mistaken for a defect of this rename. Criteria 2 and
  3 are unchanged, and criterion 3 gained the requirement that the guard be watched going red.
  ⚠ An intermediate proposal — build main, build the branch, diff the two `dist` trees — was put to
  the CPO and REJECTED by him: identical output is also what doing no work produces, so the check
  cannot distinguish a correct rename from a missing one. Dropped, not argued.
  ⚠ Written on a clean tree: the code changes were stashed by EXPLICIT PATH
  (`git stash push -m TEMP-mrA-code-while-contract-amended -- dbt_project docs site_v2`), the
  contract amended, then popped immediately. `.claude/task/` was never in the stash's path set.
