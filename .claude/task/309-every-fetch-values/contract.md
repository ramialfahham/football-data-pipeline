# Task contract — coaches, team match stats and player match stats take a value any stored fetch carried

objective: >
  Issue #309. Raw keeps every provider fetch, but base_apif__coaches, base_apif__fixture_statistics
  and base_apif__fixture_players each keep one whole fetch, so a value another fetch carried never
  reaches the site: 752 coaches show no nationality, about 2,400 team stats are blank, and about
  9,100 player stats show 0 and 1,900 are blank where another fetch has the value. Each model now
  takes a value from the newest fetch that carries it, under the checks the issue sets, and result
  values follow the match's events where two fetches disagree.

refs: >
  #309 (rules confirmed by the coordinating session, 2026-11-14); follows #201, #205, #203, #186.
  Measured on prod 2026-11-14, read-only: side-session note 290-latest-fetch-measure.md.

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__coaches.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/docs/cleaning_rules.md
  - docs/data_contract.md
  - dbt_project/tests/assert_coach_bio_from_every_fetch.sql
  - dbt_project/tests/assert_coach_fetches_agree_on_bio.sql
  - dbt_project/tests/assert_fixture_statistics_from_every_fetch.sql
  - dbt_project/tests/assert_fixture_players_from_every_fetch.sql
  - dbt_project/tests/assert_fixture_players_results_follow_events.sql
  - dbt_project/seeds/team_season_answer_key.csv
  - .claude/task/309-every-fetch-values/contract.md
  - .claude/task/309-every-fetch-values/review.md
  - .claude/task/309-every-fetch-values/review_input.patch

impact_map: >
  writers: base_apif__coaches is written only by dbt from stg_apif__coaches (RAW_APIF_COACHES,
  ingestion coaches loader, append-only). base_apif__fixture_statistics and base_apif__fixture_players
  are written only by dbt from stg_apif__fixture_statistics and stg_apif__fixture_players, both over
  RAW_APIF_FIXTURE_DETAILS (ingestion/api_football/loads/batch_fixtures.py, append-only, one row per
  fetch). No ingestion change.
  downstream: `dbt ls --select base_apif__coaches+ --resource-type model` → base_apif__coaches
  dim_coach. `dbt ls --select base_apif__fixture_statistics+ --resource-type model` →
  base_apif__fixture_players base_apif__fixture_players_from_lineups base_apif__fixture_statistics
  base_apif__lineups base_apif__players dim_player fct_fixture_lineup fct_fixture_player_stats
  fct_fixture_team_stats int_legs__player_match int_legs__team_from_players int_legs__team_match and
  every int_player_* / int_team_* / int_standings__official_rank / mart_* model reading them (82
  models in all, listed in full by that command). `dbt ls --select base_apif__fixture_players+
  --resource-type model` → the same set without fct_fixture_team_stats, int_legs__team_match,
  int_standings__official_rank and the standings/table int_team_season__* models.
  layer_rules: check_layer_contract.py (base reads staging and base only; table materialisation from
  dbt_project.yml); every model in the chain is a table rebuilt in full each night, no incremental
  fact (grep -rn incremental dbt_project/models/3_core → none), so filled values reach the facts.
  deploy_order: base only; the MR build writes ci_mr* datasets; prod changes at the first nightly
  after merge. No raw or schema change, so no ordering around the 04:00 nightly.
  blast_radius: coach bio on dim_coach (752 coaches gain nationality, birth country and names); team
  match stats (about 2,400 values, 2,048 free kicks) and every team metric and board built on them;
  player match stats (about 11,000 values, blocks and shots most) and every player metric, board,
  benchmark and leaderboard built on them; player goals, assists and cards where two fetches disagree
  and the events side with the fetch the model did not pick (goals 11, assists 15, yellow 136, red 5
  pairs table-wide). Row counts do not change.

approved_design:
  - none: no page layout changes; values on existing pages change

decisions_taken: >
  The rules of #309, confirmed by the coordinating session on 2026-11-14.
  Coaches: each bio field (name parts, birth date, birth place, birth country, nationality) from the
  newest fetch that carries it; age and photo stay from the latest fetch; a tie on the latest ingest
  time is broken by the row's own values, so every build keeps the same row. The test that two
  fetches never give one coach two bio values is a warning: where they do, the newest value stands,
  as #203 rules for revised values.
  Team stats: each stat from the newest fetch whose line carries it, before the cleaning steps, which
  run unchanged. A card count from an older fetch stands only where the match's delivered events do
  not hold a different number of cards of that colour against the team.
  Player stats: the picked fetch stays (#205). A blank non-result stat is taken from the newest other
  fetch carrying it whose goals, assists, yellow and red cards, minutes, penalties, saves and goals
  conceded equal the player's values after the events rule below (blank counted as 0). Shots and
  shots on target are filled for a team-match only where the team's player total with the fills is no
  further from the team line's figure than without them. Accurate passes are filled only from a fetch
  whose match values are in the same form (count or percentage) as the picked fetch's. Result values
  (goals, assists, cards, minutes, penalties, saves, goals conceded) are never filled from another
  fetch on its word alone.
  Events decide results: where another fetch gives a player a different number of goals, assists,
  yellow or red cards than the picked fetch, the match has full events and the events' count equals
  that fetch's value and not the picked fetch's, the events' count is the player's value; the
  cleaning steps then run unchanged. Measured: every such disagreement in goals, assists and cards is
  settled by the events (618 pairs, none unsettled), so no research rows are needed for them.
  Minutes (ruled by the coordinating session on 2026-11-14, path A): where both fetches carry
  minutes, the picked fetch's stand (#203), and a different value still keeps that fetch from filling
  the player's other stats. Where the picked fetch leaves them blank, another fetch's minutes stand
  when a substitution brought the player on at minute X and that fetch gives 90 - X or 91 - X
  (measured: 20 players, APD 14 and L1 6, each shown at 0 minutes before). The two the events do not
  settle, Marinho (fixture 1492429) and J. Aquino (fixture 1550987), stay blank and are research cases
  on #216; no new input into the player model.
  Answer keys follow the rule, as #203 has them follow the fetch the model reads: re-worked by hand
  from raw, three team_season_answer_key rows change. Spain, World Cup 2026: key passes 105 to 106
  (Ferran Torres, fixture 1489380, 1 key pass in the 16 Jun fetch, blank in the 6 Oct one).
  Argentina, World Cup 2026: interceptions 82 to 83 and defensive actions 260 to 261 (Lautaro
  Martinez, fixture 1582681, 1 interception in the 12 Jul fetch, blank in the 6 Oct one). Measured on
  prod: no other answer-key player, team, season or match row changes.
  The player model's new steps form one chain of CTEs, each read once, so BigQuery plans the model in
  time: a version with the steps joined back to each other failed its dry run on the planner timeout.
  No new mechanism; no recurring cost (base tables rebuilt nightly as today; the player model reads
  582 MB against 546 MB before).

decisions_reserved:
  - none: the minutes question was ruled (decisions_taken, Minutes); the research of the two unsettled players is #216's.

done_when:
  - dbt parse passes; sqlfluff lint passes on every changed model and test.
  - The full pytest suite passes.
  - The MR's data build passes, including the new singular tests and every answer-key test.
  - Re-running the 14 Nov measurement against the ci_mr tables finds no value the rules allow left blank or shown wrong.

amendments: (none)
