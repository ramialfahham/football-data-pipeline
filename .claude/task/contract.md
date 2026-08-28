# Task contract — rename the three `shooting` share metrics (batch C)

objective: >
  Step 3 of the metric catalogue naming programme, **MR C of six**. The three share metrics in the
  seed's `shooting` group:

      shot_accuracy      → shots_on_goal_pct
      danger_zone_ratio  → shots_inside_box_pct
      shot_share         → shots_share_pct

  They ride together because "family" is defined by the seed's own `metric_group` column, not by the
  builder's taste — the split recorded in `escalations.log`'s `2026-08-27 STEP 3 STARTS` entry.

  All three are COMPUTED COLUMNS in `int_team_season__metrics_cumulative`, so each runs through model
  SQL, the ymls, the marts and the site — not a seed-only rename like `!111` / `!112`.

  ⭐ THE COLUMN MUST FOLLOW THE METRIC, and it is machine-checked rather than a matter of taste:
  `dbt_project/tests/assert_no_uncatalogued_season_metric.sql` requires every metric-bearing column
  of `int_team_season__metrics` to be a registered `metric_id`.

  MEASURED ON THIS BRANCH BEFORE ANY EDIT, from the REPO ROOT:
  **412 occurrences** — `shot_accuracy` 177, `danger_zone_ratio` 185, `shot_share` 50 — of which
  **267 are the generated export sample** (121 / 121 / 25) and **145 are live surfaces**
  (56 / 64 / 25).
  ⚠ A FIRST ATTEMPT AT THIS COUNT RETURNED 38 / 46 / 21 AND WAS WRONG. The shell was still inside
  `dbt_project/` from the `dbt ls` call above, and `git grep` scopes to the CWD, so those were
  dbt-only counts that looked entirely plausible. CWD persists between calls; the figures above were
  re-taken with `cd /d/Projects/football-data-pipeline` asserted in the same command.

  ⭐ NO DESCRIPTION-BLOCK SPLIT, checked rather than assumed — the mechanism that surprised `!111`.
  `git grep -lE "shots_on_goal_pct|shots_inside_box_pct|shots_share_pct"` over the whole repo returns
  **nothing**: none of the three new names exists for any entity today, so the generator emits one
  bare block each. (That hazard is real but it fires on **F**, where `finishing_efficiency` exists
  for both entities.) The regeneration is the proof, not this sentence.

