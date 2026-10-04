# Review — docs/metric-map — the metric map: where each catalogue metric can be read in the marts

diff_sha256: 873bdf67b79160759f0aa83681e783372a0b4f5299177b8857101191f3389f8d

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every file in the diff is in scope_paths; amendments are none; the round-2 delta (dead data_tests branch removed, one test added) changes no scope, decision or contract line.
- Section 10 classes: the table name, marts-only scope, long-format rows, the five added metrics and the 20 questions are quoted from the CPO's answers of 2026-10-04; the variant tokens, the window column and the metric-column rule are declared readings under the 2026-10-02 delegation.
- Reserved: no catalogue row, id, label or formula changes; the only SQL edits add five pass-through select columns; fct_fixture_team_stats and int_legs__team_match are untouched.
- Thresholds: no new mechanism (generated seed with a drift check, the competition_registry.csv pattern); recurring cost declared with a number (about 50 MB a night of seed tests, five integer columns).
- Impact map present with writers, downstream lineage, layer rules, deploy order and blast radius; no coverage cut; no credential, workflow or permission change; docs/metric_layer.md updated in step.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: the five new mart columns pass through from int_team_season__metrics and int_player_season__metrics, where they exist; no new ref, no mart logic, no partition_by or cluster_by.
- Impact map: mart_team_profile and mart_team_season_insights read mart_team_season by named columns, so the new columns do not reach them; export_site_data.py reads mart_player_profile with select *, as declared.
- Removed blocks (latest_rank and four season-total blocks) have no remaining doc() reader; their replacements exist in metric_columns.md; the five __team_match blocks are hand-written and correctly ignored by the map.
- The seed is documented, carries not_null on its key, uniqueness and a relationship to metric_catalogue, and follows the full_refresh precedent; descriptions are under the column limit.
- All 20 questions traced by hand to a map row; the window filters are accepted values; no competition identifier in SQL, YAML or generator; no metric created or redefined.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Both outputs render inside one try, so an Abort writes nothing; a run interrupted between writes is repaired by the next run; --check sits in validate:governance and fails closed on a missing file, drift, an uncovered metric or an unreadable long-format mart.
- tests/test_metric_map.py pins every changed branch: row selection, marts-only, derived blocks, window column, long-format rows and value columns, the three refusals, drift in both directions and the committed map against the generator and the 20 questions.
- Round 2: the data_tests fallback is gone (dead under the dbt 1.7 pin; a data_tests mart would now hit the pins-no-accepted_values Abort, failing closed); the new test pins the rows-match-bytes-differ message.
- No dependency, credential, workflow, hook or build change; no dangling doc() reference.

## escalations
(none)
