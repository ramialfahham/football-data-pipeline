# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES, ~220
> over, which sends you trimming content that fits).

_Last updated **2026-08-16**. **TWO MRs OPEN, merge `!53` FIRST.** `!53` (#73) removes the
MR-time bootstrap ingest; `!50` (#72) onboards BPL/TSL/EKS. Both have a RED `data:build:mr`
and both are merged on judgement — see ⭐ ONBOARDING MRs below, it is expected, not a defect.
main `217b321` — see `git log` for what merged 08-12→08-16, this file no longer enumerates it.
Product **Matchday Pilot**; repo on **GITLAB** (`glab`, MRs, `.gitlab-ci.yml`). GitHub KEPT but
dormant — Actions run nothing, its 114 issues unreachable.
Self-hosted runner `ci-runner-01`; jobs burn ZERO GitLab minutes. ⚠ **A GROUP MOVE IS COMING** and
it changes the project PATH — breaking remote URLs, the WIF binding pinned to
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`. Check
before starting anything path-dependent._

## ⭐ ONBOARDING MRs GO RED ON `data:build:mr`. THAT IS CORRECT. DO NOT "FIX" IT (2026-08-16)

Four singular tests (`assert_base_leagues` / `_teams` / `_fixtures_next` / `assert_fct_fixture`
`_covers_active_competition_var`) assert "every code in the var has rows". An onboarding MR adds
the code and `!53` stops the MR job ingesting, so the rows cannot exist until post-merge. **The
tests state a true fact.** Merge on judgement, as `!50`.
⛔ Silencing them with a tag+exclude WAS BUILT AND REJECTED: all four routed reviewers failed it as
a coverage cut, the CPO called it a hack, and the scope claim behind it was wrong (said 1 test;
there are 4 of 8, the other 4 self-exclude via `inner join base_apif__leagues`).
⭐ CAUSE = **#76**: nothing records that a league HAS been ingested, only that it SHOULD be.

## ⭐ CURRENT — #62 STEP 3 IS BLOCKED ON #69'S DIMENSIONS. DO NOT BUILD THE MART (2026-08-16)

**#62, five steps.** 1 (`!40`) and 2 (#57) done. **3 is `mart_competition_index`**, 4 repoints the
export, 5 the page spec. ⚠ A seed COLUMN and its first reader cannot ship together — 3 is its own MR.

⛔ **THE MART IS WRITTEN AND PARKED** — `git stash list`, message `feat/62-mart-competition-index:
mart + confederations region_rank; region_label BLOCKED on #69`. Match by MESSAGE. `region_label`
is the blocker: COUNTRY and CONTINENT in one column, branching on `single_country`. **CPO: *"You
don't mix up countries and continents or regions in one column and add a flag 'single country'.
That's really bad modeling."*** ⚠ Nothing ever read that flag.
⛔ **#69 IS RESCOPED to TWO dimensions** (its 08-16 note is the authority): `dim_region` from
`confederations.csv` (exists, 7 rows, read by nothing) + `dim_country` built new. A competition
POINTS AT one; **which relationship is populated IS the answer** — no flag, no branch. The
registry's `country` mixes 21 countries with 24 region words; those 24 become NULL. DISCOVERY
first, then names to the CPO.

✅ **`!43` + `!45` MERGED — country fixed at source and standardised in base**, 45/45.
⚠ `sync_dbt_vars.py:45` is now accurate — do not "fix" it. ⚠ **Never normalise country names by
regex** (`Guinea-Bissau`, `Timor-Leste` are correctly hyphenated). **The transformation layer
decides the FORM, the CPO decides the NAME.**

⛔ **`sort_order` IS OBSOLETE (CPO 2026-08-16)**; the mart must not read it (incoherent across
types). **Approved rule:** has-upcoming-fixture → days to next kickoff **BUCKETED BY DAY** (raw
clock ranks ED 10:15 over PL 19:00, noise) → **region_rank** (UEFA 1 · FIFA 2 · CONMEBOL 3 ·
CONCACAF 4 · AFC 5 · CAF 6 · OFC 7, HIS judgement) → kickoff time → `league_code`; nothing upcoming
last, most-recently-played first. ⚠ Mart carries FACTS, the spec declares the ORDER BY — **sorting
is arrangement, not a fact**. ⚠ Retiring it reaches past #54 — `export_site_data.py:583`/`:586`,
`BrowseGrid.astro`, `landing.json`.

✅ **Membership is 45 rows** — all have fixtures and logos; registry `status` useless here.

⛔ **HOME PAGE: design authority is #40 (players) + #41 (teams), NOT `10_home.md` §0** (wrong on
both). #367 shipped next matches → browse; Top players/teams designed NOT built, slot BETWEEN.
Follow-ups **#36** (blocks #377) · **#38** · **#42** · **#43** · **#44** · **#45**.

⚠ **REBASE TAX:** conflicts land ONLY in `.claude/task/*` and `active_work.md`. **MINE** for
contract/review/review_input; **UNION** `escalations.log` by ARITHMETIC, then REBIND `diff_sha256`.
⚠ **NEVER restore uncommitted work with `git checkout --`** — it restores from HEAD and wipes the
edits. Bit me twice.

⚠ **DEFERRED by #57 — do not "fix":** `world_championship` keeps its name (branched on at
`int_team_momentum_window.sql:135` behind a `coalesce`; renaming without the SQL edit silently gives
the World Cup a last-5 window, every test green) · `display_group` kept for **#44**.

