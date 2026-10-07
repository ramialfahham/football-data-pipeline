# Acceptance evidence — #177 part 1: the form window serves every Form comparison metric

Read from the branch's changed models compiled and inlined against prod, read-only, 2026-10-07, against the prod
tables built by that morning's nightly.

criteria_demonstrated:
  - EXISTING VALUES UNCHANGED. mart_team_momentum: 9,042 rows on both sides, 0 unmatched, 0 rows where any existing
    column differs. int_team_season__metrics_cumulative: 120,030 rows on both sides, 0 unmatched, 0 rows differing.
  - THE 16 NEW METRICS SERVED. For Borussia Dortmund and SV Werder Bremen before their 9 Oct match (5-match windows):
    shots on target against 3.6 / 4.0, shots off target 6.2 / 5.6, blocked shots 5.8 / 3.4, shots inside box 14.0 /
    11.6, accurate passes 416.2 / 459.0, possession 0.531 / 0.536, dribbles attempted 17.8 / 15.2, dribbles completed
    7.8 / 7.4, dribble share 0.438 / 0.487, duels won 48.0 / 48.8, saves 3.0 / 2.2, fouls 10.8 / 11.8, offsides 2.2 /
    2.2, yellow cards 1.8 / 1.2, red cards 0.0 / 0.0. Each equals the value worked by hand from the provider's team
    lines and the player legs of the same ten matches.
  - FREE KICKS FOLLOWS RULE R4. Both teams have a window match without a free-kick value, so free_kicks_per_match is
    blank for both. 1,732 of 11,954 team lines this season carry one.
  - GENERATED CODE IN STEP. generate_metric_sql.py --check: 11 surfaces match the catalogue.
    sync_metric_docs_blocks.py --check: 179 blocks and 451 map rows match. pytest tests/: all pass.
