# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES, ~220
> over, which sends you trimming content that fits).

_Last updated **2026-08-16**. **ONE MR OPEN: `!53`** (#73 — stops `data:build:mr` bootstrap-
ingesting, which wrote PROD raw from an unmerged branch; closes #33 item 13 for the MR path).
`!50` merged (#72 BPL/TSL/EKS; women's dropped/CPO). main `53b6a51`. Product **Matchday Pilot**;
repo on **GITLAB** (`glab`, MRs, `.gitlab-ci.yml`). GitHub KEPT but dormant. Self-hosted runner
`ci-runner-01`; jobs burn ZERO GitLab minutes. ⚠ **A GROUP MOVE IS COMING** and it changes the
project PATH — breaking remote URLs, the WIF binding pinned to `attribute.project_path`, and every
hardcoded `rami.al-fahham/football-data-pipeline`. Check before anything path-dependent._

## ⭐ ONBOARDING MRs GO RED ON `data:build:mr`. CORRECT. DO NOT "FIX" IT (2026-08-16)
FOUR `*_covers_active_competition_var` tests fail on an onboarding MR: the MR adds the code, `!53`
stops the MR job ingesting, so rows cannot exist until post-merge. **They state a true fact.**
Merge on judgement, as `!50` was. ⛔ Silencing them with a tag+exclude WAS BUILT, failed by all four
reviewers as a coverage cut, and ruled a hack — see the `dbt test` step of `data:build:mr` and
`escalations.log`. ⭐ CAUSE = **#76**: nothing records a league HAS been ingested, only that it SHOULD.

## ⭐ CURRENT — #62 STEP 3 IS BLOCKED ON #69'S DIMENSIONS. DO NOT BUILD THE MART (2026-08-16)

**#62, five steps.** 1 (`!40`) and 2 (#57) done. **3 is `mart_competition_index`**, 4 repoints the
export, 5 the page spec. ⚠ A seed COLUMN and its first reader cannot ship together — 3 is its own MR.

⛔ **THE MART IS WRITTEN AND PARKED** — `git stash list`, message `feat/62-mart-competition-index:
mart + confederations region_rank; region_label BLOCKED on #69`. Match by MESSAGE. `region_label`
is the blocker: COUNTRY and CONTINENT in one column, branching on `single_country`. **CPO: *"You
don't mix up countries and continents or regions in one column and add a flag 'single country'.
That's really bad modeling."*** ⚠ Nothing ever read that flag (`seeds/schema.yml:99` says so).
⛔ **#69 IS RESCOPED to TWO dimensions** (its 08-16 note is the authority): `dim_region` from
`confederations.csv` (**exists, 7 rows, read by nothing**) + `dim_country` built new. A competition
POINTS AT one; **which relationship is populated IS the answer** — no flag, no branch. The
registry's `country` mixes 21 countries with 24 region words; those 24 become NULL. Deletes
`single_country`. ✅ **DISCOVERY COMPLETE (08-16 notes on #69).** 285 values; the defect is ONE
endpoint: `/teams` hyphenates 37 countries that `/players`/`/coachs` spell with spaces.
⛔ **`!45` made `USA` WORSE:** leagues now read `United States of America`, the other three still
`USA` (28/816/45), so `countries.csv` must map it for EVERY surface. `World` is league-only (24)
and never becomes a country row. **NEXT: canonical names, HIS.**

✅ **`!43` + `!45` LIVE IN PROD.** ⚠ `sync_dbt_vars.py:45` is now accurate — do not "fix" it.
⚠ **Never normalise country names by regex** — `Guinea-Bissau`/`Timor-Leste` are correctly
hyphenated, now MEASURED (#69). **The transformation layer decides the FORM, the CPO the NAME.**

⛔ **`sort_order` IS OBSOLETE (CPO 2026-08-16)**; the mart must not read it. **The full rule is the
08-16 ordering note on #54 — read it, do not reconstruct it.** ⚠ **Mart carries FACTS, the spec
declares the ORDER BY** — sorting is arrangement, not a fact. ⚠ Retiring it reaches past #54 into
`export_site_data.py`, `BrowseGrid.astro`, `landing.json` — NOT scoped yet.

✅ **Membership is 45 rows** — all have fixtures and logos; registry `status` useless here.

⛔ **HOME PAGE: authority is #40 + #41, NOT `10_home.md` §0** (it says nine/six boards top 5; truth
is FOUR boards of ONE metric, top 7). #367 shipped next matches → browse; Top players/teams designed
NOT built, slot BETWEEN. Follow-ups **#36** (blocks #377) · **#38** · **#42**–**#45**.

⚠ **DEFERRED by #57 — do not "fix":** `world_championship` keeps its name (branched on at
`int_team_momentum_window.sql:135`; renaming without that SQL edit silently gives the World Cup a
last-5 window, every test green) · `display_group` kept for **#44**.

**#54 competitions page: DESIGNED AND CLOSED** — its five notes supersede the description; read
them, do not reconstruct. ⚠ **Its 16 is ELEMENTS, not mart columns** ("16-column contract" is
WRONG). Mocks are OUTSIDE the repo in `design-mocks/`.

## ⭐ AN AUDIT FINDS; IT DOES NOT DECIDE
Audit + cold re-run in **GitLab #30**. **Findings replicate, prioritisation does not** — output is
LEADS TO VERIFY, never a work list. **Mechanism beats wording:** of 50 corrections, **33 prose-only,
22 recurred, every rule that got a mechanism stopped.**
**⚠ OPERATIONAL NOTES LIVE IN `CLAUDE.md`** — dbt CLI, SQLFluff, commit mechanics, the stash-dance,
CWD/fnmatch/heredoc/grep traps. **Do not copy back**: that file is not capped.
**FIRST ACTION: `git stash list` before any git work.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX. TWO
must not be rebuilt: **`feat/player-overview-tab: Overview BUILT`** and the **#62 mart** (⭐ above)._

## ⭐ The ingest cluster
✅ **PROD IS CURRENT as of 08-16 13:40 UTC** — `dim_league` reads **45/45 country, 21/21 flag**
(`Saudi Arabia · South Korea · United States of America · World ×24`). **TWO nightlies:** GitLab CI
`data:nightly` moved to **Cloud Run under #39**, so its GitLab schedule (id 4379625) is **paused ON
PURPOSE — do not re-enable.** Runbook `deploy/nightly/README.md`.
⛔ **#74 — THE IMAGE NEVER TRACKED `main`.** `gcloud run jobs deploy --source .` packages the
working tree and nothing redeploys it (no trigger, no CI job — verified). It ran 08-14 code for two
days and **rebuilt prod nightly from it, REVERTING `!43`/`!45`**. Redeployed by hand 08-16; **stale
again on the next merge.**
⛔ **#75 — red nights are DATA QUALITY.** 08-16 failed on ONE orphan row (`player_sk` 544602, CIT),
skipping **103 nodes**; 08-12 on another fixture-event test, **540**. The skip is the gate working.
⚠ **A GREEN EXECUTION PROVES NOTHING** — it says the container ran, not which code. **Check DATA.**
⚠ **Lesson, in memory: an impact map that stops at LINEAGE misses GATES** (#33 item 14).
⚠ **None of the four ingest fixes does what its title suggests** — caveats on #896-#898. Ultra plan
**450/min, 75,000/day**, draw ~8,300, so the PER-MINUTE limit binds.

## ⭐ COST — read **GitLab issue #3** before touching anything
**#3 holds it all** — baselines, the ranked list **in ITS order**, the free tools (`bq query
--dry_run`, `report_bq_cost.py`; ⚠ **paste the output or do not claim it**), the traps (**never a
time-based partition expiry on raw**, #892 — nine biennial tournaments would lose their only row;
a fixed lookback is the same defect). Read it; do not redo it. ⚠ **#70** is the scan-budget guard,
and #3's item 6 records that `require_partition_filter` + `maximum_bytes_billed` are **NEITHER
set** — nothing bounds a runaway query today.

- **⚠ STORAGE WAS NEVER MEASURED** (08-16; "storage" appears **0×** in #3). Every figure there is
  bytes SCANNED, and storage only grows with a nightly-snapshot ingest. `region-eu…TABLE_STORAGE`
  is Access Denied here; per-table `bq show` works and is free.
- **⚠ Do NOT claim the API quota "breaks first"** — claimed once without evidence, withdrawn.
  (`standings.py:30` / `teams.py:28` DO loop every season daily with no skip — real, worth fixing.)
- **MEASURED 08-03: $2.73/day**, prod tests $1.46 vs models $0.75. ⚠ PREDATES both fixes to its top
  item (#33 items 9/15). **Re-measure; never quote it as current.**
- **⚠ #2 IS LIVE** (fired 08-07, 08-13). `data:build:main` triggers on `data_paths`, which includes
  `.gitlab-ci.yml` and `scripts/check_*.py`, so a governance-only MR rebuilds all of prod.

## ⭐ REVIEW MECHANICS — what the working agreement does not give you
Rules are `docs/working_agreement.md` §2 (#878). Only the traps live here.
- **Build the patch with the hook, never by hand:**
  `python .claude/hooks/git_discipline.py --review-patch > .claude/task/review_input.patch`
  ⚠ It is `git diff --staged <base>`, so **`git add` FIRST or it comes out EMPTY**. `contract.md` +
  `escalations.log` ARE delivered; task notes are not. A trailer names any excluded file that IS
  edited (#25), so absence is not evidence of untouched. ⚠ **`review.md` must be `git add`ed too**
  — writing it is not committing it (cost a red CI on !50).
- **Run `check_task_artifacts.py` BARE** (#24, !15) — it resolves the live remote, as does the hook
  since **#63**; `GOVERNANCE_BASE` overrides both. `--staged-hash` matches CI at any length.
- **A PASS may find nothing.** One `risks_checked:` entry is enough; never invent one. Cap 3 rounds
  then STOP. ⚠ `rounds: 0` is REFUSED.
- **`.claude/task/**` is scope-exempt; `active_work.md` is NOT** — it must be in `scope_paths`, and
  a commit touching `contract.md` is **never** artifact-exempt.
- ⚠ **REBASE TAX:** conflicts land in `.claude/task/*` **and `active_work.md`** — **MINE** for
  contract/review, **UNION** `escalations.log` by ARITHMETIC, then REBIND `diff_sha256`. When main
  has moved a lot, take **THEIRS** wholesale and re-apply your delta. ⚠ **`git rebase` replays
  commits IN ORDER**, so a scope amendment committed LAST does not apply to an earlier commit's
  conflict — **`git merge` applies the tip at once, use it** (08-16). ⚠ **NEVER `git checkout --`
  to restore uncommitted work** — it restores from HEAD and wipes it.
- **⭐ A correction REPLACES, never accumulates, and must replace EVERYWHERE.** ⚠ 08-14: four
  occurrences cost five rounds — fixed in one artifact, alive in another as a PARAPHRASE. **Sweep
  the CLASS semantically, not the phrase you wrote.** Mechanism: **#71**.

## Player page — HELD on #845
**#846 + #886 merged:** the season a page opens on is a warehouse fact (`is_featured_season`, DQ
guarded). **CPO: the pipeline picks, not the page**, by the tab's LENS.
**#845 + #882 are ONE decision and his** — which entities earn a page, and whether a past season
gets a URL or a control; deciding apart sets the URL shape twice. Measured (×3 locales): players
51,589→154,767; **matches BIGGER at 176,235**; h2h 51,903; teams 9,669; a 5-match gate leaves
1,274 teams / 21,979 players. **Bring the counts.**
**Overview is BUILT but UNCOMMITTED** in stash `feat/player-overview-tab: Overview BUILT` (⚠ NOT
the #62 mart stash); default is known-wrong (`seasons[0]` = most recent of ANY competition, so both
samples open on WC 2026), mart half IS shipped, one line on resume. **#848: FOUR tabs**,
International a national-lens TAB not a toggle (a crawler cannot follow a control).

## OWED — deferred
- **Guard telemetry is absent** (#30 finding 4) — 2,684 lines of enforcement, zero records of a
  gate firing; the round cap only RECORDS a typed number. Also: delete
  `macros/apif_latest_source_partition.sql` · metric-change skill · mirror crests.
- **⭐ #904 IS THE DOMINANT FAILURE** — a claim asserted rather than RUN. Faces seen: a grep scoped
  narrower than its sentence; a TEST that passes either way (#63 shipped three); **a column read
  without its VALUES** (`!43`); **a number repeated out of this file** (`!47`); **a JOB STATUS read
  instead of the data** (`!49`); **08-16, four in one task** (insecure option filed, "only 1 test"
  when 4 were, a CPO call taken alone, his nightly described unchecked). **Absence must state where
  it looked; a test must be seen RED; a column is not data; green is not evidence; grep for SIBLINGS
  before writing "only one".** Prose has failed 8×; mechanism is **#71**.

## NEXT
0. **MERGE `!53`** (#73, reviewed round 2, all PASS). Then **the nightly's two REAL defects, both
   filed** (⭐ above): **#74** the image does not track `main` — redeployed 08-16 but stale on the
   next merge, so prod silently reverts. **#75** fixture-event integrity turns it red and skips
   103–540 nodes. ⚠ **#4**: a web dispatch from ANY branch builds prod from THAT branch's code.
1. **#69 FIRST, then #62 step 3** (⭐ CURRENT). Discovery COMPLETE; next is **canonical names to the
   CPO**, then the two dims. Then step 4 repoints the export, 5 the page spec.
2. **The audit stream (⭐ above).** The CPO's, one command each: **Q2 of #21** (`main` push access
   to No one — the SERVER should protect it, not a client hook) · delete the 2 dead
   `~/.claude/hooks/` copies · route or delete `seo-expert-reviewer`.
3. **⭐ THEN COST, SYSTEMATICALLY** — the whole pipeline **including CI/CD, what gets triggered,
   when, where** (CPO). Trigger/cost map FIRST, rank by real spend, fix in that order; the map goes
   in a GitLab ISSUE, not a doc. `data_paths` (#2) and the unmeasured STORAGE line belong in it.
4. **#845 + #882 — the CPO's decision.** Counts are in this file: bring them, not a general
   question. Unblocks the player page off the stash.
5. **Legal/imprint**, then launch. (The "first green nightly" gate is MET — 08-15 and 08-16.)
6. Follow-ups (GITHUB numbers, **bodies UNREACHABLE** — re-derive from code): DE/FI i18n gaps
   (metric group headings, `GD`/`W/D/L`/`T·I·B`, rows breaking mid-word) · PROTECTED path editable
   with no `protected_override` · `Regular Season - 20` provider text the copy gate cannot see ·
   MR-time DQ cannot see its own models · blank `competition_type` skipped by all 3 guards.
7. Mine, on GitLab: **#64** #63's residuals · **#67** the contract gate enforces on the Edit tool
   only, so `sed -i` bypasses it · **#68** the form-window CODE diverges from
   `metrics_context_model.md` §4 in 2 places (⚠ **the agreement is the authority**; never fix it by
   editing the doc) · **#60** `.venv` is not where `CLAUDE.md` implies · **#70** scan-budget guard.

## OPEN — the CPO's alone
**Imprint operator + address** (#799), blocks publication, never conclude it · hosting recurring
run · feedback Apps Script (#687) · **#850** alias · **#875** where a group name lives · **#895
slim-vs-drop, blocking the biggest cost item** · **#21** · **#69** canonical country names.

## DO NOT (standing)
- **DESIGN, the weak spot:** never off the cuff — approved wireframes + role briefs, no block
  invented to fill a slot, never the canonical page built on an edge case, ONE tab at a time.
  Rendered output not prose; gather copy decisions BEFORE the branch.
- Do NOT treat the tracker as agreed work; re-validate. **No new planning docs, no fresh audits**
  (#30 already ran; it returns our own built work as findings). Do NOT touch `site/` (retired).
  Do NOT derive facts in the export or frontend.
- ⛔ **VERIFY BEFORE ASSERTING.** Run the grep, read the file, then speak.
- **Never merge an MR. The CPO merges. Branch from main; never commit to main.**
- Plain language, lead with the decision, **no em dashes**, no walls of text.
- Do NOT ask him to adjudicate what a rule settles. **But copy is ALWAYS his (§10).**
- Do NOT bring him a fix for a defect he never asked about; fix it and move on.

## Verified state reference
- **No PUBLIC site.** v2 unlisted, every page `noindex` — why URLs are still free.
- **v2 built:** design system + 26 components, fixture page, team page (3 tabs), home page (next
  matches → browse), page-spec + SEO contract (#826/#844), per-locale metric labels.
- **Tests: 814 python + 1 skipped** (08-14 on main), 59 site, **1004 dbt in prod**. ⚠ MEASURE,
  never predict (#904) — python was 665 two weeks ago.
- **`ruff` runs in CI** as `lint:python` (!20), config **`.ruff-ci.toml`** — filename load-bearing,
  pinned by `tests/test_lint_config.py`.
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). Reselling
  API-Football data is the one hard prohibition.
