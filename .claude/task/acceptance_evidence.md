# Acceptance evidence — rename `corner_kicks_per_match` → `corners_per_match`, `save_ratio` → `saves_pct`

Step 3 of the metric catalogue naming programme, MR B of six.
Branch `refactor/metric-rename-team-set-pieces-goalkeeping`, from main `a70b7e2`.

The four criteria are the ones the CPO approved as STANDING for MRs B–F ("do it", recorded in
`escalations.log`), after the first two drafted for `!114` turned out to be unprovable. Everything
below is read from the BUILT site under `site_v2/dist/` (61 pages), from a test run, or from a guard
deliberately broken and watched.

criteria_demonstrated:
  - **Criterion 1 — no rendered metric name changed its words, in any locale.** Read back from the built fixture pages, the surface that renders the metric block. Each locale renders **14** metric names; of those, the ones the untouched CPO-validated corpus `site/i18n/<loc>.json` also declares were compared word for word — EN **7** compared, DE **8**, FI **8**, and **wording differences: NONE** in all three. The one reported divergence is pre-existing and already exempted by name in `check-metric-labels.test.mjs`: EN `finishing_efficiency` renders `% Goals per shot on target` where the corpus says `% Conversion rate`. Source pages: `site_v2/dist/<loc>/brasileirao/matches/2026-07-26-palmeiras-vs-atletico-mg/index.html`.
  - **Criterion 2 — neither old name survives in the built site or the hand-written source.** `grep -rl` over `site_v2/dist` → **0 files** of 61 built pages plus every asset. `git grep -l` over `site_v2/src` excluding `src/data` → **0 files**. The generated sample still holds **364** occurrences of the two old keys: that is the declared transient, regenerated from the prod marts only after `data:build:main` runs on merge.
  - **Criterion 3 — the label suite passes AND was watched failing.** `npm test`: **76 tests, 76 pass, 0 fail**, including the cross-check that every `labelKey` is a `label_i18n_key` the catalogue declares and that ≥27 CPO-validated labels match `site/i18n/` with zero drift. Then broken on purpose: the seed's `saves_pct` row was reverted to `label_i18n_key = metrics.save_ratio.label` and the suite went **RED — 75 pass, 1 fail** — `AssertionError: label keys the catalogue does not declare in label_i18n_key: metrics.saves_pct.label`. Restored, green again.
  - **Criterion 4 — the built team page still shows the absent state where these rows would sit, in all three locales.** Read from `site_v2/dist/<loc>/teams/manchester-united-fc/index.html`: EN *"Not enough games this season to rank Manchester United FC against the league."*, DE *"Zu wenige Spiele in dieser Saison, um Manchester United FC mit der Liga zu vergleichen."*, FI *"Liian vähän otteluita tällä kaudella, jotta Manchester United FC voisi verrata sarjaan."* That page's featured season has one game played, below the `>= 3 finished games` benchmark floor, so it is unchanged by the rename and is recorded so the absence is never read as a defect of it.

## ⛔ THE TRANSIENT IS VISIBLE THIS TIME, and the contract said it would not be

The declared transient is the same in cause as `!114`'s — the committed sample cannot carry the new
keys until prod rebuilds — but **not in effect**, and an earlier draft of the contract said "on the
page this is invisible either way". That was reasoned from the team tab and is wrong about the
fixture page. Measured on the built site:

| | before | after |
|---|---|---|
| metric names rendered per fixture page, EN / DE / FI | 16 / 16 / 16 | **14 / 14 / 14** |

`MetricComparison.astro`'s `hasData()` drops any row where neither side has a value, so the two
renamed rows are OMITTED from the 16-row comparison on all **51** built fixture pages until the
sample is regenerated. `!114` did not do this because its renames touched the TEAM binding only;
these two are FIXTURE fields.

⛔ AND IT IS ONE STEP LARGER THAN "TWO ROWS", which bi-analyst-reviewer spotted and I had not.
`saves_pct` is the ONLY row in the **Goalkeeping** group, and `MetricComparison.astro` drops a group
once it has no rows (`.filter((g) => g.rows.length > 0)`), so the group HEADING disappears too.
Verified on the built EN page: the word `Goalkeeping` occurs **0** times, while `Set pieces` still
occurs (its sibling `corners_against_per_match` survives). So the fixture comparison loses two rows
AND one of its seven section headings until the sample is regenerated.

⚠ It is the codebase's honest-absent behaviour, not a break — rows are omitted, never blank and
never a fabricated zero, exactly as `14_team_stats.md` §6 requires — and it closes the moment the
sample is regenerated. The contract is corrected to say so.

