# Task contract — rename the two `passing` metrics (batch D)

objective: >
  Step 3 of the metric catalogue naming programme, **MR D of six**. The two metrics in the seed's
  `passing` group:

      pass_accuracy         → passes_accuracy_pct
      key_passes_per_match  → passes_key_per_match

  They ride together because "family" is defined by the seed's own `metric_group` column, not by the
  builder's taste — the split recorded in `escalations.log`'s `2026-08-27 STEP 3 STARTS` entry.

  Both are COMPUTED COLUMNS in `int_team_season__metrics_cumulative`, so each runs through model SQL,
  the ymls, the marts and the site.

  ⭐ THE COLUMN MUST FOLLOW THE METRIC, and it is machine-checked, not a matter of taste.
  `dbt_project/tests/assert_no_uncatalogued_season_metric.sql` states it directly: "every
  metric-bearing column must be registered in metric_catalogue. The test FAILS (returns rows) if a
  model computes a metric that is not catalogued." Move the `metric_id` without the column and that
  test goes red in `data:build:mr`. This is why the twelve remaining renames are NOT seed-only edits,
  unlike `!111` (`goals_for` → `goals`) and `!112`, which renamed metrics that were not computed
  columns. The record says the same: "Every one is a COMPUTED COLUMN in the season models, so unlike
  the three above each runs through model SQL, the ymls, the marts and the site."

  MEASURED ON THIS BRANCH BEFORE ANY EDIT, from the REPO ROOT: **`pass_accuracy` 63,
  `key_passes_per_match` 40** whole-token occurrences.
  ⚠ Taken with `cd /d/Projects/football-data-pipeline` asserted in the same command. On batch C the
  first count came out 38/46/21 because the shell was still inside `dbt_project/` and `git grep`
  scopes to the CWD — plausible-looking figures that were wrong by a factor of four.

  ⭐ NO DESCRIPTION-BLOCK SPLIT: `git grep -lE "passes_accuracy_pct|passes_key_per_match"` returns
  nothing, so neither new name exists for any entity today and the generator emits one bare block
  each. (That hazard fires on **F**, where `finishing_efficiency` exists for both entities.)

refs: >
  **`.claude/task/escalations.log`, the block "THE METRIC CATALOGUE NAMING PROGRAMME"** — rulings
  dated 2026-08-26, complete tables appended 2026-08-27. Both renames appear verbatim in its
  "⛔ TEAM, 12 REMAINING" table.

  Per-name authority:
  · `pass_accuracy` → `passes_accuracy_pct` is **RULING 1** ("pass_accuracy becomes
    pass_accuracy_pct") as corrected by **item 6 of the enumerated six** (`pass_accuracy_pct` /
    `pass_accuracy_player_pct` → `passes_accuracy_pct` / `passes_accuracy_player_pct`, "singular
    where the family is plural").
  · `key_passes_per_match` → `passes_key_per_match` is **THE RULED PATTERN**, applied.
    `escalations.log:5483-5485`, verbatim:
        "⭐ THE PATTERN THIS PRODUCES, to be applied to any metric added later:
             noun [_qualifier] [_against] [_player] [_form]
         `_form` is `_per_match` for a team, `_per90` for a player, `_pct` for a percentage."
    Applied to the team's key-passes rate: noun `passes` (the family noun, already established by
    `passes_total`, `passes_accurate`, `passes_key`, `passes_per_match`) + qualifier `key` + form
    `_per_match` for a team = **`passes_key_per_match`**. No other pattern-consistent name exists.
    ⭐ THE PATTERN IS THE RULING, AND IT IS DELIBERATELY GENERAL. The CPO's stated purpose for it,
    verbatim, is exactly this case: "Ensure consistency here as well **so we are able to write down
    a pattern in case we will have to add new metrics**." He replaced per-name rulings with a rule;
    demanding a separate per-name quote for a name the rule already determines defeats the thing he
    asked for.
    ⚠ TWO EARLIER CITATIONS FOR THIS NAME WERE WRONG AND ARE RECORDED AS SUCH, because the reviewers
    who caught them were right about the record even though the name was never in doubt:
      · "RULING 6 as reversed by the higher-order instruction" — WRONG. RULING 6 verbatim is
        `"key_passes_player"` → `passes_key_player`, the **PLAYER** metric throughout. It never
        names the team one. `football-analytics-expert-reviewer` FAILed round 1 on this.
      · "the CPO approved THIS MR's plan… 'then go ahead'" — TRUE but UNVERIFIABLE from the record,
        because the log recorded the approval without reproducing the table it answered. Both
        `football-analytics-expert-reviewer` and `analytics-engineer-reviewer` FAILed round 2 on it,
        and both were right: an approval is only checkable authority when what it approved is
        quoted beside it. That is the log's own 2026-08-26 rule, broken again by me.
    Neither wrong citation was ever needed. The pattern above was in the record the whole time.
  The CPO's reply to the enumerated six, verbatim: "apply the suggested changes to ensure
  consistency." ⚠ `key_passes_per_match` is **NOT** one of those six; `pass_accuracy` (item 6) is.

  ⛔ NO PLAN FILE IS CITED. `feat/metric-rename-goals` and `feat/metric-rename-catalogue-only` were
  each FAILed for citing one; the tables live in the log itself.

  Branched from main **`62d3b18`**, clean tree — the main carrying `!119` (batch C).

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
  - docs/wireframes/02_team_profile.md
  - docs/wireframes/10_home.md
  - docs/wireframes/14_team_stats.md
  - docs/wireframes/metrics_display.md
  - site/match-preview/metric_bindings.csv
  - site/match-preview/metric_definitions.json
  - site/i18n/de.json
  - site/i18n/en.json
  - site/i18n/fi.json
  - site_v2/src/lib/metricRows.ts
  - site_v2/src/lib/types.ts
  - site_v2/src/i18n/strings.ts
  - site_v2/src/specs/teams/team.spec.json
  - site_v2/src/specs/competition/matches/fixture.spec.json
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/active_work.md

