# Acceptance evidence — batch D: the two `passing` metrics

Branch `refactor/metric-rename-team-passing`, from main `62d3b18`.
Step 3 of the metric catalogue naming programme, **MR D of six**:
`pass_accuracy` → `passes_accuracy_pct`, `key_passes_per_match` → `passes_key_per_match`.

The four criteria are the CPO's STANDING set for MRs B–F ("do it", recorded in `escalations.log`
beside the list it answered). Reproduced, not re-drafted. Everything below is read from the BUILT
site under `site_v2/dist/`, from a test run, or from a guard deliberately broken and watched.

criteria_demonstrated:
  - **Criterion 1 — no rendered metric name changed its words, in any locale.** Read back from the built fixture pages. Each locale renders **13** metric names; of those, the ones the untouched CPO-validated corpus `site/i18n/<loc>.json` also declares were compared word for word — EN **7** compared, DE **8**, FI **8**, and **wording differences: NONE** in all three. Source pages: `site_v2/dist/<loc>/2-bundesliga/matches/2026-08-28-eintracht-braunschweig-vs-hertha-bsc/index.html`.
  - **Criterion 2 — neither old name survives in the built site or the hand-written source.** `grep -rl` over `site_v2/dist/` → **0 files** of 66 built pages plus every asset. `git grep -l` over `site_v2/src` excluding `src/data` → **0 files**. The generated sample still holds **243** occurrences: the declared transient, closing with the final refresh after F.
  - **Criterion 3 — the label suite passes AND was watched failing.** `npm test`: **76 tests, 76 pass, 0 fail**. Then broken on purpose, and deliberately on a metric that IS one of the rendered 16 — batch C proved a mutation on a non-displayed metric leaves the suite green and proves nothing. The seed's `passes_accuracy_pct` row was reverted to `label_i18n_key = metrics.pass_accuracy.label` and the suite went **RED — 75 pass, 1 fail** — `AssertionError [ERR_ASSERTION]: label keys the catalogue does not declare in label_i18n_key: metrics.passes_accuracy_pct.label`. Restored, green again at 76/76.
  - **Criterion 4 — the built team page still shows the absent state where these rows would sit, in all three locales.** Read from `site_v2/dist/<loc>/teams/manchester-united-fc/index.html`: EN *"Not enough games this season to rank Manchester United FC against the league."*, DE *"Zu wenige Spiele in dieser Saison, um Manchester United FC mit der Liga zu vergleichen."*, FI *"Liian vähän otteluita tällä kaudella, jotta Manchester United FC voisi verrata sarjaan."* One game played, below the `>= 3 finished games` benchmark floor, so this is unchanged by the rename and recorded so the absence is never read as a defect of it.

## The declared transient came out at exactly the predicted number

The contract predicted **15 → 13, no group heading lost**, written before any code changed.

| | before (`62d3b18`) | after |
|---|---|---|
| metric rows per comparison block, EN / DE / FI | 15 / 15 / 15 | **13 / 13 / 13** |
| group headings | 7 | **7 — none lost** |

Across all 19 fixture pages the w1 and w2 row counts are both `[13]` (min 13, max 13) in every
locale. The rendered-name set difference isolates the cause — exactly the two `Passing` labels are
removed per locale and **nothing is added**:

| locale | removed |
|---|---|
| EN | `% Pass accuracy`, `Ø Key passes` |
| DE | `% Angekommene Pässe`, `Ø Schlüsselpässe` |
| FI | `% Syöttötarkkuus`, `Ø Avainsyötöt` |

`Passing` keeps its heading: it had 3 rows and loses 2, leaving `passes_per_match`.

⚠ The comparison script that produced this now ASSERTS its own parsed count against the header count
it read. On batch C an ad-hoc version of it silently dropped the last name of a locale (its regex
needed a trailing newline the file does not have) and reported FI as 15→14 against a true 16→15. It
cannot fail that way unnoticed again.

## ⛔ The whole risk of this batch was protecting the player metrics — verified, not assumed

Three different things share these stems. The rename classified **every** token containing a stem
and printed its decision, so the protection is auditable rather than a trusted exclusion list:
**147 renamed, 34 protected.**

Each protected token re-counted after the passes, against the **base commit** rather than against a
number written down earlier:

| token | base | after | |
|---|---|---|---|
| `pass_accuracy_pct` (PLAYER metric) | 51 | **51** | untouched |
| `pass_accuracy_recent` (retired MVP `live_id`) | 3 | **3** | untouched |
| `key_passes_per90` (PLAYER) | 14 | **14** | untouched |
| `passes_key` (PLAYER) | 83 | **83** | untouched |
| `key_passes_this_season` (PLAYER yoy) | 6 | **6** | untouched |
| the 4 `*_pass_accuracy_pct_in_range` PLAYER tests | 4 | **4** | all present |

