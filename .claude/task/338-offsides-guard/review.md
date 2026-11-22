# Review — claude/338-offsides-fresh-76fb24 — 2026-11-22

diff_sha256: 224c9f46ee932c679d290d365bfb4fc219071eb9cb467ebea9f044b0b83f0d86

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 2, whole branch: every changed path is inside scope_paths; the Blank-rule extension is a section 10 rule extension named in decisions_taken and approved by the merge; the split of the players model is a base model of an existing class, declared in decisions_taken; no new run, dependency or recurring cost.
- impact_map now pastes the dbt ls output (87 models from the new model downstream), with layer_rules, deploy_order and the 7 measured team-matches; approved_design none matches a diff with no site or export change.
- Residual risk recorded: the guard reads the player's cleaned offsides, so a blank could turn to 0 where an earlier fetch showed a player offside and a later one corrected it; the done_when comparison on ci_mr tables against prod exposes any such case.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The move of the players model's first half into base_apif__fixture_player_lines, CTE by CTE against the removed lines: moved verbatim, both jinja sets kept, no dangling reference in the remaining model, no dependency cycle.
- max(coalesce(offsides, donated_offsides)) equals the player's final offsides above 0: the only later step fills blanks, and no later step rewrites a positive offsides; the players model keeps its offsides_counted, so it stays row and column identical.
- Keys and fan-out: lines team ids are the ids the players model keeps, the same id space as the guard test; one row per (fixture, team) joins 1:1.
- Every test and seed that recomputes the Blank rule for offsides: the invariant test has no exclusion; assert_base_team_stats_cleaned and assert_fixture_statistics_from_every_fetch exempt a team with a player offside; the other tests are generic comparisons.
- Opponent clause reads the other team's offsides as delivered; disclosed in the contract, no prod team-match shows it.

## escalations
(none)