# ⚠ NOT IN SCOPE, each for a stated reason rather than by omission:
#  · site_v2/src/data/** — the GENERATED export sample; never hand-edited. Re-opens the declared
#    transient; see decisions_taken for the measured size (15 → 13 rows, no heading lost).
#  · site/team-season/index.html — frozen PAGE CODE of the product retired 2026-07-21. `!116` and
#    `!119` both left the byte-identical construct untouched; same call, established precedent.
#  · site/match-preview/metric_manifest.json — the retired MVP's own `live_id`s, mapped THROUGH the
#    bindings by check_ui_i18n_metrics.py, so they stay valid untouched.
#  · EVERY PLAYER SURFACE. int_player_profile.yml, int_player_profile__yoy.sql,
#    mart_player_profile.sql, int_legs__team_from_players.sql and the player rows of the seed are
#    NOT touched. They carry names that merely SHARE A STEM with these two; see decisions_taken.

protected_override: >
  none required. No file in scope_paths is protected.

impact_map: >
  writers: `int_team_season__metrics_cumulative` is the single home of both formulas —
    `safe_divide(passes_accurate, passes_total)` and
    `safe_divide(key_passes, games_with_player_stats)`. `int_team_season__metrics` is its final-row
    projection via `select sf.* except (match_number)`, so it is not edited and cannot drift.
    ⚠ `mart_team_momentum` computes BOTH AGAIN — a second copy of ~20 team formulas, open as **#93**.
    Renamed here too; the duplication itself is NOT addressed and #93 stays open.

  downstream: pasted from `dbt ls --select int_team_season__metrics_cumulative+ --resource-type
    model` run on this branch (dbt 1.7.19, `.venv/Scripts/dbt.exe`) BEFORE the first structural edit:
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
    ⚠ THAT LIST IS NOT THE WHOLE EDIT SET. `mart_team_momentum` and `mart_matchday_insights` do NOT
    appear in it — momentum recomputes the metrics from its own window (#93) and
    `mart_matchday_insights` reads THAT — yet both are edited. The lineage is EVIDENCE, not the file
    list; that correction came out of `!114`'s review.

  layer_rules: `check_layer_contract.py`; both names stay inside 4_intermediate/5_marts, so no layer
    boundary moves. Coupled guards: `assert_no_uncatalogued_season_metric` (column ⇄ catalogue
    identity) and the THREE 22-name `accepted_values` lists at
    `int_competition_benchmarks.yml:27`, `int_competition_benchmarks.yml:66`, `shared.yml:2080`.
    Both names are in all three; neither new name may be added twice or dropped.
    ⛔ NO OFFLINE GATE ENFORCES THOSE THREE LISTS — proved by a mutation that survived the whole
    offline suite on `!114` and again on `!119`. Filed as **#96**. Only the warehouse
    `accepted_values` test in `data:build:mr` catches a miss, so they are checked BY EYE here.

  deploy_order: none needed. No touched model is incremental; `data:build:main` rebuilds every
    affected table in one pass on merge.

  blast_radius: two columns rename on the season, momentum and profile models plus
    `mart_team_profile`'s yoy forms; two `metric_key` VALUES change on the benchmark chain; and two
    `home_*_recent` / `away_*_recent` aliases change on `mart_matchday_insights`, which feeds only
    the retired MVP's export. **No number changes** — both formulas are byte-identical.

acceptance_criteria:
  - Every metric name the BUILT site renders reads in the same words after the rename as before it, in all three locales, shown by extracting the rendered metric labels from the pages under `site_v2/dist/` and comparing each against the untouched CPO-validated wording in `site/i18n/<loc>.json`.
  - No built page and no `site_v2/src` source file outside the generated sample contains the string `pass_accuracy` or `key_passes_per_match`, shown by a grep over `site_v2/dist/` and over `site_v2/src/` excluding `src/data/`.
  - `npm test` passes in `site_v2/`, including the metric-label cross-check against `site/i18n/`, AND that check is watched going RED against a deliberately stale key — a green guard nobody has broken proves nothing.
  - The BUILT team page still shows the "not enough games to rank" absent state where these rows would sit, in all three locales, shown by reading the built page's rendered text — recorded so the missing rows are read as the sample's one-game featured season and never as a defect of this rename.

decisions_taken: >
  Both names come from the record and neither is chosen here; the authorities are quoted per name in
  `refs`. THE FOUR ACCEPTANCE CRITERIA ABOVE ARE THE CPO'S STANDING SET for MRs B–F ("do it",
  recorded in `escalations.log` beside the list it answered) — reproduced, not re-drafted, and
  deliberately not re-put to him.

  ⛔⛔ THE WHOLE RISK OF THIS BATCH IS THAT THREE DIFFERENT THINGS SHARE THESE STEMS, and the
  substring pass that COMPLETED batch C would corrupt every one of them. Each is excluded
  programmatically, not by hand:
    · `pass_accuracy_pct` (51 occurrences) is the **PLAYER** metric and a step-4 name. A substring
      sweep turns it into `passes_accuracy_pct_pct`.
    · `key_passes_this_season` / `_prev_season` / `_prev_season_full` / `_delta_yoy` (23) are
      **PLAYER** yoy forms — verified by reading which model they sit in: `int_player_profile.yml`,
      `int_player_profile__yoy.sql`, `mart_player_profile.sql`, `shared.yml`. There is no team
      `key_passes` metric for them to belong to.
    · four **PLAYER** test names — `std_player_…`, `player_profile_…`, `mart_leaderboards_…`,
      `int_player_season_…` `_pass_accuracy_pct_in_range`.
    · `key_passes_per90` and `passes_key` (29) are **PLAYER** metrics, step 4.
    · `pass_accuracy_recent` STANDING ALONE (3) is the retired MVP's `live_id` in
      `metric_bindings.csv`; `check_ui_i18n_metrics.py` maps it THROUGH the bindings, so renaming it
      breaks the mapping while changing nothing a catalogue reader sees. The `home_`/`away_` forms
      are NOT protected and ARE renamed.
    · `docs/wireframes/10_home.md:134` and `:150` name the **PLAYER** `pass_accuracy_pct`. Only
      line 175 carries the team pair.
  ⭐ Word-boundary matching separates the team names from `pass_accuracy_pct` correctly, because `_`
  blocks the boundary. The danger lives only in the substring pass.

  ⭐ BARE `key_passes` IS DELIBERATELY NOT RENAMED, and the reasoning is checked rather than assumed.
  It is created in `int_legs__team_from_players.sql:28` as `sum(passes_key) as key_passes` and
  consumed in `int_team_season__metrics_cumulative.sql:150` as
  `safe_divide(key_passes, games_with_player_stats) as key_passes_per_match`. It is NOT a catalogue
  `metric_id` (0 rows in the seed) and NOT a declared column of `int_team_season` (no `- name:
  key_passes` in any model yml), so `assert_no_uncatalogued_season_metric` does not reach it. It is
  an aggregate INPUT, structurally identical in that role to `tackles`, `interceptions` and `blocks`
  on the adjacent lines — a structural parallel only, NOT a claim that key passes are a defensive
  action; they are a creative metric and the CPO corrected that phrasing. The recorded rule "A METRIC
  AND ITS COLUMN MAY LEGITIMATELY DIFFER" covers it.

  ⭐ THE FROZEN `site/` TREE IS EDITED ONLY WHERE A LIVE GATE FORCES IT, and only for
  `pass_accuracy` — `key_passes_per_match` has no `site/` presence at all. Only the catalogue-id
  plumbing: `metric_bindings.csv`'s `catalogue_metric_id` plus `home_column`/`away_column`, the
  `metrics.<id>` KEYS in `site/i18n/*.json`, and the REGENERATED `metric_definitions.json`. **No
  wording, no page code, no `live_id`.**

  ⛔ THE TRANSIENT RE-OPENS, with its size measured rather than guessed. The export sample cannot
  carry a name renamed after its export, so `MetricComparison.astro`'s `hasData()` drops the renamed
  rows until the closing refresh. **BOTH** of these are among the LOCKED 16 (`Passing` group), so the
  count goes **15 → 13**. `Passing` KEEPS its heading — it has 3 rows and loses 2, leaving
  `passes_per_match`.
  ⚠ Honest-absent behaviour, not a break: rows are OMITTED, never blank and never a fabricated zero,
  per `14_team_stats.md` §6. It closes with the final refresh after F, which must be another
  ROLL-FORWARD (`!118` proved a past fixture can never be re-exported).

  THRESHOLD DECLARATIONS. NEW MECHANISM: none — no new script, macro, hook, test, generator or
  dependency; every guard already exists and is re-run. RECURRING COST: none — no new CI job, no
  schedule, no extra build.

