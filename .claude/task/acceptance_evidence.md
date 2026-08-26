# Acceptance evidence — #90, `clean_sheets` (count) vs `clean_sheets_share` (rate)

Every figure measured on this branch against merged main `5894aff`. Where a measurement
contradicted an expectation, the contradiction is what is recorded — and one of them contradicted
the issue itself.

## The headline

| | |
|---|---|
| catalogue rows | **85 → 86** (rate renamed in place, count added) |
| generated docs blocks | **181 → 183** (+5 added, −3 removed) |
| rate columns renamed | **7** — one expression, three yoy columns, one unpivot member, two mart pass-throughs |
| count columns renamed | **0**, deliberately |
| `accepted_values` lists moved | **3** (the issue named 2) |
| dangling `{{ doc() }}` after the change | **0** (`dbt parse` clean) |
| warehouse columns whose BigQuery description was WRONG and is now right | **2** |
| files | 19 code and doc · added 165 · deleted 76 |

## ⛔ The issue's premise is false, and verifying it was the first instruction

#90 says `mart_team_profile.clean_sheets` is the RATE and asks whether that is a LIVE DISPLAY BUG.
It is not, and the check that settles it is one join:

```
mart_team_profile.sql:86    ts.clean_sheets
mart_team_profile.sql:209   from metrics as m
mart_team_profile.sql:210   left join team_season as ts     <-- ts = mart_team_season, the COUNT
mart_team_season.sql:41     m.clean_sheets_sum_season as clean_sheets
```

Identical for `mart_team_season_insights.sql:57` (`ts` = the `mart_team_season` CTE, join at `:91`).
The committed payload agrees: `teams/33.json` carries `seasons[0].clean_sheets = 8` beside
`clean_sheets_this_season = 0.2105`, and 8/38 = 0.2105.

**Where the rate actually reaches the product** — a path the issue never names:

```
int_team_season__metrics_cumulative.sql:91   safe_divide(clean_sheet_games, games_played)
int_team_season__metrics.sql                 sf.* except (match_number)      <-- passes through
int_team_competition_benchmark_metrics_long.sql:34   UNPIVOT member
mart_team_competition_benchmarks             metric_key = 'clean_sheets'
```

Same payload: `{metric_key: 'clean_sheets', metric_value: 0.2105}`.

**So no wrong number was ever on screen.** The fixture surface serves counts from two count marts
with `games_in_window` / `games_played` denominators; the team surface serves the benchmark rate
and both row components coerced `count_fraction → percent` inline, each with a comment saying
"clean_sheets is served as a rate". That coercion was the two-meanings defect wearing frontend
clothes. It is deleted here and replaced by a declared per-surface binding.

⚠ The lesson is narrower than "the issue was wrong": the issue cited `mart_team_profile.sql:86`
correctly. The line was read for the column NAME and not for the alias it resolves to. A citation
is not a verification.

## The live defect this DOES fix

`{{ doc('clean_sheets') }}` — whose text is the COUNT definition, "shown as a count of games played
(e.g. 3/5)" — was attached to the two RATE columns at `int_team_season.yml:120` and `:256`.
`persist_docs` has already pushed that sentence onto both in BigQuery. Same class as the
`goals_against` defect `!104` fixed. After this change those two columns point at
`doc('clean_sheets_share')` and the five count columns keep `doc('clean_sheets')`, which is correct
for the first time.

## Acceptance criteria, demonstrated

⚠ The key below is at column 0 and its bullets are indented, because
`git_discipline._block()` anchors `^criteria_demonstrated[^\S\n]*:` at the line start and stops at
the first unindented line. Written as a markdown heading (`## criteria_demonstrated:`) it parses as
zero criteria and the commit is denied — which is exactly what happened on the first attempt.

criteria_demonstrated:
  - **EN/DE/FI label**, read from `site_v2/dist/{lang}/teams/manchester-united/index.html` after a
    clean `npm run build` (60 pages, `audit-seo` OK): season-panel row 3 renders `% Clean sheets`,
    `% Zu-Null-Spiele` and `% Nollapelit` respectively. No locale falls back to English and none
    resolves to an empty label.
  - **Fixture surface untouched**, read from
    `dist/en/champions-league/matches/2026-08-18-dinamo-zagreb-vs-viking/index.html`: the string
    `1/4 Clean sheets` appears twice, once per window — the count over its denominator, label
    unchanged, exactly as before the rename.
  - **Honest-absent on the stale sample**: the built team page shows 15 rows in the "vs the league"
    panel against 16 in "vs last season", i.e. the clean-sheet row is OMITTED rather than rendered
    as a zero bar, because the committed export still keys it `clean_sheets`. The season panel
    shows that row with an en-dash for both value and delta.
  - **Nothing else moved**: all 16 season-panel rows render in the locked block order in every
    locale, and every label except row 3 is byte-identical to main — Ø Goals, Ø Goals against, Ø
    Shots, % Shots from box, Ø Shots on target, % Goals per shot on target, Ø Duels, % Duels won, Ø
    Defensive actions, Ø Passes, % Pass accuracy, Ø Key passes, Ø Corners, Ø Corners against, %
    Save percentage.

## Offline verification, re-derived rather than quoted

| check | result |
|---|---|
| `sync_metric_docs_blocks.py --check` | OK, 183 blocks match the seed AND the model YAML |
| `check_description_hygiene.py` | ok — 1604 descriptions, 245 blocks resolved, all within 1024/16384 |
| `dbt parse` (1.7.19 / bigquery 1.7.2) | clean; 0 errors, 0 dangling `{{ doc() }}` |
| `sqlfluff lint` on all 4 edited models, full rule set | All Finished! |
| `npm test` (site_v2) | 76 pass, 0 fail |
| `python -m pytest tests/` | 1007 passed, 1 skipped, 14 subtests |
| `npm run build` | 60 pages, `audit-seo: 61 built page(s) checked. OK.` |

## ⛔ Mutation testing — the guards were watched going RED

A passing test over a renamed column proves nothing. Each guard was broken deliberately and the
failure observed, then restored; the restored diff is byte-identical (19 files, +165/−76 before and
after).

| mutation | guard | result |
|---|---|---|
| team binding points at `metrics.clean_sheet_share.label` (the key the plan originally proposed, which the catalogue declares nowhere) | `check-metric-labels.test.mjs` | **3 tests FAILED** |
| `int_team_profile.yml:65` points back at `doc('clean_sheets_this_season__team')`, the block the rename deleted | `dbt parse` | **Compilation Error** |
| `% Nollapelit` deleted from the FI dict only | `check-metric-labels.test.mjs` | **1 test FAILED**: "FI has no label for: metrics.clean_sheets_share.label" |

⚠ **NOT offline-checkable, stated rather than claimed**: renaming the unpivot member back to
`clean_sheets` while the three `accepted_values` lists say `clean_sheets_share` produces a red
`dbt test`, not a red offline gate. Nothing on this machine catches it. `data:build:mr` is where
that half is proved.

## Diff shape

19 code and doc files, +165 / −76. Line endings verified as BYTES: every edited file is uniformly
CRLF in the worktree (metricRows.ts 105/105, strings.ts 738/738, metric_catalogue.csv 87/87), so no
file flipped its endings.

## What is deliberately NOT here

The committed sample under `site_v2/src/data/` is one build stale and stays that way: the renamed
columns do not exist in BigQuery until `data:build:main` runs after merge, so the export cannot be
rerun yet. Hand-editing exported JSON to fake the new key would relocate a violation rather than
fix one. The visible consequence is measured above and is the honest-absent path, not a break.
