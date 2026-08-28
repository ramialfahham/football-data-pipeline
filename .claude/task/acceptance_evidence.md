# Acceptance evidence — batch E: the deserved chain

Branch `refactor/metric-rename-team-deserved-chain`, from main `db47b0a`.
Step 3 of the metric catalogue naming programme, **MR E of six**:
`sot_difference_per_match` → `shots_on_goal_difference_per_match`,
`sot_points_gap` → `deserved_points_gap`.

The four criteria are the CPO's STANDING set for MRs B–F. Reproduced, not re-drafted. Everything
below is read from the BUILT site under `site_v2/dist/`, from a test run, or from a guard
deliberately broken and watched.

criteria_demonstrated:
  - **Criterion 1 — no rendered metric name changed its words, in any locale.** Each locale renders **13** metric names; of those, the ones the untouched corpus `site/i18n/<loc>.json` also declares were compared word for word — EN **7**, DE **8**, FI **8**, and **wording differences: NONE** in all three. Source: `site_v2/dist/<loc>/2-bundesliga/matches/2026-08-28-eintracht-braunschweig-vs-hertha-bsc/index.html`.
  - **Criterion 2 — neither old name survives in the built site or the hand-written source.** `grep -rl` over `site_v2/dist/` → **0 files** of 66 built pages. `git grep -l` over `site_v2/src` excluding `src/data` → **0 files**. The generated sample holds **71** occurrences: the declared transient, closing with the final refresh after F.
  - **Criterion 3 — the label suite passes AND was watched failing.** `npm test`: **76 tests, 76 pass, 0 fail**. Broken on purpose: the seed's `shots_on_goal_difference_per_match` row reverted to `label_i18n_key = metrics.sot_difference_per_match.label` → **RED, 75 pass / 1 fail** — `AssertionError [ERR_ASSERTION]: label keys the catalogue does not declare in label_i18n_key: metrics.shots_on_goal_difference_per_match.label`. Restored, green again at 76/76.
  - **Criterion 4 — the built team page still shows the absent state where these rows would sit, in all three locales.** From `site_v2/dist/<loc>/teams/manchester-united-fc/index.html`: EN *"Not enough games this season to rank Manchester United FC against the league."*, DE *"Zu wenige Spiele in dieser Saison, um Manchester United FC mit der Liga zu vergleichen."*, FI *"Liian vähän otteluita tällä kaudella, jotta Manchester United FC voisi verrata sarjaan."*

## The transient does NOT grow this time, and that was the prediction

The contract predicted **13 → 13, unchanged**, written before any code, because neither name is
among the LOCKED 16 in `metricRows.ts` (0 hits). Measured on the built site:

| | before (`db47b0a`) | after |
|---|---|---|
| metric rows per comparison block, EN / DE / FI | 13 / 13 / 13 | **13 / 13 / 13** |
| rendered names REMOVED | — | **none** |
| rendered names ADDED | — | **none** |
| group headings | 7 | 7 |

Across all 19 fixture pages, both windows, all three locales: `[13]` (min 13, max 13). C took
16→15, D took 15→13, E moves it not at all. The set difference is empty in every locale — the
strongest form of "nothing on the page changed".

## ⛔ A MUTATION CORRECTED A RULE I RECORDED ON BATCH C

Batch C's entry claimed a green `npm test` "ONLY COVERS THE 16 ROWS `metricRows.ts` BINDS", inferred
from `shots_on_goal_pct` surviving that mutation. **Batch E disproves it.** The identical mutation on
`shots_on_goal_difference_per_match` — which is ALSO not one of the 16 — went **RED**.

⚠ I first recorded the correction by EDITING the batch C log entry in place. `scope-auditor` FAILed
that, citing `working_agreement.md:118` ("history stays append-only… Escalations are appended"), and
was right: the C block belongs to a merged, already-reviewed MR. Reverted verbatim — the log now
diffs as a pure append against `db47b0a` — and the correction is an appended entry instead. The
distinction against the CPO's "a correction replaces, it does not accumulate" rule: that governs
LIVING documents (comments, contracts, evidence); a DATED log gets appended to, because replacing
text in a dated block falsifies the chronology.

Read from the test source at `site_v2/scripts/check-metric-labels.test.mjs:36-38`:

    asked = rowKeys ∪ heroKeys

`rowKeys` are the `labelKey:` entries in `src/lib/metricRows.ts` (the 16); `heroKeys` are the keys
`src/components/team/DeservedHero.astro` passes to `metricLabel(lang, "…")`. Every `asked` key must
be declared in the seed's `label_i18n_key` column. **Covered set = the 16 plus the DeservedHero
keys, and nothing else.** `shots_on_goal_difference_per_match` is a DeservedHero key → covered.
`shots_on_goal_pct` is in neither → uncovered.

⚠ **IT TOOK THREE ATTEMPTS TO STATE THIS CORRECTLY.** Batch C said "only the 16"; my first
correction here said "`strings.ts` plus the `*.spec.json` files" — also wrong, since `strings.ts` is
the DEFINITION side (asserted in the opposite direction) and the specs are not read by this test at
all. `bi-analyst-reviewer` read the source and caught it.
⭐ **THE RULE: grep `metricRows.ts` AND `DeservedHero.astro` before relying on that guard.** And the
lesson under it — I wrote the rule twice from observed behaviour and was wrong about the mechanism
both times, while right about the observation both times. **When a guard's scope matters, read the
guard.** For step 4 the covered set is nearly empty, so almost none of the 35 player renames will be
caught by it; a different mutation target is needed there.

