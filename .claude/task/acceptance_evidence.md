# Verification — the played match page's year

Read from two builds. The sample build ran `npm run build` in site_v2 on main and on the branch, in a
worktree that held only the committed sample. The full-scale build ran `npm run build` with
`NODE_OPTIONS=--max-old-space-size=8192` on the export of deploy job 17243256610 (60,303 played
and 4,340 unplayed payloads, as its manifest counts them).

criteria_demonstrated:
  - 1 Title and h1: the full-scale build's Hoffenheim–Dortmund pages read `<title>TSG 1899 Hoffenheim vs Borussia Dortmund, 5 Sept 2026</title>` with the same h1 (EN), `TSG 1899 Hoffenheim - Borussia Dortmund, 5. Sept. 2026` (DE) and `TSG 1899 Hoffenheim–Borussia Dortmund, 5.9.2026` (FI); 60,303 EN match pages carry a year in the title, the manifest's played count exactly.
  - 2 Description: the EN page's meta description reads "Full time: TSG 1899 Hoffenheim 2–3 Borussia Dortmund · Matchday 2 · 5 Sept 2026."
  - 3 Next match pages unchanged: on the sample, 2,539 of the branch's pages are byte-identical to main's (hashed asset names aside), every next match page among them; the 33 that differ are the 11 played samples in 3 locales, each gaining its year. At full scale, the 4,342 EN match pages without a year match the manifest's 4,340 unplayed payloads plus the 2 sample payloads the export does not write.
  - 4 Width test: `node --test scripts/audit-seo.test.mjs` passes 36 of 36; the fixture test measures each locale's template with that locale's widest real date over the twelve months, from Intl as format.ts renders it, and holds the next match form under 600px and the played form under the 660px hard cap (widest: DE "28. März 2026" at 635px, EN "28 Sept 2026" at 631px, FI "28.10.2026" at 591px, for SG Sonnenhof Grossaspach against Borussia Mönchengladbach). At full scale 161 titles are over 600px and none is over 660px.
  - 5 Sample build: prebuild tests pass (122 of 122), astro build 2,571 pages, "audit-seo: 2572 built page(s) checked. OK.", "check-built-pages: 1917 match page(s) = 639 payload(s) x 3 … OK."
  - 6 Full scale: 204,498 pages in 724s; audit-seo reports 63 violations, none a title, h1 or description of a match page: 9 from the two Nyasa Big Bullets team pages (team ids 4596 and 4599) and 54 dead links from lists built on the committed sample to 18 moved matches in 3 locales.
  - 7 Wireframe: 01_fixture_page.md §8 carries "A played match's date carries its year: the same clubs meet on the same day in other seasons."
