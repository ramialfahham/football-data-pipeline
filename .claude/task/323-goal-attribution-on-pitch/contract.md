# Task contract — a goal's scorer and assister were on the pitch at its minute

objective: >
  Issue 323. A goal's added minute is read from the newest fetch that carried one. A goal's scorer
  or assister who was not on the pitch at the goal's minute, on a confirmed or researched line-up,
  is withheld under the provider-error rule of issue 262: flagged and blank in base, the goal and
  the score unchanged, listed by its flag column. Sourced research for the withheld goals goes into
  fixture_goal_corrections.

refs: >
  Issue 323; provider-error rule issue 262; go-live gate issue 290. The 82 goals measured on MR 457.
  Route set by the coordinating session.

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__fixture_events.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_events_checked.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players_from_lineups.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players_checked.sql
  - dbt_project/models/3_core/fct_fixture_player_stats.sql
  - dbt_project/tests/assert_withheld_goal_credits_blank.sql
  - dbt_project/tests/assert_stat_facts_equal_base.sql
  - dbt_project/docs/layering.md
  - docs/data_contract.md
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture_event.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/seeds/fixture_goal_corrections.csv
  - dbt_project/seeds/player_match_cleaning_answer_key.csv
  - dbt_project/tests/assert_goal_attributions_on_the_pitch.sql
  - dbt_project/tests/assert_goal_added_minute_from_newest_fetch.sql
  - dbt_project/tests/assert_result_corrections_applied.sql
  - .claude/task/323-goal-attribution-on-pitch/contract.md
  - .claude/task/323-goal-attribution-on-pitch/review.md
  - .claude/task/323-goal-attribution-on-pitch/review_input.patch

approved_design:
  - none: no page output changes beyond withheld or researched goal names and restored added minutes on match pages

depends_on:
  - none: no open MR (glab mr list returns none); builds on gitlab/main 5db6166e

shared_files:
  - none: no design baseline, chart manifest or chart pin changes

impact_map: >
  writers: base_apif__fixture_events is the only writer of the cleaned match events; the new
  base_apif__fixture_events_checked reads it and base_apif__lineups and is read by
  fct_fixture_event and base_apif__fixture_players_from_lineups. fixture_goal_corrections is read by
  base_apif__fixture_events and base_apif__lineup_sheets.
  downstream: `dbt ls --select base_apif__fixture_events+ --resource-type model` lists 85 models
  (all event, player, team and fixture models to the marts). `dbt ls --select "fct_fixture_event+
  base_apif__fixture_players_from_lineups+" --resource-type model` lists 56, among them
  fct_fixture_event, fct_fixture_player_stats, mart_competition_fixtures, mart_player_fixture_stats,
  mart_leaderboards, mart_player_profile, mart_team_season and the int_player_* / int_team_* metrics.
  layer_rules: the check is cleaning and lives in base. It cannot sit in base_apif__fixture_events
  because base_apif__lineups reads that model's substitutions; the checked model is the first base
  model downstream of both. Core only switches its ref and carries the two flags.
  deploy_order: model and seed changes in one MR, no schema migration; the 04:00 nightly rebuilds
  every model after merge, so nothing breaks between merge and the nightly.
  blast_radius: measured on prod before the build. 588 provider goals in 548 matches get the added
  minute an earlier fetch carried. 28 goals in 28 matches have a scorer (24) or assister (4) off
  the pitch on a checked line-up; one is a sourced correction and stays; the other 27 are withheld
  or researched. The line-up player goals of a team with a withheld scorer become blank under the
  existing goals_need_research rule. Measured again in the MR by comparing ci_mr tables with prod.

decisions_taken: >
  The provider-error rule of issue 262 (approved in chat, 2026-11-15): a provider value that fails
  its check is withheld and listed for research, and a sourced correction makes it live. Reused as
  built for cards, results and team goals: a needs_research flag in base, the value blank, an error
  test that every flagged value is blank. No new mechanism and no recurring cost. A goal from
  fixture_goal_corrections is sourced and is not checked. The new cleaning-rules sentences go in
  only with the text the coordinating session relays as approved. Model names and the check's
  minute reading are engineering calls of the coordinating session.

decisions_reserved:
  - The cleaning-rules wording for the added minute, the on-the-pitch check and its 45'/90' reading,
    sent to the coordinating session before any model edit.
  - 842 goal events whose scorer or assister id is on neither sheet of a checked match (an id
    mismatch, not this check) are reported to the coordinating session, not withheld here.

done_when:
  - assert_goal_attributions_on_the_pitch and assert_goal_added_minute_from_newest_fetch pass in
    data:build:mr, with the full singular suite.
  - assert_players_from_lineups_goals_add_up, assert_mart_competition_fixtures_goals_add_up and
    assert_fixture_events_only_from_latest_fetch pass in data:build:mr.
  - A read-only ci_mr vs prod comparison (under 20 GB) counts the contradictions corrected, withheld
    and still to research, and the goals whose added minute changed.
  - python scripts/ci_local.py --mr is green; the MR pipeline is green.

amendments:
  - 2026-11-16: + dbt_project/tests/assert_result_corrections_applied.sql — authority: the
    provider-error rule of issue 262 (a sourced correction makes a withheld value live); content: a
    goal correction stays needed while a provider goal of its match fails the scorer or assister
    check, so a correction that confirms a withheld attribution is not reported as no longer needed.
  - 2026-11-16: + base_apif__fixture_players_checked.sql, fct_fixture_player_stats.sql,
    assert_withheld_goal_credits_blank.sql, dbt_project/docs/layering.md, docs/data_contract.md —
    authority: the cleaning-rules text approved in chat, 2026-11-16 (a scorer or assister who fails
    the check is withheld); content: review round 1 found that a player with a provider stat line
    kept the goal or assist of a withheld attribution, because base_apif__fixture_players reads the
    unchecked events and base_apif__lineups reads base_apif__fixture_players. A base model
    downstream of both blanks that player's goals or assists in the match, and
    fct_fixture_player_stats reads it; a test covers both player paths. The two docs that name the
    events' readers and fetch rule follow the change.
  - 2026-11-16: + dbt_project/tests/assert_stat_facts_equal_base.sql — authority: the same approved
    text; content: review round 2 found that the test compares fct_fixture_player_stats with
    base_apif__fixture_players, the model before the withhold, so it would fail on every withheld
    stat-line player; it now compares with base_apif__fixture_players_checked, the fact's base.
    int_competition_season__player_stat_corrections keeps counting the cleaning of
    base_apif__fixture_players: a withheld attribution is not a stat correction.
