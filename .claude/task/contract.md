# Task contract — #177, part 2: metric names without sigils, from one place

objective: >
  Every metric name on the site comes only from site_v2/src/i18n/strings.ts and carries no Ø or %:
  a value averaged over several matches shows "per match" on a second line, a share without a
  football word of its own shows "percentage". The approved English, German and Finnish names
  replace today's. The catalogue's label_en column is removed.

refs: >
  #177 (the metric catalogue): names without Ø or %, label_en removed, names only in strings.ts;
  the name list, the second-line words, the acceptance criteria and the document text approved in
  chat, 2026-10-07.

acceptance_criteria:
  - On every built page (match, team, Rankings, Home), no metric name carries "Ø" or "%", in any language.
  - A row whose value is an average over several matches shows "per match" (DE "pro Spiel", FI "ottelua kohden") on its second line. A share without its own football word shows "percentage" (DE "in Prozent", FI "prosentteina") wherever it appears. A single match's values carry no "per match".
  - Every name shown matches the approved list in all three languages, and strings.ts is the only place any metric name exists.
  - The catalogue has no label_en column, and every seed, label and copy check passes.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/docs/metric_rules.md
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/metricRows.ts
  - site_v2/src/components/fixture/MetricRow.astro
  - site_v2/src/components/team/MetricLeagueRow.astro
  - site_v2/src/components/team/MetricSeasonRow.astro
  - site_v2/src/components/team/TeamPerformance.astro
  - site_v2/src/components/team/DeservedHero.astro
  - site_v2/src/components/competition/RankingBoard.astro
  - site_v2/src/components/home/TopTeams.astro
  - site_v2/src/styles/system.css
  - site_v2/scripts/check-metric-labels.test.mjs
  - scripts/export_site_data.py
  - docs/metric_layer.md
  - docs/wireframes/metrics_display.md
  - docs/wireframes/10_home.md
  - docs/wireframes/01_fixture_page.md
  - docs/wireframes/02_team_profile.md
  - docs/wireframes/14_team_stats.md
  - docs/wireframes/03_player_profile.md
  - docs/wireframes/12_player_stats.md
  - design-mocks/gen_home.py
  - design-mocks/gen_home_with_rules.py
  - design-mocks/gen_competition_teams.py
  - design-mocks/top_teams_mock.html
  - design-mocks/top_players_mock.html
  - design-mocks/gen_top_teams.py
  - design-mocks/gen_top_players.py
  - design-mocks/check_players.py
  - design-mocks/check_teams.py
  - tests/test_sentence_length_in_docs.py
  - tests/test_no_decision_history_in_code.py
  - tests/test_no_decision_history_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md

impact_map: >
  writers: metric_catalogue.csv by hand; strings.ts by hand. No model is changed.
  downstream: the catalogue seed loses one column. `grep -rn "label_en"` over dbt_project/,
    scripts/, tests/, site_v2/src/ and design-mocks/ (excluding the competition_types and
    confederations seeds, whose own label_en column is unrelated) finds, before this change:
    seeds/schema.yml (the column entry and the entity+label_en unique test), metric_rules.md:4,
    two comments in export_site_data.py, two comments in strings.ts, gen_top_teams.py and
    gen_top_players.py (the only code readers), check_players.py/check_teams.py comments;
    dbt_project/models/**/*.sql: none (`dbt ls` lineage of a seed column with no model reader is
    empty). No dbt model or test SQL reads the column. The two generators move to strings.ts; the
    three generators that import them (gen_home, gen_home_with_rules, gen_competition_teams)
    follow. Site: every surface that renders a
    metric name (Form comparison rows, team page rows and hero tiles, Rankings boards, Home boards).
  layer_rules: the catalogue keeps identity, formula, direction, format and label_i18n_key; names
    stay frontend copy in strings.ts (docs/metric_layer.md, metrics_display.md).
  deploy_order: the seed rebuilds with the nightly; the site changes on the next manual deploy.
  blast_radius: the names on every page; no number changes.

decisions_taken: >
  The names, the second-line words, the acceptance criteria and the document text are approved in
  chat, 2026-10-07. Readings: "per match" is decided by the value being a per-match average (the
  board payload's per_match from the catalogue; metricRows.ts carries it for its rows until the
  next #177 MR removes that file's copies); "percentage" is a naming fact and lives in strings.ts
  with the names, as the list of shares without a word of their own. The German player label for
  saves follows the approved team name. Names asked by no surface today are added when a surface
  renders them (check-metric-labels allows no unrendered label); about 70 catalogue metrics no page
  shows therefore have no name until one does, accepted in chat, 2026-10-07. The Form comparison's
  "tackles + interceptions + blocks" caption leaves, as #166 rules ("no Defending sub-label",
  approved on #132); the team page keeps its served T · I · B figures after "per match". The
  site's per-match flags and its list of shares named by their count are pinned to the catalogue
  by a test until the next #177 MR serves them from the export. The legacy byte-identity test
  against the retired site's labels is removed: the ruled names now differ from it.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - Order, direction and format from the catalogue: the next #177 MR.

done_when:
  - dbt parse clean; pytest tests/ passes; npm test in site_v2 passes; check_copy_gate passes.
  - astro build of the committed sample; the built pages show the approved names and second
    lines, no Ø or % in any metric name (evidence per criterion).

amendments:
  - 2026-10-07: German team-page copy — authority: CPO in chat, 2026-10-07; content: heroVerdictUnder,
    heroVerdictOver, heroCaption and axPlay say "Differenz der Schüsse aufs Tor" / "Differenz Schüsse
    aufs Tor / Spiel" for "Torschussdifferenz", as approved word for word.
  - 2026-10-07: + tests/test_no_decision_history_in_code.py, tests/test_no_decision_history_in_docs.py
    — authority: CPO in chat, 2026-10-07; content: their pins lowered to the counts this change
    leaves (history lines removed; the pins only move down).
  - 2026-10-07: + the three wireframes 01_fixture_page.md, 02_team_profile.md, 14_team_stats.md —
    authority: CPO in chat, 2026-10-07; content: each metric name in them becomes the metric's key
    and a pointer to strings.ts, so no document holds a second copy of a name.
  - 2026-10-07: + docs/wireframes/03_player_profile.md and 12_player_stats.md — authority: CPO in
    chat, 2026-10-07; content: the same conversion; the Home wireframe's live lines follow it.
  - 2026-10-07: + design-mocks gen_home.py, gen_home_with_rules.py, gen_competition_teams.py and the
    two mock outputs — authority: CPO in chat, 2026-10-07; content: the Home mock generators and
    check_teams.py take the name and "per match" as the site does, and run.
  - 2026-10-07: EN and DE seoCompetitionStatsDesc and compDeservedExplainer say "shots on target" /
    "Schüsse aufs Tor" — authority: CPO in chat, 2026-10-07, approved word for word.
