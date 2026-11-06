# Review — feat/256-fill-from-lineups — 2026-11-06

diff_sha256: d8bcba833e999e53a4a57d63c8420a72c15e497cb63c32138fea0a7c1ad28081

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 2 finding: the impact_map now says the export's player log shows filled values while its rows and has_stat_line stay, which agrees with blast_radius.
- match_involvement for filled rows is stated in the contract and agrees with the mart.
- dbt_project/seeds/schema.yml is in scope_paths; the two descriptions carry the CPO-approved text and add no mechanism, metric or label.
- Round 1 and 2 checks stand: every changed file is in scope_paths, documentation matches the new meaning of has_stat_line, the tests are narrowed by is_from_lineups with the filled rows compared against their own base, and metric_rules.md R4 matches done_when.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- assert_stat_facts_equal_base compares the fact in two slices, one per base; has_stat_line is false for filled rows, so mart_team_momentum_window.has_player_stats does not move.
- assert_player_page_windows: Appearances and match_involvement played read the same minutes on the same fact rows, and a blank-minutes row blanks the card, so the check skips it.
- assert_team_goals_equal_players_goals holds on filled matches: player goals and team goals_own come from the same corrected events.
- Seed descriptions match the models and tests that use the seeds; the union column order, the macro and the five inline copies, and the competition-agnostic rule were checked with no defect.

## escalations
- question: the exact text of the descriptions of fixture_goal_corrections and player_match_cleaning_answer_key.
  CPO ANSWER: approved in chat, 2026-11-06, relayed by the coordinating session.
