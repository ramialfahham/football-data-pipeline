# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-27**. **main `9b4b225`** (after `!115`, the #92 CI fix). The METRIC CATALOGUE
NAMING PROGRAMME is running: `!111`, `!112`, `!113` and `!115` merged, **47 renames still to go**,
and **STEP 3 IS IN FLIGHT** — **MR A (`!114`) is GREEN and awaiting merge**: rebased onto `9b4b225`,
all six jobs pass, 234/234 build and 30/30 singular tests, `ci_mr114_*` datasets.
⭐ **`!114` proves `!115` worked**: `assert_mart_team_season_insights_metric_consistency` now passes
in BOTH runs, where before it errored in the trailing one with "Unrecognized name:
points_capture_pct". **Nothing else is in flight.**
⚠ **MR A ships BOTH renames** — splitting `points_capture` out was considered when it was blocked,
and became unnecessary once `!115` landed. Do not split it.
**GITLAB** (`glab`, MRs); runner `ci-runner-01`, ZERO GitLab minutes.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding
on `attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ NEXT: the naming programme, step 3

⛔⛔ **THE COMPLETE REMAINING RENAME LIST IS IN `.claude/task/escalations.log`**, at the end of the
2026-08-27 block inside "THE METRIC CATALOGUE NAMING PROGRAMME". **READ IT FIRST AND CITE IT** — it
holds the CPO's six rulings verbatim, the six-item list his blanket approval answered, all 47
remaining names, the 9 label changes, and the two live transients. **Do not re-derive any of it and
do not cite a plan file: two MRs were FAILed for exactly that.**

**STEP 3 — the 12 TEAM column renames, SPLIT INTO SIX MRs + a closing refresh.** Every one is a
COMPUTED COLUMN in the season models, so each runs through model SQL, the ymls, the marts and the
site. Re-measured on `1804a64`: **894 occurrences** in live surfaces (not the ~600 an earlier count
gave — that was taken over a narrower path set), plus 1,532 in the generated sample. The split keys
on the seed's own `metric_group` column, and is recorded in `escalations.log` under
"2026-08-27 STEP 3 STARTS":
**A** goals+outcomes ← IN REVIEW · **B** set_pieces+goalkeeping · **C** shooting shares ·
**D** passing · **E** the deserved chain · **F** `finishing_efficiency` alone · **G** sample refresh.
⭐ **Branch each MR from the main that already carries the previous one's record.**
⚠ The acceptance gate FIRES on step 3 (it touches `site_v2/src/`), so the contract needs
`acceptance_criteria:` and the evidence a `criteria_demonstrated:` block. **Both keys at column 0,
NOT as `##` headings** — that cost two commit denials in one session.
⛔ **THE METRIC ROWS RENDER ON NO BUILT PAGE TODAY**, and this will bite every one of B–F the same
way. Team 33's featured season is PL 2026 with ONE game played, below the `>= 3 finished games`
benchmark floor, so `TeamPerformance.astro`'s `hasBench` guard renders the absent state for the
whole tab. **Do not write an acceptance criterion that reads a metric row off the built page.**
What IS demonstrable: the 16 metric NAMES render on the fixture pages, in all three locales.
⛔ **NO OFFLINE GATE PINS THE THREE 22-NAME `accepted_values` LISTS** (two in
`int_competition_benchmarks.yml`, one in `shared.yml`) to the columns they enumerate — proved by a
mutation that survived the whole offline suite. Only `data:build:mr` catches a forgotten entry.
Filed as its own issue; do not fold a new guard into a rename MR.

**STEP 4** — the 35 player renames. **STEP 5** — the 9 English labels.

