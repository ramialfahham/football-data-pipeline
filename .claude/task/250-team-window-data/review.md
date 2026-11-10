# Review — claude/250-team-window-data — 2026-11-10

diff_sha256: 04227408f05a243908135b1f608090ce2a14fef9a6acc93d748c2fb591e1b2e9

rounds: 8

rounds_cap_override: round 8 re-checks four depends_on lines CI's data:build:mr asked for in the new rate guard, after a compile error; approved in chat, 2026-11-10

## scope-auditor
VERDICT: PASS
risks_checked:
- The round-8 change is four depends_on lines in assert_team_page_window_rates_inputs_covered.sql, each naming a model the test body already reads; no new file, dependency edge, mechanism, cost or metric.
- No credentials or workflow permissions; no doc describes test dependency declarations, so no doc-sync is due.
- No decision class of section 10 is touched, and no page surface file is in the change.
- Scope, decisions, impact map and approved_design of the cumulative diff stand as passed in round 7.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Every ref() in the rate guard has a depends_on line; the four new lines sit after config() and outside the jinja comment, as in assert_season_rates_inputs_covered.sql.
- assert_team_metrics_follow_catalogue_formula declares every literal ref and the six surface models its dynamic ref reads.
- The change adds comment lines only: no SQL or logic changes, and neither test is weakened (floors of 15 and 100 hold).
- CI built every model and passed 223 of 224 nodes; the read-only comparison of the ci_mr424 tables with prod matches the contract.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Enumerated every ref() on the staged tree: all nine models the rate guard reads have a depends_on line, and all four new ones exist as models.
- The formula recompute's dynamic ref reads six surfaces, all declared; its body refs are declared.
- No other changed test or model hides a ref() inside a conditional: the answer key refs its model unconditionally too, and the pool test has no conditional ref.
- The round-6 and round-7 judgement that these lines were unnecessary was wrong, as CI showed; the fix is correct.

## escalations
(none)
