# Verification — appearances as a catalogue metric

Checked locally on the branch: generate_metric_sql.py --check (10 surfaces match the catalogue);
sync_metric_docs_blocks.py --check (183 docs blocks, 450 map rows); dbt parse; SQLFluff on the two
player intermediates, mart_player_career and the drift test (only the dbt_utils template noise of
these files, on unchanged lines); the seven offline gates; pytest (1,612 passed, 2 skipped) after
lowering the decision-history pin by the one line the mart comment no longer holds.

After round 1 of the review the position surface generates appearances too, the player profile
wireframe and the minutes description follow, and the same checks pass again (pytest 1,612 passed,
2 skipped).

The generated appearances column keeps the hand-written guard: blank when a match's minutes are
unknown or the window holds a played team match with no player data, otherwise countif(minutes > 0).

The answer key gains appearances for its five player-seasons, read from int_legs__player_match on
2026-10-30 (55.8 MB): Kane BL1 2024-25 31 of 31 match rows, Olmo EURO 2024 6 of 7 (one match named
without minutes), Salah PL 2024-25 38 of 38, Mbappé WC 2026 8 of 8, Martínez WC 2026 8 of 8; no
row without minutes.
