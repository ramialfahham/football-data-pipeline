# Review — claude/277-deterministic-tiebreaks-4afa9c — 2026-11-15

diff_sha256: 06a7716bea269069defeb88f2559729ff7c9446ef5d6fc5a2c2f6e3ca381d9e0

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file against scope_paths: all 18 are listed; base_apif__lineups.sql entered by the 2026-11-15 amendment, and only its transfers, same_day_departures, latest_moves and club_on_match_day CTEs change.
- decisions_reserved "none" and approved_design "none": no metric, label, URL, page composition, site_v2 or export change in the diff.
- The impact_map lineage: the pasted dbt ls output lists 99 models, matching the stated count; no ingest, scope or coverage is narrowed.
- Appendix A: no new metric, library, service or frontend logic; the tests reuse dbt_utils unique_combination_of_columns.
- Non-blocking: these are the first source-level tests in sources.yml, and the 32.5 MB a night they scan is stated in recurring_cost; both are listed in the MR head for the merge.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Every changed pick against the grain or unique test of its input: coach career, transfers, competition seasons, league entity, global teams, the three team-name picks, fixture statistics, club on the match day, form-window legs, national competition, featured season, competition order, next round, goal list and position to date. All final keys are total.
- base_apif__lineups: rank() keeps both clubs on a tie and club_on_match_day gives no club for two distinct clubs; the join to the distinct same_day_departures cannot fan out.
- The new source and staging tests against the partition and order keys of the picks they pin: the keys match.
- Layer placement, competition-agnostic logic, seeds and project config: no violation.
- Non-blocking: the line-length note on int_team__current_national_competitions.sql:55 measures 120 characters, within the limit, and SQLFluff with the dbt templater reports no violation.
- Non-blocking: the new error-severity tests stop the nightly on a raw duplicate; prod holds 0 today. Listed in the MR head.

## escalations
(none)
