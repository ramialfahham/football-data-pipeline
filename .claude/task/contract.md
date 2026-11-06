# Task contract — Player cards data: Yellow and Red cards, the fill from card events, has_player_page

objective: >
  The Player page's six cards (#136 note 4178574390) need Yellow cards and Red cards per tab, and
  the rule for who gets a page (#259 note 4178916887) needs a flag the page MR can read. The fill
  gives both card counts from the card events it already reads. No page changes.

refs: >
  #136 note 4178574390; #259 note 4178916887; plan approved in chat 2026-11-06.

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__fixture_players_from_lineups.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/2_base/api_football/base_apif__fixture_events.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/3_core/fct_fixture_event.sql
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/seeds/fixture_card_corrections.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_card_corrections_applied.sql
  - dbt_project/tests/assert_players_from_lineups_goals_add_up.sql
  - dbt_project/tests/assert_base_player_stats_cleaned.sql
  - dbt_project/tests/assert_player_stat_corrections_within_limit.sql
  - dbt_project/tests/assert_fixture_events_only_from_latest_fetch.sql
  - dbt_project/tests/assert_player_row_and_events_same_team.sql
  - dbt_project/models/4_intermediate/shared/int_player__page_profile.sql
  - dbt_project/models/4_intermediate/shared/int_player_window__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_squad_window__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_page.yml
  - dbt_project/models/5_marts/shared/mart_player_window_metrics.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/mart_player_fixture_stats.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/3_core/core.yml
  - dbt_project/docs/layering.md
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/seeds/metric_map.csv
  - dbt_project/seeds/player_match_cleaning_answer_key.csv
  - dbt_project/seeds/player_window_answer_key.csv
  - dbt_project/tests/assert_player_has_page.sql
  - scripts/generate_metric_sql.py
  - tests/**
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: every changed model is written only by dbt. int_player_window__metrics and
  int_player_squad_window__metrics hold SQL written by scripts/generate_metric_sql.py from the
  catalogue; metric_map.csv is written by scripts/sync_metric_docs_blocks.py.

  downstream: `dbt ls --select base_apif__fixture_players_from_lineups+ int_player__page_profile+
  --resource-type model` lists fct_fixture_player_stats, int_legs__player_match,
  int_legs__team_from_players, int_player__page_profile, int_player_club_season__metrics,
  int_player_competition_benchmark_metrics_long, int_player_competition_benchmarks,
  int_player_match__metrics, int_player_momentum__metrics, int_player_page__window_seasons,
  int_player_profile__contribution, int_player_profile__yoy, int_player_season__metrics,
  int_player_season__team, int_player_season_position__metrics, int_player_season_record,
  int_player_squad_window__metrics, int_player_window__metrics,
  int_team__current_national_competitions, int_team_competition_benchmark_metrics_long,
  int_team_competition_benchmarks, int_team_momentum__metrics, int_team_profile__yoy,
  int_team_season__deserved_vs_actual, int_team_season__metrics,
  int_team_season__metrics_cumulative, int_team_season_record, mart_competition_fixtures,
  mart_leaderboards, mart_match_days, mart_matchday_insights, mart_player_career,
  mart_player_competition_benchmarks, mart_player_fixture_stats, mart_player_momentum,
  mart_player_profile, mart_player_season_record, mart_player_squad_benchmarks,
  mart_player_window_metrics, mart_team_competition_benchmarks, mart_team_competitions,
  mart_team_index, mart_team_leaderboards, mart_team_momentum_window, mart_team_profile,
  mart_team_season, mart_team_season_insights, mart_team_season_record, mart_team_window_metrics.
  `dbt ls --select base_apif__fixture_events+ base_apif__fixture_players+ --resource-type model`
  adds base_apif__fixture_statistics, base_apif__lineups, base_apif__players, dim_player,
  fct_fixture_event, fct_fixture_lineup, fct_fixture_team_stats, int_legs__team_match,
  int_standings__official_rank, int_team_momentum_window, int_team_profile__streaks,
  int_team_season__biggest_results, int_team_season__longest_runs,
  int_team_season__standings_primary, int_team_season__table_by_time, int_team_season__table_legs,
  int_team_season__table_state, mart_competition_index, mart_competition_season_summary,
  mart_fixture_standing_context, mart_head_to_head, mart_next_matchday, mart_roster, mart_standings,
  mart_team_fixtures. With the seed empty, base_apif__fixture_events changes by one NULL column; a
  seed row replaces that match's card events, which base_apif__fixture_statistics reads.
  Every team model in that list reads the players through int_legs__team_from_players, which
  leaves filled rows out, so team values do not move. Player models that sum cards gain values
  where blanks stood. The export's player rows carry the new mart_player_window_metrics rows and
  has_player_page as columns it does not read yet: the page MR reads them.

  layer_rules: check_layer_contract.py. The fill stays 2_base. has_player_page is decided in the
  intermediate layer and the mart carries it. No model declares partition_by or cluster_by. No
  per-competition file.

  deploy_order: one MR, no raw change, no ingest change. The MR build writes its own ci_mr tables.
  After the merge, the next build of main and the 04:00 nightly rebuild prod.

  blast_radius: filled matches gain yellow and red cards, so player cards appear where blanks stood
  in player marts and leaderboards. mart_player_window_metrics gains two card rows per player tab.
  mart_player_profile gains one column. Team metrics do not move. No layout change. A provider row
  in dispute loses its cards, so that player's Yellow and Red cards go blank for the window. A sheet
  player with a card and no stat line gains a fill row: at 0 minutes his counts are 0, and with
  minutes his other counts are blank, so R4 blanks those metrics for his window.

approved_design:
  - none: no site or export file changes; the page MR reads these, named in the plan

decisions_taken: >
  The plan approved in chat 2026-11-06 names these readings. Plain counts of card events give both
  numbers, held to the card maximum. A match with no events gives blank. A club match counts for
  has_player_page when competition_season_map places its edition in the current or previous season, read
  by the competition's own season type. A national-team match counts from 1 July of last season's
  start year. The current season comes from today's date. The name has_player_page is the amendment below.
  NEW MECHANISM: none. RECURRING COST: none beyond two columns in tables already built.

decisions_reserved:
  - none: the seed description and the two rule names are approved in chat 2026-11-06, relayed by the coordinating session

done_when:
  - dbt parse passes; SQLFluff passes on every changed model.
  - scripts/generate_metric_sql.py and scripts/sync_metric_docs_blocks.py report no drift.
  - pytest tests passes.
  - data:build:mr is green, with assert_player_window_answer_key,
    assert_player_match_cleaning_answer_key and assert_player_has_page passing.

amendments: >
  Relayed by the coordinating session, 2026-11-06. The flag is named has_player_page and needs a
  tab as well as the 3 matches. By the Blank rule, a card no sheet player can take leaves that
  team's players without a placed card blank. The wording of three docs and the mart comment names
  the card events beside the goal events.

  Approved in chat 2026-11-06, relayed by the coordinating session, recorded on #256: cards are
  exact, and no name rule places a card. The Cards line joins cleaning_rules.md under Results. The
  seed fixture_card_corrections follows fixture_goal_corrections and is applied in
  base_apif__fixture_events. Until a correction stands, a player whose stat line and card events
  disagree has blank cards, and a card with no player on the sheet blanks its team's players
  without a card. Every other player of the match keeps his cards. The seed loads the researched
  matches whose every card lands on the match's sheet or stat lines, with the player id the sheet
  holds. A match with a card that does not stays in dispute. The rest of the list lands in a
  follow-up MR. A sheet player with a card and no stat row gains a row in the fill.
  base_apif__fixture_players compares each team's kept rows with its card events, per team. The
  fill checks its own team's cards against its sheet. By the Blank rule, a fill row at 0 minutes of
  a team with stat lines holds 0 for the counts the provider counted in the match.
