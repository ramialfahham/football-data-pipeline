# Acceptance evidence — refresh the committed export sample after #90

One file changed: `site_v2/src/data/teams/33.json`, replaced verbatim with
`artifacts/site_data/teams/33.json` from `python scripts/export_site_data.py --entities teams`
(3,289 payloads written to the gitignored `artifacts/site_data`; one copied across).

## The headline

| | |
|---|---|
| tracked sample files changed | **1** of 22 |
| benchmark rows in the payload | 466 |
| `metric_key: "clean_sheets"` (old) | **0** |
| `metric_key: "clean_sheets_share"` (new) | **22** |
| old `clean_sheets_{this,prev}_season` / `_delta_yoy` keys | **0** |
| new `clean_sheets_share_*` season keys | **75** |
| seasons still carrying the COUNT `clean_sheets` | **25 of 25** |
| BigQuery read, measured by dry-run before spending it | 157.7 MiB |

## Acceptance criteria, demonstrated

⚠ The key below is at column 0, NOT a `##` heading. `git_discipline._block()` anchors
`^criteria_demonstrated[^\S\n]*:` at the line start, so a heading parses as zero criteria and the
commit is denied. This is the second time in one session I have written it as a heading.

criteria_demonstrated:
  - **Post-#90 names present, count preserved**: the refreshed payload carries zero
    `metric_key: "clean_sheets"` rows and 22 `clean_sheets_share` ones across its 466 benchmark
    rows, zero old yoy keys and 75 `clean_sheets_share_*` ones, while all 25 seasons still carry
    `clean_sheets` (the count) and `clean_sheet_run` — the columns the rename did not touch.
  - **Built page renders in all three locales**: `npm run build` completed 60 pages with
    `audit-seo: 61 built page(s) checked. OK.`, and each of
    `dist/{en,de,fi}/teams/manchester-united-fc/index.html` renders its Performance tab without
    error.
  - **Tracked file SET unchanged**: `git status --porcelain` shows exactly one changed file under
    `site_v2/src/data/`, so no `.gitignore` allowlist edit was needed and no internal link moved.
  - **No stray payload left behind**: `git status --porcelain --ignored site_v2/src/data` returns
    the one modified tracked file and nothing else, so the "every link resolves locally while only
    the tracked ones reach CI" trap in `README.md:9-13` is not armed.

## ⛔ What the refresh does NOT restore, and why that is correct

The Performance tab renders **"Not enough games this season to rank Manchester United FC against
the league"** in all three locales — 0 rows in both panels, not the 16 the first draft of this
contract predicted.

That is the product working. The export's featured season has rolled to **PL 2026, 1 game played**,
and `mart_team_competition_benchmarks` ranks nothing below **3 games**, so that season carries 0
benchmarks. PL 2025 is still in the payload with its 22 benchmark rows; it is simply no longer the
season the page opens on (#846: the pipeline decides). The tab will populate itself once the season
reaches three games.

⚠ So the visible state changed from "15 rows, clean-sheet row absent" to "tab not rankable yet".
Both are honest-absent paths the tab already implements. Neither is a defect, and the clean-sheet
rename is verified above in the PAYLOAD, which is where this task's evidence lives.

## ⚠ A side effect this commit carries, disclosed not buried

The team's name and slug moved with the refresh — `Manchester United` → `Manchester United FC`,
`manchester-united` → `manchester-united-fc` — so the built page relocates from
`/{locale}/teams/manchester-united/` to `/{locale}/teams/manchester-united-fc/`. `dim_team.sql:7`
calls `team_slug` "the team's permanent, locale-independent URL segment". Not caused by #90, not
investigated here, and no internal link breaks (nothing links to a team page today). Registered in
`decisions_reserved` as its own issue against #852.
