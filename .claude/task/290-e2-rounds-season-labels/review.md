# Review — claude/290-e2-rounds-season-labels — 2026-11-12

diff_sha256: 7100744fd2b21bedf4a16938a8085a56c96bf04040074eb7a9b20d0678b25529

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths, including int_team_index__round_values.sql and docs/shared_columns.md added in round 2.
- No new mechanism: fixture_round_corrections follows fixture_result_corrections (one row per fixture, a source on every row, applied by left join in base) and extends the existing applied test. No recurring cost.
- The two round labels' EN/DE/FI wording and the UESC one-year ruling are recorded in decisions_taken as approved in chat, 2026-11-12; strings.ts matches the acceptance criteria verbatim.
- blast_radius lists the 44 corrected fixtures and the 18 changed labels; no URL or slug changes.
- Round 2: the two new round-value rows reuse the 0-point preliminary-round value; the impact_map paragraph on the round-values table and the shared doc matches the diff.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The correction is a seed applied in base beside fixture_result_corrections; the label is a seed join in core; no league_code in model logic, no stg ref in core.
- fixture_round_corrections: 32 CAF rows form 16 two-leg ties and 12 UCL rows fall 3 per year; every source is https and the match_reports rows carry two sites, which assert_result_corrections_applied checks with round_checks (not_applied, no_longer_needed).
- The new round_names patterns are anchored and cannot collide with ^preliminary round$; the CAFCL ^2nd preliminary round$ row already names the corrected CAF text.
- The label test checks the label against the map, and the answer-key values agree with the map rows.
- Round 2: int_team_index__round_values carries both new keys at (0, null), so assert_team_index_cup_rounds_scored finds them and mart_team_index gives 0 points, not null; the shared round_name doc names the corrected round; the contract's UESC sentence states the measured anchor effect.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The only site_v2 change is three-language copy for two round keys in strings.ts; no markup, CSS or component change.
- Acceptance criteria 1 and 2: the EN, DE and FI strings match the contract text character for character; criterion 3: roundPreliminaryRound1/2 and both new keys exist in all three languages.
- The binding holds: the keys come from round_names rows that int_round_names serves; the export and site data are untouched.
- Round 2: both new keys have a round value at (0, null) like the other preliminary rounds; a repo-wide sweep finds no other keyed list of round keys.

## escalations
(none)
