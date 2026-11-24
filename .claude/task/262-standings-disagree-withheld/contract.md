# Task contract - a team-season whose results disagree with the provider's standings is withheld and listed

objective: >
  Issue #262, box "Only a check that catches a defect in our own code stops the nightly." Two tests stop
  the build when the provider's results disagree with the provider's standings:
  assert_team_season_equals_league_table (a team-season's wins, draws, losses, goals, goals against or
  points differ from the table row that counts the same games) and
  assert_team_season_games_not_short_of_standings (our count of played games is below the standings'
  played count). Both compare provider data with provider data. Now int_team_season__metrics carries a
  flag counts_withheld, true for a team-season where either disagreement holds, read from fct_standings
  and the standings_points_adjustments seed. For such a team-season every season value of the row is
  blank (the keys, entity_type and the flag stay), so the site renders it as it renders any withheld
  value, and mart_team_leaderboards ranks it as a blank metric value is ranked today: a board is
  served only when every team that played has a value, so the competition-season's team boards are
  withheld. The team-season's matches go on mart_competition_research_list. Both tests stay at error and
  become the proof: they derive the disagreement inline from fct_standings and the legs, never from the
  flag, and fail where a disagreeing team-season is not withheld or a withheld one does not disagree.
  The tests that compare int_team_season__metrics with a recomputation expect a blank value where the
  same inline derivation says the team-season disagrees. assert_team_table_equals_published_tables
  (the rebuilt table, our code) stays at error and leaves out only the withheld team-seasons: a team
  that is not withheld and differs from the published table in points or place is a red row, and the
  places are compared among the teams that are not withheld. A hand-written answer key runs both
  disagreements, the agreements next to them, the points adjustment and a team with two standings rows
  through the macro that finds them, another runs the published-table comparison, including a team
  that is not withheld whose points are off by 1, and python pins fix the wiring.

refs: >
  #262 What exactly / How (approved in chat, 15 Nov 2026). The coordinating session ruled, for this
  change (standings, option B): the counts of a team-season whose provider results disagree with the
  provider standings are withheld in base through a flag in int_team_season__metrics that reads
  fct_standings; the row and the team stay; every season value renders as the site renders a withheld
  value; it is ranked as a blank metric value is today, with no new ranking rule; the matches of the
  team-season go on the research list; the recompute tests derive the disagreement inline and stay at
  error; assert_team_table_equals_published_tables stays at error and must still fail on a place
  mismatch among teams whose counts agree.

depends_on:
  - none: every file this change edits is on gitlab/main

shared_files:
  - none: no design baseline, chart manifest or chart pin is changed

scope_paths:
  - dbt_project/macros/team_seasons_off_standings.sql
  - dbt_project/macros/published_table_mismatches.sql
  - dbt_project/macros/team_season_counts_from_legs.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/5_marts/shared/mart_team_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_competition_research_list.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/tests/assert_team_season_equals_league_table.sql
  - dbt_project/tests/assert_team_season_games_not_short_of_standings.sql
  - dbt_project/tests/assert_team_season_off_standings_answer_key.sql
  - dbt_project/tests/assert_team_season_blank_exactly_when_withheld.sql
  - dbt_project/tests/assert_no_uncatalogued_season_metric.sql
  - dbt_project/tests/assert_team_form_window_follows_the_rule.sql
  - dbt_project/tests/assert_mart_team_leaderboards_one_leader_per_league.sql
  - dbt_project/tests/assert_team_metrics_follow_catalogue_formula.sql
  - dbt_project/tests/assert_mart_team_leaderboards_boards_cover_every_team.sql
  - dbt_project/tests/assert_team_table_equals_published_tables.sql
  - dbt_project/tests/assert_published_table_mismatches_answer_key.sql
  - tests/test_team_season_withheld_wiring.py
  - .claude/skills/research-provider-errors/SKILL.md
  - .claude/task/262-standings-disagree-withheld/contract.md
  - .claude/task/262-standings-disagree-withheld/review.md
  - .claude/task/262-standings-disagree-withheld/review_input.patch

