# Verification — Home rebuilt to its approved design

Built locally with `npm run build` in `site_v2` on the refreshed sample: exit 0, the site's tests
pass, audit-seo checks 2,269 pages OK, check-built-pages checks 1,644 match pages and 15,606 match
rows OK. `python scripts/check_design_inventory.py --dist site_v2/dist`: 24 pages × 375/700/1010 px
× EN/DE/FI, 0 failures; the 30 warnings are all the proposed Header row. Counts below are read from
`site_v2/dist/{en,de,fi}/index.html`, the same in all three.

criteria_demonstrated:
  - Shared match row: 285 `a.fxrow` rows (MatchRow, `data-fixture` on each, every one a link), 65 `.dh` date headings, 285 `.rowtz` zone labels reading "UTC", 24 `.topmatch` tags; the design check passes Match row kick-off, Match row zone, Date heading and Row link (hover ink@11%, press sunk) on Home.
  - Competition head and fold: 31 `.fxgroup` heads with crest (`.clogo`), name and chevron, the 2px line measured by the design check; 3 rows before each fold, 23 `details.fxmore` folds reading "Show all 5" (EN), "Alle 5 anzeigen" (DE), "Näytä kaikki 5" (FI).
  - Served order: HeroFixtures imports no ordering code (no `orderUpcomingGroups`), the export reads `order by n.competition_order, c.fixture_order` (pinned by `test_the_hero_reads_the_next_matchday_mart_whole_in_the_served_order`), and the 31 heads render in landing.json's order.
  - Rankings board: 8 `.ctab.rkt` boards from RankingBoard.astro, 56 `.ctab-row` rows, 7 per board, the board name in the head row; no `.brow` row remains; the design check passes Board name and Board name cell on Home.
  - Block explainer: the two intros are `p.bsub`, measured 13px, colour muted (rgb 139,144,153) in the browser and by the design check's Block explainer row.
  - Nothing else: three sections (Next matches, Top players, Top teams), four boards each in the catalogue order, the elite pool's leagues; `site_v2/src/i18n/strings.ts` is unchanged against main, so the intro wording is the same in EN, DE and FI.
