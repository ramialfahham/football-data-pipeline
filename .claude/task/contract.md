# Task contract — rename finishing_efficiency to finishing_efficiency_pct (batch F)

objective: >
  Step 3 of the metric catalogue naming programme, **MR F of six and the LAST of the twelve team
  renames**. One metric:

      finishing_efficiency  →  finishing_efficiency_pct        (TEAM entity only)

  It is a COMPUTED COLUMN in the season models, so this is the same full-stack shape as A–E, not a
  seed-only edit — `dbt_project/tests/assert_no_uncatalogued_season_metric.sql` requires every
  metric-bearing column of `int_team_season__metrics` to be a registered `metric_id`, and moving the
  `metric_id` while leaving the column turns that test red in `data:build:mr`.

  ⛔⛔ **WHY F WAS HELD BACK, AND WHAT MAKES IT DIFFERENT FROM A–E: `finishing_efficiency` is a
  `metric_id` for BOTH entities.** The seed carries a team row and a player row under the same name.
  Two consequences, both measured on `cdd2218` before any edit and both handled deliberately below:
  the generated doc blocks RESTRUCTURE, and a substring sweep would corrupt the player metric.

  MEASURED FROM THE REPO ROOT (`cd` asserted in the same command as every counting grep, because
  `git grep` scopes to the CWD and that produced wrong figures on batch C):
  **220 bare `finishing_efficiency`** tree-wide outside `.claude/`; yoy forms **31 / 31 / 29**.

  The sweep classified **144 occurrences** in 40 files — **108 renamed, 36 protected** — and printed
  every decision with its reason. The bare stem splits **61 TEAM (renamed) / 34 PLAYER (protected)**;
  the remaining 120 bare occurrences are in the generated export sample and 5 more in files this
  branch deliberately does not sweep.

