# Review — claude/323-goal-attribution-on-pitch — 2026-11-16

diff_sha256: 38a237eecb057486502c37956dfa7df0756e7c2f711b707f9ed9a24f2529b0b1

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is in scope_paths; the three amendments are dated, name their authority (the issue 262 rule and the cleaning-rules text approved in chat, 2026-11-16) and state their content.
- The cleaning_rules.md lines match the approved text word for word, appended to the Results bullet; layering.md and data_contract.md follow the model change (round 1 finding, closed).
- No new mechanism or recurring cost: both checked models reuse the needs_research pattern of issue 262; the 842 id-mismatch goals stay reserved and untouched; no page, export or secret change.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: both checked models read only base models and sit downstream of base_apif__lineups, with no cycle; core only switches refs and carries the flags.
- Stat-line path (round 1 finding): base_apif__fixture_players_checked withholds a withheld scorer's goals (own goals excluded) and a withheld assister's assists on goals that count; its columns keep base_apif__fixture_players' order, which fct_fixture_player_stats unions by position (round 2 finding); assert_stat_facts_equal_base compares with it.
- Flag semantics: a flag marks a provider goal that failed the check and awaits research while is_goal holds; assert_result_corrections_applied keeps a correction needed while its match's provider goal fails the check.
- Seed rows: 22 rows in 6 matches, no duplicate keys, each side adds up to the score, sources meet the official / two-site rule.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- The data_contract.md sentence matches base_apif__fixture_events: the newest fetch that carried a goal's added minute wins, only for goals the latest fetch lists, so the shorter-list rule still holds.
- The recovery rests on the append-only raw table, which the diff leaves untouched; no ingestion, registry, raw schema or cost knob changes.

## escalations
(none)
