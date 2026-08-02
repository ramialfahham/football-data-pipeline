# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — `wc -c` counts BYTES and this file is full of multi-byte
> symbols, so it over-reports by ~220 and will send you trimming content that fits.

_Last updated **2026-08-02**. main GREEN at **79317d3**; **#846 is MERGED**. **IN FLIGHT:
`feat/886-featured-season-dq-test`, 2 reviewers PASS, awaiting the CPO's merge.**
The product is **Matchday Pilot** on `matchdaypilot.com`.
**FIRST ACTIONS: read "⭐ THE REVIEW RULES CHANGED" below — it changes how every task runs — then run
`git stash list` before any git work.** The player page is FOUR tabs (#848); its Overview is **BUILT
but UNCOMMITTED in `stash@{0}` with a known-wrong default rule**, held on #845 + #846._

## ⭐ THE REVIEW RULES CHANGED (#878, merged 2026-08-01) — read before reviewing anything

#370 took **twelve rounds** for a ~300-line change; the code was right from round 5 and rounds 6-12
found only defects in the branch's own paperwork. Measured cause and the fix, all four CPO-ruled:

1. **Reviewers no longer see the task notes.** `review_exclude_paths` in `review_routing.json` hides
   `review.md`, `review_input.patch`, both evidence artifacts, both templates, `active_work.md`.
   **`contract.md` and `escalations.log` ARE delivered** — they carry authority, and a reviewer cannot
   check whether a cited ruling exists without the log.
2. **Build the patch with the hook, never by hand:**
   `python .claude/hooks/git_discipline.py --review-patch > .claude/task/review_input.patch`
   It is CUMULATIVE from the base branch and fails loud or large, never quietly narrower.
3. **The two evidence artifacts left `diff_sha256`.** Fixing a typo in them no longer voids a PASS —
   this is what let two verdicts survive three fix passes on #370. `contract.md` stays hashed, so
   scope still cannot move after review.
4. **A PASS may find nothing.** One entry under `risks_checked:` stating what was EXAMINED is enough;
   "checked X against Y, no defect" is complete. Never invent a finding. The old "two named risks"
   rule made invention mandatory on correct code. Floor is 1 in BOTH the hook and the CI twin
   (`check_task_artifacts.py`) — they must always agree.

**The org itself did NOT change** and the CPO ruled on that explicitly: activation-on-necessity is
right and **low activation is not a defect**. `data-engineer-reviewer` fires on 1% of commits and
caught 2 real bugs. A specialist that sleeps until its domain is touched is the cheapest thing here.
No role, brief, routing row or decision right was removed. Do not propose cutting reviewers.

**⭐ THE STANDING RULE THIS PRODUCED — a correction REPLACES, it never accumulates.** CPO: *"if one
comment doesn't pass the PR then you change it and only the new version stays. not the old and the
new."* No "an earlier version said X", no "caught by <reviewer> in round N", no running tallies in a
living document (they go stale and correcting them writes the next wrong number — four rounds failed
on exactly that). A moving set of items lives in ONE issue with file:line refs and no total.
Applying it took #370's paperwork from ~3.5 MB to ~240 KB and its contract from 643 lines to 171.

## THE GOAL
A football-stats site a fan actually uses. Data honesty is non-negotiable — the CPO cannot verify
numbers by hand, so every number the site shows is covered by an automated test.

## ⭐ CURRENT — unblock the player page (#845 + #846)

**#846 IS BUILT AND REVIEWED** on `feat/846-featured-season-from-mart`. The season a page opens on is
now a warehouse fact: both profile marts emit `is_featured_season`, the export's `_latest_season_row`
is gone and the team page's `.find()` on `competition_type` with it. **CPO ruling 2026-08-02: the
pipeline picks, not the page**, and "most recent" is scoped by the LENS the tab shows (club tabs =
most recent CLUB season). Built team pages are **byte-identical** in all three locales. The player
page's own `.find()` is NOT converted — it is in `stash@{0}`, held on #845; its mart half IS shipped,
so it becomes a one-line change there. Filed, not fixed: **#882** past seasons ingested but
unreachable (he wants them selectable), **#883** a blank `competition_type` in the registry is
skipped by all three guards, **#887** why #886 had to wait: `ci_*` datasets are SHARED, so
`--favor-state` forces
every ref to prod and **the PR-time DQ step cannot see the branch's own models**. ⚠ My first fix was
to drop the flag; he caught it as a hack.

**The org/process overview was delivered** (a visual board, not committed); he said *"I wanted
something else but nevermind."* Guess: a MAP of how work flows, not a reference board. Do not
rebuild unasked.

### 1. The player page is FOUR tabs (#848, CPO-agreed 2026-07-27)
Overview · Performance · Career = **club only**, always shown. **International = national lens, shown
only when `national_appearances_total >= 1`.** A tab, NOT a toggle: a crawler cannot follow a control,
so the national lens would have no URL. The condition is a **served fact**, so more national data
makes the tab appear with zero template change. It carries a competition selector **+ PERFORMANCE**.
**Read #848 before shaping it** — four CPO-class consequences are NOT actioned there.

### 2. ⚠️ PLAYER OVERVIEW IS BUILT BUT UNCOMMITTED — IN `stash@{0}`, WITH A KNOWN-WRONG RULE
`git checkout feat/player-overview-tab && git stash pop` — **do NOT rebuild it.** Build and tests
green, `bi-analyst-reviewer` + `scope-auditor` PASS; uncommitted because the gate rejects a FAIL.
**⚠️ Its default-season rule is WRONG:** `seasons[0]` = most recent of ANY competition, so both
sample players open on **World Cup 2026** with their national side. Under #848 the club tabs are
club-only, so it must be the most recent CLUB season. It would also now be blocked by the acceptance
gate — which is the point: it passed both reviewers while doing the wrong thing.

**Held on:** **#845** — adding `players` = **154,644 pages** against a build already needing 8GB at a
sixteenth of that · **#846** — the payload must carry the lens per season AND which club season is
featured. Not the frontend, not the export (**consumption too**), so it is a MART change.

**#753's design-state comment is the authority. Everything in its section C is still open.**
**RENDER FAILURE fix, keep all three:** ONE tab at a time, a **NEW** artifact URL, both channels.
**Still owed:** the CPO-approved chip/pill sizing (`.cchip` 44px) — own PR, edits `system.css`.

**Data deps.** **#840** (club match count; rank YoY sign) · **#838** + **#839** block the **TEAM**
Overview's cup behaviour, not the player page · **#841** blocks player **PERFORMANCE**.

## Reserved (§10, standing)
Nav order · search style · desktop RAIL per page type · footer/legal (imprint-blocked) ·
default-theme policy. **Deferred:** component/metric catalogue, import-boundary rule, #828.

## DESIGN DISCIPLINE (the weak spot — read every time)
Never design off the cuff. Use the approved wireframes and role briefs. Never invent a block to fill
a slot. Never design the canonical page around an edge case (the player page was first built around
a goalkeeper). Build ONE tab at a time, each content boundary decided before mocking.
**Show rendered output or a mock — never ask the CPO to rule on prose in the abstract.**
**Copy is ALWAYS his (§10).** Gather copy decisions UP FRONT in one pass, before the branch: #370
extracted 14 rulings one review round at a time, which is the single biggest cost driver on record.

## OWED — deferred, not forgotten (must survive rewrites)
- **The org/process overview** (see ⭐ CURRENT) — the CPO's outstanding ask.
- **The round cap still only RECORDS.** `ROUND_CAP = 3` is checked by the COMMIT gate against a
  number the builder types, so nothing stops a fourth round while rounds run. Rounds 5-6 of #370 were
  taken unnoticed. CPO ruled "finish this branch, then tighten the rule" — the rule is NOT tightened.
- **No gate records when it fires.** ~2,500 lines of enforcement across 7 hooks and 5 CI scripts, with
  zero telemetry, so most of ~72 checks cannot be shown to have ever worked. One appended line per
  denial is the highest-value follow-up in the repo.
- **The copy gate is wired to nothing** (#872) — it finds 16 real user-visible defects on main and
  blocks none. Blocked on those 16 being the CPO's copy to fix.
- A **metric-change skill** (one metric touched SIX files) · **mirror the crests** (built pages
  hotlink `media.api-sports.io`) · **reviewers as peers** (#822 shipped only the model half) ·
  **amend `metrics_display.md`** (#804's 2 metrics).

## DONE (history is in git — only still-live gotchas kept)
Merged: **#878** (review scope) · **#879** (#370 metric labels, per locale) · #842, #847, #854, #857,
#862, #865, #867, #874. #753 carries the player design state. Metric layer complete.
- ⚠️ `appearances` = played legs (`minutes_played > 0`), not squad selections.
- ⚠️ `astro build` OOMs at full scale (`--max-old-space-size=8192`); before a local dev build run
  `git clean -fX site_v2/src/data`.
- ⚠️ team-page footer says "Sample data" on real data. No player photos (CPO). API-Football:
  reselling is the one hard prohibition.

## NEXT
1. **Merge #846** (the CPO merges), then **#845** — which entities earn a page, HIS decision, bring
   him the page counts. Then the player page comes off `stash@{0}`, Performance → Career, ONE tab
   at a time.
2. **#882 + #845 are one decision.** Season pages multiply page count by history depth (1 to 11 per
   competition) on top of 154,644 player pages. Decide them together.
3. **#880 RESOLVED, no code change.** The mermaid is valid and renders; GitHub renders it in a
   viewscreen iframe and the error box was that bundle failing. A committed SVG was offered, not taken.
4. Home page (`1c35e7aa` = reference only), **then legal/imprint**, then launch.
5. Follow-ups: **#875** metric GROUP headings render in English on DE/FI pages, **needs a CPO ruling**
   on where a group name lives · **#877** `GD`, `W/D/L`, `T·I·B` and the result letters reach DE/FI
   readers in English, needs only the words · **#876** Performance rows break mid-word (CPO: filed) ·
   **#863** PROTECTED path editable with NO `protected_override` · **#866** `Regular Season - 20`
   untranslated · **#864** stale `cutover` comments · **#873** routing matcher hand-copied in
   `git_discipline.py` + `check_task_artifacts.py`, no parity test · route `seo-expert-reviewer`
   (0/150 commits, the only reviewer with no routing row) · GAP-22 should be GAP-20 · #833.

## OPEN — the CPO's alone
- **Imprint operator + address** (#799) — blocks publication; get a lawyer, never conclude it.
- **Hosting recurring run** — trigger shape only; go-public is imprint-blocked.
- **The feedback Apps Script** — #687.
- **#850's alias decision** — which duplicate team record is canonical. PR D freezes the URLs.
- **#875** — where a metric group name lives (chrome strings, or a catalogue/seed column per GAP-09).

## DO NOT (standing)
- Do NOT treat the tracker as agreed work; re-validate before acting.
- Do NOT write another planning document (the tracker + this file are the plan).
- Do NOT touch `site/` (retired/frozen). Do NOT build an unapproved page.
- Do NOT derive facts in the export or frontend — select/group/rename only.
- **Never merge a PR. The CPO merges. Branch from main; never commit to main.**
- Communication: plain language, lead with the decision, **no em dashes** (flagged twice as an AI
  tell, in prose AND product copy), no walls of text.
- Do NOT ask him to adjudicate what a rule can settle. Bring a rule that runs itself, or say plainly
  that none exists and name the cost. **But copy is ALWAYS his (§10) — that is not adjudication.**
- Do NOT bring him a fix for a defect he did not ask about, framed as though it changes a decision.
  Fix it in ten seconds and move on.

## Operational notes
- **⚠ THE dbt CLI IS NOT BROKEN — the one on PATH is. This note said the opposite for weeks and cost
  every session its lineage evidence.** Use **`.venv/Scripts/dbt.exe`** (`dbt=1.7.19` +
  `bigquery=1.7.2`, exactly the `requirements.txt` pin): `parse`, `ls`, `ls --select <model>+` all
  work with `DBT_PROFILES_DIR=C:/Users/Rami/.dbt`. The GLOBAL `dbt` pairs core 1.11.11 with
  bigquery 1.7.2 and throws `ModuleNotFoundError: dbt.adapters.factory`. Nothing needs installing.
  **Use it for `impact_map` lineage.** Never run `dbt build` (shared prod dataset).
- **SQLFluff works; only its dbt templater needs GCP.** **Lint from
  the REPO ROOT** (the root `.sqlfluff` has the jinja macro path, `dbt_project/.sqlfluff` does not):
  `python -m sqlfluff lint <model> --templater jinja --dialect bigquery`, FULL rule set (a `--rules`
  subset missed ST06). BigQuery rejects a FROM-less WHERE.
- **A wildcard is fine over ONE ref; add a join and AM04 fires.** Enumerate columns, the repo has
  **zero `noqa`**. Nesting ceiling ≈8 calls.
- **Frontend:** `deploy-site-v2.yml` (manual-only) does export → build → firebase deploy. The Browser
  pane CAN drive the dev server (`preview_start` name `v2`) — accessibility tree, geometry and console
  all work; only `screenshot` fails (the pane is not displayed). Measure overflow with a **Range-based**
  method; `scrollWidth` lies. Force the tab radio AND sub-panel or a hidden container reads as clean.
- **Commit mechanics:** `git commit` runs alone (no chaining); `--amend` gate-blocked. **Use
  `git commit -F <file>` for any message — an apostrophe breaks the form gate's shlex parse.** Write
  the message to the scratchpad, not the repo. A post-commit hook auto-pushes and opens the PR.
  `review.md` must be COMMITTED or CI reads the stale hash.
- **⚠ ON A SECOND COMMIT, `--staged-hash` IS THE WRONG NUMBER** — it covers only the increment, CI
  recomputes over the whole branch. Take it from `check_task_artifacts.py --base origin/main`, the
  code CI runs. A `review.md`-only commit is artifact-exempt, so rebinding is free.
- **Contract edits need a CLEAN tree** — stash-dance with explicit paths. ⚠ A pathspec stash can
  capture MORE than the paths given; if popping conflicts, `git checkout stash@{0} -- <paths>` then
  drop. Check `git stash list` after — never assume the index.
- **⚠ CWD PERSISTS between Bash calls** — `cd` to the repo root in the command, or a script silently
  measures nothing. **⚠ `fnmatch`'s `*` CROSSES `/`**, so `site_v2/*.json` also matches
  `site_v2/src/data/*.json`; and `scope_paths`' `[lang]`/`[team]` are CHARACTER CLASSES, so a literal
  Astro dynamic-route path can NEVER match itself — use `site_v2/src/pages/*/teams/*.astro`.
- **⚠ A line-based grep misses a phrase that straddles a line break** — three rounds of #878 missed
  the same stale rule that way. Sweep whitespace-collapsed when checking prose.
- **⚠ `src/pages/index.astro` is DEAD CODE** — `prefixDefaultLocale` writes a root redirect over it.

## Verified state reference
- **Live to users:** no PUBLIC site. v2 is on `football-data-pipeline-gcp.web.app` (unlisted), every
  page `noindex`. **Nothing is published, which is why URLs are still free to change.**
- **v2 built:** design system (`system.css` + 26 components), fixture page, team page (3 tabs), nav
  shell (#825), page-spec + SEO contract (#826/#844), **metric labels per locale (#879)**.
  `.shell`/`.page-grid`/`.rail` wired into zero pages; team/fixture stay at 680px `.inner`.
- **Datasets:** base + seeds in `dbt_analytics`; also `staging`, `core`, `marts`, `ci_*`.
  `generate_schema_name` prefixes non-prod targets, but **never run a local `dbt build`.**
- **Tests:** 258 governance (`tests/test_governance_hooks.py`), 59 site (`cd site_v2 && npm test`).
