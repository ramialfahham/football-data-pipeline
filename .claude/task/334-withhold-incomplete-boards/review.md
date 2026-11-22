# Review — claude/334-withhold-boards — 2026-11-22

diff_sha256: 20d1326215a81a2f4eb4b054584808fb3f6b418d865f5794f59717518acff23f

rounds: 4

rounds_cap_override: round 4, scope-auditor, doc delta only — approved in chat, 2026-11-22

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 4, doc delta only: the mart-level sentence and the column description of mart_leaderboards.is_current_season in shared.yml now match the latest_played_season and season_flagged CTEs (the latest season with a finished match; a withheld latest season has no rows, so the flag never moves to the season before it), and no stale wording remains.
- decisions_taken carries the line that the is_current_season meaning follows from the approved rule and is stated in the MR head; decisions_reserved stays none; approved_design names home, competition and statistics.
- Round 3 findings otherwise held: scope paths, thresholds (no new model, column, dependency or recurring cost), the rule sentences in the ranking_rules block of metric_rules.md.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 3: the flag in mart_leaderboards means the latest season of the league with a finished match (one row per league, so the left join cannot fan out; match rows stay NULL), and the team mart computes it before the withhold filter, so a withheld latest season never hands the flag to an earlier one.
- assert_one_current_season_per_league against the new meaning: a league whose latest finished season is withheld (stats_need_research or a finished match without player minutes) must have no flagged season, which the flag gives; the two new tests fail closed and the three scoped tests exclude only what the rule withholds.
- Layer placement: both marts compose from core and intermediate refs only; no model, column or grain is added; the export reads the flag and computes nothing.
- After the review, one comment line, a dbt depends_on hint for int_team_season__metrics, was added to assert_mart_team_leaderboards_boards_cover_every_team because the MR's data build could not infer the ref() inside its loop; the other 180 tests of that build passed.

## escalations
(none)
