# Task contract — #166, part 2 of the page build: the warehouse serves which form window each side shows

objective: >
  The match page shows one form window per side, as docs/metrics_context_model.md §3-4 give it: a
  domestic league before the team's first match in it shows last season's record in that league;
  every other side shows its form window. mart_team_season_record and mart_team_momentum each serve
  is_form_window, so the export picks the flagged block and decides nothing.

refs: >
  #166 (match page, state 1): Form comparison "one window per team as the phase rules give it". The
  page build in three MRs, and the column name is_form_window: approved in chat, 2026-10-08.

scope_paths:
  - dbt_project/models/5_marts/shared/mart_team_season_record.sql
  - dbt_project/models/5_marts/shared/mart_team_momentum.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_one_form_window_per_side.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md

impact_map: >
  writers: each mart is written only by its own model. mart_team_season_record reads
    int_team_season__metrics; mart_team_momentum reads int_team_momentum__metrics; both read the
    competition_registry seed for which competitions are domestic leagues, and mart_team_momentum reads
    int_team_season__metrics for whether the team has played the fixture's competition this season.
  downstream: dbtRunner `ls --select mart_team_momentum+ mart_team_season_record+ --resource-type model`
    printed football_data_pipeline.5_marts.domestic_league.mart_matchday_insights,
    football_data_pipeline.5_marts.shared.mart_team_momentum and
    football_data_pipeline.5_marts.shared.mart_team_season_record. mart_matchday_insights names the
    momentum columns it reads, so its output is unchanged. Outside dbt: scripts/export_site_data.py
    reads both marts with select *, so each side's w1 and w2 gain the field; the page reads neither
    until part 3.
  layer_rules: check_layer_contract.py; the window rule is decided in the marts, never in the export.
  deploy_order: both marts rebuild in the 04:00 UTC nightly after merge; no reader uses the column
    before part 3.
  blast_radius: one boolean column on each mart; every existing value unchanged.

decisions_taken: >
  The column name is_form_window: approved in chat, 2026-10-08. It sits on both marts with one
  meaning, so a domestic-league side with no record in that league yet (a promoted club before its
  first match there) shows no window, as §4 gives it. A singular test fails when a side flags both
  blocks, or when a side that has played its domestic league this season does not flag its form window.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none. RECURRING COST: measured on the compiled SQL before the
  MR and stated on it.

decisions_reserved:
  - The export's choice by the flag and the page: part 3, its own MR.

done_when:
  - dbt parse clean; sqlfluff clean on the changed SQL; check_layer_contract.py and
    check_description_hygiene.py pass; pytest tests/ passes.
  - Read once from prod with the compiled SQL: the number of sides per flag value and the new test's
    result; the billed bytes before and after on the MR.
