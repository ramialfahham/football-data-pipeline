# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — `wc -c` counts BYTES and this file is full of multi-byte
> symbols, so it over-reports by ~220 and will send you trimming content that fits.

_Last updated **2026-07-31**. main GREEN at **8b43d48**. **IN FLIGHT: `feat/868-org-operational`,
18 files, UNCOMMITTED, review round 4 under a CPO `rounds_cap_override`.** The product is
**Matchday Pilot** on `matchdaypilot.com`.
The player page is FOUR tabs (#848); its Overview is **BUILT but UNCOMMITTED in `stash@{0}` with a
known-wrong default rule**, held on #845 + #846. **FIRST ACTIONS: read "⭐ CURRENT", run
`git stash list` before any git work, read #848 before the International tab.**

**NEW PROCESS (#858), in force: every plan is challenged by two independent reviewers BEFORE the CPO
sees it.** It found 24 defects on C2's plan and 9 on #868's. Never present an unchallenged plan._

## ✅ THE ORG IS IMPLEMENTED — branch `feat/868-org-operational`, #868
Four CPO rulings (2026-07-31) are now MECHANISMS. **`escalations.log` is the DECISIONS log now and
holds all four verbatim with their authority. Read it before re-deciding anything.**
1. **CTO SPLIT.** `platform-reviewer` (NEW) takes territory + line review; `cto-reviewer` keeps
   authority, no broad globs, woken by a PROPERTY of the change. **cto 28%→12%, platform 24%.**
   Zero `site_v2/src/**` pulls in either (test-pinned). Of the 8 guard paths, cto gets all at opus,
   platform joins on **2** (`hooks/**`, `workflows/**`); widening that is a cost = §10.
2. **Thresholds.** 2 of 4 are routing rows; new-mechanism + recurring-cost are DECLARED in
   `decisions_taken:`, tripwire = `scope-auditor`'s undeclared-threshold item (cite by NAME, numbers
   shift). **No gate parses that field: judgement at haiku tier. Stated, not hidden.**
3. **QA = evidence artifact + gate**, not an agent. `_acceptance_gate` fires ONLY on `site_v2/src/`:
   needs `acceptance_criteria:` + each demonstrated in `.claude/task/acceptance_evidence.md` under
   `criteria_demonstrated:`, from BUILT output. **No CI twin (#870).**
4. **Criteria: I draft, CPO approves BEFORE code, LOCKED after.** The lock is the mechanism.
5. **Editorial = mechanical gate** (`check_copy_gate.py`), never a copy approver. Wording ALWAYS
   yours. Growth owns a title's shape, Editorial its words.

**⚠ `check_copy_gate.py` EXITS 1 — 16 findings** (14 em dashes, `fi.secForm` `Muotovertailu` vs
`kunto`, `fi.footerDataSource` in English). **Not wired to CI: every fix is copy = §10 (#872).**
`report_process_health.py` reports rulings/branch, rounds, activation. **NOT CPO-ruled, sets NO
target** — an earlier draft invented a threshold AND a sunset rule for withdrawing your process; both
guard reviewers failed that as builder-authored governance. **Any threshold is yours.**

## THE GOAL
**The new website live.** Quality over speed. He runs **a 100% audit before go-live** and expects a
refactor may follow. "The result has to be (almost) perfect."

## ⭐ CURRENT — nothing in flight. Recommended next: unblock the player page (#845 + #846).

### 0. **PR D not started:** pre-launch with #799/#377 — slug persistence, the freeze, #843 redirects.
**WHY THE PLAYER PAGE BEATS D:** its Overview is built, tested and reviewer-passed in `stash@{0}`.
Two decisions (#845, #846) convert finished work into a shipped page. Everything else is longer.

**BLOCKING GO-LIVE, in rough order of harm:** **#838** renders a synthetic points number in the
CRAWLABLE BODY (`RecordStrip.astro:28`, verified `#3 · 71 pts`) — must land before indexing ·
**#861** fixture URLs destroyed weeks after kickoff · **#843/#852** slugs re-derive every build so an
indexed URL can move · **#845** what earns a page (154,644 player pages otherwise) · **#799**
imprint, the CPO's · **6 of 15 screens unspec'd**.

**⚠ `PROJECT_BOARD_TITLE`** (`board-request-sync.yml` + `_paused/project-status-sync.yml`) is a
**live lookup key** for `Matchday Pilot - Project Board`: `:101` matches BY TITLE, **throws** at
`:104`. String and board move together, never "tidy" one alone.

**Old brand ON PURPOSE, do not "fix":** `north_star.md` (#860) · 6 wireframe `| Matchday IQ` titles ·
`site_v2/package*.json` · `system.css:2` (locked, stripped at build) · **`site/**`, the retired
prototype, where `Matchday IQ` is CORRECT HISTORY.**

**Rulings** (escalations.log): **E3 TRANSLITERATE** — base letter where one exists, expand where
none, so `ü→u` AND `ß→ss` are ONE rule · **E2 warehouse** produces slugs · ONE locale-independent
slug · **base prepares, the core dim publishes.**

**Carry into D:** 39 teams lack a country, **22 have one in `stg_apif__teams`** · flat `slug_map` so
**90 player kebabs equal coach kebabs** · players id-suffixed · `fixture_slug` from NAMES in Python ·
`team_name_key` zero callers · **#3045 takes `/teams/dragon/`, #4207 `/teams/warriors/`** silently.

### 1. #844 SHIPPED (#867). What it leaves open.

Gate: `scripts/audit-seo.mjs` + `integrations/seo-audit.mjs`; switch: `src/config/indexability.mjs`;
specs carry a required `seo` block. **Flipping `INDEXABLE` true is the go-live act**, and the audit
refuses it while `STUB_PAGES` is non-empty.

**Open:** `LinksFooter` renders `<span>` where `<a>` belongs (own PR) · no redirect/alias mechanism ·
no 404 strategy for the fixture cliff · structured-data COMPLETENESS (the check is format-only) ·
rich vs thin tier · OG-image fitness · **localised COMPETITION names** (registry has ONE `name`, so
Finnish readers see "Premier League" not "Valioliiga") · the title-width gate fails at 660px not 600.

**Siblings:** **#845** what earns a page · **#843** the URL derives from an unverified mutable field ·
**#846** window selection in the frontend.

**`seo-expert-reviewer` (#842) is STILL INERT** — absent from `review_routing.json`. The org work
(#868) did NOT route it: approved in principle, not commissioned, its own governance event. **It IS
usable directly as a consultant** — its #844 ruling reversed a CPO decision. Its domain IS
enumerable in 12 globs, so the old "no glob expresses it" premise was FALSE.

### 2. The player page is FOUR tabs (#848, CPO-agreed 2026-07-27)

Overview · Performance · Career = **club only**, always shown. **International = national lens, shown
only when `national_appearances_total >= 1`.** A tab, NOT a toggle: a crawler cannot follow a control,
so the national lens would have no URL. The condition is a **served fact**, so more national data
makes the tab appear with zero template change. It carries a competition selector **+ PERFORMANCE**.
**Read #848 before shaping it** — four CPO-class consequences are NOT actioned there.

### 3. ⚠️ PLAYER OVERVIEW IS BUILT BUT UNCOMMITTED — IN stash@{0}, WITH A KNOWN-WRONG RULE

`git checkout feat/player-overview-tab && git stash pop` — **do NOT rebuild it.** Build and tests
green, `bi-analyst-reviewer` + `scope-auditor` PASS; uncommitted because the gate rejects a FAIL.
**⚠️ Its default-season rule is WRONG:** `seasons[0]` = most recent of ANY competition, so both
sample players open on **World Cup 2026** with their national side. Under #848 the club tabs are
club-only, so it must be the most recent CLUB season. **Note: it would now ALSO be blocked by the new
acceptance gate**, which is the point — it passed both reviewers while doing the wrong thing.

**Held on:** **#845** — adding `players` = **154,644 pages** against a build already needing 8GB at a
sixteenth of that · **#846** — the payload must carry the lens per season AND which club season is
featured. Not the frontend, not the export (**consumption too**), so it is a MART change.

**#753's design-state comment is the authority. Everything in its section C is still open.**
**RENDER FAILURE fix, keep all three:** ONE tab at a time, a **NEW** artifact URL, both channels.
**Still owed:** the CPO-approved chip/pill sizing (`.cchip` 44px) — own PR, edits `system.css`.

**Data deps.** **#840** (club match count; rank YoY sign) · **#838** + **#839** block the **TEAM**
Overview's cup behaviour, not the player page · **#841** blocks player **PERFORMANCE**.

## Reserved (§10, standing)
Nav order · search style · desktop RAIL per page type · footer/legal (imprint-blocked) ·
default-theme policy. **Deferred:** component/metric catalogue, import-boundary rule, #828.

## DESIGN DISCIPLINE (the weak spot — read every time)
- **Compose from the locked `system.css` ONLY.** Refs `be7bd6d3` · fixture `d70aae67` · team
  `f6348775`; player `6c21ef71` NOT approved.
- **Show, don't describe.** Rendered output or a mock IS the proposal; never ask him to rule on prose.
- **A rename is not a find-and-replace.** Where a line describes the RETIRED MVP, `Matchday IQ` is
  correct history; only forward-looking refs become Matchday Pilot.
- **READ THE DOCS AND QUERY THE DATA FIRST, don't assert.** Eight logged misses, each a query away.
  Memory `feedback_engineering` + `feedback_verify_real_world_identity`.
- **A decision taken means the next action is an EDIT**, not another artifact.
- **MY SEARCHES KEEP BEING STRUCTURALLY UNABLE TO FIND THE THING.** `git grep` is BRE so `?` is
  literal; a brand grep cannot find a CLAIM omitting the brand; an `--include` narrower than the
  class. **State what a grep CANNOT see or do not call it a sweep.** Verify renames against RENDERED
  TEXT (Astro EMITS `<!-- -->`). Memory `feedback_verify_renames_against_rendered_text`.
- **I CANNOT self-assess copy in ANY language, English included.** #844: FOUR of nine strings wrong
  (German missing an article, Finnish `sarjassa` + an uninflected borrowed noun, `muoto` not `kunto`,
  an unverified separator). **`site/i18n/*.json` = 127 VALIDATED strings per locale, check against
  it** — `check_copy_gate.py` now does. Em dashes read as AI-generated.
- **Design for the DEFAULT case** — a page built around a goalkeeper gave two wrong conclusions.
- **Never fill an empty slot to balance a layout.**
- **Real data only** — honest empty states; "no hero, not shippable" is RETRACTED.
- **Multi-tab pages: write the per-tab content boundary FIRST, build ONE tab at a time.** Check ALL
  sibling wireframes, not one.

## WHERE WE STAND
**Pages** 2 of 5 (fixture + team) + player Overview HELD · **6 of 15 screens UNSPEC'D** (home, comp
hub, browse, leaderboards, h2h, glossary) · **Real data** ✅ · **Hosting** LIVE, trigger shape +
go-public left · **Legal** not started. Marts + metric layer DONE, do not reopen.

**⚠️ v2 makes third-party requests TODAY** — `Crest`/`PlayerRow` render `media.api-sports.io` as
`<img>`, the defect that took the MVP offline. Fix = mirror crests to our origin.

## OWED — deferred, not forgotten (must survive rewrites)
- **A ui-BUILDER agent** (`stash@{1}`) — superseded: the org chose ONE builder wearing lenses.
- **The metric-change skill** (one metric touched SIX files) · **mirror the crests** · **reviewers
  as peers** (#822 shipped only the model half) · **amend `metrics_display.md`** (#804's 2 metrics).

## DONE (history is in git — only still-live gotchas kept)
Filed: **#838–#841, #843–#846, #848, #850–#853, #863–#866, #868, #870–#873**. Merged: #842, #847,
#854, #857, #862, #865, #867. #753 carries the player design state. Metric layer complete.
- ⚠️ `appearances` = played legs (`minutes_played > 0`), not squad selections.
- ⚠️ `astro build` OOMs at full scale (`--max-old-space-size=8192`); before a local dev build run
  `git clean -fX site_v2/src/data`.
- ⚠️ team-page footer says "Sample data" on real data. No player photos (CPO). API-Football:
  reselling is the one hard prohibition.

## NEXT
1. **Player page** (#845 + #846), then Performance → Career, ONE tab at a time, each content
   boundary decided before mocking.
2. Home page (`1c35e7aa` = reference only), **then legal/imprint**, then launch.
3. Follow-ups: **#863** PROTECTED path editable with NO `protected_override` · **#866**
   `Regular Season - 20` untranslated · **#864** stale `cutover` comments · **routing matcher is
   hand-copied** in `git_discipline.py:132` + `check_task_artifacts.py:156`, NO parity test ·
   copy-gate's 16 findings (CPO) · route `seo-expert-reviewer`; GAP-22 should be GAP-20; #833.

## OPEN — the CPO's alone
- **Imprint operator + address** (#799) — blocks publication; get a lawyer, never conclude it.
- **Hosting recurring run** — trigger shape only; go-public is imprint-blocked.
- **The feedback Apps Script** — #687.
- **#850's alias decision** — which duplicate team record is canonical. PR D freezes the URLs.

## DO NOT (standing)
- Do NOT treat the tracker as agreed work; re-validate before acting.
- Do NOT write another planning document (the tracker + this file are the plan).
- Do NOT touch `site/` (retired/frozen). Do NOT build an unapproved page.
- Do NOT derive facts in the export or frontend — select/group/rename only.
- **Never merge a PR. The CPO merges. Branch from main; never commit to main.**
- Communication: plain language, lead with the decision, **no em dashes** (he flagged them twice as
  an AI tell, in my prose AND in product copy), no walls of text.
- Do NOT ask him to adjudicate what a rule can settle. Bring a rule that runs itself, or say plainly
  that none exists and name the cost. **But copy is ALWAYS his (§10) — that is not adjudication.**

## Operational notes
- **dbt CLI is broken locally. SQLFluff is NOT** — only its dbt templater is (needs GCP). **Lint from
  the REPO ROOT** (the root `.sqlfluff` has the jinja macro path, `dbt_project/.sqlfluff` does not):
  `python -m sqlfluff lint <model> --templater jinja --dialect bigquery`, FULL rule set (a `--rules`
  subset missed ST06). BigQuery rejects a FROM-less WHERE.
- **A wildcard is fine over ONE ref; add a join and AM04 fires.** Enumerate columns, the repo has
  **zero `noqa`**. Nesting ceiling ≈8 calls.
- **Frontend:** `deploy-site-v2.yml` (manual-only) does export → build → firebase deploy. The Browser
  pane CAN drive the dev server (`preview_start` name `v2`) — accessibility tree, geometry and console
  all work; only `screenshot` fails. **Artifact delivery works** with the three rules in "⭐ CURRENT".
- **Commit mechanics:** `git commit` runs alone (no chaining); `--amend` gate-blocked; **no double
  quotes in the message** (the form gate reads them as pathspecs). A post-commit hook auto-pushes and
  opens the PR. `review.md` must be COMMITTED or CI reads the stale hash.
- **Contract edits need a CLEAN tree** — stash-dance with explicit paths. ⚠ A pathspec stash can
  capture MORE than the paths given; if popping conflicts, `git checkout stash@{0} -- <paths>` then
  drop. Check `git stash list` after — never assume the index.
- **⚠ CWD PERSISTS between Bash calls** — `cd` to the repo root in the command, or a script silently
  measures nothing. **⚠ `fnmatch`'s `*` CROSSES `/`**, so `site_v2/*.json` also matches
  `site_v2/src/data/*.json`; and `scope_paths`' `[lang]`/`[team]` are CHARACTER CLASSES, so a literal
  Astro dynamic-route path can NEVER match itself — use `site_v2/src/pages/*/teams/*.astro`.
- **⚠ `src/pages/index.astro` is DEAD CODE** — `prefixDefaultLocale` writes a root redirect over it.

## Verified state reference
- **Live to users:** no PUBLIC site. v2 is on `football-data-pipeline-gcp.web.app` (unlisted), every
  page `noindex`. **Nothing is published, which is why URLs are still free to change.**
- **v2 built:** design system (`system.css` + 26 components), fixture page, team page (3 tabs), nav
  shell (#825), page-spec + SEO contract (#826/#844). `.shell`/`.page-grid`/`.rail` wired into zero
  pages; team/fixture stay at 680px `.inner`.
- **Datasets:** base + seeds in `dbt_analytics`; also `staging`, `core`, `marts`, `ci_*`.
  `generate_schema_name` prefixes non-prod targets, but **never run a local `dbt build`.**