## ⛔ The one decision in E: `sotd` is NOT renamed

`sotd` is the export payload key (`scripts/export_site_data.py:230`), the frontend type field
(`types.ts:142`), the variable throughout `DeservedHero.astro`, and — decisively — an **i18n
PLACEHOLDER TOKEN inside user-facing translated sentences** in all three locales
(`strings.ts:94-95, 299-300, 476-477`, e.g. *"a shots-on-target difference of {sotd} per match"*).
Renaming it would force edits to six translated strings. **Wording is forbidden in a rename MR and
is §10.** It is a display-layer variable, not a catalogue `metric_id`; only the COLUMN references it
reads from were renamed.

Also NOT renamed, same class as batch D's bare `key_passes`: `mean_sot_difference`,
`sd_sot_difference`, `corr_sot_points` — local CTE aliases in the OLS block of
`int_team_season__deserved_vs_actual.sql:169-190`, verified NOT published columns (no `- name:` in
any yml) and NOT catalogue ids.

**Every protected token re-counted against the BASE COMMIT, not against a note:**

| token | base `db47b0a` | after |
|---|---|---|
| `sotd` | 230 | **230** |
| `mean_sot_difference` | 2 | **2** |
| `sd_sot_difference` | 2 | **2** |
| `corr_sot_points` | 2 | **2** |

⭐ The rename script also ABORTS before writing if any protected token's count would change — a
guard on the guard, added after D showed how easy a shared stem is to corrupt.

## Occurrence reconciliation, against the FINAL tree

Whole-token, excluding the generated sample and task artifacts: **base 85 → now 5.**

| count | where | disposition |
|---|---|---|
| 76 | in-scope files | renamed (`sot_difference_per_match` 55, `sot_points_gap` 21) |
| 4 | `dbt_project/models/docs/metric_columns.md` | **cleared** by regeneration — now 0 |
| 5 | `.claude/active_work.md` | the handover's own E row, struck through in this commit |

76 + 4 + 5 = 85. Plus one derived identifier: the named test
`int_team_season_sot_points_gap_contract` → `int_team_season_deserved_points_gap_contract`.

## Gates

| gate | result |
|---|---|
| `npm test` (site_v2) | **76 pass, 0 fail** |
| `astro build` | 66 pages, `audit-seo` 67 checked — OK |
| `sync_metric_docs_blocks.py --check` | OK (179 blocks) |
| `check_description_hygiene.py` | OK — 1604 descriptions, 241 docs blocks resolved |
| `check_layer_contract.py` · `check_ui_i18n_metrics.py` · `check_copy_gate.py` | OK |
| `pytest tests/test_export_site_data.py` | 45 passed |
| `dbt parse` | clean, 0 errors |
| `sqlfluff lint` (6 changed models, from the REPO ROOT) | clean — see note |
| `pytest -q` (repo root) | **1009 passed, 1 skipped, 1 warning, 14 subtests passed** in 552.22s — identical to the 1009 passed / 1 skipped baseline on `db47b0a`, so no new failure. This is the CLEAN re-run started after both mutations were restored; see the note at the end. |

⚠ **SQLFLUFF REPORTS 4 LT02 + 1 TMP ON `assert_metric_catalogue_expr_resolvable.sql`, AND THEY ARE
PRE-EXISTING.** Verified rather than asserted: the file was stashed and linted unmodified, and the
output is byte-identical. Cause is `run_query` being unresolvable under the jinja templater — the
exact class `CLAUDE.md` warns to check against main before believing.

## The three `accepted_values` lists, by eye — and #96 for the FOURTH batch running

`int_competition_benchmarks.yml:27`, `:66`, `shared.yml:2080`: **22 values each,
`shots_on_goal_difference_per_match` present, no old names, no duplicates.** `sot_points_gap` was
never one of the 22 and was correctly not added.

**Mutation 2 — one entry reverted. SURVIVED the entire offline suite** (`check_layer_contract`,
`check_ui_i18n_metrics`, `sync_metric_docs_blocks --check`, `check_description_hygiene`). That is
**#96 reproduced on `!114`, `!119`, `!120` and now E — four consecutive batches.**
`platform-reviewer` recommended on `!120` closing it with a small offline test alongside E; that is
a NEW MECHANISM and therefore not taken here.

⚠ The first `pytest` run overlapped the mutations and was DISCARDED rather than reported. The figure
in the Gates table — **1009 passed, 1 skipped, 14 subtests, 552.22s** — is a clean re-run started
after both mutations were restored. Same handling as batch D.
⚠ **THAT NUMBER WAS MISSING FROM THIS DOCUMENT UNTIL `platform-reviewer` FAILed round 1 for it.**
The Gates row read "see below" and nothing below supplied it, while the closing sentence referred to
"the figure above" as though one were shown. The run had happened and was clean; I simply never
wrote the result down. ⭐ THE RULE: **a gate is not evidenced by a sentence saying it passed — the
number goes in the artifact.** "See below" with nothing below is indistinguishable, to a reader,
from a check that was never run.
