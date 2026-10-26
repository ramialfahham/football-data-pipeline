# Verification — the round in the competition header, in the page's language

Checked locally on the branch: dbt parse; SQLFluff on int_round_names, the three marts and the
singular test (clean); a dry run of int_round_names and the coverage test against prod's
fct_fixture (valid, 2.1 MB if run); the seven offline gates incl. check_copy_gate.py (106 seed keys
resolvable in every locale) and check_description_hygiene.py; check-page-specs (10 pages OK);
pytest (1,606 passed, 2 skipped); the site's node tests (134 passed). An offline replay of the seed
over every round text of each competition's latest season in the measured fct_fixture (1,678 round
texts, 48 competitions) names every one: 0 unresolved, 68 copy keys.

Lineage: `dbt ls --select int_round_names+ --resource-type model` lists int_round_names,
mart_competition_fixtures, mart_competition_index, mart_match_days, mart_next_matchday;
mart_match_days is the leaf the new columns pass under unread.

The MR's own data build (ci_mr343) loaded round_names (89 rows), built int_round_names (6.6k
competition-season round texts) and the marts without error; assert_every_round_text_resolves
passed (every latest-season round named). Read from ci_mr343_marts (3.6 MB, approved): all 34 BL1
2026 rounds served as compFactMatchday with their matchday. The committed BL1 sample carries those
fields per round, and as its current round the served name of its own next round (Regular Season - 6),
its other fields unchanged.

criteria_demonstrated:
  - round_names names each round text by the competition-season's own row, then the competition's, then the general one; int_round_names serves its copy key, number and group letter per (league_code, season_api_year, round_name); assert_every_round_text_resolves (warn, stored failures) reports a latest-season round without a key or without the number or letter its name shows.
  - mart_competition_fixtures and mart_next_matchday serve round_label_i18n_key, round_number and round_letter joined on league_code, season_api_year and round_name; mart_competition_index serves current_round_label_i18n_key, current_round_number and current_round_letter from mart_next_matchday.
  - The export carries the three per round and the current round in the competition payload; roundName() renders the served key with its number and letter; pytest pins that the mart columns are selected and carried by the competition fixture shape and the page meta; the header's round and the Matchdays picker read only those (examples: Bundesliga "6. Spieltag", Premier League "Matchweek 6", Veikkausliiga "Mestaruussarja, 23. kierros", WC "Bronze final", Copa del Rey 2026 "Round of 128" as "First round").
  - check_copy_gate.py reads round_names.csv and every one of its keys resolves in EN, DE and FI.
