# Review — fix/player-event-team-side — a player's row and his match events under one team: the squad list decides

diff_sha256: 677547d38f9c10da04d459f7d546eebb513cf8005f358e86dc0b7bd02b6d0290

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: the seven changed files (two base models, base.yml, fct_fixture_event.sql, core.yml, cleaning_rules.md, the new test) and the task artifacts are all in scope_paths; amendments none.
- Section 10: the rule is #189 as approved on 2026-10-03; the rebuild question carries the CPO's answer of 2026-10-04; the readings are declared under the 2026-10-02 delegation; no metric, label, URL or user-visible name is introduced, and resolved_player_team_id is an internal base column.
- Appendix A: own goals stay out of the evidence and the moves; where nothing decides nothing moves and the test fails; base and core SQL only, no consumption-side change.
- Doc-sync: the rule is one cleaning_rules bullet, base.yml documents the new column and the team change, core.yml the re-merge.
- Impact map carries the pasted lineage (54 models, 24 marts) and a read-only prod measurement; no coverage cut; no credential, workflow or permission change; no new mechanism, recurring cost declared with numbers.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: base reads staging and base only, no cycle (base_apif__player_team_season reads only staging; the events model does not read the player model); the rule is decided once and the player model takes it from resolved_player_team_id; no materialisation set.
- Join fan-out: every decision CTE is unique per (fixture, player) and team_names per (fixture, team), so the base grain holds; season and season_year are both int64.
- The player-row team in the events model repeats the player model's override correction; a player with rows under two teams is excluded, matching the collision guard; the player model's coalesce changes nothing when the decision keeps the row's team.
- Own goals excluded from evidence, moves and the test; the test is a singular error with store_failures, failing on undecided cases; no test deleted or loosened.
- fct_fixture_event: the third self-heal clause compares the stored team with base on (fixture, event_index), keeps the merge key and the high-water mark, is self-limiting, and never touches events only the fact holds.
- No catalogue, seed, project-config, consumption or ratio change; descriptions within limits; no decision history in comments. Noted, not a defect: a moved event whose new team has no named event in the match carries a NULL team_name.

## escalations
(none)
