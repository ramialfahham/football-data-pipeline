# Task contract — Players hub: the warehouse and the export

objective: >
  Issue #135, the approved Players hub design: the warehouse serves every player with a page with
  the two blocks' orders, World's best (this year's Ballon d'Or and Yashin Trophy nominees in the
  Top clubs order of their current club) and Players by nation (nations in the Top national teams
  order, national-team regulars first, then the Teams hub's club order and minutes), and the
  export writes them to players_index.json. The page itself is a second MR.

refs: >
  #135 "The approved design" (approved in chat, 2026-11-09); data from #269 (nationality to
  national team), #271 (country confederation), #272 (award seed), #277 (one_value, no
  any_value). Plan and readings ruled by the coordinating session on 2026-11-09.

scope_paths:
  - dbt_project/models/5_marts/shared/mart_team_index.sql
  - dbt_project/models/5_marts/shared/mart_player_index.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/4_intermediate/shared/int_player__national_team_minutes.sql
  - dbt_project/models/4_intermediate/shared/int_player_page.yml
  - dbt_project/tests/assert_team_index_club_order_follows_the_rule.sql
  - dbt_project/tests/assert_player_national_team_minutes_recomputed.sql
  - dbt_project/tests/assert_player_index_nation_order_follows_the_rule.sql
  - dbt_project/tests/assert_player_index_order_in_nation_follows_the_rule.sql
  - dbt_project/tests/assert_player_index_worlds_best_follows_the_seed.sql
  - dbt_project/tests/assert_player_index_covers_every_player_page.sql
  - dbt_project/docs/layering.md
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - .claude/task/135-players-hub-data/contract.md
  - .claude/task/135-players-hub-data/review.md
  - .claude/task/135-players-hub-data/review_input.patch

impact_map: >
  writers: dbt only; no ingestion or seed change. mart_team_index gains one column, club_order.
  int_player__national_team_minutes and mart_player_index are new.
  lineage: `dbt ls --resource-type model --select mart_team_index+ int_player__page_profile+`
  returns int_player__page_profile int_player_page__window_seasons
  int_player_squad_window__metrics int_player_window__metrics mart_player_competition_benchmarks
  mart_player_fixture_stats mart_player_profile mart_player_squad_benchmarks
  mart_player_window_metrics mart_team_index mart_team_momentum_window: mart_team_index has no
  downstream model, and int_player__page_profile is only read, not changed. The two new models
  are leaves.
  consumption: export_site_data.py reads mart_team_index with select * and projects it through
  _TEAM_INDEX_KEEP, so teams_index.json does not change. The new players_index entity reads
  mart_player_index alone. The deploy job's entity list (.gitlab-ci.yml, protected) is not
  changed here, so nothing deployed changes until the page MR adds the entity.
  ci_layer_rules: scripts/check_layer_contract.py (no mart ref from intermediate, the
  any_value / approx_quantiles ban), scripts/check_description_hygiene.py,
  scripts/check_relationships_coverage.py.
  deploy_order: one merge; the nightly builds the new models. No backfill.
  blast_radius: one new column on mart_team_index; two new tables; one new export file that no
  page reads yet. No existing value changes.

approved_design:
  - players: #135

decisions_taken: >
  Readings of the approved design, ruled by the coordinating session on 2026-11-09:
  this year's nominees are the latest edition in the seed per award; the Top clubs order is the
  served order without the Teams hub's display cut (every club with a top_club_rank by
  region_rank then rank, then the other clubs by country_order and team_order_in_country, places
  shared broken by team_name then team_slug, the Teams hub's export order); nominees at one club
  follow the published placing, then name; the Goalkeepers list is the Yashin Trophy nominees and
  the outfield lists the Ballon d'Or nominees by their page position; a national team's minutes
  are the length of each of its matches with player data since 1 July 2025 as #135 states it
  (90, 120 after extra time); minutes this season are the player's club minutes in the
  this_season club window of the featured season. mart_player_index is a new mart because its
  grain (player) differs from mart_player_profile (player, season); ruled by the coordinating
  session. No new mechanism, no recurring cost beyond two small tables in the nightly build.
  docs/site_architecture.md §5 maps each page template to the export files it reads; the Players
  page template and its row there come together in the page MR, since no template reads
  players_index.json before it.

decisions_reserved:
  - How the built hub page stays small on a phone when the approved design lists all 18,528
    players with a page, each nation group showing 6 and the rest under the shared fold, which
    today holds every row in the HTML. Page design, for the page MR.

done_when:
  - dbt parse succeeds from the repo root.
  - python scripts/check_layer_contract.py, check_description_hygiene.py and
    check_relationships_coverage.py pass.
  - python -m pytest tests -q is green.
  - SQLFluff adds no violation on any changed model or test.
  - CI's data:build:mr is green, every new test included.
  - The ci_mr tables are compared with prod read-only: mart_team_index differs only by the new
    column, and mart_player_index's rows, nominees and regulars match the plan's measurements.
  - The export of this branch against main writes the same files plus players_index.json.

amendments: (none)
