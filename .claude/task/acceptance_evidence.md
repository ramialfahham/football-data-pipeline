# Acceptance evidence — #173 part 1: the match page's lists of matches read mart_competition_fixtures

Read from two runs of the fixture export on the same prod data, 2026-10-07: main's code against prod, and this
branch's code with the branch's mart_competition_fixtures compiled and inlined against prod, read-only.

criteria_demonstrated:
  - SAME HEADER AND RECENT MATCHES. Both runs wrote the same 4,614 fixture files. With next_match set aside on both
    sides, every file is equal to main's, value for value: the header (now read from mart_competition_fixtures) and
    form_window (Recent matches) are unchanged.
  - EACH TEAM'S NEXT MATCH. 8,517 sides carry next_match, read from mart_competition_fixtures by its
    is_home_team_next_match / is_away_team_next_match flags; 711 carry none, each because its next match is the
    page's own match. An independent check, the earliest kick-off still ahead per team among the exported
    fixtures, agrees on every side: 0 disagreements. Example: Bayern München vs Borussia Dortmund, 31 Oct, names
    FC Augsburg vs Bayern München (10 Oct) and Borussia Dortmund vs SV Werder Bremen (9 Oct).
  - A TEST FAILS ON TWO NEXT MATCHES. assert_mart_competition_fixtures_one_next_match_per_team, compiled and run
    against the inlined mart: with the mart mutated to flag a team's two earliest matches it returns 553 rows
    (fails); as written it returns 0 rows (passes).
