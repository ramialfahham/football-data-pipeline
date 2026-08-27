# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-27**. **main `4975934`** (after `!116`). The METRIC CATALOGUE NAMING
PROGRAMME step 3 is running: **4 of 12 team renames merged**, `!114` + `!116`. `#92` is FIXED
(`!115`). **Nothing else is in flight.** **GITLAB** (`glab`, MRs); runner `ci-runner-01`.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ NEXT ACTION: the export-sample refresh, PULLED FORWARD ON CPO INSTRUCTION

⭐ **His words: "116 merged, do the refresh".** It was planned as the LAST step of the programme;
he moved it to NOW. Do this before renaming batch C.

**WHY IT MOVED.** A renamed FIXTURE field drops its row from the 16-row comparison on all 51 fixture
pages until the sample carries the new key — `MetricComparison.astro`'s `hasData()` omits a row with
no value. `!116` measured **16 rendered metric names → 14**, and the whole **Goalkeeping** heading
vanished because `saves_pct` was its only row. C–F rename five more fixture fields, so the gap would
grow to ~10 missing rows. `!114` did not do this (its renames were team-binding only).

**THE RECIPE** (precedent `!109`, "refresh the committed export sample after #90"):
1. ⛔ **WAIT for `data:build:main` to be GREEN on `4975934`** — the export reads PROD, so the new
   columns must exist there first. Check `glab ci list`.
2. Branch from the main that carries `!116`. Contract: scope is `site_v2/src/data/**` + artifacts.
3. `python scripts/export_site_data.py --entities teams,fixtures --out site_v2/src/data`
   — ⚠ that `--entities` list is LOAD-BEARING, copy it exactly from `.gitlab-ci.yml`'s
   `deploy:export`. **Never hand-edit the sample.**
4. Rebuild the site and re-measure: the count must return to **16** rendered names per locale and
   `Goalkeeping` must reappear. That is the acceptance evidence.
5. ⚠ The sample is a gitignore-pinned SET (22 tracked files). Its README's "18 files" is stale.

## ⭐ THEN: renaming batches C–F. Names are FIXED; do not re-derive

⛔⛔ **THE AUTHORITY IS `.claude/task/escalations.log`** — the block "THE METRIC CATALOGUE NAMING
PROGRAMME" (rulings 2026-08-26, full tables appended 2026-08-27). **CITE IT, never a plan file: two
MRs were FAILed for citing one.** Remaining, verbatim from its "TEAM, 12 REMAINING" table:

| MR | renames |
|---|---|
| **C** shooting shares | `shot_accuracy`→`shots_on_goal_pct` · `danger_zone_ratio`→`shots_inside_box_pct` · `shot_share`→`shots_share_pct` |
| **D** passing | `pass_accuracy`→`passes_accuracy_pct` · `key_passes_per_match`→`passes_key_per_match` |
| **E** deserved chain | `sot_difference_per_match`→`shots_on_goal_difference_per_match` · `sot_points_gap`→`deserved_points_gap` |
| **F** alone | `finishing_efficiency`→`finishing_efficiency_pct` |

⭐ **F IS LAST AND ALONE ON PURPOSE**: `finishing_efficiency` exists for BOTH entities, so the doc
block splits/merges and every occurrence must be classified by reading the model it sits on. Also
`site_v2/scripts/check-metric-labels.test.mjs` carries an EN exemption keyed on the literal string
`finishing_efficiency` — re-point it or the test compares v2's label against the corpus's
"% Conversion rate" and goes red.
⚠ **D's `pass_accuracy` must not match the player's `pass_accuracy_pct`** (a step-4 name). Anchor it.
⚠ **STEP 4** = the 35 player renames. **STEP 5** = the 9 English labels ("on target"→"on goal"),
which includes `sot_difference_per_match`'s label — do NOT do it in E.

## ⭐ THE PER-MR RECIPE (proven on `!114` and `!116`)

⭐ **THE FOUR ACCEPTANCE CRITERIA ARE STANDING FOR B–F** (CPO "do it", in the log). Do not re-draft
or re-ask per MR: (1) rendered metric names unchanged in all 3 locales, vs the untouched
`site/i18n` corpus; (2) neither old name in `dist/` or `src/` outside the sample; (3) `npm test`
green AND watched going red on a stale key; (4) the team page's absent state recorded.

