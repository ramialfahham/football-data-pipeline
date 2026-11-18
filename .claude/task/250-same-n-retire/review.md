# Review — claude/250-same-n-retire-a5a4d0 — 2026-11-18

diff_sha256: 65c78e897ec9137c1e678fc10ed892b178c5fe86654677464a19deedadcfb4fc

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1: every path in the patch is in scope_paths; the R6 text, the content_architecture,
  metrics_context_model and ui_design_brief edits, the points_rank removal and the player chain are
  each tied in refs to a dated approval; no metric, label, URL or format is decided beyond them.
- Round 1: the gen_team_mock.py explainer follows #250 note 4254003834 as decisions_taken names; the
  test_metric_map.py questions re-point at existing marts; site_v2 is untouched.
- Round 1: the impact_map pastes the dbt ls lineage for both yoy models and the benchmark long
  model; no new mechanism, dependency or recurring cost; the nightly reads less.
- Round 2 (delta): the seven paths added to scope_paths each have a dated amendment with a named
  authority; the layering.md edit is strip-only; the schema.yml variant description matches the
  variants metric_map.csv holds.
- Round 3 (delta): tests/test_sentence_length_in_docs.py is in scope_paths with a dated amendment;
  the one pin moves down only, 15 to 4; no decision class is taken.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL, four findings: stale descriptions in int_competition_benchmarks.yml and
  shared.yml (mart_team_profile), the layering.md mart row, and five comments or descriptions
  naming the deleted year-over-year consumer.
- Round 2 (delta): each of the four findings checked at its location and fixed; the round_order
  block and the metric_map variant description match the data; no compiled SQL, grain or test changes.
- Round 1: layer placement is pure deletion; the retained models (int_team_season__metrics_cumulative,
  int_team_season__table_by_time, int_player_season_record, int_team_season_record) still have readers.
- Round 1: no doc() reference to a removed block and no test or macro on a removed column remains;
  no test was weakened on a surviving column; points_rank appears nowhere else.
- Round 1: MIN_DERIVED 3 sits under the real derived count and the floor still fires; the export
  change only drops a key; gen_team_mock.py only looks up and formats served values.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- The only metric_catalogue.csv change is the deletion of the points_rank row; no remaining row is edited.
- The removal is named and dated in contract refs as CPO-approved.
- No remaining reference to the metric: the map row and the doc blocks go in the same diff, and no
  neighbouring row (deserved_rank, deserved_points_gap_rank) reads it.

## platform-reviewer
VERDICT: PASS
risks_checked:
- sync_metric_docs_blocks.py MIN_DERIVED 40 to 3 checked against the derived blocks left in
  metric_columns.md; the abort still fires on a stopped read.
- export_site_data.py: dropping metric_value_prev_season is pinned by the exact-dict test; the
  remaining prev_season reads come from the window marts.
- gen_team_mock.py reads last_season in the shape _team_last_season emits; the existing full-run
  failure is outside this change and is not a CI gate.
- test_metric_map.py questions name real map rows; test_no_decision_history_in_code.py pins match
  the three flagged lines in the two deleted files.
- No hooks, workflows, dependencies, hosting or credentials touched; the build can only shrink.
- Round 3 (delta): the metric_columns.md pin 15 to 4 matches the count the failing run measured;
  the test checks both directions, so a wrong pin fails it; no other pin changed.

## escalations
(none)
