# Task contract — a player's nationality and his national team resolve to one country

objective: >
  Issue #269. Every player's nationality resolves to one country in `core.dim_country`. Every
  national team also resolves to its country. `mart_player_profile` serves each player's
  nationality team, so the Players hub (#135) can group a nation once and find its national
  team regulars.

refs: >
  #269. Plan approved in chat, 2026-11-09, through the coordinating session. #135 is the Players
  hub design that reads the result. Replays MR !400 as one change on current main.

scope_paths:
  - .claude/task/269-nationality-country/
  - dbt_project/models/2_base/api_football/base_apif__player_profiles.sql
  - dbt_project/models/2_base/api_football/base_apif__players.sql
  - dbt_project/models/3_core/dim_team.sql
  - dbt_project/models/3_core/dim_country.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/seeds/country_name_overrides.csv
  - dbt_project/seeds/countries.csv
  - dbt_project/seeds/team_country_corrections.csv
  - dbt_project/seeds/player_bio_corrections.csv
  - dbt_project/seeds/schema.yml

impact_map: >
  writers: base_apif__player_profiles and base_apif__players are the only writers of player_nationality.
  They feed dim_player, which takes the profile value first and falls back to the identity source.
  dim_team is the only writer of the new is_national_team. It reads base_apif__fixtures_next and
  dim_league; neither reads dim_team. base_apif__teams_global still writes team_country, now with six
  more rows in team_country_corrections.
  downstream: `dbt ls --select base_apif__teams_global+ base_apif__player_profiles+ base_apif__players+
  --resource-type model` (run 2026-11-09) gives: base_apif__player_profiles base_apif__players
  base_apif__teams_global dim_player dim_player_team_season_mapping dim_team
  mart_competition_fixtures mart_fixture_standing_context mart_leaderboards mart_match_days
  mart_matchday_insights mart_player_career mart_player_competition_benchmarks
  mart_player_fixture_stats mart_player_profile mart_roster mart_standings
  mart_team_competition_benchmarks mart_team_competitions mart_team_fixtures mart_team_index
  mart_team_leaderboards mart_team_market_value mart_team_momentum_window mart_team_profile
  mart_team_season mart_team_season_insights.
  layer_rules: base reads base and seeds only. dim_team (core) reads base and dim_league, and
  dim_league stays the only reader of the competition_registry seed. The mart reads core. All are
  checked by check_layer_contract.py. No partition_by or cluster_by. No per-competition file.
  deploy_order: additive. One new column on dim_team (is_national_team) and one on
  mart_player_profile (nationality_team_sk); no column is renamed or dropped. The merge
  rebuilds everything downstream in data:build:main, and the 04:00 nightly rebuilds it again.
  blast_radius: player_nationality values change on every mart that carries them (roster,
  profile, career, leaderboards, benchmarks, fixture stats), e.g. Korea Republic becomes
  South Korea. Measured on MR !400's CI build: the profile mart's reconciled spellings cover
  941 Korea Republic, 933 USA and 805 Türkiye players, among others, and its row count is
  unchanged (271,503). team_country changes for six national teams: India, Hong Kong,
  Lebanon, Malaysia, South Sudan and Sint Maarten. mart_team_index changes only those six
  rows' team_country.

decisions_taken: >
  The plan was approved in chat on 2026-11-09 through the coordinating session.
  Nationality is reconciled in base through country_name_overrides, the same seed already used for
  birth country, under the approved #69 naming rule. The provider's exact string is the join key,
  mapped after the bio correction and before the text repair, so the provider's two garbled spellings
  (TÃ¼rkiye, CÃ´te d'Ivoire) are seed rows of their own. Repairing first and then joining exceeds
  SQLFluff's parse depth. A future garbled spelling fails the new relationships test instead of
  passing through. A blank or whitespace-only nationality becomes NULL.
  is_national_team means the team plays a fixture in a competition whose dim_league entity_type is
  national: 216 teams, the same set mart_team_index uses. It is built in dim_team because
  dim_league is the only reader of the competition_registry seed and a base model cannot read a dim.
  The provider's /teams list for a national competition holds one Portuguese club (4767, Mação, in
  WCQAS) that has no fixtures there, so /teams is not the source.
  The national-team tests sit on dim_team, filtered to national teams: team_country not_null, unique,
  and a relationships test to dim_country. No new model.
  Seed rows:
  - country_name_overrides: Andorra CF, Falkland Islands (Malvinas), and the two garbled spellings,
    under the #69 rule.
  - countries: Falkland Islands, Guernsey, Isle of Man and Kiribati, under the rule that admits
    Jersey.
  - team_country_corrections: six national teams, each citing its federation page, as Macao does.
  - player_bio_corrections: player 13730, whose nationality the provider sends blank, becomes
    Colombia, sourced from Fichajes. The CPO answered for this row in this task's session on
    2026-11-09. The seed's description widens from conflicting records to conflicting or missing ones.
  Fan-visible: the nationality text on the team squad list and the player page moves to the #69
  country names that birth country already shows. This is the approved #69 rule; the head of the MR
  lists it under fan-visible changes.
  No new mechanism and no recurring cost.

decisions_reserved:
  - none: the route, the seed rows and the fan-visible change are covered by the plan approved on 2026-11-09, the #69 rule and the CPO's answer on player 13730; a youth or women's national team failing the unique test goes to the coordinating session with the measured rows before any new model.

done_when:
  - check_layer_contract.py, check_description_hygiene.py, sqlfluff on the changed models, dbt parse, and the offline Python suite all pass locally.
  - data:build:mr is green, including the new relationships, not_null and unique tests.
  - Measured on the ci_mr datasets, each split nation in the issue is one country, and each nation with a national team has one nationality_team_sk.
  - The export-facing columns (nationality on roster and profile; team_country on dim_team) are diffed between ci_mr and prod, and every difference is a reconciled spelling or one of the six corrected teams.

amendments: (none)
