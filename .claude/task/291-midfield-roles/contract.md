# Task contract — Midfield roles: defensive, central and attacking midfielders

objective: >
  Issue #291. A midfielder's role (DM, CM or AM) is read from his line on the grid in each match he
  played, as a starter or in the slot he took as a substitute; his season role is the most frequent
  of those, and the Player page compares him with the players of the same season role in each
  competition. The Player header and the Players index row name the role; the Team squad groups keep
  the four positions. With it: the three-step position rule on the page profile (#183 residual), the
  Player page explainers without the page's own player, and the Finnish squad legend.
refs: "#291 (CPO decisions approved in chat, 2026-11-13 and 2026-11-14); #183; Player page design #136; Players page design #135"

scope_paths:
  - .claude/task/291-midfield-roles/**
  - dbt_project/models/2_base/api_football/base_apif__lineups.sql
  - dbt_project/models/2_base/api_football/base_apif__lineup_sheets.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture_lineup.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_player__page_profile.sql
  - dbt_project/models/4_intermediate/shared/int_player_page.yml
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/macros/player_benchmark_metrics.sql
  - dbt_project/models/5_marts/shared/mart_player_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/mart_player_index.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/tests/assert_lineup_midfield_role_follows_the_grid.sql
  - dbt_project/tests/assert_player_season_midfield_role_is_most_frequent.sql
  - dbt_project/tests/assert_player_page_position_follows_the_rule.sql
  - dbt_project/tests/assert_player_peer_pools_follow_the_season_role.sql
  - dbt_project/tests/assert_player_metrics_follow_catalogue_formula.sql
  - dbt_project/tests/assert_played_midfielders_have_a_role.sql
  - dbt_project/tests/assert_lineup_fetch_keeps_grid_only_for_same_eleven.sql
  - dbt_project/tests/assert_no_uncatalogued_season_metric.sql
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - tests/test_midfield_roles.py
  - site_v2/src/i18n/strings.ts
  - site_v2/src/styles/system.css
  - site_v2/src/lib/types.ts
  - site_v2/src/lib/playerPage.ts
  - site_v2/src/lib/playerIndex.mjs
  - site_v2/src/lib/playerIndex.test.mjs
  - site_v2/src/components/player/PlayerHeader.astro
  - site_v2/src/components/player/PlayerComparison.astro
  - site_v2/src/components/player/PlayerIndexRow.astro
  - site_v2/src/pages/[[]lang]/[[]players]/[[]player].astro
  - site_v2/src/data/players/*.json
  - site_v2/src/data/player_peers/**
  - site_v2/src/data/players_index.json

impact_map: >
  writers: base_apif__lineup_sheets (new base table: each team's chosen fetch, the earlier fetch's
  grid places, the parsed sheet and the shirt pairing, one row per sheet player; base_apif__lineups
  reads it, so its sheet checks plan inside BigQuery's limit, and nothing else reads it),
  base_apif__lineups (adds midfield_role), fct_fixture_lineup (passes it),
  int_player_season__metrics (adds the season midfield_role), int_player_season_position__metrics
  (MID rows take the season role), int_player__page_profile (position rule, position_role), mart_player_competition_benchmarks (page filter on the four groups),
  mart_player_profile and mart_player_index (pass position_role), macro player_benchmark_metrics
  (DM, CM and AM beside MID).
  downstream: `dbt ls --select base_apif__lineups+ --resource-type model` → 61 models, marts:
  mart_competition_fixtures mart_leaderboards mart_match_days mart_matchday_insights
  mart_player_career mart_player_competition_benchmarks mart_player_fixture_stats mart_player_index
  mart_player_momentum mart_player_profile mart_player_season_record mart_player_squad_benchmarks
  mart_player_window_metrics mart_roster mart_team_competition_benchmarks mart_team_competitions
  mart_team_index mart_team_leaderboards mart_team_momentum_window mart_team_page_window_metrics
  mart_team_profile mart_team_season mart_team_season_insights mart_team_season_record
  mart_team_window_metrics. midfield_role is read only by int_player_season__metrics. The earlier
  fetch's grid places and formation reach every reader of grid_position and team_formation (the
  match page line-up, the winger mapping by grid row) for the sheets whose latest fetch has none and
  whose earlier fetch names the same starting eleven: 132 team sheets in 18 competitions, measured on
  prod 2026-11-14. Their bench, substitutions, minutes and line-up state are unchanged. `int_player_season__metrics+` → mart_leaderboards mart_player_index
  mart_player_profile. `int_player__page_profile+` → int_player_page__window_seasons
  int_player_squad_window__metrics int_player_window__metrics mart_player_competition_benchmarks
  mart_player_fixture_stats mart_player_index mart_player_profile mart_player_squad_benchmarks
  mart_player_window_metrics mart_team_momentum_window. `int_player_season_position__metrics+` →
  int_player_competition_benchmark_metrics_long int_player_competition_benchmarks
  mart_player_competition_benchmarks; the singular test assert_player_metrics_follow_catalogue_formula
  recomputes it at its grain.
  layer_rules: base holds the grid rule (first logic, beside the line-up code mapping);
  intermediate aggregates; marts pass columns. check_layer_contract.py, no partition_by/cluster_by.
  deploy_order: additive columns and new values; no table is dropped or renamed. The site reads
  position_role when present and falls back to position_group, so the deployed site keeps working
  between merge and the next export.
  blast_radius: position_group stays GK/DEF/MID/ATT on int_player__page_profile, mart_player_profile
  and mart_player_index, so mart_roster, the Players index groups and filters, the squad and window
  benchmarks and the leaderboards' outfield filter are unchanged. The peer pool key
  (position_group of int_player_season_position__metrics, int_player_competition_benchmarks and
  mart_player_competition_benchmarks) gains DM, CM and AM: a midfielder's benchmark rows, ranks,
  medians and pool counts change to his season role's pool. Measured on prod, current seasons:
  BL1 2026 midfielders 99 → DM 14, CM 59, AM 26.

acceptance_criteria:
  - The built Player page of a midfielder whose payload carries position_role DM names the role in the header (EN "Defensive midfielder", DE "Defensiver Mittelfeldspieler", FI "Puolustava keskikenttäpelaaja") and its competition intro reads "Compared with the {n} defensive midfielders who played at least 270 minutes in {competition} {season}." (DE "Im Vergleich der {n} defensiven Mittelfeldspieler, …", FI "Suoritusta verrataan niihin {n} puolustavaan keskikenttäpelaajaan, …").
  - The CM and AM labels render as approved in all three languages (EN central/attacking midfielder; DE Zentraler/Offensiver Mittelfeldspieler; FI keskikentän keskustan pelaaja, hyökkäävä keskikenttäpelaaja), shown by the strings test and one built page.
  - Every midfielder who played and is in a comparison pool (270 minutes or more in a competition-season) or has a built Player page carries DM, CM or AM. A singular test with severity error fails on any one without, and no such player's built page shows "Midfielder".
  - No explainer on the built Player page contains the page's own player name; the four intros read as in decisions_taken.
  - The FI squad legend of a multi-word team reads "Muut Bayern München -pelaajat".
  - A Players index row of a player with a role reads "<role label> · <club>"; the Players page position filter keeps the four groups; the Team page squad keeps its four group headings.
  - At 260, 280, 320 and 375px in EN, DE and FI the Player page header's position item never passes the column, no "·" starts a line, and nothing in the page body is clipped.

approved_design:
  - player: #136
  - players: #135

decisions_taken: >
  CPO, approved in chat 2026-11-14 (#291): add CM; EN/DE labels as in the mock; FI DM "puolustava
  keskikenttäpelaaja", CM "keskikentän keskustan pelaaja", AM "hyökkäävä keskikenttäpelaaja"; the
  finer label in the Player header and the Players index row, and in the comparison legend as the
  approved mock shows it ("Name · Defensive midfielder", "Other defensive midfielders"); the page
  title and meta description keep the position group; Team squad groups unchanged; no pool
  minimum — a player is always compared within his season role, the intro shows the pool count.
  Role rule as measured for #291: a starter's line is his grid row minus one within the formation;
  one midfield line → CM; with two or more, the lowest is DM when it holds one or two players, else
  CM; the highest is AM when it holds one to three, else CM; any line between → CM; a provider
  midfielder on the defence line → DM, on the attack line → AM.
  Evidence first (CPO, approved in chat 2026-11-14): a role is what the player played that season.
  A starter's line is his own; a substitute takes the line of the player he replaced, followed back
  to the starter. A starter the sheet names no position for counts when his stats line codes him M
  (CPO, approved in chat 2026-11-14). Confirmed or researched team sheets count. Each part of a
  sheet is judged by its own checks: the starters of a sheet that failed only the substitutions
  and/or squad_lists checks count; its bench and substitutions do not (CPO, approved in chat
  2026-11-14). fct_fixture_lineup carries failed_checks for it. When a team's
  latest fetch has no grid places, its starters take the grid places, and the sheet the formation,
  of the latest earlier fetch that has them, only if both name the same starting eleven; nothing
  else comes from the earlier fetch (CPO, in chat 2026-11-14: discarding a stored fetch's grid
  places is a defect).
  Season role: most frequent over those matches, then the latest match, then the code. A midfielder
  with no role from that season's evidence takes his most frequent role across his other seasons
  (any competition, counted over matches); a tie goes to the role of the nearest season, then the
  earlier season (CPO, approved in chat 2026-11-14). midfield_role_from says which: this_season or
  other_seasons; the page shows both the same way.
  Every midfielder who played and is in a comparison pool or has a built Player page must carry a
  role (coordinator, 2026-11-14); a bench-only midfielder needs none. The ones left without a role
  in any season are filled through the researched sheet, in a separate research task; this MR
  merges only once assert_played_midfielders_have_a_role is green.
  Engineering calls (coordinator, 2026-11-13): the peer pool is the season role and the values are
  all the player's midfield matches; the Player header's position item may wrap inside itself.
  Position rule (#183 residual, ruled with #277's rule): most frequent position in the season, then
  the most recent match, then the code. #256 stays with the CPO; nothing of it is built here.
  assert_player_metrics_follow_catalogue_formula.sql recomputes the pool model's grain, so its
  midfield rows take the season role from int_player_season__metrics as the model does.
  The finer position is carried as position_role next to position_group (GK/DEF/MID/ATT) on the
  page profile, the profile mart and the index mart, per match on fct_fixture_lineup and per
  competition-season on int_player_season__metrics. dim_player is unchanged: the role is a property
  of a season, not of the player, and layering.md's dimension rule keeps an attribute off a dim that
  no reader shares.
  The explainers without the page's own player follow the #230 rule (coordinator, 2026-11-14):
  playerPeerIntro, playerSquadClubIntro, playerSquadNationalIntro and playerLastSeasonIntro, EN, DE
  and FI, as shown in the mock. The FI squad legend passes the team through teamBeforeCompound.
  Thresholds: no new mechanism, no recurring cost (columns on existing models; no new model, seed,
  schedule or dependency).

decisions_reserved:
  - none: every fan-visible choice in this task is decided above (labels, pools, pages); a new one that surfaces goes to the coordinator, unbuilt.

done_when:
  - dbt parse passes; sqlfluff lint of every changed model clean against main's baseline
  - full pytest passes; site_v2 node --test passes
  - the five singular tests pass in data:build:mr, with the build green (the role-coverage test after the research task fills the gaps)
  - acceptance_evidence.md demonstrates every acceptance criterion from the built output

amendments:
  - 2026-11-14: + the stats-line midfielder — authority: CPO, approved in chat 2026-11-14; content: decisions_taken, "Evidence first".
  - 2026-11-14: + the starters of a sheet that failed only the substitutions or squad_lists checks; fct_fixture_lineup carries failed_checks — authority: CPO, approved in chat 2026-11-14 (each part of a sheet by its own checks); content: decisions_taken, "Evidence first".
  - 2026-11-14: + the earlier fetch's grid places and formation for the same starting eleven, with its test — authority: CPO, in chat 2026-11-14 (discarding them is a defect); content: decisions_taken, "Evidence first"; impact_map, the 132 sheets.
  - 2026-11-14: + the role from other seasons for a midfielder without one this season, and midfield_role_from — authority: CPO, approved in chat 2026-11-14; content: decisions_taken, "Season role".
  - 2026-11-14: + assert_no_uncatalogued_season_metric.sql — authority: the coordinator's engineering calls of 2026-11-14 (the role columns on int_player_season__metrics); content: midfield_role and midfield_role_from join its non-metric columns, as starts and minutes are.
  - 2026-11-14: the site-commit round also carries the two-literal syntax fix to assert_lineup_fetch_keeps_grid_only_for_same_eleven.sql — authority: coordinator, 14 Nov 2026; content: two problem labels lose their doubled apostrophes, which BigQuery rejects.
  - 2026-11-14: + base_apif__lineup_sheets.sql (round 7) — authority: CPO, approved in chat 2026-11-14 (one more review round); the split is the coordinator's engineering call of 2026-11-14; content: the parsed team sheet moves into its own base table and base_apif__lineups reads it, because the one query was too complex for BigQuery to plan; rules and output unchanged. The same round removes the header wrap rule from system.css: the position item in PlayerHeader carries no nowrap class instead.
