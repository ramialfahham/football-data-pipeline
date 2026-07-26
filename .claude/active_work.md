# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Must stay under
> 16,000 characters (the SessionStart hook's injection budget).

_Last updated **2026-07-26**. main GREEN at **a1e4909**. **Phase B is DONE** — #825 (foundation
shell), #827 (sharpened reviewer), #826 (page-spec contract) all MERGED. **SEQUENCE LOCKED (CPO
2026-07-26) — do NOT re-open it: CURRENT = Phase C, player page, DESIGN-FIRST.** Step one is a
DESIGN CONVERSATION with the CPO (open content Qs + mock approval) — do NOT start building the
player page before that happens. Then home page, then legal/imprint, then launch. Firebase deploy
is LIVE + verified (manual, `.web.app`, not public)._

## THE GOAL
**The new website live.** ~2–3 weeks; **quality over speed** (CPO 2026-07-22).

## ⭐ Phase B — DONE (2026-07-26): foundation shell + lean-process scaffolding
Why: a 2026-07-26 spec audit found the frontend systematic on DATA/CONTENT but improvisational on
LAYOUT/CHROME/page-production. CPO: foundation-first, lean process, before more pages.
- **#825 (PR #829)**: `Layout.astro` gained a global header (brand, 6-item nav — inert `<span>`,
  no index pages exist yet — search box, WORKING dark/light theme toggle via `localStorage`,
  mobile hamburger/drawer) + footer, from the CPO-approved mock (`87d14109`). `system.css` gained
  its first responsive breakpoints (nav inline ≥700px, `.shell`/`.page-grid`/`.rail` two-column
  primitive ≥900px — built, wired into ZERO pages, per-page rail contents reserved — search field
  ≥1010px). Team/fixture pages: zero file changes (inherit via Layout). `docs/wireframes/09_chrome.md`
  + a layout-system section in `00_overview.md`. Home-content mock `1c35e7aa` is reference only —
  home page is NOT built (that's Phase C).
- **#827 (PR #832)**: sharpened `bi-analyst-reviewer` to require rendered-page evidence
  (`.claude/task/rendered_page_evidence.md`, required for rendering-affecting `site_v2/src/**`
  diffs) instead of a code-only read — a real gap #829's own review proved (a CSS specificity bug
  passed review, only caught by actually building the site).
- **#826 (PR #834)**: schema-validated page-spec contract. Each page template declares blocks/
  marts/i18n keys in `site_v2/src/specs/**/*.spec.json`; `check-page-specs.mjs` (hand-rolled, zero
  new dependency, 14-test suite) runs via `prebuild` so `npm run build` refuses an underspecified
  page, on both real build paths, no `.github/workflows` edit needed.

**Reserved (CPO §10, still standing, NOT decided in build):** exact nav contents/order · search
style · what fills the desktop RAIL per page type (home = standings/trending/scorers) ·
footer/legal (imprint-blocked) · default-theme policy (dark-fixed vs follow-OS).

**DEFERRED from the backtobayesics study (right-sized, NO autonomy):** component/metric catalogue,
import-boundary rule, one-page-at-a-time driver (#828) — do after Phase C's first pages, only if
still needed.

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
| 1 | **Pages** | 2 of 5 built (fixture + team). **Phase B DONE** (foundation shell #825, reviewer #827, page-spec contract #826 — all merged). **CURRENT: player page, design conversation first** (mock not approved). 6 of 15 screens UNSPEC'D (home, competition hub, browse, leaderboards, h2h, glossary) — chrome now spec'd. |
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
- **2026-07-26:** Phase B complete — #825 (PR #829, commit 9990d2b), #827 (PR #832, commit
  c290df9), #826 (PR #834, commit a1e4909). #826 went through 2 review rounds: round 1 caught a
  mislabeled fixture spec block (bi-analyst-reviewer) and a schema/checker wording overclaim plus
  missing test coverage (cto-reviewer); both fixed, round 2 clean PASS. Follow-up filed: #833
  (wire the rendered_page_evidence.md obligation into a builder-facing doc).
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

## NEXT — SEQUENCE LOCKED (CPO 2026-07-26, this exact order, do not re-decide it)
1. **CURRENT: Phase C, pages one at a time, DESIGN-FIRST — player page first.** NOT a clean
   build — open content questions (what a GK's Overview shows; whether YoY holds across a
   club/role change) and mock `6c21ef71` is NOT approved. **Step one is a design conversation
   with the CPO to settle those and get a mock approved — do NOT start building before that.**
   Use consultants (football-analytics-expert, data-journalist), don't answer by instinct. Once
   approved: branch off main, plan mode, CPO go, build, review cycle, PR, close the issue myself
   once merged (own the full lifecycle — [[feedback-issues-for-upcoming-work]]).
2. Then the home page, in the new shell (home-content mock `1c35e7aa` is reference only).
3. **THEN legal/imprint** (CPO decision, blocks going public), **then launch**.
4. Small follow-ups: em-dash/AI-tell sweep in `site_v2/src/i18n/strings.ts`; `site_v2/src/data/README.md`
   stale; `content_architecture.md` cites GAP-22 (should be GAP-20) for squad; fixture PlayerRow
   "1 assists" → singular i18n; FI `footerDataSource` untranslated (#825 nit); wire the
   `rendered_page_evidence.md` obligation into a builder-facing doc (#833, cto-reviewer follow-up).

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
- **v2 built:** the shared design system (`system.css` + 26 components), the fixture page (#672), the
  team page (3 tabs), the **shared nav shell + responsive layout system (#825)** — header,
  footer, theme toggle, 700/900/1010px breakpoints — and the **page-spec contract (#826)**: every
  real page must declare its blocks/marts/i18n keys, checked at build time. The
  `.shell`/`.page-grid`/`.rail` primitive exists but is wired into zero pages; team/fixture stay at
  their locked 680px `.inner` width.
- **Automation:** session default Opus+high in gitignored `settings.local.json`; review-fleet effort
  pinned (#822) — see [[reference-model-effort-automation]].
- **Metric layer:** all 78 catalogue rows carry `direction` + `interpretation`; six guards; the
  catalogue is the only source of metric definitions.
