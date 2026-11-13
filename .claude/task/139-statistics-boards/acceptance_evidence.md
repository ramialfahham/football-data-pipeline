# Verification — the two comparison row files

Read from the regenerated files themselves, which the site build reads as they are, compared with
`gitlab/main` (`git diff --stat gitlab/main -- site_v2/src`, and the metric_id lists of both
versions). tests/test_metric_rows.py holds each file equal to a fresh regeneration from the seed;
tests/test_form_comparison_metric_set.py holds both metric sets.

criteria_demonstrated:
  - **metric_rows.json:** 34 rows on main and 34 now, the same metric_ids. Order now: shooting runs shots, shots on target, shots inside box, inside-box share, shooting accuracy, goals per shot on target, then shots on target against (on main it came third); passing runs passes, accurate passes, pass accuracy, key passes, then possession (passes_share_pct, on main before key passes); discipline runs yellow cards, red cards, fouls, offsides (on main fouls and offsides came first).
  - **player_metric_rows.json:** 24 rows on main and 24 now, the same metric_ids. Order now: passing runs passes per 90, pass accuracy, key passes per 90, then ball actions per 90 (on main ball actions came before key passes); one-on-one runs dribbles completed per 90, dribble success, duels won per 90, duels won share (on main the two duels rows came first).
  - **No other site_v2/src file:** `git diff --stat gitlab/main -- site_v2/src` lists site_v2/src/data/metric_rows.json and site_v2/src/data/player_metric_rows.json and nothing else.
