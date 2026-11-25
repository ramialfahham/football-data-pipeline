# Task contract — Statistics pages, step 1b: the export of the full ranked field

objective: >
  Issue #347 (build of the Statistics pages; design approved on #139 and #140), step 1 of its
  How, second of two merge requests (the first, !537, gave the two goals metrics their place in
  the catalogue). The `leaderboards/{league_code}/{season}.json` export entity serves, for every
  competition of the Statistics dropdown, the full ranked field of every board of the Players
  tab and the Teams tab, as the two leaderboard marts rank it. No page reads the payload yet; the
  pages are step 2 of #347.

refs: >
  #347; #139 approved design and notes of 2026-11-10 and 2026-11-12; #140; the earlier data
  build (0175ee42, "every player and team ranked") that made the marts complete.

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - tests/test_catalogue_order.py
  - tests/test_leaderboard_board_sets.py
  - tests/test_statistics_payload.py
  - docs/site_architecture.md
  - .claude/task/347-statistics-payload/contract.md
  - .claude/task/347-statistics-payload/review.md
  - .claude/task/347-statistics-payload/review_input.patch

depends_on:
  - none: !537 (the catalogue order) is merged; the marts it reads are on main

shared_files:
  - none: no design baseline, chart manifest or chart pin changes

approved_design:
  - statistics: #139

impact_map: >
  writers: no ingestion, dbt model or seed changes.
  downstream: the export reads mart_leaderboards and mart_team_leaderboards, which
  `dbt ls --select metric_catalogue+ --resource-type model` lists with
  mart_player_competition_benchmarks and mart_team_competition_benchmarks; none of them changes.
  Consumption: scripts/export_site_data.py. The `leaderboards` entity had no reader (it is
  outside DEPLOY_ENTITIES and tests/test_deploy_entities.py pins that); its old payload (thirteen
  boards, rank <= 10) is replaced, nothing else reads it. The fetch_metric_rows and
  fetch_player_metric_rows row sets are filters and do not change
  (tests/test_form_comparison_metric_set.py).
  layer_rules: check_layer_contract.py does not apply (no model changes).
  deploy_order: additive. The payload is written by the export only; the pages of step 2 read it.
  blast_radius: the export's nightly read of mart_leaderboards and mart_team_leaderboards gains
  one query each over the Statistics board sets (bytes measured in the MR). No page output
  changes in this MR.

decisions_taken: >
  The board sets, forms and ranking directions are the #139 design (approved in chat,
  2026-11-10); the marts serve exactly those boards (tests/test_leaderboard_board_sets.py pins
  the tuples to the marts' lists). The page prints the shown value: the marts' display_value, as
  the earlier data build's contract decided so that the rank and the page cannot disagree
  (approved in chat, 2026-11-11, on #230). The dropdown's order is the statistics_competitions
  seed and its Clubs and National teams groups are the competition's entity_type, as that seed's
  description says. Only the current season of a competition is exported, the rows the marts
  serve with is_current_season, as the season control lists "today the current one" (#139). The
  boards follow the catalogue's metric_order. A competition whose latest season serves no board
  has no payload.

decisions_reserved:
  - none: every rule applied is named in decisions_taken with its approval

done_when:
  - full pytest passes
  - the payload of one real competition is exported and its size and the query bytes are reported in the MR
  - tests/test_deploy_entities.py is unchanged and passes
