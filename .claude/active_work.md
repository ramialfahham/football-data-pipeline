# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES, ~220
> over, which sends you trimming content that fits).

_Last updated **2026-08-16**. **NOTHING IN FLIGHT** — `!50` merged (#72 BPL/TSL/EKS; women's
dropped/CPO); `data:build:mr` RED BY DESIGN, see **#73**. main `3c8492b` — see `git log` for what
merged, this file no longer enumerates it. Product **Matchday Pilot**; repo on **GITLAB**
(`glab`, MRs, `.gitlab-ci.yml`). GitHub KEPT but dormant — Actions run nothing, its 114 issues
unreachable.
⚠ **CI WORKS AGAIN** — a self-hosted runner (`ci-runner-01`) serves this project, so jobs burn ZERO
GitLab minutes. ⚠ **A GROUP MOVE IS COMING** and it changes the
project PATH — breaking remote URLs, the WIF binding pinned to `attribute.project_path`, and every
hardcoded `rami.al-fahham/football-data-pipeline`. Check before starting anything path-dependent._

## ⭐ CURRENT — #62 STEP 3 IS BLOCKED ON #69'S DIMENSIONS. DO NOT BUILD THE MART (2026-08-16)

**#62, five steps.** 1 (`!40`) and 2 (#57) done. **3 is `mart_competition_index`**, 4 repoints the
export, 5 the page spec. ⚠ A seed COLUMN and its first reader cannot ship together, so 3 is its own
MR.

⛔ **THE MART IS WRITTEN AND PARKED** — `git stash list`, message `feat/62-mart-competition-index:
mart + confederations region_rank; region_label BLOCKED on #69`. Match by MESSAGE. `region_label` is
the blocker: it puts a COUNTRY and a CONTINENT in one column and branches on
`competition_types.single_country`. **CPO: *"You don't mix up countries and continents or regions in
one column and add a flag 'single country'. That's really bad modeling."*** ⚠ Nothing ever read that
flag (`seeds/schema.yml:99` says so itself).
⛔ **#69 IS RESCOPED to TWO dimensions** (its 08-16 note is the authority): `dim_region` from
`confederations.csv` (**exists, 7 rows, read by nothing**) + `dim_country` built new. A competition
POINTS AT one; **which relationship is populated IS the answer** — no flag, no branch. Cost: the
registry's `country` mixes 21 countries with 24 region words; those 24 become NULL. Deletes
`single_country`. ✅ **DISCOVERY COMPLETE — the 08-16 notes on #69.** 285 values; the defect is ONE
endpoint: `/teams` hyphenates 37 countries that `/players`/`/coachs` spell with spaces.
⛔ **`!45` made `USA` WORSE:** leagues now read `United States of America`, the other three still
`USA` (28/816/45), so `countries.csv` must map it for EVERY surface. `World` is league-only (24)
and never becomes a country row. **NEXT: canonical names, HIS.**

✅ **`!43` + `!45` LIVE IN PROD.** ⚠ `sync_dbt_vars.py:45` is now accurate — do not "fix" it.
⚠ **Never normalise country names by regex** — `Guinea-Bissau`/`Timor-Leste` are correctly
hyphenated, now MEASURED (#69 note). **The transformation layer decides the FORM, the CPO the
NAME.**

⛔ **`sort_order` IS OBSOLETE (CPO 2026-08-16)**; the mart must not read it. **The full rule is the
08-16 ordering note on #54 — read it, do not reconstruct it.** In one line: has-upcoming-fixture →
days to next kickoff **BUCKETED BY DAY** → **region_rank** (UEFA 1 · FIFA 2 · CONMEBOL 3 · CONCACAF
4 · AFC 5 · CAF 6 · OFC 7, HIS judgement, on `confederations.csv`) → kickoff time → `league_code`;
nothing upcoming last, most-recently-played first. ⚠ **Mart carries FACTS, the spec declares the
ORDER BY** — sorting is arrangement, not a fact. ⚠ Retiring `sort_order` reaches past #54 into
`export_site_data.py`, `BrowseGrid.astro`, `landing.json` (#44, #367) — NOT scoped yet.

✅ **Membership is 45 rows** — all have fixtures and logos; registry `status` useless here.

⛔ **HOME PAGE: authority is #40 + #41, NOT `10_home.md` §0** (it says nine/six boards top 5; truth
is FOUR boards of ONE metric, top 7). #367 shipped next matches → browse; Top players/teams designed
NOT built, slot BETWEEN. Follow-ups **#36** (blocks #377) · **#38** · **#42**–**#45**.

⚠ **REBASE TAX:** conflicts land ONLY in `.claude/task/*` — **MINE** for contract/review, **UNION**
`escalations.log` by ARITHMETIC (not always `main + (mine − base)`), then REBIND `diff_sha256`.
⚠ **NEVER `git checkout --` to restore uncommitted work** — it restores from HEAD and wipes it.

⚠ **DEFERRED by #57 — do not "fix":** `world_championship` keeps its name (branched on at
`int_team_momentum_window.sql:135` behind a `coalesce`; renaming without the SQL edit silently gives
the World Cup a last-5 window, every test green) · `display_group` kept for **#44**.

