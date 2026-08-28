# Acceptance evidence — batch C: the three `shooting` share metrics

Branch `refactor/metric-rename-team-shooting-shares`, from main `9e2aaf9`.
Step 3 of the metric catalogue naming programme, **MR C of six**:
`shot_accuracy` → `shots_on_goal_pct`, `danger_zone_ratio` → `shots_inside_box_pct`,
`shot_share` → `shots_share_pct`.

The four criteria are the CPO's STANDING set for MRs B–F ("do it", recorded in `escalations.log`
beside the list it answered). Reproduced, not re-drafted, and not re-put to him. Everything below is
read from the BUILT site under `site_v2/dist/`, from a test run, or from a guard deliberately broken
and watched.

criteria_demonstrated:
  - **Criterion 1 — no rendered metric name changed its words, in any locale.** Read back from the built fixture pages, the surface that renders the metric block. Each locale renders **15** metric names; of those, the ones the untouched CPO-validated corpus `site/i18n/<loc>.json` also declares were compared word for word — EN **8** compared, DE **9**, FI **9**, and **wording differences: NONE** in all three. The one reported divergence is pre-existing and already exempted by name in `check-metric-labels.test.mjs`: EN `finishing_efficiency` renders `% Goals per shot on target` where the corpus says `% Conversion rate`. Source pages: `site_v2/dist/<loc>/2-bundesliga/matches/2026-08-28-eintracht-braunschweig-vs-hertha-bsc/index.html`.
  - **Criterion 2 — no old name survives in the built site or the hand-written source.** `grep -rl` over `site_v2/dist/` for all three names → **0 files** of 66 built pages plus every asset. `git grep -l` over `site_v2/src` excluding `src/data` → **0 files**. The generated sample still holds **267** occurrences: that is the declared transient, and it closes with the final refresh after F.
  - **Criterion 3 — the label suite passes AND was watched failing.** `npm test`: **76 tests, 76 pass, 0 fail**. Then broken on purpose: the seed's `shots_inside_box_pct` row was reverted to `label_i18n_key = metrics.danger_zone_ratio.label` and the suite went **RED — 75 pass, 1 fail** — `AssertionError [ERR_ASSERTION]: label keys the catalogue does not declare in label_i18n_key: metrics.shots_inside_box_pct.label`. Restored, green again at 76/76.
  - **Criterion 4 — the built team page still shows the absent state where these rows would sit, in all three locales.** Read from `site_v2/dist/<loc>/teams/manchester-united-fc/index.html`: EN *"Not enough games this season to rank Manchester United FC against the league."*, DE *"Zu wenige Spiele in dieser Saison, um Manchester United FC mit der Liga zu vergleichen."*, FI *"Liian vähän otteluita tällä kaudella, jotta Manchester United FC voisi verrata sarjaan."* That page's featured season has one game played, below the `>= 3 finished games` benchmark floor, so it is unchanged by the rename and is recorded so the absence is never read as a defect of it.

## The declared transient came out at exactly the predicted number

The contract predicted **16 → 15, no group heading lost**, written before any code was changed.
Measured on the built site afterwards:

| | before (`9e2aaf9`) | after |
|---|---|---|
| metric rows per comparison block, EN / DE / FI | 16 / 16 / 16 | **15 / 15 / 15** |
| group headings | 7 | **7 — none lost** |
| blocks with no Goalkeeping heading | 0 | **0** |