⚠ I briefly mis-stated `passes_key`'s baseline as 15 while checking this — 15 was `key_passes`, a
different token. Checking against `git grep <base-sha>` rather than against my own earlier note is
what settled it, and is the only method used above.

⭐ Bare `key_passes` (15, unchanged) is deliberately NOT renamed. It is created in
`int_legs__team_from_players.sql:28` as `sum(passes_key) as key_passes` and consumed at
`int_team_season__metrics_cumulative.sql:150`. It is not a catalogue `metric_id` (0 seed rows) and
not a declared column of `int_team_season` (no `- name: key_passes` in any yml), so
`assert_no_uncatalogued_season_metric` does not reach it. The recorded rule "a metric and its column
may legitimately differ" covers it.
⚠ In an earlier note I described it as sitting "alongside `tackles`/`interceptions`/`blocks`". That
was a STRUCTURAL observation — four consecutive, identically shaped lines — and the CPO rightly read
it as implying a semantic family. Key passes are creative, not defensive. The structural point
stands; the phrasing was wrong.

## Occurrence reconciliation, verified against the FINAL tree

⚠ This is the check `bi-analyst-reviewer` FAILed batch C round 1 for: the arithmetic there was taken
when the passes ran and never re-checked. Every figure below is a live count, with the base taken
from `62d3b18` directly.

Whole-token occurrences, excluding the generated sample and task artifacts:
**base 103 → now 7.**

| count | where | disposition |
|---|---|---|
| 93 | in-scope files | renamed as bare tokens (`pass_accuracy` 56, `key_passes_per_match` 37) |
| 3 | `metric_columns.md` (2) + `metric_definitions.json` (1) | **cleared** by regeneration — both now 0 |
| 2 | `site/team-season/index.html` | STAYS — frozen PAGE CODE of the retired MVP (`!116`/`!119` precedent) |
| 5 | `.claude/active_work.md` | STAYS — the handover's own D rows, updated in this commit |

93 + 3 + 7 = 103. Separately, **54 derived identifiers** were renamed (10 `_recent` aliases, 40 yoy
forms and `__team` doc blocks, 4 team `*_in_range` test names) — substrings of longer tokens, so not
part of the 103.

## Gates

| gate | result |
|---|---|
| `npm test` (site_v2) | **76 tests, 76 pass, 0 fail** |
| `node scripts/check-page-specs.mjs` | 4 pages validated — OK |
| `astro build` | 66 pages built, `audit-seo` 67 checked — OK |
| `sync_metric_docs_blocks.py --check` | OK (179 blocks) |
| `export_metric_definitions_json.py` + `pytest tests/test_metric_bindings.py` | 13 definitions regenerated; **4 passed** on byte-identity |
| `check_description_hygiene.py` | OK — 1604 descriptions, **241 docs blocks resolved**, no dangling `doc()` |
| `check_layer_contract.py` · `check_ui_i18n_metrics.py` · `check_copy_gate.py` | OK |
| `dbt parse` | clean, zero errors |
| `sqlfluff lint` (all 8 changed models, from the REPO ROOT) | **All Finished!** |
| `pytest -q` (repo root) | **1009 passed, 1 skipped, 14 subtests** — identical to the count on `62d3b18`, so no new failure. This is the CLEAN re-run; see the mutation note below for why the first run was discarded. |

## The three `accepted_values` lists — by eye, because #96 means nothing else does

`int_competition_benchmarks.yml:27`, `:66`, `shared.yml:2080` — each re-counted after the edit:
**22 values, both new names present, zero old names, no duplicates.**

## Mutations

**Mutation 1 — stale `label_i18n_key` on `passes_accuracy_pct`, which IS one of the rendered 16.
RED**, quoted under criterion 3. Chosen deliberately: batch C showed the same mutation on a
non-displayed metric leaves `npm test` at 76/76 because `metricRows.ts` never binds it.

**Mutation 2 — one entry of the 22-name `accepted_values` list in `shared.yml` reverted to
`key_passes_per_match`. SURVIVED the entire offline suite**: `check_layer_contract.py`,
`check_ui_i18n_metrics.py`, `sync_metric_docs_blocks.py --check` and
`check_description_hygiene.py` all green. That is **#96 reproduced for the third batch running**
(`!114`, `!119`, and now here) rather than assumed from the earlier two. Only the warehouse
`accepted_values` test in `data:build:mr` catches it. Not fixed here — a new guard is a new
mechanism and belongs in a task about the guard.

⚠ Both mutations were restored before the final gate run, and `pytest` was restarted from scratch
afterwards: the first run had been launched before mutation 1 and was live while the seed was
broken, so its result was discarded rather than reported.
