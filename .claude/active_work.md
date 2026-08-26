# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-26**. **main `c138600`.** **#90 MERGED** (`!107`) and its export-sample
follow-up with it (`!109`). **Nothing is in flight.**
**GITLAB** (`glab`, MRs); runner `ci-runner-01`, ZERO GitLab minutes.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding
on `attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ NEXT: #91

⭐ **THE WORK IS IN THE TRACKER. `glab issue view <n>`.** Do not re-scope or re-audit it here.
⭐ **READ `escalations.log`'s 08-20 to 08-26 entries FIRST.** The last two entries are #90's, and
both record a CPO **SELECTION between builder-authored options** — not a verbatim ruling. Never
quote either as "you ruled".

**#91 — the catalogue does not drive the SQL**, and the test that would catch it is BUILT and
PARKED at `C:\Users\Rami\.claude\projects\D--Projects-football-data-pipeline\parked\` with three
reusable scripts; its yml companion is in the stash labelled **"PARK: value-equivalence test"** —
match by MESSAGE, never by index. Needs 5 `model_column_alias` entries first.

## ⛔ #95, FILED THIS SESSION — read it before touching any slug or team name

**`team_slug` is documented as PERMANENT and is RE-DERIVED FROM `team_name` ON EVERY BUILD**
(`base_apif__teams_global.sql:69-72,236`), so correcting a name MOVES A PUBLISHED URL. It fired for
real: the sample refresh moved team 33 from `manchester-united` to `manchester-united-fc`, because
`team_name_overrides.csv:75` corrects that club. `not_null` + `unique` (`core.yml:247`) both judge
ONE build, so nothing can go red when a URL moves.
⚠ **111 corrections are already in the seed and the team-names programme is PAUSED PART-WAY**, so
every remaining correction moves another URL. Harmless only because nothing links to a team page
today — which is exactly the protection that ends when something does.
**The fork is in the issue and is the CPO's; do not decide it in passing.**

## ⭐ WHAT #90 SETTLED, so nobody re-opens it

**`clean_sheets` is the COUNT of shut-out matches; `clean_sheets_share` is the proportion.** Both
are catalogue rows. The count is served by the fixture windows (`x/y`), the share by the team
page's benchmark and yoy family (`% Clean sheets`).
⛔ **THE ISSUE'S PREMISE WAS FALSE and the merged contract says so.** #90 claimed
`mart_team_profile.clean_sheets` was a RATE and possibly a live display bug. It is the COUNT —
`:86` reads `ts.clean_sheets` and `ts` is the `mart_team_season` CTE (join at `:209-210`). **No
wrong number was ever on screen.** Do not "restore" that map.
(The two durable traps #90 produced — a display slot binding two metrics, and the `% ` label
convention — live once, under THE METRIC LAYER below.)

## ⛔ OPEN, ALL THE CPO'S — none blocks the sample refresh or #91

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
⛔ **THE ACCEPTANCE GATE FIRES ON ANY `site_v2/src/` DIFF** — `site_v2/src/data/**` INCLUDED: the
contract needs an `acceptance_criteria:` key and `acceptance_evidence.md` a `criteria_demonstrated:`
block with at least as many bullets, each ≥15 chars, all distinct, indented under the key.
⚠ **BOTH KEYS MUST SIT AT COLUMN 0, NOT AS A `##` MARKDOWN HEADING.** `_block()` anchors
`^criteria_demonstrated[^\S\n]*:` at the line start, so a heading parses as ZERO criteria and the
commit is denied with a message that reads like the evidence is missing. Cost two denials in one
session — the second AFTER writing this trap down.
⚠ **Write acceptance criteria the DATA can satisfy.** A criterion invented from an assumption
about what a page will render is not a gate, it is a guess — and mine then argued against shipping
correct work. If a criterion turns out unmeetable, fix the criterion; do not stop the task.
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
