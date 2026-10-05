# Review — docs/team-column-descriptions — team stat columns in core and intermediate describe themselves as team columns

diff_sha256: 65a44638f04fdb6e050b5f2f3794fde2e9e1bf0c413ad8e4b95f22b86b4fc0d0

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every diff file is in scope_paths; no amendment needed.
- Doc references: the five __team_match blocks pointed at exist in shared_columns.md and the four new __team_from_players blocks are added in the same file; no doc() reference dangles.
- Section 10 and Appendix A: no metric, label, format or number; the extension from the issue's 19 columns to 23 is recorded as a reading of the checklist rule "no team model outside the marts", applied to the table the issue's totals come from.
- Impact map: descriptions only, no .sql change, the five affected tables named; no threshold crossed; no secret, workflow or escalations.log change.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The 17 statistics-line columns: each of the five models' SQL passes the team's own cleaned line through at one row per team-match, so the __team_match blocks are true; no window sum is hidden.
- The four new __team_from_players blocks and the duels repoints: int_legs__team_from_players sums them over player legs per team-match and int_team_season_record joins them; "this team's players ... summed over its players" is accurate, dribbles being attempts.
- Sweep completeness: every remaining player doc reference in core and intermediate sits on a player-grained model; 23 repointed, matching the contract.
- Catalogue governance: no catalogue row or generated block touched; the new suffix does not collide with the __team / __player entity suffixes; each block well under the 1,024-character limit.

## escalations
(none)
