# Review — claude/blank-count-in-full-line — 2026-11-21

diff_sha256: ce6ba68d7642c64f069df11e883c6281bf98f21d40a4dd77a6b0d3aefb9c2d99

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 3, whole branch: the six changed paths are inside scope_paths; the answer-key edit (three offsides_player and three offsides_per90 rows, blank to a number) tightens the check and is the required consequence of the approved cleaning-rule extension, with no tolerance or skip added.
- Decision rights: the extension is a section 10 rule extension named in decisions_taken, approved by the merge with the rule sentence at the top of the MR head; offsides only, with cards, free kicks and passes left out and the reason stated.
- impact_map: 86 models by layer from the pasted dbt ls command, and the player path traced to base_apif__fixture_players.sql lines 757 and 895; approved_design none matches a diff with no site or export change.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 2: the seed arithmetic (630, 0 and 1440 over 698, 431 and 2389 minutes) and every other seed and test that carries offsides; only the six rows were stale.
- The filled CTE reads the team's own raw fouls and possession, not the filled aliases or the opponent's; newest_values is per stat across fetches, so the clause means any fetch carried them.
- The new singular test's full line (cleaned fouls above 0 and possession) is a subset of the model's, so the full-line half cannot fail on correct data; the thin-line half is limited to a thin, blank opponent, which is stated in the test.
- Delta, the player-offside guard (stg_apif__fixture_players read as a per-team maximum): no dependency cycle, no fan-out, a team with no player lines or all-null lines passes as ruled, the two team-match answer-key rows are well formed. Accepted limit: the guard keys on the provider's raw team id, which agrees with the remapped id on today's prod data (one guarded match in both); a test of the cleaned team count against the players' maximum is recommended once measured.

## escalations
(none)
