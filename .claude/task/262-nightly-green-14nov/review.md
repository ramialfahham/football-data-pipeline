# Review — claude/262-nightly-green-14nov — 2026-11-14

diff_sha256: e6d0b1ccde3aba94efda09b067833a792d5ad3772fda79052f7858368ecdcee8

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- The three changed files (fixture_result_corrections.csv, assert_player_stat_corrections_within_limit.sql, contract.md) all lie inside scope_paths.
- The test reads only ref() of four staging and two base models, no raw table; no new mechanism, hook, library or workflow step, and the run cadence is unchanged.
- The limit stays 0.08 and the severity error; the measured set narrows under the data contract's "Second fetch" rule (coverage.py SECOND_FETCH_DELAY, 3 days), recorded in decisions_taken with the coordinating session's ruling of 2026-11-14, and the named case guards against measuring nothing.
- The exclusion is bounded and measured: 31 matches of 12-14 Nov, none older; the Sep-Oct Nations League blanks stay measured and reserved.
- The seed row for fixture 1647959 uses the match_reports kind with two sites, neither rfef.es; the provider's 2-2 stays and base derives the winner.
- No credentials, no site or export file, no doc whose contract changes; decisions_reserved is untouched.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: a singular test reading stg_ and base_ models has precedent in existing tests; the cleaning stays in base.
- Seed row 1647959 matches its neighbours' shape and passes every branch of assert_result_corrections_applied; base derives the winner from the shoot-out, Valenciennes.
- Same-window rule: the numerator and denominator come from the same filtered player_rows; the exclusion is per fixture.
- The limit (0.08) and the severity (error) are unchanged and nothing is deleted; store_failures is kept and a failure column labels each row.
- Population rule matches second_fetch_due: latest fetch at or after kickoff plus 72 hours, a NULL kickoff or no fetch measured; the latest fetch is the newest raw_ingested_at over the four staging models of the bundle.
- Remaining divergences from coverage.py, non-blocking: a second fetch with all four sections empty is invisible to staging, the exclusion has no time bound, and the 14-day newer-format refetch is not mirrored; none applies to any match on prod today.
- Type safety: raw_ingested_at and kickoff_datetime are TIMESTAMP; season is int64 for the union.
- No catalogue metric, export script, model grain or raw write changes.

## escalations
(none)
