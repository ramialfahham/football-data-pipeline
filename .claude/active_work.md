# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-28**. **main `db47b0a`** (after `!120`, batch D). The METRIC CATALOGUE
NAMING PROGRAMME step 3: **9 of 12 team renames merged** (`!111`, `!112`, `!114`, `!116`, `!119`,
`!120`), and **batch E is BUILT on `refactor/metric-rename-team-deserved-chain`** — 2 more,
awaiting review/merge. **Only F remains after it** (`finishing_efficiency` → `finishing_efficiency_pct`).
`#92` FIXED (`!115`). The export sample was rolled forward by `!118` to 19 fixture payloads.
**GITLAB** (`glab`, MRs); runner `ci-runner-01`.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ NEXT ACTION: batch D once C merges. Names are FIXED; do not re-derive

## ⛔ THE RENAME METHOD — proven over C, D and E; use it for F and all 35 player renames

⛔⛔ **`\b` FAILS AGAINST `_`.** A word-boundary replace cannot reach `home_<id>_recent`,
`<id>_this_season`/`_prev_season`/`_delta_yoy`, or `std_team_<id>_in_range`. C shipped incomplete
until `check_description_hygiene.py` went red on six dangling `doc()` refs.
⭐ **THE METHOD: classify EVERY token containing the stem once, and PRINT the decision**
(D: 147 renamed / 34 protected; E: 77 renamed, 4 protected tokens asserted unchanged). A reviewer
can check a decision list; nobody can check an exclusion you kept in your head. E's script
additionally ABORTS if a protected token's count would change — cheap and it fails loudly.
⭐ Sweep before AND after: `git grep -ohE "[a-z_0-9]*(<old>)[a-z_0-9]*" | sort | uniq -c`.
⭐ **Re-count every protected token against `git grep <base-sha>`, never against a number you wrote
down** — that caught a slip of mine mid-check on D.
⛔ **PROTECT `<id>_recent` STANDING ALONE** — the retired MVP's `live_id`; `check_ui_i18n_metrics.py`
maps it THROUGH the bindings. `home_`/`away_` forms are NOT protected.
⛔ **PROTECT ANYTHING AN i18n STRING INTERPOLATES.** E's `sotd` is the export key, the frontend
field AND a `{sotd}` placeholder inside translated sentences in all three locales — renaming it
would have forced wording edits, which are forbidden here and are §10.
⛔ **F NEEDS BOTH PASSES**: `finishing_efficiency` has **16** yoy forms AND exists for BOTH
entities, so the player rows must be excluded token by token exactly as `pass_accuracy_pct` was in D.
⚠ **CATALOGUE-ONLY IS IMPOSSIBLE for the 12** and the CPO asked why — the answer, if it comes up
again: `assert_no_uncatalogued_season_metric.sql` requires every metric-bearing column of
`int_team_season__metrics` to be a registered `metric_id`, so moving the id without the column turns
`data:build:mr` red. That is what separates these from `!111`/`!112`, which were seed-only.
⭐ **THE LABEL GUARD COVERS `metricRows.ts`'s 16 PLUS the keys `DeservedHero.astro` asks for —
NOTHING ELSE.** Read from `check-metric-labels.test.mjs:36-38`: `asked = rowKeys ∪ heroKeys`.
So `shots_on_goal_difference_per_match` (a DeservedHero key, not one of the 16) goes RED on a stale
key, while `shots_on_goal_pct` (in neither) survives silently.
⚠ **Grep BOTH files before relying on it for a criterion-3 mutation.** Two earlier versions of this
line were wrong — "only the 16", then "strings.ts + the specs". `strings.ts` is the DEFINITION side,
checked in the opposite direction; the specs are not read by this test at all.
⚠ **For step 4 that covered set is nearly EMPTY** — the player surface is largely unbuilt, so this
guard will catch almost none of the 35 player renames. Plan a different mutation target.
⚠ **`git grep` SCOPES TO THE CWD** and CWD persists between calls. A count taken from inside
`dbt_project/` returned 38/46/21 against a true 177/185/50. Assert `cd <repo root>` in the same
command as any counting grep.

## ⛔ THE SAMPLE REFRESH — a FINAL one is owed after F