Not a spot check: across all 19 fixture pages the w1 and w2 row counts are both `[15]` (min 15,
max 15) in every locale. The rendered-name set difference isolates the cause — the only name removed
is `danger_zone_ratio`'s label in each locale (EN `% Shots from box`, DE `% Schüsse aus dem
Strafraum`, FI `% Laukaukset boksista`) and **nothing was added or otherwise removed**. `Shooting`
keeps its heading because it still has 3 of its 4 rows, unlike `!116` where `saves_pct` was
Goalkeeping's only row.

## Gates

| gate | result |
|---|---|
| `npm test` (site_v2) | **76 tests, 76 pass, 0 fail** |
| `node scripts/check-page-specs.mjs` | 4 pages validated — OK |
| `astro build` | 66 pages built, `audit-seo` 67 checked — OK |
| `sync_metric_docs_blocks.py --check` | OK (179 blocks regenerated from the seed) |
| `export_metric_definitions_json.py` + `pytest tests/test_metric_bindings.py` | 13 definitions regenerated; **4 passed** on byte-identity |
| `check_description_hygiene.py` | OK — 1604 descriptions, 241 docs blocks resolved, rendered lengths within 1024/16384 |
| `check_layer_contract.py` | OK |
| `check_ui_i18n_metrics.py` | OK |
| `check_copy_gate.py` | OK |
| `dbt parse` | clean, zero dangling `doc()` |
| `sqlfluff lint` (all 8 changed models, from the REPO ROOT) | **All Finished!** — clean |
| `pytest -q` (repo root) | **1009 passed, 1 skipped, 14 subtests** — identical to the count on `9e2aaf9`, so no new failure |

## The three `accepted_values` lists — checked by eye, because #96 means nothing else does

`int_competition_benchmarks.yml:27`, `int_competition_benchmarks.yml:66`, `shared.yml:2080`.
Each re-counted after the edit: **22 values, both new names present, zero old names, no duplicates.**
`shot_share` is correctly NOT among the 22 — it is not a benchmarked metric and was not added.

## Mutations — three run, and the two that did NOT go red are the informative ones

**Mutation 1 — stale `label_i18n_key` on `shots_on_goal_pct`. SURVIVED `npm test` (76/76 green),
caught by `pytest`.** Not a hole, and worth stating precisely rather than filing as a defect:
`shots_on_goal_pct` is not one of the 16 rows `metricRows.ts` binds, so the site's label test has
nothing to check it against — correctly. The guard that did fire is
`tests/test_metric_bindings.py::test_regenerated_json_matches_committed`, which regenerates
`metric_definitions.json` from the seed plus the bindings and asserts byte-identity. ⭐ THE LESSON:
"the label test is green" is only evidence for the metrics that test actually reaches. Choosing a
non-displayed metric for the criterion-3 mutation would have proved nothing, and nearly did.

**Mutation 2 — the same mutation on `shots_inside_box_pct`, which IS one of the 16. RED**, as quoted
under criterion 3. This is the mutation criterion 3 rests on.

**Mutation 3 — one entry of the 22-name `accepted_values` list in `shared.yml` reverted to
`danger_zone_ratio`. SURVIVED the ENTIRE offline suite**: `sync_metric_docs_blocks.py --check`,
`check_layer_contract.py`, `check_ui_i18n_metrics.py`, `check_description_hygiene.py` and
`dbt parse` all green. That reproduces `!114`'s finding on this batch and is why the three lists are
checked by eye above. Only the warehouse `accepted_values` test inside `data:build:mr` catches it.
Filed as **#96**; not fixed here, because a new guard is a new mechanism and belongs in a task about
the guard.

## ⛔ A RENAME CLASS THAT WORD-BOUNDARY REPLACEMENT CANNOT REACH, and a gate caught it, not me

`\b` fails against `_`, because `_` is a word character. So `\bshot_accuracy\b` does not match
inside `home_shot_accuracy_recent`, `danger_zone_ratio_this_season`, or
`std_team_shot_accuracy_in_range`. I anticipated the first family and handled it as an explicit
pass; I did **not** anticipate the other two, and the rename shipped incomplete until
`check_description_hygiene.py` went red on **six dangling `doc()` references**
(`danger_zone_ratio_this_season__team` and its siblings). A third pass then swept the class rather
than the instance, renaming **31 more occurrences** across two families:

- the yoy forms `_this_season` / `_prev_season` / `_delta_yoy` and their `__team` doc-block names
- **nine** named dbt tests: `std_team_<id>_in_range`, `momentum_team_<id>_in_range`,
  `mmi_home_<id>_in_range`, `mmi_away_<id>_in_range`, `team_profile_<id>_in_range`
  (precedent: `!116` renamed `momentum_team_saves_pct_in_range` the same way)

⛔ ONE FORM IS PROTECTED AND WAS PROGRAMMATICALLY EXCLUDED: `<id>_recent` standing alone is the
retired MVP's own `live_id` in `metric_bindings.csv`. `check_ui_i18n_metrics.py` maps it THROUGH the
bindings to the catalogue id, so renaming it would break the mapping while changing nothing a
catalogue reader sees. Verified untouched: `shot_accuracy_recent` and `danger_zone_ratio_recent`
both still present, 3 occurrences each.

⭐ THE RULE: **on an identifier rename, sweep for the metric name as a SUBSTRING of other
identifiers, not as a whole token.** The whole-token form is what you want to CHANGE; the substring
form is what tells you where the derived names are hiding.

## Occurrence reconciliation, so nothing is silently left behind

Measured before any edit, from the repo root: **412 occurrences** — `shot_accuracy` 177,
`danger_zone_ratio` 185, `shot_share` 50 — of which **267 are the generated sample** and **145 are
live surfaces**. Of those 145: **128** were replaced as whole tokens by the rename passes, **8** were
cleared by REGENERATING the two generated artifacts, and **9** remain, each declared. 128 + 8 + 9 =
145. Separately, **51** derived identifiers were replaced (20 `_recent` aliases + 31 yoy forms and
test names); those are substrings of longer tokens and so are not part of the 145.

| count | where | disposition |
|---|---|---|
| 6 | `dbt_project/models/docs/metric_columns.md` | **cleared** by regenerating with `sync_metric_docs_blocks.py` — 0 remain |
| 2 | `site/match-preview/metric_definitions.json` | **cleared** by regenerating with `export_metric_definitions_json.py` — 0 remain |
| 4 | `site/team-season/index.html` | STAYS — frozen PAGE CODE of the retired MVP; `!116` left the byte-identical construct alone |
| 1 | `docs/working_agreement.md:348` | STAYS — Appendix A anti-pattern A1 names a **player** `shot_accuracy` that was invented and REJECTED |
| 1 | `dbt_project/models/5_marts/shared/mart_player_profile.sql:16` | STAYS — same rejected player metric, in a comment |
| 3 | `.claude/active_work.md` | STAYS — the handover's own batch C table, struck through in this commit |

⚠ **THIS TABLE WAS WRONG IN ROUND 1 AND `bi-analyst-reviewer` CAUGHT IT.** It listed the first two
rows under "why it stays" and counted them in a total of 17. They do not stay: regenerating cleared
them, and a direct grep of both files returns **0**. The reconciliation had been computed at the
moment the rename passes ran and never re-checked against the final tree — the exact failure #71
names. Re-verified now: 9 remain, in the four files marked STAYS.

⚠ ONE MORE MEASUREMENT ERROR, MINE, CAUGHT BEFORE IT REACHED THE CONTRACT. The first occurrence
count came out 38 / 46 / 21 and looked entirely plausible. The shell was still inside `dbt_project/`
from the `dbt ls` call, and `git grep` scopes to the CWD. CWD persists between calls; every figure
above was re-taken with `cd /d/Projects/football-data-pipeline` asserted in the same command.

⚠ AND A THIRD SUBSTRING ARTIFACT, in a throwaway diff script rather than in the evidence: an ad-hoc
before/after comparison reported FI as 15 → 14 while the measurement itself said 16 → 15. Its regex
required a trailing newline the output file does not have, so it dropped the last FI name from both
sides equally. The evidence script's own counts were correct; the ad-hoc one was not, and the
disagreement is what exposed it.
