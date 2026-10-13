# Task contract — a window of one played match on the Form comparison's mart

objective: >
  The Form comparison's mart serves each played match as a window of one: for every played
  fixture, each side gets one row with window_type match, the same columns, catalogue formulas,
  coverage gates and directions as the form windows, so the played match page can show each
  team's numbers in that match. The mart is renamed mart_team_momentum to
  mart_team_window_metrics and its key upcoming_fixture_sk to fixture_sk. Every existing form
  window row and value, and every existing page and payload, stays the same.

refs: >
  #176 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/176), the line
  "The Form comparison's mart serves one match as a window of one". The name
  mart_team_window_metrics with the key fixture_sk, the plan, and the four core-document texts
  in decisions_taken: approved in chat, 2026-10-13. The page it feeds is #175, its design
  approved on #132.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_team_momentum_window.sql
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_player_momentum__metrics.sql
  - dbt_project/models/4_intermediate/world_championship/wc/int_wc.yml
  - dbt_project/models/5_marts/shared/mart_team_momentum.sql
  - dbt_project/models/5_marts/shared/mart_team_window_metrics.sql
  - dbt_project/models/5_marts/shared/mart_team_momentum_window.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/5_marts/domestic_league/mart_matchday_insights.sql
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/docs/metric_rules.md
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/seeds/metric_map.csv
  - dbt_project/tests/assert_form_window_rates_inputs_covered.sql
  - dbt_project/tests/assert_momentum_awarded_matches_do_not_null_team_stats.sql
  - dbt_project/tests/assert_momentum_window_matches_momentum.sql
  - dbt_project/tests/assert_one_form_window_per_side.sql
  - dbt_project/tests/assert_player_momentum_window_matches_team.sql
  - dbt_project/tests/assert_team_metrics_follow_catalogue_formula.sql
  - dbt_project/tests/assert_tournament_form_window.sql
  - dbt_project/tests/assert_team_form_window_follows_the_rule.sql
  - dbt_project/tests/assert_player_metrics_follow_catalogue_formula.sql
  - dbt_project/tests/assert_match_window_covers_every_played_match.sql
  - dbt_project/docs/layering.md
  - scripts/export_site_data.py
  - scripts/generate_metric_sql.py
  - scripts/sync_metric_docs_blocks.py
  - scripts/declare_missing_columns.py
  - tests/test_export_site_data.py
  - tests/test_metric_map.py
  - tests/test_metric_rows.py
  - tests/test_no_decision_history_in_code.py
  - tests/test_no_decision_history_in_docs.py
  - tests/test_sentence_length_in_docs.py
  - site_v2/src/specs/competition/matches/fixture.spec.json
  - site_v2/src/data/README.md
  - .gitignore
  - docs/metrics_context_model.md
  - docs/site_architecture.md
  - docs/content_architecture.md
  - docs/wireframes/01_fixture_page.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: dbt builds int_team_momentum_window from fct_fixture, the competition registry and
  types seeds, and int_legs__team_match; int_team_momentum__metrics aggregates it; the mart reads
  that. No ingestion writer.
  downstream: dbt ls --select int_team_momentum_window+ (dbt 1.7.20, on the branch's base)
  returns the models int_player_momentum__metrics, int_team_momentum__metrics,
  int_team_momentum_window, mart_matchday_insights, mart_player_momentum, mart_team_momentum,
  mart_team_momentum_window and the singular tests assert_form_window_rates_inputs_covered,
  assert_momentum_awarded_matches_do_not_null_team_stats, assert_momentum_window_matches_momentum,
  assert_one_form_window_per_side, assert_player_metrics_follow_catalogue_formula,
  assert_player_momentum_window_matches_team, assert_team_form_window_follows_the_rule,
  assert_team_metrics_follow_catalogue_formula, assert_tournament_form_window. Outside dbt:
  scripts/export_site_data.py (fetch_fixture_payloads, fetch_metric_rows),
  scripts/generate_metric_sql.py, metric_map.csv (generated), the Python tests,
  site_v2/src/specs/competition/matches/fixture.spec.json.
  layer_rules: selection stays in int_team_momentum_window, aggregation in the generated
  int_team_momentum__metrics; no new model beyond the renamed mart; check_layer_contract unchanged.
  deploy_order: the renamed mart builds in data:build:mr and in the first build on main. The
  committed fixture samples are not re-exported; the CI export reads the renamed mart only after
  that build. The old prod table marts.mart_team_momentum stays until the CPO drops it.
  blast_radius: int_team_momentum_window and int_team_momentum__metrics gain two rows per played
  fixture (window_type match); the player builder and the form list filter them out, so
  mart_player_momentum and mart_team_momentum_window are unchanged; mart_matchday_insights joins
  upcoming fixtures only and is unchanged; the fixture payload keeps its keys and values.

acceptance_criteria:
  - Every committed sample payload under site_v2/src/data is byte-identical to main's; git diff gitlab/main -- site_v2/src/data lists only README.md.
  - The built site's every page has the same text on the branch as on main, compared by script over the built output.
  - The fixture payload the export shapes from a form row carries the same keys as before; a unit test shows it.

decisions_taken: >
  The name mart_team_window_metrics, the key fixture_sk, the intermediates keeping their names and
  upcoming_fixture_sk as their key, is_form_window false on match rows, and these exact
  core-document texts: approved in chat, 2026-10-13.
  docs/metrics_context_model.md section 5, a new bullet after Form window: "- **Match window.** It
  holds one played match, for that match's own page. Its `window_type` is `match`, and the same
  formulas apply to a window of one." Section 6: mart_team_momentum becomes
  mart_team_window_metrics. docs/site_architecture.md Fixture page row and
  docs/content_architecture.md Matchup row: mart_team_momentum becomes mart_team_window_metrics.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; one more window type through the existing
  selection and the generated formulas. RECURRING COST: rises, two rows per played fixture through
  the window selection and the aggregate in every build; measured before and after and put to the
  CPO in GiB.

decisions_reserved:
  - Dropping the orphaned prod table marts.mart_team_momentum after merge.
  - Renaming the intermediates and their key upcoming_fixture_sk.
  - mart_leaderboards' window of one and removing mart_team_fixture_stats: later lines of #176.

done_when:
  - dbt parse passes; dbt compile of the changed models passes; sqlfluff lint of the changed models is clean.
  - generate_metric_sql.py --check and sync_metric_docs_blocks.py --check pass; the full pytest suite passes.
  - data:build:mr is green, its tests included.
  - On prod data the renamed mart's form rows equal prod mart_team_momentum in every key and column; the match rows number two per played fixture.
  - The acceptance criteria are shown in acceptance_evidence.md.
  - The warehouse read before and after is measured and put to the CPO.

amendments: >
  After review round 1, approved in chat, 2026-10-13, as exact text:
  (1) docs/content_architecture.md, the Performance / Form (recent) row: mart_team_momentum
  becomes mart_team_window_metrics, nothing else.
  (2) docs/metrics_context_model.md section 8.4: the list of window kinds gains the last bullet
  "- one played match, for its own page." and its window_type table gains the row
  "| Match window | `match` |".
  (3) dbt_project/docs/layering.md mart inventory row: "| `mart_team_window_metrics` |
  (fixture_sk, team_sk) | A team's metrics over a window, for the match whose page shows them:
  its form before an upcoming match, the match alone once played. |"
  (4) the window_type__form doc block in dbt_project/models/docs/metric_rules.md gains:
  "`match`: the fixture itself, once played; the window of one on that match's page. The player
  tables and the form list leave it out." This corrects the first approved wording, which said
  `match` was on mart_team_window_metrics only although its two intermediates carry it too:
  approved in chat, 2026-10-13, after review round 2.
  Added tests/test_sentence_length_in_docs.py to scope_paths: the two README sentences that named
  the old mart were over the length limit and are now split, so the file's pin goes down. No
  behaviour changes.