decisions_reserved:
  - none NEW: both names are ruled in `escalations.log` and quoted above.
  - ⚠ STILL OPEN, carried forward: **GitLab #98**, the seven metric group headings rendering in
    ENGLISH on the DE and FI pages. Untouched by this MR and unaffected by it; the German and
    Finnish wording is a §10 CPO naming decision.

done_when:
  - `python scripts/sync_metric_docs_blocks.py --check` passes after regeneration.
  - `python scripts/export_metric_definitions_json.py` regenerates `metric_definitions.json` and `python -m pytest -q tests/test_metric_bindings.py` passes on byte-identity.
  - `check_description_hygiene.py`, `check_layer_contract.py` and `check_ui_i18n_metrics.py` all pass.
  - `python -m pytest -q` from the repo root passes with no new failures against the 1009 passed / 1 skipped measured on `62d3b18`.
  - `dbt parse` clean with zero dangling `doc()`; `sqlfluff lint` clean on every changed model, run FROM THE REPO ROOT.
  - `cd site_v2 && npm test && node scripts/check-page-specs.mjs` passes.
  - The three 22-name `accepted_values` lists are each updated and counted BY EYE back to 22, because #96 means no offline gate will catch a miss.
  - EVERY protected token listed in `decisions_taken` is verified UNCHANGED after the passes, by name and by count — not assumed from the exclusion list.
  - The occurrence reconciliation is re-verified AGAINST THE FINAL TREE, not against the counts taken when the passes ran. `bi-analyst-reviewer` FAILed `!119` round 1 for exactly that.
  - The fixture-page row count is measured and reported as **13** — a number that comes out 15 or 11 means something other than the declared transient happened.
  - Each acceptance criterion is demonstrated in `acceptance_evidence.md` under `criteria_demonstrated:`, read from the BUILT site.
  - At least two mutations are watched going RED and then restored, and at least one is on a metric that IS among the rendered 16.

