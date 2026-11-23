# Review - claude/262-null-keys-mr1-6d92d9

diff_sha256: 44d2eaa1684d3dce18f9cf3aa12ab559302f65908f2fdac890209e0350791278

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL on three contract statements: the claim that the nightly no longer stops overreached the not_null tests, the impact_map had no dbt ls evidence, and the recurring cost of the new model and test was not recorded. Round 2 PASS: the title and blast_radius name only the not_null tests, the impact_map carries the dbt ls counts, and recurring_cost records 106 MB per build and 260 MB at most per test run.
- Round 3 PASS: the contract names the owners of the staging uniqueness residual, and the three policy sentences except stg_apif__fixture_players, which keeps its three not_null tests. Each sentence matches the code on this branch.
- Every changed path is in scope_paths, tests/test_lineup_ties_wiring.py included; amendments is none and none is needed.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: tests/test_lineup_ties_wiring.py pinned two strings this change moves. Round 2 PASS: both pins follow the new union branch and the new accepted value; the listing rule follows base's own selection (statistics by the teams that have the stat from a line with a team id in any fetch after the same override mapping, line-ups by the sheets base_apif__lineup_sheets serves), traced against the base models.
- Round 3 PASS: the three policy sentences were compared one by one with base.yml, the base filters and the staging yml, and are true; stg_apif__fixture_players keeps not_null on fixture_id, team_id and player_id.
- Every singular test and macro that reads a moved staging model was counted against a fresh grep and carries the filter base applies or compares strings only.
- Residual, not a defect: the staging order-keys uniqueness tests can still fail on two NULL-key rows, as the contract states and assigns to its owners.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: the stale pins in test_lineup_ties_wiring.py, two of three override joins of the macro not exercised by the answer key, guard gaps in the moved-tests pin. Round 2 PASS: the answer key has a reattribute_in_fixture and a reattribute_if_cohabiting case, mutation-checked on BigQuery; all four override join lines are text-pinned; macros are scanned and reads are counted per pinned file.
- Round 3 PASS: the pin for the three policy sentences matches the file text and goes red when a sentence or the fixture_id not_null of stg_apif__fixture_players changes; the doc sentence-length and no-decision-history ratchets are not moved.
- Residual, not a defect: the pin checks not_null on fixture_id of stg_apif__fixture_players only; assert_names_carry_no_html_entity reads moved models through a loop no regex sees and compares strings only.

## escalations
(none)
