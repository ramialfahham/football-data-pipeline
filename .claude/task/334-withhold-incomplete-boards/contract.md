# Task contract — a Rankings board is shown only when every team or player in its field has a value

objective: >
  Issue #334: a Rankings board is withheld for a competition-season unless every team that played
  (team boards, checked per metric) has a value for its metric, and a player board is withheld for
  a competition-season in which a finished match has no player statistics. The CAF Champions League
  2026 shots boards ranked 15 of 61 teams as the competition's ranking; the rule removes them.

refs: "#334; R4 in metric_rules.md; stats_need_research in int_competition_season__player_stat_corrections"

scope_paths:
  - .claude/task/334-withhold-incomplete-boards/**
  - dbt_project/models/5_marts/shared/mart_team_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/metric_rules.md
  - dbt_project/tests/assert_mart_team_leaderboards_boards_cover_every_team.sql
  - dbt_project/tests/assert_mart_leaderboards_season_boards_have_player_stats.sql
  - dbt_project/tests/assert_mart_leaderboards_every_home_board_has_a_leader.sql
  - dbt_project/tests/assert_mart_team_leaderboards_difference_ranks_every_team.sql
  - dbt_project/tests/assert_one_current_season_per_league.sql

impact_map: >
  writers: mart_team_leaderboards and mart_leaderboards are the only models changed.
  downstream: both are leaf marts; `.venv/Scripts/dbt.exe ls --select mart_team_leaderboards+
  mart_leaderboards+ --resource-type model` lists only these two models. Their readers are the
  export (scripts/export_site_data.py: the competition Rankings boards, Home's Top teams and Top
  players, the leaderboards payload; the match window of mart_leaderboards is untouched).
  tests: three existing tests assert that a board exists where it no longer must (the third,
  assert_one_current_season_per_league, recomputes which latest seasons are withheld and also
  takes a season with a finished match without player statistics as withheld; the review of the
  first version found it):
  assert_mart_leaderboards_every_home_board_has_a_leader (an elite league's current season with a
  finished match without player statistics is excluded, as a stats_need_research season is) and
  assert_mart_team_leaderboards_difference_ranks_every_team (the difference board must rank every
  team only in a competition-season where it is shown).
  is_current_season (a served column, read by Home's Top teams and Top players): in
  mart_team_leaderboards it is computed before the withhold filter, so a withheld latest season
  never hands the flag to the season before it; in mart_leaderboards it now means the latest
  season of the league with a finished match (from fct_fixture), not the latest season with
  player rows. Measured on prod: CAFCL and CDF flag an older season today (2024 against 2026 and
  2025 against 2026) because their latest season has no player rows; under the new meaning they
  have no current season, so their stale Home boards go, and no other league changes (the
  compiled mart gives one flagged season per league, equal to the latest finished season).
  layer_rules: no model, grain or column is added; marts keep composing from int and core refs
  (check_layer_contract.py).
  deploy_order: the next nightly build (fdp-nightly) rebuilds both marts before the export reads
  them; fewer rows, same columns, so an export between merge and that build only shows the
  previous boards.
  blast_radius: boards withheld per competition-season: team boards of competitions with a team
  missing a value on a metric (measured 21 Nov on prod core: 17 competitions have incomplete team
  statistics, 14 incomplete player statistics; K League 1 201 of 210 finished matches covered, UCL
  147 of 162, CAFCL 50 of 90); Home boards of those competitions; goal-based team boards stay. The
  before and after counts per competition are measured on the MR's ci_mr tables and put in the MR.
  Some withheld boards are withheld because of our own cleaning (half of the blank offsides counts
  were a provider zero in a full line; fixed in #335, merged before this MR), so the counts are
  measured after it; the rest are statistics the provider does not send.

approved_design:
  - home: #127
  - competition: #129
  - statistics: #139

depends_on:
  - none: marts and tests on main alone
shared_files:
  - none: no design, registry, font or chart baseline changes

decisions_taken: >
  The strict rule, every team in the field has a value (so, under R4, every finished match has the
  input), approved in chat, 21 Nov 2026, and its placement in the marts through the withhold filter
  stats_need_research already uses. The rule's two sentences go in the ranking_rules block of
  metric_rules.md, the block the mart descriptions embed, so the reader of a mart sees them; they
  are stated at the top of the MR head and the merge is the approval. No new model, column,
  dependency, run or recurring cost.

  The is_current_season meaning in mart_leaderboards (the latest season with a finished match)
  follows from the same rule: a competition whose latest season is withheld or has no player rows
  shows no Home board of that kind, and the flag never moves to an older season; this is stated
  in the MR head.

decisions_reserved:
  - none: the rule and the page behaviour (a competition losing boards keeps the rest, one losing all has no Statistics tab) are the approved issue text.

done_when:
  - dbt parse and sqlfluff lint of the two marts and the two tests pass (`.venv/Scripts/dbt.exe parse`, `python -m sqlfluff lint <file> --templater jinja --dialect bigquery` from the repo root).
  - On the MR's ci_mr tables, both new singular tests return 0 rows and the existing board tests of the two marts pass.
  - On the ci_mr tables, the CAFCL 2026 team boards of shots on goal, shots on goal against and shots on goal difference are absent and its goals boards remain; the per-competition count of boards withheld matches the 21 Nov table within the changes of the nightly.
  - python scripts/ci_local.py --mr is green on this branch.

amendments: (none)
