# Review — feat/256-lineup-research

diff_sha256: 64f37727e5813f1685d23ef8e47bd0bb51ccb77622b0828564a25f4b6782528a

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 escalated whether the stop of 2026-11-06 covers the 17 matches read from uefa.com and resultados.rfef.es; #176 note 4181862000 (approved in chat, 2026-11-07) lets them in, makes no new reads, and keeps the leagues' permission and the legal check open for them.
- The diff holds only the contract and the seed, both in scope_paths, and the task artifacts.
- The reworded notes of 1589428 and 1607628 match the contract's rule on formations and positions; no new rule.
- No new mechanism and no recurring cost; no secrets; no page or export touched; the Line-ups rule already covers researched sheets.
- The reserved decisions stay undecided: the four matches left out, the resumption of research, the permission and legal check, the Sevilla and N. Pinto cards.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The seed hunk adds 1,089 rows and removes none; every row has the seed's shape, one https official source and a note.
- 52 team sheets with eleven starters each; no starter with a minute on; no repeated player id within a match.
- All 253 substitutions pair with a player on the same sheet at a matching minute off, extra minutes and chains included.
- One formation per team; the 85 reworded notes end alike and no other field or row moved.
- Researched sheets feed base_apif__fixture_players_from_lineups, fct_fixture_player_stats and the marts as the contract's blast radius says; int_legs__team_from_players filters is_from_lineups, so team totals do not move.

## escalations
scope-auditor, round 1: the 17 matches read from uefa.com and resultados.rfef.es.
CPO ANSWER: all 26 go in, #176 note 4181862000, approved in chat, 2026-11-07.
