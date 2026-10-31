# Task contract — club regions on the Teams page

objective: >
  Five clubs the provider files under a wrong country get their real country from a correction
  row (Dragon, Al Shorta, Cano Sport, GR / SIAF, 15 de Agosto), and the correction seed records
  the country it replaces so the warn test flags a row only when the provider changes it. A club
  with no region of its own takes its country's, and a country none of whose clubs has a region
  takes its national team's, so Auckland City is filed under Oceania.

refs: >
  #239, nine clubs with a missing or contradicting region (decisions and exact texts approved in
  chat, 2026-10-31; this MR's plan approved in chat, 2026-10-31). The three clubs sharing a
  provider id with a namesake (Newmarket, Victoria United, Warriors FC) go to #238.

scope_paths:
  - dbt_project/seeds/team_country_corrections.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_team_country_corrections_still_needed.sql
  - dbt_project/models/5_marts/shared/mart_team_index.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  `.venv/Scripts/dbt.exe ls --project-dir dbt_project --select team_country_corrections+
  mart_team_index+ --resource-type model` lists base_apif__teams_global, dim_team,
  dim_player_team_season_mapping, mart_competition_fixtures, mart_fixture_standing_context,
  mart_leaderboards, mart_match_days, mart_matchday_insights, mart_player_career,
  mart_player_fixture_stats, mart_player_profile, mart_roster, mart_standings,
  mart_team_competition_benchmarks, mart_team_competitions, mart_team_fixtures, mart_team_index,
  mart_team_leaderboards, mart_team_market_value, mart_team_momentum_window, mart_team_profile,
  mart_team_season, mart_team_season_insights.
  The seed's five rows change team_country for five teams wherever a model carries it; the new
  column is read only by the warn test. The mart_team_index change moves only clubs with no
  region: on prod today that is Auckland City alone (checked 2026-10-31).
  blast_radius: five teams' country on every page that shows it; Auckland City's region and New
  Zealand's country region on the Teams page.

decisions_taken: >
  Approved in chat, 2026-10-31: the five corrections with their sources and notes; the new
  provider_country column and the warn test's rule; the region rule for clubs and countries with
  no region; the exact texts in seeds/schema.yml and shared.yml; the three shared-id clubs left
  to #238.

decisions_reserved:
  - "none: every decision of this task is approved, see decisions_taken"

acceptance_criteria:
  - "The five teams carry their corrected country in dim_team; each seed row cites an official page that lists the team with that country."
  - "The warn test flags a correction row only when the provider's latest country differs from the row's provider_country (empty counts as none); the 78 existing rows behave as before."
  - "In mart_team_index, a club with no region takes its country's region, and a country none of whose clubs has a region takes its national team's; on prod data the only change is Auckland City's region_key and New Zealand's country_region_key, both OFC."

done_when:
  - dbt parse, SQLFluff on the changed SQL, pytest and the offline gates pass.
  - The compiled mart, run on prod data, differs from prod mart_team_index only in Auckland City's region_key and country_region_key.
  - The provider's country for each of the five ids equals the row's provider_country.