**#54 the competitions page is DESIGNED AND CLOSED** — five notes supersede the description; note 4
is the provenance table. ⚠ **Its 16 is ELEMENTS, not mart columns** ("16-column contract" is WRONG)
— ~9 data columns + `league_code`, the rest **i18n chrome** that must NOT become columns; see its
08-15 note. Mocks are OUTSIDE the repo in `design-mocks/`; `gen_competitions.py`'s
`check_registry_still_unedited()` fires by design now #57 merged — drop `continental_club` from
`RENAMED_TYPES`, `CWC` from `RETYPED` first.

## ⭐ AN AUDIT FINDS; IT DOES NOT DECIDE
Audit + cold re-run in **GitLab #30**. **Findings replicate, prioritisation does not** — output is
LEADS TO VERIFY, never a work list. **Mechanism beats wording:** of 50 corrections, **33 prose-only,
22 recurred, every rule that got a mechanism stopped.**
**⚠ OPERATIONAL NOTES LIVE IN `CLAUDE.md`** — dbt CLI, SQLFluff, commit mechanics, the stash-dance,
CWD/fnmatch/heredoc/grep traps. **Do not copy back**: that file is not capped._

**FIRST ACTION: `git stash list` before any git work.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX. TWO
must not be rebuilt: **`feat/player-overview-tab: Overview BUILT`** and the **#62 mart** (⭐ above)._

