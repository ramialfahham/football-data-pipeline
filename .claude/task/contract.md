# Task contract — Sint Maarten in the country list

objective: >
  The country list gains Sint Maarten as its own country, so every player's birth country is a listed
  country and the nightly's relationships test on dim_player passes.

refs: >
  The nightly's failing test relationships_dim_player_player_birth_country (one player, born in Sint
  Maarten). Sint Maarten as its own row, as Curacao is: approved in chat, 2026-10-09.

scope_paths:
  - dbt_project/seeds/countries.csv
  - dbt_project/models/3_core/dim_country.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: dim_country.sql changes only the row count inside its {# #} header comment, which dbt drops
    at compile; its compiled SQL is unchanged. The countries seed gains one row.
  downstream: `dbt ls --select dim_country+` returns dim_country and 8 tests, no model -
    not_null and unique on country_key and country_name, and the relationships tests from
    dim_coach.coach_birth_country, dim_league.league_country, dim_player.player_birth_country and
    dim_team.team_country. One more row lets a failing relationships test pass and changes no
    existing row.
  layer_rules: a seed row and a comment; no logic.
  deploy_order: the nightly loads the seed after merge.
  blast_radius: dim_country gains one row; the nightly's relationships test on dim_player passes.

acceptance_criteria:
  - countries.csv has the row sint-maarten,Sint Maarten in alphabetical order; country_key and country_name stay unique and not null.
  - Every value the nightly's relationships test returned is a country_name in countries.csv.

decisions_taken: >
  Sint Maarten is its own country row, apart from Saint Martin (the French half of the island), as
  Curacao is: approved in chat, 2026-10-09.

decisions_reserved:
  - Any other country, override or naming change.

done_when:
  - The two acceptance criteria are shown in .claude/task/acceptance_evidence.md.
  - pytest tests/ passes.

amendments: dim_country.sql added to scope_paths, with the impact map, so its row count in the header
  comment stays true: approved in chat, 2026-10-09.
