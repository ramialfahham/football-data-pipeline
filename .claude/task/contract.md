# Task contract — the Teams page's rankings, served by the warehouse

objective: >
  A new mart, `mart_team_index`, serves one row per team with a Team page: identity, club or
  national team, country, region, covered league and table position, and the orders the Teams
  page shows (#133): Top clubs per region, the order of countries, the order of clubs inside a
  country, Top national teams in the world and per region, and whether national teams come first.
  Each continent's top club cup and championship are data on its row in `confederations.csv`.
  The value of each round lives once, in `int_team_index__round_values`. The cup rounds that
  have no name yet get one in `round_names.csv`, so every round of the counted seasons has a stage.

refs: >
  #222, the Teams menu page (build plan approved in chat, 2026-10-30); design #133.

scope_paths:
  - dbt_project/seeds/confederations.csv
  - dbt_project/seeds/round_names.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/seeds/team_index_answer_key.csv
  - dbt_project/models/4_intermediate/shared/int_team_index__round_values.sql
  - dbt_project/models/4_intermediate/shared/int_team_index__round_values.yml
  - dbt_project/models/5_marts/shared/mart_team_index.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/macros/team_ranking_round_values.sql
  - dbt_project/tests/assert_team_index_cup_rounds_scored.sql
  - dbt_project/tests/assert_team_index_one_winner_per_cup_season.sql
  - dbt_project/tests/assert_team_index_stage_answer_key.sql
  - dbt_project/tests/assert_team_index_covers_every_team_page.sql
  - dbt_project/docs/layering.md
  - site_v2/src/i18n/strings.ts
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  New: `int_team_index__round_values`, read by `mart_team_index` and one test, and
  `mart_team_index`, read by nothing yet (the Teams page export is the next MR). The mart reads
  `mart_team_profile` (the teams with a page), `mart_team_competitions` (each team's furthest
  round per competition and season, and its table position), `dim_team`, `fct_fixture`,
  `int_round_names`, `competition_registry`, `competition_types` and `confederations`.
  `.venv/Scripts/dbt.exe ls --project-dir dbt_project --select confederations+ round_names+
  --resource-type model` lists 58 models: dim_region int_knockout_ties int_legs__team_match
  int_player_club_season__metrics int_player_competition_benchmark_metrics_long
  int_player_competition_benchmarks int_player_momentum__metrics int_player_profile__contribution
  int_player_profile__yoy int_player_season__metrics int_player_season_position__metrics
  int_player_season_record int_round_names int_standings__official_rank
  int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  int_team_momentum__metrics int_team_momentum_window int_team_profile__streaks
  int_team_profile__yoy int_team_season__biggest_results int_team_season__deserved_vs_actual
  int_team_season__longest_runs int_team_season__metrics int_team_season__metrics_cumulative
  int_team_season__standings_primary int_team_season__table_by_time int_team_season__table_legs
  int_team_season__table_state int_team_season_record mart_competition_fixtures
  mart_competition_index mart_competition_season_summary mart_fixture_standing_context
  mart_head_to_head mart_leaderboards mart_match_days mart_matchday_insights mart_next_matchday
  mart_player_career mart_player_competition_benchmarks mart_player_momentum mart_player_profile
  mart_player_season_record mart_standings mart_team_competition_benchmarks
  mart_team_competitions mart_team_fixtures mart_team_index mart_team_leaderboards
  mart_team_momentum_window mart_team_profile mart_team_season mart_team_season_insights
  mart_team_season_record mart_team_window_metrics.
  blast_radius: `confederations.csv` gains two columns that no existing model reads. The new
  `round_names.csv` rows are each scoped to one competition and match only round texts that
  have no name today: those fixtures gain a round name and a stage kind, so `int_knockout_ties`
  gains their ties and `mart_team_competitions` their cup status. Measured on prod: the rows name
  435 fixtures in 22 competition-season rounds that have no name today (UCL 2021-2024, AFCCL
  2017-2025, LIBER 2019-2025, CCCU 2024-2025); every matched round text has no name today, so no
  named round changes. One new copy key, `roundKnockoutPlayoffs`, in EN, DE and FI.
  Cost: about 0.6 GB a night more, the mart about 80 MB and its tests about 0.5 GB.

approved_design:
  - teams: #133
  - competition: #129
  - team: #134

acceptance_criteria:
  - "The round the provider calls \"Knockout Round Play-offs\" (Champions League 2024-25) is named \"Knockout phase play-offs\" / \"Play-offs der K.-o.-Phase\" / \"Pudotuspelivaiheen playoff\" wherever a page names it."
  - "The competition page (header and Matchdays) and the Team page (Competitions block) show the new round names through the round key, as their approved designs already do for every named round."

decisions_taken: >
  The build plan approved in chat, 2026-10-30, with its decisions: the last five finished seasons;
  each continent's top cup and championship on its row in `confederations.csv`; the round points
  written once, in a model; clubs and countries still level after the most recent season
  separated by wins, then goal difference, then sharing the place. Approved in chat, 2026-10-31:
  the copy of `roundKnockoutPlayoffs`; national teams still level on all three of #133's criteria
  separated by qualifier goal difference per match, then sharing the place. The stages come from
  `mart_team_competitions`, which already serves each team's furthest round and its final won.
  Readings of #133 stated on #222: CONCACAF's "1st Round" is the round of 32; for national teams
  "furthest stage" counts each round in order (group, round of 32, round of 16, quarter-final,
  semi-final, final, winner); a ranked club's region is its top club competition's. Approved in
  chat, 2026-10-31: the exact text of every new seed, model and column description; the model
  `int_team_index__round_values` with its text; the seed `team_index_answer_key.csv`; AFC's
  "League Phase East/West" named as its league stage and "Ranking of second-placed teams" as
  its group stage; the nightly cost of about 0.6 GB; the layering.md row; the region_key text.

decisions_reserved:
  - "none: every decision of this task is approved, see decisions_taken"

done_when:
  - dbt parse passes; the new SQL passes SQLFluff; the offline gates and the whole pytest pass.
  - The copy gate passes with the new key in three languages.
  - The MR's data:build:mr passes, and on prod, read-only, the new tests return no rows
    and the Top clubs, country and national-team orders are shown to the CPO.

amendments:
  - "Review round 1: the round values move from a macro into `int_team_index__round_values` (engineering_standards.md 1.3); the answer key is a seed like the existing ones; range and coverage tests added; four defects fixed."
