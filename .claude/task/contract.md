# Task contract — team stat columns in core and intermediate describe themselves as team columns

objective: >
  #193. Team columns in core and intermediate that BigQuery describes with a player metric's
  sentence (for example "Shots on target the player had." on fct_fixture_team_stats) point at a
  team description instead: the __team_match blocks for the statistics-line columns, and new
  __team_from_players blocks for the totals summed from players. Docs only.

refs: >
  #193, approved by the CPO; his go to build the next handover item, 2026-10-05.

acceptance_criteria:
  # The issue's checklist line, verbatim.
  - "No team model outside the marts describes a column with a player metric's definition: the 19 columns below point at a team description."

scope_paths:
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/docs/shared_columns.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  Descriptions only (short form): no .sql file, seed, macro or catalogue row is in scope, so no model
  is rebuilt differently and no value changes. writers: the four yml files and shared_columns.md are
  read only by dbt parse and docs generate. downstream: +persist_docs pushes each description to its
  BigQuery column on the next build of fct_fixture_team_stats, int_legs__team_match,
  int_legs__team_from_players, int_team_momentum_window and int_team_season_record, nothing else;
  check_description_hygiene.py holds every rendered description under the 1,024-character limit.
  layer_rules: none apply to a description. deploy_order: none. blast_radius: the column
  descriptions of those five tables in BigQuery and the dbt docs; no number, page or export changes.

decisions_taken: >
  #193 as written.

  Readings, under the CPO's delegation of 2026-10-02 ("Readings of approved rules are yours"):
  - The checklist line's rule is "no team model outside the marts describes a column with a player
    metric's definition". A sweep of every team model's yml outside the marts finds the issue's 19
    columns and 4 more on int_legs__team_from_players (duels, duels_won, dribbles,
    dribbles_success), the table the issue's team totals come from; all 23 are fixed.
  - Every one of the five models has one row per team-match, so no column sums a window and no
    "Here, ..." sentence is needed. The statistics-line columns take the existing __team_match
    blocks; the totals summed from players take four new __team_from_players blocks in
    shared_columns.md, worded from the player block with "this team's players ... summed over its
    players".

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none; descriptions are pushed by the
  build that already runs.

decisions_reserved:
  - The marts are not in scope (fixed with the metric map). No catalogue description changes.

done_when:
  - The sweep finds no team model outside the marts with a player description.
  - dbt parse, check_description_hygiene.py, sync_metric_docs_blocks.py --check and pytest pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.

amendments: (none)
