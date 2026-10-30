# Review — feat/235-team-fixture-order — 2026-10-30

diff_sha256: 7c1265b0f8e33fb47b2c84060acb76bbb397573401a5d914188c99d2a7807691

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: the diff touches only mart_team_fixtures.sql, shared.yml and the task files, all in the contract's scope_paths; amendments are none.
- Decision rights: the two column names carry a dated approval with no quoted words; the ordering mirrors upcoming_rank and recency_rank without competition in the partition; no new metric, label, URL, mechanism or recurring cost.
- Existing numbers: the SQL only appends two columns and the existing rank expressions are untouched; done_when requires the except-distinct comparison against main.
- Impact map: the pasted dbt ls output shows no downstream model; the one outside reader, scripts/export_site_data.py, keeps only _TEAM_FIXTURE_FIELDS, so no payload changes and approved_design none holds.
- Docs and writing: the model header and shared.yml descriptions are updated and state what each column is; no secrets, no escalations.log entry.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: two row_number() windows in a 5_marts model, no new ref, no staging ref; materialisation unchanged.
- Window correctness: both orders are total (kickoff then fixture_sk), the grain (team_sk, fixture_sk) rules out duplicates in a partition, and the case-when guards leave NULL on ineligible rows.
- Tests: four added (null exactly when the flag is false, positive, unique per partition with a where config); none removed or weakened; a null flag passes expression_is_true as it already does for the existing rank test.
- Catalogue and competition-agnostic: ordering keys, not metrics; metric_map unaffected; no hardcoded competition identifier.
- Consumption: the export is unchanged and drops the new columns; the order is computed in the warehouse as layering.md §Consumption layer requires.

## escalations
(none)
