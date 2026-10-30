# Verification — the Team page, built to its approved design

Read from the built output of `npm run build` in site_v2 (prebuild: 137 site tests pass and 10 page
specs validate; 2,268 pages built; audit-seo and check-built-pages OK). The sample page is
`/{locale}/{teams word}/manchester-united-fc/` (team 33), read from `site_v2/dist` in EN, DE and FI.
The browser check ran on the dev server at 280px, 375px and desktop width.

criteria_demonstrated:
  - Three tabs: EN Overview · Matches · Performance, DE Übersicht · Spiele · Leistung, FI Yleiskatsaus · Ottelut · Suoritus; Overview is checked on load. Every block reads the featured season (Premier League 2026/27, `is_featured_season`); only Next matches and Upcoming list matches to come.
  - Overview block names, in order: Competitions, Recent matches, Next matches, Highs and lows, Squad. Competitions shows "Premier League · Matchweek 8, 16th" and "UEFA Champions League · League phase, 21st" with W/D/L, goals and points. Cup rows read from `cup_status`: "DFB-Pokal · Second round, Through" (VfB Stuttgart), "DFB-Pokal · Second round, Knocked out" (SV Werder Bremen), "UEFA Super Cup · Final, Winners" (Paris Saint-Germain). The soonest next match carries "Next". The squad groups by Goalkeepers, Defenders, Midfielders and Forwards; its first line reads "Belgium · 24 · 8 appearances · 90 minutes per appearance".
  - Matches: the shared Filter bar offers All, Premier League and UEFA Champions League, with the dropdown "All competitions" (DE "Alle Wettbewerbe", FI "Kaikki kilpailut"). Upcoming holds 2 competition groups in the order of their first match; Results holds 11 result rows, newest first. Choosing UEFA Champions League leaves 1 group and 3 results in the browser.
  - Performance: the tab's explainer, then Standing, Deserved points, Compared with the league and Compared with last season. Deserved points has its table, headed "Premier League, after 8 matches", and the scatter plot. The league comparison draws 33 strip rows and the season comparison 33 table rows with This season, Last season and Trend. Each shows the 14 key metrics until its "Show all metrics" switch is on (browser: 14 rows off, 33 on). No page carries a "Metric Glossary" link; that link follows #168.
  - Copy in EN, DE and FI: every block name, the explainers, the legend, the switch and the table heads render in the page's language, as approved on #134, #223 and #235. Metric names and groups come from `metricLabel` and the served `metric_rows.json` only; the label test passes and the copy gate reports "COPY GATE ok".
  - Documents: `docs/wireframes/02_team_profile.md` describes the built page; the screen inventory marks the Team page built and the Squad and Stats rows retired; `design-mocks/gen_team_mock.py` holds the mock's generator, listed in the design-mocks README.

No sideways overflow on any tab in EN at 375px or in DE and FI at 280px. The design check passes on
all 10 built pages and the 14 mocks with the new block-standard rows. pytest: 1,616 passed, 2 skipped.
The samples were re-exported after the merge of the team-wide order in `mart_team_fixtures`: in
teams 33 and 157, Upcoming runs soonest first and Results newest first, in the served order.
