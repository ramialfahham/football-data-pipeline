# Review — claude/262-withhold-provider-checks — 2026-11-15

diff_sha256: fd1994adebee834cc90ac7a8c6a753f1d82b678bded87042f6247560eb405d68

rounds: 5

rounds_cap_override: approved in chat, 2026-11-15; round 4 is a lint-only fix after round 3 (CI sqlfluff LT02 indentation in mart_leaderboards.sql), no logic change; round 5 is the merge of main after !446, so the MR's data build includes it, with no change to this MR's own content.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file lies inside scope_paths, the staging README and the four adjusted tests included; decisions_reserved is untouched.
- Routes (1) to (11) match decisions_taken under the coordinating session's rulings of 2026-11-15; the 8% limit and the 72-hour window move unchanged.
- No test is weakened. Each provider check becomes "every flagged value is withheld", error severity, named cases kept. Tests that compare an independent set with a board excuse only a flagged competition-season.
- No new mechanism beyond the cards pattern; the new staging read over RAW_APIF_TEAMS (about 0.24 GB a night) was ruled in.
- impact_map pastes the dbt ls lineage, models and singular tests.
- Decision (10) narrows the board withhold to rankings and is listed in the MR head for the CPO's merge.
- Round 4: the one mart_leaderboards.sql hunk reflows the season-rows filter; same tokens, whitespace only.
- Round 5: after the merge of main, every file is in scope_paths and no !446 line shows as a change of this MR; cleaning_rules.md holds both MRs' lines, current behaviour only.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Each flag equals the old failing condition: goals (team scored, goals do not add up), standings (league kind beside group or conference sections), country (blank, or changed after country_name_overrides with no correction row), stats (share over 8% on final matches).
- Positional unions: fct_fixture_player_stats and assert_player_match_cleaning_answer_key drop goals_need_research.
- is_current_season is computed in ranked before the withheld season leaves the board; a league whose latest season is withheld has no current season, and the tests excuse only that case.
- NOT IN subqueries filter NULLs; season_sk is not null where flagged and related to dim_competition_season.
- Slugs anchor on the raw country, so a withheld country moves no URL; mart_team_index already handles NULL countries.
- Standings readers: mart_standings and the two team-season models drop flagged sections; the standings tests that start from fct_standings or the mart stay consistent.
- Staging is a plain unnest; layer placement holds; descriptions are within limits.
- Round 4: the season-rows filter is unchanged in logic after the reflow; the dbt-templater lint of the 22 changed model files is clean.
- Round 5: the five shared files hold both MRs' blocks once each; a withheld result never reaches goals_need_research, the goals test or the squad windows, because the line-up model and both leg models already drop a match with no score.

## escalations
(none)
