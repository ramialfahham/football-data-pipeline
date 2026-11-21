# Task contract — core team-fixture fact and match status decided once in base (#327, MR 1 of 4)

objective: >
  Steps 1-3 of #327. Match status and the round classification are decided once in base and carried
  on fct_fixture. fct_fixture_team_stats becomes the team-per-fixture fact: two rows per fixture of
  every status, with goals_for / goals_against, the result, the opponent's key and the opponent's
  stat values. int_legs__team_match becomes a thin selection over that fact and its output is
  unchanged. No page number changes.
refs: "#327 (steps 1, 2, 3; checkboxes 1, 2 and the first half of 5)"

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__fixtures_next.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_rounds.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture.sql
  - dbt_project/models/3_core/fct_fixture_team_stats.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/shared/int_round_names.sql
  - dbt_project/models/4_intermediate/shared/int_round_names.yml
  - dbt_project/models/4_intermediate/shared/int_legs__team_match.sql
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/docs/layering.md
  - tests/test_no_decision_history_in_code.py
  - dbt_project/tests/assert_stat_facts_equal_base.sql
  - dbt_project/tests/assert_fanout_facts_not_empty.sql
  - dbt_project/tests/assert_fct_fixture_team_stats_covers_active_competition_var.sql
  - dbt_project/tests/assert_team_fixture_rows_reconcile.sql
  - dbt_project/tests/assert_team_stats_team_in_fixture_participants.sql
  - dbt_project/seeds/schema.yml
  - .claude/task/327-team-fixture-status/**

impact_map: >
  writers: base_apif__fixtures_next (adds is_finished, is_played, is_awarded_result, is_shootout,
  round_order from its own status_short and round_name); new base_apif__fixture_rounds (the round
  matching moved verbatim out of int_round_names); fct_fixture (adds those columns and
  round_stage_kind, is_table_shootout); fct_fixture_team_stats (re-grained to every side of every
  fixture, left-joined to base_apif__fixture_statistics); int_legs__team_match (selection over the
  fact); int_round_names (selection over base_apif__fixture_rounds plus is_latest_season).
  downstream: `dbt ls --select <model>+ --resource-type model` from the repo root, run 2026-11-21:
  base_apif__fixtures_next+ = 98 models, 34 marts; fct_fixture_team_stats+ = 66 models, 32 marts;
  int_legs__team_match+ = 65 models, 32 marts; int_round_names+ = 67 models, 32 marts. The readers
  of fct_fixture_team_stats are int_legs__team_match and four tests
  (assert_fct_fixture_team_stats_covers_active_competition_var, assert_fanout_facts_not_empty,
  assert_team_id_aliases_merged, assert_team_stats_team_in_fixture_participants) plus
  assert_stat_facts_equal_base; none selects a column the widening removes.
  layer_rules: check_layer_contract.py: base refs no core, intermediate or mart (the rounds model
  reads base_apif__fixtures_next and the round_names seed only); core refs no stg_* or mart_*
  (fct_fixture_team_stats reads fct_fixture, base_apif__fixture_statistics and nothing else);
  materialisation stays set per layer. fct_fixture_team_stats now reads fct_fixture, a same-layer
  ref the cross-layer consumption rule allows.
  deploy_order: no table is dropped or renamed, only columns added and one fact widened by rows
  whose stat columns are NULL, so the deployed marts keep building against the new tables in the
  same nightly build, in dependency order. int_round_names keeps its columns and grain.
  blast_radius: none for any number on any page. Proof: int_legs__team_match from the MR build
  equals prod's, row for row and column for column, by EXCEPT DISTINCT both ways (query and row
  counts in the MR head); fct_fixture_team_stats has 2 x fixtures-with-both-teams rows, all stat
  totals equal base (assert_stat_facts_equal_base), int_round_names equals prod's the same way.
  RAW evidence, prod 2026-11-21: core.fct_fixture 65,209 fixtures, 0 with a NULL team, every team
  in dim_team across all ten statuses; core.fct_fixture_team_stats 123,250 rows, all on a side of a
  finished fixture; 8 finished fixtures carry no scoreline (withheld, kept out of the legs as now).

depends_on:
  - "!500: it rewrites fct_fixture.sql and edits core.yml; this branch commits those two files after it merges, then rebases on gitlab/main"
shared_files:
  - "none: no design baseline, registry or screenshot fixture is touched"

decisions_taken: >
  #327 direction and its How steps 1-3 approved in chat, 2026-11-18; the issue's What exactly and
  How are the spec. Engineering calls inside it, stated here: (1) the status columns reuse the
  names already in the warehouse (is_finished, is_awarded_result, is_table_shootout_win,
  has_stat_line) plus is_played and is_shootout; (2) is_finished is the status list alone and is
  not the same set as "has a scoreline", so a finished match whose result is withheld stays
  finished and its goals stay NULL; readers that need a scoreline test the goals columns, as
  int_legs__team_match does today; (3) is_played is FT, AET, PEN, the played list the readers
  write out today; (4) the fact carries keys, status, goals, result, stats and the opponent's
  stats; header attributes (kick-off, season, round) are read from fct_fixture by the readers, not
  copied onto the fact; (5) the round_names matching moves into base_apif__fixture_rounds because
  base may not read int_round_names; int_round_names stays as the reader-facing selection;
  (6) the fact keeps the name fct_fixture_team_stats in this MR; the rename to fct_team_fixture is
  an engineering decision (a model name) taken by the coordinating session, one mechanical MR
  after this one and before MR 2; the CI check on status_short literals is likewise decided: a
  pytest pin that only goes down, added in the last reader-move MR once the count is zero;
  (6b) the fct_fixture_team_stats rows of dbt_project/docs/layering.md and fact qualification
  rule 3 change in this MR, with the sentences written at the top of the MR description under
  "Core text for approval"; the merge is the approval;
  (6c) the two tests that count the fact's rows (assert_fanout_facts_not_empty and
  assert_fct_fixture_team_stats_covers_active_competition_var) keep their meaning by counting
  finished sides only, since the fact now also holds unplayed sides;
  (7) rule R3 is not touched: forfeits keep their scoreline and their NULL stat columns in the
  rows, and is_awarded_result stays the column the metric filters read.
  No new dependency, no recurring cost, no new CI check, no change to a protected path.

decisions_reserved:
  - "none: the rename, the status_short pin and the layering.md text are decided as stated in decisions_taken (6) and (6b); this MR adds no other CPO-class question"

done_when:
  - ".venv/Scripts/dbt.exe parse --project-dir dbt_project exits 0 (from the repo root)"
  - "python -m sqlfluff lint on each changed model, from the repo root, with the full rule set, reports nothing new"
  - "python scripts/check_layer_contract.py and python scripts/check_description_hygiene.py exit 0"
  - "python scripts/ci_local.py --mr is green"
  - "in the MR build: int_legs__team_match and int_round_names equal prod by EXCEPT DISTINCT both ways, 0 rows each way, and the row counts match"
  - "in the MR build: assert_team_fixture_rows_reconcile and assert_stat_facts_equal_base return 0 rows"

amendments: >
  (1) assert_team_stats_team_in_fixture_participants joins scope_paths: the fact now builds its team
  rows from the fixture's own participants, so a check of the fact against fct_fixture can no longer
  fail. The test is re-pointed at base_apif__fixture_statistics, the input that can carry a
  mis-attributed team, so the invariant it guards is kept. An engineering edit inside the approved
  #327, found by the round 1 platform review; no new decision class.
  (2) dbt_project/seeds/schema.yml joins scope_paths: the round_names seed description names the
  model that applies the seed, which is now base_apif__fixture_rounds, not int_round_names. One
  sentence is reworded so the persisted description points at the right model; found by the round 2
  warehouse review; no new decision class.
