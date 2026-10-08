# Task contract — #166, part 1: the marts the next match page still lacks

objective: >
  The next match page's Players to watch and Head to head read what the approved design shows.
  mart_player_season_record ranks each side's players by goals plus assists, then goals, then
  fewer minutes, over the season record the window rules give the fixture. mart_head_to_head serves
  which side was at home in each recent meeting, describes its window truthfully, and tests the
  fields inside recent_meetings.

refs: >
  #166 (match page, state 1): its "Warehouse" checklist line; render match-page_2026-10-07_75. The
  warehouse-first split, no new model, and the window rules of docs/metrics_context_model.md §1 and
  §4 deciding the players' window: approved in chat, 2026-10-08.

scope_paths:
  - dbt_project/models/5_marts/shared/mart_head_to_head.sql
  - dbt_project/models/5_marts/shared/mart_player_season_record.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/tests/assert_head_to_head_recent_meetings_fields.sql
  - dbt_project/tests/assert_player_season_record_rank_order.sql
  - dbt_project/tests/assert_season_record_within_one_competition.sql
  - dbt_project/seeds/metric_map.csv
  - scripts/generate_metric_sql.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md

impact_map: >
  writers: mart_head_to_head is written only by its own model, from int_legs__team_match (which
    already carries home_away). mart_player_season_record is written only by its own model, from
    int_player_season_record. int_player_season_record gains two columns: scorer_points_player
    (generated from the catalogue by generate_metric_sql.py) and minutes (its running total). No
    model, seed or macro is added.
  downstream: dbtRunner `ls --select mart_head_to_head+ mart_player_season_record+ --resource-type
    model` printed exactly football_data_pipeline.5_marts.shared.mart_head_to_head and
    football_data_pipeline.5_marts.shared.mart_player_season_record. int_player_season_record's other
    reader, int_player_profile__yoy, names its columns, so its output is unchanged. Outside dbt:
    scripts/export_site_data.py selects mart_head_to_head (`select *`, drops only team_sk,
    opponent_team_sk, pair_key, is_canonical), so the new struct field reaches the fixture payload;
    the site renders recent_meetings fields by name. Nothing outside shared.yml and metric_map.csv
    names mart_player_season_record. mart_competition_fixtures gains two not_null tests only (prod:
    0 null names in 64,818 rows). assert_player_metrics_follow_catalogue_formula already recomputes
    every catalogue column of int_player_season_record, so it covers scorer_points_player there.
  layer_rules: check_layer_contract.py; metric SQL generated from metric_catalogue.csv.
  deploy_order: the models rebuild in the 04:00 UTC nightly after merge; the export reads
    mart_player_momentum until part 2, so no reader needs the new columns before then.
  blast_radius: mart_player_season_record keeps its window; a side now takes one window (this season,
    else last season) instead of a choice per player, and gains three columns. mart_head_to_head
    gains one struct field; every existing value unchanged.

decisions_taken: >
  The warehouse ships first and the export and page follow in their own MR; no new model; the
  players' window follows metrics_context_model.md §1 (a season record stays within one competition)
  and §4 (before a league starts, the previous season of this league): approved in chat, 2026-10-08.
  The §1 rule is enforced by a singular test: no season-record row, team or player, counts more
  matches than its entity played in that one competition and season (approved in chat, 2026-10-08).
  A side whose rank inputs are unknown has no rank. top_player_rank keeps the column name
  mart_player_momentum serves. The competition name and the form block's metric columns stay
  coverage-restricted (engineering_standards §3.1, rule R4), so they gain no not_null; the two
  team-name columns are never null and gain it.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none. RECURRING COST: measured on the compiled SQL before the
  MR and stated on it.

decisions_reserved:
  - The export, the match page, the breadcrumb markup and the footer: part 2, its own MR.

done_when:
  - dbt parse clean; sqlfluff clean on the changed SQL; generate_metric_sql.py --check and
    sync_metric_docs_blocks.py --check pass; check_layer_contract.py and check_description_hygiene.py
    pass; pytest tests/ passes.
  - The compiled models run as dry runs; their billed bytes before and after are on the MR.
  - Read once from prod with the compiled SQL: the catalogue recompute of int_player_season_record,
    the two new tests, and Dortmund's and Bremen's top five.
