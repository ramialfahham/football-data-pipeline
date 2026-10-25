# Task contract — the competition page's season label, served by the warehouse

objective: >
  The competition page header's meta line shows the season as the warehouse serves it: "Season
  2026/27" for a split-year competition, "Season 2026" for a calendar-year one ("Saison", "Kausi"),
  on every competition with a payload. The label is a column of dim_competition_season, built from
  the registry's season_type; the export carries it and no page computes it.

refs: >
  #229 (one way to show the season; the competition page's header text approved in chat,
  2026-10-22, note 4066426889); #129 (the competition page, design approved); #233 (the country in
  the page's language, split off, decided in chat, 2026-10-25).

scope_paths:
  - dbt_project/models/3_core/dim_competition_season.sql
  - dbt_project/models/3_core/core.yml
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - site_v2/src/components/competition/CompetitionHeader.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/index.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/[[]matches]/index.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/[[]stats]/index.astro
  - site_v2/src/lib/types.ts
  - site_v2/src/specs/competition/index.spec.json
  - site_v2/src/specs/competition/matches/index.spec.json
  - site_v2/src/specs/competition/stats/index.spec.json
  - site_v2/src/data/competitions/BL1/2026.json
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: dim_competition_season gains season_label (a join of the competition_registry seed);
  the export's competitions target gains season_label per payload, read from
  core.dim_competition_season. downstream: `dbt ls --select dim_competition_season+ --resource-type
  model` lists 15 models: dim_competition_season, dim_player_team_season_mapping, fct_standings,
  int_team_season__deserved_vs_actual, int_team_season__standings_primary,
  mart_competition_fixtures, mart_fixture_standing_context, mart_match_days,
  mart_matchday_insights, mart_next_matchday, mart_roster, mart_standings, mart_team_profile,
  mart_team_season, mart_team_season_insights; 5 leaves (mart_match_days,
  mart_matchday_insights, mart_roster, mart_team_profile, mart_team_season_insights). The two
  direct SQL readers, dim_player_team_season_mapping and fct_standings, select named columns
  (season_sk, league_sk, league_code, season_api_year), so the new column reaches no model; all
  14 rebuild in the MR data build unchanged. The site: the competition header on the
  Overview, Matchdays and Rankings pages. layer_rules: a core attribute of the season, no fact
  computed; the export reads a served column. deploy_order: the column reaches prod with the
  nightly after merge; the export carries it on the next deploy:export; deploy:site-v2 is manual.
  blast_radius: the competition header's meta line; a null label drops the season part, as a
  null season does today.

approved_design:
  - competition: #129

acceptance_criteria:
  - "dim_competition_season serves season_label: split_year as YYYY/YY (2026/27), calendar_year as YYYY (2026); not null and of that shape, asserted by dbt tests."
  - "Each competitions/{league_code}/{season}.json carries season_label as served; the export computes nothing."
  - "The competition header's meta line reads region · Season <label> · round (Saison, Kausi) on the Overview, Matchdays and Rankings pages; no page formats the year."

decisions_taken: >
  Approved in chat, 2026-10-22: the season label as plain text in the header's meta line, from the
  registry's season_type, on every competition. The plan approved in chat, 2026-10-25, with the
  country names split to #233. Readings: a competition without a payload shows no season's data
  and so no season; the label is a core attribute so every page reads one definition. No new
  dependency; the recurring cost is a join of a 48-row seed.

decisions_reserved: []

done_when:
  - dbt parse, SQLFluff, the offline gates, check_description_hygiene.py, pytest and the site node tests pass.
  - A local build on the sample shows Season 2026/27 on the Bundesliga in EN, DE and FI.
  - The MR data build passes, including the season_label tests.
  - Reviewers per review_routing.json pass.

amendments: []
