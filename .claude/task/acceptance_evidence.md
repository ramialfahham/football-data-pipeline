# Verification — Red Star de Bangui gets its own team id

Read-only on prod data, each query's bytes approved before it ran. The changed models' compiled SQL
read prod's tables with the branch's three seeds inlined.

- The new test on today's prod returns both fixtures: 1239850 and 1239851 carry 104 in
  base_apif__fixtures_next, base_apif__fixture_statistics, and for 1239850 also in
  base_apif__fixture_events and base_apif__lineups; neither fixture carries -1.
- With the fix, per source for the two fixtures: fixture list -1 v Djoliba 8060 in both;
  events 3 rows -1 and 3 rows 8060 (1239850); line-ups 18 rows -1 and 19 rows 8060 (1239850);
  team statistics 1 row -1 and 1 row 8060 in each fixture, run on the corrected fixture list.
  No 104 remains.
- Neither fixture has a player-team decision in base_apif__fixture_events, so the player feed
  reading today's events table changes nothing.
- base_apif__teams_global with the fix: -1 is Red Star, Central African Republic, slug `red-star`;
  104 stays RED Star FC 93, France, slug `red-star-fc-93`. No other team's slug changes.

dbt parse passes. SQLFluff on the six changed models and the new test passes;
assert_base_team_stats_cleaned.sql reports the same 32 findings as on main. pytest: 1,617 passed,
4 skipped. The fast offline gates pass.
