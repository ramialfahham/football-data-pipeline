# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-17**. **ONE MR OPEN: `!57`** (#75 part C, the event-loss detector;
reviewed round 2, PASS). **`!53`, `!56`, `!50` all merged.** ⚠ `data:build:mr` on any MR is red on
a PRE-EXISTING orphan, not on the diff (⭐ below). Product **Matchday Pilot**; repo on **GITLAB**
(`glab`, MRs). GitHub KEPT but dormant.
Self-hosted runner `ci-runner-01`; jobs burn ZERO GitLab minutes. ⚠ **A GROUP MOVE IS COMING**; it
changes the project PATH, breaking remote URLs, the WIF binding on `attribute.project_path`, and
every hardcoded `rami.al-fahham/football-data-pipeline`. Check before path-dependent work._

⚠ **START HERE: the tree is on `fix/75c-event-consistency-tests` (that is `!57`), and THIS FILE's
current version lives on that branch, NOT on main.** Merge `!57` first, or carry this file across
when you branch — otherwise you will read a stale handover and re-open decided questions.

## ⭐ CURRENT — #62 STEP 3 IS BLOCKED ON #69'S DIMENSIONS. DO NOT BUILD THE MART (2026-08-16)

**#62, five steps.** 1 (`!40`) and 2 (#57) done. **3 is `mart_competition_index`**, 4 repoints the
export, 5 the page spec. ⚠ A seed COLUMN and its reader cannot ship together — 3 is its own MR.
⛔ **THE MART IS WRITTEN AND PARKED** — `git stash list`, message `feat/62-mart-competition-index`.
Match by MESSAGE. `region_label` is the blocker: COUNTRY and CONTINENT in one column, branching on
`single_country`. **CPO: *"You don't mix up countries and continents in one column and add a flag
'single country'."*** ⚠ Nothing ever read that flag.
⛔ **#69 IS RESCOPED to TWO dims**: `dim_region` from `confederations.csv` (**exists, read by
nothing**) + `dim_country` built new. A competition POINTS AT one; **which relationship is
populated IS the answer** — no flag, no branch. The registry's `country` mixes 21 countries with 24
region words; those 24 become NULL. Deletes `single_country`. ✅ **DISCOVERY + NAMES DONE — the
08-16 notes on #69 are the authority.** 285 provider values → **224 entities**. **Rule: English,
everyday short form, no diacritics**; exceptions `Republic of Ireland` + `United States of
America`. **NEXT: `dim_country` + `dim_region`, then FKs.**

✅ **`!43` + `!45` LIVE IN PROD.** ⚠ `sync_dbt_vars.py:45` is now accurate — do not "fix" it.
⚠ **Never normalise country names by regex** — `Guinea-Bissau` is correctly hyphenated, MEASURED
on the player surface. **The transformation layer decides the FORM, the CPO the NAME.**

⛔ **`sort_order` IS OBSOLETE (CPO 2026-08-16)**; the mart must not read it. **The full rule is the
08-16 ordering note on #54 — read it, do not reconstruct it.** ⚠ **Mart carries FACTS, the spec
declares the ORDER BY** — sorting is arrangement, not a fact. ⚠ Retiring it reaches past #54 into
`export_site_data.py`, `BrowseGrid.astro`, `landing.json` — NOT scoped yet.

⛔ **HOME PAGE: authority is #40 + #41, NOT `10_home.md` §0** (which says nine/six boards top 5;
truth is FOUR boards of ONE metric, top 7). #367 shipped next matches → browse; Top players/teams
designed NOT built, slot BETWEEN. Follow-ups **#36** (blocks #377) · **#38** · **#42**–**#45**.

⚠ **REBASE TAX:** conflicts land in `.claude/task/*` and `active_work.md` — **MINE** for
contract/review, **UNION** `escalations.log`, then REBIND `diff_sha256`. When main has moved a lot,
take **THEIRS** wholesale and re-apply your delta.
⚠ **NEVER `git checkout --` to restore uncommitted work** — it restores from HEAD and wipes it.

⚠ **DEFERRED by #57 — do not "fix":** `world_championship` keeps its name (branched on at
`int_team_momentum_window.sql:135`; renaming without that edit silently gives the World Cup a
last-5 window, every test green) · `display_group` for **#44**.

**#54 competitions page: DESIGNED AND CLOSED** — its five notes supersede the description; read
them, do not reconstruct. ⚠ **Its 16 is ELEMENTS, not mart columns.**

