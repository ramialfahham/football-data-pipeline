# Task contract — rename the deserved chain (batch E)

objective: >
  Step 3 of the metric catalogue naming programme, **MR E of six**. The two metrics of the
  deserved-vs-actual chain:

      sot_difference_per_match  → shots_on_goal_difference_per_match
      sot_points_gap            → deserved_points_gap

  Both are COMPUTED COLUMNS in the season models, so this is the same full-stack shape as A–D, not a
  seed-only edit — `dbt_project/tests/assert_no_uncatalogued_season_metric.sql` requires every
  metric-bearing column of `int_team_season__metrics` to be a registered `metric_id`.

  MEASURED ON THIS BRANCH BEFORE ANY EDIT, from the REPO ROOT (`cd` asserted in the same command,
  because `git grep` scopes to the CWD and that produced wrong figures on batch C):
  **`sot_difference_per_match` 107** (46 in the generated sample, 61 live);
  **`sot_points_gap` 49** (25 sample, 24 live).

  ⭐ THREE THINGS MAKE E DIFFERENT FROM C AND D, all measured rather than assumed:
    1. **NEITHER NAME IS AMONG THE RENDERED 16** (`site_v2/src/lib/metricRows.ts` — 0 hits), so the
       built fixture-page row count **HOLDS AT 13**. C took 16→15, D took 15→13; E moves it not at
       all. A count of 12 or 14 would mean something other than this rename happened.
    2. **NO FROZEN `site/` PRESENCE AT ALL** (0 hits across the whole tree). So unlike C and D there
       is no `metric_bindings.csv` edit, no `site/i18n/*.json` key rename, and no
       `metric_definitions.json` regeneration. `check_ui_i18n_metrics.py` is untouched by this diff.
    3. **NO YOY FORMS** — `sot_difference_per_match` and `sot_points_gap` each have **0**
       `_this_season` / `_prev_season` / `_delta_yoy` derivatives, unlike D's 16 and 12. The
       derived-identifier sweep still runs, but it has almost nothing to find.

  ⭐ NO DESCRIPTION-BLOCK SPLIT: neither `shots_on_goal_difference_per_match` nor
  `deserved_points_gap` exists for any entity today, so the generator emits one bare block each.