⛔ **THE OBVIOUS RECIPE IS A TRAP.** "Rerun the export and the committed payloads update" CANNOT
work: `fetch_fixture_payloads` emits UPCOMING fixtures only, and a kicked-off fixture has **0 rows**
in `mart_team_momentum` / `mart_team_season_record` (queried), so a past id can never be
re-exported. The export exits **0**, reports thousands written, and changes **nothing** you care
about. **ROLL THE WHOLE SET FORWARD** — full recipe in `site_v2/src/data/README.md`.
⭐ **THE RULE: exit code 0 and a big "written" count are not evidence the files you care about were
written.** Diff the specific artifacts, never the summary line.
⚠ `git clean -fX` is BLOCKED here. Use `git ls-files --others --ignored --exclude-standard <dir>`
as the delete set — `--others` makes it structurally unable to pick a tracked file. Dry-run first.
⚠ **The rendered fixture rows are drifting below the locked 16 as the batches land**: 16 → 15 (C)
→ 13 (D). E touches no fixture payload field so it holds at 13; F takes it to 12. Honest-absent,
not broken — closes with the final refresh.
⚠ **GitLab #98 opened**: the seven metric GROUP HEADINGS render in ENGLISH on DE/FI
(`MetricComparison.astro:40`, `TeamPerformance.astro:89`/`:110`). Pre-existing, §10 (the words are
the CPO's), NOT fixed. `TeamSquad.astro:99` already does it right — copy that pattern.

## ⭐ BATCHES D–F. Names are FIXED; do not re-derive (C is BUILT, awaiting merge)

⛔⛔ **THE AUTHORITY IS `.claude/task/escalations.log`** — the block "THE METRIC CATALOGUE NAMING
PROGRAMME" (rulings 2026-08-26, full tables appended 2026-08-27). **CITE IT, never a plan file: two
MRs were FAILed for citing one.** Remaining, verbatim from its "TEAM, 12 REMAINING" table:

| MR | renames |
|---|---|
| ~~**C** shooting shares~~ | ~~`shot_accuracy`→`shots_on_goal_pct` · `danger_zone_ratio`→`shots_inside_box_pct` · `shot_share`→`shots_share_pct`~~ **BUILT, awaiting merge** |
| ~~**D** passing~~ | ~~`pass_accuracy`→`passes_accuracy_pct` · `key_passes_per_match`→`passes_key_per_match`~~ **BUILT, awaiting merge** |
| ~~**E** deserved chain~~ | ~~`sot_difference_per_match`→`shots_on_goal_difference_per_match` · `sot_points_gap`→`deserved_points_gap`~~ **BUILT, awaiting merge** |
| **F** alone | `finishing_efficiency`→`finishing_efficiency_pct` |

⭐ **F IS LAST AND ALONE ON PURPOSE**: `finishing_efficiency` exists for BOTH entities, so the doc
block splits/merges and every occurrence must be classified by reading the model it sits on. Also
`site_v2/scripts/check-metric-labels.test.mjs` carries an EN exemption keyed on the literal string
`finishing_efficiency` — re-point it or the test compares v2's label against the corpus's
"% Conversion rate" and goes red.
⚠ **STEP 4** = the 35 player renames. **STEP 5** = the 9 English labels ("on target"→"on goal").
⚠ **STEP 5 HAS A TARGET THE 9-ROW LIST MAY MISS**, found in E and not fixed there: the EN hero
sentences at `site_v2/src/i18n/strings.ts:94-95` read "shots-on-target difference". Those are UI
SENTENCE strings, not catalogue `label_en` rows, so the nine-row list does not obviously cover them.
Wording is §10 — put it to the CPO when step 5 is scoped.

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
   `check_layer_contract.py`, `check_ui_i18n_metrics.py`, `pytest` (1009 on `b022909`), `dbt parse`,
   `sqlfluff lint` from the REPO ROOT, `cd site_v2 && npm test && node scripts/check-page-specs.mjs`.
6. Mutations watched going RED, then restored. Evidence read from the BUILT site.

## ⛔ TRAPS THAT COST TIME THIS SESSION — read before measuring anything

⛔ **A SUBSTRING TEST IS NOT A PRESENCE TEST.** My evidence script matched `Ø Corners` inside
`Ø Corners against` and reported 16 rendered names when 14 was true — it would have certified two
MISSING rows as present. This metric set is full of `X` / `X against` pairs. Subtract the longer
label's occurrences. ⚠ **IT HAS A SOURCE-TEXT FORM TOO**, hit on 2026-08-28: `grep -o points_capture`
returned 25 hits that were all inside `points_capture_pct`; the true count was 0. Tally WHOLE TOKENS
(`grep -oE 'stem[a-z_0-9]*' | sort | uniq -c`). ⭐ Better than either: count STRUCTURALLY — the
fixture comparison emits `<div class="mrow">` per row and `<div class="mgroup">` per heading, which
no substring can fake. The fixed script is in the session scratchpad; rewrite it if lost.
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