## ⭐ The ingest cluster
✅ **PROD IS CURRENT as of 08-16 13:40 UTC** — `dim_league` reads **45/45 country, 21/21 flag**
(`Saudi Arabia · South Korea · United States of America · World ×24`). **TWO nightlies:** GitLab CI
`data:nightly` moved to **Cloud Run under #39**, so its GitLab schedule (id 4379625) is **paused ON
PURPOSE — do not re-enable.** Runbook `deploy/nightly/README.md`.
⛔ **#74 — THE IMAGE NEVER TRACKED `main`.** `gcloud run jobs deploy --source .` packages the
working tree and nothing redeploys it (no trigger, no CI job — verified). It ran 08-14 code for two
days and **rebuilt prod nightly from it, REVERTING `!43`/`!45`** after `data:build:main` had written
them correctly. Redeployed by hand 08-16; **stale again on the next merge.**
⛔ **#75 — red nights are DATA QUALITY.** 08-16 failed on ONE orphan row (`player_sk` 544602, CIT),
skipping **103 nodes**; 08-12 on another fixture-event test, **540**. The skip is the gate working.
⚠ **A GREEN EXECUTION PROVES NOTHING** — it says the container ran, not which code. **Check DATA.**
⚠ **Lesson, in memory: an impact map that stops at LINEAGE misses GATES** (#33 item 14).
⚠ **None of the four ingest fixes does what its title suggests** — caveats on #896-#898. Ultra plan
**450/min, 75,000/day**, draw ~8,300, so the PER-MINUTE limit binds.

## ⭐ COST — read **GitLab issue #3** before touching anything
Everything recoverable from #547 is in **GitLab #3** — baselines, the ranked list **in ITS order**,
the free tools, MEASURED vs UNMEASURED. Read it; do not redo it. ⚠ **#70** adds a scan-budget
guard. Traps:

- **⚠ NEVER set a time-based partition expiry on raw** (#892). Nine biennial/quadrennial tournaments
  go months without a refresh; expiry would delete the ONLY surviving row and staging's `qualify`
  would return zero. Use keep-latest-per-`(table, league_code)`. **A fixed lookback window is the
  same defect.**
- **⚠ Do NOT claim the API quota "breaks first"** — claimed once without evidence, withdrawn.
  (`standings.py:30` and `teams.py:28` DO loop every season daily with no skip — real, worth fixing.)
- **⭐ FREE: `bq query --dry_run`** (exact bytes, nothing runs) and **`report_bq_cost.py`**.
  ⚠ **Paste the output or do not claim it.**
- **MEASURED 08-03: $2.73/day**, prod tests $1.46 vs models $0.75. ⚠ PREDATES both fixes to its top
  item (#33 items 9/15). **Re-measure; never quote it as current.**
- **⚠ #2 IS LIVE** (fired 08-07, 08-13). `data:build:main` triggers on `data_paths`, which includes
  `.gitlab-ci.yml` and `scripts/check_*.py`, so a governance-only MR rebuilds all of prod.
  **Check `data_paths` first.**

## ⭐ REVIEW MECHANICS — what the working agreement does not give you
Rules are `docs/working_agreement.md` §2 (#878). Only the traps live here.
- **Build the patch with the hook, never by hand:**
  `python .claude/hooks/git_discipline.py --review-patch > .claude/task/review_input.patch`
  ⚠ It is `git diff --staged <base>`, so **`git add` FIRST or it comes out EMPTY**. `contract.md` +
  `escalations.log` ARE delivered; task notes are not. A trailer names any excluded file that IS
  edited (#25), so absence is not evidence of untouched.
- **Run `check_task_artifacts.py` BARE** (#24, !15) — it resolves the live remote, as does the hook
  since **#63**; `GOVERNANCE_BASE` overrides both. `--staged-hash` matches CI at any length. ⚠ On an
  UNCOMMITTED branch it prints "empty diff — OK": vacuous, not green.
- **A PASS may find nothing.** One `risks_checked:` entry is enough; never invent one. Cap is 3
  rounds then STOP. ⚠ `rounds: 0` is REFUSED — you do not get to skip the cycle.
- **`.claude/task/**` is scope-exempt; `active_work.md` is NOT** — it must be in `scope_paths`, and
  a commit touching `contract.md` is **never** artifact-exempt.
- **The org does NOT change** (CPO): low activation is not a defect.
- **⭐ A correction REPLACES, never accumulates, and must replace EVERYWHERE.** ⚠ Four occurrences
  on 08-14 cost five review rounds — corrected in one artifact, alive in another as a PARAPHRASE.
  **Sweep the CLASS semantically, not the phrase you wrote.** Mechanism: **#71**.

## Player page + the next CPO decision
**#846 + #886 merged:** the season a page opens on is a warehouse fact (`is_featured_season`, DQ
guarded). **CPO: the pipeline picks, not the page**, by the tab's LENS.

**#845 + #882 are ONE decision and his** — which entities earn a page, and whether a past season
gets a URL or a control. Deciding apart sets the URL shape twice. Measured (×3 locales): players
51,589→154,767; **matches BIGGER at 176,235**; h2h 51,903; teams 9,669. A 5-match gate leaves 1,274
teams and 21,979 players. Bring counts, not a question.

**The player Overview is BUILT but UNCOMMITTED** in the stash `feat/player-overview-tab: Overview
BUILT` (⚠ NOT the #62 mart stash), with a known-wrong default (`seasons[0]` = most recent of ANY
competition, so both samples open on WC 2026). Mart half IS shipped — a one-line change on resume.
Held on #845. **#848: FOUR tabs**, International a national-lens TAB not a toggle (a crawler cannot
follow a control); four CPO-class consequences open.

## OWED — deferred
- **Guard telemetry is absent** — 2,684 lines of enforcement, zero records of a gate firing (#30
  finding 4); **the round cap only RECORDS** a typed number. Both unfixed. Also: delete
  `macros/apif_latest_source_partition.sql` · metric-change skill · mirror crests · reviewers as
  peers.
- **⭐ #904 IS THE DOMINANT FAILURE** — a claim asserted rather than RUN. Faces all seen: a grep
  scoped narrower than its sentence; a TEST that passes either way (#63 shipped three); **a column
  read without its VALUES** (`!43`); **a number repeated out of this file** (`!47`); and **a JOB
  STATUS read instead of the data** (`!49`, which declared the nightly fine while it ran two-day-old
  code). **Absence must state where it looked; a test must be seen RED; a column is not data; green
  is not evidence.** Prose has failed 8×; the mechanism is **#71**.

## NEXT
0. **THE NIGHTLY: two REAL defects, both filed** (⭐ above). **#74** the image does not track `main`
   — redeployed 08-16 but it goes stale on the next merge, so prod silently reverts. **#75**
   fixture-event integrity turns it red and skips 103–540 nodes. ⚠ **#4**: a web dispatch from ANY
   branch builds prod from THAT branch's code.
1. **#69 FIRST, then #62 step 3** (⭐ CURRENT). Discovery COMPLETE; next is **canonical names to the
   CPO**, then the two dims. Then step 4 repoints the export, 5 the page spec.
2. **The audit stream (⭐ above).** ⚠ Do NOT mix with cost. The CPO's, one command each: **Q2 of
   #21** (set `main`'s push access to No one — the SERVER should protect it, not a client hook;
   ⚠ a branch cut from `gitlab/main` INHERITS that upstream, so unset it) · delete the 2 dead
   `~/.claude/hooks/` copies · route or delete `seo-expert-reviewer`.
3. **⭐ THEN COST, SYSTEMATICALLY** — the whole pipeline **including CI/CD, what gets triggered,
   when, where** (CPO). Trigger/cost map FIRST, rank by real spend, fix in that order; the map goes
   in a GitLab ISSUE, not a doc. `data_paths` (#2) ranks ~4th.
4. **#845 + #882 — the CPO's decision.** Counts are in this file: bring them, not a general
   question. Unblocks the player page off the stash.
5. **Legal/imprint**, then launch. (The "first green nightly" gate is MET — 08-15 and 08-16.)
6. Follow-ups — GITHUB numbers, **bodies UNREACHABLE**; re-derive from code, re-file when picked up.
   **#875** metric GROUP headings English on DE/FI · **#877** `GD`, `W/D/L`, `T·I·B` need DE/FI ·
   **#876** rows break mid-word · **#863** PROTECTED path editable with no `protected_override` ·
   **#866** `Regular Season - 20` is provider text the copy gate cannot see · **#887** MR-time DQ
   cannot see its own models · **#883** blank `competition_type` skipped by all 3 guards.
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
- Do NOT treat the tracker as agreed work; re-validate. No new planning docs. Do NOT touch `site/`
  (retired). Do NOT derive facts in the export or frontend.
- **Never merge an MR. The CPO merges. Branch from main; never commit to main.**
- Plain language, lead with the decision, **no em dashes**, no walls of text.
- Do NOT ask him to adjudicate what a rule settles. **But copy is ALWAYS his (§10).**
- Do NOT bring him a fix for a defect he never asked about; fix it and move on.

## Verified state reference
- **No PUBLIC site.** v2 unlisted, every page `noindex` — why URLs are still free.
- **v2 built:** design system + 26 components, fixture page, team page (3 tabs), **home page (next
  matches → browse)**, page-spec + SEO contract (#826/#844), per-locale metric labels.
- **Tests: 814 python + 1 skipped** (08-14 on main), 59 site, **1004 dbt in prod**. ⚠ MEASURE,
  never predict (#904) — python was 665 two weeks ago.
- **`ruff` runs in CI** as `lint:python` (!20), config **`.ruff-ci.toml`** — filename load-bearing,
  pinned by `tests/test_lint_config.py`.
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). Reselling
  API-Football data is the one hard prohibition.
