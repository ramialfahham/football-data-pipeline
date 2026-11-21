# Review — claude/256-player-page-tests — 2026-11-21

diff_sha256: 33b6df204dca287e3fa7c78bfbfe76594a35991e30d64a66f84250404b1993b7

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: all seven changed paths are in scope_paths and the contract has no amendments; no defect.
- Decision rights (section 10): no model, export or page output changes, and no test sets a new metric definition, label or format; no defect.
- Appendix A: the seed values are worked from int_legs__player_match, int_legs__team_match and fct_fixture, not the marts under test, and the seed description says so; no defect.
- Impact map: the short form is honest, since no model, macro or export is edited and nothing refs the seed or the tests; no defect.
- Threshold crossings: no new mechanism (the pattern of player_season_answer_key) and no new run cadence, API call or history season; no defect.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Vacuity and circularity: the answer-key test left-joins the key to the actual rows and fails on a missing row; the expected values are worked from int_legs__* and fct_fixture; no defect.
- Seed arithmetic re-derived by hand (19 and 14 appearances, 1294 and 981 minutes, 1120 last-season minutes, floor 1140, median of the 9th and 10th values, tied rank 11); no defect.
- Clock sensitivity of the choices test: nations with a boundary within a day, birthdays today and 29 February births are excluded, and the running rule matches the model; no defect.
- Grain and joins of the blocks test: filter order, squad rank, squad median and the club-tab minutes each fail on a wrong value; no defect.
- Seed conventions (column_types, unique combination, not_null working, description naming its test); no defect.
- Reviewer ran no SQL; the builder ran all three tests against prod with zero failing rows, and negative controls fail as intended.

## escalations
(none)