refs: >
  **`.claude/task/escalations.log`, the block "THE METRIC CATALOGUE NAMING PROGRAMME"** — rulings
  dated 2026-08-26, complete tables appended 2026-08-27. All three renames appear verbatim in its
  "⛔ TEAM, 12 REMAINING" table.

  Per-name authority, quoted rather than summarised:
  · `shot_accuracy` → `shots_on_goal_pct` and `danger_zone_ratio` → `shots_inside_box_pct` are
    **RULING 4**, three names put to the CPO one per line and answered one per line, verbatim:
    "1. deserved_points_gap / 2. shots_inside_box_pct / 3. shots_on_goal_pct".
  · `shot_share` → `shots_share_pct` is **RULING 1** ("shot_share becomes shot_share_pct") as
    corrected by **item 2 of the enumerated six** (`shot_share_pct` → `shots_share_pct`, "singular
    where the family is plural"). The CPO's reply to those six, verbatim: "apply the suggested
    changes to ensure consistency."

  ⛔ NO PLAN FILE IS CITED. `feat/metric-rename-goals` and `feat/metric-rename-catalogue-only` were
  each FAILed for citing one; the tables live in the log itself.

  Branched from main **`9e2aaf9`**, clean tree — the main carrying `!118`, so the export sample is
  freshly rolled forward and this branch's before/after measurement starts from a true 16.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics_cumulative.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_team_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_team_profile.yml
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/mart_team_season_record.sql
  - dbt_project/models/5_marts/shared/mart_team_momentum.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/5_marts/domestic_league/mart_team_season_insights.sql
  - dbt_project/models/5_marts/domestic_league/mart_matchday_insights.sql
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - docs/wireframes/01_fixture_page.md
  - docs/wireframes/02_team_profile.md
  - docs/wireframes/14_team_stats.md
  - docs/wireframes/99_gaps_register.md
  - docs/wireframes/metrics_display.md
  - scripts/export_site_data.py
  - scripts/check_description_hygiene.py
  - tests/test_description_hygiene.py
  - site/match-preview/metric_bindings.csv
  - site/match-preview/metric_definitions.json
  - site/i18n/de.json
  - site/i18n/en.json
  - site/i18n/fi.json
  - site_v2/src/lib/metricRows.ts
  - site_v2/src/i18n/strings.ts
  - site_v2/src/specs/teams/team.spec.json
  - site_v2/src/specs/competition/matches/fixture.spec.json
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

# ⚠ NOT IN SCOPE, each for a stated reason rather than by omission:
#  · site_v2/src/data/** — the GENERATED export sample. `!118` rolled it forward two commits ago and
#    it cannot carry a name renamed after that export. Never hand-edited. This re-opens the declared
#    transient; see decisions_taken for the measured size (16 → 15 rows, no heading lost).
#  · site/team-season/index.html — frozen PAGE CODE of the product retired 2026-07-21. It reads
#    `row.shot_accuracy` and `t("metrics.shot_accuracy.label", "<German fallback>")`. `!116` left the
#    byte-identical construct untouched for `corner_kicks_per_match` and `save_ratio`; same call here,
#    established precedent, not a new decision.
#  · site/match-preview/metric_manifest.json — holds the retired MVP's own `live_id`s
#    (`shot_accuracy_recent`, `danger_zone_ratio_recent`). Those are that product's display ids, not
#    catalogue ids; `check_ui_i18n_metrics.py` maps them THROUGH the bindings, so they stay valid.
#  · docs/match_preview_pages_refinement.md — a record of HISTORY, and its only hit is
#    `home_shot_share_recent`, a column `mart_matchday_insights` does not even emit today (verified:
#    it aliases only shot_accuracy and danger_zone_ratio). Renaming inside a record of what happened
#    falsifies the record. Same call as `!116`.
#  · docs/working_agreement.md and dbt_project/models/5_marts/shared/mart_player_profile.sql — both
#    name a PLAYER `shot_accuracy` that was invented and REJECTED (Appendix A anti-pattern A1: "no
#    goal_conversion, no player shot_accuracy"). No such metric exists to rename, and renaming it
#    would falsify a record of a mistake.

protected_override: >
  none required. No file in scope_paths is protected.

impact_map: >
  writers: `int_team_season__metrics_cumulative` is the single home of all three formulas.
    `int_team_season__metrics` is its final-row projection via `select sf.* except (match_number)`,
    so it is not edited and cannot drift.
    ⚠ `mart_team_momentum` computes `shot_accuracy` and `danger_zone_ratio` AGAIN — a second copy of
    ~20 team formulas, open as **#93**. Its columns carry the same metric names and are renamed here
    too; the duplication itself is NOT addressed by this MR and #93 stays open.

  downstream: pasted from `dbt ls --select int_team_season__metrics_cumulative+ --resource-type model`
    run on this branch (dbt 1.7.19, `.venv/Scripts/dbt.exe`) BEFORE the first structural edit:
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
    ⚠ THAT LIST IS NOT THE WHOLE EDIT SET, and saying so is the correction `!114`'s review left.
    `mart_team_momentum` and `mart_matchday_insights` do NOT appear in it — momentum recomputes the
    metrics from its own window (#93) and `mart_matchday_insights` reads THAT — yet both are edited.
    A contract that took the lineage as the file list would have missed them.

  layer_rules: `check_layer_contract.py`; all three names stay inside 4_intermediate/5_marts, so no
    layer boundary moves. The coupled guards are `assert_no_uncatalogued_season_metric` (column ⇄
    catalogue identity) and the THREE 22-name `accepted_values` lists, located exactly:
    `int_competition_benchmarks.yml:27`, `int_competition_benchmarks.yml:66`, `shared.yml:2080`.
    Each carries `shot_accuracy` and `danger_zone_ratio` at positions 5 and 6; `shot_share` is NOT
    one of the 22 and must not be added.
    ⛔ NO OFFLINE GATE ENFORCES THOSE THREE LISTS — proved by a surviving mutation on `!114`, filed
    as **#96**. Only the warehouse `accepted_values` test in `data:build:mr` catches a miss, so they
    are checked BY EYE here as well as by the build.

  deploy_order: none needed. No touched model is incremental; `data:build:main` rebuilds every
    affected table in one pass on merge.

  blast_radius: three columns rename on the season, momentum and profile models plus
    `mart_team_profile`'s yoy forms; two `metric_key` VALUES change on the benchmark chain
    (`shot_share` is not benchmarked); and two `home_*_recent` / `away_*_recent` aliases change on
    `mart_matchday_insights:149-150,161-162`, which feeds only the retired MVP's export. **No number
    changes** — every formula is byte-identical.

acceptance_criteria:
  - Every metric name the BUILT site renders reads in the same words after the rename as before it, in all three locales, shown by extracting the rendered metric labels from the pages under `site_v2/dist/` and comparing each against the untouched CPO-validated wording in `site/i18n/<loc>.json`.
  - No built page and no `site_v2/src` source file outside the generated sample contains the string `shot_accuracy`, `danger_zone_ratio` or `shot_share`, shown by a grep over `site_v2/dist/` and over `site_v2/src/` excluding `src/data/`.
  - `npm test` passes in `site_v2/`, including the metric-label cross-check against `site/i18n/`, AND that check is watched going RED against a deliberately stale key — a green guard nobody has broken proves nothing.
  - The BUILT team page still shows the "not enough games to rank" absent state where these rows would sit, in all three locales, shown by reading the built page's rendered text — recorded so the missing rows are read as the sample's one-game featured season and never as a defect of this rename.

decisions_taken: >
  All three names come from the record and none is chosen here; the authorities are quoted per name
  in `refs`. THE FOUR ACCEPTANCE CRITERIA ABOVE ARE THE CPO'S STANDING SET for MRs B–F ("do it",
  recorded in `escalations.log` with the list it answered) — reproduced, not re-drafted, and
  deliberately not re-put to him.

  ⭐ `label_i18n_key` FOLLOWS `metric_id`, as in `!111`, `!112`, `!114` and `!116`. The catalogue's
  one deliberate id≠key disagreement (`shots_on_goal_per_match` → `metrics.shots_on_target_per_match.label`)
  is not in this set and is not touched.
  ⚠ AND IT IS ADJACENT HERE, so it is worth stating: `shot_accuracy` becomes `shots_on_goal_pct`,
  which reads like the existing `shots_on_goal_per_match`. They are DIFFERENT metrics — a share
  versus a rate — and neither inherits the other's label or key.

  ⭐ THE FROZEN `site/` TREE IS EDITED ONLY WHERE A LIVE GATE FORCES IT, and only the catalogue-id
  plumbing: `metric_bindings.csv`'s `catalogue_metric_id` plus its `home_column`/`away_column`, the
  `metrics.<id>` KEYS in `site/i18n/*.json`, and the REGENERATED `metric_definitions.json`. The gate
  is `check_ui_i18n_metrics.py`, which walks manifest `live_id` → bindings `catalogue_metric_id` →
  `site/i18n/*.json`. **No wording changes, no page code, no `live_id`.** `shot_share` has no `site/`
  presence at all.

  ⭐ TWO ILLUSTRATIVE STRINGS ARE RENAMED, and the judgement is declared rather than passed silently:
  `scripts/check_description_hygiene.py:118` and `tests/test_description_hygiene.py:287` use
  `shot_share` as an EXAMPLE inside a comment and a test fixture ("feeds shot_share downstream").
  Renaming them is zero-risk and clears the dead name; a reviewer who thinks an example string
  should have been left alone can see the call here rather than infer it.

  ⛔ THE TRANSIENT RE-OPENS, declared with its measured size rather than as a worry. The export
  sample under `site_v2/src/data/` was rolled forward by `!118` two commits ago and cannot carry a
  name renamed after that export, so `MetricComparison.astro`'s `hasData()` drops the renamed row
  from the fixture comparison until the closing refresh. Measured, not guessed: of the three,
  **only `danger_zone_ratio` is one of the rendered 16** — `shot_accuracy` is a payload field the
  16-row contract in `metricRows.ts` deliberately drops, and `shot_share` is not in the fixture
  payload at all. So the count goes **16 → 15 and NO group heading is lost** (Shooting keeps 3 of 4,
  unlike `!116` where `saves_pct` was Goalkeeping's only row).
  ⚠ It is honest-absent behaviour, not a break — rows are OMITTED, never blank and never a
  fabricated zero, per `14_team_stats.md` §6 — and it closes with the final refresh after F, which
  must be another ROLL-FORWARD (`!118` proved a past fixture can never be re-exported).

  THRESHOLD DECLARATIONS. NEW MECHANISM: none — no new script, macro, hook, test, generator or
  dependency; every guard already exists and is re-run. RECURRING COST: none — no new CI job, no
  schedule, no extra build; the renamed columns are the same width and count as the ones they
  replace.

decisions_reserved:
  - none NEW: all three names are ruled in `escalations.log` and quoted above, and the only
    judgement here — which metrics ride together — is the builder's call the record assigns to the
    builder.
  - ⚠ STILL OPEN from `!118`, carried forward so it is not lost: **GitLab #98**, the seven metric
    group headings rendering in ENGLISH on the DE and FI pages. Untouched by this MR and unaffected
    by it; the German and Finnish wording is a §10 CPO naming decision.

done_when:
  - `python scripts/sync_metric_docs_blocks.py --check` passes after regeneration.
  - `python scripts/export_metric_definitions_json.py` regenerates `metric_definitions.json` and `python -m pytest -q tests/test_metric_bindings.py` passes on byte-identity.
  - `check_description_hygiene.py`, `check_layer_contract.py` and `check_ui_i18n_metrics.py` all pass.
  - `python -m pytest -q` from the repo root passes with no new failures against the 1009 passed / 1 skipped measured on `9e2aaf9`.
  - `dbt parse` is clean with zero dangling `doc()` references; `sqlfluff lint` clean on every changed model, run FROM THE REPO ROOT.
  - `cd site_v2 && npm test && node scripts/check-page-specs.mjs` passes.
  - The three 22-name `accepted_values` lists at `int_competition_benchmarks.yml:27`, `:66` and `shared.yml:2080` are each updated and counted BY EYE back to 22, because #96 means no offline gate will catch a miss.
  - Each acceptance criterion is demonstrated in `acceptance_evidence.md` under `criteria_demonstrated:`, read from the BUILT site.
  - At least two mutations are watched going RED and then restored.
  - The fixture-page row count is measured and reported as **15**, matching the declared transient — a number that comes out 16 or 14 instead means something other than the declared effect happened.

amendments: (none)