impact_map: >
  writers: three macros added (team_seasons_off_standings, team_season_counts_from_legs, which builds
  the season counts the tests compare with the standings from the legs, and published_table_mismatches);
  int_team_season__metrics gains the flag counts_withheld and blanks its 66 season values where it is
  true; mart_team_leaderboards counts a withheld team-season in the field of teams that played and takes
  the current season of a league from the seasons whose teams played, not from the seasons that have a
  board (read-only on prod, the mart SQL equals the prod table: 151,513 rows each, 0 rows only on
  either side);
  mart_competition_research_list gains one branch and one row kind; two tests rewritten into the proof
  (assert_team_season_equals_league_table, assert_team_season_games_not_short_of_standings), two
  answer keys and one reverse-direction test added, two recompute tests expect a blank value for a
  withheld team-season (assert_team_metrics_follow_catalogue_formula,
  assert_team_form_window_follows_the_rule, whose season-record half recomputes games_played);
  the hand-worked assert_team_season_answer_key is unchanged and does not follow the withhold, so a
  keyed team-season that comes out withheld is a red row,
  assert_mart_team_leaderboards_boards_cover_every_team counts a withheld team-season as having played,
  assert_mart_team_leaderboards_one_leader_per_league expects a league whose latest season holds a
  withheld team-season to have no current season, as assert_one_current_season_per_league does for the
  player boards, one test that leaves out the withheld team-seasons
  (assert_team_table_equals_published_tables), and assert_no_uncatalogued_season_metric
  lists the flag among the columns that are no metric. The yml tests not_null on the
  withheld values are replaced by assert_team_season_blank_exactly_when_withheld, which holds the
  values blank exactly where the flag is true, in int_team_season__metrics, mart_team_season,
  mart_team_season_insights and mart_team_season_record: int_team_season__metrics.season_games_played,
  mart_team_season.played, wins, draws, losses, goals_for, goals_against, goal_diff, points,
  clean_sheets, mart_team_season_insights.season_games_played and
  mart_team_season_record.games_played. The four models carry blank values for a withheld
  team-season.
  The standings row itself is untouched: mart_standings and fct_standings show the provider's own
  table row (rank, points, played, wins, draws, losses, goals), never our counts, so no rule for the
  position of a standings row with withheld counts is needed and none is added.
  The changed model and its readers, pasted from `dbt ls --select int_team_season__metrics+
  --resource-type model` (the .venv dbt, repo root): int_team__featured_season,
  int_team_competition_benchmark_metrics_long, int_team_competition_benchmarks,
  int_team_season__deserved_vs_actual, int_team_season__metrics, int_team_window__metrics,
  mart_matchday_insights, mart_player_index, mart_team_competition_benchmarks, mart_team_index,
  mart_team_leaderboards, mart_team_momentum_window, mart_team_page_window_metrics, mart_team_profile,
  mart_team_season, mart_team_season_insights, mart_team_season_record, mart_team_window_metrics.
  The flag reads core.fct_standings and the seed standings_points_adjustments, both upstream of nothing
  that reads int_team_season__metrics, so no cycle: `dbt ls --select +fct_standings` lists
  base_apif__competition_seasons, base_apif__crest_objects, base_apif__league_entity,
  base_apif__leagues, base_apif__standings, dim_competition_season, dim_league, fct_standings and the
  staging models, and no model of int_team_season__metrics+.
  `dbt ls --select mart_team_leaderboards+ mart_competition_research_list+ --resource-type model`
  lists mart_competition_research_list and mart_team_leaderboards, each alone.
  Measured on prod, read-only (2 MB): the equals-table comparison of int_team_season__metrics with
  core.fct_standings, adjustments applied, returns no row; the new model SQL run on prod inputs equals
  the prod table (14,296 rows each, 0 rows only on either side, 0 rows withheld).
  downstream: prod holds no team-season that disagrees today, so no row, no number and no page
  changes; a later disagreement blanks one team-season and
  withholds the team boards of its competition-season, and lists its matches.
  layer_rules: macros, one intermediate model, mart edits, tests; check_layer_contract applies unchanged.
  deploy_order: one build; the nightly picks it up after merge.
  blast_radius: none for any value today. A provider result that disagrees with the provider standings
  no longer stops the nightly: it withholds the team-season and lists its matches.

