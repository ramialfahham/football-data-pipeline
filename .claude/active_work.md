# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Must stay under
> 16,000 characters (the SessionStart hook's injection budget).

_Last updated **2026-07-27**. main GREEN at **95c0dd1**. **Phase B is DONE** — #825/#827/#826 all
MERGED. **CURRENT: Phase C player OVERVIEW tab is mostly designed and CPO-reviewed; 5 CPO decisions
are open before it can be built.** The render failure is DIAGNOSED and the working delivery practice
is recorded below. Performance and Career tabs NOT started. **FIRST ACTION next session: read the
design-state comment on #753 — it is the authority and splits every item by who decided it. Do not
build from its section C.** Firebase deploy is LIVE + verified (manual, `.web.app`, not public)._

## THE GOAL
**The new website live.** ~2–3 weeks; **quality over speed** (CPO 2026-07-22).

## ⭐ CURRENT — Phase C player OVERVIEW: 5 CPO decisions open, then build (2026-07-27, #753)

**The authority is the design-state comment on #753, not this summary.** It splits EVERY item by who
decided it: (A) decided by the CPO, (B) CPO direction implemented, (C) **STILL OPEN — do not build
from these**, (D) factual findings, (E) data deps, (F) recommendation. An earlier version of that
comment wrongly marked open items "approved"; it was rewritten. Trust the sections, not memory.

**THE 5 OPEN CPO DECISIONS** (the rest of section C I will default and state explicitly):
1. **One URL with 3 tabs (mirrors the shipped team page) vs 3 sub-paths** (specs 12/13 carry their
   own canonicals + meta). **Decide FIRST** — changes what gets built and invalidates those sections.
2. Does the **9-row season bundle leave Overview** for Performance (a change to spec 03).
3. The team's **thinned record strip** — accept, or restore the standing line and drop rank/points
   from block 1. **Touches the LIVE team page.**
4. Does the **inert selector ship looking clickable** (#362)?
5. **Wording + names** (§10, CPO-only): block-1 heading (breaks for cups — "current vs last season"
   with no last season), the appearances line, the scope line, `Fixtures` vs `Match log`, and the
   rank-delta sign convention (15th→3rd is −12 as a number, +12 as an improvement).

**RENDER FAILURE: DIAGNOSED.** Not sharing/permission (artifact existed, CPO-owned, served complete
HTML) and not CSP (zero external refs). Prime suspect: every tab panel sat behind
`.page{display:none}` revealed only by `#tab-x:checked ~`. **Working practice — keep doing all three:
show ONE tab at a time (no hidden panels), publish to a NEW artifact URL (never republish), deliver
via Artifact AND SendUserFile.** Every mock since has rendered.

**Approved design in brief** (provenance in #753 A/B): block order = **current vs last season →
deserved vs actual → fixtures**, identical on team and player. Player block 1 = **goals, assists,
shots on target, key passes**. Strip = **games played only** (mins/app + substitute apps → the
Performance tab). Player strip states **appearances out of the club's matches**. **Scope line under
the tabs** (option 2) on both pages. Chips fixed **44px** so both pill groups are exactly **140px**
and align; a label before each group; each label+group is atomic; 560px container query.
**The outfielder is the DEFAULT page; the goalkeeper is the VARIANT** (a keeper is 1 of 4 position
groups — designing the canonical page around one was a real mistake this session).

**⚠️ The chip change edits shipped `system.css`** (`.cchip` auto-width → fixed 44px box). It affects
the **LIVE team page**, not only a mock.

**Data deps.** **#840** (club match count for the "of 38"; rank YoY + sign) blocks the player strip
line only. **#838** (points is a synthetic 3-1-0 tally in EVERY competition: FA Cup renders 0, UEL
renders 32 against a real league-phase 18) and **#839** (phase spike — tables vs brackets) block the
**TEAM** Overview's cup behaviour, **not** the player page. **#841** (pass accuracy 23–30% since 2022
vs 72–73% before) blocks player **PERFORMANCE**, not Overview.

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
  pattern sheet `be7bd6d3`, fixture `d70aae67`, team `f6348775`. Player mock `6c21ef71` NOT approved.
- **Design for the DEFAULT case, not an edge case.** The player page was designed around a
  goalkeeper because the open question (#366) happened to be about keepers. A keeper is 1 of 4
  position groups. Two conclusions drawn from that page were wrong until it was rebuilt on an
  outfielder. Pick the representative subject first, handle the variant second.
- **Never fill an empty slot to balance a layout.** Cards were put in a player strip purely because
  the right side looked empty — same reflex as the invented hero of 2026-07-21. If nothing honest
  belongs there, the space stays empty or the block changes shape.
- **Survey the real tree before recommending an architecture.** A phase model was proposed from 3
  competitions; surveying all 44 refuted 3 of its 4 structural claims in one query.
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
| 1 | **Pages** | 2 of 5 built (fixture + team). **Phase B DONE** (#825, #827, #826 — all merged). **CURRENT: player page — Overview designed + CPO-reviewed, 5 decisions open, then build; Performance/Career not started.** 6 of 15 screens UNSPEC'D (home, competition hub, browse, leaderboards, h2h, glossary) — chrome now spec'd. |
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
- **2026-07-27:** Phase C player **Overview** designed with the CPO over many rounds; render failure
  diagnosed; **4 issues filed (#838 #839 #840 #841)** and #753's design-state comment rewritten to
  separate CPO decisions from open questions. Overview mostly settled, 5 CPO decisions open.
  Performance/Career not started. No repo code changed beyond this handover.
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
1. **CURRENT: Phase C player page.** Read "⭐ CURRENT" then #753's design-state comment. Next
   actions in order: **(a) get the 5 open CPO decisions** (URL structure first — it changes what is
   built); **(b) build the Overview tab** — branch off main, plan mode, CPO go, review cycle, PR;
   **(c) THEN Performance, THEN Career, one tab at a time**, deciding each tab's content boundary
   against Overview before mocking it. Close #753 myself once merged (own the full lifecycle —
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
