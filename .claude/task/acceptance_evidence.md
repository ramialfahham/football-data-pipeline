# Verification — the Team page's Competitions block

Checked locally on the branch: dbt parse; SQLFluff on int_round_names, int_knockout_ties,
mart_team_competitions and the two new tests (clean); a dry run of each against prod with the
branch's round_names seed inlined (valid, 2.0 to 12.0 MiB each if run); the six offline gates and
both generator checks; pytest (1,610 passed, 2 skipped). The MR's data build runs the models and
their tests in BigQuery. A prod query of 4.9 MB (approved in chat, 2026-10-28) mapped each cup and
continental competition's latest-season rounds: single-leg cups (DFBP, CIT, CDF), two-legged
rounds (UEFA qualifying and play-offs, CAFCL, CCCU, LIBER knockouts, CDR's first round), FA Cup
replays as rounds of their own, and the league-phase tables (UCL "League Phase", UEL and UECL a
table named after the competition, AFCCL East and West, LIBER groups).

Lineage: `dbt ls --select round_names+ --resource-type model` lists int_round_names,
int_knockout_ties, mart_competition_fixtures, mart_competition_index, mart_match_days,
mart_next_matchday and mart_team_competitions.

criteria_demonstrated:
  - round_names.csv gains stage_kind on all 89 rows: 25 table (the rows named by a matchday), 6 final (the final patterns, Veikkausliiga's European play-off final left a knockout round), 3 placement (the third-place patterns), 55 knockout; seeds/schema.yml tests not_null and the four values; int_round_names serves round_stage_kind, tested to the four values.
  - int_knockout_ties: one row per team and tie (league, season, round, team, opponent) over the knockout rounds; legs, legs played, goals over the played legs, decided_by goals, shootout or award, won; tested for the grain, played legs in range and that a result comes with its decision; assert_knockout_tie_has_one_winner fails a tie whose two rows disagree or whose decided tie has not one winner and one loser.
  - mart_team_competitions: one row per (team_sk, league_code, season_api_year) with the standing of the section named in the latest played round (else the one with the most matches), the latest played round, the reached round (a third-place match left out) and its kind, cup_status by the tie rule with winners only for a final outside a qualifying competition, and competition_order (league, cups, super cup, then the rest); tested for the grain, the accepted values, a cup status only in a round of ties and winners only in a final; assert_team_competitions_one_winner fails a competition-season with more than one winner, assert_team_competitions_knocked_out_has_no_later_fixture a knocked-out team or winner with a fixture in a later round.
  - The team payload's featured season carries competitions in competition_order with the display fields only; test_the_featured_season_lists_its_competitions_in_the_served_order and test_a_sampled_team_export_scopes_its_competitions_to_the_sample pin it.
