# Acceptance evidence — rename `clean_sheets_share` → `clean_sheets_pct`, `points_capture` → `points_capture_pct`

Step 3 of the metric catalogue naming programme, MR A of six.
Branch `refactor/metric-rename-team-goals-outcomes`, from main `1804a64`.

Everything below is read from the BUILT site under `site_v2/dist/` (61 pages, rebuilt after the
final source state), from a test run, or from a guard that was deliberately broken and watched.
Nothing is read from source and nothing from `outerHTML`.

⚠ THE FOUR CRITERIA WERE AMENDED MID-TASK with the CPO's authority, recorded in
`contract.md` → `amendments:`. Criteria 1 and 4 originally asked for the clean-sheet row's label
and value to be read off the built page. **That row renders on no built page, and did not before
this branch either**: team 33's featured season is PL 2026 with ONE game played, under the
`>= 3 finished games` benchmark floor, so `season.benchmarks` is empty, `TeamPerformance.astro`'s
`hasBench` guard is false, and the whole tab renders its absent state. That is a property of the
committed sample, not of this rename. The amended criteria are demonstrated below.

criteria_demonstrated:
  - **Criterion 1 — no rendered metric name changed its words, in any locale.** Read back from the built fixture pages, which are the surface that actually renders the 16-row metric block. Each locale renders all **16** metric names; of those, the ones the untouched CPO-validated corpus `site/i18n/<loc>.json` also declares were compared word for word — EN **9** compared, DE **10**, FI **10**, and **wording differences: NONE** in all three. EN reads `Clean sheets · Ø Corners · Ø Corners against · % Shots from box · Ø Defensive actions · Ø Duels · % Duels won · % Goals per shot on target · Ø Goals against · Ø Goals · Ø Key passes · % Pass accuracy · Ø Passes · % Save percentage · Ø Shots on target · Ø Shots`; DE reads `Zu-Null-Spiele · Ø Ecken · … · Ø Schüsse`; FI reads `Nollapelit · Ø Kulmapotkut · … · Ø Laukaukset`. ONE divergence is reported and is **pre-existing, not caused here**: EN `finishing_efficiency` renders `% Goals per shot on target` where the corpus says `% Conversion rate` — the same divergence `check-metric-labels.test.mjs` already exempts by name, because the corpus wording is a §10 pick reserved to the CPO. Source page for each locale: `site_v2/dist/<loc>/brasileirao/matches/2026-07-26-palmeiras-vs-atletico-mg/index.html`.
  - **Criterion 2 — neither old name survives in the built site or in the hand-written source.** `grep -rl -E "clean_sheets_share|points_capture" site_v2/dist` → **0 files** of the 61 built pages plus every asset. `git grep -c -E "clean_sheets_share|points_capture" -- site_v2/src ':!site_v2/src/data'` → **0 files**. The generated sample under `site_v2/src/data/` still holds **122** occurrences of the two old keys, which is the declared transient: it is regenerated from the prod marts and cannot carry the new columns until `data:build:main` has run on merge. It closes in the step's final refresh MR.
  - **Criterion 3 — the label suite passes AND was watched failing.** `npm test` in `site_v2/`: **76 tests, 76 pass, 0 fail**, including `the CPO-validated MVP labels are byte-identical to site/i18n` (its own floor is ≥27 comparisons with zero drift) and `every labelKey is a label_i18n_key the catalogue actually declares`. Then the guard was broken on purpose: the seed's `clean_sheets_pct` row was reverted to `label_i18n_key = metrics.clean_sheets_share.label` and the suite went **RED — 75 pass, 1 fail**, with `AssertionError: label keys the catalogue does not declare in label_i18n_key: metrics.clean_sheets_pct.label`. Restored, green again. A green guard nobody has broken proves nothing.
  - **Criterion 4 — the built team page renders the absent state where the share row would sit, in all three locales.** Read from `site_v2/dist/<loc>/teams/manchester-united-fc/index.html`: EN *"Not enough games this season to rank Manchester United FC against the league."*, DE *"Zu wenige Spiele in dieser Saison, um Manchester United FC mit der Liga zu vergleichen."*, FI *"Liian vähän otteluita tällä kaudella, jotta Manchester United FC voisi verrata sarjaan."* No share-class label (`% Clean sheets` / `% Zu-Null-Spiele` / `% Nollapelit`) is present on any of the three. Recorded so the missing row is read as the sample's one-game featured season and never as a defect of this rename; its first real render is verified when the sample refresh lands.

