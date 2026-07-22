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

**The sequence** (CPO: *"go"*): licensing check → one governance task for the guards and agents →
build the team page.

---

## API-Football licensing — terms read in full, 2026-07-22

Read directly from `api-football.com/terms` (last updated 2025-05-21). **Not a blocker.**

- **Websites are an expected use.** *"We provide data for you to create different projects such as
  applications, websites, fantasy soccer games etc."*
- **The one hard prohibition is reselling.** *"you cannot directly sell the data we provide."*
- **They grant no publication licence.** *"Any license or permission to publish the data must be
  requested by the user from the competent authorities."* That is them disclaiming, not forbidding;
  the question sits with the leagues and federations.
- **Logos and images:** *"solely for identification and descriptive purposes"*; they own none of it
  and claim no rights over it; use *"may require additional authorization or licensing from the
  respective rights holders"*.
- **THE REAL RISK, operational not legal:** on a formal complaint from a league, federation or event
  organiser they *"reserve the right to immediately suspend or terminate the client's access to the
  API, without refund"*. That is the whole pipeline stopping.

Open, and NOT for an agent to answer: whether the rights-holder question needs a real lawyer before
publishing. **An agent must never produce a legal conclusion.**

---

## ⚠️ v2 makes third-party requests TODAY

An earlier claim that `site_v2` made none was **WRONG** — it grepped code files and missed the data
files. The committed sample data carries `media.api-sports.io` URLs, and
`site_v2/src/components/ui/Crest.astro` and `.../fixture/PlayerRow.astro` render them as `<img src>`.
**The exact defect that took the MVP offline is already present in v2.**

Fix: mirror crests onto our own origin instead of hotlinking. Honestly: that fixes the **privacy**
problem (visitors stop talking to a third party) and does **not** improve the rights position —
arguably it worsens it, since we would host copies. The two pull in opposite directions.

---

## The retrospective — six conclusions (2026-07-22)

1. **The pattern behind the failures.** Nothing checks whether the thing being made is worth making.
   Every hook gates paths, scope, evidence and commits; every agent judges conformance. So the
   default is to make whatever can be finished alone. The drift always runs the same way: build a
   page → design a page → write doctrine about pages → write process for writing doctrine. Each step
   up feels like diligence and never fails loudly.
2. **The guard system is blind to design.** Every gate keys on file paths. The three rejected mocks
   were artifacts, so no contract, no routing, no reviewer and no commit gate ever touched them. The
   one surface with no machinery is the one that failed three times in a day.
3. **Agents can help reasoning, and it is proven** — `escalations.log` records the football reviewer
   producing genuinely new information that changed an outcome. Every entry is a metric, scope or
   naming decision. **No design decision has ever been logged there.** Agents break single-sampling;
   they do not create taste. For taste the CPO and a user probe remain the check.
4. **Two enforcement holes, verified in code.** The protected paths (`.claude/hooks/`,
   `.claude/agents/`, `.claude/commands/`, `.github/workflows/`) are NOT in the structural surface,
   so editing a hook needs CPO authority but no blast-radius trace while a leaf dbt model needs one.
   And no hook fires on the Artifact tool at all.
5. **Bad questions.** Working agreement §11 bans recommendations, but the CPO wants one, and practice
   is split down the middle: `escalations.log` has 9 entries that explicitly withhold a
   recommendation per §11 and 8 that give one. So the rule is both stale and inconsistently
   followed. The test before asking: state what I will do if never answered, and what undo costs.
   No default nameable → not ready to ask. Cheap undo → just do it. **Never ask about something
   visual in words; build it and show it.**
6. **What actually gets read.** CLAUDE.md (9k) and the memory index. That is the whole list. `docs/`
   is 50 files and 443,000 characters. Three tiers: code that runs, briefs that load, reference prose
   only read when hunted for. The failures were rules written in tier three that needed tier one.

**Plain language is enforced by nothing** and failed inside the retrospective itself: file paths,
section numbers and invented vocabulary throughout.

---

## NEXT — the governance task (specified, ready to pick up cold)

One task, protected paths, needs `protected_override`, routes to `cto-reviewer` at **opus**.

**(a) Close the two enforcement holes.** Add the protected paths to `_is_structural` in
`.claude/hooks/task_contract_gate.py`. Add an `Artifact` matcher to `PreToolUse` in
`.claude/settings.json` so publishing a mock requires a contract and forces the design question into
`decisions_reserved`. **CPO ruled it BLOCKS, not warns** (quality over speed).

**(b) Plain-language enforcement.** The Stop hook already blocks a turn; extend it to read the turn's
own output and block on file paths, section numbers, em dashes, or excess length.

**(c) The agent set.** Five definitions:
- `ui-expert` **doer** — writes `site_v2/` and the wireframes. A draft is stashed (`git stash list`,
  "ui-expert agent, unreviewed, parked"); good raw material, it names every 2026-07-21 design failure
  as a prohibition. **Move its redundancy and slot-order rules to the reviewer** — a doer cannot
  police itself.
- `ui-expert-reviewer` — **the hole**: `site_v2/**` routes only to `cto-reviewer` (build config), so
  nothing reviews built pages for design or display honesty. Add it in `.claude/review_routing.json`.
- `football-analytics-expert` and `data-journalist` as **consultants** — consulted BEFORE design,
  never owning a file surface (a surface invites them to write specs, and specs are documents).
- A **fan probe** — given a task, not an opinion prompt, and it must see the RENDERED page.
  **Unverified prerequisite:** whether a subagent can hold the browser tools. Check first.

**(d) `legal-counsel`** — consultant first, producing a risk register from the terms above; doer
later, writing the imprint and privacy pages once the operator question is answered.

**(e) Correct §11** of `docs/working_agreement.md` to require a recommendation.

**(f) Wire the SessionStart hook** (`docs/portable_guardrails/hooks/handover_in.py`) or delete the
claim that it exists. Verified: no `SessionStart` key in `.claude/settings.json`,
`.claude/settings.local.json`, or the user-level `~/.claude/settings.json`. The script exists and
nothing runs it.

**Then build the team page.** Design approved, unbuilt, no design invention needed.

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
- PR **#673** (team profile Overview) is OPEN but SUPERSEDED — cluttered, predates the approved
  3-tab design. Close or rewrite it when the team page is built.
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
