# Review — fix/awarded-results

diff_sha256: 916109d8ecdc34a304516f1437e70b90996f0f4d64ea2cfbe867015ba5e45815

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- The diff is the seed, its schema, its test and the contract, all in scope_paths; the three columns, the 9 filled rows and the 44 new rows are covered by decisions_taken; nothing in decisions_reserved is touched (no mart or page reads the new columns, no goal corrections, CAF match 1619054 absent).
- NEW MECHANISM and RECURRING COST none holds against the diff: three columns on an existing seed and one problem kind in its existing test; every source is https, official rows carry at least one URL and match_reports rows two different sites.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- No model changes; base_apif__fixtures_next applies goals, status and winner as before, and the new columns have no reader; every row traced by hand passes award_not_valid, and the 43 newly awarded matches go through the existing AWD handling in int_legs__team_match and the coverage tests.
- The CSV has 79 rows (35 + 44, 42 not played, 1 played, 1 score fix); home and away goals agree with the team order in the notes; the two winner-without-score rows carry 0-0 and awarded_to_team_id as the Bastia-Lyon row does.

## escalations
(none)
