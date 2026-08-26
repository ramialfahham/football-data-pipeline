# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-26**. Branch **`fix/90-clean-sheets-count-vs-share`**, off main `5894aff`.
**#90 is BUILT and VERIFIED; the blinded review round has not run.** **GITLAB** (`glab`, MRs);
runner `ci-runner-01`, ZERO GitLab minutes.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding
on `attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ WHERE #90 STANDS — everything but the review is done

⭐ **THE WORK IS IN THE TRACKER. `glab issue view <n>`.** Do not re-scope or re-audit it here.
⭐ **READ `escalations.log`'s 08-20 to 08-26 entries FIRST.** The last two entries are this task's.

**DONE, all gates green offline:** the seed split (85 → 86 rows), the docs blocks regenerated
(181 → 183), seven rate columns renamed, three `accepted_values` lists moved, the frontend's
per-surface binding, three locale labels, two wireframes. `contract.md`,
`acceptance_evidence.md` and `rendered_page_evidence.md` are written and current.
`dbt parse` clean · `sqlfluff` clean · `npm test` 76/0 · `pytest` 1007 pass · `npm run build`
60 pages · three MUTATIONS watched going RED.

**NOT DONE — the next action, in order:**
  1. Spawn the FOUR blinded reviewers the routing requires: **scope-auditor**,
     **analytics-engineer-reviewer**, **football-analytics-expert-reviewer**, **bi-analyst-reviewer**
     (computed from `review_routing.json`, not guessed). ⛔ NEVER WRITE A VERDICT YOURSELF.
  2. Write their verdicts into `review.md` under `## <exact-routing-key>` headers, BEFORE writing
     about them anywhere else, with `diff_sha256` from
     `python .claude/hooks/git_discipline.py --staged-hash` and `rounds:`.
  3. `git add` then a plain `git commit -F <scratchpad file>` as the SOLE command in its own call.
     A post-commit hook auto-pushes and opens the MR.

## ⛔ THE ONE THING A REVIEWER MUST NOT "FIX"

**#90's own premise is FALSE and the contract says so.** The issue claims
`mart_team_profile.clean_sheets` is a RATE and might be a live display bug. It is the COUNT —
`mart_team_profile.sql:86` reads `ts.clean_sheets` and `ts` is the `mart_team_season` CTE (join at
`:209-210`). The rate reaches the product through
`int_team_competition_benchmark_metrics_long.sql:34` → `mart_team_competition_benchmarks.metric_key`,
which the issue never mentions. **No wrong number was ever on screen.** Do not "restore" the
issue's map; it was checked against the SQL and the committed payload.

## ⚠ THE MR SHIPS ONE BUILD STALE, ON PURPOSE

