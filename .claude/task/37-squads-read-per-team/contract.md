# Task contract - a squad is read per team, so no squad the loader wrote is dropped

objective: >
  Issue #37. RAW_APIF_SQUADS holds one row per fetch covering a subset of a league's teams.
  stg_apif__squads keeps only the newest row per league_code, so every team that row does not carry
  vanishes from base_apif__squads and from the Player page's national-team tab (measured in prod:
  AFCON 16 teams current, 0 squads read; WCQAF 28, 0; WCQAS 37, 1 of which 16 hold a squad under
  another league). Now staging reads every row (the loader accumulates, like the profiles and
  career pulls; a team block with an empty list is kept as one row with no player),
  base_apif__squads gives each team the players of its newest block in any row (grain team, player; league_code
  is the league that capture was written under), and the two readers of it (int_player__page_profile
  and the test that recomputes it) join on the team and no longer on the league. The loader stops
  discarding a catch-up that the quota cut part-way: every team block it fetched is written, because
  a block is read on its own. The data contract and the source description state the per-team read.
  A new error test lists any team in RAW_APIF_SQUADS that staging does not carry and any team whose
  base players differ from its newest block. A python test pins
  that a quota-cut catch-up writes the teams it fetched.

refs: >
  #37 (the two candidate directions: read as accumulation, or write complete rows; this takes the
  read, which is correct against the rows already stored and needs no provider call). Unblocks the
  national-team Squad block of #342, which can read base_apif__squads by team.

depends_on:
  - none: every file this change edits is on gitlab/main (b62cd603)

shared_files:
  - none: no design baseline, chart manifest or chart pin is changed

scope_paths:
  - dbt_project/models/1_staging/api_football/stg_apif__squads.sql
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/1_staging/api_football/sources.yml
  - dbt_project/models/2_base/api_football/base_apif__squads.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/4_intermediate/shared/int_player__page_profile.sql
  - dbt_project/tests/assert_player_page_choices_follow_the_rule.sql
  - dbt_project/tests/assert_squads_read_per_team.sql
  - tests/test_staging_key_tests_moved.py
  - ingestion/api_football/loads/player_squads.py
  - ingestion/api_football/loads/competition_runner.py
  - docs/data_contract.md
  - tests/test_player_squads_catchup.py
  - tests/test_never_record_a_gap.py
  - tests/test_squads_read_per_team.py
  - .claude/task/37-squads-read-per-team/contract.md
  - .claude/task/37-squads-read-per-team/review.md
  - .claude/task/37-squads-read-per-team/review_input.patch

impact_map: >
  writers: the only writer of RAW_APIF_SQUADS is ingestion/api_football/loads/player_squads.py
  (load_player_squads_batch), called from competition_runner.run_player_squads_for_competition
  (in-season, every run) and run_player_squads_catchup (finished comps, require_complete=True today).
  The loader's rows do not change shape; only the catch-up's discard of a quota-cut partial goes.
  downstream: `dbt ls --select stg_apif__squads+ --resource-type model` (the .venv dbt, run on this
  branch) printed 13 models: stg_apif__squads, base_apif__squads, int_player__page_profile,
  int_player_page__window_seasons, int_player_squad_window__metrics, int_player_window__metrics,
  mart_player_competition_benchmarks, mart_player_fixture_stats, mart_player_index,
  mart_player_profile, mart_player_squad_benchmarks, mart_player_window_metrics and
  mart_team_momentum_window. A 14th line of that output, "snapshots.football_data_pipeline", is a
  warning about an unused configuration path and is not a model. The only direct reader of
  base_apif__squads is int_player__page_profile (national_team: a squad member of a current national
  competition's team) and the singular test assert_player_page_choices_follow_the_rule, which
  recomputes it. mart_roster does not read squads (it reads dim_player_team_season_mapping, club
  competitions only).
  layer_rules: staging reads all rows and flattens (no qualify, as stg_apif__player_profiles); the
  newest block per team after the team-id override and the player grain are base;
  check_layer_contract applies unchanged. No new model, no per-competition file.
  deploy_order: one build; the nightly picks it up after merge. No raw rewrite, no provider call.
  blast_radius: stg_apif__squads and base_apif__squads gain the teams the old read dropped (rows rise
  from 95,974 in base); a national-team player whose team the old read lost now carries the national
  tab the approved rule gives that player (the rule is unchanged, its input was short). A club squad read
  from the newest block of the team across leagues can show the newest capture where the old read
  showed the newest row of one league; no club mart reads it. Measured and compared in the MR with
  ci_mr tables against prod.
  recurring_cost: staging scans RAW_APIF_SQUADS once as before (1.16 GB, payload column); the new
  test scans it once more per run, about 1.2 GB a night, about 36 GB a month, well under one dollar.

decisions_taken: >
  Engineering calls of the coordinating session's brief for #37, which names the defect and leaves
  the route open (the issue lists two). Route: read the table as accumulation, the way
  stg_apif__player_profiles and stg_apif__player_teams are read; the other route (carry stored
  teams into each new row) changes ingestion and needs a read of the whole raw table on every run.
  Table class: layering.md, unchanged, says a raw table is read as accumulation iff its loader is
  skip-if-present. The squads catch-up loader is: captured_team_seasons lists what is stored and
  select_squad_catchup_team_ids skips it. So RAW_APIF_SQUADS falls under the rule's own test, and
  layering.md needs no edit. The sentences that state it (data_contract.md, the staging yml
  header, the model headers) go in the MR head as text approved by the merge.
  Loader: with every team block read on its own, the discard of a quota-cut catch-up has no purpose
  and costs the fetches already paid for; it goes. Player page: the rule that gives a player the
  national-team tab is unchanged; only its input, the squad list, is no longer short. The recompute
  test drops the league join with the model and the national_seasons join, which cannot filter
  anything because expected_current already holds national seasons only. Recurring cost: one extra
  scan of RAW_APIF_SQUADS per run, about 1.2 GB a night, under the CPO's money threshold; stated
  here so the CTO's recurring-cost item sees it.
