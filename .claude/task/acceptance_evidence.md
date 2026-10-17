# Verification — competition page tab titles within the title limit

Built locally with `npm run build` in `site_v2` on the committed samples: exit 0, the site's 125 tests
pass, audit-seo checks 2,572 pages OK, check-built-pages OK.

criteria_demonstrated:
  - Rankings titles, read from `site_v2/dist`: `en/bundesliga/stats` "Bundesliga: Stats 2026"; `de/bundesliga/statistiken` "Bundesliga: Statistiken 2026"; `fi/bundesliga/tilastot` "Bundesliga: tilastot 2026".
  - Matchdays titles, read from `site_v2/dist`: `en/bundesliga/matches` "Bundesliga: Fixtures and results 2026"; `de/bundesliga/spiele` "Bundesliga: Spielplan 2026"; `fi/bundesliga/ottelut` "Bundesliga: otteluohjelma 2026".
  - Overview titles unchanged: `en/bundesliga/index.html` "Bundesliga: Overview"; the three Overview strings are not in the diff.
  - Width: `titleWidthPx` from `audit-seo.mjs` over all 48 competitions in `competition_index.json`, three tabs, three languages: 0 titles over 660px.
