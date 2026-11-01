# Verification — Ball actions

Read on prod data on 2026-11-01; the bytes of each query were approved before it ran.

criteria_demonstrated:
  - The catalogue holds `ball_actions_player` (integer) and `ball_actions_per90` (decimal_1), formula `sum(passes + shots + dribbles + tackles + interceptions + blocks + saves)` (the per 90 `* 90 / sum(minutes)`), group passing, direction higher_better, with the approved description and interpretation.
  - `generate_metric_sql.py` writes both into `int_player_season__metrics` and the per 90 into `int_player_season_position__metrics`; `--check` reports all 10 surfaces match the catalogue. The existing metrics' generated SQL is unchanged (the diff adds lines only, plus the comma after the previous last column).
  - `mart_player_profile` serves `ball_actions_player`; `ball_actions_per90` joins the position-peer comparison for GK, DEF, MID and ATT, and the benchmark `metric_key` accepted values list it.
  - The compiled season model run on prod data: 193,804 rows, as the prod table; Ball actions is blank on 61,518 player-seasons (passes 39,076, defensive actions 57,860), each with an unrecorded match. Values: Salah PL 2024-25 1,418 and 37.79 per 90; Kane BL 2024-25 775 and 29.20; Mbappé WC 2026 307 and 39.58; E. Martínez WC 2026 266 (20 saves) and 29.56; Olmo EURO 2024 215 and 44.90.
  - The answer key carries both metrics for the five player-seasons, worked from the match lines (each component summed, the provider's blanks counted); every value equals the model's.
  - The two design docs and the benchmark descriptions no longer restate the set's count, members or directions; they point to the catalogue's direction column and to the benchmark model.

`generate_metric_sql.py --check` and `sync_metric_docs_blocks.py --check` pass. dbt parse passes. SQLFluff
on the changed intermediate models passes; mart_player_profile reports the same warnings as on main.
pytest: 1,619 passed, 2 skipped. The fast offline gates pass.
