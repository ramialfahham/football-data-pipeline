# Review — feat/player-metric-labels — 2026-11-01

diff_sha256: a802d0f769684fd485d8db109050288281040c686742e3e284937aef2b0e49a5

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is in scope_paths; the wireframe edit carries its own dated amendment.
- The directions, interpretation texts, schema sentence and wireframe edit each carry a recorded approval; decisions_reserved is none.
- The impact map names every reader of the changed cells, including the glossary export, which the deploy does not run and no page reads.
- No chat quotes, dates, issue numbers or decision history in the changed files; approved_design none holds, as no site file changes.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Only direction and interpretation change on the three rows, plus one schema.yml sentence and one wireframe word.
- direction is read in SQL only by the two team marts, filtered to team rows; none of the three is a player benchmark metric, so no served value changes.
- The export's metric rows are team-only, export_metric_definitions_json reads only lower_better, and metrics.json is not in the deploy's export list.
- No test or doc pins the removed text or the old directions; generated metric SQL does not read these cells.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The wireframe row stays correct without "(neutral)"; no other wireframe restates a direction for the three metrics.
- The built Team Squad renders appearances and minutes per appearance as plain text and never reads direction.
- Every direction reader under site_v2/src takes team metric rows; no page reads the glossary export.
- No block, field, sample key or user-visible string is added; the labels stay with the page that first shows them.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Appearances, minutes per appearance and share of team goals are each better when higher, all else equal.
- Each interpretation still matches its formula and holds only its own meaning; the share keeps its position caveat in brackets.
- The direction description now reserves neutral for a narrative gap, which the deserved points rows keep.
- No formula, label, unit or window cell changes; no new or redefined metric.
