# Review — claude/212-subs-starters-5eea63 — 2026-11-16

diff_sha256: 5584690b351f482957e53cd66f3574004c85c673e4c1ed981b5d3af3d99649b2

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is in scope_paths, shared_columns.md included after the contract fix; nothing else is touched.
- The rule reuses the approved Line-ups and researched-sheet rules of cleaning_rules.md and the published is_substitute__fixture wording; no label, metric id, display or catalogue change, no new mechanism or recurring cost.
- The changed season numbers are declared in decisions_taken and blast_radius with measured counts, and the MR comparison is a done_when item.
- done_when now names the D. Ings, Premier League 2019 case the test pins; the round 1 paperwork note is closed.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL (done_when named a different player-season than the test pins) is resolved: contract and test both carry D. Ings, Premier League 2019, 32 starts, 6 substitute appearances, 38 appearances.
- The join to fct_fixture_lineup on (fixture_sk, player_sk) cannot fan out unnoticed: the leg keeps its unique_combination_of_columns test.
- starts plus substitute_appearances still partition appearances exactly, so the int_player_club_season test holds.
- Only int_player_season__metrics and int_player_club_season__metrics read the changed leg columns; no catalogue, seed, project config or export change.
- Intermediate reads core only; no competition identifier in model logic.
- The starts and substitute_appearances descriptions now state the sheet-first rule and stay far below the 1,024-character limit.

## escalations
(none)
