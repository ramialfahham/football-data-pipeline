# Verification — key metrics in the catalogue, cards as totals

Checked locally on the branch: the catalogue compared column by column with main's; the served
list regenerated with the export's own `fetch_metric_rows` and read back; `dbt parse`,
`generate_metric_sql.py --check` and `sync_metric_docs_blocks.py --check`; `npm run build` in
`site_v2` on the committed sample, its 548 built match pages searched in EN, DE and FI; the full
pytest suite; the design check. The MR's data build runs the models and their tests in BigQuery.

criteria_demonstrated:
  - The catalogue differs from main's in two columns only: `importance_tier` renamed `is_key_metric`, true on 14 team rows (goals_per_match, goals_against_per_match, shots_per_match, shots_on_goal_per_match, shots_on_goal_against_per_match, passes_per_match, passes_accuracy_pct, passes_share_pct, duels_per_match, duels_won_pct, defensive_actions_per_match, fouls_per_match, cards_yellow, cards_red), false on the other 42 team rows, blank on the 49 player rows; `metric_order` blank on exactly shots_off_target_per_match, shots_blocked_per_match, cards_yellow_per_match and cards_red_per_match. No file in the repo names `importance_tier` any more.
  - `metric_rows.json` holds 34 rows, every one with `is_key_metric` (14 true); the four rows are gone; cards_yellow (place 4) and cards_red (place 6) are served with `per_match: false` and format `integer`. `tests/test_metric_rows.py` pins the file to a fresh regeneration and each row's flag to the catalogue.
  - `int_team_momentum__metrics` (regenerated from the form surface) and `mart_team_window_metrics` gain `cards_yellow` and `cards_red`, built from the catalogue formula `sum(cards_*)`; `metric_map.csv` gains their two rows; both generator checks pass. The MR's data build runs the formula and coverage tests on them.
  - 0 of 548 built match pages show Shots off target or Blocked shots, in EN, DE or FI. The committed sample payloads carry no card totals yet, so no card row shows until the next full export.
  - `metrics_display.md` holds the approved Key metrics section, the paired rule as approved, the team table without its Tier column, and no remaining mention of a tier; `metric_layer.md` line 21 reads as approved.