⭐ THIS STRENGTHENS THE CASE FOR PULLING THE SAMPLE REFRESH FORWARD rather than letting the gap run
to MR F. MRs C–F rename five more fixture fields, so by F the comparison would be missing roughly
ten of sixteen rows and several headings. Put to the CPO; not decided here.

## ⚠ AND THE MEASUREMENT EXPOSED A FLAW IN MY OWN EVIDENCE METHOD

The script used for criterion 1 on `!114` tested each label with a plain substring match, so
**`Ø Corners` tested TRUE against a page containing only `Ø Corners against`.** It reported 16
rendered names here when the true figure was 14 — i.e. it would have certified two missing rows as
present. Verified directly: `grep -o "Ø Corners"` and `grep -o "Ø Corners against"` both return
**2** on the EN page, so every "Ø Corners" occurrence IS an "against" one.

Fixed: the count for a label now subtracts the occurrences of any longer label containing it. The
numbers above are from the corrected method.
⭐ THE RULE: a substring test over rendered text is not a presence test wherever one label is a
prefix of another — and this metric set is full of `X` / `X against` pairs (`Ø Goals`,
`Ø Corners`, `Ø Shots on target`, …). `!114`'s conclusion still holds, because nothing it renamed
was a fixture field, but its method was weaker than its claim.

## Mutations — two run, both RED, both restored

| mutation | result |
|---|---|
| seed `label_i18n_key` reverted to `metrics.save_ratio.label` | ✅ RED — `check-metric-labels.test.mjs`, 1 of 76 failing |
| `catalogue_metric_id` in the FROZEN `site/match-preview/metric_bindings.csv` reverted to `save_ratio` | ✅ RED — `tests/test_metric_bindings.py`: *"save_ratio_recent -> unknown catalogue metric 'save_ratio'"* |

The second is the one that matters for this MR specifically: it proves the coupling between the
catalogue and the retired MVP's binding file is real, which is why the frozen tree had to be touched
at all.

## Gates

| gate | result |
|---|---|
| `python scripts/sync_metric_docs_blocks.py --check` | OK — 179 blocks match the seed and the model YAML |
| `python scripts/export_metric_definitions_json.py` | regenerated 13 definitions; `tests/test_metric_bindings.py` byte-identity passes |
| `python scripts/check_ui_i18n_metrics.py` | OK — 13 shown metrics resolve in 3 locale files |
| `python scripts/check_layer_contract.py` | passed |
| `python scripts/check_description_hygiene.py` | OK — 1604 descriptions, 241 docs blocks resolved, none dangling |
| `python -m pytest -q` | **1009 passed**, 1 skipped, 14 subtests — unchanged from `a70b7e2` |
| `dbt parse` | clean; zero dangling `doc()` references |
| `sqlfluff lint`, 10 changed models, repo root, full rule set | All Finished — no violations |
| `npm test` + `check-page-specs.mjs` | 76/76; 4 pages validated |
| `npm run build` | 60 pages, `audit-seo: 61 built page(s) checked. OK.` |

⚠ `pytest` was first launched from `site_v2/` by mistake and reported "no tests ran in 0.14s" — a
green-looking result that ran nothing. Re-run from the repo root for the figure above. The CWD trap
in `CLAUDE.md`, hit live.

## The three `accepted_values` lists

All THREE carry the new names — `int_competition_benchmarks.yml` lines 27 and 66, and `shared.yml`
line 2080 — checked by eye as well as by grep, because **#96** records that no offline gate pins
them to the model columns and only the warehouse build would catch a miss.

## One stale artifact, named rather than left to be found

`.claude/task/rendered_page_evidence.md` still holds content from an unrelated earlier task (the
sample refresh after #90) and says nothing about this branch. bi-analyst-reviewer noted it and
judged the built-output requirement substantively met by this file instead, which carries the
locale-by-locale rendered-name counts read from `site_v2/dist/`. It is NOT updated here because it
is not in `scope_paths` and pulling it in would be scope drift for a file no gate reads on this
diff. Flagged so the next task does not mistake it for current.

## Deliberate survivors of the sweep

`git grep` over every live path leaves four, each intended and each named in the contract:
`metric_bindings.csv`'s two `live_id`s and the same ids as keys in the generated
`metric_definitions.json` and in `metric_manifest.json` — those are the RETIRED product's display
ids, not catalogue ids, and `check_ui_i18n_metrics.py` maps them through the bindings — plus
`site/team-season/index.html`, a page of the product retired on 2026-07-21 that no gate reads.
