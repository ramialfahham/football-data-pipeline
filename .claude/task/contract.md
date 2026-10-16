# Task contract — the played match page

objective: >
  A played match gets its page (state 3): the export writes a payload for every played match and
  the match page renders it in the approved order (Breadcrumb, Header, Goals, Match leaders, Match
  stats, Line-ups, Next matches). Every played row that leads to a match then links to its page.
  The block standard, the fixture page wireframe and the design brief state the page.

refs: >
  #175, the played match page (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/175);
  #174, which matches get a page: option D, every played match in the data window
  (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/174). The renders are
  design-mocks/renders/played-match-page_2026-10-07_41.html and _42.html. The plan, the readings in
  decisions_taken and the acceptance criteria: approved in chat, 2026-10-15 and 2026-10-16.

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__lineups.sql
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/tests/assert_fixture_lineup_order_starters_first.sql
  - dbt_project/models/5_marts/shared/mart_head_to_head.sql
  - dbt_project/models/5_marts/shared/mart_competition_fixtures.sql
  - dbt_project/tests/assert_mart_head_to_head_meetings_are_fixtures.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - site_v2/src/lib/builtFixtures.mjs
  - site_v2/src/lib/builtFixtures.test.mjs
  - site_v2/src/lib/href.ts
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - tests/test_leaderboard_board_sets.py
  - tests/test_no_decision_history_in_code.py
  - tests/test_sentence_length_in_docs.py
  - site_v2/src/lib/format.ts
  - site_v2/src/pages/?lang?/?competition?/?matches?/?fixture?.astro
  - site_v2/src/components/fixture/*.astro
  - site_v2/src/components/ui/MatchRow.astro
  - site_v2/src/components/competition/RankingBoard.astro
  - site_v2/src/lib/types.ts
  - site_v2/src/i18n/strings.ts
  - site_v2/src/styles/system.css
  - site_v2/src/specs/competition/matches/fixture.spec.json
  - site_v2/src/data/fixtures/*.json
  - site_v2/scripts/check-built-pages.mjs
  - site_v2/scripts/check-built-pages.test.mjs
  - site_v2/scripts/check-metric-labels.test.mjs
  - docs/wireframes/block_standard.md
  - docs/wireframes/01_fixture_page.md
  - docs/wireframes/99_gaps_register.md
  - docs/ui_design_brief.md
  - docs/site_architecture.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: dbt builds base_apif__lineups from stg_apif__lineups and the seed
  fixture_lineup_corrections; scripts/export_site_data.py writes site_v2/src/data/fixtures/*.json;
  the Astro build writes the match pages.
  downstream: pasted output of `dbt ls --resource-type model --select base_apif__lineups+ --output
  name` on the branch's base: base_apif__lineups base_apif__players dim_player fct_fixture_lineup
  mart_competition_fixtures mart_leaderboards mart_match_days mart_player_career
  mart_player_competition_benchmarks mart_player_fixture_stats mart_player_profile mart_roster
  mart_team_momentum_window; `dbt ls --select mart_head_to_head+` lists mart_head_to_head alone
  (a leaf), and its recent_meetings gain the meeting's fixture as fixture_api_id. Only lineup_order's values for substitutes change; no model but
  fct_fixture_lineup and mart_player_fixture_stats carries that column. Outside dbt: the export
  gains the played payloads; the match route builds one page per payload and locale; MatchRow,
  RecentMatch and HeadToHead rows link a played match when its page is built, which changes the
  Matches page, the Matchdays tab and the next match page.
  layer_rules: the substitutes' order is base logic; the export selects and shapes served values
  only; the site renders what it is served (layering.md, Consumption layer). No new model.
  deploy_order: the warehouse change builds in data:build:mr; the export and the site build run
  in CI on the MR; deploy:site-v2 stays manual. No prod write.
  blast_radius: lineup_order changes on substitute rows only. ~60,000 played payloads and three
  locale pages each join the build; the export's size and the build's size and time are measured
  and put to the CPO before the MR is called ready.

acceptance_criteria:
  - "1. Payload: the export writes one payload for every played match (is_played) and copies served values only; unit tests show no value computed in Python; every next-match payload is byte-identical to main's except each head-to-head meeting gaining its fixture id."
  - "2. Block order: a played page shows Breadcrumb, Header, Goals, Match leaders, Match stats, Line-ups, Next matches, in that order; a block that does not apply is absent."
  - "3. Breadcrumb: Home › Competitions › {competition} › Matchdays|Rounds › {home} vs {away}, as on the next match page; a cup reads Rounds."
  - "4. Header, score and status: the competition's group head opens it; the final score stands where vs stood, the winner's number bold (winner_team_sk; neither on a draw); the status word is Full time, After extra time, After penalties or Awarded; no standing chip; under 700px each team's goals close its line."
  - "5. Header, penalties and awards: after penalties the big score is the shoot-out score, the score after extra time on the line under it; an awarded result shows its line under the score: The match was not played; the result was awarded. / Played {1–1}; the result was awarded {0–2} afterwards. / Abandoned at {1–0}; the result was awarded {3–0}."
  - "6. Goals: with minutes, one row per goal in served order: the score after the goal, the scorer with the crest of the side it counts for, a 14px line with the minute (45', 90+6') and the assist, Own goal or Penalty; each row links to the scorer's page when that page is built. Without minutes: the line The minutes of these goals are not recorded., then scorers home team first, no running score, 2 goals where it applies. Not recorded: the heading and Goal scorers are not recorded for this round. A 0–0 has no Goals block; a match awarded without being played has no Goals, Match leaders, Match stats or Line-ups."
  - "7. Match leaders: seven boards in catalogue order (Shots, Passes, Key passes, Dribbles attempted, Duels won, Defensive actions, Fouls), each up to three players in served order with the served rank, a shared count sharing the rank; the board name is not a link and has no chevron; rows link to the player's page when it is built; the intro The match's most notable players, across both teams., with no glossary link until #168; a board with no row is absent; no player stats: the heading and one line; one side missing: the boards and one line naming that side."
  - "8. Match stats: the Form comparison's element and rows without the Goals group, in catalogue order, no W/D/L pills, no per match line; a row neither side has is left out, a value one side lacks shows –; the intro Each team's numbers in this match.; no team stats: the heading and one line."
  - "9. Line-ups: each team under {team} · {formation} (the team name alone with no formation served), the eleven in served order, then Substitutes: the players who came on, in the order they came on; the second line {position} · off 73' or {position} · on 73' for {player}; {n} min on the right; rows link when the player's page is built; no line-up: the heading and one line."
  - "10. Next matches: each team's next match as on the next match page; last on the page."
  - "11. Played rows link: every played row on the Matches page, the Matchdays tab, Recent matches and Head to head links to its match page exactly when that page is built; check-built-pages.mjs proves it."
  - "12. Every page that is not a match page shows the same text as main's build, apart from the links in criterion 11."
  - "13. Every new label exists in EN, DE and FI; the label tests pass; the DE and FI words are the ones the CPO approved on the MR."
  - "14. At 375, 700 and 1010px in EN, DE and FI a played page has no horizontal scroll; check_design_inventory.py passes on it with no failures; block_standard.md carries the new element rows."
  - "15. Committed sample payloads cover full time, extra time, penalties, the three award kinds, goals without minutes, goals not recorded, no player stats and one side without player stats; each renders as above in EN, DE and FI."
  - "16. The full export and site build with every played page is measured on ci-runner-01 (output size in GiB, run time) and put to the CPO before the MR is called ready."

decisions_taken: >
  Approved in chat, 2026-10-15 and 2026-10-16: the plan; the 16 acceptance criteria above; the
  Match leaders labels (Shots / Schüsse / Laukaukset; Duels won / Gewonnene Zweikämpfe / Voitetut
  kaksinkamppailut; Fouls / Fouls / Rikkeet); the header's status word for an awarded result,
  Awarded; lineup_order numbers substitutes in the order they came on (minute, added minute, then
  the substitution's place in the events), substitutes who did not come on after them by shirt
  number. The renders _41 and _42 are the design. Readings of the rule "No block renders empty"
  (approved in chat, 2026-10-11): a played match without player stats, a line-up or team stats
  keeps that block's heading and one line saying what is not recorded; Match leaders with one
  side's numbers missing shows the boards and one line naming that side; a 0–0 has no Goals
  block.

  Approved in chat, 2026-10-16, after the build: every new EN, DE and FI line and label in
  strings.ts as shown in chat, the "awarded to {team}" lines among them; Finnish "minuuttia" for
  the minutes; the played page's description is the status word and the result line, composed in
  the page from translated words; the match page URL is declared permanent in the page spec; the
  played payloads carry no player slug, so scorer, board and line-up rows stay unlinked until the
  player pages bring a slug the warehouse serves; the head-to-head meeting's fixture is named
  fixture_api_id, as goals.player_api_id names a player inside the goals list.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; a payload kind and page state on the existing
  export and route. RECURRING COST: the export and the site build grow with ~60,000 played
  matches × 3 locales; measured on ci-runner-01 and put to the CPO (criterion 16). Hosting stays
  in the free tier at the #174 estimate (~3.8 GB); re-measured with the real payload.

decisions_reserved:
  - The exact EN, DE and FI text of every new line and label, put to the CPO before it is written.
  - The exact new text of docs/site_architecture.md's Fixture page row (a core document), put to
    the CPO before the edit.
  - Matches played then awarded (status AWD) stay out of mart_player_fixture_stats and the match
    window and boards.
  - How the match rows elsewhere show a shoot-out (#178 steps 2-3).
  - The metric glossary links (#168).

done_when:
  - dbt parse and compile pass; sqlfluff is clean on the changed SQL; the governance gates and the full pytest suite pass.
  - npm run build in site_v2 exits 0 with its prebuild tests; check-built-pages and audit-seo pass.
  - check_design_inventory.py passes on the built played page; every acceptance criterion is shown in acceptance_evidence.md from the built output.
  - data:build:mr is green; the full-scale measurement is put to the CPO.

amendments: >
  + tests/test_leaderboard_board_sets.py and site_v2/src/lib/format.ts, before any review.
  Authority: engineering_standards.md §3 (a board list the export carries is pinned to its mart's
  list, as the existing tuples are) and the consumption layer's one formatting module. Content:
  the Match leaders board list pinned to the mart's match_boards; the minute and score formats.
  + criterion 1 now ends "except each head-to-head meeting gaining its fixture id"; +
  dbt_project/models/5_marts/shared/mart_head_to_head.sql, dbt_project/models/5_marts/shared/shared.yml,
  site_v2/src/lib/builtFixtures.mjs and its test. Authority: approved in chat, 2026-10-16 (a
  head-to-head row can link to its played match only through the meeting's fixture id). Content:
  mart_head_to_head's recent_meetings carry the meeting's fixture; one build-time list of the match pages
  built, which every match row reads to decide whether it links.
  + site_v2/src/lib/href.ts. Authority: the same approval; content: the one function that turns a
  built match page into its address, beside the other address helpers.
  + dbt_project/models/5_marts/shared/mart_competition_fixtures.sql. Authority: the award lines
  that name a team where the league set no score, approved in chat, 2026-10-16. Content: the mart
  carries fct_fixture's awarded_to_team_sk, under its own name, so the page reads which line
  applies instead of working it out.
  + tests/test_no_decision_history_in_code.py and tests/test_sentence_length_in_docs.py. Authority:
  their own rule, that a pin moves down in the open when the tree sheds a flagged line. Content:
  the pins lowered to the counts the tree now holds; no pin is raised.
  + dbt_project/tests/assert_mart_head_to_head_meetings_are_fixtures.sql. Authority:
  engineering_standards.md §3.1 (a key carries a test of its parent), raised by the analytics
  engineer in review round 1. Content: every meeting's fixture_api_id is a fixture of fct_fixture.
