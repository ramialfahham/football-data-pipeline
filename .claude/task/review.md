# Review — refactor/176-player-match-mart

diff_sha256: e009e9e1fae670cfa8b811916edf5988a5b4460626e7347ced9d4399f37acdce

rounds: 1

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Key set against the deleted mart_player_match_log: every stat-line row survives the full outer join with has_stat_line true and the stats row's team; has_stat_line selects the old key set; assert_mart_player_fixture_stats_keeps_every_stat_line still guards it.
- Value parity: minutes, stat columns, pass accuracy, is_home and the fixture columns use the same expressions; only is_starter, is_substitute and position_code can differ, as contracted.
- W/D/L and opponent derivation equal the old ones on either side, null goals give D in both; opponent left join to dim_team is on a unique key, no fan-out.
- Tests moved with the columns: opponent_team_sk not_null and relationship, result not_null and accepted values, the (player_sk, fixture_sk) grain test.
- The singular formula test loses only the match-log arm; the metric map maps the score pair to the existing ids goals and goals_against.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Match-log payload: the 40 old columns are listed name by name, two aliased back to goals_for and goals_against; the goalkeeper's goals_against is not selected, no key collision.
- Match-stats payload: the seven added columns are in the drop set, a new test pins the resulting row.
- site_v2/src reads no field of either payload; no frontend field is added, removed or changed.
- Docs: site_architecture.md and 03_player_profile.md name the merged mart; no user-visible label introduced.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Export column list matches the deleted mart's final select in name and order; the row filter matches the old inner join.
- Singular test read by hand: match_level still defines every column the final select uses; Jinja and SQL shape unchanged.
- Generated SQL and metric map: only the deleted Surface goes; the map's new rows carry no variant, as the generator computes.
- Pins: 3 flagged lines in 2 files removed (748 to 745, 188 to 186); the docs pin loses the one dated line (4 to 3); nothing added trips a marker.
- Deploy order: CI exports teams and fixtures only; a manual player export before the first build fails closed on an unknown column.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is inside scope_paths; the diff adds only the seven contracted columns and the opponent join.
- Amendments: the two pin files record removals and change no behaviour; the site_architecture.md replacement is the approved exact text, named with its date.
- The §10 decisions (kept name, the score pair, the line-up flags) are in decisions_taken with their approval; the reserved items are untouched.
- Threshold declaration reads honestly: no new mechanism; cost expected to fall, to be measured.

## escalations
(none)
