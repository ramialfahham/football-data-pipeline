# Verification — the two comparison row files

Read from the regenerated files themselves, which the site build reads as they are, compared with
`gitlab/main` (`git diff --stat gitlab/main -- site_v2/src`, and the metric_id lists of both
versions). tests/test_metric_rows.py holds metric_rows.json equal to a fresh regeneration from the
seed; tests/test_design_mocks_read_catalogue_order.py does the same for player_metric_rows.json;
tests/test_form_comparison_metric_set.py holds both metric sets.

criteria_demonstrated:
  - **metric_rows.json:** 34 rows on main and 34 now, the same metric_ids. In Shooting, shots on target against moves from last to third: shots, shots on target, shots on target against, shots inside box per match, shots inside box percentage, shooting accuracy, goals per shot on target. Every other group reads as on main. Shots off target and blocked shots have places 11 and 12 in the catalogue and are not rows: the export serves the approved set, which tests/test_metric_rows.py::test_a_place_in_the_catalogue_never_adds_a_row holds.
  - **player_metric_rows.json:** unchanged: `git diff --stat gitlab/main -- site_v2/src` does not list it, and the committed file equals a fresh regeneration from the seed.
  - **No other site_v2/src file:** `git diff --stat gitlab/main -- site_v2/src` lists site_v2/src/data/metric_rows.json and nothing else.
