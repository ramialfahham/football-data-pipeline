# Review — feat/match-days-mart — #160 part 1

diff_sha256: f52464c06de2ac72d3c0fcb9edee755b1ae8f715d3d19667379632aa6db301af

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is in scope_paths; the reach, the opening day and the UTC day are attributed to the #130/#131 rulings and #146 reserved, and the SQL implements exactly that; no metric, no product text, no new mechanism (store_failures and unique_combination_of_columns are existing patterns); no export or site change; THRESHOLD DECLARATIONS checked against the SQL; no credential-shaped string. The marts table in layering.md lacks this mart as it lacks mart_competition_fixtures: a pre-existing gap outside scope.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Mart-to-mart refs are allowed and precedented; no ordering or selection pushed to the export or site; no catalogue metric; no hardcoded league; no seed or project config change; fixture_sk unique/not_null/relationships plus a unique (match_day, league_code, day_row_order); the singular test recomputes reach, neighbours and opening day from fct_fixture and int_legs__team_match; is_last_round and mart_next_matchday's rows are disjoint (played vs future-dated unplayed), so nothing double-counts and no past day holds an unplayed fixture; materialisation from the layer config. Noted, not a defect: with no competition having an upcoming fixture there would be no opening day, a state that yields no rows at all.

## escalations
(none)
