# Review — claude/nightly-tests-fix-d33f8f — 2026-11-20

diff_sha256: 5201bc3406f34b2718b55c2eec3386a89ddbfc44ff98561700b03900d1482b29

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: the diff touches only the two singular tests and the task's contract, review and patch files, all in scope_paths; no amendments, so no authority to check.
- Decision classes and decisions_reserved: no metric, label, URL, copy, model, seed or number changes; no new mechanism or recurring cost.
- Leaderboard test: its withheld-season predicate is the one mart_leaderboards uses at its two final where clauses, so the test follows the rule and does not extend it; every non-withheld season is still compared.
- Standings test: the hard-coded provider label is replaced by a structural definition, and the test still fails when the combined table is missing or is not a ranking, so coverage is not narrowed.
- Impact map, doc sync, secrets and page surface: tests are leaves; no site_v2, export script, model or workflow path touched.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Leaderboard test mirrors the mart's withhold rule: same predicate and same season_sk source; ranking before or after the filter is identical because the partition is the fixture and a fixture belongs to one season.
- NULL season_sk in NOT IN: the subquery excludes null season_sk, so it cannot poison the NOT IN, and the test and the mart treat null-season rows alike.
- Vacuity of the leaderboard test: a withheld season that still has mart rows appears as served-only rows and fails; assert_player_stat_corrections_within_limit also flags it.
- Combined-table definition: the section holding every APD 2026 team cannot match a 15-team group; two full sections would both have to be rankings, as in the model; a missing or non-ranking combined table fails.
- Vacuity of the standings test: an absent APD 2026 or no section holding every team emits a row through the new missing-table branch; the never-a-ranking branch is exempted only for the combined section. Note: the WC and ACN labels stay hard-coded, as the contract states.

## escalations
(none)
