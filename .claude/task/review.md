# Review — feat/223-filter-bar — 2026-10-23

diff_sha256: 0dd1e5e949b8fca22c72a35afbf95c8c67bb2d9afd0734f556581de9b192037b

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is in scope_paths; approved_design names the two pages whose output changes, and FilterRows renders nowhere else.
- The copy rests on the approved #223 table and the fit rule on its approvals; the two readings are recorded; the shared script and the fit kinds add no dependency or cost.
- Nothing touches the Team or Teams pages kept in decisions_reserved; the block standard is updated in the same branch; both pins only move down.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The bar's choices come only from the entity type and confederation the rows already carry; nothing is computed.
- The two new keys match #223's copy table in EN, DE and FI; every other string is an existing key.
- The hiding rules still cover every value and the sibling order holds; the block-standard rows match the CSS; the evidence covers each criterion.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The bar's listener on its scope runs before the fit script's document listener, so choices are synced before the re-fit; a dropdown change cannot loop.
- The fit result depends only on visible labels and width, so resize passes settle; the dropdown row is measured only once the bar shows it.
- Without the script the buttons show and wrap and still filter; both pin changes are decreases matching the removed lines; no dependency, workflow, deploy or cache change.

## escalations
(none)
