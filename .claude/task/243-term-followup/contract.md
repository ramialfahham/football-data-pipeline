# Task contract — term list follow-up: one save, a five-item menu, the last old names

objective: >
  Issue #243 follow-up: a goalkeeper row names one save in the singular; the menu, drawer and footer
  carry five items, without Standings; the documents that list the menu say so; the two mock
  generators drop the last old metric and menu names.

refs: >
  #243 note 4194616642 (the singular save word); #137 and #138 (Standings leaves the menu),
  approved in chat 2026-11-09.

scope_paths:
  - .claude/task/243-term-followup/
  - site_v2/src/i18n/strings.ts
  - site_v2/src/components/fixture/PlayerRow.astro
  - site_v2/src/lib/menu.ts
  - docs/site_architecture.md
  - docs/wireframes/09_chrome.md
  - design-mocks/gen_competitions.py
  - design-mocks/gen_navmap.py
  - docs/wireframes/10_home.md
  - tests/test_sentence_length_in_docs.py

impact_map: >
  writers: none; no ingestion, no dbt model, no seed, no export change.
  downstream: strings.ts gains one key (savesOne) read by PlayerRow.astro on match pages; menu.ts
  feeds SiteHeader.astro and SiteFooter.astro on every page. The `table` key stays: the
  competition page's Table section and its spec read it.
  layer_rules: scripts/check_copy_gate.py, site_v2/scripts/check-term-list.test.mjs,
  site_v2/scripts/check-page-specs.mjs.
  deploy_order: none; the site deploy is manual.
  blast_radius: every page's header, drawer and footer lose one inert menu item; a goalkeeper row
  with one save changes its word.

approved_design:
  - home: #127
  - competitions: #128
  - competition: #129
  - matches: #130
  - match: #132
  - teams: #133
  - team: #134
  - players: #135
  - player: #136

acceptance_criteria:
  - A goalkeeper row with one save reads "1 save" in English, "1 Parade" in German and "1 torjunta" in Finnish; with more saves it reads saves, Paraden and torjuntaa.
  - The menu, the phone drawer and the footer list Competitions, Matches, Teams, Players and Statistics, in every language, and no page shows a Standings or Table menu item.
  - The competition page's table section still reads Table, Tabelle and Sarjataulukko.

decisions_taken:
  - The singular save word, #243 note 4194616642.
  - Standings leaves the menu, #137 and #138, approved in chat 2026-11-09.

decisions_reserved:
  - none: a word not in the table goes to the CPO.

done_when:
  - npm test in site_v2 passes.
  - python scripts/check_copy_gate.py passes.
  - npm run build in site_v2 passes.
  - pytest tests passes, apart from the CI-check tests that fail on Windows only.

amendments:
  - 2026-11-10: + docs/wireframes/10_home.md — authority: approved in chat, 2026-11-10; content: its
    line 90 ends "Date tabs and a "more matches" control are deferred to **#908**.", dropping the
    stale count of nav items without a page.
  - 2026-11-10: + tests/test_sentence_length_in_docs.py — authority: approved in chat, 2026-11-10;
    content: the 10_home.md pin goes from 128 to 127, the long sentence the line 90 cut removed.
