# Review — feat/132-players-to-watch-data — 2026-11-12

diff_sha256: 7131aada5e01a1cb27974d70681997c4bf03639fe2bcb0973b0af6f9536ab5de

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1: every diffed path is in scope_paths; no URL, label, wording, dependency or shipped value changes; ball_actions_per90 reuses its catalogue row and the existing generator path.
- Round 1: decisions_taken against decisions_reserved — the outfield fallback, the awarded-result exclusion, row_number places and the zero exclusion are written out; nothing reserved is decided.
- Round 1: impact_map carries the pasted lineage, the export's select * path and the stopping point at int_player_profile__yoy; additive change, no coverage cut.
- Round 2 (delta, the singular test): the outfield rule and the recounted floor match the mart and the contract; refs only to models the mart already reads; no new mechanism or threshold.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1: layer placement — the metric is generated in the intermediate from the catalogue formula, the floor and ranks sit in the mart beside top_player_rank; no mart-from-mart read.
- Round 1: the generated block matches the catalogue row and the existing rendering; assert_player_metrics_follow_catalogue_formula already covers int_player_season_record's columns.
- Round 1: team_matches is unique per join key, joined on the window row's own season, awarded results excluded as in mart_player_squad_benchmarks; numerator and denominator of the floor share one window.
- Round 2 (delta): the test's outfield rule equals the mart's; the recount from int_legs__team_match equals the mart's count at its grain; neither join fans out.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL, two test-coverage findings: the dim_player goalkeeper fallback was unpinned, and the floor read the mart's own team_matches.
- Round 2: both resolved — the test applies the outfield rule with the dim_player fallback independently, and recounts played matches from int_legs__team_match; a reverted mart would now turn it red.
- Round 1: generated SQL, determinism of the row_number places, build size, deploy order and re-run safety checked, no defect.

## escalations
(none)