**#54 competitions page: DESIGNED AND CLOSED** — its five notes supersede the description.
⚠ **Its 16 is ELEMENTS, not mart columns** ("16-column contract" is WRONG). Mocks live OUTSIDE
the repo in `design-mocks/`.

## ⭐ AN AUDIT FINDS; IT DOES NOT DECIDE — AND DO NOT RUN ANOTHER ONE
Audit + cold re-run in **GitLab #30**. **Findings replicate, prioritisation does not** — output is
LEADS TO VERIFY, never a work list. **Mechanism beats wording:** of 50 corrections, **33 prose-only,
22 recurred, every rule that got a mechanism stopped.** ⛔ Offering a fresh audit was REJECTED
2026-08-16: #30 already found it, and a re-run returns our own built work as a finding.

**⚠ OPERATIONAL NOTES LIVE IN `CLAUDE.md`** — dbt CLI, SQLFluff, commit mechanics, the stash-dance,
CWD/fnmatch/heredoc/grep traps. **Do not copy back**: that file is not capped.
**FIRST ACTION: `git stash list` before any git work.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX. TWO
must not be rebuilt: **`feat/player-overview-tab: Overview BUILT`** and the **#62 mart** (⭐ above)._

## ⭐ The ingest cluster — MEASURED 2026-08-16, not inferred
**TWO Cloud Run jobs, both ENABLED, both by design** (`gcloud scheduler jobs list --location
europe-west1`): `fdp-nightly` daily 04:00 UTC, `fdp-freshness` **hourly** at :07. GitLab's
`data:nightly` schedule (4379625) is **paused ON PURPOSE — do not re-enable**; #39 moved it to
Cloud Run. Runbook `deploy/nightly/README.md`. The "weekly" one is NOT a job — it is the 7-day
transfers cadence INSIDE the daily run.
✅ `fdp-freshness` 8/8 green, **cost ZERO** (`client.get_table()` is metadata, no bytes scanned).
✅ **The dbt build DOES run in the nightly** (~1004 tests) — the old "unverified" note is answered.
⚠ **NOT flaky. Deterministic DQ failures, FIXTURE EVENTS every time.** 08-11 + 08-12
`assert_event_team_in_fixture_participants`; 08-14 the completeness gate (**fixed since**);
08-16 12:42 MANUAL run `relationships fct_fixture_event.player_sk → dim_player`. 08-15 and 08-16
04:00 scheduled runs were GREEN. One orphan row reddens the whole run. **NOT YET FILED** — find
the rows and fix the cause; do not add another `fixture_event_team_overrides` row.
⚠ **An impact map that stops at LINEAGE misses GATES:** #33 item 14 changed FETCH CADENCE and broke
a gate assuming nightly fetches, past four reviewers.
⚠ **None of the four ingest fixes does what its title suggests** (#896-#898). Ultra plan
**450/min, 75,000/day**, draw ~8,300, so the PER-MINUTE limit binds.

## ⭐ COST — read **GitLab issue #3** before touching anything

**#3 holds it all** — baselines, #547's ranked list IN ITS ORDER, the free tools (`bq query
--dry_run`, `report_bq_cost.py`), the traps (never a time-based partition expiry on raw; "paste the
output or do not claim it"). Read it; do not redo it. NOT in #3, found 08-16:
- **⚠ STORAGE WAS NEVER MEASURED.** "storage" appears **0×** in #3; every figure is bytes SCANNED,
  and storage only grows with a nightly-snapshot ingest. `region-eu…TABLE_STORAGE` is Access Denied
  here; per-table `bq show` works and is free.
- **⚠ NO COST CEILING.** #3's item 6: `require_partition_filter` + `maximum_bytes_billed` are
  **NEITHER set**. Nothing bounds a runaway query. **#70** is that guard.
- **⚠ Current spend UNKNOWN.** Last measure 08-03 ($2.73/day) PREDATES #33 items 9/15, the fixes to
  its own top item. Never quote it as current.
- **⚠ #2 IS LIVE; fired 08-07 and 08-13.** `data:build:main` triggers on `data_paths`, which
  includes `.gitlab-ci.yml` and `scripts/check_*.py`, so a governance-only MR rebuilds all of prod.

## ⭐ REVIEW MECHANICS — what the working agreement does not give you
Rules are `docs/working_agreement.md` §2 (#878). Only the traps live here.

- **Build the patch with the hook, never by hand:**
  `python .claude/hooks/git_discipline.py --review-patch > .claude/task/review_input.patch`
  ⚠ It is `git diff --staged <base>`, so **`git add` FIRST or it comes out EMPTY**. `contract.md` +
  `escalations.log` ARE delivered; task notes are not. A trailer names any excluded file that IS
  edited (#25), so absence is not evidence of untouched.
  ⚠ **`review.md` must be `git add`ed too** — writing it is not committing it (cost a red CI on !50).
- **Run `check_task_artifacts.py` BARE** (#24, !15) — it resolves the live remote, as does the hook
  since **#63**; `GOVERNANCE_BASE` overrides both. `--staged-hash` matches CI at any length.
- **A PASS may find nothing.** One `risks_checked:` entry is enough; never invent one. Cap 3 rounds
  then STOP. ⚠ `rounds: 0` is REFUSED.
- **`.claude/task/**` is scope-exempt; `active_work.md` is NOT** — it must be in `scope_paths`, and
  a commit touching `contract.md` is **never** artifact-exempt.
- ⚠ **`git rebase` replays commits IN ORDER**, so a scope amendment committed LAST does not apply
  to an earlier commit's conflict. **`git merge` applies the branch tip at once — use it** (08-16).
- **⭐ A correction REPLACES, never accumulates, and must replace EVERYWHERE.** ⚠ Four occurrences
  on 08-14 cost five review rounds — corrected in one artifact, alive in another as a PARAPHRASE.
  **Sweep the CLASS semantically, not the phrase you wrote.** Mechanism: **#71**.

## Player page + the next CPO decision
**#846 + #886 merged:** the season a page opens on is a warehouse fact (`is_featured_season`, DQ
guarded). **CPO: the pipeline picks, not the page**, by the tab's LENS.

**#845 + #882 are ONE decision and his** — which entities earn a page, and whether a past season
gets a URL or a control. Deciding apart sets the URL shape twice. Measured (×3 locales): players
51,589→154,767; **matches BIGGER at 176,235**; h2h 51,903; teams 9,669. A 5-match gate leaves
1,274 teams / 21,979 players. Bring the counts.

**The player Overview is BUILT but UNCOMMITTED** in the stash `feat/player-overview-tab: Overview
BUILT` (⚠ NOT the #62 mart stash), with a known-wrong default (`seasons[0]` = most recent of ANY
competition, so both samples open on WC 2026). Mart half IS shipped, a one-line change on resume.
Held on #845. **#848: FOUR tabs**, International a national-lens TAB not a toggle (a crawler cannot
follow a control).

## OWED — deferred
- **Guard telemetry is absent** — 2,684 lines of enforcement, zero records of a gate firing (#30
  finding 4); **the round cap only RECORDS** a builder-typed number. Also: delete
  `macros/apif_latest_source_partition.sql` · metric-change skill · mirror crests.
- **⭐ #904 IS THE DOMINANT FAILURE** — a claim about the code asserted rather than RUN. Faces seen:
  a grep narrower than the sentence it supported; a TEST that passes either way (#63 shipped three);
  reading a column but never its VALUES (`!43`); repeating a number out of this file without opening
  the source (`!47`); see also DO NOT, 08-16. **A claim of ABSENCE must state where it looked; a
  test must be seen RED first; a column is not data. Grep for SIBLINGS before writing "only one".**
  Prose has failed 8×; the mechanism is **#71**.

## NEXT
0. **MERGE `!53` THEN `!50`** (both CPO's; both red on `data:build:mr` by design, ⭐ above). Then
   the two FIXTURE-EVENT orphans that redden the nightly (⭐ ingest cluster) — **not yet filed**.
   ⚠ **#4**: a web dispatch from ANY branch builds prod from THAT branch's code.
1. **#69 FIRST, then #62 step 3** (⭐ CURRENT) — step 3's `region_label` needs #69's two dimensions;
   the mart is written and stashed. Then step 4 repoints the export, 5 the page spec.
2. **The audit stream (⭐ above).** The CPO's, one command each: **Q2 of #21** (`main` push access
   to No one — the SERVER should protect it, not a client hook) · delete the 2 dead
   `~/.claude/hooks/` copies · route or delete `seo-expert-reviewer`.
3. **⭐ THEN COST, SYSTEMATICALLY** — the whole pipeline **including CI/CD, what gets triggered,
   when, where** (CPO). Trigger/cost map FIRST, rank by real spend, fix in that order; the map goes
   in a GitLab ISSUE, not a doc. **#76** and the unmeasured STORAGE line (⭐ COST) belong in it.
4. **#845 + #882 — the CPO's decision.** Counts are in this file: bring them, not a general
   question. Unblocks the player page off the stash.
5. **Legal/imprint**, then launch. (The "first green nightly" gate is MET — 08-15 and 08-16.)
6. Follow-ups (GITHUB numbers, **bodies UNREACHABLE** — re-derive from code): DE/FI i18n gaps
   (metric group headings, `GD`/`W/D/L`/`T·I·B`, rows breaking mid-word) · a PROTECTED path
   editable with no `protected_override` · `Regular Season - 20` is provider text the copy gate
   cannot see · blank `competition_type` skipped by all 3 guards.
7. Mine, on GitLab: **#64** #63's residuals · **#67** the contract gate enforces on the Edit
   tool only, so `sed -i` bypasses it · **#68** the form-window CODE diverges from
   `metrics_context_model.md` §4 in 2 places (⚠ **the agreement is the authority**; never fix it by
   editing the doc) · **#60** the canonical clone sits on a feature branch, so `.venv` is not where
   `CLAUDE.md` implies · **#70** scan-budget guard.

## OPEN — the CPO's alone
**Imprint operator + address** (#799), blocks publication, never conclude it · hosting recurring run
· feedback Apps Script (#687) · **#850** alias · **#875** where a group name lives · **#895
slim-vs-drop, blocking the biggest cost item** · **#21** · **#69** canonical country names.

## DO NOT (standing)
- **DESIGN, the weak spot:** never off the cuff — approved wireframes + role briefs, no block
  invented to fill a slot, never the canonical page built around an edge case, ONE tab at a time.
  Rendered output not prose; gather copy decisions BEFORE the branch.
- Do NOT treat the tracker as agreed work; re-validate. **No new planning docs, no fresh audits.**
- Do NOT touch `site/` (retired). Do NOT derive facts in the export or frontend.
- **Never merge an MR. The CPO merges. Branch from main; never commit to main.**
- Plain language, lead with the decision, **no em dashes**, no walls of text.
- Do NOT ask him to adjudicate what a rule settles. **But copy is ALWAYS his (§10).**
- Do NOT bring him a fix for a defect he never asked about; fix it and move on.
- ⛔ **VERIFY BEFORE ASSERTING.** 08-16 cost four round-trips: an insecure option written into an
  issue, "only one test affected" when four were, his nightly setup described unchecked.
  **Run the grep, read the file, then speak.**

## Verified state reference
- **No PUBLIC site.** v2 unlisted, every page `noindex` — why URLs are still free.
- **v2 built:** design system + 26 components, fixture page, team page (3 tabs), home page (next
  matches → browse), page-spec + SEO contract (#826/#844), per-locale metric labels.
- **Test counts go stale — MEASURE, never predict** (#904). `ruff` runs as `lint:python`, config
  **`.ruff-ci.toml`** (filename load-bearing).
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). Reselling
  API-Football data is the one hard prohibition.
