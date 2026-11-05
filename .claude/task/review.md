# Review — claude/feat-136-player-data-4a65b7

diff_sha256: a8d363b6627cf5d72a4f1bc95535d733247ad4a30be9f85ba378f5c75f81dd9c

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 failed on doc-sync: the rank change made layering.md and the locked display contract false. Round 2 confirms rank is back to value descending, rank_best_first carries the direction-aware rank, and the layering.md row is updated.
- Every path in the patch is in scope_paths; approved_design none holds, as neither site_v2/src nor the export changes.
- decisions_taken lists the five new rows, the seven key flags and the metric order, and they match the seed diff.
- docs/wireframes/12_player_stats.md still says five ratio metrics; the contract declares it stays because #136 retires it in the tab build.
- No credentials, new mechanism, recurring cost or reserved decision in the diff.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 failed on two findings: the contract quoted no catalogue row, and the rank contract went stale. Both resolved: the contract matches the seed, and rank stays value descending with rank_best_first tested in assert_player_page_windows.
- Layer placement: base refs staging only, no intermediate refs a mart, no competition literal above staging.
- Same-window rule: each ratio's numerator and denominator run over the same window rows under the same completeness gate.
- Rule R4: one macro serves the window, squad and national models, and a competition the player did not play in still counts.
- Grain, relationship and value tests exist on all new models; the formula test covers both new metric surfaces.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- The five new rows checked against pitch meaning, description, formula and direction sibling; name, description and formula agree on each.
- shots_on_goal_player_pct: the numerator is a subset of the denominator on cleaned data.
- metric_order is unique and gapless per player group, and the relative order of the rows already ordered is kept.
- Exactly seven player rows carry is_key_metric true.

## platform-reviewer
VERDICT: PASS
risks_checked:
- generate_metric_sql.py renders in memory before writing and aborts on a missing metric; the drift tests pin the new surfaces.
- The history-comment pin moves from 707 to 704, matching three removed lines; the test still fails on a rise.
- No hook, workflow, requirements or site config in the diff.
- metric_order keeps the passing boards' order that test_catalogue_order pins.

## escalations
(none)
