# Review — feat/227-chart-theme

diff_sha256: 02435df0d1a1f1867dd79300d6ae049011b8c6e9434e577a934268d12ad619fb

rounds: 6

rounds_cap_override: approved in chat, 2026-11-03: one round, platform-reviewer only, for a test-only fix to the round-3 finding; then two rounds, platform-reviewer only, for the baseline lowered to CI's measurement and the screenshot pins from CI's artifact; then one round, platform-reviewer only, for the scatter label fix the second pipeline's Linux run required.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL closed: .claude/skills/validate-local/SKILL.md is in scope_paths by a recorded amendment and its CI mapping table lists both chart checks under validate:ui, matching the job.
- Every file of the patch is in scope_paths; the pins are in scope and not yet committed, as the contract states for the first pipeline.
- protected_override names the approval for the validate:ui change; the CI diff adds the two checks, their tests, one artifacts path and the new *ui_paths entries only.
- The comparison element's look, green only for the better value, the legend-style team names, no tooltips and the ruled chart rows are each in decisions_taken with their 2026-11-03 approval; the three new mechanisms are declared with no recurring cost; decisions_reserved is closed.
- approved_design names team #134 and match #132, the two changed pages; TeamLastSeason.astro is not touched.
- No secret or widened permission; the new block_standard rows state what each element is, with no history.
- Rounds 3 and 4 changed only scripts/check_chart_screenshots.py and its tests and tests/test_check_chart_components.py, after this verdict.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The built match page renders the comparison as cmp-team, the family group heading and cmp-row with the better value green; group and row order unchanged; the form pills sit under both team names on an upcoming match page.
- Tooltips: the scatter circles' titles and the strip dots' title attributes are gone; only the document head title remains on the built Team page.
- Binding rule: only class names, markup and layout change; every value comes from the same served fields as on main; no data field or sample data added.
- Locked metric contract: comparisonGroups order kept, nonkey only on groups without a key row, nulls still render as the dash, no percentage format change, no metric added or removed.
- Theme tokens resolve on body.fx per theme; the block_standard chart rows match system.css (legend 12px ink-2, tick 11px, name 14px ink, team name 12px 400 ink-2).
- Rounds 2 to 4 changed nothing in site_v2/src or docs/wireframes after this verdict.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAILs closed: only Linux pins are valid on every platform, so a foreign manifest fails; --artifacts writes only on Linux; main() is tested for a changed, missing, foreign, unchanged and off-Linux run and for zero scatter measurements.
- Round 2 FAIL closed: every manifest entry's PNG must exist with its hash and no unnamed PNG may sit in the pins, on every platform; write() removes stale PNGs; each case has a test that fails on revert.
- Round 3 FAIL closed: two tests parse .gitlab-ci.yml and fail if a chart step, its order after the design check, its --artifacts folder in artifacts.paths or its *ui_paths entries go missing; they run in validate:ui and test:python.
- CI fails closed: every new step exits non-zero on a finding or a crash; no allow_failure; the first pipeline fails on the missing pins and keeps a Linux manifest as its artifact.
- Re-run and interruption are safe; no dependency change; no credential; no new page or external request; baseline.json only lowers one width pin.
- Recorded risks, no defect: hash-exact screenshots on shared runners and a mutable image tag could flake; a class written only inside a template literal would not mark a component as a chart.
- Round 5: baseline.json lowers exactly the four counts the MR's first validate:ui run reported as fallen (Match page classes 58 to 45 and split 151 to 148, Played match page classes 51 to 38, Team page classes 87 to 60); nothing else changes, and compare_counts fails any pin off CI's measurement in either direction.
- Round 6: chartMarks.mjs place() searches the label's height in quarter steps over the same range and, under the name, may raise the name only to a height where it meets nothing; the search is bounded, adopts a position only with strictly fewer hits, resets both texts on every call and leaves the built HTML the static checks read unchanged; the Linux failure on de/mannschaften/borussia-monchengladbach at 360px is reproduced with a tall-box font (3 findings) and gone with the change (0).

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL closed: screenshot_verdict fails any manifest not taken on Linux before the platform gate, missing pins fail on Linux, --update off Linux writes nothing; each pinned by a test.
- Guard authority: protected_override and a concrete impact_map cover the validate:ui change; no existing step, rule or allow_failure is removed or loosened.
- New mechanisms: the chart theme and the two checks are declared with their approval; ChartLegend.astro is a component inside the theme; nothing undeclared.
- Dependencies none, credentials none; recurring cost none on the existing self-hosted runner, the added job time disclosed in the impact_map.
- Rounds 3 and 4 changed only the screenshot check and the chart tests, inside this ruling, after this verdict.

## escalations
- question: may the review take a fourth round past the cap of three, for a test-only fix to the round-3 platform finding?
  CPO ANSWER: approved in chat, 2026-11-03, one round, platform-reviewer only.
- question: may the review take two more rounds, platform-reviewer only, for the baseline lowered to CI's measurement and the screenshot pins from CI's artifact?
  CPO ANSWER: approved in chat, 2026-11-03, both rounds, platform-reviewer only.
- question: may the review take one more round, platform-reviewer only, for the scatter label fix the second pipeline's Linux run required?
  CPO ANSWER: approved in chat, 2026-11-03, one more round, platform-reviewer only.
