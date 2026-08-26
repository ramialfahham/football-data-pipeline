# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-26**. **main `0ec8360`.** #82 MR1-MR4c and the catalogue MR (`!104`) MERGED.
**Nothing is in flight.** **GITLAB** (`glab`, MRs); runner `ci-runner-01`, ZERO GitLab minutes.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding
on `attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ NEXT: #90, the clean_sheets rename. CPO-ruled, fully scoped in the issue

⭐ **THE WORK IS IN THE TRACKER. `glab issue view <n>`.** Each issue below carries the measurement,
the file:line evidence, and what is verified versus what is not — enough to act on without this
file. **Do not re-scope or re-audit any of it, and do not restate it here.**
⭐ **READ `escalations.log`'s 08-20 to 08-26 entries FIRST.** The 08-26 entry holds four CPO
rulings verbatim. It is append-only and is the ONLY place a ruling counts.

**#90 — `clean_sheets` means a RATE in one mart and a COUNT in another; the CPO ruled the split.**
`clean_sheets` = the number of matches, `clean_sheets_share` = the percentage.
⚠ **VERIFY BEFORE WRITING ANYTHING**: `mart_team_profile` serves the RATE under a name the frontend
renders as a COUNT (`metricRows.ts:50`). Establish which mart the team page reads. **If it reads
the profile this is a LIVE DISPLAY BUG, not a naming inconsistency** — that changes what the MR is.
Not established; the issue says so.

**#91 — the catalogue does not drive the SQL, and the test that would catch it is BUILT and
PARKED.** No model `ref()`s the seed; 48 of 68 expressions differ from their formula and one
(`finishing_efficiency`) really diverges. ⭐ **THE FILE IS AT
`C:\Users\Rami\.claude\projects\D--Projects-football-data-pipeline\parked\`** with three reusable
scripts; its yml companion is in the stash labelled **"PARK: value-equivalence test"** — match by
MESSAGE, never by index. Needs 5 `model_column_alias` entries first. Ships after #90.

## ⛔ OPEN, ALL THE CPO'S — none blocks #90 or #91

- **#92** — `--defer --favor-state` makes ALL 28 singular tests read PROD on an MR, so a model
  change cannot go red until it has merged. The job's own comment claims the reverse.
- **#93** — `mart_team_momentum` is a SECOND copy of ~20 team formulas and has ALREADY DRIFTED on
  coverage gating. Same file carries a CPO attribution the log contradicts. ⚠ Put that to him as a
  contradicted attribution, never as evidence he ruled it.
- **#94** — the naming grammar. Not built; its own review returned FATAL. Two rulings this session
  cleared most of what blocked it: **a result is not a metric**, and **context = the WINDOW a
  formula runs over, never the formula**.
- **#89** — `finishing_efficiency` follows neither tier rule and is the only metric whose tier
  differs across entities.
- **#82** — the description programme itself.

## ⭐ THE METRIC LAYER — traps that outlive any one task

⛔ **A NAME CAN MEAN TWO QUANTITIES WITH EVERY SITE BLANK** (`goals_for`), and **a column that IS a
catalogue metric under another NAME is invisible to the generator** (`key_passes_prev_season_full`
= `passes_key`). Classify each site by what that model's SQL DOES with the column.
⛔⛔ **GIVING A MULTI-GRAIN NAME A CATALOGUE ROW SILENTLY RE-ARMS THE GENERATOR.** That is how a
per-match sentence reached 18 cumulative columns in `!104`, on four names the previous merge had
deliberately left blank for exactly that reason. **The catalogue says WHAT is measured; the model
says over what span** — `sync_metric_docs_blocks.py:84` enforces it by rejecting the bare word
"window" in any seed description.
⚠ **REGENERATE** `sync_metric_docs_blocks.py` after editing the seed AND after adding a derived
column — its second input is the model YAML, not just the seed.
⚠ Programme state, counts and the ~40 unwired columns live on **#82**, not here.

## ⛔⛔ THE LESSON FROM `!104` — 5 rounds, 7 FAILs, FOUR of them one root cause

**I narrate an outcome in prose and never write it into the file that is PARSED.** The contract is
the file already open, so writing the story there feels like recording it. Instances: the contract
cited `escalations.log` for rulings the log did not hold; a tier was declared for 4 of 5 rows in the
section arguing such values must be declared; `review.md` read "pending" while the contract narrated
a finished round; the `rounds_cap_override` quoted the CPO from prose alone.
⭐ **THE RULE: a ruling is appended to `escalations.log` in the SAME TURN it is given; a verdict is
written into `review.md` BEFORE it is written about anywhere else.** Backfilling is allowed and was
judged acceptable — the entry must disclose its own after-the-fact timing on its face — but it cost
four rounds. And before claiming a file "records" something, OPEN IT AND GREP.
⚠ **NEVER SAY "YOU RULED" WITHOUT A QUOTE FROM `escalations.log`.** A seed description, a code
comment or my own memory file is REPO PRACTICE. Said as his ruling, it drew a flat "No, I didn't".

## ⭐ OPERATIONAL

⛔ **A TOO-LONG DESCRIPTION BREAKS PROD.** `persist_docs` on for 97 models + 9 seeds. **1,024**
chars/column, **16,384**/relation; one over = HTTP 400 and the model FAILS.
⚠ **`git stash push -- <paths>` SNAPSHOTS THE WHOLE INDEX**, so popping it clobbers files edited
meanwhile. Extract with `git checkout stash@{0} -- <paths>`, then drop. Hit twice in one session.
⚠ **`--review-patch` writes to STDOUT** — without a redirect the patch is silently the PREVIOUS
task's. `escalations.log` is in `hash_exclude_paths` but NOT `review_exclude_paths`: reviewers see
it, the hash ignores it.
⛔ **NEVER WRITE A REVIEWER'S VERDICT YOURSELF.** Send it and WAIT.
⚠ **A too-narrow grep reported as a clean sweep**, and a keyword scan is blind to a claim using no
keyword. **A bulk-edit script reporting success while matching nothing** — assert it found work.
⛔⛔ **INVERT THE NUMBER SWEEP**: pull EVERY integer out of the artifacts and ask of each "is this
still true", rather than sweeping for the ones you remember changing. A figure was stale across
three revisions in `!104` and only a reviewer's hand-count found it. **#71**.
⚠ **OPERATIONAL NOTES ARE IN `CLAUDE.md`** (dbt CLI, SQLFluff, commit mechanics, contract stash
dance, CWD/fnmatch/heredoc traps) — not capped, do not copy back.
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