1. Branch from the main carrying the previous MR's record. Contract on a CLEAN tree, with
   `acceptance_criteria:` at column 0 and the `dbt ls --select int_team_season__metrics_cumulative+`
   lineage PASTED.
   ⚠ **THE LINEAGE IS EVIDENCE, NOT THE FILE LIST.** `mart_team_momentum`,
   `int_team_momentum__metrics` and `mart_matchday_insights` are edited but absent from it —
   momentum recomputes the metrics itself (#93).
2. Rename: seed (`metric_id` AND `label_i18n_key`), the cumulative model, yoy, the UNPIVOT list,
   **THREE** `accepted_values` lists (`int_competition_benchmarks.yml` ×2, `shared.yml` ×1), the
   marts + ymls, `docs/wireframes/`, `site_v2/src` (metricRows, strings, specs, components).
3. **Frozen `site/` — ONLY where a live gate forces it**, and only catalogue-id plumbing:
   `metric_bindings.csv`'s `catalogue_metric_id` + `home_column`/`away_column`, and the
   `metrics.<id>` KEYS in `site/i18n/*.json`. **Never wording, never page code, never `live_id`.**
   Then REGENERATE `metric_definitions.json`. C, D and F all have names in the bindings.
4. Regenerate, never hand-edit: `sync_metric_docs_blocks.py`, `export_metric_definitions_json.py`.
5. Gates: `sync_metric_docs_blocks.py --check`, `check_description_hygiene.py`,
   `check_layer_contract.py`, `check_ui_i18n_metrics.py`, `pytest` (1009 on `4975934`), `dbt parse`,
   `sqlfluff lint` from the REPO ROOT, `cd site_v2 && npm test && node scripts/check-page-specs.mjs`.
6. Mutations watched going RED, then restored. Evidence read from the BUILT site.

## ⛔ TRAPS THAT COST TIME THIS SESSION — read before measuring anything

⛔ **A SUBSTRING TEST IS NOT A PRESENCE TEST.** My evidence script matched `Ø Corners` inside
`Ø Corners against` and reported 16 rendered names when 14 was true — it would have certified two
MISSING rows as present. This metric set is full of `X` / `X against` pairs. Subtract the longer
label's occurrences. The fixed script is in the session scratchpad; rewrite it if lost.
⛔ **CWD PERSISTS BETWEEN Bash CALLS.** `pytest` launched from `site_v2/` printed "no tests ran in
0.14s" — a green-looking result that ran NOTHING. Always `cd /d/Projects/football-data-pipeline &&`.
⛔ **CHECK THE FIXTURE SURFACE BEFORE CALLING A TRANSIENT INVISIBLE.** The team page and the fixture
page bind different fields; a rename can be invisible on one and delete a whole section on the other.
⛔ **THE CONTRACT MAY ONLY BE (RE)WRITTEN ON A CLEAN TREE.** Stash by EXPLICIT PATH
(`git stash push -m TEMP-… -- dbt_project docs site site_v2 .claude/active_work.md`), edit, pop
immediately, check `git stash list`. `.claude/active_work.md` counts as dirty; `.claude/task/` does
not. ⚠ `git reset --hard` is blocked; use `git checkout HEAD -- <path>`.
⛔ **NEVER WRITE A REVIEWER'S VERDICT YOURSELF.** ⚠ Rewriting `review.md` for a new round DROPS the
standing verdicts — re-add every required reviewer.
⛔⛔ **INVERT THE NUMBER SWEEP**: pull EVERY integer out of the artifacts and ask if it is still true
(#71). A correction that lands in one paragraph and not its neighbour is the failure this rule names.
⚠ **Heredocs are BLOCKED** for file writes, scratchpad included — use Edit/Write.
⚠ **`--review-patch` writes to STDOUT** — redirect it or the patch is the PREVIOUS task's.
⚠ **`git checkout <branch>:<path>` MANGLES**; export `MSYS_NO_PATHCONV=1` first.
⚠ **OPERATIONAL NOTES ARE IN `CLAUDE.md`** (dbt CLI, SQLFluff, commit mechanics) — not capped.
**FIRST ACTION: `git stash list`.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX. One must never be rebuilt:
**`feat/player-overview-tab`**.

## ⭐ THE METRIC LAYER — traps that outlive any one task

⭐ **THE PATTERN:** `noun [_qualifier] [_against] [_player] [_form]`; `_form` = `_per_match` (team),
`_per90` (player), `_pct` (a proportion).
⛔ **RENAMING A METRIC CAN SPLIT ITS DESCRIPTION BLOCK.** If the new name exists for BOTH entities
with different formulas, the generator replaces the bare block with `__team`/`__player` and DANGLES
every reference. Count references for BOTH names before writing the contract. **This fires on F.**
⚠ **REGENERATE** `sync_metric_docs_blocks.py` after the seed AND after any derived column — its
second input is the model YAML.
⛔ **A METRIC AND ITS COLUMN MAY LEGITIMATELY DIFFER.** `goals`, `corners`, `saves` are metrics whose
per-match provider columns keep provider names. Step 3's twelve are different: they ARE columns, and
`assert_no_uncatalogued_season_metric` forces the column to follow the metric_id.
⛔ **#95 — read before touching any slug or team name.** `team_slug` is documented PERMANENT and is
RE-DERIVED FROM `team_name` ON EVERY BUILD, so correcting a name MOVES A PUBLISHED URL. Team 33
already moved to `manchester-united-fc`. Team-names programme PAUSED part-way (97 of ~130 Pool 1).

## ⛔ OPEN, ALL THE CPO'S

- **#96** — NO offline gate pins the three 22-name `accepted_values` lists to the model columns.
  Proved by a mutation that survived the whole offline suite; only `data:build:mr` catches a miss.
  **Check those three lists by eye in every remaining batch.**
- **#97** — `docs/roles/platform_reliability.md` still names the CI/prod shared-dataset hazard fixed
  under #668. Filed with the instruction to sweep all of `docs/roles/`, not just that line.
- **#92** — FIXED in `!115`, recorded here because the shape matters: `--favor-state` is gone from
  `data:build:mr`'s **`dbt test`** line (it STAYS on `dbt build` — ⛔ never "match the two lines up"),
  and **the CI datasets are PER MERGE REQUEST** (`ci_mr<IID>_*`). ⛔ **Nothing expires or deletes
  them, by CPO instruction** — "you do nothing where you come any close to introducing the risk of
  deleting the warehouse". ~6 GB, ~12¢/month. Do not add a TTL, a drop or a cleanup step.
- **#93** — `mart_team_momentum` is a SECOND copy of ~20 team formulas and has drifted. ⚠ Its file
  carries a CPO attribution the log contradicts; put that to him as a contradicted attribution.
- **#94** naming grammar (largely superseded) · **#89** `finishing_efficiency` tier · **#82** ~40
  blank descriptions · **#83** no competition-classification core dim · **#91** the parked
  value-equivalence checker, which waits for the renaming to finish (file in the `parked/` folder
  beside the memory dir; yml companion in the stash "PARK: value-equivalence test").

## ⭐ OTHER STANDING STATE

✅ **SETTLED, do not re-propose.** BROWSE DROPPED (`!80`) — home renders next matches ALONE. TOP
TEAMS = one per league, not pooled.
⛔ **Points is a synthetic 3-1-0 tally in EVERY competition** (`int_team_season_record.sql:73`) — FA
Cup renders 0, Europa League 32 against a real 18. **The mart must emit NULL.** Blocks the team
Overview for cups.
⛔ **The deserved-vs-actual hero is EXACT ONLY for a COMPLETED season.** Two CPO decisions OPEN
before it touches live data: how to render the fitted line mid-season, and from which matchday.
⚠ **The metric rows render on NO built page today**: the sample's featured season (team 33, PL 2026)
has 1 game, below the `>= 3 finished games` benchmark floor, so the team Performance tab shows
"not enough games to rank". Do not write an acceptance criterion that reads a metric ROW off the
team page. The 16 metric NAMES do render on the fixture pages.
