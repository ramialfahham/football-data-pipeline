# Task contract — kick-off in the venue's clock

objective: >
  Issue #146: the warehouse knows where a match is played in time. A venue has an IANA time zone
  (`dim_venue`), a country has a default zone (`dim_country`), `dim_timezone` lists the valid zones
  and the labels they print, and `fct_fixture` serves `kickoff_local` and `kickoff_zone_label` for
  every fixture. The marts that list matches carry both columns, the export ships them, and the
  site's one match row prints them with the date heading of the local day. The site converts nothing.

refs: >
  #146 (shape agreed with the CPO, 2026-09-14, in the issue's comment); #129, #127, #130, #134
  (the pages whose rows change); main 2d37dc8b; the coordinator's request of 2026-11-20.

scope_paths:
  - .claude/task/146-venue-timezone/
  - dbt_project/seeds/country_time_zones.csv
  - dbt_project/seeds/time_zones.csv
  - dbt_project/seeds/venue_time_zones.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/macros/kickoff_zone_label.sql
  - dbt_project/models/2_base/api_football/base_apif__venues.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/docs/layering.md
  - docs/wireframes/00_overview.md
  - docs/wireframes/10_home.md
  - dbt_project/models/3_core/dim_venue.sql
  - dbt_project/models/3_core/dim_timezone.sql
  - dbt_project/models/3_core/dim_country.sql
  - dbt_project/models/3_core/fct_fixture.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/5_marts/shared/mart_next_matchday.sql
  - dbt_project/models/5_marts/shared/mart_competition_fixtures.sql
  - dbt_project/models/5_marts/shared/mart_team_fixtures.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/*.sql
  - scripts/export_site_data.py
  - tests/test_export_landing.py
  - tests/test_export_matches.py
  - tests/test_export_site_data.py
  - tests/test_kickoff_clock_146.py
  - tests/test_no_decision_history_in_code.py
  - tests/test_sentence_length_in_docs.py
  - site_v2/src/lib/types.ts
  - site_v2/src/lib/teamFixtures.ts
  - site_v2/src/data/competitions/BL1/2026.json
  - tests/test_export_pages_data.py
  - site_v2/src/lib/format.ts
  - site_v2/src/lib/format.test.mjs
  - site_v2/src/components/ui/MatchRow.astro
  - site_v2/src/components/home/HeroFixtures.astro
  - site_v2/src/components/competition/MatchdaySchedule.astro
  - site_v2/src/components/matches/MatchesDay.astro
  - site_v2/src/components/team/TeamFixtureGroup.astro
  - site_v2/src/components/fixture/NextMatches.astro

impact_map: >
  writers: dim_country is written by the `countries` and `country_time_zones` seeds; dim_timezone by
  the `time_zones` seed; base_apif__venues (new) by base_apif__fixtures_next, base_apif__teams_global
  and base_apif__league_entity; dim_venue (new) by base_apif__venues and two seeds; fct_fixture by
  base_apif__fixtures_next only, and now also reads dim_venue, dim_league, dim_country and
  dim_timezone. downstream, measured 2026-11-21 with `dbt ls --select fct_fixture+ --resource-type
  model`: 73 lines, among them the marts mart_competition_fixtures, mart_competition_index,
  mart_competition_research_list, mart_competition_season_summary, mart_fixture_standing_context,
  mart_head_to_head, mart_leaderboards, mart_match_days, mart_matchday_insights, mart_next_matchday,
  mart_player_career, mart_player_competition_benchmarks, mart_player_fixture_stats, mart_player_index,
  mart_player_momentum, mart_player_profile, mart_player_season_record, mart_player_squad_benchmarks,
  mart_player_window_metrics, mart_standings, mart_team_competition_benchmarks, mart_team_competitions,
  mart_team_fixtures, mart_team_index, mart_team_leaderboards, mart_team_momentum_window,
  mart_team_page_window_metrics, mart_team_profile, mart_team_season, mart_team_season_insights,
  mart_team_season_record, mart_team_window_metrics, and the intermediate models between. `dbt ls
  --select countries+` (before this change) listed dim_country, mart_player_index and
  mart_team_index. RAW count: fct_fixture has 65,205 rows and 0 NULL kickoff_datetime; the change
  adds three columns and changes no existing column. layer_rules: check_layer_contract.py (core reads
  base, seeds and other core models; marts read core; a core model reads no mart); the venue's
  country is resolved across `/fixtures`, `/teams` and `/leagues` in 2_base, as layering.md's
  cross-source entity rule requires; no per-competition file; no `partition_by`/`cluster_by`; descriptions
  stay under the BigQuery limits (check_description_hygiene.py). The registry
  docs/competition_registry.yml is not touched: the fallback for a fixture without a venue is
  `dim_league.league_country` -> `dim_country.time_zone`. deploy_order: seeds and models deploy in
  one nightly build; fct_fixture rebuilds after dim_venue (dbt orders it by ref), and a failing
  `not_null` on a venue zone stops the build before the marts. blast_radius: every row of
  fct_fixture gains `kickoff_time_zone`, `kickoff_local`, `kickoff_zone_label`; the match row on Home,
  competition, team and match-page lists prints the venue's clock instead of UTC. The Matches
  page is not changed: its day is the UTC date (mart_match_days.match_day, the key of the day-page
  URL), so its rows keep the UTC clock and a day heading and a row clock never name two dates;
  mart_match_days is untouched. The order of a round's rows (mart_competition_fixtures.fixture_order)
  follows the printed clock, so the day headings never run out of date order; the Matches page
  orders its rows by day_row_order, which is unchanged.

acceptance_criteria:
  - Every upcoming fixture row the site renders carries a served local kick-off time and a served zone label (`kickoff_local`, `kickoff_zone_label`), computed in the warehouse from the fixture's venue; the site prints them and converts nothing.
  - A venue has a time zone: a warehouse table of venues (2,492 distinct venue ids on `stg_apif__fixtures_next` today) with an IANA zone derived from the venue's city and country, tested not-null for every venue a fixture references.
  - A fixture with no venue (18,238 of 64,552 today — qualifiers and cups mostly) falls back to its competition's zone from the registry, and the row still shows a zone label; a fixture with neither shows UTC and says so.
  - `mart_next_matchday` (and the fixture-page payload) serve the two columns; Home and the competition page render them; the date heading per day uses the local date.

approved_design:
  - home: #127
  - competition: #129
  - matches: #130
  - match: #132
  - team: #134

depends_on:
  - none: main 2d37dc8b holds every model this change reads; no open MR changes fct_fixture

shared_files:
  - none: no design baseline, chart manifest or chart pin is edited by hand; a baseline the local CI run reports as drifted is regenerated, never hand-merged

decisions_taken: >
  The shape agreed with the CPO on 2026-09-14 (issue #146, comment): `dim_venue`, a default zone per
  country (the `country_time_zones` seed, published on `dim_country`), a seed of venue-level overrides for the countries that span zones, `dim_timezone`
  to refuse a typo, `fct_fixture` serving `kickoff_local` and `kickoff_zone_label`. Facts measured
  on 2026-11-20 that shaped the build: (1) BigQuery prints a zone as `UTC+2`, never as `CEST`, so
  `dim_timezone` also carries the conventional abbreviation for standard and daylight time where one
  exists, and a zone without one prints `UTC+N` from BigQuery itself; daylight time is read from the
  zone's offset at the kick-off against its lowest offset of that year. (2) The fixtures do not carry
  a venue country: a venue's country is the `league_country` of the competitions its
  fixtures belong to, else the `dim_team.team_country` of a team whose home ground it is, else the
  country most home teams of its fixtures belong to; the order is the one with the fewest wrong
  venues in the measured 2,545 (the venues where the orders differ are listed in the seed). (3)
  The overrides are keyed by venue id, because a city name is ambiguous (Saint-Denis is a Paris
  suburb and a town in Reunion). (4) A country that spans zones has no default zone, so its venues
  without an override fail the not-null test instead of taking a wrong zone. (5) The competition
  fallback reads `dim_league.league_country`, not a registry field: the registry is ingest
  configuration. The label of a fixture with no zone is `UTC`. No new dependency, no recurring cost.
  (6) The venue's country is resolved in `base_apif__venues`, not in core: layering.md's "Entity
  requiring cross-source resolution" rule names the venue across `/teams` and `/fixtures` as base
  work. (7) Docs follow the code in the same branch: layering.md's dimension inventory,
  00_overview.md's timezone convention and 10_home.md's kick-off row state the served clock; none
  is a core document of §10. (8) The Matches page stays on the UTC day and the UTC clock, as the
  issue's text defers it ("the Matches page will too"): `MatchesDay.astro` strips the two served
  columns from its rows. (9) `fixture_order` follows `kickoff_local` so that a list printed under
  local-date headings is in heading order; it changes the order of rows only where one competition's
  fixtures sit in different zones.

decisions_reserved:
  - The label wording for a zone with no conventional abbreviation (built as `UTC+N`, for example `UTC+3` in Riyadh): user-visible wording, for the CPO to confirm or replace in the same MR.
  - The match page's Masthead prints `time UTC` still; its design (#132) is not changed by this task.
  - Whether a Matches day page is keyed on the venue's local date instead of the UTC date, which changes the date of `/{locale}/matches/{yyyy-mm-dd}/`, the day pages' row sets and their links (path A, as built: the Matches page stays on UTC; path B: `mart_match_days.match_day` becomes `date(kickoff_local)` and the page prints the venue clock). Recommendation: path B once the CPO confirms the URL date, because a reader sees one clock sitewide; until then path A leaves no page contradicting itself.

done_when:
  - dbt parse passes and dbt ls --select dim_venue+ lists fct_fixture's readers.
  - python scripts/check_layer_contract.py and scripts/check_description_hygiene.py pass.
  - python -m pytest tests/test_kickoff_clock_146.py tests/test_export_landing.py tests/test_export_matches.py tests/test_export_site_data.py passes.
  - node --test site_v2/src/lib/format.test.mjs passes.
  - python scripts/ci_local.py --mr is green and the MR pipeline is green.
  - python scripts/merge_ready.py <iid> says ready.