refs: >
  **`.claude/task/escalations.log`, the block "THE METRIC CATALOGUE NAMING PROGRAMME"**. Both renames
  appear verbatim in its "⛔ TEAM, 12 REMAINING" table, as the two rows reading
  `sot_difference_per_match → shots_on_goal_difference_per_match` and
  `sot_points_gap → deserved_points_gap`.
  ⭐ Cited by CONTENT, never by line number: the log is append-only and any line number into it
  decays as it grows.

  Per-name authority, quoted:
  · `sot_points_gap` → `deserved_points_gap` is **RULING 4**, three names put to the CPO one per
    line and answered one per line, verbatim: "1. deserved_points_gap / 2. shots_inside_box_pct /
    3. shots_on_goal_pct".
  · `sot_difference_per_match` → `shots_on_goal_difference_per_match` is **RULING 1**
    ("sot_difference_per_match becomes sog_difference_per_match") as corrected by **item 1 of the
    enumerated six**, whose stated reason is quoted in the log: "`sog_difference_per_match` →
    `shots_on_goal_difference_per_match` (the abbreviation survived his own `sot`→`sog` ruling while
    the rest of the family spells it out)". The CPO's reply to those six, verbatim: "apply the
    suggested changes to ensure consistency."
  ⭐ Both also satisfy **THE RULED PATTERN** — the block in the same log headed "⭐ THE PATTERN THIS
  PRODUCES, to be applied to any metric added later", reading `noun [_qualifier] [_against]
  [_player] [_form]`, with `_form` = `_per_match` for a team. Cited up front because batch D burned
  three review rounds hunting for a per-name quote where the pattern already decided the name;
  **when a ruling is a PATTERN, the pattern is the authority for every name it determines.**

  ⛔ NO PLAN FILE IS CITED. Two MRs in this programme were FAILed for citing one.

  Branched from main **`db47b0a`**, clean tree — the main carrying `!120` (batch D).

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics_cumulative.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__deserved_vs_actual.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_team_season_record.sql
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_metric_catalogue_expr_resolvable.sql
  - docs/wireframes/10_home.md
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - site_v2/src/components/team/DeservedHero.astro
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/types.ts
  - site_v2/src/specs/teams/team.spec.json
  - site_v2/src/styles/system.css
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/active_work.md

# ⚠ NOT IN SCOPE, each for a stated reason:
#  · site_v2/src/data/** — the GENERATED export sample; never hand-edited. Carries 71 occurrences,
#    the declared transient, closing with the final refresh after F.
#  · site/** — ZERO occurrences of either name anywhere in the frozen tree, verified. Nothing to do.
#  · every PLAYER surface — neither name exists for the player entity.

protected_override: >
  none required. No file in scope_paths is protected.

impact_map: >
  writers: `shots_on_goal_difference_per_match` is computed in `int_team_season__metrics_cumulative`;
    `deserved_points_gap` is computed in `int_team_season__deserved_vs_actual`, the OLS model that
    fits points against the shots-on-goal difference. (Named post-rename throughout this
    `impact_map`, because it describes the state this branch SHIPS.) `int_team_season__metrics` is the cumulative
    model's final-row projection via `select sf.* except (match_number)`, so it is not edited.
    ⚠ Unlike C and D, `mart_team_momentum` does NOT recompute either metric (#93's duplication does
    not extend to the deserved chain — verified: 0 hits), so it is not in scope here.

  downstream: pasted from `dbt ls --select int_team_season__metrics_cumulative+ --resource-type
    model` run on this branch (dbt 1.7.19, `.venv/Scripts/dbt.exe`) BEFORE the first edit:
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
    ⚠ THE LINEAGE IS EVIDENCE, NOT THE FILE LIST — the correction `!114`'s review left. This time it
    UNDER-counts differently from C and D: `int_team_season_record.sql`,
    `assert_metric_catalogue_expr_resolvable.sql`, `scripts/export_site_data.py`,
    `tests/test_export_site_data.py`, `DeservedHero.astro`, `types.ts`, `system.css` and
    `docs/wireframes/10_home.md` are all edited and none appears above.

  layer_rules: `check_layer_contract.py`; both names stay inside 4_intermediate/5_marts. Coupled
    guards, named as this branch leaves them — BOTH are themselves renamed by this diff, so grepping
    the pre-rename names finds nothing:
      · `assert_no_uncatalogued_season_metric` (unchanged)
      · `assert_metric_catalogue_expr_resolvable` — its header comment now names `deserved_points_gap`
      · the named test `int_team_season_deserved_points_gap_contract`
      · the THREE 22-name `accepted_values` lists at `int_competition_benchmarks.yml:27`, `:66`,
        `shared.yml:2080` — `shots_on_goal_difference_per_match` is in all three;
        `deserved_points_gap` is not one of the 22 and must not be added.
    ⛔ #96: NO OFFLINE GATE ENFORCES THOSE THREE LISTS — reproduced on `!114`, `!119` AND `!120`,
    and again here. Checked BY EYE as well as by `data:build:mr`.

  deploy_order: none needed. No touched model is incremental.

  blast_radius: two columns rename on the season, deserved-vs-actual, record and profile models; one
    `metric_key` VALUE changes on the benchmark chain — the shooting-difference metric only, which
    ships as `shots_on_goal_difference_per_match`; the gap metric was never in that chain. **No
    number changes** — the OLS fit, its coefficients and every formula are byte-identical.

acceptance_criteria:
  - Every metric name the BUILT site renders reads in the same words after the rename as before it, in all three locales, shown by extracting the rendered metric labels from the pages under `site_v2/dist/` and comparing each against the untouched CPO-validated wording in `site/i18n/<loc>.json`.
  - No built page and no `site_v2/src` source file outside the generated sample contains the string `sot_difference_per_match` or `sot_points_gap`, shown by a grep over `site_v2/dist/` and over `site_v2/src/` excluding `src/data/`.
  - `npm test` passes in `site_v2/`, including the metric-label cross-check against `site/i18n/`, AND that check is watched going RED against a deliberately stale key — a green guard nobody has broken proves nothing.
  - The BUILT team page still shows the "not enough games to rank" absent state where these rows would sit, in all three locales, shown by reading the built page's rendered text — recorded so the missing rows are read as the sample's one-game featured season and never as a defect of this rename.

decisions_taken: >
  Both names come from the record; the authorities are quoted per name in `refs`. THE FOUR
  ACCEPTANCE CRITERIA ARE THE CPO'S STANDING SET for MRs B–F — reproduced, not re-drafted.

  ⛔⛔ **`sotd` IS NOT RENAMED, AND THIS IS THE ONE DECISION IN E THAT MATTERS.** `sotd` is the
  export payload key for this metric (`scripts/export_site_data.py:230`), the field name on the
  frontend type (`types.ts:142`), the variable throughout `DeservedHero.astro` — and, decisively,
  an **i18n PLACEHOLDER TOKEN inside user-facing translated sentences** in all three locales
  (`strings.ts:94-95, 299-300, 476-477`, e.g. "a shots-on-target difference of {sotd} per match").
  Renaming it would force edits to six translated strings. **Wording is forbidden in a rename MR and
  is a §10 CPO decision.** `sotd` is a display-layer variable, not a catalogue `metric_id`; the
  recorded rule "A METRIC AND ITS COLUMN MAY LEGITIMATELY DIFFER" covers it. Only the COLUMN
  references it reads from are renamed.

  ⭐ THREE REGRESSION CTE ALIASES ARE NOT RENAMED, same reasoning as D's bare `key_passes`:
  `mean_sot_difference`, `sd_sot_difference` and `corr_sot_points` are local aliases inside the OLS
  block of `int_team_season__deserved_vs_actual.sql:169-190`. Verified NOT published columns (no
  `- name:` for any of them in any model yml) and NOT catalogue `metric_id`s. They are regression
  intermediates, not metrics.
  ⚠ AND A PRE-EXISTING INCONSISTENCY THIS EXPOSES BUT DOES NOT CREATE: in that same CTE
  `mean_points_per_match` spells its source column out while `mean_sot_difference` truncates its
  own. That asymmetry is on `main` today and is untouched here; naming it so a reviewer reads it as
  pre-existing rather than introduced.

  ⛔ THE TRANSIENT DOES **NOT** GROW THIS TIME, and that is the measured prediction: neither name is
  among the LOCKED 16 in `metricRows.ts` (0 hits), so `MetricComparison.astro`'s `hasData()` has
  nothing new to drop. The built fixture-page row count **HOLDS AT 13**, where D left it. The sample
  still carries 71 stale occurrences of these two names, which close with the final refresh after F
  — a ROLL-FORWARD, since `!118` proved a past fixture can never be re-exported.

  ⚠ A WORDING ISSUE FOUND AND DELIBERATELY NOT TOUCHED, declared so it is routed rather than lost:
  the EN hero sentences at `strings.ts:94-95` say "shots-on-target difference". Step 5 renames nine
  CATALOGUE `label_en` rows from "on target" to "on goal"; these are UI sentence strings, not
  catalogue labels, so they may fall outside that nine-row list. Flagged for step 5 rather than
  fixed here — it is wording, and therefore §10.

  THRESHOLD DECLARATIONS. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - none NEW: both names are ruled in `escalations.log` and quoted above.
  - ⚠ CARRIED FORWARD: **GitLab #98**, metric group headings rendering in ENGLISH on DE/FI.
    Untouched and unaffected by this MR.
  - ⚠ CARRIED FORWARD: **#96**, now reproduced on three consecutive batches. `platform-reviewer`
    recommends closing it alongside E with a small offline test; that is a NEW MECHANISM and
    therefore the CPO's/CTO's call, not taken here.

done_when:
  - `python scripts/sync_metric_docs_blocks.py --check` passes after regeneration.
  - `check_description_hygiene.py`, `check_layer_contract.py` and `check_ui_i18n_metrics.py` all pass.
  - `python -m pytest -q` from the repo root passes with no new failures against the 1009 passed / 1 skipped measured on `db47b0a`.
  - `dbt parse` clean with zero dangling `doc()`; `sqlfluff lint` clean on every changed model, run FROM THE REPO ROOT.
  - `cd site_v2 && npm test && node scripts/check-page-specs.mjs` passes.
  - The three 22-name `accepted_values` lists are counted BY EYE back to 22, with `sot_difference_per_match` replaced and `sot_points_gap` correctly still absent.
  - EVERY protected token — `sotd` and the three regression CTE aliases — is verified UNCHANGED after the passes, by name and by count against `git grep db47b0a`, not against a note.
  - The occurrence reconciliation is re-verified AGAINST THE FINAL TREE, not against the counts taken when the passes ran.
  - The fixture-page row count is measured and reported as **13, unchanged** — a different number means something other than the declared effect happened.
  - Each acceptance criterion is demonstrated in `acceptance_evidence.md` under `criteria_demonstrated:`, read from the BUILT site.
  - At least two mutations are watched going RED and then restored.

amendments: (none)
