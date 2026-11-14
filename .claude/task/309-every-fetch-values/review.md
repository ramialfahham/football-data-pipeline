# Review — claude/309-every-fetch-values — 2026-11-14

diff_sha256: 8fbb9876f64c78ddc117f4e90195bad8873b6fb83ae688ceee01eb561be6c9c7

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every patch file is in scope_paths; amendments are none.
- The impact_map names writers, the dbt ls lineage commands, layer rules, deploy order and blast radius; the change fills values and narrows no coverage.
- decisions_taken against the SQL: every implemented rule is recorded, and the three answer-key changes are named with their fixtures. decisions_reserved decides nothing.
- No new mechanism, no recurring cost; the read size is stated.
- Docs describing the base behaviour (base.yml, cleaning_rules.md, data_contract.md) move with the code; no page surface is touched.
- Round 2 delta: the data_contract.md pointers to the Fetches line and the player model's header step 0 add no rule or decision.
- Round 3 delta: the amendment names its authority and date and adds exactly the three changed paths; the widened did_something in assert_base_player_stats_cleaned fits the existing blank-rule exemption; the team test change is comment-only; the sentence pin is lowered, not loosened.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: base reads staging, base and seeds only; base_apif__fixture_players to base_apif__fixture_statistics to base_apif__fixture_events has no cycle; materialisation unchanged.
- No competition identifier in changed logic; no metric created or redefined.
- Grain unchanged on all three models; joins in the players chain are unique per fixture and player, so no fan-out.
- Events rule fires only when the picked value differs from the events and another fetch equals them; donors must match post-events results; result columns are never donated; the shots fill compares the same team-match set; accurate passes need the same form.
- Existing tests assert_base_player_stats_cleaned, assert_base_team_stats_cleaned and assert_fixture_players_from_a_complete_fetch keep their meaning.
- Round 2 delta: the header comment and data_contract.md wording match the code; no SQL changed.
- Round 3 delta: the 3 MR-build failures of assert_base_player_stats_cleaned are substitutes whose only positive values come from another fetch, whose minutes the blank rule keeps blank; the test now counts a positive base-row value or a correction's provider value as having played. Traced: every positive base value comes from a delivered stat, so the exemption cannot cover a player with no evidence of play. Team test header is comment-only.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: the data_contract.md sentence for team stats stated the newest-fetch rule without the card-count check, and the player sentence covered blanks only. Round 2 points both sentences to the cleaning rules' Fetches line; checked against the delivered, decided, donors and donated CTEs, resolved.
- Coaches loader appends (append=True), matching the RAW_APIF_COACHES row; the base premise that raw keeps every fetch holds.
- No other data_contract.md statement still describes the old latest-fetch behaviour for these models; no ingestion, registry, raw schema or cost change.
- Round 3: no change in docs/data_contract.md or any ingestion path since round 2.

## platform-reviewer
VERDICT: PASS
risks_checked:
- tests/test_sentence_length_in_docs.py: the docs/data_contract.md pin 31 to 30 traced by hand against sentence_length_gate.py; the rewritten paragraph loses one sentence over 25 words, so 30 is exact in both directions.
- cleaning_rules.md stays at its pin of 5: every added sentence is at most 21 words.
- No dependency, workflow, hook, script, build or credential change in the diff.

## escalations
(none)
