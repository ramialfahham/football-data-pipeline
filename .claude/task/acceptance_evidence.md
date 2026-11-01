# Verification — the Team page's strip plot and scatter labels

Read on the committed sample build of `site_v2`, 2026-11-01. Details in `rendered_page_evidence.md`.

criteria_demonstrated:
  - The built Team page's Compared with the league rows carry no `.rs-med`, `.rs-medv` or `.rs-k-med` node; the legend reads the team first ("Bayern München"), then "Other Bundesliga teams" (DE "Übrige Klubs der Liga", FI "Sarjan muut joukkueet"); each right column reads the rank ("1st", DE and FI "1.") at 15px/700 with the value ("3.6", "3,6") under it at 12px/400; 33 of 33 rows keep the better marker; read at 280, 360, 560, 768 and 1010px in EN, DE and FI.
  - The scatter's team name and difference label were measured on all 102 built Team pages (34 per language) at 280, 360, 560, 768 and 1010px, 510 charts, narrow and wide: no overlap on any, the label inside the chart on all and clear of the y axis on all; Borussia Mönchengladbach's narrow chart, the one edge case, puts the label under the name. `check-built-pages` checks the placement on all 204 built scatters and passes; its tests fail the old beside-the-name placement.
  - The Team page wireframe's Compared with the league row (02_team_profile.md) no longer lists `league_median`.
  - The Team page shows the approved teamPerfIntro, compDeservedExplainer and teamVsLeagueIntro, the competition page the approved compDeservedExplainer, Home the approved homeTopPlayersIntro and homeTopTeamsIntro, in EN, DE and FI at every width; `grep teamLeagueMedian site_v2/src` finds nothing.
  - block_standard.md's Strip plot row and Strip plot value rows carry the approved texts; `check_design_inventory.py --no-mocks`: 99 renders, 0 failures, 0 warnings.

`npm run build` in `site_v2`: 154 node tests pass, page-spec check passes, 2,271 pages built, SEO audit OK on
2,272 pages, built-pages check OK (3,318 league rows and 204 scatters on 102 Team pages, each row's shown rank
equal to the served one). pytest: 1,619 passed, 2 skipped. The six fast offline gates pass.
