# Verification — the official league table at every kick-off

Checked locally on the branch: dbt parse; SQLFluff on the new model, the yoy model and the new
and changed tests (clean but for findings main already has: ST06 in
assert_team_season_equals_league_table, ST09 and two RF02 in
assert_team_yoy_pairs_the_same_games_played); a dry run against prod of the new model (11.1 MiB)
and int_team_profile__yoy (32.3 MiB) with the two seeds inlined; generate_metric_sql.py --check and
sync_metric_docs_blocks.py --check; the six offline gates; pytest (1,612 passed, 2 skipped). The
two tests that read the new model cannot be dry-run with it inlined (BigQuery: query too complex);
the MR data build runs them against the built table.

Lineage: `dbt ls --select int_team_season__table_by_time+ --resource-type model` lists
int_team_season__table_by_time, int_team_profile__yoy and mart_team_profile.

Research behind the seeds: each league's tie-break regulation per season, official texts only
(a season between two identical official editions counts as covered by them; a secondary source
does not); each deduction step's date from the decision that changed the table. Ruch Chorzow and
Al-Ittihad 2016-17 are outside the seasons the warehouse holds for those leagues.

Round 1 of the review changed: the published-table test leaves out a snapshot with a deduction
step after the matched kick-off's day; the previous season's place comes from single-table seasons
(one row per team); the second head-to-head pass groups by the first pass's criteria as the rule
applies them; assert_tiebreak_rules_end_undecidable (dry-run valid) requires every rule version to
end in one undecidable row; standings_temporary_results holds the 3-0 Juventus win over Napoli
the Serie A 2020-21 table held from 14 Oct to 21 Dec 2020, and the model counts it for both teams
(points, goals, played and head-to-head) at every kick-off in those dates. Sources are the official regulation
or, for J1's in-season order, the league's own published standings rules.

The first MR data build failed the published-table test on 508 places, no points. Serie A 2022-23
(Spezia and Verona) and Ligue 1 2025-26 (Toulouse, Lorient, Nantes) get official rows in
standings_corrections, Ligue 1's with the provider's group name and its trailing space; the test
applies a correction to every table of a past season. Saudi in-season places settled by last
season's place are not compared. The second build failed on 122 places, all Liga Portugal 2026-27
in season; every other league matched.

Liga Portugal in season: the league's nine 2026-27 matchday tables (ligaportugal.pt, read
2026-10-29) are reproduced exactly by head-to-head points once all level teams have met,
head-to-head goal difference once they have played each other twice, goal difference, the same
head-to-head among the teams still level, wins, goals; teams still level are listed
alphabetically, where the regulation gives them the same place. The provider orders teams level
on points by goal difference, then fewer goals conceded, so its tables are not the league's: that
version carries provider_order_differs and the test does not compare those places.
int_team_season__table_by_time, run against prod with the seeds inlined (11.6 MB), gives the same
place as that order for every team at all 70 Portugal 2026-27 kick-offs. The changed tests are
dry-run valid (202.7 MB; the new version test 0 B); pytest 1,612 passed, 2 skipped.

criteria_demonstrated:
  - standings_points_adjustments holds 22 dated deduction steps (Everton 3, Juventus 3, Adana Demirspor 3, Napoli 2 netting to zero, one each for the others) and the 38 halving rows undated; the seed's tests: unique per league, season, team, section and date; every step changes the points and every deduction is dated.
  - league_tiebreak_rules holds the regulations of BL1, BL2, PL, PD, SA, L1, ED, LP, TSL, SPL (from 2026), EKS (from 2023), BSA, MLS and J1 by first season and phase, each row with its source; seasons with no official text hold points alone; criterion, condition and phase are tested to closed lists.
  - int_team_season__table_by_time rebuilds every ranked league-season's table at every league kick-off: table points with the deductions in effect that day, the place by the league's rule rows (head-to-head mini-table and its second pass, conditions, play-off results), and no place for teams level at a criterion the results cannot settle; a phase with no rules orders by points alone; tested for its grain, the phase values and that an empty place only comes with a level team.
  - int_team_profile__yoy reads the rebuilt table on the day of the team's Nth match for points_this_season, points_prev_season, points_delta_yoy and points_rank_prev_season; assert_team_yoy_pairs_the_same_games_played checks those points against the table at the kick-offs it recomputes.
  - assert_team_table_equals_published_tables (error) compares the rebuilt place and points with every stored published table where the played counts match, and fails a rebuilt league-season with none comparable; the two warning tests it replaces are removed; assert_team_season_equals_league_table sums the dated steps per team.
  - The metric rules no longer hold the sentence that allowed a computed position; points_rank carries the approved description and interpretation.
