# Verification — the official table at every kick-off, within the query time limit

BigQuery's job history for int_team_season__table_by_time since 2026-10-29: eight runs of 137 to
316 s and 24 to 142 slot-hours, two stopped at the 300-second limit (MR !351's first build and
main's build after it), each plan over 1,400 stages, most of them reading 19 to 122,000 rows.

A script with temporary tables, run against prod on 2026-10-30, ran today's model (427 s, 131.6
slot-hours) and the split this branch builds: the legs (1 s), the team state (13 s) and the rest
(44 s, 0.5 slot-hours). Both gave 428,916 rows, and comparing every column of every row found
none only on one side; the script billed 479 MB.

Checked locally on the branch: dbt compile and parse; SQLFluff on the three models; a dry run
against prod of int_team_season__table_legs (11.3 MB) and int_team_season__table_state with the
legs inlined (10.7 MB), while int_team_season__table_by_time with both inlined is too complex to
plan as one query, which is the defect itself; the six offline gates;
check_relationships_coverage; pytest (1,612 passed, 2 skipped).
