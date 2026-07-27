# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Must stay under
> 16,000 characters (the SessionStart hook's injection budget).

_Last updated **2026-07-27** (late). main GREEN at **f0ac5aa**. **THE PLAN CHANGED TWICE THIS
SESSION.** **(1) SEO is now a BUILD GATE (#844)**, not an occasional review — CPO ruling — and it is
the next major work. **(2) The player page is now FOUR tabs (#848)**, the fourth conditional. The
Overview tab is **BUILT but UNCOMMITTED in a git stash, with a known-wrong default rule**, held on
#845 + #846. **FIRST ACTIONS: read "⭐ CURRENT", check `git stash list` before any git work, read
#848 before shaping the International tab.** Firebase deploy LIVE + verified (manual, not public)._

## THE GOAL
**The new website live.** ~2–3 weeks; **quality over speed** (CPO 2026-07-22).

## ⭐ CURRENT — SEO is a BUILD GATE (#844). Player Overview built but HELD.

### 1. THE RULING THAT CHANGED THE PLAN (2026-07-27)

CPO: *"This is not an ad-hoc situation where we occasionally run the SEO expert. SEO optimization has
to be ensured during the whole process of building the website."* A reviewer is after-the-fact and
cannot ensure anything.

**#844 — extend #826's page-spec contract so no page BUILDS without declaring its SEO surface**:
canonical + hreflang, title/description **uniqueness across the generated set** (presence is
worthless at scale), schema.org type, **inbound hub + outbound edges**, page-count driver
(`entity × dimensions × locale`), and the minimum-data gate. Then every future page type — analysis,
predictions, anything — inherits it by construction.

**This REORDERS the locked sequence: #369 becomes a prerequisite for the remaining pages**, because
each page built before the gate is a page to retrofit. Fixture, team and player all need retrofitting
already (`Layout.astro` has no canonical, no hreflang, no structured data; it sets `noindex`, correct
until cutover #377).

**Siblings, all filed today:** **#845** minimum-data gate (what earns a page) · **#843** slugs are
recomputed from the current name every export, so a rename changes every URL and loses its equity,
and the alias §3 promises does not exist · **#846** window selection in the frontend.

**`seo-expert-reviewer` exists (merged, #842) but is INERT** — absent from `.claude/review_routing.json`,
so it fires on nothing. Routing it is an **open governance ask** (protected file).

### 2. ⭐ NEW: the player page is FOUR tabs (#848, CPO-agreed 2026-07-27)

| Tab | Lens | Shown |
|---|---|---|
| Overview · Performance · Career | **club only** | always |
| **International** | **national** | **only when `national_appearances_total >= 1`** |

**A tab, not a lens toggle** — a toggle is a control a crawler cannot follow, so the national lens
would have no URL for a real search intent. The condition is a **served fact**, so ingesting more
national data (friendlies are NOT ingested yet) makes the tab appear with zero template change.

**The International tab carries a competition selector + PERFORMANCE, not just counts.** The agent
proposed omitting both, claiming national peer groups were too small; **checked and false** — WC 2026
already has 314 players with benchmark rows (DEF 136, MID 99, GK 41, ATT 38), larger than most
leagues. The CPO's test question ("how did Mbappé perform at WC 2026 — where does the site say?") had
no answer without it. **Full decision + rationale on #848 — read it before shaping the tab.**

**Four consequences NOT actioned (all CPO-class):** wireframe 13's Career must hand over its National
team section · `content_architecture.md` §4 states a DIFFERENT settled tab set · no wireframe file
exists for this screen · #846 changes shape.

### 3. ⚠️ THE PLAYER OVERVIEW IS BUILT BUT UNCOMMITTED — IN A STASH, WITH A KNOWN-WRONG RULE

```
git stash list     # "feat/player-overview-tab: Overview BUILT; page default rule is WRONG (seasons[0]=WC) …"
git checkout feat/player-overview-tab && git stash pop
```

**Do NOT rebuild it — it exists.** Build green, 447 tests green, `bi-analyst-reviewer` and
`scope-auditor` PASS on it. Uncommitted because the gate rejects a FAIL.

**⚠️ Its default-season rule is WRONG as stashed.** It uses `seasons[0]` = most recent of ANY
competition, so both sample players open on **World Cup 2026** with their national side. Under #848
the club tabs are club-only, so the rule must be *the most recent CLUB season*. Do not ship the
stashed rule.

**Held on:**
- **#845** — the deploy exports `teams,fixtures` only, so shipping puts **hundreds of real dead links
  on the LIVE team page**. Adding `players` means **154,644 pages** against a build already needing
  8GB at a sixteenth of that. **CPO chose (d): hold until the gate defines what earns a page.**
- **#846** — now scoped as: **the payload must carry the lens per season, and which club season is
  featured.** The frontend may not decide it (window selection, forbidden by `layering.md`) and
  neither may the export — **the export is the consumption layer too**. So it is a mart change.
  Rule to serve: most recent `entity_type='club'` season; tie-break within a year still undecided
  (Rogers has UEL, PL and FAC all in 2025).

**What the build proved (three defects only building could find):** the featured season landed on a
**World Cup** for an international · `system.css` had **no reveal rule for a `career` tab**, so the
third tab could never open (fixed) · link resolution was a glob over committed files, which the CPO
rejected — links are now data-driven from payload slugs the export carries.

**Design state: the authority is #753's design-state comment**, which splits every item by who decided
it (A decided / B CPO direction / **C STILL OPEN — do not build from these** / D findings / E deps /
F recommendation). Everything in section C is still open, including the tab-vs-URL question.

**RENDER FAILURE: DIAGNOSED. Keep doing all three:** show ONE tab at a time (no hidden panels),
publish to a **NEW** artifact URL (never republish), deliver via Artifact **and** SendUserFile.

**Not in the branch, still owed:** the chip/pill sizing change the CPO approved (`.cchip` fixed 44px
so both pill groups are 140px and align, label before each group) — deliberately a separate PR
because it edits shipped `system.css` and affects the LIVE team page.

**Data deps.** **#840** (club match count for "37 of 38"; rank YoY + sign convention) · **#838**
(points is a synthetic 3-1-0 tally in EVERY competition: FA Cup renders 0, UEL renders 32 against a
real league-phase 18) and **#839** (phase spike — tables vs brackets) block the **TEAM** Overview's
cup behaviour, not the player page · **#841** (pass accuracy 23–30% since 2022 vs 72–73% before)
blocks player **PERFORMANCE**.

## Phase B — DONE (2026-07-26)
#825 global header/footer shell (mock `87d14109`; breakpoints 700/900/1010px) · #827 bi-analyst now
requires rendered-page evidence for `site_v2/src/**` · #826 page-spec contract, build refuses an
underspecified page (**this is the mechanism #844 extends**). Home mock `1c35e7aa` = reference only.

**Reserved (CPO §10, standing):** nav order · search style · desktop RAIL per page type · footer/legal
(imprint-blocked) · default-theme policy. **Deferred:** component/metric catalogue, import-boundary
rule, one-page driver (#828).

## DESIGN DISCIPLINE (the weak spot — read every time)
- **Compose from the locked `system.css` ONLY.** Refs: `be7bd6d3` · fixture `d70aae67` · team
  `f6348775`. Player mock `6c21ef71` NOT approved.
- **READ THE DOCS FIRST, don't assert.** This session: proposed an architecture from 3 competitions
  (surveying all 44 refuted 3 of its 4 claims); missed that the club/national split was already
  modelled in `competition_types.csv`; claimed national peer groups were too small (WC 2026 has 314
  ranked players). Every one was one query away.
- **Design for the DEFAULT case, not an edge case** — the page was built around a goalkeeper because
  the open question happened to be about keepers; two conclusions were wrong until rebuilt outfield.
- **Never fill an empty slot to balance a layout** (cards in a strip, the invented hero of 07-21).
- **Build it and show it** — a mock IS the decision; never ask about something visual in words.
- **Real data only** — honest empty states; "no hero, not shippable" is RETRACTED.
- **Multi-tab pages: write the per-tab content boundary FIRST, build ONE tab at a time.** Check ALL
  sibling wireframes + the shipped tab component, not one file.

## WHERE WE STAND — five launch groups
| # | Group | Status |
|---|-------|--------|
| 1 | **Pages** | 2 of 5 built (fixture + team); player Overview built but HELD (see ⭐ CURRENT). All 3 need SEO-gate retrofit. 6 of 15 screens UNSPEC'D (home, competition hub, browse, leaderboards, h2h, glossary). |
| 2 | **Real data** | consuming ✅ (export → build → deploy). |
| 3 | **Hosting** | LIVE + verified. Recurring trigger (cost measured negligible) + go-public still gated (OPEN). |
| 4 | **Legal** | not started; imprint blocks publication. |
| 5 | **CPO decisions** | imprint operator/address (blocks going public). |

Marts + metric layer are DONE and gated — not launch work; do not reopen.

## ⚠️ v2 makes third-party requests TODAY
Committed sample data + `Crest`/`PlayerRow` render `media.api-sports.io` as `<img>` — the exact defect
that took the MVP offline. Fix = mirror crests to our origin (fixes the privacy half, not the rights
half). (The foundation mock uses text initials — no third-party requests.)

## OWED — deferred, not forgotten (must survive rewrites)
- **The agent set** — a ui-BUILDER/design-implementer (draft on `feat/expert-agents-that-build`,
  merged into main history); `football-analytics-expert` + `data-journalist` as real CONSULTANT
  agents (used as generic-agent + role-brief roleplay this session — works, but is a workaround,
  not the built thing); a fan probe on the rendered page. **Unverified:** do subagent tool calls
  fire the main session's hooks? TEST, don't assume.
- **The metric-change skill** — adding one team metric touched SIX files.
- **Mirror the crests** (§ above, third-party requests).
- **Amend the locked display contract** (`metrics_display.md`, 16-row team table) for 2 metrics
  #804 surfaced. §10.
- **legal-counsel consultant** — risk register from the API-Football terms.
- **Reviewers as peers** (not one reviewer over every diff) — #822 shipped the model-in-routing
  half; the peer split is still owed.

## DONE (history — detail in git)
- **2026-07-27:** player Overview designed AND built; render failure diagnosed; SEO re-scoped to a
  build gate; player page re-scoped to 4 tabs. **Issues filed: #838 #839 #840 #841 #843 #844 #845
  #846 #848**; #842 (SEO role) and #847 (handover) merged. #753 carries the full design state.
- **2026-07-26:** Phase B complete (#825/#827/#826); frontend spec audit; foundation mock approved.
- **2026-07-25:** Firebase deploy LIVE + verified; export cost ~$0.002/run; #822 effort pins merged.
  ⚠️ team-page footer says "Sample data" on real data (confirm intended).
- **2026-07-24:** team page (3 tabs) + real-data wiring. ⚠️ `appearances` = played legs
  (`minutes_played>0`). ⚠️ `astro build` OOMs at full scale — needs
  `--max-old-space-size=8192`; before a local dev build run `git clean -fX site_v2/src/data`.
- **2026-07-22:** #802/#803/#804 (metric layer). No player photos (CPO). API-Football licensing:
  reselling is the one hard prohibition. Lessons: fix the CLASS not the instance; verify the real
  tree.

## NEXT — RE-SEQUENCED 2026-07-27 (SEO gate now precedes the remaining pages)
1. **#846 §10 classification (CPO owes this)** — warehouse fact or display default? Unblocks the
   player branch's second hold.
2. **#844 SEO build gate + #845 minimum-data gate.** The prerequisite: every page built before the
   gate is a page to retrofit. #845 also decides what enters the deploy's `--entities`.
3. **Retrofit fixture/team/player against the gate; then the player branch merges** and Performance
   → Career follow, one tab at a time, each boundary decided before mocking.
4. Then the home page (mock `1c35e7aa` is reference only), **then legal/imprint**, then launch.
5. Small follow-ups: route `seo-expert-reviewer` (governance); em-dash sweep in `strings.ts`;
   `site_v2/src/data/README.md` stale; `content_architecture.md` cites GAP-22 (should be GAP-20);
   fixture PlayerRow "1 assists" → singular i18n; #833.

## OPEN — the CPO's alone
- **Imprint operator + address** — blocks publication (#799); get a lawyer, never conclude it.
  Publish-time only; does NOT block building.
- **Hosting recurring run** — cost negligible; only the trigger shape left. Go-public =
  imprint-blocked.
- **The feedback Apps Script** (his Google account, unreachable) — #687.

## DO NOT (standing)
- Do NOT treat the 114-issue tracker / its milestones as agreed work; re-validate before acting.
- Do NOT write another planning document (the tracker + this file are the plan). A frontend SPEC
  (chrome/layout/09_chrome) is NOT a planning doc — filling it is the task.
- Do NOT touch `site/` (retired/frozen 2026-07-21, offline).
- Do NOT build a page whose design the CPO has not approved.
- Do NOT derive facts in the export or frontend — select/group/rename only.
- **Never merge a PR. The CPO merges. Branch from main; never commit to main.**
- Communication: plain language, lead with the decision, no em dashes, no walls of text.

## Operational notes
- **dbt CLI + SQLFluff BROKEN locally** — `ci-data-build` is the real gate; offline you can run
  `python scripts/check_layer_contract.py` + read SQL. BigQuery rejects a FROM-less WHERE.
- **Frontend:** `site_v2` is Astro; `npm run build` needs `NODE_OPTIONS=--max-old-space-size=8192` at
  full scale; the deploy workflow (`.github/workflows/deploy-site-v2.yml`, manual-only) does
  export → build → firebase deploy. The in-app Browser pane is unreliable here — `navigate` to a
  `file://` path "opens" it but every screenshot / read_page then fails with "No site is open".
  Do not spend turns on it. **Artifact delivery works** when the three rules in "⭐ CURRENT" are
  followed (one tab, new URL, both channels).
- **Commit mechanics:** ONE substantive commit per PR; `git commit` runs alone (no chaining);
  `--amend` gate-blocked. Collapse: `git reset --soft HEAD~1`, re-stage, recompute hash vs main
  (`python .claude/hooks/git_discipline.py --staged-hash`), re-run required reviewers, rewrite
  `review.md`, commit, `git push --force-with-lease`.
- **Standing metric ruling:** a metric's formula is fixed math; never put coalesce/countif/null-gate in
  a `*_expr`.

## Verified state reference
- **Live to users:** no PUBLIC site. v2 deployed to `football-data-pipeline-gcp.web.app`
  (reachable, unlisted, not announced).
- **v2 built:** design system (`system.css` + 26 components), fixture page, team page (3 tabs),
  nav shell + responsive layout (#825), page-spec contract (#826, every real page declares
  blocks/marts/i18n keys, checked at build time). `.shell`/`.page-grid`/`.rail` exists, wired into
  zero pages; team/fixture stay at locked 680px `.inner`.
- **Automation:** session default Opus+high in gitignored `settings.local.json`; review-fleet
  effort pinned (#822) — see [[reference-model-effort-automation]].
- **Metric layer:** all 78 catalogue rows carry `direction` + `interpretation`; six guards.
