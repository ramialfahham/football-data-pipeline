# Review — claude/101-rotation-a — 2026-11-25

diff_sha256: 31e88997d21d1ca9499b25704a5b0539c6dbebef8b40a514d9d063b01a841c59

rounds: 1

## analytics-engineer-reviewer
VERDICT: PASS
findings:
- [nit] fallback-season-completeness: mart_home_rotation.sql fallback role and shared.yml description — the fallback season is the latest finished-match season the provider no longer marks current; a season with one or two finished matches would qualify. No count bounds it.
- [nit] boards-not-confirmed: assert_home_rotation_fallback_has_a_completed_season.sql, assert_home_rotation_has_a_slot_in_season.sql — both count mart rows only; a withheld season gives an empty block and no test fires. The widened every-board test covers the current role only.
- [nit] vacuous-pass: assert_home_rotation_season_is_the_boards_current_season.sql — the inner join returns 0 rows when mart_leaderboards has no current rows.
- [nit] two-definitions: mart_home_rotation.sql, mart_leaderboards.sql — the first reads int_legs__team_match and the second fct_fixture statuses, so they differ on forfeit-only seasons; the drift test covers it.
- [nit] seed-shape: seeds/schema.yml — there is no unique test on competition_group alone, and a league whose season has no group in the seed drops out unnoticed.
- [nit] untested-flags: shared.yml — slot_is_in_season has no test of its own.
risks_checked:
- Layer contract: the mart reads int_legs__team_match, dim_competition_season and a seed, with no partition_by, cluster_by, raw ref or competition identifier in logic; no defect.
- Grain and fan-out: one row per (league_code, board_role), pinned by unique_combination_of_columns; J1's group change between seasons is handled by reading the group from the row's own season; no defect.
- In-season gate: is_in_season is never null on current rows and matches the var; a new season under 3 matches is out; no defect.
- Widened every-board test: the expected seasons are the mart's current in-season rows, withheld seasons are excluded as mart_leaderboards withholds them; no concrete failing case for a legitimate league.
- Descriptions under 1,024 characters, impact map present, no export file touched; no defect.

## closed
(none)

## fixes
- none: the first round followed only a PASS verdict.

## escalations
(none)
