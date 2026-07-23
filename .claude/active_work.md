# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope, and do not
> infer the task from an issue title or a memory file. Keep it CURRENT STATE ONLY — history
> belongs in git, not in this file. It must stay under 16,000 characters, because that is the
> injection budget of the SessionStart hook meant to deliver it.

_Last updated **2026-07-22**. main GREEN at **0ff5037**, tree clean._

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
| 1 | **Pages** | 1 of 5 | Fixture page built and merged (#672). Team page designed and CPO-approved (mock `f6348775`), **not built**. Player, competition and landing pages not designed. |
| 2 | **Real data** | not started | The build renders from ONE committed sample fixture. `scripts/export_site_data.py` can emit teams/players/fixtures/competitions/nav; nothing consumes a real export yet. |
| 3 | **Hosting** | not chosen | Nothing is deployed anywhere. The GitHub Pages recommendation is WITHDRAWN (CPO: *"I want a website that is prepared to scale"*). |
| 4 | **Legal** | not started | No imprint, no privacy policy, no licensing note in the repo. Third-party image requests still present (below). |
| 5 | **CPO decisions** | 2 open | Operator identity + imprint address (blocks publication). Hosting choice (blocks deployment). Neither blocks building. |

Marts and the metric layer are **DONE and gated**. They are not launch work. Do not reopen them.

---

## DECIDED 2026-07-22

**No player photographs. Club crests stay.** CPO verbatim: *"OK no photos"*. Photographs carry
image rights over real people on top of photo copyright, add the most legal exposure and the least
information, and the player page is not designed yet so deciding now cost nothing. Crests run
through 13+ marts and the export, so removing them later is expensive, and the provider's own
framing for them is "identification and descriptive purposes". **The player page must be designed
without a portrait.**

**Sequence** (CPO: *"go"*): licensing ✅ → guards ✅ → team page.

---

## API-Football licensing — settled 2026-07-22, NOT a blocker

Terms read in full at `api-football.com/terms` (updated 2025-05-21). Websites are an expected use.
The one hard prohibition is reselling the data. They grant no publication licence and disclaim the
question ("must be requested from the competent authorities"), so it sits with the leagues, not with
them. Logos are "for identification and descriptive purposes"; they claim no rights over them and say
use may need the rights holders' permission. **THE REAL RISK is operational, not legal:** on a formal
complaint they may suspend API access immediately and without refund, which stops the whole pipeline.

Open, and NOT for an agent to answer: whether the rights-holder question needs a real lawyer before
publishing. **An agent must never produce a legal conclusion.**

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

## DONE 2026-07-22 — #802 handover rewrite · #803 guardrails · #804 metrics into marts

Detail is in the commits. Three things from them that are still LIVE:

⚠️ **#804 is UNVERIFIED until the fingerprint is checked.** The rename touched the column
`deserved_rank` is computed on, so a silent break is possible. After the main-push data build,
confirm unchanged: 1,376 ranked rows, sum_deserved 16,980, sum_gap -4,573, md5
`bc6d2587b6f2ad02469ded299fc025b7`. If it moved, the flagship read broke.

⚠️ **#802's rewrite DELETED an "owed work" line** (a metric rename), which then cost two review
rounds to reconstruct from git. **Anything carried as owed must survive a rewrite, or move to
`escalations.log` before the rewrite happens.** That is why the OWED section below exists.

**#803 shipped four gates:** protected paths need a blast-radius trace as well as authority; the
`Artifact` tool is gated on a contract with a real `decisions_reserved`; a Stop hook blocks em
dashes, section symbols, repo paths in prose and over 2,500 characters of prose; SessionStart is
wired (it had run nowhere).

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

## IN FLIGHT — branch `chore/trim-guardrails`

**TRIM THE MACHINERY TO WHAT EARNS ITS PLACE.** CPO (AskUserQuestion) after the staff review:
"Trim the weak parts, then reframe." Four cuts, all reductive:

- **Deleted `plain_language_gate.py`** and its Stop wiring. The 232-line hook that blocked the
  agent's own chat message on an em dash; its author flagged it disposable. The no-em-dash PREFERENCE
  survives as a norm (DO NOT section below); only the machine gate is gone.
- **Demoted `consulted:`** (shipped in #807, one day old). Removed its enforcement from the contract
  gate and the CI backstop; kept as a NORM in `working_agreement.md` and `TEMPLATE.md`. A considered
  partial reversal of #807 on the review's recommendation, logged in `escalations.log`.
- **Compressed the "forgery archaeology"** comments in `task_contract_gate.py`; kept the pattern.
- **Sped the test suite** from ~11 min to ~4: the `repo` fixture builds a git repo once and copies it
  per test instead of six subprocesses each.

KEPT: the hash-bound review, the contract/scope gate, the impact_map gate, the layer gate, the round
cap, the blinded reviewer cast, fail-open. Suite 215 passing. **TO FINISH: review cycle on the staged
hash, `review.md`, commit, PR.**

## NEXT

1. **This change** (in flight).
2. **The repo polish PR** (`chore/repo-polish`, contract saved to scratchpad). Kill the dead Pages
   links (Pages is 404), rewrite the description and headline to be honest about state, replace the
   retired-MVP screenshot with the architecture diagram, and REFRAME the `.claude/` machinery as the
   portfolio artifact per the staff review. Product copy needs CPO sign-off before writing.
3. **The hero block, as a PICTURE.** Buildable now that deserved-vs-actual is in POINTS (#806): a
   fitted line is legitimate in points space. Owed to the CPO as something to look at, never prose.
   Must never render for a non-domestic or non-single-ladder competition.
4. **The team page**, all three tabs, mock `f6348775` with that block replaced. The centerpiece the
   economics + trim work was done to make cheaper.

---

## OPEN — the CPO's alone

- **Who the site operator is and what address the imprint carries.** Blocks publication (#799).
- **Hosting.** Nothing chosen; GitHub Pages withdrawn.
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

- **Live to users:** NOTHING. The MVP was retired 2026-07-21 (matchdayiq.io offline, Pages deleted,
  deploy workflow disabled, `curl` returns 404; DNS untouched). There is no public site.
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
