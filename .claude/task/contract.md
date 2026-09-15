# Task contract — #149: the competition page's Overview tab, built to #129

objective: >
  Build the Overview tab of the competition page (`/{lang}/{competition}/`) as approved on #129
  (CPO, 2026-09-14/15) and filed as #149: header (crest · name · region · season · round), the
  tab bar (Overview active; Matchdays · Teams · Players inert until built), the Table with the
  provider's goals column and a table kind, Next matches (Home's block for one competition),
  Deserved points (two three-row boards from `mart_team_profile`), The season in numbers (fact
  rows from a new competition-season summary mart and a "match that matters" flag on
  `mart_next_matchday`). The mock generator, the design chain and two documents are corrected to
  the approved design in the same MR. The open dependencies (#105 season label, #145 sentence,
  #146 venue clock, #148 round phase, #69 country key) stay out: the header shows the served
  season year and the provider's round text, kickoffs render as today, no sentence.

refs: >
  #129 (the approved design, its notes 2026-09-14/15 and the data-model table in its
  description); #149 (the build issue; its checklist is `acceptance_criteria` below); #127
  (Home's rulings the shared blocks carry); the plan approved in this session.

scope_paths:
  - dbt_project/models/1_staging/api_football/stg_apif__standings.sql
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/2_base/api_football/base_apif__standings.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_standings.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/5_marts/shared/mart_standings.sql
  - dbt_project/models/5_marts/shared/mart_next_matchday.sql
  - dbt_project/models/5_marts/shared/mart_competition_season_summary.sql
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__deserved_vs_actual.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/seeds/standings_table_kinds.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_every_standings_section_has_a_table_kind.sql
  - dbt_project/tests/assert_one_match_that_matters_per_competition.sql
  - dbt_project/tests/assert_competition_season_summary_is_consistent.sql
  - dbt_project/docs/layering.md
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - site_v2/src/pages/*/*/index.astro
  - site_v2/src/components/competition/*.astro
  - site_v2/src/lib/types.ts
  - site_v2/src/lib/competitionPayload.mjs
  - site_v2/src/lib/competitionPayload.test.mjs
  - site_v2/src/i18n/strings.ts
  - site_v2/src/styles/system.css
  - site_v2/src/specs/competition/index.spec.json
  - site_v2/src/config/indexability.mjs
  - site_v2/src/data/competitions/*/*.json
  - site_v2/src/data/teams/*.json
  - site_v2/src/data/fixtures/*.json
  - .gitignore
  - docs/metric_layer.md
  - docs/ui_design_brief.md
  - docs/wireframes/00_overview.md
  - docs/content_architecture.md
  - docs/site_architecture.md
  - design-mocks/gen_competition_hub.py
  - design-mocks/check_competition_hub.py
  - design-mocks/README.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: the standings chain is written by `stg_apif__standings` (json_value over
    RAW_APIF_STANDINGS) -> `base_apif__standings` (dedup) -> `fct_standings` -> `mart_standings`;
    `mart_next_matchday` and the new `mart_competition_season_summary` read `fct_fixture` /
    `int_legs__team_match` / `fct_standings`; the export (`scripts/export_site_data.py`) writes
    `competitions/{league_code}/{season}.json`; the page reads the committed copies.
  downstream: `dbt ls --select stg_apif__standings+ --resource-type model` (run this session):
    base_apif__standings base_apif__teams base_apif__teams_global dim_player_team_season_mapping
    dim_team fct_standings int_team_season__deserved_vs_actual int_team_season__standings_primary
    mart_fixture_standing_context mart_leaderboards mart_matchday_insights mart_player_career
    mart_player_fixture_stats mart_player_match_log mart_player_profile mart_roster mart_standings
    mart_team_competition_benchmarks mart_team_fixture_stats mart_team_fixtures
    mart_team_leaderboards mart_team_market_value mart_team_momentum_window mart_team_profile
    mart_team_season mart_team_season_insights — all ADDITIVE (two new columns and one new
    column; no column changes value, no grain changes; every reader selects named columns or
    `select *` into a projection). `dbt ls --select mart_next_matchday+` -> mart_next_matchday
    only (leaf; one added boolean). The new mart is a leaf.
  layer_rules: json extraction stays in staging (core forbids json_value/unnest); base lists
    every column twice (src CTE + final); no per-model materialisation in staging/base; the new
    mart reads intermediate + core, not another mart; no league_code in business logic (the
    table-kind patterns are a seed over section names, not competitions); every model keeps a
    schema test and a description under the hygiene limits.
  deploy_order: additive columns and a new table — the deployed models keep working until the
    nightly rebuilds them (`fdp-nightly`, 04:00 UTC); the export runs after and the page reads
    committed data, so no window shows a half-built state. No backfill: the standings payload
    has always carried `$.all.goals`.
  blast_radius: `mart_standings` gains goals_for/goals_against/table_kind (nulls for goals only
    where the provider row lacks them); `mart_next_matchday` gains is_match_that_matters; the
    new mart is read by the export only. No served number changes.

acceptance_criteria:
  - The built page at /en/bundesliga/ (and /de/, /fi/) renders, in this order, the header (crest, name, region · season year · round text), the tab bar (Overview active; Matchdays, Teams, Players present without an href), TABLE, NEXT MATCHES, DESERVED POINTS, THE SEASON IN NUMBERS; shown by the rendered DOM in rendered_page_evidence.md.
  - The table's column headings read # · P · W · D · L · Goals · GD · Pts with one crest-and-club cell per row; Freiburg's row reads 3 3 0 0 10:1 +9 9; every row is one <a class="ctab-row"> linking to /en/teams/{slug}/; at 375px the W, D, L and Goals cells are display:none and the heading cells sit at the same x as the row cells.
  - Next matches shows every row of the competition's next matchday from the payload as <a class="fxrow"> links to /en/{competition}/matches/{slug}/, with no competition heading and no fold.
  - Deserved points shows the explanation paragraph, then "Better than the table says" with three rows ordered by deserved_points_gap ascending (Mainz first, Diff "−2.7") and "Worse than the table says" with three rows ordered descending (Dortmund first, Diff "+2.7"); Diff is the bold cell.
  - The season in numbers renders one .frow per non-null fact with label, value and context; for BL1 2026: Goals per match "3.9" / "104 goals in 27 matches", Biggest margin "0–5" / "Hamburger SV vs 1. FSV Mainz 05, <the served round text>" (the earliest of the season's three 5–0s, per the #129 tie rule "ties on a margin or a goal count go to the earlier fixture"); the two played-match facts carry no link (a played match has no page on this site, the #129 ruling "played matches have no page"); the run facts link to the first team named and the match that matters links to its fixture page; no .frow exists for a fact whose value is null.
  - A competition with no standings renders no TABLE section; a competition with no deserved points renders no DESERVED POINTS section; a competition with no next matchday renders no NEXT MATCHES section (shown on one cup and one tournament page in the evidence).
  - `node --test` and `node scripts/check-page-specs.mjs` pass in site_v2; the competition spec has `stub` removed and lists the five marts; STUB_PAGES no longer lists the competition page.
  - `python scripts/check_copy_gate.py` passes with every new key in EN, DE and FI.

decisions_taken: >
  #129 (CPO, 2026-09-14/15), consolidated in its description: four tabs named Overview ·
  Matchdays · Teams · Players; the Overview order Table · Next matches · Deserved points · The
  season in numbers; the table's columns and source rule ("every column is the provider's
  official standings row as published; goals for/against from `$.all.goals`, never summed from
  fixtures"); groups as one table per section with the provider's ranking tables dropped and
  `table_kind` carried by the mart; the league-phase tables kept through the knockouts; Next
  matches as Home's block for one competition with no link under it; the Deserved points block
  with its explanation and two three-row boards; the seven fact rows and the fact-row block
  definition; the "match that matters" rule (lowest sum of table positions on the next matchday,
  ties to the earlier kickoff) as a warehouse flag; nothing renders empty; after the season
  everything but Next matches stays; the whole-row link rule (#129 note, site-wide) and the
  facts-versus-metrics rule written into their documents in this MR.
  CPO 2026-09-15 in this session (plan approval): the three unbuilt tabs ship inert (no href);
  the deserved-points gap keeps the catalogue's sign, actual minus deserved ("consistent with a
  forecast error"), and the page shows it that way (Mainz −2.7 under Better, Dortmund +2.7
  under Worse) — the earlier #129 note saying the opposite was corrected on the issue.
  Builder rules inside those rulings: (1) `table_kind` is a seed of section-name patterns
  (`standings_table_kinds.csv`), applied in `mart_standings`, with a fallback to `league` and a
  test that `league` never shares a season with `group` or `conference`; every one of the 300+
  section names in the warehouse today resolves (measured this session). (2) The summary mart
  computes the season's longest unbeaten and winless runs itself over `int_legs__team_match`
  (the team profile's streak columns are the CURRENT run, a different measurement). (3) Home
  wins and away wins are NULL for national-team competitions (`entity_type = 'national'`), the
  closest served fact to "no home wins at neutral venues" — the warehouse holds no venue
  neutrality; reserved below in case the CPO wants another rule. (4) Ties on the biggest
  margin and the most goals go to the earlier fixture; a run of one match is no run — the runs
  are NULL until some team has strung two matches together (seen on the cup render, where after
  one round every one of 36 clubs "held" a run of 1). (5) The page reads
  `competitions/{league_code}/{season}.json` and picks the latest season present — selection on
  a served number, no computation. (6) DE and FI copy for the new keys is a builder draft, listed
  in the MR head for the CPO.
  Threshold declarations: NO new mechanism (a seed, a mart, a flag column, Astro components on
  the existing pattern, one shared CSS rule) and NO recurring cost (the new mart is one small
  table in the nightly build; the export adds one query per mart it already reads).

decisions_reserved:
  - The URLs of the Matchdays, Teams and Players tabs: ruled with each tab's review on #129; this MR fixes none of them (the tabs are inert).
  - Whether "Home wins NULL for national-team competitions" is the rule the CPO meant by "no home wins at neutral venues", or whether cups with home ties in national-team competitions (Nations League) should carry it — escalate if a reviewer reads it as a §10 call.
  - German and Finnish wording of the new labels and the deserved-points explanation: drafted here, put to the CPO on the MR.
  - Whether the deserved-points fit is shown before a minimum of matchdays — the model question #129 records; not decided here (the block renders whenever the mart serves values).

done_when:
  - `.venv/Scripts/dbt.exe parse` clean; SQLFluff clean on every changed model; the three new singular tests written against core, each mutation-checked by inverting its predicate on a bq dry run of the compiled SQL.
  - `python -m pytest tests/test_export_site_data.py tests/test_export_landing.py tests/test_no_decision_history_in_code.py -q` green; `python scripts/check_copy_gate.py`, `check_description_hygiene.py`, `check_layer_contract.py`, `check_registry_var_sync.py`, `check_competition_type_seed.py`, `check_ui_i18n_metrics.py` all OK.
  - `cd site_v2 && npm test && node scripts/check-page-specs.mjs` green; the dev server renders /en/bundesliga/, /de/bundesliga/, /fi/bundesliga/, one cup and one tournament; `acceptance_evidence.md` demonstrates every criterion from the rendered DOM; `rendered_page_evidence.md` written.
  - `python design-mocks/gen_competition_hub.py` and `python design-mocks/check_competition_hub.py` green for the four kinds.
  - Review cycle run (scope-auditor, analytics-engineer-reviewer, platform-reviewer, bi-analyst-reviewer), `review.md` hash-bound, commit as the sole command, MR open with the #149 checklist ticked and the DE/FI copy listed.

amendments:
  - 2026-09-15: + site_v2/src/data/teams/*.json, site_v2/src/data/fixtures/*.json — authority: the
    standing sample rule in `.gitignore` ("every entity the committed sample points at needs its
    payload here, or CI goes red") under the #129/#149 rulings that every table row and every
    next-matchday row is a link; content: the 16 Bundesliga team payloads not already tracked and
    the 9 Matchday 4 fixture payloads the committed competition sample links to, allowlisted in
    `.gitignore`. No other file.
  - 2026-09-15: ~ acceptance criterion 5 (The season in numbers) — authority: two #129 rulings the
    first draft contradicted, "ties on a margin or a goal count go to the earlier fixture" (so the
    biggest margin is the season's earliest 5–0, Hamburg 0–5 Mainz, not the later Freiburg one the
    mock happened to show) and "played matches have no page" (so the two played-match facts carry
    no link); content: the criterion restated to those rulings, nothing else moved. Also declared
    in `decisions_taken` (4): a run of one match is no run.
  - 2026-09-15: + mart_team_profile.sql, int_team_season__deserved_vs_actual.sql,
    int_team_season.yml, metric_catalogue.csv, docs/metric_columns.md (generated) — authority: the
    CPO's answer in this session to the analytics reviewer's finding that the export sorted the
    deserved rows and the page took the ends ("The warehouse serves a rank"): `mart_team_profile`
    gains `deserved_points_gap_rank` (1 = the most negative gap, a total order with the team id as
    the tie-break, null exactly where the gap is null), a catalogue row beside `deserved_rank`;
    the export selects by the served rank and the page renders the order it is served. Content:
    that column, its catalogue row and generated docs block, its schema tests; the export's
    `sorted()` on the gap and the name tie-break removed.
