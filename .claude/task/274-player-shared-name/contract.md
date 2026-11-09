# Task contract — the shared-name flag the Player page title reads

objective: >
  Issue #274. The Player page title carries the position when two players of one name play at one
  club. Whether a player shares a name at a club is a fact about the warehouse's players, so
  mart_player_profile carries it as `shares_name_at_club`, tested, and the export only selects it.

refs: >
  #274. The title rule: #259, approved in chat, 2026-11-06. The column's place: the Player page
  review (#259), consumption layer rule.

scope_paths:
  - .claude/task/274-player-shared-name/
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_player_shares_name_at_club.sql

impact_map: >
  writers: mart_player_profile, written by the nightly prod build (fdp-nightly) and data:build:mr.
  downstream: `dbt ls --select mart_player_profile+ --resource-type model` lists only
  football_data_pipeline.5_marts.shared.mart_player_profile: a leaf. Its one reader outside dbt is
  scripts/export_site_data.py, which selects named columns; the new column is unread until the
  Player page MR (#259) selects it.
  layer_rules: check_layer_contract.py (marts read core, intermediate and seeds only; no
  partition_by or cluster_by); the mart already reads dim_player and int_player__page_profile.
  deploy_order: before the Player page (#259). A new column on a table the nightly rebuilds; until
  the merge the deployed mart has no such column and nothing reads it.
  blast_radius: one new boolean column; every existing column and row is unchanged. The full name
  moves into the players step and is read from there, with the same expression.

decisions_taken: >
  The flag is computed among players with a page, by the full name the page shows and the current
  club the page links: two such players with one name at one club are both true. A player with no
  page, no full name or no current club is false.

decisions_reserved: none.

done_when:
  - dbt parse passes; sqlfluff lint of the model passes as on main.
  - data:build:mr builds the mart and its tests pass.
  - python -m pytest tests passes.

amendments: (none)
