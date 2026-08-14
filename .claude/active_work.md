# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`; `wc -c` counts BYTES and
> over-reports by ~220 here, which will send you trimming content that fits.

_Last updated **2026-08-14**. **NOTHING IN FLIGHT — no open MRs**; main is **`10fa570`**. Merged
08-12→08-14: **#63**, **#33 items 9/14/15 + the completeness-gate fix**, **#65**, **#57**, **#367**
(the home page), **#62 step 1**. The product is **Matchday Pilot**; the repo is on **GITLAB**
(`glab`, MRs, `.gitlab-ci.yml`). GitHub is KEPT but dormant — its Actions run nothing and its 114
issues unreachable; `.github/workflows/README.md` re-arms it.
⚠ **CI WORKS AGAIN** — a self-hosted runner (`ci-runner-01`) serves this project, so jobs burn ZERO
GitLab minutes; the old "no minutes" note is dead. ⚠ **A GROUP MOVE IS COMING** and it changes the
project PATH — breaking remote URLs, the WIF binding pinned to `attribute.project_path`, and every
hardcoded `rami.al-fahham/football-data-pipeline`. Check before starting anything path-dependent._

## ⭐ CURRENT — #62 STEP 3 IS BLOCKED ON A MEASURED FACT (2026-08-14)

**#62 is the live thread, five steps.** Steps 1 (`!40` — the seed carries `confederation`, `slug`,
`sort_order`, `tier`, `season_type`; the guard compares EVERY column) and 2 (#57) are done. **Step 3
is `mart_competition_index`**, 4 repoints the export, 5 the page spec. ⚠ A seed COLUMN and its first
reader cannot ship together, so step 3 is its own MR.

⛔ **DO NOT START THE MART. `dim_league.league_country` IS EMPTY — measured, 45 rows, 0 country,
0 flag, 45 logo.** The columns exist and `stg_apif__leagues.sql:53` extracts them; every value is
NULL. ⚠ **This was MY premise for the #69 country ruling and it was false — I read the code, not
the data (#904).** So the region sub-line's rule (#54 note 3: `single_country: true` → country,
else the confederation label) has **no source for its first branch**: the registry copy is
deliberately unprojected and the warehouse copy is empty. The confederation branch is fine.
⚠ **The cheap next step is a LOOKUP, not a decision: find out WHY it is null** — provider payload,
or something between staging and the dim. That picks between fixing the ingestion, projecting the
registry field after all, or **#69**'s seed. The 2026-08-14 note on **#62** is the authority.

✅ **Also measured, correcting two earlier claims of mine:** ALL 45 competitions have fixtures
(FAC 4,381 → WCQIP 4) and ALL 45 have logos. So membership ("if it is ingested, it shows", CPO)
yields **45 rows**, and "33 of 45 have no logo" is struck. Registry `status` is useless here.

⛔ **HOME PAGE: THE DESIGN AUTHORITY IS #40 (players) AND #41 (teams), NOT `10_home.md` §0**, which
is wrong on both (it says nine and six boards, top 5; the truth is FOUR boards of ONE metric each,
top 7). #367 shipped next matches → browse only; Top players and Top teams are designed, NOT built,
and slot BETWEEN them. Follow-ups: **#36** (blocks #377) · **#38** · **#42** · **#43** · **#44** ·
**#45**.

⚠ **THE REBASE TAX, paperwork-only:** four rebases in one session, each conflicting ONLY in
`.claude/task/*`. **MINE** for contract/review/review_input; **UNION** `escalations.log` by
ARITHMETIC. ⚠ Not always `main + (mine − base)` — !27 inserted at the TOP too, so diff the opcodes
and refuse anything not a pure insertion. Then REBIND `diff_sha256`. ⚠ A False probe is not proof
of loss — chase it.
⚠ **NEVER restore uncommitted work with `git checkout --`** (in a probe, or after a failed
`checkout`): it restores from HEAD and wipes the edits. Snapshot bytes in-process; restore in a
`finally`. Bit me twice — once destroying two scripts, once a commit (recovered from the remote).

⚠ **DEFERRED ON PURPOSE by #57 — do not "fix":** `world_championship` keeps its name (branched on at
`int_team_momentum_window.sql:135` behind a `coalesce`, so renaming without the SQL edit silently
gives the World Cup a last-5 window, every test green) · `display_group` kept for **#44** ·
`confederations.csv` unread until **#62** step 3.

