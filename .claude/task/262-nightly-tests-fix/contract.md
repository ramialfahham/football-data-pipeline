# Task contract — two singular tests follow the rules the models already implement

objective: >
  The prod nightly of 2026-11-20 (Cloud Run fdp-nightly) failed on two singular dbt tests and dbt
  skipped 410 downstream nodes, so marts.mart_standings was not rebuilt. Both failures are the
  tests, not the data. (1) assert_mart_leaderboards_match_boards_follow_the_rule recomputes the
  match boards from int_player_match__metrics and does not apply the withheld-season rule
  (stats_need_research) that mart_leaderboards applies under #262, so 104 fixtures of a withheld
  competition-season (CNL 2025) come back as 'only expected'. It now leaves the same seasons out
  of the recomputation. (2) assert_standings_cross_group_rankings hard-codes the provider's name
  of APD 2026's combined table, 'Liga Profesional Argentina'; the provider delivered that name
  from 2026-11-12 to 2026-11-19 and 'Tabla Anual' from 2026-11-20, for the same 30 teams, and
  int_standings__section_kinds already classifies it as a ranking structurally. The test now
  identifies APD 2026's combined table as the section that holds every team of the league-season,
  with no provider label. No model, seed or doc keys on either name.

refs: >
  #262 (leaderboard test, the withhold rule of commit 60c09141; the standings test is named in
  this same contract). Coordinating session routed the task on 2026-11-20. Blocks !491.

scope_paths:
  - dbt_project/tests/assert_mart_leaderboards_match_boards_follow_the_rule.sql
  - dbt_project/tests/assert_standings_cross_group_rankings.sql
  - .claude/task/262-nightly-tests-fix/contract.md
  - .claude/task/262-nightly-tests-fix/review.md
  - .claude/task/262-nightly-tests-fix/review_input.patch

impact_map: >
  writers: none; both files are singular tests (no model, seed or macro changes).
  downstream: a test is a leaf; it has no downstream models. Readers by name: grep for
  'Liga Profesional Argentina' and 'Tabla Anual' over the repo (outside task folders) finds only
  assert_standings_cross_group_rankings.sql.
  layer_rules: tests only; check_layer_contract.py is not touched.
  deploy_order: none; a corrected test only takes effect at the next dbt run of the tests, and the
  nightly stops failing on it.
  blast_radius: no mart or number changes. The leaderboard test stops flagging the withheld
  season; the standings test accepts the provider's current name for the combined table and still
  fails when the combined table is missing or not a ranking.

depends_on:
  - none: tests only; !491 waits on this change, this change needs no open MR's code

shared_files:
  - none: no design baselines or fixtures

decisions_taken: >
  Engineering calls made by the builder, stated in the MR: the leaderboard test reads the withheld
  seasons from int_competition_season__player_stat_corrections exactly as mart_leaderboards does;
  the standings test identifies the combined table by structure (the section that holds every team
  of the league-season), not by a provider label. No new mechanism, no recurring cost. The WC
  'Group Stage' and ACN 'Groups' labels in the same test are not changed. No other test on the
  withholding marts of commit 60c09141 has the gap (read all eleven; the others check mart rows
  against rules, or already exclude withheld seasons).

decisions_reserved:
  - none: no product, metric, naming or display decision; tests only

done_when:
  - dbt parse passes (.venv/Scripts/dbt.exe, repo root, --project-dir dbt_project)
  - sqlfluff lint of both tests is clean (repo root, jinja templater, bigquery dialect)
  - each test's compiled SQL, run read-only against prod after a dry run under 1 GB, returns 0 rows
  - ci_local --job test:python is green
  - merge request pipeline green

amendments: (none)
