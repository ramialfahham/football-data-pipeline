# Task contract — #90, split `clean_sheets` (count) from `clean_sheets_share` (rate)

objective: >
  CPO RULING, `escalations.log` 2026-08-26, verbatim: **"use clean_sheets (for the number of
  matches with clean sheets) and clean_sheets_share (for the percentage of matches with clean
  sheets)."**

  One name carries two quantities and one catalogue definition is attached to both. This gives the
  rate its own name and its own catalogue row, and leaves every count where it is.

  ⛔ THE ISSUE'S PREMISE IS WRONG AND THE VERIFICATION IT DEMANDED SAYS SO. #90 states that
  `mart_team_profile.clean_sheets` is the RATE and that this may be a LIVE DISPLAY BUG. It is not.
  `mart_team_profile.sql:86` reads `ts.clean_sheets`, and `ts` is the `team_season` CTE
  (`:209-210`, `from metrics as m left join team_season as ts`) = `mart_team_season`, i.e. the
  COUNT (`mart_team_season.sql:41`, `m.clean_sheets_sum_season as clean_sheets`). Identical for
  `mart_team_season_insights.sql:57` (`ts` = the `mart_team_season` CTE, join at `:91`). Ground
  truth in the committed payload `site_v2/src/data/teams/33.json`: `seasons[0].clean_sheets = 8`
  beside `clean_sheets_this_season = 0.2105`, and 8/38 = 0.2105.

  ⭐ THE RATE REACHES THE TEAM PAGE BY A PATH THE ISSUE NEVER NAMES:
  `int_team_season__metrics_cumulative.sql:91` → `int_team_season__metrics`
  (`sf.* except (match_number)`) → `int_team_competition_benchmark_metrics_long.sql:34` (the
  unpivot) → `mart_team_competition_benchmarks.metric_key = 'clean_sheets'`. Same payload:
  `{metric_key: 'clean_sheets', metric_value: 0.2105}`.

  NO WRONG NUMBER IS ON SCREEN. The fixture surface serves counts from `mart_team_momentum` /
  `mart_team_season_record` with `games_in_window` / `games_played` denominators and renders `1/4`.
  The team surface serves the benchmark rate, and both row components coerce
  `count_fraction → percent` inline (`MetricLeagueRow.astro:23`, `MetricSeasonRow.astro:22`) with
  comments saying "clean_sheets is served as a rate". So this is a NAMING defect, not a display
  bug, and the MR is smaller than the issue describes.

  ⚠ IT DOES FIX A LIVE WAREHOUSE DEFECT, of the `!104` `goals_against` class:
  `{{ doc('clean_sheets') }}` — text "…shown as a count of games played (e.g. 3/5)" — is attached
  to the two RATE columns (`int_team_season.yml:120`, `:256`), and `persist_docs` has already
  pushed the COUNT definition onto them in BigQuery.

