# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope, and do not
> infer the task from an issue title or a memory file. Keep it CURRENT STATE ONLY — history
> belongs in git, not in this file. It must stay under 16,000 characters, because that is the
> injection budget of the SessionStart hook meant to deliver it.

_Last updated **2026-07-25**. main GREEN at **b15e4fb**. Firebase deploy is **LIVE and verified** (manual dispatch, `.web.app`, not public) — real team pages render. The 2 GCP prereqs are DONE and the export scan cost is measured (~$0.002/run, negligible). Recurring run (trigger shape only) + go-public still gated (see OPEN)._

---

## THE GOAL

**The new website live.** Two weeks is the target, three is acceptable, and quality wins over
speed. CPO 2026-07-22: *"I prioritize quality over speed. If me make it in 3 weeks it's ok as
well. But 2 weeks remains our goal."* Anything that does not serve this is out.

---

## WHERE WE STAND — the five launch groups

**This is the progress view.** When the CPO asks where we stand, answer from this table. Nothing
here comes from the 114-issue tracker, which he has withdrawn confidence in; every row was
verified against the repo on 2026-07-22.

| # | Group | Status | What is left |
|---|-------|--------|--------------|
| 1 | **Pages** | 2 of 5 built | Fixture (#672) + **team page COMPLETE** (Overview #810 + Performance #811 + Squad, all merged). Player, competition, landing pages not designed. |
| 2 | **Real data** | consuming ✅ | Build CONSUMES the real export (#818 merged): team + fixture pages enumerate via `import.meta.glob`; full 45-league competitions map. The export→build→deploy job is group 3 (hosting). |
| 3 | **Hosting** | **DEPLOYED & VERIFIED LIVE** | **Firebase** live at `football-data-pipeline-gcp.web.app` (manual dispatch, `.web.app`, not public). Verified 2026-07-25: real team pages render (Man Utd #3, Liverpool #5 — distinct real data). Recurring run (trigger shape only; cost measured negligible) + go-public still gated (see OPEN). |
| 4 | **Legal** | not started | No imprint, no privacy policy, no licensing note in the repo. Third-party image requests still present (below). |
| 5 | **CPO decisions** | 2 open | Operator identity + imprint address (blocks publication). Hosting choice (blocks deployment). Neither blocks building. |

Marts and the metric layer are **DONE and gated**. They are not launch work. Do not reopen them.

---

## DECIDED 2026-07-22

**No player photographs. Club crests stay.** CPO: *"OK no photos"*. Photos carry image rights over real
people + the most legal exposure for the least info; the player page isn't designed yet so deciding now
cost nothing. Crests run through 13+ marts (expensive to remove) and are "identification/descriptive".
**The player page must be designed without a portrait.**

---

## API-Football licensing — settled 2026-07-22, NOT a blocker

Terms (`api-football.com/terms`): websites are expected use; the one hard prohibition is RESELLING the
data. No publication licence granted (sits with the leagues); logos are "for identification/descriptive
purposes". **Real risk is operational:** on a formal complaint they may suspend API access without
refund, stopping the pipeline. Open (NOT for an agent): whether publishing needs a lawyer first. **An
agent must never produce a legal conclusion.**

---

## ⚠️ v2 makes third-party requests TODAY

The committed sample data carries `media.api-sports.io` URLs, and `Crest.astro` and `PlayerRow.astro`
render them as `<img src>`. **The exact defect that took the MVP offline is already present in v2.**
(An earlier all-clear was wrong: it grepped code and missed the data files.) Fix: mirror crests onto
our own origin. That fixes the **privacy** half only, and arguably worsens the rights position since
we would host copies. The two pull in opposite directions.

---

## The retrospective (2026-07-22) — what still needs remembering

Holes 1-4 are now CLOSED by #803, so only the behavioural findings survive here.

- **The recurring defect is fixing the INSTANCE instead of the CLASS.** Every failure today was
  this: one word list holed four rounds running, a stale count in six files, a coverage sentence
  written in two places and corrected in one. Reviewers were not finding different bugs, they were
  finding one bug in new places. **When a reviewer finds the same class twice, stop patching and
  sweep it.**
- **Inference is not permission, and I made this mistake TWICE in one day** — the metric rename and
  the review routing, both §10, both "obviously right", both with no quoted answer. §10 says
  escalate "regardless of how obvious", precisely because obviousness is not the test.
- **Verify against the real tree, never a hand-picked list**, and least of all a list of files that
  do not exist yet. `git ls-files` takes one command.
- **The test before asking:** state what I will do if never answered, and what undo costs. No
  default nameable → not ready to ask. Cheap undo → do it and say so. **Never ask about something
  visual in words; build it and show it.**
- **What actually gets read:** CLAUDE.md and the memory index. That is the whole list. Rules that
  must hold belong in a hook or a test, not in prose.

---

## DONE 2026-07-22 — #802/#803/#804 (detail in commits)

⚠️ **#804 fingerprint (verify if not yet confirmed):** the `deserved_rank` rename could silently break
the flagship read. Confirm post-build: 1,376 ranked rows, sum_deserved 16,980, sum_gap -4,573, md5
`bc6d2587b6f2ad02469ded299fc025b7`. **#803** shipped four live gates (blast-radius trace on protected
paths, Artifact gate, Stop prose hook, SessionStart wiring). Lesson: **owed work must survive a
rewrite** (why OWED exists below).

---

## OWED — deferred deliberately, recorded so it is not lost

Each of these was proposed, judged worth doing, and NOT done. None is forgotten; none is decided
away. Written here because holding them in a chat is how they disappear.

**The agent set.** A `ui-expert` DOER (a draft is stashed on `feat/expert-agents-that-build`; good
raw material, it names every 2026-07-21 design failure as a prohibition — but move its redundancy and
slot-order rules to a reviewer, since a doer cannot police itself). A design reviewer for built
pages. `football-analytics-expert` and `data-journalist` as CONSULTANTS, consulted before design and
never owning a file surface. A fan probe, given a task rather than an opinion prompt, which must see
the RENDERED page. **Unverified prerequisite: whether a subagent's tool calls fire the main session's
hooks at all — if not, the artifact gate does not cover a doer. TEST IT, do not assume.**

**The metric-change skill.** Adding one team metric touched SIX files across models, schemas and
docs, and nothing enumerates that list. The skill's value IS the enumeration. Write it from what
#804 actually required, not from imagination.

**Mirror the crests.** `site_v2` renders team crests and player photos straight from
`media.api-sports.io`, so every visitor's browser talks to a third party — the exact defect that took
the MVP offline. Copying them to our own origin fixes the privacy half and does NOT improve the
rights position.

**Amend the locked display contract** (`docs/wireframes/metrics_display.md`, a 16-row team table) to
carry the two metrics #804 surfaced. A §10 display decision; the approved mock shows both.

**`legal-counsel` as a consultant** — a risk register from the API-Football terms. Doer later, for
the imprint and privacy pages, once the operator question is answered.

**The guardrail economics** (raised by the CPO after #803 cost nine rounds). Delta re-review and a
round cap of 3 shipped in #807. A staff-level AI-engineering review then judged the machinery core
strong (the hash-bound blinded review, the self-gating hooks) but three parts over-scoped; the trim
(in flight) cuts them. STILL OWED, deliberately deferred: reviewer model in the routing file, and
reviewers as peers rather than one reviewer reading every diff.

---

## DONE 2026-07-24 — team page (3 tabs) + real-data wiring (#813, #818 merged)

⚠️ **`appearances` = played legs** (`minutes_played > 0`), fixed warehouse-wide (#813); `mart_player_career`
gained `minutes` + `minutes_per_appearance`. Build CONSUMES the real export (#818): team+fixture
`getStaticPaths` enumerate `src/data/{teams,fixtures}/*.json`; full 45-league `competitions.json`.
⚠️ Default-heap `astro build` OOMs at full scale (deploy job uses `--max-old-space-size=8192`); before a
local dev build run `git clean -fX site_v2/src/data` else OOM.

## DONE 2026-07-25 — Firebase deploy LIVE + verified · effort pins (#822 merged)

**Firebase deploy LIVE + VERIFIED.** Run 30151299421 (12m41s): WIF auth → export → raised-heap build
→ `firebase deploy` all green, incl. firebase-tools accepting WIF/ADC (was unproven).
Live at `football-data-pipeline-gcp.web.app`; real team pages render distinct data (Man Utd #3,
Liverpool #5). Root `/` = "under construction" scaffold (landing not designed). **Manual dispatch,
`.web.app` only, not public.**

**Export cost measured:** ~$0.002/run (~0.18 GiB, 15 whole-mart reads) — recurring run unblocked on
cost; only the trigger shape is left. **#822 merged:** per-agent `effort` pinned (scope-auditor=medium,
five reviewers=high), models unchanged; personal Opus+high default in gitignored `settings.local.json`
([[reference-model-effort-automation]]). Follow-ups: actions warn Node 20 deprecation; team-page footer
says "Sample data · v2 preview" on real data (confirm intended).

## NEXT

1. **Deploy + hosting (group 3)** — DONE and LIVE. Firebase deploy verified 2026-07-25 (run
   30151299421). The only remaining hosting step is the **recurring trigger** — cost is measured
   negligible, so this is now purely the CPO's trigger-shape choice (`workflow_run` on dbt-scheduled
   vs a cron). See OPEN > Hosting.
2. **Player, competition, landing pages (group 1)** — design first, then build (do not build undesigned).
3. **Small follow-ups** (here in case the task chips don't survive a restart):
   - **Em-dash / AI-tell sweep (CPO must, 2026-07-24)** — replace em dashes + en-dash records in the
     display strings (`site_v2/src/i18n/strings.ts`: `aboutWithH2h`, deserved-hero verdicts,
     coming-states) with natural punctuation + a guard. Transparent AI text must not LOOK AI-generated.
   - **site_v2/src/data/README.md** stale (says one sample) → update to the real-data setup.
   - **content_architecture.md** cites "GAP-22" for squad stats; it's GAP-20.
   - **fixture PlayerRow** renders "1 assists"/"1 goals" → use the Squad tab's singular i18n pattern.

---

## OPEN — the CPO's alone

- **Imprint operator + address.** Blocks publication (#799). CPO 2026-07-23 won't publish his home
  address. Substitutes exist (service/business address) but whether the site needs an Impressum and
  whether a substitute suffices is a LEGAL question — get a lawyer, never conclude it. Publish-time
  only; does NOT block building.
- **Hosting.** Vendor **Firebase Hosting** (decided 2026-07-24). Deploy is LIVE and VERIFIED
  2026-07-25 (run 30151299421). The two GCP prereqs are **DONE** (Firebase enabled + default site
  `football-data-pipeline-gcp.web.app`; `roles/firebasehosting.admin` granted to the deploy SA
  github-actions-dbt). Cost **MEASURED**: the export scan is ~$0.002/run (~0.18 GiB, 15 queries) —
  negligible, within BigQuery's 1 TiB/month free tier. **Open, the CPO's:** the **recurring-run
  trigger shape** (`workflow_run` on dbt-scheduled vs a cron) — cost is no longer a blocker, this is
  now just the schedule choice. Go-public (custom domain, DNS, announcement) stays imprint-blocked.
  (Measurement note: the deploy SA github-actions-dbt is shared with the dbt pipeline; to measure the
  export scan, exclude the dbt-labelled queries in JOBS_BY_PROJECT or the number is ~100x too high.)
- **The feedback Apps Script and the data it collected**, in his own Google account, unreachable
  from here (#687).

---

## DO NOT (standing)

- Do NOT treat the 114-issue tracker or its 7 milestones as agreed work. Useful only as a checklist
  of things somebody noticed. Re-validate before acting on any of it.
- Do NOT cite the `road_to_launch` artifact. Superseded.
- Do NOT write another planning document. The tracker and this file are the only plan.
- Do NOT touch `site/`. RETIRED and frozen 2026-07-21, offline. No parity check, no cutover, no
  restore; any edit is work that gets deleted. #377 is void.
- Do NOT build a page whose design the CPO has not approved.
- Do NOT re-run the data phase. Marts and the metric layer are finished and gated.
- Do NOT derive facts in the export or the frontend — select, group and rename only.
- **Never merge a PR. The CPO merges.** Branch from main; never commit to main.
- PR **#673** was CLOSED 2026-07-22 as superseded (predated the approved 3-tab design; its committed
  Arsenal sample was stale and it had never had a display review). Branch `feat/site-v2-team-profile`
  is PRESERVED: ~600 lines of team components are raw material for the team page build. Do not
  reopen it; harvest from the branch.
- Communication: plain language, one question at a time, no file paths or ticket numbers in chat
  unless asked, no em dashes.

---

## Operational notes (carried forward — still true)

- **dbt CLI and SQLFluff are BROKEN locally** (SQLFluff uses the dbt templater). `ci-data-build` is
  the real gate. Offline you CAN run `python scripts/check_layer_contract.py` and read model SQL.
- **BigQuery rejects a FROM-less `WHERE`** — a singular test's empty-case fallback needs a FROM.
  Only `ci-data-build` catches it.
- **Commit mechanics:** ONE substantive commit per PR. `git commit` runs alone, no chaining;
  `--amend` is gate-blocked. To collapse: `git reset --soft HEAD~1`, re-stage, recompute the hash vs
  main with `python .claude/hooks/git_discipline.py --staged-hash`, re-run every required reviewer on
  the full diff, rewrite `review.md`, commit, then `git push --force-with-lease origin <br>:<br>`.
- **Standing metric ruling, do NOT relitigate:** a metric's formula is fixed mathematics. Data
  availability decides only whether a model can APPLY it. Never put `coalesce`/`countif`/a null-gate
  in any `*_expr`.

---

## Verified state reference

- **Live to users:** no PUBLIC site. The MVP was retired 2026-07-21 (matchdayiq.io offline, Pages
  deleted, `curl` returns 404; DNS untouched). v2 IS deployed to `football-data-pipeline-gcp.web.app`
  (reachable but unlisted, no custom domain, not announced) — a verification target, not a launch.
- **v2 built:** the shared design system (`site_v2/src/styles/system.css` + components) and the
  fixture page (#672).
- **Locked design references:** pattern sheet `be7bd6d3` (the block vocabulary — compose from it,
  never invent a per-page treatment), fixture page `d70aae67`, approved team page `f6348775`. Player
  mock `6c21ef71` is **NOT approved**.
- **The "no hero, not shippable" rule is RETRACTED.** It was self-imposed and it is what forced the
  invention of a fake hero. An empty slot is honest.
- **Open player-page content questions** (do not answer by instinct — use the consultants): what a
  goalkeeper's Overview shows when goals and assists are meaningless for him, and whether
  year-over-year survives for a player at all (he changes club, league, role and minutes).
- **Metric layer:** all 78 catalogue rows carry `direction` + `interpretation`; six guards enforce it.
  The catalogue is the only source of metric definitions.
