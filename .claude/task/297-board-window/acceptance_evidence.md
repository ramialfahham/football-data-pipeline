# Verification — the eighth Match leaders board and the season record's window

The committed played samples are not re-exported in this MR, so no committed page carries the new
board. The evidence is read from the export's own output for a played match in prod, and from the
site's board title for the board's name key.

criteria_demonstrated:
  - **The played match page's Match leaders shows a Ball actions board whose name resolves in EN, DE and FI:** this branch's `fetch_played_fixture_payloads` run read-only against prod for fixture 1575150 (BL1, 5 Sep 2026; 6 queries, 0.87 GB billed) returns 8 boards in the catalogue's order, the fourth `ball_actions_player` with `label_i18n_key` playerMetrics.ballActions.label, format integer, 3 rows, L. Avdullahu first on 76. On gitlab/main the same call stops with `KeyError: mart_leaderboards serves a match board the export does not list: ball_actions_player`. The site's `boardTitle()` for that key renders "Ball actions" (EN), "Ballaktionen" (DE) and "Pallotoiminnot" (FI); without this MR's `METRIC_TERMS` entry it renders an empty name.

The window fix (no page change in the committed sample): the compiled new `mart_player_season_record`
run read-only against prod (90 MB) has 6,552 sides against 6,641; the 89 that leave are exactly the
sides whose team has played the fixture's competition this season without player rows there. No
other side changes window, and 0 sides show the previous season after their team has played.
