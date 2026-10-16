# Task contract — the played match page's year

objective: >
  A played match page's title, heading and description carry the match's year, so two meetings of
  the same clubs on the same day in different seasons no longer share them. The full-scale site
  build's audit fails on 921 titles, 921 headings and 555 descriptions without it.

refs: >
  #175, the played match page (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/175),
  whose scale criterion this unblocks. The plan and the wireframe sentence: approved in chat,
  2026-10-16.

scope_paths:
  - site_v2/src/pages/?lang?/?competition?/?matches?/?fixture?.astro
  - site_v2/scripts/audit-seo.test.mjs
  - docs/wireframes/01_fixture_page.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: the Astro build writes the match pages; no export, model or seed changes.
  downstream: the played match pages' title, h1, og and JSON-LD names that read the same title,
  and their meta description. No other page reads them.
  layer_rules: the site formats a served kickoff with an existing formatter (formatDayYear in
  site_v2/src/lib/format.ts); nothing is computed from data.
  deploy_order: none; the site build runs on the committed samples in CI on the MR; deploy:site-v2
  stays manual.
  blast_radius: played match pages only (about 64,000 payloads, three locales each); the next match
  page's title and description are unchanged.

acceptance_criteria:
  - "1. On a played match page the title and the h1 read the seoFixtureTitle template with the day, month and year of the kick-off (formatDayYear); EN Hoffenheim–Dortmund reads TSG 1899 Hoffenheim vs Borussia Dortmund, 5 Sept 2026, and the DE and FI pages read their templates with their locale's date."
  - "2. A played match page's meta description ends with · {day month year}., e.g. Full time: TSG 1899 Hoffenheim 2–3 Borussia Dortmund · Matchday 2 · 5 Sept 2026."
  - "3. Every next match page's title, h1 and description are identical to main's build."
  - "4. audit-seo.test.mjs asserts the 600px title budget for a next match title and the 660px hard cap for a played match title, whose date carries a year, and passes; the full-scale build's count of titles over 600px is put on the MR."
  - "5. npm run build in site_v2 passes on the committed sample (prebuild tests, audit-seo, check-built-pages)."
  - "6. The full-scale build from the export of deploy job 17243256610 shows no title, h1 or description violation in audit-seo; the violations left are the 9 of the two Nyasa Big Bullets team pages and the 54 dead links of moved matches; no title passes the 660px hard cap."
  - "7. 01_fixture_page.md §8 carries the approved sentence: A played match's date carries its year: the same clubs meet on the same day in other seasons."

decisions_taken: >
  Approved in chat, 2026-10-16: the year on the played match page's title, heading and
  description; the plan; the wireframe sentence; the seven acceptance criteria. The next match page keeps its title, as approved.
  No new string key: the description joins served facts with the existing separator, as the played
  description already does.

decisions_reserved:
  - The two Nyasa Big Bullets team ids (4596 and 4599) that build two team pages with one name.
  - The deploy export's entity list, which leaves the day pages and competition lists on the committed sample (#156).
  - Any played title over the 660px hard cap, put to the CPO with the titles.

done_when:
  - npm run build in site_v2 passes on the committed sample.
  - The full-scale build's audit-seo lists no title, h1 or description violation.
  - Reviewers bi-analyst, platform and scope-auditor pass.

amendments: >
  2026-10-16: criterion 4 tests a played match title against the 660px hard cap instead of the
  600px budget, which the longest played pairings pass (626px EN, 633px DE) once the date carries
  its year — authority: approved in chat, 2026-10-16.
  2026-10-17: criteria 1 and 2 give the English month as Intl's en-GB form, Sept, the form the
  head-to-head rows already show — authority: approved in chat, 2026-10-17.
