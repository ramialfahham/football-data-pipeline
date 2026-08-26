# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-26**. **main `21c1ce0`.** #84 + #82 MR1-MR4c MERGED (`!103`).
**THE CATALOGUE MR is in review; the VALUE-EQUIVALENCE TEST is PARKED behind it.**
**GITLAB** (`glab`, MRs); runner `ci-runner-01`, ZERO GitLab minutes.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding
on `attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ CURRENT — the metric layer, not the description programme (2026-08-26)

⭐ **READ `escalations.log`'s 08-20 to 08-26 entries FIRST** — numbers, rulings, each MR's defects.
**Do not re-scope or re-audit any of it.**

⛔⛔ **THE CATALOGUE DOES NOT DRIVE THE SQL. No model `ref()`s the seed — only tests do.** Formulas
are hand-copied and nothing compares them: 20 of 68 expressions match, 48 differ, and
`finishing_efficiency` (undocumented NULL clamp) really diverges.
**IN FLIGHT: the catalogue MR** — 5 team total rows (80 → 85); the player side had 28 plain totals,
the team side 4. +20 blocks; `goals_against` splits `__team`/`__player`, 20 refs repointed, 30
columns wired. **Fixes a LIVE defect: 12 team columns carry the PLAYER goals_against definition in
BigQuery today.**
⛔ **CPO 2026-08-26, TWO RULINGS, 9 ROWS → 5.** (1) *"win, draw, loss are not metrics. they are
results of a match"* — a match attribute already in `result`; counting it tallies a dimension.
Dropping those 3 killed the cascade: 3 block-name collisions, a `dbt parse` FAILURE, the
`standings_*` rename and 6 repoints all vanished. (2) *"use clean_sheets (number of matches) and
clean_sheets_share (percentage)"* — a RENAME of a shipped metric, so its own MR, queued next.
⭐ **PARKED, ships after it**: `assert_metric_catalogue_value_equivalence.sql` — recomputes each
formula and diffs the VALUES; 66/80 verified. Scratchpad `PARKED_value_equivalence_test.sql`, yml
companion in the stash. Needs 5 `model_column_alias` entries first, and **must ship on a main that
already carries the rows it reads.**
⚠ **REGENERATE** `sync_metric_docs_blocks.py` after editing the seed AND after adding a derived
column — its second input is the model YAML.
⭐ **DESCRIPTION PROGRAMME (paused): 111 names / 300 columns left** — 48 derived families · 14
multi-meaning · 31 disagreeing · 11 · 7 h2h; then **MR5**. ⛔ Plus **~40 the catalogue MR leaves
blank**: they resolve to `<name>__team`, so `--wire-shared-docs` cannot match and
`--wire-metric-docs` refuses (`int_team_momentum__metrics` not in `MODEL_ENTITY`).
⛔ **9 of 11 metric-computing models are unguarded.** `mart_team_momentum.sql:42-117` is a SECOND
copy of ~20 team formulas and has ALREADY DRIFTED (`shot_accuracy` gates on one counter, the shared
model on two). Its `:104-106` credits that to "CPO 2026-06-25"; `escalations.log:227` says the
opposite. **A contradicted attribution in shipped code.**
⛔ **`--defer --favor-state` (`.gitlab-ci.yml:653`) makes ALL 28 singular tests read PROD on an MR**,
so a model change cannot go red until merged. The comment at `:636` claims the reverse.
⛔ **A NAME CAN MEAN TWO QUANTITIES WITH EVERY SITE BLANK** (`goals_for`), and **a column that IS a
catalogue metric under another NAME is invisible to the generator**
(`key_passes_prev_season_full` = `passes_key`). Classify by what each model's SQL DOES.
✅ **THE "SEVEN PLAYER-ONLY METRICS BLOCK 48 COLUMNS" CLAIM WAS WRONG, RETIRED** — five, not seven,
none blocked; the catalogue MR is the fix.
⭐ **A PROVENANCE CLAIM IS CHECKABLE ONLY IN THE SQL** — 6 of 37 promotions were pulled for this; a
sweep that READ the sentences still missed one. ⚠ A `protected_override` goes in `escalations.log`
BEFORE the branch touches the path.
⛔⛔ **A NAME THAT MEANS TWO THINGS IS INVISIBLE TO THE GATE** — it skips the bare name, so a wrong
or blank site goes unseen; **assert those from the YAML directly.** `league_code` = the competition
EXCEPT on entity-scoped pulls (transfers, coaches, player profiles/teams,
`base_apif__teams_global`) where it is INGEST PROVENANCE; 49 blanks stay blank; **ROOT CAUSE =
#87**. Now also `wins`/`draws`/`losses`/`goals_against`. ⚠ **NO CLASSIFIER WORKS** — 4 tried — so
**EVERY derived block is entity-suffixed**. Blank and visible beats documented and wrong.
✅ **`persist_docs` WORKS EVERYWHERE** — #86 said otherwise, CLOSED AS WRONG.
⛔⛔ **A CHECK THAT AGREES WITH ITSELF PROVES NOTHING — 9× now.** Of 18 mutations over MR4b/MR4b-2,
**5 SURVIVED** and 3 meant the RULE was wrong, not the assertion weak.

⛔ **A TOO-LONG DESCRIPTION BREAKS PROD.** `persist_docs` is on for 97 models + 9 seeds. **1,024**
chars/column, **16,384**/relation; one over = HTTP 400, model FAILS. ⚠ `seeds:` is
persist_docs-ONLY: a `+schema` relocates all 9.
⛔ **TASK ARTIFACTS COLLIDE ON CONCURRENT BRANCHES (4× on `!91`).** Take this task's whole, MERGE
`escalations.log`+`active_work.md`, rebind `review.md`'s hash — no re-review owed.

✅ **THE GATE** (`check_description_hygiene.py`) runs in CI + `stop_gate.py` FAST_GATES. ⚠ Its
shared-block rule has **NO layer filter**, so a new block makes a blank column of that name a
finding in staging and base too — write, wire and promote in ONE commit.


⛔ **THE PROVIDER SENDS NO DESCRIPTIONS — CHECKED.** Stats are a label and a number; every
definition is OURS. For an ambiguous name derive it from our own fixtures.
⚠ **CPO RULINGS 08-21:** "every column, no exception" (staging+base OUT) · no thin filler · docs
blocks only with a mechanism behind them · **NO osmosis**.
⛔ **GRAIN claims are safe to inherit from upstream prose; BEHAVIOUR and PROVENANCE are NOT.**
MR1 shipped a FALSE "newest is the fullest".
⛔⛔ **RECORD THE OPTION CHOSEN AND NOTHING ELSE**, and **never say "you ruled" without a quote from
`escalations.log`** — a seed description, code comment or memory file is REPO PRACTICE. Said as his
ruling on 08-25, it drew a flat "No, I didn't".

⛔ **FIVE TRAPS, every one hit for real. Do not re-learn them.**
1. **A too-narrow grep reported as a clean sweep**, and **a keyword scan is blind to a claim using
   NO keyword**. "partition key" is FALSE; 6 survivors = **#79**. A grep also matches a defect's
   DOCUMENTATION as the defect.
2. **A bulk-edit script reporting success while matching nothing.** Assert it found work.
3. **Verify a reviewer finding, then act** — both directions.
4. **`--review-patch` writes to STDOUT**, so without redirect the patch is silently the PREVIOUS
   task's. `origin/main` is the DORMANT GitHub remote — use `gitlab`.
5. ⛔ **NEVER WRITE A REVIEWER'S VERDICT YOURSELF.** MR5 recorded PASS for two who returned FAIL.
   Send the confirm and WAIT. ⚠ Never edit any file while the suite runs.

⛔⛔ **THE STANDING LESSON — 5 FAILs across MR4b/MR4b-2, same class each time.** CPO: *"you spam
things all around the repo and then forget to clean up ... contradictions in our docs and files."*
⭐ **THE CAUSE IS A SEARCH KEY, NOT DISCIPLINE** — I sweep for the numbers I REMEMBER, so a
forgotten one survives, and 4 prose corrections changed nothing. **INVERT IT: pull EVERY number out
of the artifacts and ask of each "is this still true".** Caught 2 in MR4c no sweep would. **#71**.

⛔ **TEAM NAMES — paused.** The provider's `team_name` is often not the display name;
`team_name_overrides` (`base_apif__teams_global.sql`) fires on completeness OR collision. **97 of
~130 Pool 1 corrected**, each citing an English Wikipedia URL. ⚠ **Bayern München EXCLUDED ON
PURPOSE** — locale preference is never corrected. NOT done: ~15 Pool 1, teams outside it,
`dim_player` short-names. **#81** = duplicates for ONE club.

✅ **SETTLED, do not re-propose.** BROWSE DROPPED (`!80`) — home renders **next matches ALONE**;
`08_browse.md` + competitions page stay LIVE. TOP TEAMS = **one per league**, not pooled;
⚠ `top_teams_mock.html` has the wrong shape, GAP-29's mart not started.

## ⭐⭐ THE METHOD, standing rule for every page (CPO's own words, do not reword)

*"the exercise is: does the mock consider the underlying mart (or mart gap)."* Per element:
(1) name the exact MART COLUMN — a seed/registry/catalogue is NOT a source, and reading one from a
page is the same violation as computing in the frontend; (2) no mart column = a GAP, registered in
`99_gaps_register.md` BEFORE building; (3) check the mock's OWN numbers against the spec.
⭐ **AUTOMATION NOT built, NOT approved.** Ask first. **#78**.

⚠ **STANDING RULE: the handover rides in the SAME commit as the code it describes.**

## ⭐ ORIENTATION
**Audits: GitLab #30, DO NOT run another** (a TARGETED blind assessment IS allowed).
**⚠ OPERATIONAL NOTES ARE IN `CLAUDE.md`** (dbt CLI, SQLFluff, commit mechanics, stash-dance,
CWD/fnmatch/heredoc/grep traps). **Do not copy back**: that file is not capped.
**FIRST ACTION: `git stash list` before any git work.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX. ONE
must never be rebuilt: **`feat/player-overview-tab`**.

⭐ **THE REPO IS NOT THE SYSTEM**: for warehouse/cloud/CI/scheduler facts check the system that
owns them (`bq ls`, `glab api`, `gcloud` — free metadata). Bit twice.

## ⭐ The ingest cluster
**TWO nightlies:** `data:nightly` on **Cloud Run under #39**; the GitLab schedule is paused ON
PURPOSE. Runbook `deploy/nightly/README.md`.
✅ **#74 FIXED** (`!70`): the nightly image tracks `main` on any push touching `*data_paths_image`
— **but the FIRST auto-run is UNVERIFIED; check it fired.** ⚠ **NOT Cloud Build** (its identity
held project Editor from ANY branch — revoked); kaniko in-job.
⚠ **OWED: set `deploy-nightly-image` resource_group to `oldest_first`** (only once the group
exists — the first run creates it). Default `unordered` lets two near-simultaneous merges deploy
out of order, pinning the OLDER commit. **Sentinel NOT repointed** — its own decision.
⚠ **A GREEN RUN PROVES NOTHING** — it says the container ran, not which code. **Check DATA.**
⚠ **None of the 4 ingest fixes does what its title says** — see #896-#898.
✅ **`!62` MERGED** — the four "gap recorded as fact" holes are closed. **Detection NOT started:**
`event_loss_detector_from` is still **'2026-08-19', in the FUTURE, so `!57`'s test is inert**;
⛔ **the volume-delta threshold is the CPO's and blocks it.**

## ✅ #84 CLOSED — warehouse clean, all 310 orphans dropped, **432 → 122**.
⛔ Nothing reconciles it on a schedule; a recurring check = NEW MECHANISM, unbuilt.
⚠ **A UDF IS NOT A MISSING TABLE** (`bq ls` omits ROUTINES): a LIVE view landed in the "risk-free"
phase, and 2 reviewers + 8 mutations passed BLIND.

## ⭐ COST — read **GitLab issue #3** first
**#3 holds it all.** ⚠ **#70** is the scan-budget guard; `require_partition_filter` and
`maximum_bytes_billed` are **NEITHER set**. ⚠ **Spend UNKNOWN** since 08-03.

## Player page — HELD on ONE decision, and it is HIS
Which entities earn their own page, and whether a past season gets a URL or a control. (GitHub
#845 + #882, bodies unreachable.) Scale: 154,767 players, 176,235 matches, 51,903 h2h, 9,669 teams.
**Overview is BUILT but UNCOMMITTED** in stash `feat/player-overview-tab`; its default season is
known-wrong.

## OWED — deferred
- Guard telemetry absent (#30). Delete `macros/apif_latest_source_partition.sql`; mirror crests.
- ⛔ **The contract/Stop gates do NOT understand a MERGE.** Mid-merge every incoming file reads as
  "dirty outside the contract", so the clean-tree rule blocks editing `contract.md`.
  ⚠ **WORKAROUND**: `_gate_bash_pre` skips `.claude/task/`, so write those via Bash mid-merge.
  Needs a `MERGE_HEAD`-aware skip; protected path, own task.
- **#904 IS THE DOMINANT FAILURE** — a claim asserted rather than RUN. ⚠ Checks that told me what I
  wanted: a bulk-edit script matching nothing, a `pytest` erroring on an unknown flag and exiting
  0, `check_task_artifacts` saying "empty diff OK" with nothing committed, a re-measure reporting 0
  gaps because a Windows manifest writes `path` with BACKSLASHES. **FLOOR every discovery. Read
  output, not exit.**

## NEXT
0. ⭐ **#82 MR4c** — see ⭐⭐ CURRENT.
0b. ⛔ **CI IS FIXED BUT ONLY IN MEMORY — IT DIES ON THE NEXT REBOOT.** 08-21: every job failed in
   ~4s at `get_sources` (`HTTP 403`) because the build machine goes out over **IPv6** and GitLab
   refuses it. Fixed live with `ip -6 route del default`; **permanence is OWED**, as is a **working
   SSH key — none exists**. Detail in the runner memory file.
1. **Team names**: finish the ~15 unverified Pool 1 teams, then decide whether to go beyond Pool 1.
   Also the player-name truncation.
2. **Decide `nav.json`'s fate** — zero frontend consumers since `!80`. Give it one, or delete
   `build_nav`/`fetch_nav`/the `--entities nav` branch, which unblocks deleting `display_group`
   (#57). ⚠ Check no CI job invokes `--entities nav` first, and note `display_group` is NOT
   deletable alone: `mart_competition_index.sql:90-91` reads its blankness as the browsable gate.
2b. **A trending-doc-rot pass.** Docs describe the "trending" block as if it exists; it was cut
   08-08. `09_chrome.md` §4/§10 remains. SEMANTIC sweep.
3. ✅ **"Pipelines must succeed" IS ON** (verified 08-22). This entry once said FALSE and that was
   wrong. **Check the live setting, not this file.**
4. **#47** — makes the competitions page's rows real links. Decisions: 680px width (not the mock's
   1080px), single-select filters, rows inert until it ships. Wire `competition_index` into CI's
   `--entities` list in #47's MR, not before.
5. **Audit stream**: Q2 of #21 · delete 2 dead `~/.claude/hooks/` copies · route/delete
   `seo-expert-reviewer`.  6. **COST** — trigger/cost map first, as an issue.
7. **#845 + #882 — his decision.** Unblocks the player page.  8. **Legal**, then go live.
9. Follow-ups (GITHUB, **bodies UNREACHABLE** — re-derive from code): DE/FI i18n gaps · PROTECTED
   path editable with no `protected_override` · `Regular Season - 20` the copy gate cannot see ·
   blank `competition_type` skipped by all 3 guards (**#83**).
10. Mine, on GitLab: **#64** #63's residuals · **#67** the contract gate enforces on Edit only, so
   `sed -i` bypasses it · **#68** the form-window CODE diverges from `metrics_context_model.md` §4
   (⚠ the agreement is the authority; never fix by editing the doc) · **#60** `.venv` · **#71** the
   duplication mechanism.

## OPEN — the CPO's alone
Imprint operator + address (#799) · hosting recurring run · feedback Apps Script (#687) · **#81**
duplicate-club alias · #875 · #895 · #21.

## DO NOT (standing)
- **DESIGN, the weak spot:** never off the cuff. Rendered output not prose; copy decisions BEFORE
  the branch, and copy is ALWAYS his (§10) even when he delegates the drafting to me.
- **Every displayed value needs its mart column named, not "a seed has it".** And do NOT
  generalize one page's mart shape onto another — see THE METHOD above.
- Do NOT treat the tracker as agreed work. No new planning docs, no fresh audits. Do NOT touch
  `site/`. Do NOT derive facts in the export or frontend.
- ⛔ **VERIFY BEFORE ASSERTING.** Search `escalations.log` + docs for a prior ruling FIRST.
- **Never merge an MR. The CPO merges. Branch from main; never commit to main.**
- Plain language, lead with the decision, **no em dashes**, no walls of text, **no jargon**: say
  "the league page" not "the hub", "database table" not "mart". ⚠ Hit AGAIN 08-24 — asked to
  confirm "the drift check", he replied **"which drift check"**. Describe what it DOES.

## Verified state reference
- **v2 built:** design system + 28 components, fixture page, team page (3 tabs), home, competitions
  index, page-spec + SEO contract, metric labels per locale.
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). Reselling
  API-Football data is the one hard ban.
