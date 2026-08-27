# Task contract — rename `corner_kicks_per_match` to `corners_per_match` and `save_ratio` to `saves_pct`

objective: >
  Step 3 of the catalogue naming programme, MR B of six. Two renames from the `set_pieces` and
  `goalkeeping` groups, and they belong together because they close the SAME transient: `!112`
  renamed the totals `corner_kicks` → `corners` and `goalkeeper_saves` → `saves` and left both
  rates behind, so main has said `corners` beside `corner_kicks_per_match` since it merged. That
  was disclosed at the time as a live transient; this closes it.

  Both are COMPUTED COLUMNS in `int_team_season__metrics_cumulative`, so unlike `!111`/`!112` each
  runs through model SQL, the ymls, the marts and the site.

  ⭐ THE COLUMN MUST FOLLOW THE METRIC, and it is machine-checked rather than a matter of taste:
  `dbt_project/tests/assert_no_uncatalogued_season_metric.sql` requires every metric-bearing column
  of `int_team_season__metrics` to be a registered `metric_id`.

  MEASURED ON THIS BRANCH BEFORE ANY EDIT: **196 occurrences across 34 files**.

  ⭐ NO DESCRIPTION-BLOCK SPLIT, checked rather than assumed — the mechanism that surprised `!111`
  mid-flight. Both metrics are team-only, and neither `corners_per_match` nor `saves_pct` exists for
  any entity today, so the generator emits one bare block each. ⚠ Note `saves` and `corners` DO now
  exist as team metrics (from `!112`) — `saves_pct` and `corners_per_match` are distinct ids and
  collide with neither. The regeneration is the proof, not this sentence.

  ⭐ THIS IS THE FIRST MR OF THE STEP TO TOUCH THE FROZEN `site/` TREE, and only where a live gate
  forces it. Both names are in `site/match-preview/metric_bindings.csv`, so
  `tests/test_metric_bindings.py` (which regenerates `metric_definitions.json` and asserts
  byte-identity) and `scripts/check_ui_i18n_metrics.py` (CI `validate:ui`, which requires
  `metrics.<catalogue_metric_id>` to exist in `site/i18n/*.json`) would both go red otherwise.

refs: >
  **`.claude/task/escalations.log`, the block "THE METRIC CATALOGUE NAMING PROGRAMME"** — its
  rulings dated 2026-08-26 and the complete tables appended 2026-08-27. Both renames appear verbatim
  in the "⛔ TEAM, 12 REMAINING" table: `corner_kicks_per_match → corners_per_match` and
  `save_ratio → saves_pct`.

  Authority for `save_ratio` → `saves_pct` is RULING 1 ("save_ratiobecomes save_ratio_pct") as
  narrowed by RULING 3 on doubled suffixes ("use the shorter as recommended") and by item 3 of the
  enumerated six (`save_pct` / `save_player_pct` → `saves_pct` / `saves_player_pct`, singular where
  the family is plural). Authority for `corner_kicks_per_match` → `corners_per_match` is item 5 of
  that same enumerated six, whose stated reason is that the team's own conceded version is already
  `corners_against_per_match`. The CPO's reply to the six, verbatim: "apply the suggested changes to
  ensure consistency."

  ⛔ NO PLAN FILE IS CITED. `feat/metric-rename-goals` and `feat/metric-rename-catalogue-only` were
  each FAILed for citing one; the tables live in the log itself.

  Branched from main **`a70b7e2`**, clean tree — main after `!114`, so it carries the step-3 record
  AND the `!115` CI fix this branch's pipeline depends on.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics_cumulative.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_team_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_team_profile.yml
  - dbt_project/models/4_intermediate/shared/int_team_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/mart_team_season_record.sql
  - dbt_project/models/5_marts/shared/mart_team_momentum.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/5_marts/domestic_league/mart_team_season_insights.sql
  - dbt_project/models/5_marts/domestic_league/mart_matchday_insights.sql
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - docs/wireframes/02_team_profile.md
  - docs/wireframes/14_team_stats.md
  - docs/wireframes/metrics_display.md
  - site/match-preview/metric_bindings.csv
  - site/match-preview/metric_definitions.json
  - site/i18n/de.json
  - site/i18n/en.json
  - site/i18n/fi.json
  - site_v2/src/lib/metricRows.ts
  - site_v2/src/i18n/strings.ts
  - site_v2/src/specs/teams/team.spec.json
  - site_v2/src/specs/competition/matches/fixture.spec.json
  - site_v2/src/components/team/MetricSeasonRow.astro
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

