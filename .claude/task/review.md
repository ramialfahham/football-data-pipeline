# Review — fix/241-242-team-page — 2026-11-01

diff_sha256: fb5b4bf173debb7e21cc90797c640e6485934fd5beee321221246f005afc3f27

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL: 02_team_profile.md still listed `league_median` for the strip plot, and metrics_display.md (LOCKED) mentions a median mark. Round 2: 02_team_profile.md drops the field strip-only and is in scope_paths; metrics_display.md stays unchanged by CPO ruling, its median mark describing the player bar; both recorded in amendments, approved in chat, 2026-11-01. Resolved.
- Every file in the diff is in scope_paths; approved_design names team, competition and home, which cover the changed output.
- The edge-case label placement and the built-pages check rule are recorded as CPO approvals; no silent product decision, no new mechanism, dependency or recurring cost; no secrets.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: on Borussia Mönchengladbach's narrow chart the y axis line ran through the difference label's minus sign. Round 2: the label moves under the name where it would reach the axis; the evidence shows 3 of 204 charts use it, every label box clear of the axis and of the name, inside the chart. Resolved.
- Binding rule: the strip plot no longer reads `league_median`; only rank and value render, no field is invented, null rank still shows the dash, no naked percentage.
- The five explainers and the removed `teamLeagueMedian` match the approved texts; the spec and block_standard.md follow; the delta adds no user-visible string.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: no test pinned the scatter label placement. Round 2: check-built-pages.mjs rule 5 accepts only the label across the dot from the name or at least one line under it, is wired into main, fails closed on missing marks, and `servesScatter` stops it passing on zero charts; the tests fail the old beside-the-name placement, including through main. Resolved.
- The rank regex reads the text before `<small>`, matching the new rank-first markup; the old layout or a missing rank fails.
- No dependency, credential, workflow, hosting or build-size change; the new functions are pure or read-only and the main test cleans its temp tree.

## escalations
(none)
