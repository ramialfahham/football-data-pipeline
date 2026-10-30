# Task contract — the official table at every kick-off, within the query time limit

objective: >
  int_team_season__table_by_time ran past BigQuery's 300-second query limit in main's build, so
  int_team_profile__yoy and mart_team_profile were skipped. BigQuery recomputes a step each time a
  later step reads it, so the model expanded into more than 1,400 stages. Its first steps move
  into two models stored as tables, the legs and the team state at every kick-off, so each is
  computed once; the table's columns, grain and values stay the same.

refs: >
  #235 (the Team page build). The plan, approved in chat, 2026-10-30, with the model names
  int_team_season__table_legs and int_team_season__table_state.

scope_paths:
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__table_legs.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__table_state.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__table_by_time.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - tests/test_*.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: int_team_season__table_by_time, now reading the two new models
  int_team_season__table_legs and int_team_season__table_state. downstream (dbt ls --select
  int_team_season__table_by_time+): int_team_profile__yoy, mart_team_profile.
  layer_rules: three intermediate models, materialised by the layer's one rule; no per-competition
  file. deploy_order: the MR data build. blast_radius: none in values; the table's columns and
  grain stay the same, proven by a row-by-row comparison with today's model.

approved_design:
  - none: no page output changes

decisions_taken: >
  The plan, approved in chat, 2026-10-30. Each step's SQL moves into one model; the legs model
  marks each leg with the dates it counts in the table so the state and table models read the
  counted legs, the play-off legs and the kick-offs from it. No new dependency; the recurring cost
  of three stored models is measured on the MR data build and put to the CPO.

decisions_reserved:
  - none: the model names are approved with the plan, and no value changes.

done_when:
  - dbt parse, SQLFluff on the three models, dry runs against prod, the offline gates and pytest pass.
  - The MR data build passes every table test as an error, with each model's time read from its log.
  - A comparison with today's model shows the same rows, none only on one side.

amendments: (none)
