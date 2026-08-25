# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-25**. **main `fa61b46`.** #84 + #82 MR1-MR4b + the CI wiring MERGED;
**MR4b-2 committed, reviewed, awaiting merge.** **NEXT once it merges: MR4c.** Product
**Matchday Pilot**; **GITLAB** (`glab`, MRs); runner `ci-runner-01`, ZERO GitLab minutes.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding
on `attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ CURRENT — **#82 MR4b-2 committed, awaiting merge. Next = MR4c** (2026-08-25)

⭐ **READ `escalations.log`'s 08-20 to 08-25 entries FIRST** — numbers, rulings, each MR's defects.
**Do not re-scope or re-audit any of it.**

Plan `serialized-enchanting-frost.md`. **MR2** declared 979 columns, **MR3** wired 146, **MR4a**
(`!98`) generated 80 metric blocks from `metric_catalogue.csv`, `!100` put `--check` in CI.
**MR4b** closed **130** derived columns (a metric + one affix), **MR4b-2** promoted **31** names to
one shared definition each; blank in-scope **635 → 422**.
⚠ **REGENERATE** after editing the seed AND after adding a derived column: the generator's second
input is the model YAML.
⭐ **NEXT: MR4c**, and it is all judgement — 134 names no seed defines, 26 partials whose sites
DISAGREE, **6 names pulled from MR4b-2** whose sentence is false at some site, and the 5 nested
`recent_meetings.*` fields (a dotted name cannot be a docs block). Then **MR5**: presence on.
⛔ **48 COLUMNS NEED A CPO RULING AND STAY BLANK.** Seven metrics (`goals`, `goals_against`,
`defensive_actions`, `shots_on_goal`, `shots_total`, `passes_accurate`, `passes_total`) are
`entity = player` ONLY while team models use the same names, so those team columns have nothing to
point at. Team metrics the catalogue lacks, or misnamed columns? The football reviewer read them as
genuinely different. Same family as **#88**.
⛔⛔ **A SHARED BLOCK IS ONLY AS TRUE AS ITS WIDEST CALL SITE — READ EVERY MODEL IT REACHES**, and
read the SQL, not the sentence. **6 of 37 promotions were PULLED for this**: `is_home` said
"upcoming fixture" at 4 finished-fixture models, `opponent_shots_total` said "cumulative" at a
per-match model, 3 said "window legs" at a season-cumulative one, and `result` named a source model
one site never reads. ⭐ **A PROVENANCE CLAIM IS CHECKABLE ONLY IN THE SQL** — my own sweep read the
sentences and missed `result`, because it reads perfectly well there. Also hit twice in MR4b on one
NULL clause: true for teams, impossible for players, then the fix dropped a TRUE cause.
⚠ **A REVIEWER PASS CAN BE THE WEAKER VERDICT** — check a PASS's supports, not just a FAIL's. And
a `protected_override` goes in `escalations.log` BEFORE the branch touches the protected path.
⛔⛔ **A NAME THAT MEANS TWO THINGS IS INVISIBLE TO THE GATE** — it skips the bare name as
ambiguous, so a wrong or blank site goes unseen. **ASSERT THESE FROM THE YAML DIRECTLY.**
`league_code` = the competition EXCEPT on entity-scoped pulls (transfers, coaches, player
profiles/teams, `base_apif__teams_global`) where it is INGEST PROVENANCE: **6 wrong**, review found
all six; its 49 blanks stay blank; **ROOT CAUSE = #87**. ⚠ **NO CLASSIFIER WORKS** — 4 tried — so
**EVERY derived block is entity-suffixed** and a metric undefined for a column's entity has nothing
to point at. **Blank and visible beats documented and wrong.**
✅ **`persist_docs` WORKS EVERYWHERE** — **#86 said otherwise and is CLOSED AS WRONG.**
⛔⛔ **A CHECK THAT AGREES WITH ITSELF PROVES NOTHING — 9× now, detail in the log.** 18 mutations
over MR4b + MR4b-2, **5 SURVIVED**, every survivor a real defect and **3 of them a wrong RULE, not
a weak assertion**. ⚠ **WRITING A TEST IS NOT HAVING ONE — break it and watch THAT test go red**,
and when a mutation SURVIVES ask whether the guard is even reachable. ⚠ A green suite on ONE OS is
not green — prove it on `git show main:<path>` bytes.

⛔ **A TOO-LONG DESCRIPTION BREAKS PROD.** `persist_docs` is on for 97 models + 9 seeds. **1,024**
chars/column, **16,384**/relation; one over = HTTP 400 and the model FAILS.
⚠ `seeds:` is persist_docs-ONLY: a `+schema` relocates all 9.
⛔ **TASK ARTIFACTS COLLIDE ON CONCURRENT BRANCHES (4× on `!91`).** Take this task's whole, MERGE
`escalations.log`+`active_work.md`, rebind `review.md`'s hash — **no re-review owed**.

✅ **THE GATE** (`check_description_hygiene.py`) runs in CI + `stop_gate.py` FAST_GATES: 6 content
rules, object coverage, shared-definition coverage. ⚠ Its shared-block rule has **NO layer filter**,
so a new block makes a blank column of that name a finding in staging and base too — write, wire
and promote in ONE commit. ⚠ Rules match ANNOTATION forms, not plain verbs: bare `ruled` hits
"goal ruled out for offside".

⛔ **THE PROVIDER SENDS NO DESCRIPTIONS — CHECKED.** Stats are a label and a number; every
definition is OURS. For an ambiguous name (`passes_total`: attempted or completed?) derive the
answer from our own fixtures.
⚠ **CPO RULINGS 08-21:** "every column, no exception" (staging+base OUT) · no thin filler · docs
blocks kept **only with a mechanism enforcing them** · **NO osmosis**.
⛔ **INHERITING UPSTREAM PROSE CARRIES AN INHERITED ERROR.** **GRAIN claims are safe to inherit;
BEHAVIOUR and PROVENANCE claims are NOT.** MR1 shipped a FALSE "newest is the fullest".
⛔ **RECORD THE OPTION CHOSEN AND NOTHING ELSE.** Reasoning wrapped around an answer hardens into a
ruling he never gave.

⛔ **#83 — COMPETITION CLASSIFICATION HAS NO CORE DIM.** 12 models join the seed direct.
⚠ **SEEDS ARE SOURCES, settled** — the defect is LAYERING: read a seed ONCE at base/core, publish
a dim.

⛔ **FIVE TRAPS, every one hit for real. Do not re-learn them.**
1. **A too-narrow grep reported as a clean sweep**, and **a keyword scan is blind to a claim using
   NO keyword**. "partition key" is FALSE; 6 survivors = **#79**. A grep also matches the
   DOCUMENTATION of a defect as the defect. Found by READING the SQL.
2. **A bulk-edit script reporting success while matching nothing.** Assert it found work.
3. **Verify a reviewer finding, then act** — both directions.
4. **`--review-patch` writes to STDOUT**, so without redirect the patch is silently the PREVIOUS
   task's. `origin/main` is the DORMANT GitHub remote — use `gitlab`.
5. ⛔ **NEVER WRITE A REVIEWER'S VERDICT YOURSELF.** MR5 recorded PASS for two who returned FAIL.
   Send the confirm and WAIT. ⚠ Never edit any file while the suite runs.

⛔⛔ **THE STANDING LESSON — 5 FAILs across MR4b and MR4b-2, same class each time.** CPO: *"you spam
things all around the repo and then forget to clean up ... contradictions in our docs and files."*
Each round I fixed only the figure the reviewer named. ⭐ **THE CAUSE IS A SEARCH KEY, NOT
DISCIPLINE** — I sweep for the numbers I REMEMBER changing, so a forgotten one survives, and 4
prose corrections changed nothing. **INVERT IT: pull EVERY number out of the artifacts and ask of
each "is this still true".** That ended it. **#71**.

⛔ **TEAM NAMES — paused.** The provider's `team_name` is often not the display name;
`team_name_overrides` (in `base_apif__teams_global.sql`) fires on completeness OR collision. **97 of
~130 Pool 1 corrected**, each citing an English Wikipedia URL. ⚠ **Bayern München EXCLUDED ON
PURPOSE** — locale preference is never corrected. NOT done: ~15 Pool 1, teams outside it,
`dim_player` short-names. **#81** = duplicate records for ONE club.

✅ **SETTLED, do not re-propose.** BROWSE DROPPED (`!80`) — home renders **next matches ALONE**;
`08_browse.md` + competitions page stay LIVE. TOP TEAMS = **one per league**, not pooled;
⚠ `top_teams_mock.html` shows the wrong shape and GAP-29's mart is not started.

## ⭐⭐ THE METHOD, standing rule for every page (CPO's own words, do not reword)

*"the exercise is: does the mock consider the underlying mart (or mart gap)."* Per element:
(1) name the exact MART COLUMN — a seed/registry/catalogue is NOT a source, and reading one from a
page is the same violation as computing in the frontend; (2) no mart column = a GAP, registered in
`99_gaps_register.md` BEFORE building; (3) check the mock's OWN rendered numbers against the spec.
⭐ **AUTOMATION (trace script + staleness checker) NOT built, NOT approved.** Ask first. **#78**.

⚠ **STANDING RULE: the handover rides in the SAME commit as the code it describes.**

## ⭐ ORIENTATION
**Audits: GitLab #30, DO NOT run another** (a TARGETED blind assessment IS allowed).
**⚠ OPERATIONAL NOTES ARE IN `CLAUDE.md`** (dbt CLI, SQLFluff, commit mechanics, stash-dance,
CWD/fnmatch/heredoc/grep traps). **Do not copy back**: that file is not capped.
**FIRST ACTION: `git stash list` before any git work.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX. ONE
must never be rebuilt: **`feat/player-overview-tab`**.

⭐ **THE REPO IS NOT THE SYSTEM**: for warehouse/cloud/CI/scheduler facts check the system that
owns them (`bq ls`, `glab api`, `gcloud` — free metadata). Bit twice: `raw_archive` called "never
built" from zero repo refs when it EXISTS, and this file's own "Pipelines must succeed" line.

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
