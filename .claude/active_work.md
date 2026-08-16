# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES, ~220
> over, which sends you trimming content that fits).

_Last updated **2026-08-16**. **MR #50 OPEN** (#72 BPL/TSL/EKS; women's dropped/CPO);
`data:build:mr` RED BY DESIGN, left as-is, see **#73**. main `1c4199f`. Merged 08-12→08-16:
**#63**, **#33 items 9/14/15 + the completeness-gate fix**, **#65**, **#57**, **#367**, **#62 step
1**, **`!43`** `!45` `!46` `!47`. Product **Matchday Pilot**; repo on **GITLAB** (`glab`, MRs,
`.gitlab-ci.yml`). GitHub KEPT but dormant — Actions run nothing, its 114 issues unreachable.
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
one column and add a flag 'single country'. That's really bad modeling."*** ⚠ Nothing has ever read
that flag (`seeds/schema.yml:99` says so itself).
⛔ **#69 IS RESCOPED to TWO dimensions** (its 08-16 note is the authority): `dim_region` from
`confederations.csv` (**exists, 7 rows, read by nothing**) + `dim_country` built new. A competition
POINTS AT one; **which relationship is populated IS the answer** — no flag, no branch. Cost: the
registry's `country` mixes 21 countries with 24 region words; those 24 become NULL. Deletes
`single_country`. DISCOVERY first, then names to the CPO.

✅ **`!43` + `!45` MERGED — country fixed at source (wrong JSON path) and standardised in base**,
45/45. ⚠ `sync_dbt_vars.py:45` is now accurate — do not "fix" it. ⚠ **Never normalise country
names by regex** — `Guinea-Bissau` and `Timor-Leste`
are correctly hyphenated. **The transformation layer decides the FORM, the CPO decides the NAME.**

⛔ **`sort_order` IS OBSOLETE (CPO 2026-08-16)**; the mart must not read it. Values are incoherent
(restart in some types, run through in others, 110/120/130 in two) — that collision forced #54 note
3's `min(sort_order)` workaround. **Approved rule:** has-upcoming-fixture → days to next kickoff
**BUCKETED BY DAY** (raw clock ranks ED 10:15 over PL 19:00 — noise) → **region_rank** → kickoff
time → `league_code`; nothing upcoming last, most-recently-played first. National teams rise during
a break with no special case. Measured 25/45 upcoming, 20 none, 11 today. `region_rank` (UEFA 1 ·
FIFA 2 · CONMEBOL 3 · CONCACAF 4 · AFC 5 · CAF 6 · OFC 7) is HIS judgement. ⚠ Mart carries FACTS,
the spec declares the ORDER BY — **sorting is arrangement, not a fact**. ⚠ Retiring it reaches past
#54 — `export_site_data.py:583`/`:586`, `BrowseGrid.astro`, `landing.json` (#44, #367). ⚠ Order is
only as fresh as the last build → the nightly (NEXT 0) is its dependency.

✅ **Membership is 45 rows** — all have fixtures and logos; registry `status` useless here.

⛔ **HOME PAGE: design authority is #40 (players) + #41 (teams), NOT `10_home.md` §0**, wrong on both
(nine/six boards top 5; truth is FOUR boards of ONE metric, top 7). #367 shipped next matches →
browse; Top players/teams designed NOT built, slot BETWEEN. Follow-ups **#36** (blocks #377) ·
**#38** · **#42** · **#43** · **#44** · **#45**.

⚠ **REBASE TAX, paperwork-only:** conflicts land ONLY in `.claude/task/*`. **MINE** for
contract/review/review_input; **UNION** `escalations.log` by ARITHMETIC (not always
`main + (mine − base)` — !27 inserted at the TOP), then REBIND `diff_sha256`.
⚠ **NEVER restore uncommitted work with `git checkout --`** — it restores from HEAD and wipes the
edits. Bit me twice.

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

## ⭐ The ingest cluster is CLOSED but UNVERIFIED

