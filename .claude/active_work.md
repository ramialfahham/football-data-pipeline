# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Must stay under
> 16,000 characters (the SessionStart hook's injection budget).

_Last updated **2026-07-26**. main GREEN at **fb3a1a4**. **CURRENT TASK: build the frontend FOUNDATION** (shared shell + responsive system) — design APPROVED via mock, build NOT started. Firebase deploy is LIVE + verified (manual, `.web.app`, not public)._

## THE GOAL
**The new website live.** ~2–3 weeks; **quality over speed** (CPO 2026-07-22).

## ⭐ CURRENT TASK — build the frontend FOUNDATION — issue #825 (start here)
**Why this, not more pages:** a spec audit (2026-07-26) found the frontend is systematic on DATA +
CONTENT but improvisational on LAYOUT, CHROME, and page-production — so every page became a one-off.
**CPO decision 2026-07-26: foundation-first, lean process.** Stop building pages until the shared
frame exists.

**Design is APPROVED** (mock, CPO "looks good for now"): foundation mock = artifact
`87d14109-c6ff-41d2-a3bf-eb59d4e46459`; home-content mock = `1c35e7aa-eca6-44a5-9cbb-b3382fb27c90`.
If a mock link is unreachable, the written build spec below + the locked refs (`be7bd6d3` / `d70aae67`
/ `f6348775`) are enough to build from. Build = turn the mock into the real shared shell, composing
ONLY from the locked `system.css` (no new identity):
- **`site_v2/src/layouts/Layout.astro`** gains a global header (logo `MatchdayIQ` + main nav
  `Competitions · Matches · Teams · Players · Standings · Stats` + search + a WORKING dark/light
  theme toggle) + a footer (links, EN·DE·FI, an imprint slot = pending). Today Layout is a bare
  `<slot>` hardcoded to `data-theme="dark"`.
- **`site_v2/src/styles/system.css`** gains the RESPONSIVE layout system it never had (its only media
  query today is `prefers-reduced-motion`): nav inline **≥700px** (hamburger drawer below), two-column
  page grid (main + rail, max **~1100px**) **≥900px**, search field **≥1010px** (icon below). The
  fixture/team/player wireframes ALREADY specify "≥900px two columns, max ~1100px" — never built.
- **Write the two missing specs:** `docs/wireframes/09_chrome.md` (never written) + a layout-system
  section (grid / breakpoints / max-widths).
- **Touches the 2 built pages** (team, fixture) — they inherit the new frame; verify they still render.
- Plan-mode it; review cycle = cto-reviewer (shell/config) + bi-analyst-reviewer (`site_v2/src/**`).

**Reserved (CPO §10, NOT decided in build):** exact nav contents/order (the listed order is the
specified start — refine only on CPO word) · search style · what fills the
desktop RAIL per page type (home = standings/trending/scorers) · footer/legal (imprint-blocked) ·
default-theme policy (dark-fixed vs follow-OS). **Approved this session:** widen desktop to two-column
~1100px; dark default + light toggle; the nav list; the breakpoints above.

**Then Phase B (lean process):** add ONLY a schema-validated page-spec contract (#826) + a sharpened
rendered-page reviewer (#827). DEFER: component catalogue, import-boundary rule, one-page driver (#828).
**Then Phase C: build pages one at a time** — **player FIRST** (fully spec'd + data-ready, no design
debate), then home in the new frame.

**Borrowed core** (from `github.com/ramialfahham/backtobayesics`, right-sized, NO autonomy):
page-spec-as-schema-contract; generated component/metric catalogue; import isolation (pages→components
only); blind default-FAIL reviewer of RENDERED pages (name 2 verified risks); a one-page-at-a-time
driver keyed to the tracker. Their repo oversells (2 of ~50 pages actually built) — copy ideas, not
vapourware.

## DESIGN DISCIPLINE (the weak spot — read every time)
- **Compose from the locked `system.css` ONLY. Never invent a per-page treatment.** Three mocks were
  rejected in one day for improvising. Locked refs: pattern sheet `be7bd6d3`, fixture `d70aae67`, team
  `f6348775` (system.css is transcribed from these). Player mock `6c21ef71` NOT approved.
- **Build it and show it** — a mock IS the design decision; never ask about something visual in words.
  Reserve open §10 questions in the contract's `decisions_reserved` (the Artifact gate enforces it).
- **Real data only, no fabrication** — no fake heroes, no invented ranks; honest empty/pending states
  ("no hero, not shippable" is RETRACTED — an empty slot is honest).
- **Player-page open content Qs** (Phase C): what a GK's Overview shows; whether YoY holds for a player
  who changes club/role — use consultants, don't answer by instinct.

## WHERE WE STAND — five launch groups
| # | Group | Status |
|---|-------|--------|
| 1 | **Pages** | 2 of 5 built (fixture + team). **Foundation shell = current task.** Player spec'd + data-ready + UNBUILT. 7 of 15 screens UNSPEC'D (home, competition hub, browse, leaderboards, h2h, glossary, chrome). |
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
- **The agent set** — a **ui-BUILDER / design-implementer** (the "doer" the CPO wants; a draft was on
  `feat/expert-agents-that-build`, now merged into main history); a **design reviewer for BUILT pages**
  (sharpen `bi-analyst-reviewer`: default-FAIL, 2 verified risks, review the RENDERED page); a
  `football-analytics-expert` + `data-journalist` as **CONSULTANTS** (before design, own no file); a
  fan probe on the rendered page. **Unverified:** do a subagent's tool calls fire the main session's
  hooks? TEST, don't assume.
- **The metric-change skill** — adding one team metric touched SIX files; the skill's value is
  enumerating them.
- **Mirror the crests** (above).
- **Amend the locked display contract** (`docs/wireframes/metrics_display.md`, 16-row team table) for the
  2 metrics #804 surfaced. §10.
- **legal-counsel consultant** — risk register from the API-Football terms; doer later for imprint/
  privacy once the operator question is answered.
- **Reviewers as peers** (not one reviewer over every diff) — the reviewer-model-in-routing half shipped
  in #822; the peer split is still owed.

## DONE (history — detail in git)
- **2026-07-26:** frontend spec audit + backtobayesics study; foundation mock approved.
- **2026-07-25:** Firebase deploy LIVE + verified (run 30151299421); export cost measured ~$0.002/run
  (exclude dbt-labelled queries in JOBS_BY_PROJECT or it reads ~100x high); **#822** per-agent effort
  pins merged. ⚠️ follow-ups: actions warn Node 20 deprecation; team-page footer says "Sample data · v2
  preview" on real data (confirm intended).
- **2026-07-24:** team page (3 tabs) + real-data wiring (#813, #818). ⚠️ `appearances` = played legs
  (`minutes_played>0`, #813). ⚠️ default-heap `astro build` OOMs at full scale — deploy uses
  `--max-old-space-size=8192`; before a local dev build run `git clean -fX site_v2/src/data`.
- **2026-07-22:** #802/#803/#804. ⚠️ **#804 fingerprint** (verify if not yet confirmed): 1,376 ranked
  rows, sum_deserved 16,980, sum_gap -4,573, md5 `bc6d2587b6f2ad02469ded299fc025b7`. #803 shipped four
  live gates. No player photos (CPO). API-Football licensing settled (reselling is the one hard
  prohibition; real risk is operational suspension). Lessons: fix the CLASS not the instance;
  inference ≠ permission (§10); verify the real tree.

## NEXT
1. **Build the frontend FOUNDATION** (the CURRENT TASK above).
2. Then Phase B (lean process) → Phase C (pages; player first).
3. Small follow-ups: em-dash/AI-tell sweep in `site_v2/src/i18n/strings.ts`; `site_v2/src/data/README.md`
   stale; `content_architecture.md` cites GAP-22 (should be GAP-20) for squad; fixture PlayerRow
   "1 assists" → singular i18n.

## OPEN — the CPO's alone
- **Imprint operator + address** — blocks publication (#799); get a lawyer, never conclude it.
  Publish-time only; does NOT block building.
- **Hosting recurring run** — cost MEASURED negligible; only the trigger shape (`workflow_run` on
  dbt-scheduled vs cron) is left. Go-public = imprint-blocked.
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
  export → build → firebase deploy. The in-app Browser pane is unreliable here (screenshots / file://
  time out) — verify frontend via the published Artifact's inline render.
- **Commit mechanics:** ONE substantive commit per PR; `git commit` runs alone (no chaining);
  `--amend` gate-blocked. Collapse: `git reset --soft HEAD~1`, re-stage, recompute hash vs main
  (`python .claude/hooks/git_discipline.py --staged-hash`), re-run required reviewers, rewrite
  `review.md`, commit, `git push --force-with-lease`.
- **Standing metric ruling:** a metric's formula is fixed math; never put coalesce/countif/null-gate in
  a `*_expr`.

## Verified state reference
- **Live to users:** no PUBLIC site. v2 IS deployed to `football-data-pipeline-gcp.web.app` (reachable,
  unlisted, not announced) — a verification target.
- **v2 built:** the shared design system (`system.css` + 24 components), the fixture page (#672), the
  team page (3 tabs). **NO shared nav shell / responsive desktop layout yet** (= the foundation task).
- **Automation:** session default Opus+high in gitignored `settings.local.json`; review-fleet effort
  pinned (#822) — see [[reference-model-effort-automation]].
- **Metric layer:** all 78 catalogue rows carry `direction` + `interpretation`; six guards; the
  catalogue is the only source of metric definitions.