`site_v2/src/data/` is a gitignore-pinned export SAMPLE. The renamed columns do not exist in
BigQuery until `data:build:main` runs after merge, so the sample still keys the benchmark
`clean_sheets` and the team page's clean-sheet row is **omitted from the "vs the league" panel**
(15 rows vs the season panel's 16). That is the tab's honest-absent path, it is measured in
`rendered_page_evidence.md`, and it is NOT a defect to chase. **Refreshing the sample as a SET is a
follow-up commit after the first main build** — never a hand edit of exported JSON.

## ⛔ OPEN, ALL THE CPO'S — none blocks the review

- **#91** — the catalogue does not drive the SQL; the value-equivalence test is BUILT and PARKED at
  `C:\Users\Rami\.claude\projects\D--Projects-football-data-pipeline\parked\`, its yml companion in
  the stash labelled **"PARK: value-equivalence test"** (match by MESSAGE, never by index). Needs 5
  `model_column_alias` entries. Ships after #90.
- **#92** — `--defer --favor-state` makes ALL 28 singular tests read PROD on an MR.
- **#93** — `mart_team_momentum` is a SECOND copy of ~20 team formulas and has ALREADY DRIFTED.
  Same file carries a CPO attribution the log contradicts. ⚠ Put that to him as a contradicted
  attribution, never as evidence he ruled it.
- **#94** — the naming grammar. Not built; its own review returned FATAL.
- **#89** — `finishing_efficiency` follows neither tier rule.
- **#82** — the description programme; ~40 columns still blank, including `clean_sheets_sum_season`.

## ⭐ THE METRIC LAYER — traps that outlive any one task

⛔ **A NAME CAN MEAN TWO QUANTITIES WITH EVERY SITE BLANK** (`goals_for`), and **a column that IS a
catalogue metric under another NAME is invisible to the generator** (`key_passes_prev_season_full`
= `passes_key`). Classify each site by what that model's SQL DOES with the column.
⛔⛔ **GIVING A MULTI-GRAIN NAME A CATALOGUE ROW SILENTLY RE-ARMS THE GENERATOR.** #90 did this
deliberately: the count row's EMPTY `denominator_expr` lifted `TOTALLING_AFFIXES`' refusal and the
generator now emits `clean_sheets_sum_season__team`. Intended, verified true at the whole-season
grain, and left UNWIRED. **The catalogue says WHAT is measured; the model says over what span** —
`sync_metric_docs_blocks.py:84` rejects the bare word "window" in any seed description.
⚠ **REGENERATE** `sync_metric_docs_blocks.py` after editing the seed AND after adding a derived
column — its second input is the model YAML, not just the seed.
⭐ **A DISPLAY SLOT CAN BIND TWO METRICS.** `metricRows.ts` row 3 now carries a `team` override and
`teamBinding()`; `field`/`labelKey`/`format` are the FIXTURE binding. Read the team side through
the helper, never through `field`.
⭐ **PERCENT LABELS CARRY A `% ` PREFIX** — 7 of 7 in the catalogue and in all three locale dicts.
Check a convention BEFORE recommending a name; #90 cost a second CPO question by not doing so.

## ⛔⛔ THE LESSON FROM `!104` — 5 rounds, 7 FAILs, FOUR of them one root cause

**I narrate an outcome in prose and never write it into the file that is PARSED.**
⭐ **THE RULE: a ruling is appended to `escalations.log` in the SAME TURN it is given; a verdict is
written into `review.md` BEFORE it is written about anywhere else.** Backfilling is allowed if the
entry discloses its own timing on its face — but it cost four rounds.
⚠ **NEVER SAY "YOU RULED" WITHOUT A QUOTE FROM `escalations.log`.** A seed description, a code
comment or a memory file is REPO PRACTICE. ⚠ And a CHOICE BETWEEN OPTIONS I AUTHORED is not a
verbatim ruling either — both of #90's naming decisions are recorded that way.

## ⭐ OPERATIONAL

⛔ **A TOO-LONG DESCRIPTION BREAKS PROD.** `persist_docs` on for 97 models + 9 seeds. **1,024**
chars/column, **16,384**/relation; one over = HTTP 400 and the model FAILS.
⛔ **THE CONTRACT MAY ONLY BE (RE)WRITTEN ON A CLEAN TREE**, and #90 hit this twice. Stash with
EXPLICIT PATHS and a `TEMP-` label, amend, then **`git checkout stash@{0} -- <paths>` and DROP** —
never `pop`, which restores the whole index. ⚠ Do not leave a background build running across a
stash: it reads the reverted tree and its output is worthless.
⚠ **`--review-patch` writes to STDOUT** — without a redirect the patch is silently the PREVIOUS
task's. `escalations.log` is in `hash_exclude_paths` but NOT `review_exclude_paths`.
⛔ **THE ACCEPTANCE GATE FIRES ON ANY `site_v2/src/` DIFF**: the contract needs an
`acceptance_criteria:` key and `acceptance_evidence.md` a `criteria_demonstrated:` block with at
least as many bullets, each ≥15 chars, all distinct, indented under the key.
⛔ **NEVER WRITE A REVIEWER'S VERDICT YOURSELF.** Send it and WAIT.
⛔⛔ **INVERT THE NUMBER SWEEP**: pull EVERY integer out of the artifacts and ask of each "is this
still true". **#71**.
⚠ **OPERATIONAL NOTES ARE IN `CLAUDE.md`** (dbt CLI, SQLFluff, commit mechanics, CWD/fnmatch/heredoc
traps) — not capped, do not copy back. ⚠ Heredocs are BLOCKED, including for scratchpad scripts.
**FIRST ACTION: `git stash list`.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX. One must never be rebuilt:
**`feat/player-overview-tab`**.

## ⭐ OTHER STANDING STATE

⛔ **TEAM NAMES — paused.** `team_name_overrides` (`base_apif__teams_global.sql`) fires on
completeness OR collision. **97 of ~130 Pool 1 corrected**, each citing an English Wikipedia URL.
⚠ **Bayern München EXCLUDED ON PURPOSE**. NOT done: ~15 Pool 1, teams outside it, `dim_player`
short-names. **#81** = duplicates for ONE club.
✅ **SETTLED, do not re-propose.** BROWSE DROPPED (`!80`) — home renders next matches ALONE. TOP
TEAMS = one per league, not pooled.
⛔ **#83** — competition classification has no core dim; 12 models join the seed direct.

## ⭐⭐ THE METHOD, standing rule for every page (CPO's words, do not reword)

*"the exercise is: does the mock consider the underlying mart (or mart gap)."* Per element:
(1) name the exact MART COLUMN — a seed/registry/catalogue is NOT a source, and reading one from a
page is the same violation as computing in the frontend; (2) no mart column = a GAP, registered in
`99_gaps_register.md` BEFORE building; (3) check the mock's OWN numbers against the spec.
⚠ **The handover rides in the SAME commit as the code it describes.**
⭐ **THE REPO IS NOT THE SYSTEM**: for warehouse/cloud/CI facts check the system that owns them
(`bq ls`, `glab api`, `gcloud` — free metadata). Bit twice.
**Audits: GitLab #30, DO NOT run another** (a TARGETED blind assessment IS allowed).
