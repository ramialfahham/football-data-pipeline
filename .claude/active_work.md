# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> chars (the SessionStart hook's budget).

_Last updated **2026-07-27** (latest). main GREEN at **92474bc**. **IN FLIGHT: branch
`feat/team-name-corrections` = PR A of a FOUR-PR sequence (see ⭐ CURRENT §0). Built + verified, not
yet committed.** SEO is a BUILD GATE (#844) but is **PR C, not next** — two independent reviewers
found it was never blocked. The player page is FOUR tabs (#848); its Overview is **BUILT but
UNCOMMITTED in git stash@{0} with a known-wrong default rule**, held on #845 + #846. **FIRST ACTIONS:
read "⭐ CURRENT" §0, run `git stash list` before any git work, read #848 before shaping the
International tab.** Firebase deploy LIVE + verified (manual, not public)._

## THE GOAL
**The new website live.** ~2–3 weeks; quality over speed (CPO 2026-07-22).

## ⭐ CURRENT — four PRs. PR A in flight. #844 is PR C, not next.

### 0. THE SEQUENCE (2026-07-27, after two independent assessments)

CPO: *"there is no aston-villa-66."* Chasing that exposed that **`dim_team` is a passive
pass-through** — the provider's short name is the ONLY team name in the product and drives the
fixture card, the H1, the `<title>`, the meta description **and the slug**, across team/player/coach/
country. **#850 #851 #852 #853 filed.** Two reviewers judged the resulting plan over-scoped; split:

| PR | Scope | Blocks #844? |
|---|---|---|
| **A** ← IN FLIGHT | #850 names: seed + join in `base_apif__teams_global` + tests | it *enables* it |
| **B** | Drop the id — slug **DERIVED** in the warehouse, no persisted table, warehouse stays reproducible | no |
| **C** | **#844 SEO build gate** (design approved, artifact `4fe25734`) | — |
| **D** | Pre-launch with #799/#377: persistence, the freeze, **and** the `firebase.json` redirects #843 needs | no |

**#844 was never blocked** — a spec declares the canonical *template*, not the value, so a slug
change touches no spec. The "#850 must land first" claim is FALSE and retracted on #852, **now PR D**.

**PR A state: PR 854 is OPEN**, both reviewers PASS (round 2). Verified 3,249 rows in/out so no
fan-out, 14 corrections land, `check_layer_contract` + 447 tests pass.

**Rulings:** base prepares / the core dim publishes · **E3 = TRANSLITERATE** not strip (`ß→ss`,
`œ→oe`, `ı→i`, `ə→e`; `Rot-Weiß Essen`→`rot-weiss-essen`) — escalations.log:45, PR B · **E2 = the
warehouse** produces slugs · ONE locale-independent slug (`bayern-munchen` everywhere).

**Carry into PR B:** country anchor corrupted — 39 teams lack a country but **22 have one in
`stg_apif__teams`**; `qualify row_number()` takes one league's row whole, and which wins depends on
ingest timestamps (`Nacional` is live) · `slug_map` is a flat dict, so **90 player kebabs equal coach
kebabs** · players give 12,551 id-suffixed URLs, `kebab(NULL)`=`''` for 11,665 ·
**`macros/team_name_normalization.sql` exists, zero callers.**

### 1. WHY #844 EXISTS (still the ruling, now PR C)

CPO: *"This is not an ad-hoc situation where we occasionally run the SEO expert. SEO optimization has
to be ensured during the whole process of building the website."* A reviewer is after-the-fact and
cannot ensure anything.

**#844 — extend #826's page-spec contract so no page BUILDS without declaring its SEO surface**:
canonical + hreflang, title/description **uniqueness across the generated set** (presence is
worthless at scale), schema.org type, **inbound hub + outbound edges**, page-count driver, and the
minimum-data gate. Design approved, three parts (declare at `prebuild` / verify at `postbuild` over
`dist/` / a minimal emitter in `Layout.astro`) — **full design on #844 + artifact `4fe25734`**.
Uniqueness only exists after generation, so the half that matters cannot be a prebuild check.
`Layout.astro` today has no canonical, no hreflang, no structured data (`noindex` is correct until
#377); fixture + team retrofit inside PR C or main ships red.

**Siblings:** **#845** minimum-data gate (what earns a page) · **#843** reframed — the URL is derived
from an unverified mutable field, not merely "changes on rename" · **#846** window selection in the
frontend.

**`seo-expert-reviewer` exists (merged, #842) but is INERT** — absent from `.claude/review_routing.json`,
so it fires on nothing. Routing it is an **open governance ask** (protected file).

### 2. The player page is FOUR tabs (#848, CPO-agreed 2026-07-27)

Overview · Performance · Career = **club only**, always shown. **International = national lens, shown
only when `national_appearances_total >= 1`.**

**A tab, not a lens toggle** — a crawler cannot follow a control, so the national lens would have no
URL. The condition is a **served fact**, so ingesting more national data (friendlies are NOT ingested)
makes the tab appear with zero template change. **It carries a competition selector + PERFORMANCE, not
just counts** — the "peer groups are too small" objection was checked and is false (WC 2026 has 314
ranked players). **Full decision + rationale on #848 — read it before shaping the tab.**

**Four consequences NOT actioned (all CPO-class):** wireframe 13's Career hands over its National team
section · `content_architecture.md` §4 states a DIFFERENT settled tab set · no wireframe file exists
for this screen · #846 changes shape.

### 3. ⚠️ PLAYER OVERVIEW IS BUILT BUT UNCOMMITTED — IN stash@{0}, WITH A KNOWN-WRONG RULE

```
git stash list     # "feat/player-overview-tab: Overview BUILT; page default rule is WRONG (seasons[0]=WC) …"
git checkout feat/player-overview-tab && git stash pop
```

**Do NOT rebuild it — it exists.** Build green, 447 tests green, `bi-analyst-reviewer` and
`scope-auditor` PASS. Uncommitted because the gate rejects a FAIL.

**⚠️ Its default-season rule is WRONG as stashed:** `seasons[0]` = most recent of ANY competition, so
both sample players open on **World Cup 2026** with their national side. Under #848 the club tabs are
club-only, so it must be the most recent CLUB season. Do not ship it.

**Held on:**
- **#845** — the deploy exports `teams,fixtures` only, so shipping puts **hundreds of real dead links
  on the LIVE team page**. Adding `players` = **154,644 pages** against a build already needing 8GB at
  a sixteenth of that. **CPO chose (d): hold until the gate defines what earns a page.**
- **#846** — **the payload must carry the lens per season, and which club season is featured.** Not
  the frontend (window selection) and not the export (**consumption too**), so it is a mart change.
  Serve the most recent `entity_type='club'` season; the within-year tie-break is undecided (Rogers
  has UEL, PL and FAC all in 2025).

**#753's design-state comment is the authority. Everything in its section C is still open — do not
build from those**, including tab-vs-URL.

**RENDER FAILURE: DIAGNOSED. Keep all three:** ONE tab at a time (no hidden panels), a **NEW**
artifact URL (never republish), deliver via Artifact **and** SendUserFile.

**Still owed:** the CPO-approved chip/pill sizing (`.cchip` fixed 44px so both pill groups are 140px
and align, label before each group) — a separate PR: it edits shipped `system.css`.

**Data deps.** **#840** (club match count for "37 of 38"; rank YoY + sign convention) · **#838**
(points is a synthetic 3-1-0 tally in EVERY competition: FA Cup renders 0, UEL renders 32 against a
real league-phase 18) and **#839** (phase spike — tables vs brackets) block the **TEAM** Overview's
cup behaviour, not the player page · **#841** (pass accuracy 23–30% since 2022 vs 72–73% before)
blocks player **PERFORMANCE**.

## Phase B — DONE (2026-07-26)
#825 header/footer shell (breakpoints 700/900/1010px) · #827 bi-analyst requires rendered-page
evidence for `site_v2/src/**` · #826 page-spec contract (**the mechanism #844 extends**). Home mock
`1c35e7aa` = reference only.

**Reserved (CPO §10, standing):** nav order · search style · desktop RAIL per page type · footer/legal
(imprint-blocked) · default-theme policy. **Deferred:** component/metric catalogue, import-boundary
rule, one-page driver (#828).

## DESIGN DISCIPLINE (the weak spot — read every time)
- **Compose from the locked `system.css` ONLY.** Refs: `be7bd6d3` · fixture `d70aae67` · team
  `f6348775`. Player mock `6c21ef71` NOT approved.
- **READ THE DOCS AND QUERY THE DATA FIRST, don't assert.** Logged misses: an architecture proposed
  from 3 of 44 competitions (one query refuted 3 of its 4 claims); the club/national split was
  already in `competition_types.csv`; "national peer groups are too small" (WC 2026 has 314 ranked
  players); **"Glasgow Rangers"** asserted from memory (never the club's official name);
  **"18.5% of players collide"** measured on the wrong column (it is 1.6%). Every one was one query
  or one file read away.
- **Design for the DEFAULT case, not an edge case** — the page was built around a goalkeeper and two
  conclusions were wrong until it was rebuilt on an outfielder.
- **Never fill an empty slot to balance a layout** (cards in a strip, the invented hero of 07-21).
- **Build it and show it** — a mock IS the decision; never ask about something visual in words.
- **Real data only** — honest empty states; "no hero, not shippable" is RETRACTED.
- **Multi-tab pages: write the per-tab content boundary FIRST, build ONE tab at a time.** Check ALL
  sibling wireframes + the shipped tab component, not one file.

## WHERE WE STAND — five launch groups
1. **Pages** — 2 of 5 built (fixture + team); player Overview built but HELD. All 3 need the SEO-gate
   retrofit. **6 of 15 screens UNSPEC'D**: home, competition hub, browse, leaderboards, h2h, glossary.
2. **Real data** — consuming ✅ (export → build → deploy). 3. **Hosting** — LIVE + verified; only the
   recurring trigger shape and go-public are left. 4. **Legal** — not started; imprint blocks
   publication. 5. **CPO decisions** — imprint operator/address.

Marts + metric layer are DONE and gated — not launch work; do not reopen.

## ⚠️ v2 makes third-party requests TODAY
`Crest`/`PlayerRow` render `media.api-sports.io` as `<img>` — the exact defect that took the MVP
offline. Fix = mirror crests to our origin (fixes privacy, not the rights half).

## OWED — deferred, not forgotten (must survive rewrites)
- **The agent set** — a ui-BUILDER (draft on `feat/expert-agents-that-build`);
  `football-analytics-expert` + `data-journalist` as real CONSULTANT agents (generic-agent +
  role-brief roleplay works but is a workaround); a fan probe on the rendered page.
  **Unverified:** do subagent tool calls fire the main session's hooks? TEST, don't assume.
- **The metric-change skill** — adding one team metric touched SIX files.
- **Mirror the crests** · **legal-counsel consultant** (API-Football terms risk register) ·
  **reviewers as peers** (#822 shipped only the model-in-routing half) · **amend
  `metrics_display.md`** for the 2 metrics #804 surfaced (§10).

## DONE (history is in git — only still-live gotchas kept)
Issues filed 2026-07-27: **#838–#841, #843–#846, #848, #850–#853**; #842 + #847 merged. #753 carries
the player design state. Phase B (#825/#827/#826) and the metric layer (#802/#803/#804) are complete.
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

## DO NOT (standing)
- Do NOT treat the 114-issue tracker as agreed work; re-validate before acting.
- Do NOT write another planning document (the tracker + this file are the plan). A frontend SPEC is
  NOT a planning doc — filling it is the task.
- Do NOT touch `site/` (retired/frozen, offline). Do NOT build a page the CPO has not approved.
- Do NOT derive facts in the export or frontend — select/group/rename only.
- **Never merge a PR. The CPO merges. Branch from main; never commit to main.**
- Communication: plain language, lead with the decision, no em dashes, no walls of text.
- Do NOT ask the CPO to adjudicate what a rule can settle. He has said so twice. Bring a rule that
  runs itself, or say plainly that none exists and name the cost.

## Operational notes
- **dbt CLI is broken locally. SQLFluff is NOT** — only its dbt templater is (it needs GCP). This
  note used to say both and it cost a CI round-trip on PR 854. **Lint before pushing:**
  `cd dbt_project && python -m sqlfluff lint <model> --templater jinja --dialect bigquery`.
  It catches AM04/LT02, which is what `ci-data-build` failed on. Also run
  `python scripts/check_layer_contract.py`. BigQuery rejects a FROM-less WHERE.
- **A wildcard is fine over ONE ref; add a join and AM04 fires** ("unknown number of result
  columns"). Enumerate the columns — the repo has **zero `noqa`**, do not add the first.
- **Frontend:** `site_v2` is Astro; `npm run build` needs `NODE_OPTIONS=--max-old-space-size=8192` at
  full scale; `deploy-site-v2.yml` (manual-only) does export → build → firebase deploy. The in-app
  Browser pane is unreliable — `file://` "opens" but every screenshot then fails. Do not spend turns
  on it. **Artifact delivery works** with the three rules in "⭐ CURRENT" (one tab, new URL, both).
- **Commit mechanics:** `git commit` runs alone (no chaining); `--amend` gate-blocked; **no double
  quotes in the message** — the form gate parses them as pathspecs and denies the commit. A
  post-commit hook auto-pushes and opens the PR. `review.md` must be COMMITTED or CI reads the
  previous task's stale hash. Collapse: `git reset --soft HEAD~1`, re-stage, recompute hash, re-run
  reviewers, rewrite `review.md`, commit, `git push --force-with-lease`.
- **Contract edits need a CLEAN tree** — stash-dance with explicit paths
  (`git stash push -- <files>`) so the player-Overview stash is not disturbed.
- **Standing metric ruling:** a metric's formula is fixed math; never put coalesce/countif/null-gate in
  a `*_expr`.

## Verified state reference
- **Live to users:** no PUBLIC site. v2 deployed to `football-data-pipeline-gcp.web.app` (reachable,
  unlisted, not announced). **Nothing is published — which is why URLs are still free to change.**
- **v2 built:** design system (`system.css` + 26 components), fixture page, team page (3 tabs), nav
  shell (#825), page-spec contract (#826 — the mechanism #844 extends).
  `.shell`/`.page-grid`/`.rail` exists, wired into zero pages; team/fixture stay at 680px `.inner`.
- **Automation:** session default Opus+high in gitignored `settings.local.json`; review-fleet effort
  pinned (#822). **Metric layer:** 78 rows carry `direction` + `interpretation`; six guards.
- **Datasets:** base models + seeds live in `dbt_analytics`; staging in `staging`; `core`; `marts`.
  CI shares prod datasets, so **never run a local `dbt build`.**