**#54 the competitions page is DESIGNED AND CLOSED** — its five notes supersede the description, and
note 4 is the mart's 16-column contract. Mocks are OUTSIDE the repo in `design-mocks/`;
`gen_competitions.py`'s `check_registry_still_unedited()` **fires by design now #57 merged** — drop
`continental_club` from `RENAMED_TYPES` and `CWC` from `RETYPED` first.

## ⭐ AN AUDIT FINDS; IT DOES NOT DECIDE

The audit and its cold re-run are in **GitLab #30**; the work list is on the tracker, not here.
Durable lesson: **findings replicate, prioritisation does not** — the cold run's first move was
deletion where the first run's was addition, so **an audit's output is LEADS TO VERIFY, never a
work list**. **Why mechanism beats wording (#30):** of 50 corrections, **33 were prose only, 22
recurred, and every rule that got a mechanism stopped.** Unmechanised: VERIFY, ESCALATE.

**⚠ OPERATIONAL NOTES LIVE IN `CLAUDE.md`** — dbt CLI, SQLFluff, commit mechanics, the stash-dance,
CWD/fnmatch/heredoc/grep traps. **Do not copy back**: that file is not capped._

**FIRST ACTION: `git stash list` before any git work.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX. The one
that must not be rebuilt contains **`feat/player-overview-tab: Overview BUILT`**._

## ⭐ The ingest cluster is CLOSED but UNVERIFIED

⛔ **THE 04:00 NIGHTLY IS FAILING AND MERGING `!39` DID NOT FIX IT.** The completeness gate treats a
DELIBERATE 7-day re-fetch skip (#33 item 14) as a stalled ingest and exits 3 before dbt runs. The fix
is merged, but **the nightly runs an IMAGE**: it needs `gcloud run jobs deploy fdp-nightly --source .
--region europe-west1` from main. ⚠ And there is still **no SCHEDULE** — manual dispatch only.
(`data:build:main` DID run 08-13, so prod itself is fresh; different job.)

⚠ **The lesson, which outlives the nightly:** item 14 passed four reviewers and nobody connected a
change in FETCH CADENCE to a gate assuming NIGHTLY FETCHES — its impact map traced dbt lineage but
not the OPERATIONAL checks on the same tables. **An impact map that stops at lineage misses gates.**

⚠ **None of the four ingest fixes does what its title suggests** — caveats on #896-#898. Ultra plan
**450/min, 75,000/day**, draw ~8,300, so the PER-MINUTE limit binds. **No public site, so no user
impact** — never present this as a live incident.

## ⭐ COST — read **GitLab issue #3** before touching anything

Everything recoverable from #547 (its GitHub comment is gone) is in **GitLab #3** — baselines, the
ranked list **in ITS order**, the free tools, MEASURED vs UNMEASURED. Read it; do not redo it.
⚠ **#70** adds a scan-budget guard there. Traps:

- **⚠ NEVER set a time-based partition expiry on raw** (#892). Nine biennial/quadrennial tournaments
  are `ingest_active` and go months without a refresh; expiry would delete the ONLY surviving row and
  staging's `qualify` would return zero rows for that league. Use keep-latest-per-`(table,
  league_code)`. **A fixed lookback window has the same defect.**
- **⚠ Do NOT claim the API quota "breaks first"** — claimed once without evidence, withdrawn; the
  number is not in the repo. (`standings.py:30` and `teams.py:28` DO loop every season daily with
  no skip — real, worth fixing.)
- **⭐ FREE: `bq query --dry_run`** (exact bytes, nothing runs) and **`report_bq_cost.py`**.
  ⚠ **Paste the output or do not claim it.**
- **MEASURED 08-03: $2.73/day**, prod tests $1.46 vs models $0.75. ⚠ PREDATES both fixes to its top
  item — staging is a TABLE now and `/injuries` is gone (#33 items 9/15). **Re-measure; never quote
  08-03 as current.**
- **⚠ #2 IS LIVE; it fired 08-07 and 08-13.** `data:build:main` triggers on `data_paths`, which
  includes `.gitlab-ci.yml` and `scripts/check_*.py`, so a governance-only MR rebuilds the whole prod
  warehouse — costly, though on 08-13 it is what un-staled prod. **Check `data_paths` first.**

## ⭐ REVIEW MECHANICS — what the working agreement does not give you

Rules are `docs/working_agreement.md` §2 (#878). Only the traps live here.

- **Build the patch with the hook, never by hand:**
  `python .claude/hooks/git_discipline.py --review-patch > .claude/task/review_input.patch`
  ⚠ It is `git diff --staged <base>`, so **`git add` FIRST or it comes out EMPTY**. `contract.md` +
  `escalations.log` ARE delivered (they carry authority); task notes are not. A trailer names any
  excluded file that IS edited (#25/!19), so absence is not evidence of untouched.
- **Run `check_task_artifacts.py` BARE** (#24, !15) — it resolves the live remote, as does the hook
  since **#63**; `GOVERNANCE_BASE` overrides both. `--staged-hash` is `git diff --raw` from the base
  and matches CI at any length. ⚠ On an UNCOMMITTED branch it prints "empty diff — OK": vacuous,
  not green.
- **A PASS may find nothing.** One `risks_checked:` entry is enough; never invent one. Cap is 3
  rounds, then STOP. ⚠ `rounds: 0` is REFUSED by the gate — you do not get to skip the cycle.
- **`.claude/task/**` is scope-exempt; `active_work.md` is NOT** — it must be in `scope_paths`, and
  a commit touching `contract.md` is **never** artifact-exempt.
- **The org does NOT change** (CPO ruling): low activation is not a defect; keep all reviewers.
- **⭐ A correction REPLACES, never accumulates, and must replace EVERYWHERE.** ⚠ Four occurrences
  on 08-14 cost five review rounds: corrected in one artifact, alive in another as a PARAPHRASE.
  **Sweep the CLASS semantically, not the phrase you wrote.** Mechanism: **#71**.

## Player page + the next CPO decision
**#846 + #886 merged:** the season a page opens on is a warehouse fact (`is_featured_season`, with a
DQ guard). **CPO: the pipeline picks, not the page**, scoped by the tab's LENS.

**#845 + #882 are ONE decision and his** — which entities earn a page, and whether a past season
gets a URL or a control. Deciding apart sets the URL shape twice. Measured (×3 locales): players
51,589→154,767; **matches are BIGGER at 176,235**; h2h 51,903; teams 9,669. A 5-match gate leaves
1,274 teams and 21,979 players. Bring counts, not a general question.

**The player Overview is BUILT but UNCOMMITTED** in the stash named above, with a known-wrong default
(`seasons[0]` = most recent of ANY competition, so both samples open on WC 2026). Its mart half IS
shipped — a one-line change when it resumes. Held on #845. **#848: the page is FOUR tabs**,
International a national-lens TAB not a toggle (a crawler cannot follow a control) — read it first,
four CPO-class consequences are open.

## DESIGN DISCIPLINE (the weak spot)
Never design off the cuff: approved wireframes + role briefs, never a block invented to fill a slot,
never the canonical page built around an edge case, ONE tab at a time. **Rendered output not prose;
copy is ALWAYS his (§10)** — gather copy decisions BEFORE the branch.

## OWED — deferred, not forgotten
- **Guard telemetry is absent** — 2,684 lines of enforcement, zero records of a gate firing (#30
  finding 4) — and **the round cap only RECORDS** a builder-typed number, so nothing stops a fourth
  round. Both unfixed. Also: delete `macros/apif_latest_source_partition.sql` · a metric-change
  skill · mirror the crests · reviewers as peers (#822 shipped the model half).
- **⭐ #904 IS THE DOMINANT FAILURE** — a claim about the code asserted rather than RUN. Three
  faces, all seen: a grep scoped narrower than the sentence it supported; a TEST that passes either
  way (#63 shipped three that passed against the very defect they targeted); and **reading a column
  in the model while never reading its VALUES** — the `dim_league` blocker above. **A claim of
  ABSENCE must state where it looked; a test must be seen RED first; a column is not data.**
  Prose has failed 8×; the mechanism is **#71**.

## NEXT
0. **⚠ DEPLOY THE NIGHTLY IMAGE** (⭐ block above) — !39's fix is merged but not live. Then: **no
   SCHEDULE exists**, so data refreshes only when a merge matches `.data_paths_prod`, which is how
   prod went stale for four days. Creating one is a recurring-COST decision, so the **CPO's**;
   bring a recipe. ⚠ **#4**: a web dispatch from ANY branch builds prod from THAT branch's code.
1. **#62: find out why `league_country` is NULL, THEN step 3** (⭐ CURRENT). Then step 4 repoints the
   export, step 5 the page spec. Then **#55** and **#69**.
2. **The audit stream — see the ⭐ block above.** ⚠ **Do NOT mix it with cost.** Also the CPO's, one
   command each: **Q2 of #21** (set `main`'s push access to No one — the SERVER should protect it,
   not a client hook; a branch cut from `gitlab/main` INHERITS that upstream, so always push an
   explicit refspec) · delete the 2 dead `~/.claude/hooks/` copies · route or delete
   `seo-expert-reviewer`.
3. **⭐ THEN COST, SYSTEMATICALLY.** The CPO's words: the whole pipeline **including CI/CD, what gets
   triggered, when, and where**. Trigger/cost map FIRST, rank by real spend, fix in that order; the
   map goes in a GitLab ISSUE, never a doc. `data_paths` (#2) ranks ~4th.
4. **#845 + #882 — the CPO's decision.** Counts are measured and in this file: bring them, not a
   general question. Unblocks the player page off the stash.
5. First green nightly · **then legal/imprint**, then launch.
6. Follow-ups — GITHUB numbers, **bodies UNREACHABLE**; re-derive from code, re-file as picked up.
   **#875** metric GROUP headings English on DE/FI · **#877** `GD`, `W/D/L`, `T·I·B` need DE/FI ·
   **#876** rows break mid-word · **#863** PROTECTED path editable with no `protected_override` ·
   **#866** `Regular Season - 20` is provider text the copy gate cannot see · **#887** MR-time DQ
   cannot see its own models · **#883** blank `competition_type` skipped by all 3 guards.
7. Mine to build, on GitLab: **#64** #63's residuals · **#67** the contract gate enforces on the Edit
   tool only, so `sed -i` bypasses it · **#68** the form-window CODE diverges from
   `metrics_context_model.md` §4 in 2 places (⚠ **the agreement is the authority**; never fix it by
   editing the doc) · **#60** the canonical clone sits on a feature branch, so `.venv` is not where
   `CLAUDE.md` implies · **#69** countries · **#70** scan-budget guard.

## OPEN — the CPO's alone
**Imprint operator + address** (#799), blocks publication, never conclude it · hosting recurring run
· the feedback Apps Script (#687) · **#850**'s alias decision · **#875** where a group name lives ·
**#895 slim-vs-drop, blocking the biggest cost item** · **#21** · **#69**'s canonical country names.

## DO NOT (standing)
- Do NOT treat the tracker as agreed work; re-validate. No new planning docs.
- Do NOT touch `site/` (retired). Do NOT derive facts in the export or frontend.
- **Never merge an MR. The CPO merges. Branch from main; never commit to main.**
- Plain language, lead with the decision, **no em dashes**, no walls of text.
- Do NOT ask him to adjudicate what a rule settles. **But copy is ALWAYS his (§10).**
- Do NOT bring him a fix for a defect he never asked about; fix it and move on.

## Verified state reference
- **No PUBLIC site.** v2 is unlisted, every page `noindex` — why URLs are still free.
- **v2 built:** design system + 26 components, fixture page, team page (3 tabs), **the home page
  (next matches → browse)**, page-spec + SEO contract (#826/#844), per-locale metric labels.
- **Tests: 814 passed + 1 skipped python** (~7 min, measured 08-14 on main), plus 59 site
  (`cd site_v2 && npm test`). ⚠ MEASURE, never predict (#904) — this was 665 two weeks ago.
- **`ruff` runs in CI** as `lint:python` (!20), config **`.ruff-ci.toml`** — the filename is
  load-bearing; `tests/test_lint_config.py` pins it.
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). Reselling
  API-Football data is the one hard prohibition.