**THEN #91**, the parked value-equivalence checker, which waits until the renaming finishes because
shipping it first would bind it to names that are about to move. Its file is at
`C:\Users\Rami\.claude\projects\D--Projects-football-data-pipeline\parked\`; its yml companion is
in the stash labelled **"PARK: value-equivalence test"** — match by MESSAGE, never by index.
⚠ It needs SIX `model_column_alias` entries, not the five the issue says: #90 added a sixth
(`clean_sheets|team`). Re-derive against the seed before trusting either number.

## ⛔⛔ THE LESSON OF THIS SESSION — one root cause, FOUR variants, three MRs FAILed on it

**THE RECORD AND THE WORK MUST TRAVEL TOGETHER.** Every failure was in the paperwork; not one was
in a rename. The code was byte-identical across every re-run.
  1. CPO rulings given in conversation and never written to `escalations.log` at all.
  2. Written down, but the next branch was cut from main BEFORE that MR merged, so from its own
     diff the citation pointed at nothing. A reviewer reasonably called it "apparently fabricated".
  3. Written down, but a per-file tally was copied from a pre-edit count and never re-derived.
  4. Written down, but only the APPROVAL, not the list it was given against. A blanket "yes" is
     unverifiable unless what it answered sits beside it.
⭐ **SO: branch each step from the main that already carries the previous step's record**, append
rulings the same turn they are given, and re-measure every number after the edit rather than before.

## ⭐ OPERATIONAL — the traps that cost time this session

⚠ **`git checkout <branch>:<path>` MANGLES ON THIS SHELL.** The colon becomes a Windows path and
the command fails SILENTLY-looking (`unknown revision`). Export `MSYS_NO_PATHCONV=1` first. A
mis-read of that made me believe a committed record did not exist.
⛔ **A STASH SNAPSHOTS THE WHOLE INDEX AGAINST ITS OWN BASE.** Restoring `dbt_project` wholesale
from a stash taken against an OLDER main silently reverted the previous MR's edits in every file
both changes touched. The contract gate caught it on one file. **If the work is scripted, discard
and RE-RUN THE SCRIPT on the new base instead of restoring a stash.**
⛔ **`git reset --hard` is blocked** by the tooling. Use `git checkout HEAD -- <path>`, which is
also what the contract gate suggests.
⛔ **The contract may only be (re)written on a CLEAN TREE.** With scripted work, the cheapest route
is `git checkout HEAD -- dbt_project`, edit the contract, then re-run the script. No stash at all.
⚠ **A sed pattern containing `doc(` is read by the gate as a PATH** and denied. Write
`s/'name')/'new')/` instead.
⚠ **`--review-patch` writes to STDOUT** — without a redirect the patch is silently the PREVIOUS
task's.
⛔ **NEVER WRITE A REVIEWER'S VERDICT YOURSELF.** Send it and WAIT. ⚠ And when review.md is
rewritten for a new round, RE-ADD the standing verdicts: the gate needs every required reviewer
present, and rewriting the file drops them.
⛔⛔ **INVERT THE NUMBER SWEEP**: pull EVERY integer out of the artifacts and ask of each "is this
still true". **#71**.
⚠ **OPERATIONAL NOTES ARE IN `CLAUDE.md`** (dbt CLI, SQLFluff, commit mechanics, CWD/fnmatch/heredoc
traps) — not capped, do not copy back. ⚠ Heredocs are BLOCKED, including for scratchpad scripts.
**FIRST ACTION: `git stash list`.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX. One must never be rebuilt:
**`feat/player-overview-tab`**.

## ⭐ THE METRIC LAYER — traps that outlive any one task

⭐ **THE NAMING PATTERN, for any metric added later:**
`noun [_qualifier] [_against] [_player] [_form]`, where `_form` is `_per_match` (team), `_per90`
(player) or `_pct` (a proportion).
⛔ **RENAMING A METRIC CAN SPLIT ITS DESCRIPTION BLOCK.** If the new name exists for BOTH entities
with different formulas, the generator replaces the bare block with `__team` / `__player` and
DANGLES every existing reference to the old bare name. This surprised `!111` mid-flight and was
predicted up front in `!112`. **Count the references for BOTH names before writing the contract.**
⚠ **REGENERATE** `sync_metric_docs_blocks.py` after editing the seed AND after adding a derived
column — its second input is the model YAML, not just the seed.
⛔ **A METRIC AND ITS COLUMN MAY LEGITIMATELY DIFFER.** `goals`, `corners` and `saves` are metrics
whose model columns keep provider names (`goals_for`, `corner_kicks`, `goalkeeper_saves`). Three
reviewers accepted that twice. Whether the columns ever follow is UNASKED and UNANSWERED.
⛔ **#95, FILED THIS SESSION — read before touching any slug or team name.** `team_slug` is
documented as PERMANENT and is RE-DERIVED FROM `team_name` ON EVERY BUILD, so correcting a name
MOVES A PUBLISHED URL. It fired for real: team 33 moved to `manchester-united-fc`. 111 corrections
are already in the seed and the team-names programme is PAUSED PART-WAY.

## ⛔ OPEN, ALL THE CPO'S — none blocks the naming programme

- **#92** — FIXED 2026-08-27 in `!115`, **in two halves, and half two is not optional**.
  (1) `--favor-state` is gone from `data:build:mr`'s **`dbt test`** line, so the 30 singular tests
  read the BRANCH; it STAYS on the `dbt build` line — ⛔ **never "match the two lines up"**.
  (2) ⛔ **THE CI DATASETS ARE PER MERGE REQUEST**: `DBT_CI_TARGET=ci_mr${CI_MERGE_REQUEST_IID}`
  names both the profile output AND its `dataset:`. **There is no shared `ci` target.** Half one
  ALONE broke things — `!115`, which changes no models, went red on three tests reading `!114`'s
  leftovers. `generate_schema_name` is UNTOUCHED (it already prefixes on `target.name`), so local
  `dev` is unaffected. ⚠ BOTH profile lines are load-bearing: the target NAME isolates the layer
  datasets, `dataset:` isolates base models + every seed (no `+schema` → bare `target.schema`).
  ⛔ **NOTHING EXPIRES OR DELETES THESE DATASETS, BY CPO INSTRUCTION** — "you do nothing where you
  come any close to introducing the risk of deleting the warehouse". They accumulate; measured, a
  full set is 6.0 GB ≈ 12¢/month. Do not add a TTL, a drop or a cleanup step.
  ⭐ **Any column rename a singular test names is unmergeable without this** — prod gains the column
  only after the merge, so the gate can never go green first. Step 4's 35 player renames would have
  hit it repeatedly.
- **#93** — `mart_team_momentum` is a SECOND copy of ~20 team formulas and has ALREADY DRIFTED.
  ⚠ Its file carries a CPO attribution the log contradicts; put that to him as a contradicted
  attribution, never as evidence he ruled it.
- **#94** — the naming grammar. Largely SUPERSEDED by this programme; re-read before reopening.
- **#89** — `finishing_efficiency` follows neither tier rule.
- **#82** — the description programme; ~40 columns still blank.
- **#83** — competition classification has no core dim; 12 models join the seed direct.

## ⭐ OTHER STANDING STATE

⛔ **TEAM NAMES — paused.** `team_name_overrides` fires on completeness OR collision. **97 of ~130
Pool 1 corrected**, each citing an English Wikipedia URL. ⚠ **Bayern München EXCLUDED ON PURPOSE**.
**#81** = duplicates for ONE club. ⚠ See #95 above before resuming: each correction moves a URL.
✅ **SETTLED, do not re-propose.** BROWSE DROPPED (`!80`) — home renders next matches ALONE. TOP
TEAMS = one per league, not pooled.
⚠ **The committed export sample** (`site_v2/src/data/`, gitignore-pinned SET) is refreshed by
rerunning `scripts/export_site_data.py`, never hand-edited, and only AFTER `data:build:main` has
materialised the new columns. Its README's "18 files" count is stale; 22 are tracked.

## ⭐⭐ THE METHOD, standing rule for every page (CPO's words, do not reword)

*"the exercise is: does the mock consider the underlying mart (or mart gap)."* Per element:
(1) name the exact MART COLUMN — a seed/registry/catalogue is NOT a source; (2) no mart column = a
GAP, registered in `99_gaps_register.md` BEFORE building; (3) check the mock's OWN numbers.
⚠ **The handover rides in the SAME commit as the code it describes.**
⭐ **THE REPO IS NOT THE SYSTEM**: for warehouse/cloud/CI facts check the system that owns them
(`bq ls`, `glab api`, `gcloud` — free metadata).
**Audits: GitLab #30, DO NOT run another** (a TARGETED blind assessment IS allowed).
