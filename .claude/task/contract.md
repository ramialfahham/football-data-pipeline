# Task contract — consistent form-window model naming (momentum + season_record)

> CPO naming decision (conversation 2026-06-13, "Option 2"): make the form/window model
> family use ONE root per concept from the metrics_context_model.md matrix — `momentum`
> (live form / last-5) and `season_record` (within-competition cumulative). Today the live
> concept uses three roots (form_window, momentum, last_5) and the season concept uses
> `season_to_date`. Pure rename — NO logic/metric change. See docs/working_agreement.md §2/§10.

objective: >
  Rename the two concepts consistently:
  (A) live form: keep `momentum`; rename the SELECTION model `int_form_window__team` →
      `int_momentum_window__team` and its drill-down mart `mart_form_window__team` →
      `mart_momentum_window__team`.
  (B) season record: rename `int_season_to_date__{team,player}` →
      `int_season_record__{team,player}` and `mart_season_to_date__{team,player}` →
      `mart_season_record__{team,player}`.
  Update every `ref()`, model `name:`, the consuming intermediates/marts, the export script's
  mart-table reads, the one cross-check test, and all docs that name these models.
  BOUNDARIES (do NOT change): the `window_type` literal VALUES (`last_5`, `season_to_date`,
  `prev_season`) — they label the cut, not the model, and the wireframe reads `w2.window_type`;
  the published JSON output key `form_window` in export_site_data.py (UI contract — only the
  3 mart TABLE-NAME reads change, not the key/variable); the future-spec column
  `form_window_kind` in player_metrics_catalogue.md (substring coincidence, not this model);
  the unrelated `int_matchday__player_form_window` ref in player_stats_ui_data_modeling_concept.md
  (a different, pre-existing stale ref — out of scope); the historical audit doc.

refs: CPO Option-2 ruling (conversation 2026-06-13); docs/metrics_context_model.md §1/§4/§5.

scope_paths:
  # renamed model files (old + new paths both appear during git mv)
  - dbt_project/models/4_intermediate/shared/int_form_window.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_form_window__team.sql
  - dbt_project/models/4_intermediate/shared/int_momentum_window__team.sql
  - dbt_project/models/4_intermediate/shared/int_season_to_date.yml
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/4_intermediate/shared/int_season_to_date__team.sql
  - dbt_project/models/4_intermediate/shared/int_season_record__team.sql
  - dbt_project/models/4_intermediate/shared/int_season_to_date__player.sql
  - dbt_project/models/4_intermediate/shared/int_season_record__player.sql
  - dbt_project/models/5_marts/shared/mart_form_window__team.sql
  - dbt_project/models/5_marts/shared/mart_momentum_window__team.sql
  - dbt_project/models/5_marts/shared/mart_season_to_date__team.sql
  - dbt_project/models/5_marts/shared/mart_season_record__team.sql
  - dbt_project/models/5_marts/shared/mart_season_to_date__player.sql
  - dbt_project/models/5_marts/shared/mart_season_record__player.sql
  - dbt_project/tests/assert_form_window_matches_momentum.sql
  - dbt_project/tests/assert_momentum_window_matches_momentum.sql
  # referencing code (refs/comments updated, not renamed)
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_momentum__team.sql
  - dbt_project/models/4_intermediate/shared/int_team_profile__yoy.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - scripts/export_site_data.py
  # docs that NAME the models (doc-sync)
  - dbt_project/docs/layering.md
  - docs/metrics_context_model.md
  - docs/site_architecture.md
  - docs/competition_registry.yml
  - docs/competitions/wc26.md
  - docs/wireframes/01_fixture_page.md
  - docs/wireframes/99_gaps_register.md
  - docs/wireframes/metrics_display.md
  - .claude/task/contract.md

decisions_taken: >
  Pure rename approved by the CPO (Option 2). No SQL logic, grain, or metric changes — the
  compiled output of each model is identical apart from its table name. `window_type` VALUES
  and the published JSON key `form_window` are deliberately preserved (model-root vs
  cut-label vs UI-contract are separate axes). Verified by `dbt parse` (all refs resolve) +
  sqlfluff; no parallel-run needed because the logic is byte-identical. Old BQ tables become
  orphaned after the next build — dropping them is a separate CPO-approved cleanup (destructive).

decisions_reserved:
  - Do NOT change `window_type` values, the `form_window` JSON output key/variable, the
    UI "form window" caption term, or any model SQL logic. Do NOT rename
    `int_matchday__player_form_window` (different, pre-existing stale ref) or
    `form_window_kind` (future spec). If a reviewer finds a missed consumer or a stale
    model-name ref outside this scope, STOP and surface it.
  - Renaming the published JSON key or UI terms is a separate UI-contract decision, NOT here.

done_when:
  - all 8 models + the 1 test are renamed; every `ref()`/`name:`/comment pointing at an old
    name is updated; the export reads `mart_momentum_window__team` + `mart_season_record__*`
    while keeping the `form_window` output key; no stale `int_form_window`/`int_season_to_date`/
    `mart_form_window`/`mart_season_to_date` model-name reference remains in code or the
    in-scope docs (window_type values, the JSON key, form_window_kind, the unrelated
    int_matchday__player_form_window, and the historical audit excepted).
  - `dbt parse` succeeds (refs resolve); sqlfluff clean on changed SQL.
  - reviewers: scope-auditor (always) + analytics-engineer-reviewer (dbt_project/** +
    export_*) + cto-reviewer (scripts/export_* + tests/**) + data-engineer-reviewer
    (competition_registry.yml) + bi-analyst-reviewer (wireframes/**) — PASS.

amendments: (none)
