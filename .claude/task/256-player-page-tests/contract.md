# Task contract — Player page: value tests for the values #256 serves without one

objective: >
  Issue 256. The Player page's values are served and merged (MRs 382, 388, 390), and the
  hand-worked answer key covers the five new metrics. Six checklist lines have no value test:
  the header (age, season label, full name, current club), the featured season's latest-match
  tie-break, a nation's current competitions, the tab flags, the position count and filter order,
  the Squad's count, median and rank, and the last-season minutes of the cards. This adds
  hand-worked cases for real players and squads in seasons that are over, in one new seed, and two
  singular tests that recompute each rule for every player, so a wrong value fails a build. It
  changes no model; a wrong value a test finds is reported, and fixed here only when the fix is
  inside the #256 checklist.

refs: >
  Issue 256 (the checklist, "Quality: every new metric value has a value test"); design 136;
  coordinating session's audit of 20 Nov (256-checklist-audit.md in the shared notes). Pattern:
  player_season_answer_key and assert_player_season_answer_key.

scope_paths:
  - .claude/task/256-player-page-tests/contract.md
  - .claude/task/256-player-page-tests/review.md
  - .claude/task/256-player-page-tests/review_input.patch
  - dbt_project/seeds/player_page_answer_key.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_player_page_answer_key.sql
  - dbt_project/tests/assert_player_page_choices_follow_the_rule.sql
  - dbt_project/tests/assert_player_page_blocks_follow_the_rule.sql

approved_design:
  - none: no page output changes; one seed and three tests are added and no model or export changes

depends_on:
  - none: reads models already on main

shared_files:
  - none: no design baseline, chart manifest or chart pin changes

impact_map: >
  Leaf change: no model, macro or export is edited. writers: nothing writes the new seed except
  `dbt seed`. downstream: the seed and the three singular tests are read by nothing;
  `dbt ls --select "mart_player_profile+ mart_player_window_metrics+ mart_player_competition_benchmarks+
  mart_player_squad_benchmarks+ int_player__page_profile+ int_team__current_national_competitions+"
  --resource-type model --output name` (main 5544c8b0) returns only int_player__page_profile
  int_player_page__window_seasons int_player_squad_window__metrics int_player_window__metrics
  int_team__current_national_competitions mart_player_competition_benchmarks mart_player_fixture_stats
  mart_player_index mart_player_profile mart_player_squad_benchmarks mart_player_window_metrics
  mart_team_momentum_window, the models the tests read. layer_rules: check_layer_contract has no
  rule for singular tests or seeds beyond the seed description. deploy_order: none; the seed lands
  in the ci_mr dataset in the MR build and in the prod seed dataset on the first nightly after merge,
  and a test that fails on prod data fails the nightly, so every case is checked against prod
  before the push. blast_radius: none for any number; a new failing test on a later data change is
  the intended effect.

decisions_taken: >
  The coordinating session ruled on 20 Nov that hand-worked value tests for the six gaps are inside
  the approved #256 checklist, and set the scope: one MR, answer-key rows plus singular tests, the
  pattern of player_season_answer_key. Cases are real players and squads in seasons that are over,
  so a nightly refresh cannot change an answer: Vercoutre, Matip, Basa, Evra and the player with
  provider id 94 for the header, the featured season and the cards; Bundesliga 2018 for the
  position counts; Nancy 2016/17 for the Squad. The answers are worked out by queries over
  int_legs__player_match, int_legs__team_match and fct_fixture, which are not the models under test,
  and the key says so in its description. Rules that move with the clock (a nation's current
  competitions, the national-team tab) are recomputed for every player in a singular test.

decisions_reserved:
  - none: the tests restate rules already approved on #136 and #256, and the filter order's basis (the
    competition's last match, not the player's) is the model's behaviour and is only pinned, not changed

done_when:
  - "dbt parse from the repo root passes with the new seed and tests"
  - "the three tests return zero rows against the prod datasets, and each case in the key was compared with a query worked without the marts"
  - "python scripts/ci_local.py --mr passes"
  - "the MR pipeline is green and python scripts/merge_ready.py <iid> says ready"

amendments: (none)
