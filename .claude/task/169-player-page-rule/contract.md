# Task contract — the build follows the approved Player-page rule

objective: >
  Issue #169: a player gets a Player page after 3 matches with minutes above 0 this season or last,
  in any competition we hold, club or national team, and nothing else. A national-team edition is
  placed in a season by its last match, not match by match: an edition counts when its last match
  is on or after 1 July of last split-year season, and then every match of the player in it counts.
  The "and a tab" condition goes. A player with no squad place in the nation's current competitions
  but a match in such an edition gets a National team tab that shows those editions.

refs: "#169 (ruling, approved in chat, 2026-11-22); #259 (the rule, approved in chat, 2026-11-06); #136 (the Player page design)"

scope_paths:
  - .claude/task/169-player-page-rule/**
  - dbt_project/models/4_intermediate/shared/int_competition_season__national_editions.sql
  - dbt_project/models/4_intermediate/shared/int_player__page_profile.sql
  - dbt_project/models/4_intermediate/shared/int_player_page__window_seasons.sql
  - dbt_project/models/4_intermediate/shared/int_player_squad_window__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_page.yml
  - dbt_project/models/5_marts/shared/mart_player_window_metrics.sql
  - dbt_project/models/5_marts/shared/mart_player_squad_benchmarks.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/tests/assert_player_has_page.sql
  - dbt_project/tests/assert_player_page_choices_follow_the_rule.sql

impact_map: >
  writers: int_player__page_profile (has_player_page, has_national_team_tab, national_team_sk and
  the new national_tab_basis), int_player_page__window_seasons (the current_competitions rows),
  mart_player_window_metrics (the National team tab's rows) and int_player_squad_window__metrics
  with mart_player_squad_benchmarks (the squad a tab compares against); one new model,
  int_competition_season__national_editions, one row per national competition-season placed this
  season or last.
  downstream: output of `dbt ls --select int_player__page_profile+ --resource-type model --output
  name`, 11 models: int_player__page_profile int_player_page__window_seasons
  int_player_squad_window__metrics int_player_window__metrics mart_player_competition_benchmarks
  mart_player_fixture_stats mart_player_index mart_player_profile mart_player_squad_benchmarks
  mart_player_window_metrics mart_team_momentum_window. The new model is read by the profile and by
  the window seasons only. The export reads mart_player_profile.has_player_page and builds a tab
  from has_national_team_tab, so it and the site need no edit; a row links to a player only when
  the player's page is built.
  layer_rules: intermediate reads core and intermediate only; marts read intermediate and core;
  one model per grain, nothing per competition, no partition_by or cluster_by.
  deploy_order: the nightly rebuilds in order; the new model is built before the two that read it;
  no consumer reads a column that is removed.
  blast_radius: measured read-only on prod, 2026-11-22, with the placing above: 1,142 players gain
  a page (18,617 to 19,759), none lose one. Players with a page, no squad place and at least 1
  counted national match, who get the earned tab: 1,278 (306 gain their page with it, 972 already
  have a page). Squad-place tabs are unchanged. mart_player_index and the position pools gain the 1,142
  players. mart_player_competition_benchmarks reads the window seasons for the competition order,
  so an earned-tab player's counted editions gain page_tab national_team and a competition_order
  there; the benchmark engine and the peer pools are untouched.

approved_design:
  - player: #136

depends_on:
  - none: models on main alone
shared_files:
  - none: no design, registry, font or chart baseline changes

decisions_taken: >
  Ruling on #169 (approved in chat, 2026-11-22): the rule stays the one of #259, "last season" for
  a national team is the competition's season, a player who earns the page through national
  matches has a National team tab with the competitions in which the page was earned, the
  condition "and a tab" goes. Placing an edition by its last match is an engineering reading of
  that ruling, approved in chat, 2026-11-22 (#169). No new run, dependency or recurring cost.

decisions_reserved:
  - none: who gets the earned National team tab was ruled on #169, note 4294939008 (approved in
    chat, 2026-11-22): every player with a page who is in the current squad or played for the
    nation this season or last. 1,278 players without a squad place gain the tab, 972 of them on
    pages that exist today.

done_when:
  - dbt parse and sqlfluff lint of the changed models and tests pass; check_description_hygiene.py and check_layer_contract.py pass.
  - On the MR's ci_mr tables against prod, mart_player_profile differs only by 1,142 players with has_player_page true and by the earned tabs; every squad-place tab is identical.
  - Luis Santamaría Crisanto Peña and S. Ortiz (El Salvador) have has_player_page and has_national_team_tab true, in assert_player_has_page.
  - python scripts/ci_local.py --mr is green and python scripts/merge_ready.py <MR> says ready.

amendments: (none)