refs: >
  GitLab #90. CPO ruling 2026-08-26 in `.claude/task/escalations.log` (RULING 2), given while
  `!104` was in flight and deliberately deferred out of it — the previous contract's
  `decisions_reserved` reserved exactly this change.
  ⚠ That reservation restates the premise corrected above; it is superseded by the verification in
  `objective`, which was run against the SQL and the committed payload rather than against the
  issue text.
  Display name: TWO CPO decisions this session, both SELECTIONS from options I authored rather
  than verbatim words, both recorded on their face in `escalations.log` — the second supersedes the
  first (BUILDER'S CALL 3).
  Branched from main `5894aff`, clean tree.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics_cumulative.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_team_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_team_profile.yml
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - site_v2/src/lib/metricRows.ts
  - site_v2/src/lib/types.ts
  - site_v2/src/i18n/strings.ts
  - site_v2/src/components/team/TeamPerformance.astro
  - site_v2/src/components/team/MetricLeagueRow.astro
  - site_v2/src/components/team/MetricSeasonRow.astro
  - site_v2/src/specs/teams/team.spec.json
  - docs/wireframes/metrics_display.md
  - docs/wireframes/14_team_stats.md
  - docs/wireframes/02_team_profile.md
  - docs/wireframes/01_fixture_page.md
  - docs/wireframes/99_gaps_register.md
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/active_work.md

# ⚠ `metric_columns.md` is GENERATED — `python scripts/sync_metric_docs_blocks.py`, never edited by
# hand; `--check` fails CI on drift. ⚠ NO script, NO test file, NO CI file is touched: this adds no
# mechanism. ⚠ `site_v2/src/data/**` is NOT in scope — it is an exported sample set, refreshed by
# rerunning the export, never hand-edited (see decisions_reserved).

protected_override: >
  none required. No file in scope_paths is protected.

impact_map: >
  writers: ONE expression is renamed, none is changed.
    · `int_team_season__metrics_cumulative.sql:91` — `safe_divide(clean_sheet_games, games_played)`
      keeps its arithmetic and is aliased `clean_sheets_share`.
    · `int_team_profile__yoy.sql:91,111,131` — the three yoy columns follow the rename on both
      sides of the difference.
    · `int_team_competition_benchmark_metrics_long.sql:34` — the UNPIVOT list, which is what makes
      the benchmark's `metric_key` value change from `clean_sheets` to `clean_sheets_share`.
    · `mart_team_profile.sql:140-142` — pass-through of the renamed yoy columns.
    NOT touched, and each is already the COUNT under the right name: `mart_team_season.sql:41`,
    `mart_team_season_record.sql:72,129`, `mart_team_momentum.sql:44`, `mart_team_profile.sql:86`,
    `mart_team_season_insights.sql:57`.

  downstream: PASTED, not hand-traced. `dbt ls --select <model>+ --resource-type model`, run on
    this branch (`dbt=1.7.19`, 97 models) for each of the three renamed WRITERS.

      $ dbt ls --select int_team_season__metrics_cumulative+ --resource-type model
      football_data_pipeline.4_intermediate.shared.int_team_competition_benchmark_metrics_long
      football_data_pipeline.4_intermediate.shared.int_team_competition_benchmarks
      football_data_pipeline.4_intermediate.shared.int_team_profile__yoy
      football_data_pipeline.4_intermediate.domestic_league.team_season.int_team_season__deserved_vs_actual
      football_data_pipeline.4_intermediate.domestic_league.team_season.int_team_season__metrics
      football_data_pipeline.4_intermediate.domestic_league.team_season.int_team_season__metrics_cumulative
      football_data_pipeline.5_marts.shared.mart_team_competition_benchmarks
      football_data_pipeline.5_marts.shared.mart_team_profile
      football_data_pipeline.5_marts.shared.mart_team_season
      football_data_pipeline.5_marts.domestic_league.mart_team_season_insights
      football_data_pipeline.5_marts.shared.mart_team_season_record

      $ dbt ls --select int_team_profile__yoy+ --resource-type model
      football_data_pipeline.4_intermediate.shared.int_team_profile__yoy
      football_data_pipeline.5_marts.shared.mart_team_profile

      $ dbt ls --select int_team_competition_benchmark_metrics_long+ --resource-type model
      football_data_pipeline.4_intermediate.shared.int_team_competition_benchmark_metrics_long
      football_data_pipeline.4_intermediate.shared.int_team_competition_benchmarks
      football_data_pipeline.5_marts.shared.mart_team_competition_benchmarks

    All 11 classified by READING each model's projection, never by its name:
    · `int_team_season__metrics` — `sf.* except (match_number)`, so it carries the rename with no
      edit of its own. Not edited.
    · `int_team_profile__yoy` — consumes the renamed column; its three yoy outputs follow. EDITED.
    · `int_team_competition_benchmark_metrics_long` — the UNPIVOT member IS the `metric_key`
      VALUE, which is why the frontend's lookup key changes at all. EDITED.
    · `int_team_competition_benchmarks` / `mart_team_competition_benchmarks` — both aggregate or
      rank the long form generically (`group by league_code, season_api_year, metric_key`); no
      metric is named in either model's SQL. Only their `accepted_values` lists change.
    · `mart_team_profile` — the three yoy pass-throughs from `y.` change; `:86` is
      `ts.clean_sheets` off the `mart_team_season` CTE, the COUNT, and is untouched.
    · `mart_team_season` / `mart_team_season_record` / `mart_team_season_insights` — each reads
      `clean_sheets_sum_season` under the name `clean_sheets`. COUNT. Unaffected.
    · ⚠ `int_team_season__deserved_vs_actual` — **IN THE LINEAGE AND ABSENT FROM THE FIRST DRAFT OF
      THIS MAP.** That omission is precisely why this evidence is pasted rather than asserted. It
      takes an EXPLICIT column list from `int_team_season__metrics` (`:70-79`:
      `sot_difference_per_match`, `points_won_sum_season`, `season_games_played`) and no
      clean-sheet column at all. UNAFFECTED — established by reading `:70-82`, not inferred from
      its absence from a grep.

    NOT in any of the three lineages, therefore untouched: `mart_team_momentum`. Its
    `clean_sheets` is `b.clean_sheet_games` from `int_team_momentum__metrics`, a different chain,
    and is a COUNT.

    No model `ref()`s the seed — only tests do — so the seed row split cannot alter any
    `depends_on`. No model is incremental (all `table` or `view`, checked per model), so there is
    NO `--full-refresh` hazard.

  ⛔ THE RENAME CROSSES THE WAREHOUSE/FRONTEND BOUNDARY AND CANNOT SHIP IN PIECES.
    `mart_team_competition_benchmarks.metric_key` is a VALUE the frontend matches on
    (`TeamPerformance.astro`, `benchByKey`). Renaming it in the warehouse without the frontend
    binding silently drops the row from the "vs the league" panel; renaming the frontend without
    the warehouse does the same. Both halves are in this MR.

  blast_radius: `persist_docs` is on, so every repointed column's BigQuery description changes on
    the next build. The two RATE columns move from a WRONG sentence (the count's) to a right one;
    the count columns that already point at `{{ doc('clean_sheets') }}` keep their reference and it
    becomes correct for the first time. Rendered length measured against the 1,024-character
    column cap that fails a model.

  ⚠ A GATE, NOT LINEAGE: the count row carries an EMPTY `denominator_expr`, which lifts
    `sync_metric_docs_blocks.py`'s `TOTALLING_AFFIXES` refusal and makes the generator emit a
    `clean_sheets_sum_season` block it refuses to emit today. That is intended and the composed
    sentence is true at the whole-season grain. The yml reference stays unwired (#82's programme),
    so nothing new reaches BigQuery from it.

  layer_rules: no new model, no directory, no materialisation config, no macro. The rate is renamed
    where it is COMPUTED (intermediate) and flows outward; nothing is derived in a mart or in the
    frontend.

  deploy_order: warehouse and frontend merge together. The renamed columns do not exist in BigQuery
    until `data:build:main` runs post-merge, so the committed sample set lags by one build — see
    decisions_reserved.

decisions_taken: >
  THRESHOLD DECLARATION — NEW MECHANISM: one, declared for rejection. `metricRows.ts` gains an
  optional per-surface `team` binding and one `teamBinding()` helper (see BUILDER'S CALL 2). It
  adds no dependency, no script, no CI step and no recurring cost.
  THRESHOLD DECLARATION — RECURRING COST: none.

  BUILDER'S CALL 1: THE TWO SEED ROWS.
    · `clean_sheets_share` — the existing row RENAMED in place, keeping
      `countif(goals_against = 0)` / `count(*)`, `format` moved `count_fraction` → `percent`
      because a share of matches is a proportion and is displayed as one.
    · `clean_sheets` — a NEW row with an EMPTY `denominator_expr`, the shape `!104` established for
      a team total (`goals_for`, `corner_kicks`). `format` stays `count_fraction`, NOT `integer`:
      the fixture surface serves the count together with the matches behind it and renders `1/4`,
      and `metricRows.ts` states that its `format` mirrors the catalogue — `integer` would make
      that claim false. This is the one place the two totals precedents diverge, deliberately.
    · Both descriptions are GRAIN-FREE and neither contains the word "window"
      (`sync_metric_docs_blocks.py:WINDOW_PHRASING` rejects it): the catalogue says WHAT is
      measured, the model says over what span. Each names its sibling so a stranger reading one
      column knows the other exists.
    · Both stay `metric_group: goals`, `importance_tier: 2`, `direction: higher_better`. Tier is a
      CPO-class column and the display contract already places clean sheets at tier 2; moving
      either would be a display change this task does not carry.
    · `label_i18n_key` FOLLOWS the metric_id — `metrics.clean_sheets_share.label`. The plan wrote
      `metrics.clean_sheet_share.label`; that would have created a second deliberate id↔key
      divergence beside `shots_on_goal_per_match`, for no reason. The user-facing WORDS are still
      "Clean sheet share" (singular), which is the English that reads correctly.

  ⛔ BUILDER'S CALL 2, AND IT IS THE ONE TO ATTACK: ONE DISPLAY SLOT, TWO METRICS.
    `metricRows.ts:50` binds `field: "clean_sheets"` for BOTH surfaces, and after the split those
    are two different names. The row gains an optional
    `team: { field, labelKey, format }` and `metricRows.ts` exports one `teamBinding(row)` that
    returns it, falling back to the row itself.
    ⭐ THIS REMOVES A HACK RATHER THAN ADDING ONE. Both team row components currently carry
    `const fmt = row.format === "count_fraction" ? "percent" : row.format` plus a comment
    explaining that clean_sheets is really a rate here. That coercion IS the two-meanings defect,
    expressed in the frontend. Both lines are DELETED; the fallback is stated once, in the helper.
    The contract stays SIXTEEN rows — order, groups, tiers and `denom` are untouched, so
    `metrics_display.md`'s locked ordering is not reopened.

  BUILDER'S CALL 3 — SUPERSEDED MID-TASK, AND THE SUPERSEDING IS THE POINT.
    `metric_catalogue_label_en_unique_within_entity` forbids two team rows sharing `label_en`, so
    the rate needs its own display name whether or not it is rendered. I first recommended
    "Clean sheet share" / "Zu-Null-Quote" / "Nollapelien osuus" and the CPO approved it with the
    plan.
    ⛔ THAT RECOMMENDATION WAS MADE WITHOUT CHECKING THE FILE'S OWN CONVENTION, and the convention
    is unanimous: EVERY `percent`-format team metric in the catalogue carries a `% ` prefix in
    `label_en` — 7 of 7 — and so does every percent label in all three locale dicts
    (`% Duels won`, `% Trefferquote`, `% Torjuntaosuus`). "Clean sheet share" would have been the
    only percent label in the repo without it. Put back to him as one question; he chose the
    convention.
    SHIPPED: `% Clean sheets` / `% Zu-Null-Spiele` / `% Nollapelit`, and catalogue `label_en`
    `% Clean sheets`. The count keeps `Clean sheets` / `Zu-Null-Spiele` / `Nollapelit` untouched.
    ⚠ PROVENANCE, exactly: he SELECTED between two options I authored. The words are mine, the
    choice is his, and neither approval is a verbatim ruling. Both are recorded that way in
    `escalations.log`, including the process defect — check the convention BEFORE recommending a
    name, not after implementing one.

  BUILDER'S CALL 4: THREE `accepted_values` LISTS, NOT TWO. #90 names
    `int_competition_benchmarks.yml:27,66`. `shared.yml:2080` (`mart_team_competition_benchmarks`)
    carries the same 22-metric list and is missing from the issue. All three move together or the
    benchmark chain fails its own test.

  BUILDER'S CALL 5: THE DOC SWEEP IS NARROWER THAN THE PLAN SAID, ON PURPOSE. Five wireframes name
    `clean_sheets`; only the two that would become FALSE are edited.
    · EDITED — `14_team_stats.md` (§4 mock row, §5 binding table, the direction sentence, the
      block table, the §10 caveat) and `metrics_display.md` (locked row 3 + a new paragraph on why
      one slot carries two ids). These describe the TEAM screen, which now ranks the share.
    · LEFT, because each is about the COUNT and stays true: `02_team_profile.md:96` (the record
      block's integer), `01_fixture_page.md:150` and `99_gaps_register.md:22` and
      `metrics_display.md:282` (GAP-11, whose subject is the count in the two WINDOW marts).
    · `02_team_profile.md:137` says the team metric table shows x/y. That contradicts 14, it
      contradicted it BEFORE this change (14 §10 says so in as many words), and resolving which
      document owns the team metric table is not this rename's to settle.

  ⚠ NOT A RULING: the seed schema's wording about denominators, formats and tiers is REPO
  PRACTICE. Only `escalations.log` entries are quoted as CPO rulings anywhere here.

decisions_reserved:
  - ⛔ THE COMMITTED SAMPLE SET IS NOT REFRESHED HERE AND THE MR SHIPS ONE BUILD STALE.
    `site_v2/src/data/` is a gitignore-pinned export sample (`src/data/README.md`: refresh as a
    SET, by rerunning `scripts/export_site_data.py`). The renamed columns do not exist in BigQuery
    until `data:build:main` runs post-merge, so the sample keeps `metric_key: 'clean_sheets'` and
    the team page's clean-sheet row is OMITTED from the "vs the league" panel on the sample build —
    the honest-absent path the tab already implements, not a crash. Hand-editing exported JSON to
    fake the new name is the defect this project calls the export "consumption too". Refresh is a
    follow-up commit after the first main build.
  - `mart_team_momentum.sql:42-117` is a SECOND hand-written copy of ~20 team formulas and has
    already drifted (#93). Its `clean_sheets` is a COUNT and is correct under this ruling, so it is
    untouched. Consolidating the copy is #93 and is the CPO's.
  - The catalogue still does not drive the SQL (#91): nothing compares
    `int_team_season__metrics_cumulative.sql:91` against the seed's `numerator_expr` /
    `denominator_expr`. The parked value-equivalence test is what would, and it ships after this.
  - `clean_sheets_sum_season` stays UNWIRED in both ymls even though the split makes a block
    available for it, and so do the ~40 other blank columns of #82. Wiring them is that
    programme's, and doing it here would make the diff unreviewable.
  - The `_sum_season` affix's sentence "Totalled over the season." is cumulative-grain-false on
    `int_team_season__metrics_cumulative`, where the column is a running total to matchday N. That
    is a pre-existing property of EVERY `_sum_season` block (`goals_for_sum_season__team` and
    siblings), not something this MR introduces, and it is why the reference stays unwired.
  - No range test is ADDED for the count on `mart_team_season` / `mart_team_profile`. The count has
    range tests where it already had them (`shared.yml:127-128`, `:883-884`); adding new ones is
    coverage work outside this rename.

acceptance_criteria:
  - The team page Performance tab labels the clean-sheet row **`% Clean sheets`** in EN,
    **`% Zu-Null-Spiele`** in DE and **`% Nollapelit`** in FI, read from the BUILT page in each
    locale. A label falling back to English, or resolving to nothing, fails this.
  - The fixture page still renders the clean-sheet row as the COUNT over its denominator
    (`1/4` on the committed sample), with the label unchanged, in BOTH windows. The count surface
    must be untouched by a rename that is not about it.
  - Where the served benchmark set does not carry `clean_sheets_share`, the team page OMITS that
    row from the "vs the league" panel and dashes the "vs last season" value, rather than showing a
    zero bar, a stale number or a broken row. This is the state the committed sample produces until
    the export is refreshed, so it is the state that must be demonstrated.
  - All sixteen rows of the locked contract still render on the team page's season panel, in the
    locked block order, with every label except row 3 byte-unchanged — the rename must not move,
    drop or relabel anything else.

done_when:
  - The seed parses at 86 rows, 15 fields each, pure ASCII, line endings preserved as BYTES, and
    every `schema.yml` seed test re-derived offline: unique `(metric_id, entity)`, unique
    `label_i18n_key`, unique `(entity, label_en)`, every `accepted_values`, every `not_null`, and
    `direction` in lockstep with `lower_is_better`.
  - `python scripts/sync_metric_docs_blocks.py` regenerates and `--check` is green. MEASURED on the
    branch: **181 → 183**, five blocks added (`clean_sheets_share`, its three yoy siblings, and
    `clean_sheets_sum_season__team` — the one the empty denominator un-refuses) and three removed
    (the old `clean_sheets_{this,prev}_season__team` and `clean_sheets_delta_yoy__team`). The
    `clean_sheets` block itself keeps its name and changes its TEXT to the count definition.
  - `dbt parse` CLEAN and ZERO dangling `{{ doc() }}` references anywhere — asserted across every
    model yml, not only the edited ones.
  - `check_description_hygiene.py` green repo-wide, read from its OUTPUT against a baseline
    measured on this branch before the first edit.
  - ⛔ EVERY REMAINING `clean_sheets` REFERENCE IN THE REPO IS CLASSIFIED COUNT OR RATE BY READING
    THAT MODEL'S SQL, and recorded per site. This is the part that reaches the warehouse and no
    test can check it.
  - `npm test` in `site_v2` green — `check-metric-labels.test.mjs` (all three locales; every
    `labelKey` a `label_i18n_key` the catalogue declares; no locale carrying a label nothing
    renders) and `check-page-specs`, both of which run in `prebuild` and gate the build.
  - ⛔ MUTATION, NOT A GREEN TICK: the renamed range tests and the spec check are each broken
    deliberately and observed going RED. A passing test over a column that no longer exists proves
    nothing.
  - The fixture page still renders the count as `1/4` and the team page renders the sample's
    honest-absent state, both captured in `rendered_page_evidence.md` from the running dev server.
  - Offline gates green plus `ruff`, and `python -m pytest tests/` at a baseline measured on this
    branch.
  - ⚠ EVERY INTEGER IN THE ARTIFACTS RE-DERIVED before commit, by pulling each number out and
    asking whether it is still true — not by sweeping for the ones I remember changing (#71).
