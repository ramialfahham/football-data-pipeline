# Task contract — a cup fixture names the club that played it

objective: >
  Issue #280. Every fixture whose provider id names a same-named club from another country names
  the club that played it, through rows in the existing per-fixture override seed. A test fails
  when a club in a continental club competition belongs to another confederation.

refs: >
  #280. Plan approved in chat, 2026-11-09, through the coordinating session. Five provider team
  searches approved in chat, 2026-11-09.

scope_paths:
  - .claude/task/280-fixture-team-ids/
  - dbt_project/seeds/fixture_team_id_overrides.csv
  - dbt_project/seeds/team_country_corrections.csv
  - dbt_project/seeds/team_name_overrides.csv
  - dbt_project/tests/assert_continental_club_in_competition_confederation.sql

impact_map: >
  writers: fixture_team_id_overrides is read by base_apif__fixtures_next, base_apif__fixture_events,
  base_apif__fixture_players, base_apif__fixture_statistics, base_apif__lineups and
  base_apif__teams, and by the tests assert_fixture_team_id_overrides_applied,
  assert_base_team_stats_cleaned and the three team-in-fixture-participants tests.
  team_country_corrections and team_name_overrides are read by base_apif__teams_global, the only
  writer of dim_team.
  downstream: `dbt ls --select fixture_team_id_overrides+ team_country_corrections+
  --resource-type model` (run 2026-11-09) gives 88 models, 31 of them marts: every model that
  carries a fixture's teams, a team's matches or a team's country.
  layer_rules: seed rows only; no model changes. The new test reads core (fct_fixture, dim_team,
  dim_league, dim_country). No partition_by or cluster_by. No per-competition file.
  deploy_order: additive seed rows. The merge rebuilds everything downstream in data:build:main.
  blast_radius: measured on prod, 2026-11-09. 11 fixtures change one team each: 3 FA Cup to
  Newmarket Town (8878), 4 CAF Champions League to Victoria United of Cameroon (20800) and to our
  own Gambia Armed Forces (-2), 4 Coupe de France to Diables Noirs de Combani (20600) and to our
  own Lourdes FC (-3), Rochefort FC (-4) and AS Montigny-lès-Metz (-5). CD Lourdes (9852) moves
  from France to Spain. 20800 and Victoria United (18919) share a name: 18919's slug moves from
  victoria-united to victoria-united-canada, and 20800, whose provider country no feed carries,
  takes victoria-united-20800. The new names take no slug another team holds. The MR head lists
  every fixture before and after.

approved_design:
  - none: no page output changes

decisions_taken: >
  The plan was approved in chat on 2026-11-09 through the coordinating session.
  No new mechanism: the reattribute_in_fixture mode of fixture_team_id_overrides already moves a
  wrong id to the right one inside one fixture across the fixture list and every match feed.
  Each row cites the organiser's page (CAF, The FA, the FFF and its leagues, the RFEF) or a party
  to the match, and the provider's own fixtures where they prove the id.
  The provider's own id is used where its team search finds the club (20800); our own ids -2 to
  -5 are minted where it does not, each with a sourced name and country, as -1 was.
  The continental check compares the club's country's confederation with the competition's, only
  where both are stored. The domestic version stays a proposal: Welsh, Canadian and French
  overseas clubs cross borders legitimately, so it needs a list of allowed pairs.

decisions_reserved:
  - The domestic check (a club in another country's domestic competition) needs a list of
    allowed country pairs, which is a new holder; it is proposed, not built.

done_when:
  - dbt parse passes; SQLFluff passes on the new test; the offline gates and pytest pass.
  - The changed base models, compiled with the new rows and run read-only on prod, carry the right
    id in every listed fixture and feed; assert_fixture_team_id_overrides_applied returns no rows.
  - The new test returns no rows once every row is applied.
  - The MR's ci_mr tables compared with prod change only the listed fixtures, teams and countries.

amendments: (none)
