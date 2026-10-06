# Review — fix/cleaning-key-cases

diff_sha256: 4127b6c5a2d4b25a74e466cdab57b805157ebeaca0baeb9957f88b6391753410

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Diff touches only contract.md and the two cleaning answer-key seeds, both in scope_paths; the step-1 paths dropped from scope are untouched.
- §10: five data rows in existing seeds; no metric, label, URL, naming, mechanism or rule introduced or extended.
- Team opponent_shots_on_target_unverified has no real case; the contract declares it and the MR head states it, so nothing is hidden.
- No structural path, so no impact_map; no doc needs syncing; no secrets; NEW MECHANISM and RECURRING COST none, consistent with the diff.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Team 1311456/5277: shots_on_target 1 raised to 2 open-play goals (gap 1, raised_to_open_play_goals) and shots 1 raised to 2 (raised_to_shots_on_target, open-play goals not above the cleaned shots on target), checked against base_apif__fixture_statistics.sql and the raw values.
- Player 1451034/169/25926: count 3 plus 1 own goal is 4, not 5, so the events (4 plus the own goal, every scorer with a row) give him 2 goals; shots on target and shots 1 raised to 2 with the labels the model emits.
- Player 1180382/119/50077: the opponent's provider shots on target (0, before team correction) fail the check against 1 open-play goal conceded, so the 2 saves go blank under opponent_shots_on_target_unverified.
- Seed mechanics: column count, blank field, unique keys and populated workings checked; the tests compare expected_value only, so each rule label was checked against the model by hand.

## escalations
(none)
