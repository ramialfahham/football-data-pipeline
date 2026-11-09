# Review — claude/277-standings-section — 2026-11-09

diff_sha256: e59816ffbd69bc486c85736c041900b4817c86946d427202a2358c792ebc2505

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is inside scope_paths; amendment 1 adds the two existing tests kept in step with the ruled structural rule, citing decisions_taken.
- The impact map carries the pasted 19-model lineage, the readers of the grain change and a measured blast radius.
- No URL, label, metric or format change; the page effect is the existing rule that a cross-group ranking is never shown, applied to two sections.
- No new mechanism or recurring cost; league codes appear only in test fixtures.
- The lineup duplicate stays reserved for #281 and no lineup code changes.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- int_standings__section_kinds is unique on (league_code, season_api_year, group_name), so the three-key joins in mart_standings, int_team_season__table_state and int_team_season__standings_primary stay one to one.
- The team-table rule lives once in int_team_season__standings_primary and mart_team_competitions only selects from it; its order ends on group_name, a total order.
- The stage match handles round names without " - ", a team with no played match and an empty name.
- No cycle: section kinds read only fct_standings, and no intermediate model refs a mart.
- assert_every_standings_section_has_a_table_kind recomputes the structural rule on its own and fails exactly the two reclassified sections on the old kinds.

## escalations
(none)
