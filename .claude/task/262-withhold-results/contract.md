# Task contract — a match result that fails a result check is withheld, not a stopped build

objective: >
  Issue #262: a match whose result fails a check of the provider's data stops the nightly today,
  and dbt then skips every model below fct_fixture. Under the rule the CPO adopted, such a result
  is withheld instead, the way cards_need_research withholds cards. base_apif__fixtures_next flags
  it (result_needs_research) and blanks its score, shoot-out and winner, and the build goes on.
  The flag runs through fct_fixture to mart_competition_fixtures, where the match is not played. The
  provider-data result tests on fct_fixture become error tests that every flagged result is blank
  and every unflagged one complete. The daily list reads the flag. The MR also carries !442's
  eleven fixture_result_corrections rows for the Coupe de France matches of 14 Nov 2026, unchanged
  (the same blob, reviewed there), and supersedes !442: a branch carries one task folder.

refs: >
  #262 and its What exactly / How as edited for this rule; the CPO adopted it in chat on
  2026-11-15 (approved in chat, 15 Nov 2026), relayed by the coordinating session, which ruled the
  route on 2026-11-15: the cards_need_research pattern, error tests, no warn severity, results only
  in this MR. !442 for the seed rows and their sources.

scope_paths:
  - dbt_project/seeds/fixture_result_corrections.csv
  - dbt_project/models/2_base/api_football/base_apif__fixtures_next.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/shared/int_knockout_ties.sql
  - dbt_project/models/5_marts/shared/mart_competition_fixtures.sql
  - dbt_project/models/5_marts/shared/mart_player_fixture_stats.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/tests/assert_fct_fixture_finished_goals_not_null.sql
  - dbt_project/tests/assert_fct_fixture_goals_plausible.sql
  - dbt_project/tests/assert_result_corrections_applied.sql
  - .claude/task/262-withhold-results/contract.md
  - .claude/task/262-withhold-results/review.md
  - .claude/task/262-withhold-results/review_input.patch

impact_map: >
  writers: base_apif__fixtures_next is written only by dbt from stg_apif__fixtures_next and three
  seeds (fixture_team_id_overrides, fixture_result_corrections, fixture_round_corrections); no
  ingestion code writes it. downstream: `dbt ls --select base_apif__fixtures_next+ --resource-type
  model` lists 94 models, fct_fixture+ 74, mart_competition_fixtures+ 5 (mart_competition_fixtures,
  mart_match_days, mart_player_index, mart_team_competitions, mart_team_index). layer_rules: the
  flag and the blanking are cleaning, so they sit in base; core passes the column; the mart serves
  it; check_layer_contract applies unchanged. deploy_order: models change together in one build; the
  nightly picks them up after merge, and no table outside the build reads the new column.
  blast_radius: only flagged fixtures and the ten fixtures the seed rows correct change. Measured on
  prod 2026-11-15, read-only (2 MB): the flag condition holds for the 11 Coupe de France fixtures of
  14 Nov, and with the seed rows only for 1647990. For it, score, shoot-out and winner become NULL;
  int_legs__team_match already leaves out a finished match with no score, so it counts in no form,
  record, points or season summary, and mart_competition_fixtures serves it as not played.

approved_design:
  - none: no page layout changes; a flagged match is served as not played with result_needs_research true, and the site's "awaiting result" label is a site task of its own

decisions_taken: >
  Ruled by the coordinating session on 2026-11-15. (1) The flag is the exact condition of the
  provider-data result tests it replaces, on the corrected values: a finished match (FT, AET, PEN)
  without both goals or with goals outside 0 to 20 (assert_fct_fixture_finished_goals_not_null,
  assert_fct_fixture_goals_plausible); one shoot-out score without the other
  (fct_fixture_shootout_both_or_neither_and_decided_on_penalties); a PEN match without a shoot-out
  score or with a tied one (not_null on shootout_home, shootout_away and winner_team_sk where PEN,
  and the same expression test). (2) Flagged: goals, shoot-out and winner blank; status, award and
  on-pitch fields stay. (3) Those tests become: not_null where PEN and not flagged; finished-goals
  and plausible-goals on unflagged matches; a new fct_fixture test that a flagged match's goals,
  shoot-out and winner are blank; a mart test that a flagged match is not played.
  assert_result_corrections_applied compares published values only on unflagged matches. Each is
  error severity. (4) Tests of our code stay as they are: winner_follows_the_result, the winner and
  award keys, award_kind, team_goal_split, and assert_result_corrections_applied's seed checks.
  (5) int_knockout_ties counts a leg as played only with both goals, the finished-match rule of
  int_legs__team_match; before, a withheld second leg would leave the tie's summed goals to the
  first leg alone. (6) mart_player_fixture_stats reads fct_fixture by status and keeps every stat
  line, so a withheld match's rows stay; their result is blank instead of falling through to a
  draw, and its not_null test covers the rows with a score. (7) The seed rows are !442's, byte for byte; fixture 1647990's row gives the official 1-1 and no
  shoot-out, so its result is withheld until a source settles the shoot-out.

decisions_reserved:
  - The site's "awaiting result" label in EN, DE and FI, and the export of result_needs_research: a site task, with the CPO's wording.
  - assert_extra_time_goals_counted_in_score: it reads goal events, which are built from base_apif__fixtures_next, so its check cannot sit in base; it stays an error test.
  - The other five provider-data checks (the stat-corrections limit, the unnamed standings section, players_from_lineups goals, team country not_null and unique): the next MR.
  - The shoot-out of fixture 1647990, until fff.fr or two agreeing reports state it.

done_when:
  - dbt parse passes; sqlfluff lint passes on the changed models and tests; the full pytest suite passes.
  - The MR's data build runs every model with no skipped model, and every test passes.
  - In the MR's tables, result_needs_research is true for fixture 1647990 only, its score, shoot-out and winner are blank, and it is not played in mart_competition_fixtures.
  - Compared with prod, the eleven seeded fixtures are the only fct_fixture rows that change.