## Mutation testing — four run, THREE red, ONE SURVIVOR

Per the standing rule that a passing test proves nothing. Each was applied, observed, and restored.

| # | mutation | result |
|---|---|---|
| 1 | one `accepted_values` entry in `int_competition_benchmarks.yml` reverted to `clean_sheets_share` | ⛔ **SURVIVED** — `dbt parse`, `sync_metric_docs_blocks.py --check`, `check_description_hygiene.py` and `pytest -k "metric or benchmark or catalogue"` (71 passed) were **all green** |
| 2 | seed `label_i18n_key` reverted to `metrics.clean_sheets_share.label` | ✅ RED — `check-metric-labels.test.mjs`, 1 of 76 failing |
| 3 | seed `metric_id` reverted to `points_capture` | ✅ RED — `sync_metric_docs_blocks.py --check`: *"missing block: points_capture / block no longer in the seed: points_capture_pct"* |
| 4 | `doc('points_capture_pct')` in `domestic_league.yml` reverted to `doc('points_capture')` | ✅ RED in TWO places — `check_description_hygiene.py`: *"unresolved docs block: 'points_capture'"*, and `dbt parse`: *"Documentation for 'model...mart_team_season_insights' depends on doc 'points_capture' which was not found"* |

⛔ **THE SURVIVOR IS A REAL GAP AND IS NOT CLOSED HERE.** Nothing offline pins the three
`accepted_values` lists of the 22 benchmark `metric_key`s to the model columns they enumerate; the
only guard that fires is the warehouse `accepted_values` test inside `data:build:mr`. So a rename
that updates the column and forgets a list is caught only after a BigQuery build. Out of this
contract's scope (a new guard is a new mechanism) — filed separately rather than folded in.

## Gates

| gate | result |
|---|---|
| `python scripts/sync_metric_docs_blocks.py --check` | OK — 179 blocks match the seed and the model YAML |
| `python scripts/check_description_hygiene.py` | OK — 1604 descriptions, 241 docs blocks resolved, none dangling |
| `python scripts/check_layer_contract.py` | Layer contract checks passed |
| `python scripts/check_ui_i18n_metrics.py` | OK — 13 shown metrics resolve in 3 locale files |
| `python -m pytest -q` | **1007 passed, 1 skipped**, 14 subtests — unchanged from `1804a64` |
| `dbt parse` (1.7.19, `.venv/Scripts/dbt.exe`) | clean; zero dangling `doc()` references |
| `sqlfluff lint` on all 5 changed models, repo root, full rule set | All Finished — no violations |
| `npm test` + `node scripts/check-page-specs.mjs` | 76/76; 4 pages validated against their specs |
| `npm run build` | 60 pages built, `audit-seo: 61 built page(s) checked. OK.` |

## The sweep, and its ONE deliberate survivor

`git grep -n -E "clean_sheets_share|points_capture([^_]|$)"` over every path except the generated
sample, the task artifacts, `docs/audits/`, `docs/match_preview_pages_refinement.md` and the dormant
`.github/` returns exactly **one** hit:

`docs/wireframes/10_home.md:187` — inside a **verbatim quotation** of `gen_top_teams.py`'s header
(*"'% Points captured' dropped as a board; `points_capture` is shown nowhere"*), in a passage
already marked SUPERSEDED. Editing a quotation stops it being one, so it stays. Every other
reference in that file, including the ones in the superseded table and the struck-through
paragraph, was renamed.

Two further classes were left alone on the same principle — they record HISTORY, and renaming
inside a record of what happened falsifies the record: `docs/working_agreement.md:348`
(Appendix A incident A1, "invented player metrics… player shot_accuracy") and `docs/audits/`.
Neither name occurs anywhere under `site/`, so no frozen file of the retired MVP is touched by
this MR at all.
