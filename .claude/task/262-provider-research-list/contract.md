# Task contract — the daily list of provider errors to research

objective: >
  Issue #262, boxes 1, 2 and 7. A new mart, mart_competition_research_list, rebuilt by the nightly,
  holds one row per match (or match-team, or seed row) where a check of the provider's data
  withholds a value on goals, scores, awards or cards, and one row per correction the provider no
  longer needs. The list's reader is the research routine of #262 (its own MR). Two provider-data
  cases that still fail the build move to the list: a correction the provider no longer needs
  (no_longer_needed in assert_result_corrections_applied) and a match whose goal events add up
  neither alone nor with the players' goals (goals_not_reconciled in
  assert_mart_competition_fixtures_goals_add_up). Cards gain the no-longer-needed check the other
  correction seeds have.

refs: >
  #262 What exactly boxes 1, 2 and 7 (box 7: approved in chat, 2026-11-15); scope ruled by the
  coordinating session on 2026-11-18: this MR leaves out the standings tests and the standings
  section kind, which get their own MR. Research priority tiers: #176 (approved in chat,
  2026-10-12). Withhold pattern: !446 and !447.

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__fixture_events.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/4_intermediate/shared/int_pipeline__corrections_no_longer_needed.sql
  - dbt_project/models/4_intermediate/shared/int_pipeline__corrections_no_longer_needed.yml
  - dbt_project/models/5_marts/shared/mart_competition_research_list.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/docs/layering.md
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_result_corrections_applied.sql
  - dbt_project/tests/assert_mart_competition_fixtures_goals_add_up.sql
  - .claude/task/262-provider-research-list/contract.md
  - .claude/task/262-provider-research-list/review.md
  - .claude/task/262-provider-research-list/review_input.patch

impact_map: >
  writers: every changed model is written by dbt only; no ingestion code and no raw table change.
  The two new models are new leaves.
  downstream: `dbt ls --select base_apif__fixture_events+ --resource-type model` on 2026-11-18 lists
  89 models, the two new ones included: base_apif__fixture_events base_apif__fixture_events_checked base_apif__fixture_players
  base_apif__fixture_players_checked base_apif__fixture_players_from_lineups
  base_apif__fixture_statistics base_apif__lineup_sheets base_apif__lineups base_apif__players
  dim_player fct_fixture_event fct_fixture_lineup fct_fixture_player_stats fct_fixture_team_stats,
  the int_player_*, int_team_*, int_legs__*, int_standings__official_rank and
  int_competition_season__player_stat_corrections models, and every mart from
  mart_competition_fixtures to mart_team_window_metrics. The one change there is a new column,
  provider_cards_match_research. Each of the model's ten readers names its columns
  (base_apif__fixture_events_checked's final select and fct_fixture_event's are explicit;
  the others select named columns), so no reader carries the column and no number below changes.
  The new int model and mart have no downstream model; the mart is the int model's one reader. The two edited tests read
  mart_competition_fixtures, fct_fixture_event and the four result seeds; they lose provider-data
  cases and gain goals_on_not_recorded, a check of our code.
  layer_rules: check_layer_contract applies unchanged. The int model reads base and seeds only
  (no mart). The mart reads base, core, intermediate, seeds and mart_competition_fixtures
  (marts may ref marts): the provider_* columns and the withheld card and line-up goal flags exist
  only in base. No model sets its own materialisation.
  deploy_order: one build; the nightly picks it up after merge.
  blast_radius: no shipped number changes; the nightly can no longer stop on the two moved cases.
  The new mart's nightly bytes come from a dry-run and are stated in the MR.

approved_design:
  - none: no page output changes; the list is read by the research routine, not by the site

depends_on:
  - none: builds on merged !446, !447 and !465 only
shared_files:
  - none: no design baseline, chart manifest or chart pin changes

decisions_taken: >
  Ruled by the coordinating session on 2026-11-18 under #262. (1) The list holds the checks of
  box 1's kinds (goals, scores, awards, cards): result_withheld (result_needs_research),
  goals_not_reconciled, scorer_withheld and assist_withheld (scorer_ and assist_needs_research),
  cards_withheld (cards_need_research), lineup_goals_withheld (goals_need_research), and
  correction_no_longer_needed for fixture_result_corrections, fixture_goal_corrections,
  fixture_round_corrections, standings_corrections and fixture_card_corrections. Each row names
  the seed that fixes it. Team country and the stats limit are not result kinds and stay off the
  list. (2) Each row carries research_tier from #176: 1 a domestic league of the registry, 2 a
  match of a national team, 3 a match of a club that plays a registry domestic league in its
  current season, NULL otherwise; and is_current_season from dim_competition_season. Which tiers
  are researched is the routine's rule, not the list's. (3) The no-longer-needed logic moves
  unchanged from assert_result_corrections_applied into int_pipeline__corrections_no_longer_needed;
  the test keeps every check of our seed and code. (4) A card correction is no longer needed when
  the provider's own card events of the match, cleaned, equal the seed card for card (player id,
  card, minute and added minute), with no card without a player, and its stat lines carry the same
  cards (no cards_from_research row). base_apif__fixture_events compares the events before the seed
  replaces them, as provider_cards_match_research. (5) goals_not_reconciled leaves the error test
  and the test gains goals_on_not_recorded: a not_recorded match serves no goal. (6) Both edited
  tests stay error severity. The list is a table with no severity: nothing on it stops a build.
  (7) Item key: item_key, the check and its subject, unique.
  (8) Names follow engineering_standards §1: the mart's entity is competition, because every row
  is a competition's match or standings row; the int model is an int_pipeline__ helper.
  Threshold declarations: no new mechanism (a mart and an int model in existing layers). Recurring cost: two small tables a night, measured by dry-run in the MR.

decisions_reserved:
  - The standings tests (assert_team_season_equals_league_table, assert_team_table_equals_published_tables, assert_team_season_games_not_short_of_standings) and kind_needs_research: what a disagreement withholds is the CPO's (Q2 of the #262 plan), its own MR.
  - The live-without-merge route, the scheduled runner and the weekly report: CPO decisions, not built here.
  - Which research tiers the routine researches: the research skill's MR.

done_when:
  - dbt parse passes; sqlfluff lint passes on the changed models and tests; the full pytest suite passes.
  - The MR's data build runs every model and every test passes.
  - The MR states, measured read-only on its tables, the list's rows by check and tier, and the nightly bytes of the two new models from a dry-run.
