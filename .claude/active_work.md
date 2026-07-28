# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> chars (the SessionStart hook's budget).

_Last updated **2026-07-28**. main GREEN at **27b26e9** (PRs A/#854 and B/#857 MERGED). **IN FLIGHT:
branch `feat/rename-matchday-pilot` = PR C1.** The product is renamed **Matchday Pilot**, domain
`matchdaypilot.com`. PR C was split on its own scope warning: **C1 rename (this), C2 = #844 gate +
emitted surface.** The player page is FOUR tabs (#848); its Overview is **BUILT but UNCOMMITTED in git
stash@{0} with a known-wrong default rule**, held on #845 + #846. **FIRST ACTIONS: read "⭐ CURRENT",
run `git stash list` before any git work, read #848 before shaping the International tab.**

**NEW PROCESS (#858), in force: every plan is challenged by two independent reviewers BEFORE the CPO
sees it.** Its first use on C2's plan found 24 defects across two rewrites, four structural. Do not
present a plan he has not seen challenged._

## THE GOAL
**The new website live.** ~2–3 weeks; quality over speed (CPO 2026-07-22).

## ⭐ CURRENT — C1 rename in flight, then C2 (#844).

### 0. THE SEQUENCE

| PR | Scope | State |
|---|---|---|
| **A** | #850 team name corrections in base | ✅ MERGED #854 |
| **B** | #852 drop the provider id, slug DERIVED in the warehouse | ✅ MERGED #857 |
| **C1** | Rename to **Matchday Pilot** + `site` → `matchdaypilot.com` | ← IN FLIGHT |
| **C2** | **#844 SEO gate** + the emitted surface (canonical/hreflang/OG/JSON-LD/sitemap) | next |
| **D** | Pre-launch with #799/#377: slug persistence, the freeze, #843's redirects | — |

**#844 was never blocked by the slug** — a spec declares the canonical *template*, not the value.

**Rulings** (escalations.log): **E3 = TRANSLITERATE** — fold to the base letter where one exists,
expand only where none does, so `ü→u` AND `ß→ss` are ONE rule · **E2 = the warehouse** produces slugs ·
ONE locale-independent slug · **base prepares, the core dim publishes.**

**Carry into C2/D:** country anchor corrupted — 39 teams lack a country, **22 have one in
`stg_apif__teams`** · `slug_map` is flat, so **90 player kebabs equal coach kebabs** · players still
id-suffixed · `fixture_slug` still from NAMES in Python · `team_name_key` zero callers ·
`dbt_project/.sqlfluff` lacks the jinja macro path · **#3045 silently takes `/teams/dragon/`, #4207
`/teams/warriors/`** (no collision, no signal, and PR D freezes them) · **#861: fixture URLs are
DESTROYED weeks after kickoff** — 4,598 live vs 52,585 finished with no page. Latent under `noindex`,
catastrophic at #377.

### 1. WHY #844 EXISTS (the ruling stands; it is now PR C)

CPO: *"SEO optimization has to be ensured during the whole process of building the website."* A
reviewer is after-the-fact and cannot ensure anything.

**#844 — extend #826's page-spec contract so no page BUILDS without declaring its SEO surface.** Three
parts: declare at `prebuild` · verify at `postbuild` over `dist/` (uniqueness only exists after
generation, so the half that matters CANNOT be a prebuild check) · a minimal emitter in
`Layout.astro`. **Full design on #844 + artifact `4fe25734`.**

**PR C must also carry the SEO list two experts rated above the slug change:** `astro.config.mjs`
`site` points at the **DELETED** GitHub Pages host, so every canonical would resolve to a dead domain ·
no canonical/hreflang/sitemap/`robots.txt` · all three locales ship **byte-identical titles and
descriptions** · the two built pages link to each other **zero** times and `LinksFooter` renders
`<span>` where `<a>` belongs · uniqueness domain must be **entity × locale**. Retrofit fixture + team
in PR C or main ships red.

**Siblings:** **#845** minimum-data gate (what earns a page) · **#843** reframed — the URL is derived
from an unverified mutable field, not merely "changes on rename" · **#846** window selection in the
frontend.

**`seo-expert-reviewer` exists (merged, #842) but is INERT** — absent from `.claude/review_routing.json`,
so it fires on nothing. Routing it is an **open governance ask** (protected file).

### 2. The player page is FOUR tabs (#848, CPO-agreed 2026-07-27)

Overview · Performance · Career = **club only**, always shown. **International = national lens, shown
only when `national_appearances_total >= 1`.**

**A tab, not a toggle** — a crawler cannot follow a control, so the national lens would have no URL.
The condition is a **served fact**, so ingesting more national data makes the tab appear with zero
template change. **It carries a competition selector + PERFORMANCE**, not just counts (the "peer groups
too small" objection was checked and is false: WC 2026 ranks 314 players). **Read #848 before shaping
it.** Four CPO-class consequences NOT actioned: wireframe 13's Career hands over its National team
section · `content_architecture.md` §4 states a DIFFERENT settled tab set · no wireframe file exists ·
#846 changes shape.

### 3. ⚠️ PLAYER OVERVIEW IS BUILT BUT UNCOMMITTED — IN stash@{0}, WITH A KNOWN-WRONG RULE

`git checkout feat/player-overview-tab && git stash pop` — **do NOT rebuild it, it exists.** Build
green, tests green, `bi-analyst-reviewer` + `scope-auditor` PASS. Uncommitted because the gate rejects
a FAIL.

**⚠️ Its default-season rule is WRONG as stashed:** `seasons[0]` = most recent of ANY competition, so
both sample players open on **World Cup 2026** with their national side. Under #848 the club tabs are
club-only, so it must be the most recent CLUB season. Do not ship it.

**Held on:** **#845** — the deploy exports `teams,fixtures` only, so shipping puts hundreds of real
dead links on the team page; adding `players` = **154,644 pages** against a build already needing 8GB
at a sixteenth of that (CPO chose: hold until the gate defines what earns a page) · **#846** — the
payload must carry the lens per season AND which club season is featured. Not the frontend (window
selection), not the export (**consumption too**), so it is a mart change: serve the most recent
`entity_type='club'` season; the within-year tie-break is undecided (Rogers has UEL, PL, FAC in 2025).

**#753's design-state comment is the authority. Everything in its section C is still open — do not
build from those**, including tab-vs-URL.

**RENDER FAILURE: DIAGNOSED. Keep all three:** ONE tab at a time (no hidden panels), a **NEW**
artifact URL (never republish), deliver via Artifact **and** SendUserFile.

**Still owed:** the CPO-approved chip/pill sizing (`.cchip` fixed 44px so both pill groups are 140px
and align, label before each group) — a separate PR: it edits shipped `system.css`.

**Data deps.** **#840** (club match count for "37 of 38"; rank YoY sign) · **#838** (points is a
synthetic 3-1-0 tally in EVERY competition: FA Cup renders 0, UEL 32 against a real 18) and **#839**
(phase spike, tables vs brackets) block the **TEAM** Overview's cup behaviour, not the player page ·
**#841** (pass accuracy 23–30% since 2022 vs 72–73% before) blocks player **PERFORMANCE**.

## Phase B — DONE (#825 shell, breakpoints 700/900/1010px · #827 · #826 page-spec contract)
**Reserved (CPO §10, standing):** nav order · search style · desktop RAIL per page type · footer/legal
(imprint-blocked) · default-theme policy. **Deferred:** component/metric catalogue, import-boundary
rule, one-page driver (#828). Home mock `1c35e7aa` = reference only.

## DESIGN DISCIPLINE (the weak spot — read every time)
- **Compose from the locked `system.css` ONLY.** Refs `be7bd6d3` · fixture `d70aae67` · team
  `f6348775`; player mock `6c21ef71` NOT approved.
- **READ THE DOCS AND QUERY THE DATA FIRST, don't assert.** Logged misses, every one a query or a file
  read away: an architecture proposed from 3 of 44 competitions; the club/national split already in
  `competition_types.csv`; "national peer groups too small" (WC 2026 ranks 314); **"Glasgow Rangers"**
  from memory (never the official name); **"18.5% of players collide"** off the wrong column (1.6%);
  **"`fct_fixture` is incremental"** (it is a table) used to justify a design; a proposed guard that
  checked the output the pipeline already guarantees, so it could never fire.
- **Design for the DEFAULT case, not an edge case** — the page was built around a goalkeeper and two
  conclusions were wrong until it was rebuilt on an outfielder.
- **Never fill an empty slot to balance a layout** (cards in a strip, the invented hero of 07-21).
- **Build it and show it** — a mock IS the decision; never ask about something visual in words.
- **Real data only** — honest empty states; "no hero, not shippable" is RETRACTED.
- **Multi-tab pages: write the per-tab content boundary FIRST, build ONE tab at a time.** Check ALL
  sibling wireframes + the shipped tab component, not one file.

## WHERE WE STAND — five launch groups
**Pages** 2 of 5 built (fixture + team), player Overview built but HELD, all 3 need the SEO-gate
retrofit, **6 of 15 screens UNSPEC'D** (home, competition hub, browse, leaderboards, h2h, glossary) ·
**Real data** consuming ✅ · **Hosting** LIVE, only the trigger shape + go-public left · **Legal** not
started, imprint blocks publication · **CPO** imprint operator/address.
Marts + metric layer are DONE and gated; do not reopen.

## ⚠️ v2 makes third-party requests TODAY
`Crest`/`PlayerRow` render `media.api-sports.io` as `<img>` — the defect that took the MVP offline.
Fix = mirror crests to our origin (fixes privacy, not the rights half).

## OWED — deferred, not forgotten (must survive rewrites)
- **The agent set** — a ui-BUILDER (draft on `feat/expert-agents-that-build`);
  `football-analytics-expert` + `data-journalist` as real CONSULTANT agents (generic-agent +
  role-brief roleplay works but is a workaround); a fan probe on the rendered page.
- **The metric-change skill** (one team metric touched SIX files) · **mirror the crests** ·
  **legal-counsel consultant** (API-Football terms) · **reviewers as peers** (#822 shipped only the
  model-in-routing half) · **amend `metrics_display.md`** for the 2 metrics #804 surfaced (§10).

## DONE (history is in git — only still-live gotchas kept)
Filed 2026-07-27/28: **#838–#841, #843–#846, #848, #850–#853**; #842 + #847 + #854 merged. #753 carries
the player design state. Metric layer (#802/#803/#804) complete.
- ⚠️ `appearances` = played legs (`minutes_played > 0`), not squad appearances.
- ⚠️ `astro build` OOMs at full scale — needs `--max-old-space-size=8192`; before a local dev build
  run `git clean -fX site_v2/src/data`.
- ⚠️ team-page footer says "Sample data" on real data (confirm intended).
- No player photos (CPO). API-Football licensing: reselling is the one hard prohibition.

## NEXT — the PR A→D table in ⭐ CURRENT §0 is the sequence. Then:
1. **Player branch merges** (needs #846 + #845), then Performance → Career, one tab at a time, each
   content boundary decided before mocking.
2. Home page (mock `1c35e7aa` is reference only), **then legal/imprint**, then launch.
3. Follow-ups: route `seo-expert-reviewer` (governance); em-dash sweep in `strings.ts`;
   `src/data/README.md` stale; `content_architecture.md` cites GAP-22 (should be GAP-20); fixture
   PlayerRow "1 assists" singular i18n; #833; the 4-way locale-list duplication.

## OPEN — the CPO's alone
- **Imprint operator + address** — blocks publication (#799); get a lawyer, never conclude it.
  Publish-time only; does NOT block building.
- **Hosting recurring run** — only the trigger shape is left; go-public is imprint-blocked.
- **The feedback Apps Script** (his Google account, unreachable) — #687.
- **#850's alias decision** — which duplicate team record is canonical. PR D freezes the URLs.

## DO NOT (standing)
- Do NOT treat the 114-issue tracker as agreed work; re-validate before acting.
- Do NOT write another planning document (the tracker + this file are the plan). Filling a frontend
  SPEC is the task, not a planning doc.
- Do NOT touch `site/` (retired/frozen). Do NOT build a page the CPO has not approved.
- Do NOT derive facts in the export or frontend — select/group/rename only.
- **Never merge a PR. The CPO merges. Branch from main; never commit to main.**
- Communication: plain language, lead with the decision, no em dashes, no walls of text.
- Do NOT ask the CPO to adjudicate what a rule can settle. He has said so twice. Bring a rule that
  runs itself, or say plainly that none exists and name the cost.

## Operational notes
- **dbt CLI is broken locally. SQLFluff is NOT** — only its dbt templater is (it needs GCP). Saying
  both cost a CI round-trip on #854. **Lint before pushing, from the REPO ROOT** (the root `.sqlfluff`
  has the jinja macro path; `dbt_project/.sqlfluff` does not yet):
  `python -m sqlfluff lint <model> --templater jinja --dialect bigquery`, FULL rule set — a `--rules`
  subset missed ST06 on #854. Also `python scripts/check_layer_contract.py`. BigQuery rejects a
  FROM-less WHERE. `sqlfluff fix` is safe here and settles LT02 layout.
- **A wildcard is fine over ONE ref; add a join and AM04 fires.** Enumerate columns — the repo has
  **zero `noqa`**, do not add the first. Nesting ceiling is ≈8 function calls (parse depth 255).
- **Frontend:** `site_v2` is Astro; `npm run build` needs `NODE_OPTIONS=--max-old-space-size=8192` at
  full scale; `deploy-site-v2.yml` (manual-only) does export → build → firebase deploy. The in-app
  Browser pane is unreliable — `file://` "opens" but every screenshot then fails. Do not spend turns
  on it. **Artifact delivery works** with the three rules in "⭐ CURRENT" (one tab, new URL, both).
- **Commit mechanics:** `git commit` runs alone (no chaining); `--amend` gate-blocked; **no double
  quotes in the message** — the form gate parses them as pathspecs and denies the commit. A
  post-commit hook auto-pushes and opens the PR. `review.md` must be COMMITTED or CI reads the
  previous task's stale hash. Collapse: `git reset --soft HEAD~1`, re-stage, recompute hash, re-run
  reviewers, rewrite `review.md`, commit, `git push --force-with-lease`.
- **Contract edits need a CLEAN tree** — stash-dance with explicit paths (`git stash push -- <files>`;
  `git add` a NEW file first or the pathspec fails) so the player-Overview stash is untouched.
- **⚠ `scope_paths` uses `fnmatch`, so `[lang]`/`[team]` are CHARACTER CLASSES.** A literal Astro
  dynamic-route path can NEVER match itself — use `site_v2/src/pages/*/teams/*.astro` etc. Every v2
  route is dynamic, so this bites every frontend contract.
- **⚠ `src/pages/index.astro` is DEAD CODE.** Astro's i18n `prefixDefaultLocale` generates its own root
  redirect that overwrites it — the shipped `/index.html` is Astro's stub (and it already emits a
  correct `<link rel="canonical">`). Editing that file changes nothing that ships.

## Verified state reference
- **Live to users:** no PUBLIC site. v2 is on `football-data-pipeline-gcp.web.app` (unlisted).
  **Nothing is published — which is why URLs are still free to change.**
- **v2 built:** design system (`system.css` + 26 components), fixture page, team page (3 tabs), nav
  shell (#825), page-spec contract (#826). `.shell`/`.page-grid`/`.rail` exists, wired into zero
  pages; team/fixture stay at 680px `.inner`.
- **Datasets:** base models + seeds in `dbt_analytics`; also `staging`, `core`, `marts`, `ci_*`.
  `generate_schema_name` prefixes non-prod targets, but **never run a local `dbt build`.**
