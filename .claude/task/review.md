# Review — feat/219-home-approved-design — 2026-10-18

diff_sha256: 7fe4c91af122e53c4a41f02d045cd356899d98314cfb35dc8c2937b1929674e5

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL: dbt_project/docs/layering.md:315 said mart_next_matchday is not ordered; round 2 checked the strip-only fix ("nothing is capped in it") and the scope_paths amendment with its authority, no defect.
- Checked every changed file against scope_paths, no file outside it.
- Checked the impact_map: writers, the pasted dbt ls lineage, layer rules, deploy order and blast radius are present; the inner join to competition_order drops no rows.
- Checked §10: the column name and the order key are plan-approved and ruled on #127; no new mechanism, no recurring cost.
- Checked the added SQL, yml and test for credential-shaped content, none.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: the same layering.md:315 line; round 2 checked the row no longer contradicts the mart and no other line in the file calls it unordered, no defect.
- Checked the window over the grouped CTE and the league_code final key: a gapless dense rank with no ties, no defect.
- Checked seed join fan-out: league_code unique in competition_registry, confederation unique in confederations, no extra rows.
- Checked parity with compareCompetitions: UTC day, region_rank, earliest kick-off, league_code, nulls last where the JS sorts them last, no defect.
- Checked downstream readers mart_competition_fixtures, mart_match_days and the export name their columns, so the additive column reaches none of them.
- Checked the singular test recomputes the order from the mart rows and seeds and fails on two orders, a shared order or a wrong place.

## escalations
(none)
