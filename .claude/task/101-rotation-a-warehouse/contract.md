# Task contract — Home rotation, part A: the warehouse

objective: >
  Issue #101, first of three merge requests. The warehouse serves what Home's group rotation
  draws from: the slots and their weights (a seed), and per league its slot, its current season,
  whether it is in season and its last completed season (a mart). It also carries the alerts:
  one for no slot in season, and the every-board-has-a-leader test widened to every slot that can
  be drawn. Nothing reads the mart yet; the export (part B) and the fallback copy (part C) follow.

refs: >
  #101 (decision 2026-09-03, weights changed and build scope confirmed 2026-09-13). The seed home,
  the widened alert and the split into three merge requests are the coordinator's rulings,
  2026-11-23 and 2026-11-25.

scope_paths:
  - dbt_project/seeds/home_rotation_slots.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/5_marts/shared/mart_home_rotation.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_home_rotation_*.sql
  - dbt_project/tests/assert_mart_leaderboards_every_home_board_has_a_leader.sql
  - dbt_project/dbt_project.yml
  - .claude/task/101-rotation-a-warehouse/contract.md
  - .claude/task/101-rotation-a-warehouse/review.md
  - .claude/task/101-rotation-a-warehouse/review_input.patch

impact_map: >
  writers: new seed home_rotation_slots (hand-authored CSV); new mart mart_home_rotation, written
  only by its own SQL. No existing model, seed or loader changes.
  downstream: mart_home_rotation is a leaf and nothing reads it yet. Upstream it reads
  int_legs__team_match, dim_competition_season and the seed. The one existing test this changes,
  assert_mart_leaderboards_every_home_board_has_a_leader, is a leaf test; `dbt ls --select
  +assert_mart_leaderboards_every_home_board_has_a_leader` lists its parents (mart_leaderboards,
  dim_competition_season, fct_fixture, fct_fixture_player_stats and their tests) and it now also
  reads mart_home_rotation.
  layer_rules: marts read core, intermediate and seeds, never a raw table; no partition_by or
  cluster_by; check_layer_contract.py and check_description_hygiene.py (every description under
  1,024 characters) apply.
  deploy_order: the seed and the mart are created by the first dbt build after the merge. The
  widened test reads the mart in the same build, after it. Nothing else depends on it, so no
  model breaks before then.
  blast_radius: none for any page or number; two new tables and four new tests. The widened test
  now covers every in-season league of every slot; against prod data it returns 0 rows.

approved_design:
  - none: no page output changes

depends_on:
  - none: the leaderboard marts this reads are on main

shared_files:
  - none: no design baseline, component registry or font coverage file changes

decisions_taken: >
  The weights 80/10/10 and the rule (a slot is in season when one of its leagues has 3 or more
  finished matches this season; no slot in season falls back to elite's last completed season with
  a data-quality alert) are #101's CPO decision of 2026-09-03 and its 2026-09-13 amendment. The
  slots and weights live in the seed home_rotation_slots (columns slot, competition_group,
  slot_weight, is_fallback_slot), ruled by the coordinator on 2026-11-23, replacing #101's
  "registry" wording; the extra column is_fallback_slot and the dbt var
  home_rotation_min_finished_matches (3) were accepted by the coordinator. A league's group is read
  from its played season's row, as the leaderboard marts do. No existing mart fits: the
  competition index and the leaderboard marts hold no slot, weight or per-league in-season flag.
  No recurring cost and no new mechanism.

decisions_reserved:
  - none: nothing here is a page, a metric or a name that is the CPO's to decide.

done_when:
  - dbt parse succeeds from the repo root; dbt ls --select mart_home_rotation+ lists the mart and its tests.
  - The mart SQL and the new and widened tests dry-run against BigQuery, and the widened test returns 0 rows on prod data.
  - python scripts/ci_local.py --mr is green apart from the known line-ending failure of tests/test_ci_local.py.
  - The full pytest run is green apart from that known failure.
  - CI's data:build:mr is green, and mart_home_rotation returns one row per league and role.

amendments: (none)