refs: >
  **`.claude/task/escalations.log`, the block "THE METRIC CATALOGUE NAMING PROGRAMME"**.
  ⭐ Cited by CONTENT, never by line number and never a plan file: two MRs in this programme were
  FAILed for citing a plan file, and one for a line number that had decayed onto another batch's
  rows. The log is append-only, so any line number into it decays as it grows.

  Per-name authority, quoted:
  · **RULING 1**, the CPO's own words listing the team renames one by one, contains verbatim:
    "finishing_efficiency becomes finishing_efficiency_pct".
  · The same block's table headed "⛔ TEAM, 12 REMAINING" carries the row
    `finishing_efficiency        → finishing_efficiency_pct`.
  · It is **not** among "THE SIX, ENUMERATED" corrections and needs no correction — RULING 1 names
    the target spelling exactly, with no abbreviation and no singular/plural break.
  ⭐ It also satisfies **THE RULED PATTERN** — the block in the same log headed "⭐ THE PATTERN THIS
  PRODUCES, to be applied to any metric added later", reading `noun [_qualifier] [_against]
  [_player] [_form]`, with `_form` = `_pct` for a percentage. Cited UP FRONT because batch D burned
  three review rounds hunting a per-name quote the pattern had already settled, and the CPO's reply
  was "we have defined it. you should be able to look it up, no?".
  **When a ruling is a PATTERN, the pattern is the authority for every name it determines.**

  ⛔ THE PLAYER ROW IS **NOT** IN THIS MR. `finishing_efficiency` → `finishing_efficiency_player_pct`
  is in the same log's "⛔ PLAYER, 35 REMAINING" list and belongs to **step 4**. The log already
  declares the interval a disclosed transient, verbatim: "team `finishing_efficiency` and player
  `finishing_efficiency` will diverge the moment the team `_pct` sweep lands, until the player sweep
  follows. Neither is a defect; both close as the remaining MRs land."

  ⛔ `label_en` IS NOT TOUCHED. The team row's "% Goals per shot on target" is one of the nine
  catalogue labels RULING 2 sends from "on target" to "on goal"; that is **step 5**, a separate MR.

  Branched from main **`cdd2218`**, clean tree — the main carrying `!122` (the batch-E handover).
  `glab mr list`: no open merge requests, so nothing here is a hard dependency of one and a
  standalone branch is correct (`docs/working_agreement.md` §3a).

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics_cumulative.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_team_profile.yml
  - dbt_project/models/4_intermediate/shared/int_team_profile__yoy.sql
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/5_marts/domestic_league/mart_matchday_insights.sql
  - dbt_project/models/5_marts/domestic_league/mart_team_season_insights.sql
  - dbt_project/models/5_marts/shared/mart_team_momentum.sql
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/mart_team_season_record.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - scripts/sync_metric_docs_blocks.py
  - tests/test_sync_metric_docs_blocks.py
  - docs/wireframes/02_team_profile.md
  - docs/wireframes/10_home.md
  - docs/wireframes/14_team_stats.md
  - docs/wireframes/metrics_display.md
  - site_v2/scripts/check-metric-labels.test.mjs
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/metricRows.ts
  - site_v2/src/specs/competition/matches/fixture.spec.json
  - site_v2/src/specs/teams/team.spec.json
  - site/i18n/de.json
  - site/i18n/en.json
  - site/i18n/fi.json
  - site/match-preview/metric_bindings.csv
  - site/match-preview/metric_definitions.json
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/active_work.md

# ⚠ TWO PLAYER-SCOPED FILES ARE IN scope_paths AND CARRY NO RENAME — they are edited ONLY to
# re-point a `doc()` reference the generator's block merge would otherwise dangle:
#   · dbt_project/models/4_intermediate/shared/int_player_season_position.yml  (1 edit, 4 protected)
#   · dbt_project/models/5_marts/shared/shared.yml — mart_leaderboards section  (1 edit, 11 protected)
# The third re-point is in int_team_season.yml's int_player_season__metrics section.
#
# ⚠ NOT IN SCOPE, each for a stated reason:
#  · site_v2/src/data/** — the GENERATED export sample; never hand-edited. Carries 195 occurrences
#    of this stem (120 bare + 75 yoy). The declared transient; closes with the final roll-forward.
#  · site/team-season/index.html — FROZEN MVP page code. Left stale on purpose by `!116`/`!119`/`!120`;
#    verified on `cdd2218` it still reads `shot_accuracy`, `danger_zone_ratio` and `pass_accuracy`.
#  · site/match-preview/metric_manifest.json — carries the `live_id` only, which is protected.
#  · docs/audits/2026-06_alignment_audit.md — a DATED audit naming `finishing_efficiency_season`, a
#    column on a model that no longer exists. Left stale by the same earlier batches.
#  · docs/wireframes/12_player_stats.md, docs/wireframes/99_gaps_register.md,
#    dbt_project/macros/player_benchmark_metrics.sql, int_player_season__metrics.sql,
#    int_player_season_position__metrics.sql, int_player_competition_benchmarks.sql,
#    mart_leaderboards.sql, scripts/export_metric_definitions_json.py — PLAYER surfaces, step 4.

protected_override: >
  none required. No file in scope_paths is a protected command-class file.

impact_map: >
  writers: `finishing_efficiency` is computed in `int_team_season__metrics_cumulative.sql:127` and
    computed AGAIN, independently, in `mart_team_momentum.sql:77` — #93's duplication, which the
    lineage below does NOT show. `int_team_season__metrics` is the cumulative model's final-row
    projection via `select sf.* except (match_number)`, so it is not edited.
    `int_team_profile__yoy.sql` derives the three yoy forms; `mart_matchday_insights.sql` projects
    the `home_`/`away_…_recent` pair. (Named post-rename where it describes what this branch SHIPS.)

  downstream: pasted from `dbt ls --select int_team_season__metrics_cumulative+ --resource-type
    model` run on THIS branch (dbt 1.7.19, `.venv/Scripts/dbt.exe`) BEFORE the first edit:
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
    ⚠ **THE LINEAGE IS EVIDENCE, NOT THE FILE LIST** — the correction `!114`'s review left. It
    under-counts here in both directions: `mart_team_momentum`, `mart_matchday_insights`,
    `int_momentum.yml`, both `site/` trees, the four `site_v2/src` files, the label test and the
    four wireframes are all edited and none appears above; while
    `int_team_season__deserved_vs_actual` and `mart_team_season` appear and are NOT edited.

  layer_rules: `check_layer_contract.py`; the name stays inside 4_intermediate/5_marts. Coupled
    guards, named as this branch leaves them:
      · `assert_no_uncatalogued_season_metric` (unchanged) — the reason a catalogue-only rename is
        impossible for these twelve.
      · SIX named range tests are RENAMED with the column — `tsi_`, `mmi_home_`, `mmi_away_`
        (`domestic_league.yml`), `team_profile_`, `std_team_`, `momentum_team_` (`shared.yml`).
      · ⛔ **`mart_leaderboards_finishing_efficiency_in_range` is the SEVENTH and does NOT rename.**
        It is the PLAYER board's test — it sits beside `mart_leaderboards_save_pct_in_range`, and
        `save_pct` is the player metric while `saves_pct` is the team one. Six of seven rename.
      · the THREE 22-name TEAM `accepted_values` lists at `int_competition_benchmarks.yml:27`,
        `:66` and `shared.yml:2080` — `finishing_efficiency` is in all three and becomes
        `finishing_efficiency_pct` in all three.
      · ⛔ **THREE PLAYER `accepted_values` LISTS ALSO CARRY THE BARE STEM AND MUST NOT MOVE** —
        `int_competition_benchmarks.yml:105` (18 names), `shared.yml:2186` (18) and
        `shared.yml:1756` (14, the rate boards). Found by mapping every occurrence to its owning
        model, not by reading the name.
    ⛔ #96: NO OFFLINE GATE ENFORCES ANY OF THOSE LISTS — reproduced on `!114`, `!119`, `!120` and
    `!121`. The three TEAM lists were therefore checked BY EYE on the base (each exactly 22 values,
    no duplicates, all three byte-identical to one another) and again after the edit.

  deploy_order: none needed. No touched model is incremental, so no `--full-refresh` is required.

  blast_radius: one column renames on the cumulative, momentum, record, insights, profile and
    matchday models; one `metric_key` VALUE changes on the team benchmark chain; the two
    `home_/away_…_recent` projections rename. **No number changes** — every formula, floor and null
    policy is byte-identical.

acceptance_criteria:
  - Every metric name the BUILT site renders reads in the same words after the rename as before it, in all three locales, shown by extracting the rendered metric labels from the pages under `site_v2/dist/` and comparing each against the untouched CPO-validated wording in `site/i18n/<loc>.json`.
  - No built page and no `site_v2/src` source file outside the generated sample contains the string `finishing_efficiency` as a standalone metric key, shown by a whole-token grep over `site_v2/dist/` and over `site_v2/src/` excluding `src/data/`.
  - `npm test` passes in `site_v2/`, including the metric-label cross-check against `site/i18n/`, AND that check is watched going RED against a deliberately stale key — a green guard nobody has broken proves nothing.
  - The BUILT team page still shows the "not enough games to rank" absent state where these rows would sit, in all three locales, shown by reading the built page's rendered text — recorded so the missing rows are read as the sample's one-game featured season and never as a defect of this rename.

decisions_taken: >
  The name comes from the record; the authority is quoted in `refs`. **THE FOUR ACCEPTANCE CRITERIA
  ARE THE CPO'S STANDING SET FOR MRs B–F** (his "do it", answering a message that listed them and
  asked whether they could stand for the remaining batches) — reproduced, not re-drafted, not
  re-asked.

  ⛔⛔ **THE DOC-BLOCK MERGE — the reason F was saved for last, and the one structural change here.**
  `_blocks()` in `scripts/sync_metric_docs_blocks.py` emits ONE block per `metric_id` where its rows
  agree and splits on `entity` ONLY where they disagree. The two `finishing_efficiency` rows
  disagree today, so the file carries `finishing_efficiency__team` and `finishing_efficiency__player`.
  Renaming only the team side leaves each name with a SINGLE row, so the generator emits **two bare
  blocks** — and every reference to the suffixed names dangles. Measured on `cdd2218` and handled
  explicitly rather than discovered by a red gate:
    · **6** `doc('finishing_efficiency__team')` references → `doc('finishing_efficiency_pct')`
    · **3** `doc('finishing_efficiency__player')` references → `doc('finishing_efficiency')`
      (`int_team_season.yml`, `int_player_season_position.yml`, `shared.yml`) — ⛔ **these would
      dangle even though this MR renames nothing on the player side.**
    · the three `*__player` yoy blocks lose their referent column and are dropped by the generator;
      they have **0** references, so nothing dangles from their removal.
  ⭐ The bare shape is the shape already on `main` for every single-row metric: `save_pct` (player)
  and `saves_pct` (team) each hold a bare block, as do `pass_accuracy_pct` and
  `passes_accuracy_pct`. Derived yoy blocks always carry `__team`. `check_description_hygiene.py` is
  the gate that would have caught a dangling `doc()`; it is run after regeneration, not relied on
  as the discovery mechanism.

  ⭐ **THE RENAME METHOD, the one proven over C, D and E, used verbatim.** `\b` FAILS AGAINST `_`,
  so every token CONTAINING the stem was enumerated and **classified once with its decision
  PRINTED** — 108 renamed, 36 protected, each carrying the reason it was decided by (owning model,
  seed row entity, or file scope). The script **ABORTS BEFORE WRITING** if any protected token's
  count would change, and verifies the post-transform token multiset per file. Protected counts were
  re-derived from `git grep cdd2218`, never from a number written down.
  ⚠ Model→entity is an EXPLICIT map, not a substring rule, and an unlisted model aborts:
  `mart_leaderboards` is a PLAYER mart whose name contains neither "player" nor "team", so a
  substring rule would have mis-scoped five occurrences and renamed the one range test that must not.

  ⛔ PROTECTED, and each asserted unchanged against the base:
    · **`finishing_efficiency_recent` standing alone** — the retired MVP's `live_id` in
      `metric_bindings.csv`. `check_ui_i18n_metrics.py` maps THROUGH it, so renaming it breaks the
      mapping while changing nothing a catalogue reader sees. The `home_`/`away_` prefixed forms are
      NOT protected and are renamed.
    · **`mart_leaderboards_finishing_efficiency_in_range`** — the player board's range test.
    · **`finishing_efficiency_season`** — a column of a model that no longer exists, named only in a
      dated audit.
    · **34 bare PLAYER occurrences** across nine player-scoped files plus the player sections of
      `shared.yml`, `int_team_season.yml`, `int_competition_benchmarks.yml`, the seed's rows 15 and
      32, and the player-row ratio list in `metrics_display.md`.
  ⚠ No i18n placeholder is at risk here — unlike E's `sotd`, nothing in this rename appears as a
  `{token}` inside a translated sentence, so no wording is touched anywhere.

  ⛔ **`site_v2/scripts/check-metric-labels.test.mjs` carries an EN exemption keyed on the literal
  metric id** and it is RE-POINTED, not removed: v2's locked EN label is deliberately kept against
  the MVP corpus's "% Conversion rate", which is a §10 pick reserved to the CPO. Left unmoved, the
  test compares the two and goes red for a reason that has nothing to do with this rename.

  ⭐ TWO PROSE MENTIONS IN `scripts/sync_metric_docs_blocks.py` AND `tests/test_sync_metric_docs_blocks.py`
  ARE RENAMED, and the reasoning is recorded because it is a judgement call. Both narrate the
  window-phrasing defect the guard once missed, and the description that carried it was the **TEAM**
  row's (traced through the log's own entry, not inferred from the name). The QUOTED phrases stay
  verbatim; only the metric id moves. Precedent: batch C updated exactly this class of prose in
  `check_description_hygiene.py`, `export_site_data.py` and `test_description_hygiene.py`.
  The seed's `goals_open_play` TEAM row, whose description reads "The numerator of
  finishing_efficiency.", moves for the same reason; the PLAYER `goals_open_play` row does not.

  ⛔ **THE TRANSIENT GROWS, AND THE NUMBER IS PREDICTED HERE BEFORE ANY CODE: the built fixture
  pages go from 13 rendered metric rows to 12, and NO group heading is lost.**
  `finishing_efficiency` IS one of the locked 16 in `site_v2/src/lib/metricRows.ts`, and the
  committed sample still serves the old key, so `MetricComparison.astro`'s `hasData()` drops the
  row — honest-absent, never blank and never a fabricated zero. Shooting keeps `shots_per_match`
  and `shots_on_goal_per_match`, so its heading survives. Programme running total:
  16 → 15 (C) → 13 (D) → 13 (E) → **12 (F)**. **A count other than 12 means something other than
  this rename happened.** It closes with the final sample roll-forward, which is owed after F and
  is NOT in this branch.

  THRESHOLD DECLARATIONS. NEW MECHANISM: none. RECURRING COST: none. NEW DEPENDENCY: none.

decisions_reserved:
  - none NEW: the name is ruled in `escalations.log` and quoted above.
  - ⚠ CARRIED FORWARD: **#96**, now reproduced on FOUR consecutive batches. `platform-reviewer`
    recommends closing it with a small offline test parsing the three ymls; that is a NEW MECHANISM
    and therefore the CPO's/CTO's call, not taken here. The three lists were checked by eye instead.
  - ⚠ CARRIED FORWARD: **GitLab #98**, metric group headings rendering in ENGLISH on DE/FI.
    Untouched and unaffected by this MR.
  - ⚠ CARRIED FORWARD: whether a contract's NARRATIVE sections should be hash-excluded the way the
    evidence artifacts already are. Governance, not a batch task.
  - ⚠ FOR STEP 4, NOT HERE: `contribution_share` → `contribution_player_pct` is the one name in the
    35-row player list the CPO did not rule on directly. To be settled with him BEFORE step 4.

done_when:
  - `python scripts/sync_metric_docs_blocks.py --check` passes after regeneration, with the two bare blocks and no `__team`/`__player` pair for this metric.
  - `check_description_hygiene.py`, `check_layer_contract.py` and `check_ui_i18n_metrics.py` all pass, and `dbt parse` is clean with zero dangling `doc()`.
  - `python -m pytest -q` from the repo root passes with no new failures against the baseline measured on `cdd2218`.
  - `sqlfluff lint` clean on every changed model, run FROM THE REPO ROOT, UNPIPED, with the exit code read bare — never through `tail`/`head`.
  - `npm test` green in `site_v2/`, and the criterion-3 mutation watched going RED.
  - The built site is measured STRUCTURALLY (`<div class="mrow">` / `<div class="mgroup">`), not by substring, and reports exactly 12 rows with all 7 headings intact.