⛔ **THE 04:00 NIGHTLY IS FAILING; `!39` DID NOT FIX IT.** The completeness gate reads a DELIBERATE
7-day re-fetch skip (#33 item 14) as a stalled ingest and exits 3 before dbt. Fix merged, but **the
nightly runs an IMAGE** — needs `gcloud run jobs deploy fdp-nightly --source . --region
europe-west1` from main. (`data:build:main` ran 08-13, so prod is fresh; different job.)
⚠ **Lesson, also in memory: an impact map that stops at LINEAGE misses GATES.** Item 14 changed
FETCH CADENCE and broke a gate assuming nightly fetches, past four reviewers.
⚠ **None of the four ingest fixes does what its title suggests** — caveats on #896-#898. Ultra plan
**450/min, 75,000/day**, draw ~8,300, so the PER-MINUTE limit binds. **No public site** — not a live
incident.

## ⭐ COST — read **GitLab issue #3** before touching anything

Everything recoverable from #547 is in **GitLab #3** — baselines, the ranked list **in ITS order**,
the free tools, MEASURED vs UNMEASURED. Read it; do not redo it.
⚠ **#70** adds a scan-budget guard there. Traps:

- **⚠ NEVER set a time-based partition expiry on raw** (#892). Nine biennial/quadrennial tournaments
  are `ingest_active` and go months without a refresh; expiry would delete the ONLY surviving row and
  staging's `qualify` would return zero rows. Use keep-latest-per-`(table, league_code)`. **A fixed
  lookback window has the same defect.**
- **⚠ Do NOT claim the API quota "breaks first"** — claimed once without evidence, withdrawn.
  (`standings.py:30` and `teams.py:28` DO loop every season daily with no skip — real, worth fixing.)
- **⭐ FREE: `bq query --dry_run`** (exact bytes, nothing runs) and **`report_bq_cost.py`**.
  ⚠ **Paste the output or do not claim it.**
- **MEASURED 08-03: $2.73/day**, prod tests $1.46 vs models $0.75. ⚠ PREDATES both fixes to its top
  item (#33 items 9/15). **Re-measure; never quote 08-03 as current.**
- **⚠ #2 IS LIVE; it fired 08-07 and 08-13.** `data:build:main` triggers on `data_paths`, which
  includes `.gitlab-ci.yml` and `scripts/check_*.py`, so a governance-only MR rebuilds the whole prod
  warehouse — costly, though on 08-13 it is what un-staled prod. **Check `data_paths` first.**

## ⭐ REVIEW MECHANICS — what the working agreement does not give you
Rules are `docs/working_agreement.md` §2 (#878). Only the traps live here.

- **Build the patch with the hook, never by hand:**
  `python .claude/hooks/git_discipline.py --review-patch > .claude/task/review_input.patch`
  ⚠ It is `git diff --staged <base>`, so **`git add` FIRST or it comes out EMPTY**. `contract.md` +
  `escalations.log` ARE delivered; task notes are not. A trailer names any excluded file that IS
  edited (#25/!19), so absence is not evidence of untouched.
- **Run `check_task_artifacts.py` BARE** (#24, !15) — it resolves the live remote, as does the hook
  since **#63**; `GOVERNANCE_BASE` overrides both. `--staged-hash` matches CI at any length. ⚠ On an
  UNCOMMITTED branch it prints "empty diff — OK": vacuous, not green.
- **A PASS may find nothing.** One `risks_checked:` entry is enough; never invent one. Cap is 3
  rounds then STOP. ⚠ `rounds: 0` is REFUSED — you do not get to skip the cycle.
- **`.claude/task/**` is scope-exempt; `active_work.md` is NOT** — it must be in `scope_paths`, and
  a commit touching `contract.md` is **never** artifact-exempt.
- **The org does NOT change** (CPO): low activation is not a defect; keep all reviewers.
- **⭐ A correction REPLACES, never accumulates, and must replace EVERYWHERE.** ⚠ Four occurrences
  on 08-14 cost five review rounds — corrected in one artifact, alive in another as a PARAPHRASE.
  **Sweep the CLASS semantically, not the phrase you wrote.** Mechanism: **#71**.

## Player page + the next CPO decision
**#846 + #886 merged:** the season a page opens on is a warehouse fact (`is_featured_season`, DQ
guarded). **CPO: the pipeline picks, not the page**, scoped by the tab's LENS.

**#845 + #882 are ONE decision and his** — which entities earn a page, and whether a past season
gets a URL or a control. Deciding apart sets the URL shape twice. Measured (×3 locales): players
51,589→154,767; **matches are BIGGER at 176,235**; h2h 51,903; teams 9,669. A 5-match gate leaves
1,274 teams and 21,979 players. Bring counts, not a general question.

**The player Overview is BUILT but UNCOMMITTED** in the stash `feat/player-overview-tab: Overview
BUILT` (⚠ NOT the #62 mart stash), with a known-wrong default (`seasons[0]` = most recent of ANY
competition, so both samples open on WC 2026). Mart half IS shipped — a one-line change on resume.
Held on #845. **#848: FOUR tabs**, International a national-lens TAB not a toggle (a crawler cannot
follow a control); four CPO-class consequences open.

## OWED — deferred
- **Guard telemetry is absent** — 2,684 lines of enforcement, zero records of a gate firing (#30
  finding 4); **the round cap only RECORDS** a builder-typed number. Both unfixed. Also: delete
  `macros/apif_latest_source_partition.sql` · metric-change skill · mirror crests · reviewers as
  peers (#822 shipped half).
- **⭐ #904 IS THE DOMINANT FAILURE** — a claim about the code asserted rather than RUN. Faces all
  seen: a grep scoped narrower than the sentence it supported; a TEST that passes either way (#63
  shipped three); **reading a column while never reading its VALUES** (`!43`); and **repeating a
  number out of this file without opening the source** (`!47`, the "16-column contract"). **A claim
  of ABSENCE must state where it looked; a test must be seen RED first; a column is not data.**
  Prose has failed 8×; the mechanism is **#71**.

## NEXT
0. **⚠ THE NIGHTLY — now DECIDED, build it.** CPO 2026-08-16: *"there should be a nightly"* — the
   recurring cost is approved, closed. Two parts: deploy image (`gcloud run
   jobs deploy fdp-nightly --source . --region europe-west1` from main; !39's fix is merged but not
   live) AND create the missing GitLab SCHEDULE. ⚠ **#4**: a web dispatch from ANY branch builds
   prod from THAT branch's code. The #62 ordering rule DEPENDS on this.
1. **#69 FIRST, then #62 step 3** (⭐ CURRENT) — step 3's `region_label` needs #69's two dimensions;
   the mart is written and stashed. Then step 4 repoints the export, 5 the page spec.
2. **The audit stream (⭐ above).** ⚠ Do NOT mix it with cost. The CPO's, one command each: **Q2 of
   #21** (set `main`'s push access to No one — the SERVER should protect it, not a client hook;
   ⚠ a branch cut from `gitlab/main` INHERITS that upstream, so unset it or push an explicit
   refspec) · delete the 2 dead `~/.claude/hooks/` copies · route or delete `seo-expert-reviewer`.
3. **⭐ THEN COST, SYSTEMATICALLY** — the whole pipeline **including CI/CD, what gets triggered,
   when, where** (CPO). Trigger/cost map FIRST, rank by real spend, fix in that order; the map goes
   in a GitLab ISSUE, never a doc. `data_paths` (#2) ranks ~4th.
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
   `CLAUDE.md` implies · **#70** scan-budget guard.

## OPEN — the CPO's alone
**Imprint operator + address** (#799), blocks publication, never conclude it · hosting recurring run
· feedback Apps Script (#687) · **#850** alias · **#875** where a group name lives · **#895
slim-vs-drop, blocking the biggest cost item** · **#21** · **#69** canonical country names.

## DO NOT (standing)
- **DESIGN, the weak spot:** never off the cuff — approved wireframes + role briefs, no block
  invented to fill a slot, never the canonical page built around an edge case, ONE tab at a time.
  Rendered output not prose; gather copy decisions BEFORE the branch.
- Do NOT treat the tracker as agreed work; re-validate. No new planning docs.
- Do NOT touch `site/` (retired). Do NOT derive facts in the export or frontend.
- **Never merge an MR. The CPO merges. Branch from main; never commit to main.**
- Plain language, lead with the decision, **no em dashes**, no walls of text.
- Do NOT ask him to adjudicate what a rule settles. **But copy is ALWAYS his (§10).**
- Do NOT bring him a fix for a defect he never asked about; fix it and move on.

## Verified state reference
- **No PUBLIC site.** v2 unlisted, every page `noindex` — why URLs are still free.
- **v2 built:** design system + 26 components, fixture page, team page (3 tabs), **home page (next
  matches → browse)**, page-spec + SEO contract (#826/#844), per-locale metric labels.
- **Tests: 814 python + 1 skipped** (measured 08-14 on main), plus 59 site (`cd site_v2 && npm
  test`); **219 dbt** after `!45`. ⚠ MEASURE, never predict (#904) — python was 665 two weeks ago.
- **`ruff` runs in CI** as `lint:python` (!20), config **`.ruff-ci.toml`** — filename load-bearing,
  pinned by `tests/test_lint_config.py`.
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). Reselling
  API-Football data is the one hard prohibition.