## ⭐ AN AUDIT FINDS; IT DOES NOT DECIDE — AND DO NOT RUN ANOTHER
**GitLab #30.** Findings replicate, prioritisation does not — output is LEADS TO VERIFY, never a
work list. **Mechanism beats wording:** of 50 corrections, **33 prose-only, 22 recurred; every rule
that got a mechanism stopped.** ⛔ A fresh audit was REJECTED 08-16: #30 already ran.
**⚠ OPERATIONAL NOTES LIVE IN `CLAUDE.md`** — dbt CLI, SQLFluff, commit mechanics, the stash-dance,
CWD/fnmatch/heredoc/grep traps. **Do not copy back**: that file is not capped.
**FIRST ACTION: `git stash list` before any git work.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX. TWO
must not be rebuilt: **`feat/player-overview-tab: Overview BUILT`** and the **#62 mart** (⭐ above)._

## ⭐ #75 — WHY PROD IS RED, AND WHAT IS AND IS NOT FIXED
⛔ **A 2-row DQ failure leaves PROD HALF-BUILT and reddens every later MR.** `data:build:main` on
the `!50` merge hit the `fct_fixture_event.player_sk -> dim_player` orphan and **SKIPPED 103
nodes** — `mart_team_momentum_window` skipped while `mart_team_momentum` was NOT, so MRs fail
`assert_momentum_window_matches_momentum` (1641 rows) on unrelated diffs.
⚠ Layers for 1564795: raw 17 · staging 17 · base 17 · **core 27**. Core was the accidental archive;
base was STARVED, not failing.
✅ **`!56` MERGED — the retry DELETED the row but only checked *statistics*, so it destroyed
events.** MEASURED: 5 fixtures, 29 events. Ports **#896**.
⛔ **The backlog is UNREPAIRABLE** — the provider now returns 17 events for 1564795, gone at source.
⚠ **`fct_fixture_event` is INCREMENTAL: the RICHEST record, and RIGHT. Do NOT make the fact mirror
base** — measured, that deletes 13 real events from 1564793 alone.
⭐ **DECIDED 08-17 — CPO: *"raw keeps both versions."*** `RAW_APIF_FIXTURE_DETAILS` STOPS being
merge-on-write; the retry no longer deletes, both payloads land, and **BASE decides** (its existing
newest-per-`event_index` rule then yields 27, not 17). A deliberate partial reversal of #539 /
#33 item 8 FOR THIS TABLE — do not "restore" the delete as a regression fix. Verified safe before
the ruling: staging reads faithfully, base dedups on entity keys, `!56` already made the coverage
read order-independent. Cost ~cents.
⛔ **NOT BUILT** — remove `_delete_fixtures` from `batch_fixtures.py`; update
`docs/data_contract.md` + `layering.md` §1_staging (both describe the delete); pin it.
✅ **`!57` (part C) adds the DETECTOR** — `assert_no_event_loss_since_cutoff` flags any event the
fact holds that base lost. Scoped by KICKOFF DATE (`event_loss_detector_from`); ⚠ **never raise
that var to go green.** ⛔ Two sibling tests were KILLED by measurement ("PEN implies shootout
events" — **371/753** PEN fixtures have none); see `escalations.log` before re-proposing.

## ⭐ The ingest cluster
**TWO nightlies:** GitLab CI `data:nightly` moved to **Cloud Run under #39**, so its GitLab
schedule (id 4379625) is **paused ON PURPOSE — do not re-enable.** Runbook
`deploy/nightly/README.md`. ⚠ The 04:00 run FAILED on 08-17.
⛔ **#74 — THE IMAGE NEVER TRACKED `main`.** `gcloud run jobs deploy --source .` packages the
working tree and nothing redeploys it (no trigger, no CI job — verified). It ran 08-14 code for two
days and **rebuilt prod from it, REVERTING `!43`/`!45`**. Redeployed by hand 08-16; **stale again
on the next merge.**
⛔ **#75 — red nights are DATA QUALITY** (⭐ above for the chain and what is fixed).
⚠ **A GREEN EXECUTION PROVES NOTHING** — it says the container ran, not which code. **Check DATA.**
⚠ **An impact map that stops at LINEAGE misses GATES** (#33 item 14).
⚠ **None of the four ingest fixes does what its title suggests** — caveats on #896-#898.

## ⭐ COST — read **GitLab issue #3** first
**#3 holds it all** — baselines, #547's ranked list IN ITS ORDER, the free tools (`bq query
--dry_run`, `report_bq_cost.py`; ⚠ **paste the output or do not claim it**), the traps (**never a
time-based partition expiry on raw**, #892). Read it; do not redo it. ⚠ **#70** is the scan-budget
guard; #3 item 6: `require_partition_filter` + `maximum_bytes_billed` are **NEITHER set**.
- **⚠ STORAGE WAS NEVER MEASURED** (08-16; "storage" is **0×** in #3). Every figure is bytes
  SCANNED; storage only grows. `bq show` per table is free.
- **⚠ Current spend UNKNOWN.** Last measure 08-03 ($2.73/day) PREDATES #33 items 9/15. Never quote
  as current.
- **⚠ #2** — check `.data_paths_prod` before assuming what triggers a prod rebuild; it is NARROWER
  than the MR anchor.
- **⚠ Do NOT claim the API quota "breaks first"** — claimed once without evidence, withdrawn.
  (`standings.py:30` / `teams.py:28` DO loop every season daily with no skip — real.)

## ⭐ REVIEW MECHANICS — what the working agreement does not give you
Rules are `docs/working_agreement.md` §2 (#878). Only the traps live here.
- **Build the patch with the hook, never by hand:**
  `python .claude/hooks/git_discipline.py --review-patch > .claude/task/review_input.patch`
  ⚠ It is `git diff --staged <base>`, so **`git add` FIRST or it comes out EMPTY**. `contract.md` +
  `escalations.log` ARE delivered; task notes are not. A trailer names any excluded file that IS
  edited (#25), so absence is not evidence it is untouched.
  ⚠ **`review.md` must be `git add`ed too** — writing it is not committing it (a red CI on !50).
- **Run `check_task_artifacts.py` BARE** (#24, !15) — it resolves the live remote, as does the hook
  since **#63**. `--staged-hash` matches CI at any length.
- **A PASS may find nothing.** One `risks_checked:` entry is enough; never invent one. Cap 3 rounds
  then STOP. ⚠ `rounds: 0` is REFUSED.
- **`.claude/task/**` is scope-exempt; `active_work.md` is NOT** — it must be in `scope_paths`; a
  commit touching `contract.md` is **never** artifact-exempt.
- ⚠ **`git rebase` replays commits IN ORDER**, so a scope amendment committed LAST does not apply
  to an earlier commit's conflict. **`git merge` applies the tip at once — use it.**
- **⭐ A correction REPLACES, never accumulates, and must replace EVERYWHERE.** ⚠ 08-14: four
  occurrences cost five rounds — fixed in one artifact, alive in another as a PARAPHRASE. **Sweep
  the CLASS, not the phrase you wrote.** Mechanism: **#71**.

## Player page — HELD on #845
**#846 + #886 merged:** the season a page opens on is a warehouse fact (`is_featured_season`, DQ
guarded). **CPO: the pipeline picks, not the page**, by the tab's LENS.
**#845 + #882 are ONE decision and his** — which entities earn a page, and whether a past season
gets a URL or a control; deciding apart sets the URL shape twice. Measured (×3 locales): players
51,589→154,767; **matches BIGGER at 176,235**; h2h 51,903; teams 9,669; a 5-match gate leaves
1,274 teams / 21,979 players. **Bring the counts.**
**Overview is BUILT but UNCOMMITTED** in stash `feat/player-overview-tab: Overview BUILT` (⚠ NOT
the #62 mart stash); default is known-wrong (`seasons[0]` = most recent of ANY competition), mart
half IS shipped. **#848: FOUR tabs**, International a national-lens TAB not a toggle (a crawler
cannot follow a control).

## OWED — deferred
- **Guard telemetry is absent** (#30 finding 4) — 2,684 lines of enforcement, zero records of a
  gate firing. Also: delete `macros/apif_latest_source_partition.sql` · mirror crests.
- **⭐ #904 IS THE DOMINANT FAILURE** — a claim asserted rather than RUN. Faces seen: a grep scoped
  narrower than its sentence; a TEST that passes either way (#63 shipped three); a column read
  without its VALUES (`!43`); a number repeated out of this file (`!47`); a JOB STATUS read instead
  of the data (`!49`). **Absence must state where it looked; a test must be seen RED; green is not
  evidence.** Prose has failed 8×; the mechanism is **#71**.

## NEXT
0. ⭐ **BUILD PART A — "raw keeps both versions" is DECIDED** (⭐ #75 has the scope). Then merge
   `!57`.
1. ⛔ **PROD IS HALF-BUILT and nothing heals it on its own.** MEASURED 08-17: 1641 mismatched rows.
   ⚠ `.data_paths_prod` EXCLUDES `.gitlab-ci.yml` — **the old claim that a CI-only MR rebuilds prod
   is FALSE.** The nightly also FAILED. ⚠ **A rebuild still dies on the orphan even after part A**;
   part A stops FUTURE loss. Clearing the backlog is a separate call.
2. **THE NIGHTLY: #74** the image does not track `main` — redeployed 08-16 but stale on the next
   merge, so prod silently reverts. ⚠ **#4**: a web dispatch from ANY branch builds prod from that
   branch's code.
3. **#69 FIRST, then #62 step 3** (⭐ CURRENT). Discovery COMPLETE; next is **canonical names to the
   CPO**, then the two dims. Then step 4 repoints the export, 5 the page spec.
4. **The audit stream (⭐ above).** The CPO's, one command each: **Q2 of #21** (`main` push access
   to No one — the SERVER should protect it) · delete the 2 dead `~/.claude/hooks/` copies · route
   or delete `seo-expert-reviewer`.
5. **⭐ THEN COST, SYSTEMATICALLY** — the whole pipeline **including CI/CD, what gets triggered,
   when, where** (CPO). Trigger/cost map FIRST, rank by real spend, fix in that order; the map goes
   in a GitLab ISSUE.
6. **#845 + #882 — the CPO's decision.** Counts are in this file: bring them, not a general
   question. Unblocks the player page off the stash.
7. **Legal/imprint**, then launch.
8. Follow-ups (GITHUB numbers, **bodies UNREACHABLE** — re-derive from code): DE/FI i18n gaps ·
   PROTECTED path editable with no `protected_override` · `Regular Season - 20` provider text the
   copy gate cannot see · blank `competition_type` skipped by all 3 guards.
9. Mine, on GitLab: **#64** #63's residuals · **#67** the contract gate enforces on the Edit tool
   only, so `sed -i` bypasses it · **#68** the form-window CODE diverges from
   `metrics_context_model.md` §4 (⚠ **the agreement is the authority**; never fix it by editing the
   doc) · **#60** `.venv` is not where `CLAUDE.md` implies · **#70** scan-budget guard.

## OPEN — the CPO's alone
**Imprint operator + address** (#799), blocks publication, never conclude it ·
hosting recurring run · feedback Apps Script (#687) · **#850** alias · **#875** where a group name
lives · **#895 slim-vs-drop** · **#21**.

## DO NOT (standing)
- **DESIGN, the weak spot:** never off the cuff — approved wireframes + role briefs, no block
  invented to fill a slot, never the canonical page built on an edge case, ONE tab at a time.
  Rendered output not prose; copy decisions BEFORE the branch.
- Do NOT treat the tracker as agreed work; re-validate. **No new planning docs, no fresh audits.**
  Do NOT touch `site/` (retired). Do NOT derive facts in the export or frontend.
- ⛔ **VERIFY BEFORE ASSERTING; FINISH EXPLORE BEFORE PROPOSING.** Search `escalations.log` and the
  docs for a prior ruling FIRST — on #75 four fixes were invented while **#896** already answered
  it (CPO: *"you are always coming up with something new. THAT is the real defect"*).
- **Never merge an MR. The CPO merges. Branch from main; never commit to main.**
- Plain language, lead with the decision, **no em dashes**, no walls of text.
- Do NOT ask him to adjudicate what a rule settles. **But copy is ALWAYS his (§10).**
- Do NOT bring him a fix for a defect he never asked about; fix it and move on.

## Verified state reference
- **No PUBLIC site.** v2 unlisted, every page `noindex` — why URLs are still free.
- **v2 built:** design system + 26 components, fixture page, team page (3 tabs), home page (next
  matches → browse), page-spec + SEO contract (#826/#844), per-locale metric labels.
- **Tests: 816 python + 1 skipped** (08-16), 59 site, **1004 dbt in prod**. ⚠ MEASURE, never
  predict (#904). `ruff` runs as `lint:python`, config `.ruff-ci.toml` (filename load-bearing).
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). Reselling
  API-Football data is the one hard prohibition.