approved_design:
  - none: no page output changes

decisions_taken: >
  Ruled by the coordinating session on #262's approved rule (approved in chat, 15 Nov 2026), standings
  option B. Engineering decisions inside the ruling (working agreement section 10 unclear cases): the
  flag is named counts_withheld; the disagreement is the two conditions of the tests that stop the
  build today, unchanged (a table row that counts the same games and differs in a count or in points
  net of the declared adjustments; our played count below the largest played count of the team-season's
  standings rows); the withheld values are the 66 columns of the row apart from team_season_sk,
  team_sk, league_sk, season_sk, league_code, season_api_year and entity_type, season_games_played
  among them, so a withheld team-season is a team-season with no values, and the leaderboard field
  counts it as having played (season_games_played >= 1 or counts_withheld), which withholds the boards
  of its competition-season through the existing rule that every team that played must have a value;
  the research list names each finished match of the team-season, once per match and team, as
  team_season_off_standings with seed none (no seed fixes it: a result, an adjustment or the standings
  row can be the cause); the macro team_seasons_off_standings takes the team-season counts, the
  standings and the adjustments as relations, so the model feeds it the final row and the tests feed it
  counts built from the legs, and the answer key feeds it hand-written rows; assert_team_table_equals_
  published_tables leaves out of its comparison only the team-seasons withheld against the standings
  (ruled by the coordinating session): a team that is not withheld and whose rebuilt points differ from
  the published points is a red row, and so is a place that differs, as before. The withheld team-seasons
  are derived inline from the legs and fct_standings. A team's place on each side is its rank on
  that side less the number of withheld teams of the section ranked above it, so a withheld team's
  points cannot move the places of the others; that is the rank itself when no team is withheld. The
  teams whose place the league's rule does not fix, and the teams with no published or no rebuilt
  rank, stay in the section and are left out of the result. A place is compared only where both
  ranks are not blank. A withheld team does not decide whether a published section is comparable. The adjustments of a team-season are summed per
  trimmed group name.
  The benchmark distribution of int_team_competition_benchmark_metrics_long leaves a withheld
  team-season out through its existing games floor for the competition-seasons it reads from
  int_team_season__metrics. A competition-season with a table phase reads
  int_team_competition_phase__metrics, which is built from the legs and is not blanked.
  Not blanked, and left to the follow-up change the coordinating session ruled for the streaks: the
  streaks, longest runs and biggest results of mart_team_profile, the team page window metrics
  (int_team_window__metrics, mart_team_page_window_metrics), mart_competition_season_summary and the
  phase benchmarks above, which all read the legs directly. The follow-up reuses the row kind
  team_season_off_standings. A team-season whose standings snapshot is ahead of our finished matches
  is withheld until the next build brings the match, the case the games_short condition already
  describes. The doc blocks of the blanked columns say the value is blank only where the team-season
  is withheld.

decisions_reserved: >
  none: no page, metric, name or rule is added.

done_when:
  - python scripts/ci_local.py --mr passes
  - dbt parse passes
  - python -m pytest tests/test_team_season_withheld_wiring.py passes, and fails with the macro, the model flag, the leaderboard field, the mart branch or a test changed
  - the MR pipeline is green, data:build:mr included

amendments:
  - scope_paths gained assert_team_form_window_follows_the_rule.sql and
    assert_mart_team_leaderboards_one_leader_per_league.sql (both read the withheld values and stay at
    error, found in review round 1), shared_columns.md (the doc blocks of the blanked columns), and
    the macro team_season_counts_from_legs.sql. Authority: the coordinating session's standings (B)
    ruling, as engineering consequences classified under working agreement section 10, unclear cases.
  - decisions_taken: a place is the rank less the withheld teams ranked above it (no re-ranking among
    the teams that are not withheld), and a withheld team does not decide whether a published section
    is comparable. Both found in review; same ruling and authority as above.
  - decisions_taken: assert_team_season_answer_key stays as on main. Its numerators are worked by hand
    and name the correct value, so it is not a recomputation from the legs and does not expect a blank
    for a withheld team-season; a keyed team-season that comes out withheld is red. Found in review;
    same ruling and authority as above.
