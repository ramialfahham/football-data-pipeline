# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — `wc -c` counts BYTES and this file is full of multi-byte
> symbols, so it over-reports by ~220 and will send you trimming content that fits.

_Last updated **2026-07-29**. main GREEN at **8b43d48**. **NOTHING IN FLIGHT — clean slate, no
branch, no open PR.** The A→C2 sequence is DONE: #854, #857, #862, #865, #867 all merged. The product
is **Matchday Pilot** on `matchdaypilot.com`.
The player page is FOUR tabs (#848); its Overview is **BUILT but UNCOMMITTED in git stash@{0} with a
known-wrong default rule**, held on #845 + #846. **FIRST ACTIONS: read "⭐ CURRENT", run
`git stash list` before any git work, read #848 before shaping the International tab.**

**NEW PROCESS (#858), in force: every plan is challenged by two independent reviewers BEFORE the CPO
sees it.** On C2's plan it found 24 defects and 3 FALSE claims. Never present an unchallenged plan._

## ⏸ PAUSED MID-EXERCISE — the org/process design (#868)
The CPO wants this project run like a real company and is **mid-way through defining the roles,
processes and org**. It is a DESIGN exercise; nothing is implemented. **Resume from #868's second
comment**, which holds the roles x rituals grid, the three bands, and the open questions.
**His correction, which is the organising principle: define where each role's responsibility BEGINS
and ENDS — do NOT scale ceremony by change size** (that just adds a judgement call). A change either
enters a domain or it does not.
**The finding that unlocks it:** `review_routing.json` maps FILE PATHS to roles, but a domain is not
a set of paths. SEO's domain ("what a crawler sees") spans `Layout.astro`, the specs, `strings.ts`,
the export's slug logic AND the registry's competition names. No glob expresses that, which is why
`seo-expert-reviewer` **has never fired once** despite being created deliberately.
**Missing roles found by absence:** Localisation Lead (cost us on #867 — four of nine strings wrong,
the CPO wrote the Finnish himself), Product Lead, and fractional Legal + SRE.
**Then: back to building.** He said so explicitly.

## THE GOAL
**The new website live.** Quality over speed. He runs **a 100% audit before go-live** and expects a
refactor may follow. "The result has to be (almost) perfect."

## ⭐ CURRENT — nothing in flight. Recommended next: unblock the player page (#845 + #846).

### 0. THE SEQUENCE — A→C2 ALL MERGED (#854, #857, #862, #865, #867). **D is next and not started:**
pre-launch with #799/#377 — slug persistence, the freeze, #843's redirects.

**WHY THE PLAYER PAGE BEATS D AS THE NEXT MOVE:** its Overview is already built, tested and
reviewer-passed in `stash@{0}`. Two decisions (#845 what earns a page, #846 which season it opens on)
convert finished work into a shipped page type. Everything else on the list is longer.

**BLOCKING GO-LIVE, in rough order of harm:** **#838** renders a synthetic points number in the
CRAWLABLE BODY (`RecordStrip.astro:28`, verified `#3 · 71 pts`) — must land before indexing ·
**#861** fixture URLs destroyed weeks after kickoff · **#843/#852** slugs re-derive every build so an
indexed URL can move · **#845** what earns a page (154,644 player pages otherwise) · **#799**
imprint, the CPO's · **6 of 15 screens unspec'd**.

**⚠ `PROJECT_BOARD_TITLE`** in `board-request-sync.yml` + `_paused/project-status-sync.yml` is a
**live lookup key** for `Matchday Pilot - Project Board`: `:101` matches BY TITLE and **throws** at
`:104`. String and board move together — never "tidy" one alone.

**Still carrying the old brand ON PURPOSE, do not "fix":** `north_star.md` (#860) · the 6 wireframe
`| Matchday IQ` title templates · `site_v2/package*.json` · `system.css:2` (locked, stripped at
build) · **`site/**`, the retired prototype, where `Matchday IQ` is CORRECT HISTORY.**

**Rulings** (escalations.log): **E3 = TRANSLITERATE** — fold to the base letter where one exists,
expand only where none does, so `ü→u` AND `ß→ss` are ONE rule · **E2 = the warehouse** produces
slugs · ONE locale-independent slug · **base prepares, the core dim publishes.**

**Carry into D:** 39 teams lack a country, **22 have one in `stg_apif__teams`** · `slug_map` is flat,
so **90 player kebabs equal coach kebabs** · players still id-suffixed · `fixture_slug` still from
NAMES in Python · `team_name_key` zero callers · **#3045 takes `/teams/dragon/`, #4207
`/teams/warriors/`** silently (PR D freezes them).

### 1. #844 SHIPPED (#867). What it leaves open.

Gate: `scripts/audit-seo.mjs` + `integrations/seo-audit.mjs`; switch: `src/config/indexability.mjs`;
specs carry a required `seo` block. **Flipping `INDEXABLE` true is the go-live act**, and the audit
refuses it while `STUB_PAGES` is non-empty.

**Open, from the challenge + reviews:** `LinksFooter` renders `<span>` where `<a>` belongs (a NEW
rule, own PR) · no redirect/alias mechanism · no 404 strategy for the fixture cliff · structured-data
COMPLETENESS (the check is format-only) · rich vs thin tier · OG-image fitness · **localised
COMPETITION names** (the registry has ONE `name`, so Finnish readers see "Premier League" where they
expect "Valioliiga") · **14 em dashes in shipped copy**, worst `heroVerdictUnder` on the team page ·
the title-width gate fails at 660px not 600, which bundles calibration with an accepted-truncation
decision the CPO has now seen.

**Siblings:** **#845** what earns a page · **#843** the URL derives from an unverified mutable field ·
**#846** window selection in the frontend.

**`seo-expert-reviewer` (#842) is INERT** — absent from `review_routing.json`, so it fires on
nothing (see the PAUSED section: that is a boundary problem, not a routing typo). **It IS usable
directly as a consultant** — its #844 ruling reversed a CPO decision.

### 2. The player page is FOUR tabs (#848, CPO-agreed 2026-07-27)

Overview · Performance · Career = **club only**, always shown. **International = national lens, shown
only when `national_appearances_total >= 1`.** A tab, NOT a toggle: a crawler cannot follow a control,
so the national lens would have no URL. The condition is a **served fact**, so more national data
makes the tab appear with zero template change. It carries a competition selector **+ PERFORMANCE**.
**Read #848 before shaping it** — four CPO-class consequences are NOT actioned there.

### 3. ⚠️ PLAYER OVERVIEW IS BUILT BUT UNCOMMITTED — IN stash@{0}, WITH A KNOWN-WRONG RULE

`git checkout feat/player-overview-tab && git stash pop` — **do NOT rebuild it.** Build and tests
green, `bi-analyst-reviewer` + `scope-auditor` PASS; uncommitted because the gate rejects a FAIL.

**⚠️ Its default-season rule is WRONG as stashed:** `seasons[0]` = most recent of ANY competition, so
both sample players open on **World Cup 2026** with their national side. Under #848 the club tabs are
club-only, so it must be the most recent CLUB season.

**Held on:** **#845** — adding `players` = **154,644 pages** against a build already needing 8GB at a
sixteenth of that · **#846** — the payload must carry the lens per season AND which club season is
featured. Not the frontend, not the export (**consumption too**), so it is a MART change.

**#753's design-state comment is the authority. Everything in its section C is still open.**

**RENDER FAILURE fix, keep all three:** ONE tab at a time, a **NEW** artifact URL, both channels.

**Still owed:** the CPO-approved chip/pill sizing (`.cchip` 44px) — own PR, edits `system.css`.

**Data deps.** **#840** (club match count; rank YoY sign) · **#838** + **#839** block the **TEAM**
Overview's cup behaviour, not the player page · **#841** blocks player **PERFORMANCE**.

## Reserved (CPO §10, standing)
Nav order · search style · desktop RAIL per page type · footer/legal (imprint-blocked) ·
default-theme policy. **Deferred:** component/metric catalogue, import-boundary rule, #828.

## DESIGN DISCIPLINE (the weak spot — read every time)
- **Compose from the locked `system.css` ONLY.** Refs `be7bd6d3` · fixture `d70aae67` · team
  `f6348775`; player `6c21ef71` NOT approved.
- **Show, don't describe.** Rendered output or a mock IS the proposal; never ask him to rule on prose.
- **A rename is not a find-and-replace.** Where a line describes the RETIRED MVP, `Matchday IQ` is
  correct history; only forward-looking references become Matchday Pilot.
- **READ THE DOCS AND QUERY THE DATA FIRST, don't assert.** Eight logged misses, each a query away.
  Memory `feedback_engineering` + `feedback_verify_real_world_identity`.
- **MY SEARCHES KEEP BEING STRUCTURALLY UNABLE TO FIND THE THING.** Three times in one session:
  `git grep` is BRE so `?` is a literal; a brand grep cannot find a false CLAIM that omits the brand;
  an `--include` filter narrower than the class. **State what a grep CANNOT see, or do not call it a
  sweep.** Verify renames against RENDERED TEXT (split markup and `outerHTML` defeat greps; Astro
  EMITS `<!-- -->`, use `{/* … */}`). Memory `feedback_verify_renames_against_rendered_text`.
- **I CANNOT self-assess copy in ANY language, English included.** #844's nine SEO strings went to
  the CPO after a §10 FAIL and FOUR of mine were wrong (German missing a required article, Finnish
  `sarjassa` + an uninflected borrowed noun, `muoto` where football says `kunto`, an unverified
  separator). **The retired MVP's `site/i18n/*.json` is 127 VALIDATED strings per locale — check new
  copy against it.** Em dashes read as AI-generated. **No Localisation role exists (#868).**
- **Design for the DEFAULT case** — a page built around a goalkeeper gave two wrong conclusions.
- **Never fill an empty slot to balance a layout.**
- **Real data only** — honest empty states; "no hero, not shippable" is RETRACTED.
- **Multi-tab pages: write the per-tab content boundary FIRST, build ONE tab at a time.** Check ALL
  sibling wireframes, not one.

## WHERE WE STAND
**Pages** 2 of 5 built (fixture + team) + player Overview HELD · **6 of 15 screens UNSPEC'D** (home,
competition hub, browse, leaderboards, h2h, glossary) · **Real data** ✅ · **Hosting** LIVE, trigger
shape + go-public left · **Legal** not started. Marts + metric layer DONE; do not reopen.

**⚠️ v2 makes third-party requests TODAY** — `Crest`/`PlayerRow` render `media.api-sports.io` as
`<img>`, the defect that took the MVP offline. Fix = mirror crests to our origin.

## OWED — deferred, not forgotten (must survive rewrites)
- **The agent set** — a ui-BUILDER (draft on `feat/expert-agents-that-build`); real CONSULTANT
  agents; a fan probe. **#868 supersedes this** as the org/process overhaul.
- **The metric-change skill** (one metric touched SIX files) · **mirror the crests** · **reviewers
  as peers** (#822 shipped only the model half) · **amend `metrics_display.md`** (#804's 2 metrics).

## DONE (history is in git — only still-live gotchas kept)
Filed: **#838–#841, #843–#846, #848, #850–#853, #863, #864, #866, #868**. Merged: #842, #847, #854,
#857, #862, #865, #867. #753 carries the player design state. Metric layer complete.
- ⚠️ `appearances` = played legs (`minutes_played > 0`), not squad selections.
- ⚠️ `astro build` OOMs at full scale (`--max-old-space-size=8192`); before a local dev build run
  `git clean -fX site_v2/src/data`.
- ⚠️ team-page footer says "Sample data" on real data. No player photos (CPO). API-Football:
  reselling is the one hard prohibition.

## NEXT
1. **Player page** (#845 + #846), then Performance → Career, ONE tab at a time, each content
   boundary decided before mocking.
2. Home page (`1c35e7aa` = reference only), **then legal/imprint**, then launch.
3. Follow-ups: **#863** a PROTECTED path is editable with NO `protected_override` · **#866**
   `Regular Season - 20` untranslated in every locale · **#864** stale `cutover` comments ·
   **#868** operationalise the agent org (discovery spikes, issue anchors, veto criteria) · route
   `seo-expert-reviewer`; `content_architecture.md` cites GAP-22 (should be GAP-20); fixture
   PlayerRow "1 assists" singular; #833; the 4-way locale-list duplication.

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
  subset missed ST06). Also `check_layer_contract.py`. BigQuery rejects a FROM-less WHERE.
- **A wildcard is fine over ONE ref; add a join and AM04 fires.** Enumerate columns — the repo has
  **zero `noqa`**. Nesting ceiling ≈8 calls (parse depth 255).
- **Frontend:** `deploy-site-v2.yml` (manual-only) does export → build → firebase deploy. The Browser
  pane CAN drive the dev server (`preview_start` name `v2`) — accessibility tree, geometry and console
  all work; only `screenshot` fails. **Artifact delivery works** with the three rules in "⭐ CURRENT".
- **Commit mechanics:** `git commit` runs alone (no chaining); `--amend` gate-blocked; **no double
  quotes in the message** (the form gate reads them as pathspecs). A post-commit hook auto-pushes and
  opens the PR. `review.md` must be COMMITTED or CI reads the stale hash.
- **Contract edits need a CLEAN tree** — stash-dance with explicit paths. ⚠ A pathspec stash can
  capture MORE than the paths given; if popping conflicts, `git checkout stash@{0} -- <paths>` then
  drop. Check `git stash list` after — never assume the index.
- **⚠ CWD PERSISTS between Bash calls.** Four false results this session came from a script running
  in `site_v2/` and silently measuring nothing. `cd` to the repo root in the command.
- **⚠ `scope_paths` uses `fnmatch`, so `[lang]`/`[team]` are CHARACTER CLASSES.** A literal Astro
  dynamic-route path can NEVER match itself — use `site_v2/src/pages/*/teams/*.astro`. Bites every
  frontend contract.
- **⚠ `src/pages/index.astro` is DEAD CODE** — `prefixDefaultLocale` generates a root redirect that
  overwrites it. Editing it changes nothing that ships.

## Verified state reference
- **Live to users:** no PUBLIC site. v2 is on `football-data-pipeline-gcp.web.app` (unlisted), every
  page `noindex`. **Nothing is published — which is why URLs are still free to change.**
- **v2 built:** design system (`system.css` + 26 components), fixture page, team page (3 tabs), nav
  shell (#825), page-spec + SEO contract (#826/#844). `.shell`/`.page-grid`/`.rail` exists, wired
  into zero pages; team/fixture stay at 680px `.inner`.
- **Datasets:** base models + seeds in `dbt_analytics`; also `staging`, `core`, `marts`, `ci_*`.
  `generate_schema_name` prefixes non-prod targets, but **never run a local `dbt build`.**
