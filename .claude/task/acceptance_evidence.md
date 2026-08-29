# Acceptance evidence — batch F: finishing_efficiency → finishing_efficiency_pct (TEAM only)

Branch `refactor/metric-rename-team-finishing-efficiency`, from main `cdd2218`.
Step 3 of the metric catalogue naming programme, **MR F of six — the LAST of the twelve team
renames**.

The four criteria are the CPO's STANDING set for MRs B–F. Reproduced, not re-drafted. Everything
below is read from the BUILT site under `site_v2/dist/`, from a test run, or from a guard
deliberately broken and watched. No gate below was piped through `tail`/`head`; every exit code was
read bare.

criteria_demonstrated:
  - **Criterion 1 — no rendered metric name changed its words, in any locale.** Every rendered name is compared as a WHOLE element text, never by substring. Of the names each locale still renders, the ones the untouched corpus `site/i18n/<loc>.json` also declares were compared for exact equality: EN **7 → 7**, DE **8 → 7**, FI **8 → 7**. **Names ADDED: none, in all three locales. Names lost: exactly one, and it is this metric's own row** — EN `% Goals per shot on target`, DE `% Trefferquote`, FI `% Viimeistelytehokkuus`. **No surviving name changed its wording anywhere.**
  - **Criterion 2 — the old name survives nowhere in the built site or the hand-written source.** Whole-token `grep -rlE "(^|[^A-Za-z_0-9])finishing_efficiency([^A-Za-z_0-9]|$)"` over `site_v2/dist/` → **0 files** of 67 built pages. The same whole-token `git grep` over `site_v2/src` excluding `src/data` → **0 files**. The generated sample holds **195** occurrences (120 bare + 25 each of the three yoy forms): the declared transient, closing with the final roll-forward after F.
  - **Criterion 3 — the label suite passes AND was watched failing.** `npm test`: **76 tests, 76 pass, 0 fail** (exit 0). Broken on purpose: the seed's `finishing_efficiency_pct` row reverted to `label_i18n_key = metrics.finishing_efficiency.label` → **RED, exit 1, 75 pass / 1 fail** — `AssertionError [ERR_ASSERTION]: label keys the catalogue does not declare in label_i18n_key: metrics.finishing_efficiency_pct.label`. Restored: green again at 76/76, and `sync_metric_docs_blocks.py --check` still OK at 176 blocks.
  - **Criterion 4 — the built team page still shows the absent state where these rows would sit, in all three locales.** Read from the `<div class="cb">` element inside the `data-page="performance"` panel of `site_v2/dist/<loc>/teams/manchester-united-fc/index.html` — matched on the element, not by searching for a phrase. EN *"Not enough games this season to rank Manchester United FC against the league."*, DE *"Zu wenige Spiele in dieser Saison, um Manchester United FC mit der Liga zu vergleichen."*, FI *"Liian vähän otteluita tällä kaudella, jotta Manchester United FC voisi verrata sarjaan."* Identical before and after; the sample's featured season (team 33, PL 2026) has one game played, below the `>= 3 finished games` benchmark floor.

⚠ **Criterion 3 lands on a COVERED metric, and that was checked before it was relied on.** Batch C
recorded a mutation surviving because `shots_on_goal_pct` is asked for by nothing; the guard's real
scope, read from `check-metric-labels.test.mjs:36-38`, is `asked = rowKeys ∪ heroKeys`.
`finishing_efficiency_pct` IS one of the 16 `labelKey:` entries in `metricRows.ts`, so this mutation
genuinely exercises the guard rather than proving nothing.

## The transient grew to exactly the predicted number

The contract predicted **13 → 12, no group heading lost**, written before any code, because
`finishing_efficiency` IS one of the LOCKED 16 in `metricRows.ts` while the committed sample still
serves the old key. Measured on the built site, counted structurally:

| | before (`cdd2218`) | after |
|---|---|---|
| metric rows per comparison block, EN / DE / FI | 13 / 13 / 13 | **12 / 12 / 12** |
| group headings per block | 7 / 7 / 7 | **7 / 7 / 7** |
| rendered names REMOVED | — | **exactly 1 per locale, this metric's** |
| rendered names ADDED | — | **none** |

Across all 19 fixture pages, both windows, all three locales: `[12]` (min 12, max 12).
Shooting keeps `Ø Shots` and `Ø Shots on target`, so its heading survives — all seven remain.
Programme running total: 16 → 15 (C) → 13 (D) → 13 (E) → **12 (F)**. Honest-absent, never blank and
never a fabricated zero (`14_team_stats.md` §6). It closes with the final roll-forward, which is
owed after F and is NOT in this branch.

## Gates — every exit code read bare, nothing piped

| gate | exit | result |
|---|---|---|
| `python scripts/sync_metric_docs_blocks.py --check` | 0 | 176 blocks match the seed and the model YAML |
| `python scripts/check_description_hygiene.py` | 0 | 1604 descriptions, 20 files, **238 docs blocks resolved**, zero dangling `doc()` |
| `python scripts/check_layer_contract.py` | 0 | passed |
| `python scripts/check_ui_i18n_metrics.py` | 0 | 13 shown metrics resolve in 3 locale files |
| `dbt parse` (1.7.19) | 0 | clean, zero error lines |
| `sqlfluff lint` — the 8 changed models, from the repo root | 0 | no findings; full output read, nothing truncated |
| `python -m pytest -q` (repo root) | 0 | **1009 passed, 1 skipped, 14 subtests** — identical to the `cdd2218` baseline measured before any edit |
| `npm test` (`site_v2/`) | 0 | 76/76 |
| `npm run build` | 0 | 66 pages, `audit-seo: 67 built page(s) checked. OK.` |

⛔ **THE FULL-TREE LINT, AND THE CLAIM STATED NARROWLY.** `sqlfluff lint dbt_project/models` reports
**0 LT05 findings tree-wide** — the rule batch E shipped a violation of, because `| tail -3` cut the
FAIL away and left the `All Finished!` banner, which sqlfluff prints on failure too. 18 files still
FAIL on `LT02` (20) and `ST11` (12). **Every one of those 18 was proved byte-identical to `cdd2218`
by asking `git diff --quiet cdd2218 -- <file>` per file** — not by reading their paths and judging
them untouched. The intersection of {flagged} and {changed} is empty.
⚠ A first version of that intersection check used a `sed` that failed to compile, so it reported an
empty flagged set and therefore an empty intersection — a check that passes equally on the work and
on its absence. Recorded because that is precisely the class the CPO has ruled is not a check. It
was rewritten to ask git per file, and only then believed.

## #96 — the three lists, checked BY EYE again, and a hazard the handover did not carry

The three 22-name TEAM `accepted_values` lists (`int_competition_benchmarks.yml:27`, `:66`,
`shared.yml:2080`): each exactly **22 values, no duplicates, all three byte-identical to one
another**, and `finishing_efficiency_pct` present in all three. Verified on `cdd2218` before the
edit and again after.

⛔ **THREE *PLAYER* `accepted_values` LISTS ALSO CARRY THE BARE STEM.** Not in the handover; found by
mapping every occurrence to its owning model rather than reading names.
`int_competition_benchmarks.yml:105` (18 names) and `shared.yml:2186` (18) are identical to each
other and `shared.yml:1756` (14, the rate boards) is a third. All three still read
`finishing_efficiency` and none gained `finishing_efficiency_pct` — asserted, not assumed. A
bare-token sweep without model scoping would have corrupted every one of them.
