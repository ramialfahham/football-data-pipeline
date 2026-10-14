# Review — feat/176-match-leaders

diff_sha256: 17188086bfc419b3f4bbeda744445ffdab73c47c77620206d398e00c2a2239f0

rounds: 2

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Season rows keep their select list, window columns, surrogate key and types; the three new columns trail, and the windows run before the union.
- The union's 49 columns line up in order and type; the match null casts coerce with the season types.
- Match boards: DENSE_RANK per fixture across both teams, cut by row_number on count, fewer minutes, player_sk at three, zeros and nulls dropped.
- The new intermediate reads int_legs__player_match only, at its grain, with the generated catalogue formulas; the formula test covers it.
- yml tests split per window; the descriptions now state both grains, both key formulas, and the match minutes.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- No page or payload changes: the three export reads take season rows only, and the export's allow-lists keep the new columns out.
- The new label carries the approved words in EN, DE and FI and is used by no page yet.
- The catalogue's order change keeps every order a page shows: the Rankings and Home boards keep their relative order.
- The match boards follow the approved Match leaders design: seven boards, top three, a shared count sharing the rank, fewer minutes at the cut, no zero.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- fouls_player is the player's own fouls committed, traced to the provider's committed count; formula, name and description agree.
- The description is one plain sentence on cleaned data; the interpretation carries the meaning; each column holds only its own thing.
- Direction lower_better and tier 3 match the team twin and the other discipline counts.
- The order is unique per group and reads naturally: shots, on target, conversion; dribbles, duels, duels won; fouls, yellow, red.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The three export reads carry the season filter; the source-text test fails on a dropped filter or a fourth read.
- The generator surface renders the seven formulas as the model holds them; the metric map adds the three sort_value rows and the window column.
- The sentence-length pin moves by exactly the one long sentence removed from layering.md.
- Deploy order: the CI export reads no leaderboard entity; a manual export before the first build fails closed.
- The acceptance evidence demonstrates each criterion.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope; nothing beyond the objective.
- The fouls_player row, the catalogue order, the label words and the layering.md text match decisions_taken and the amendment exactly.
- The impact_map pastes the dbt ls output (3 models, 20 singular tests); the blast radius states at most 21 rows per match.
- Threshold declarations honest; the cost rise declared, measured on the MR build before merge; reserved decisions untouched.

## escalations
(none)