amendments:
  - 2026-08-28 (round 3, after BOTH `football-analytics-expert-reviewer` and
    `analytics-engineer-reviewer` FAILed round 2): the citation REPLACED with the one that was
    correct all along — **THE RULED PATTERN** at `escalations.log:5483-5485`, which the CPO
    explicitly scoped "to be applied to any metric added later". AUTHORITY: none needed; this cites
    an existing ruling instead of two wrong things, and changes no name.
    ⛔ MY ERROR, AND IT IS THE INSTRUCTIVE PART: I went hunting for a per-NAME approval and, not
    finding one, first misattributed a player ruling and then leaned on an unverifiably-recorded
    plan approval — escalating a settled question to the CPO in the process. His reply was one line:
    "we have defined it. you should be able to look it up, no?" He was right. The pattern is a
    RULE he asked for precisely so individual names would not need individual rulings, and it
    determines this name uniquely.
    ⭐ THE RULE THIS LEAVES: **when a ruling is a PATTERN, the pattern IS the authority for every
    name it determines.** Looking for a per-instance quote where a general rule exists is not
    rigour; it manufactures a gap and then escalates it.
  - 2026-08-28 (round 2, after `football-analytics-expert-reviewer` FAILed round 1): the `refs:`
    citation for `key_passes_per_match` → `passes_key_per_match` REWRITTEN. AUTHORITY: none needed —
    this corrects a false statement about what the record says; it narrows nothing and changes no
    name. ⛔ THE FINDING WAS EXACT: I cited RULING 6, which is verbatim about the PLAYER metric
    (`key_passes_player` → `passes_key_player`) and never names the team one. The reviewer also
    established that this rename is NOT among "THE SIX, ENUMERATED" — the list built specifically to
    cure "the builder's own unrecorded reconstruction dressed as the record" — so the defect that
    round was created to fix still applied here.
    ⚠ TWO REVIEWERS SPLIT ON IT: `scope-auditor` examined the same citation and PASSed, reasoning
    that it is "a direct application of an approved general rule" and that the CPO engaged with this
    MR mid-flight and challenged the SCOPE, not the name. Both readings are recorded; the citation
    is rewritten to the stronger, honest chain rather than to whichever reviewer is more convenient.