# ⚠ NOT IN SCOPE, each for a stated reason rather than by omission:
#  · site_v2/src/data/** — the GENERATED export sample, regenerated from the PROD marts and unable
#    to carry the new columns until data:build:main has run. Never hand-edited. The declared
#    transient below; closes in the step's final refresh MR.
#  · site/match-preview/metric_manifest.json — holds the retired MVP's own `live_id`s
#    (`save_ratio_recent`, `corner_kicks_per_match_recent`). Those are that product's display ids,
#    not catalogue ids; `check_ui_i18n_metrics.py` maps them THROUGH the bindings, so they stay
#    valid untouched. `points_won_form` already shows a live_id that names no catalogue metric.
#  · site/team-season/index.html — a page of the product RETIRED on 2026-07-21. No gate reads it.
#  · docs/audits/**, docs/match_preview_pages_refinement.md, docs/working_agreement.md — records of
#    HISTORY. Renaming inside a record of what happened falsifies the record.

protected_override: >
  none required. No file in scope_paths is protected.

impact_map: >
  writers: `int_team_season__metrics_cumulative` is the single home of both formulas —
    `safe_divide(corner_kicks, games_with_team_stats) as corner_kicks_per_match` and the
    save-coverage-gated `safe_divide(goalkeeper_saves, goalkeeper_saves + goals_against_in_save_games)
    as save_ratio`. `int_team_season__metrics` is its final-row projection via
    `select sf.* except (match_number)`, so it is not edited and cannot drift.
    ⚠ `mart_team_momentum` computes BOTH AGAIN — it is a second copy of ~20 team formulas and is
    open as **#93**. Its columns carry the same metric names and are renamed here too; the
    duplication itself is NOT addressed by this MR and #93 stays open.

  downstream: pasted from `dbt ls --select int_team_season__metrics_cumulative+ --resource-type
    model` run on this branch (dbt 1.7.19, `.venv/Scripts/dbt.exe`) BEFORE the first structural
    edit, not asserted from memory:
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
    ⚠ THAT LIST IS NOT THE WHOLE EDIT SET, and saying so matters. `mart_team_momentum`,
    `int_team_momentum__metrics` and `mart_matchday_insights` do NOT appear in it because they are
    not downstream of the cumulative model — `mart_team_momentum` computes both metrics AGAIN from
    the momentum window (#93), and `mart_matchday_insights` reads THAT. They are edited anyway,
    which is exactly why a lineage list must be read as evidence and not as the file list.
    Of the eleven above, four name a column and are edited: `int_team_competition_benchmark_metrics_long`
    (the UNPIVOT list), `int_team_profile__yoy`, `mart_team_profile`, `mart_team_season_insights`.
    `int_team_season__metrics`, `int_team_competition_benchmarks`, `mart_team_season` and
    `mart_team_competition_benchmarks` propagate by `select *`, so their OUTPUT changes while their
    SQL does not. `int_team_season__deserved_vs_actual` reads neither name (verified by grep).

  layer_rules: `check_layer_contract.py`; both names stay inside 4_intermediate/5_marts, so no
    layer boundary moves. The coupled guards are `assert_no_uncatalogued_season_metric` (column ⇄
    catalogue identity) and the THREE 22-name `accepted_values` lists — two in
    `int_competition_benchmarks.yml`, one in `shared.yml`.
    ⛔ NO OFFLINE GATE ENFORCES THOSE THREE LISTS — proved by a surviving mutation on `!114` and
    filed as **#96**. Only the warehouse `accepted_values` test in `data:build:mr` catches a
    forgotten entry, so they get checked by eye here as well as by the build.

  deploy_order: none needed. No touched model is incremental; `data:build:main` rebuilds every
    affected table in one pass on merge.

  blast_radius: two columns rename on the season, momentum, record and profile models plus
    `mart_team_profile`'s three yoy forms; two `metric_key` VALUES change on the benchmark chain;
    and two `home_*_recent` / `away_*_recent` aliases change on `mart_matchday_insights`, which
    feeds only the retired MVP's export. **No number changes** — every formula and coverage gate is
    byte-identical.

acceptance_criteria:
  - Every metric name the BUILT site renders reads in the same words after the rename as before it, in all three locales, shown by extracting the rendered metric labels from the pages under `site_v2/dist/` and comparing each against the untouched CPO-validated wording in `site/i18n/<loc>.json`.
  - No built page and no `site_v2/src` source file outside the generated sample contains the string `corner_kicks_per_match` or `save_ratio`, shown by a grep over `site_v2/dist/` and over `site_v2/src/` excluding `src/data/`.
  - `npm test` passes in `site_v2/`, including the metric-label cross-check against `site/i18n/`, AND that check is watched going RED against a deliberately stale key — a green guard nobody has broken proves nothing.
  - The BUILT team page still shows the "not enough games to rank" absent state where these rows would sit, in all three locales, shown by reading the built page's rendered text — recorded so the missing rows are read as the sample's one-game featured season and never as a defect of this rename.

decisions_taken: >
  Both names come from the record and neither is chosen here; the authorities are quoted in `refs`.

  ⭐ `label_i18n_key` FOLLOWS `metric_id`, as in `!111`, `!112` and `!114`. The catalogue's one
  deliberate id≠key disagreement (`shots_on_goal_per_match` → `metrics.shots_on_target_per_match.label`)
  is not in this set and is not touched.

  ⭐ THE FROZEN `site/` TREE IS EDITED ONLY WHERE A LIVE GATE FORCES IT, and only the catalogue-id
  plumbing: `metric_bindings.csv`'s `catalogue_metric_id` (plus its `home_column`/`away_column`,
  because `mart_matchday_insights` aliases them `home_<metric>_recent`), the `metrics.<id>` KEYS in
  `site/i18n/*.json`, and the REGENERATED `metric_definitions.json`. **No wording changes, no page
  code, no `live_id`.** Every label string in the corpus stays byte-identical, which is what keeps
  `check-metric-labels.test.mjs`'s "CPO-validated MVP labels" comparison at full strength rather
  than needing a rename map bolted into three guards.

  ⛔ THE LIVE TRANSIENT, declared as it is created: the committed export sample can only be
  regenerated against the prod marts, so between this merge and the step's closing refresh MR it
  serves the OLD keys. Nothing public degrades — the site is unlisted and `deploy:site-v2` is
  manual-only.

  ⛔ AND IT IS **VISIBLE THIS TIME**, unlike `!114`'s. An earlier draft of this paragraph said "on
  the page this is invisible either way", reasoning from the team Performance tab, which renders its
  absent state regardless. That is wrong about the FIXTURE page, and MEASURED on the built site
  rather than reasoned: `MetricComparison.astro`'s `hasData()` drops any row where neither side has
  a value, so the two renamed rows disappear from the 16-row comparison on **all 51 built fixture
  pages, in all three locales — 16 rendered names before, 14 after**. `!114` did not do this because
  its renames touched the TEAM binding only; `corner_kicks_per_match` and `save_ratio` are FIXTURE
  fields, so this is the first MR of the step where the transient is on screen.
  ⚠ It is the codebase's honest-absent behaviour, not a break: the rows are OMITTED, never rendered
  as a blank or a fabricated zero, exactly as `14_team_stats.md` §6 requires. It closes the moment
  the sample is regenerated. But it is visible, and calling it invisible would have been a false
  statement in the contract a reviewer would have had to catch.

  ⚠ ONE MORE THING THAT MEASUREMENT EXPOSED, about my own method rather than this diff: the evidence
  script I used on `!114` matched labels by plain substring, so "Ø Corners" tested TRUE against a
  page containing only "Ø Corners against". It reported 16 rendered names here when the true figure
  was 14. Fixed to subtract the occurrences of any longer label that contains the shorter one.
  ⭐ THE RULE: a substring test over rendered text is not a presence test wherever one label is a
  prefix of another — and this metric set is full of `X` / `X against` pairs.

  THRESHOLD DECLARATIONS. NEW MECHANISM: none — no new script, macro, hook, test or dependency;
  every generator and guard already exists and is re-run. RECURRING COST: none — no new CI job, no
  extra build, no schedule; the renamed columns are the same width and count as the ones they
  replace.

decisions_reserved:
  - none: both names are ruled in `escalations.log` and quoted above, and the only judgement here —
    which metrics ride together — is the builder's call the record assigns.

done_when:
  - `python scripts/sync_metric_docs_blocks.py --check` passes after regeneration.
  - `python scripts/export_metric_definitions_json.py` regenerates `metric_definitions.json` and
    `python -m pytest -q tests/test_metric_bindings.py` passes on byte-identity.
  - `python scripts/check_description_hygiene.py`, `check_layer_contract.py` and
    `check_ui_i18n_metrics.py` all pass.
  - `python -m pytest -q` passes with no new failures against the count on `a70b7e2`.
  - `dbt parse` is clean with zero dangling `doc()` references; `sqlfluff lint` clean on every
    changed model from the repo root.
  - `cd site_v2 && npm test && node scripts/check-page-specs.mjs` passes.
  - The three 22-name `accepted_values` lists are updated in all THREE places and checked by eye,
    because #96 means no offline gate will catch a miss.
  - Each acceptance criterion is demonstrated in `acceptance_evidence.md` under
    `criteria_demonstrated:`, read from the BUILT site.
  - At least two mutations are watched going RED and then restored.

amendments: (none)
