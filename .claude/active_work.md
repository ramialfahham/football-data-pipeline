# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Must stay under
> 16,000 characters (the SessionStart hook's injection budget).

_Last updated **2026-07-27**. main GREEN at **95c0dd1**. **Phase B is DONE** — #825/#827/#826 all
MERGED. **CURRENT: Phase C player-page design conversation is IN PROGRESS AND BLOCKED — NOT
approved, NOT ready to build.** CPO verdict on the mock: **"badly drifting"** — redundancy,
content/design-language inconsistency across the 3 tabs, no decided per-tab content boundary.
Corrected process: **decide which tab owns which content IN WRITING first, build ONE tab at a
time** — never all 3 in one pass again. Separately, the Artifact/SendUserFile render also failed
TWICE, undiagnosed. **FIRST ACTIONS next session: (1) diagnose the rendering failure, (2) redo the
per-tab content-boundary decision in writing before building anything.** See "⭐ CURRENT" below.
Firebase deploy is LIVE + verified (manual, `.web.app`, not public)._

## THE GOAL
**The new website live.** ~2–3 weeks; **quality over speed** (CPO 2026-07-22).

## ⭐ CURRENT — Phase C player page, design conversation BLOCKED (2026-07-27, issue #753)

**Read this before touching anything.** Two rounds of mock iteration happened this session; the
CPO still has not seen a working mock. Do not repeat the same mistakes — read the corrections
below, not just the recommendations.

**BLOCKER (fix first):** the mock artifact (built at
`.../scratchpad/player_decisions_mock.html`, republished twice to the same Artifact URL) never
rendered for the CPO — "I still don't see anything" both times. Root cause **undiagnosed**.
Before building a third mock: check whether it is a sharing/permission issue (Artifacts are
private unless shared — did the share step happen?), a CSP violation in the HTML, or something
else about this delivery path. Consider an alternate delivery (e.g. a real built Astro page
behind the dev server, if the Browser pane cooperates this time) rather than blindly re-publishing
the same Artifact a third time.

**Three mistakes already made and corrected — do not repeat them:**
1. First mock described a layout change in prose instead of showing it ("promote save% to row
   1"). CPO: "This is the player page??" — always show, never describe.
2. Second mock (after fixing #1) showed a flat single-page Overview with NO tabs. CPO: "It had at
   least 2 tabs (if not 3). Things are going south again." **The player page is 3 TABS — Overview
   / Performance / Career — mirroring the team page exactly** (locked 2026-07-20, mock `6c21ef71`;
   confirmed against `docs/wireframes/12_player_stats.md` = Performance [percentile-vs-peers] and
   `13_player_career.md` = Career [club-grouped season log], both sub-screens of 03, using the
   SAME JS-free radio+label mechanism already shipped in
   `site_v2/src/components/team/Tabs.astro`). `03_player_profile.md` alone is ONLY the Overview
   tab spec — reading it in isolation is what caused the miss.
3. Third mock (all 3 tabs, built in one pass) was **"badly drifting"**: redundant + inconsistent.
   Confirmed — Save percentage and Pass accuracy each appeared verbatim in BOTH the Overview stat
   bundle AND the Performance percentile rows, no stated reason for the overlap; each tab also
   used a DIFFERENT visual row shape (`.pbrow` / `.vs-row` / `.carrow`) with no shared language.
   **The exact same redundancy failure class as the original 2026-07-21 incident — read
   `feedback_design_off_the_cuff.md` in full, this is a second occurrence, not new.**
   **CORRECTED PROCESS: decide, in writing, which tab owns which content — for all 3 tabs at
   once — BEFORE building any visual mock. A stat on two tabs needs a stated, different framing
   reason (e.g. "Overview = the raw number, Performance = where it ranks" is a reason; the
   identical string twice is not). Then build and show ONE tab at a time against that written
   boundary, never all 3 in one pass.**

**The two content questions — recommendations exist, NOT approved. The recommendations
themselves were not what the CPO objected to; how they got built into one mock was.**
- **GK Overview stat order (design-call #366):** promote the Save-percentage bundle row to the
  top for `position='G'` profiles; leave rows 2–9 in their existing fixed relative order (no
  hiding, no reshuffle — keeps "no tiers for players"). Both football-analytics-expert and
  data-journalist consultant passes (role briefs in `docs/roles/`) independently agreed. Precedent
  exists twice already (fixture-page GK strip variant, Stats-tab per-position metric sets).
- **YoY after a transfer:** `int_player_profile__yoy.sql` already nulls safely across a club
  change (no fabrication risk). Recommendation: name the new club in the empty state, since the
  club is already a shown, sourced fact on the page — **but do NOT hand over drafted final copy**
  (a prior pass wrote a specific sentence; composing user-visible wording is CPO-only, §10 — bring
  the content decision, not the sentence). Same-club role change: ship with NO caveat — position
  data (G/D/M/F only) is too coarse to describe one honestly; file a follow-up issue, don't block.
- Full reasoning + real-data grounding (B. Leno, a real Fulham GK; A. Isak's real Newcastle→
  Liverpool move, both queried from BigQuery) is posted on **issue #753** (two comments: the
  original findings, then the drift correction) — read both before re-deriving anything.

**Do NOT build the player page from these recommendations until the CPO has actually seen and
approved a mock built tab-by-tab against a written content boundary.** They are well-researched,
not decided, and the last attempt to mock them drifted.

## ⭐ Phase B — DONE (2026-07-26): foundation shell + lean-process scaffolding
- **#825 (PR #829)**: global header/footer (nav, search, working theme toggle, mobile drawer) in
  `Layout.astro`, from mock `87d14109`. `system.css` breakpoints (700/900/1010px). Home-content
  mock `1c35e7aa` is reference only — home page NOT built.
- **#827 (PR #832)**: `bi-analyst-reviewer` now requires rendered-page evidence for
  `site_v2/src/**` diffs, not just a code read.
- **#826 (PR #834)**: schema-validated page-spec contract — build refuses an underspecified page.

**Reserved (CPO §10, still standing):** exact nav order · search style · desktop RAIL contents per
page type · footer/legal (imprint-blocked) · default-theme policy. **Deferred** (backtobayesics,
right-sized): component/metric catalogue, import-boundary rule, one-page driver (#828).

## DESIGN DISCIPLINE (the weak spot — read every time)
- **Compose from the locked `system.css` ONLY. Never invent a per-page treatment.** Locked refs:
  pattern sheet `be7bd6d3`, fixture `d70aae67`, team `f6348775`. Player mock `6c21ef71` NOT
  approved. See "⭐ CURRENT" for the full, current player-page mistake list (3 of them, 2026-07-27)
  — do not repeat any.
- **Build it and show it** — a mock IS the design decision; never ask about something visual in words.
  Reserve open §10 questions in the contract's `decisions_reserved` (the Artifact gate enforces it).
- **Real data only, no fabrication** — no fake heroes, no invented ranks; honest empty/pending states
  ("no hero, not shippable" is RETRACTED — an empty slot is honest).
- **Multi-tab pages: decide per-tab content ownership in writing FIRST, build ONE tab at a time.**
  Never build all tabs in one pass — that is what produced the redundancy/inconsistency drift.
  Check ALL sibling wireframe files + the shipped tab component for the entity, not one file alone.

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
- **2026-07-27:** Phase C player-page design conversation started, NOT completed — see "⭐ CURRENT".
  Researched both content Qs, corrected a flat-page mock to the real 3-tab structure, then the
  3-tab mock itself was called "badly drifting" (redundant, inconsistent) — corrected process
  posted to #753 (two comments). Blocked on an undiagnosed Artifact-rendering failure. No repo
  code changed.
- **2026-07-26:** Phase B complete — #825 (PR #829, commit 9990d2b), #827 (PR #832, commit
  c290df9), #826 (PR #834, commit a1e4909). #826 went through 2 review rounds: round 1 caught a
  mislabeled fixture spec block (bi-analyst-reviewer) and a schema/checker wording overclaim plus
  missing test coverage (cto-reviewer); both fixed, round 2 clean PASS. Follow-up filed: #833
  (wire the rendered_page_evidence.md obligation into a builder-facing doc).
- **2026-07-26:** frontend spec audit + backtobayesics study; foundation mock approved.
- **2026-07-25:** Firebase deploy LIVE + verified; export cost ~$0.002/run; **#822** effort pins
  merged. ⚠️ team-page footer says "Sample data" on real data (confirm intended).
- **2026-07-24:** team page (3 tabs) + real-data wiring. ⚠️ `appearances` = played legs
  (`minutes_played>0`). ⚠️ `astro build` OOMs at full scale — needs
  `--max-old-space-size=8192`; before a local dev build run `git clean -fX site_v2/src/data`.
- **2026-07-22:** #802/#803/#804 (metric layer). No player photos (CPO). API-Football licensing:
  reselling is the one hard prohibition. Lessons: fix the CLASS not the instance; verify the real
  tree.

## NEXT — SEQUENCE LOCKED (CPO 2026-07-26, this exact order, do not re-decide it)
1. **CURRENT, IN PROGRESS: Phase C player page, design conversation.** Read "⭐ CURRENT" above
   FIRST. Literal next actions, in order: **(a) diagnose why the mock Artifact will not render**
   for the CPO (two failed attempts) before trying a third time blind; **(b) write the per-tab
   content-ownership boundary for all 3 tabs** before building any of them; **(c) build and show
   ONE tab at a time** against that boundary. Once approved: branch off main, plan mode, CPO go,
   build, review cycle, PR, close issue #753 myself once merged (own the full lifecycle —
   [[feedback-issues-for-upcoming-work]]).
2. Then the home page, in the new shell (home-content mock `1c35e7aa` is reference only).
3. **THEN legal/imprint** (CPO decision, blocks going public), **then launch**.
4. Small follow-ups: em-dash sweep in `strings.ts`; `site_v2/src/data/README.md` stale;
   `content_architecture.md` cites GAP-22 (should be GAP-20); fixture PlayerRow "1 assists" →
   singular i18n; FI `footerDataSource` untranslated (#825); wire `rendered_page_evidence.md` into
   a builder-facing doc (#833).

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
  export → build → firebase deploy. The in-app Browser pane is unreliable here (screenshots / file://
  time out). **⚠️ 2026-07-27: the Artifact/SendUserFile delivery path itself also failed to render
  for the CPO twice** (previously reliable all session for #825-#827) — undiagnosed, investigate
  before relying on it again for a CPO-facing mock.
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
