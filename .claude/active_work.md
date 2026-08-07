# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — `wc -c` counts BYTES and this file is full of multi-byte
> symbols, so it over-reports by ~220 and will send you trimming content that fits.

_Last updated **2026-08-06**. main GREEN at **cbd81aa**. The product is **Matchday Pilot**.
**The repo is on GITLAB** (`glab`, MRs, `.gitlab-ci.yml`). GitHub is KEPT but dormant — its
Actions run nothing and its 114 issues are unreachable. Merged today: **MR !6** (web dispatch
must not auto-start a prod build), **MR !7** (`4844c32`, the copy gate's 16 findings cleared).

**FIRST ACTIONS: run `git stash list` before any git work.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX —
the indices move every time anything is stashed, and on 2026-08-06 this file still pointed at
`stash@{0}` for the player Overview after it had shifted to `{1}`, which would have sent a fresh
session to pop the landing page instead. The one that must not be rebuilt is the entry whose
message contains **`feat/player-overview-tab: Overview BUILT`** (currently `{1}`)._

## ⭐ START HERE — the ingest cluster is CLOSED but UNVERIFIED. Cost is next.

The four fixes below are merged and live. **NO PRODUCTION RUN HAS EXERCISED ANY OF THEM**, and the
window to check widened rather than closed: the nightly moved hosts. It now runs as
`data:nightly` in `.gitlab-ci.yml`, reachable from a GitLab SCHEDULE or a manual web dispatch —
and **no schedule has been created yet**, so nothing is running nightly at all right now. That is
a live gap, not a background detail.

Verify with `glab ci list --per-page 5` then `glab ci trace <job-id>`, grepping the `data:nightly`
log for `rateLimit: Too many requests`. Expect **zero** drops and ingest near **98 min** rather
than 63 (08-03 baseline: 6 drops in 1h16m38s; 08-02: 26). If it lands materially off, the 1.55x
pacing estimate was wrong — say so with the log output rather than explaining it away.

**What each fix does NOT do — the limits are the part that still matters:** #897 pacing reduces
the failure RATE only · #896 stops the data LOSS but does NOT make failure visible · #898 counts
and hard-fails on STAGNATION only, and does NOT measure completeness · cause 3 gates
players/squads/transfers but **COACHES reports only** (~23 teams genuinely have no coach).

**Standing facts, each of which corrected a wrong assumption:** plan is Ultra **450/min,
75,000/day**, and daily draw ~8,300 (~11%) — so the per-minute limit is the constraint, never the
daily · transfers healing is OBSERVED (`load_transfers_batch` is append-only, so a gap is staging
masking and recoverable) · per-team data was COMPLETE at 08-03, so cause 3's gate starts green and
can only fire on a regression.

**No user impact: there is no public site.** Do not present any of this as a live incident.

## ⭐ COST — read **GitLab issue #3** before touching anything

#547's comment WAS the durable record and is now unreachable (GitHub). Everything recoverable was
copied into **GitLab #3 "Cost knowledge recovery"** — baselines, the ranked list, the free tools,
and which figures are MEASURED vs UNMEASURED. Read it there; do not redo the analysis. Key traps:

- **⚠ NEVER set a time-based partition expiry on raw** (#892 comment). Nine biennial/quadrennial
  tournaments are `ingest_active` and go months to years without a refresh in poll mode; expiry would
  delete the ONLY surviving row and staging's `qualify` would return zero rows for that league,
  silently. Use keep-latest-per-`(table, league_code)` instead. **A fixed lookback window has the same
  defect** — the #892 fix must compute per-league maxima.
- **⚠ Do NOT claim the API quota "breaks first".** `standings.py:30` and `teams.py:28` do loop every
  configured season daily with no skip, which is real and worth fixing. But the daily quota number is
  not in the repo, and Thread 1 + #547 both assessed the API budget as fine. That claim was made this
  session without evidence and withdrawn.
- **⭐ Two FREE tools, use them: `bq query --dry_run`** (exact bytes, nothing runs — use it to CHOOSE
  a query shape) and **`python scripts/report_bq_cost.py`** (read-only INFORMATION_SCHEMA, spend by
  workload/node). ⚠ The CPO instructed on 2026-08-06 that `report_bq_cost.py` not be run — check
  `escalations.log` before running it.
- ⚠ **Paste the command output or do not claim it.** Three completeness claims in #547 were wrong.
- **#547's ranked list, in ITS order** (full text in GitLab #3): 1 ingest cluster DONE · 2 fetch-side
  skip on `/standings` `/teams` `/coachs` `/injuries`, an API-VOLUME finding and NOT a proven quota
  breach · 3 `pages-match-preview.yml` — **now $0, never translated to GitLab; returns only if
  GitHub is reactivated** · 4 **#895** ~$9.96/35d, needs the slim-vs-drop call · 5 **#892** ~$2/mo ·
  6 guards (`require_partition_filter`, `maximum_bytes_billed`), neither set · 7 merge-on-write.
- **MEASURED 08-03: $2.73/day**, prod tests $1.46 vs models $0.75. The top cost is now
  `not_null_stg_apif__transfers_raw_ingested_at` at $0.30/day — a test on a STAGING view rescanning
  6.99 GiB. **The two-step read is the proven cheap shape**: subquery-MAX predicate 7.51 GB vs
  literal timestamps 384 MB vs maxima alone 14.8 KB. Rationale in
  `completeness.py::_latest_snapshot_timestamps`; figures in GitLab #3.

## ⭐ REVIEW MECHANICS — what you cannot derive from the working agreement

Rules are `docs/working_agreement.md` §2 (#878). Only the traps live here.

- **Build the patch with the hook, never by hand:**
  `python .claude/hooks/git_discipline.py --review-patch > .claude/task/review_input.patch`
  Cumulative from base. Reviewers do NOT see task notes; `contract.md` + `escalations.log` ARE
  delivered, because they carry authority. `site_v2/src/data/**` is summarised as a MANIFEST,
  not pasted — it still binds the hash, so reviewers must grep those files directly.
- **A PASS may find nothing.** One `risks_checked:` entry is enough. Never invent a finding. Cap is
  3 rounds, then STOP and bring open findings to the CPO.
- **`.claude/task/**` is scope-exempt; `.claude/active_work.md` is NOT** — it must be in
  `scope_paths`. And a commit touching `contract.md` is **never** artifact-exempt, so even a
  bookkeeping commit needs a scope audit.
- **The org does NOT change** and the CPO ruled on it: activation-on-necessity is right, low
  activation is not a defect. Do not propose cutting reviewers.
- **⭐ A correction REPLACES, never accumulates.** No "an earlier version said X", no round tallies.

## THE GOAL
A football-stats site a fan actually uses. Data honesty is non-negotiable — the CPO cannot verify
numbers by hand, so every number is covered by an automated test. **Daily freshness is required.**

## Player page + the next CPO decision
**#846 + #886 merged:** the season a page opens on is a warehouse fact (`is_featured_season` on both
profile marts, with a DQ guard). **CPO ruling: the pipeline picks, not the page**, and "most recent"
is scoped by the LENS the tab shows (club tabs = most recent CLUB season).

**#845 + #882 are ONE decision and his.** Which entities earn a page, and whether a past season gets a
URL or a control. Deciding apart sets the URL shape twice. Measured counts (×3 locales): players
51,589→154,767 pages; **matches are BIGGER at 176,235**; h2h 51,903; teams 9,669. With a per-season
gate of 5 matches: 1,274 teams and 21,979 players qualify. Bring counts, not a general question.

**The player Overview is BUILT but UNCOMMITTED in `stash@{0}`** with a known-wrong default rule
(`seasons[0]` = most recent of ANY competition, so both samples open on World Cup 2026). Its mart half
IS shipped, so it is a one-line change when it resumes. Held on #845.
**#848: the player page is FOUR tabs** — Overview/Performance/Career are **club only**; International
is a national-lens TAB (not a toggle: a crawler cannot follow a control), shown only when
`national_appearances_total >= 1`. Read #848 before shaping it; four CPO-class consequences are open.

## DESIGN DISCIPLINE (the weak spot)
Never design off the cuff. Use approved wireframes and role briefs. Never invent a block to fill a
slot. Never design the canonical page around an edge case. Build ONE tab at a time.
**Show rendered output — never ask the CPO to rule on prose in the abstract.**
**Copy is ALWAYS his (§10).** Gather copy decisions UP FRONT in one pass, before the branch.

## OWED — deferred, not forgotten
- **The round cap only RECORDS.** `ROUND_CAP = 3` is checked at commit against a number the builder
  types; nothing stops a fourth round while rounds run. CPO: tighten it later. Not tightened.
- **No gate records when it fires** — ~2,500 lines of enforcement, near-zero telemetry. Highest-value
  follow-up in the repo. Partly addressed 2026-08-06: the commit gate and routing loader now emit a
  CANARY when they fail open, so a dead gate is no longer silent. Nothing else is instrumented.
- ~~The copy gate is wired to nothing~~ **DONE 2026-08-06.** MR !7 cleared its 16 findings, then it
  was wired into `validate:governance` + `validate-local` + the Stop hook.
- Delete or rewrite `macros/apif_latest_source_partition.sql` — zero callers and it never pruned.
- A metric-change skill · mirror the crests · reviewers as peers (#822 shipped only the model half).
- **#904: contract claims about the code are unverified.** SEVEN false factual statements in one
  task's `contract.md`, every one caught in review, costing five rounds and two cap overrides on a
  task whose CODE passed cleanly. Cause: the contract is written BEFORE the code, so its claims are
  predictions, and nothing re-reads it against the finished tree. Measurements never failed because
  producing them verified them. **Until the lint exists: grep every "is tested / is read / has N
  callers / gains N arguments" claim before writing it**, and never count test-file call sites.
- **#900: blueprint §4 says a full daily run is 20-50 API calls; measured ~8,300.**

## NEXT
0. **⚠ NO NIGHTLY SCHEDULE EXISTS ON GITLAB.** `data:nightly` is written and reachable only by a
   manual web dispatch. Until a schedule is created, the pipeline does not refresh and the data
   goes stale silently. Creating one is a COST decision (a nightly prod build), so it is the
   CPO's — bring it as a recipe, not a question.
1. **Read the first GitLab nightly** (⭐ block above). First evidence for any of the four fixes.
2. **#845 + #882 — the CPO's decision, and the ONLY unblocked next step.** Counts are measured and
   in this file: bring them, not a general question. Unblocks the player page off the Overview stash.
3. **COST IS PARTLY BLOCKED, which is why it is not step 2.** #547's #2 is unmeasured, #895 needs
   the CPO's slim-vs-drop call, and the staging-view fix changes a LAYER materialisation, which is
   CPO-class. What IS unblocked: **measure a QUIET day** (08-03 ran every node 7x because four PRs
   merged, so its $2.73 overstates a normal day).
4. Home page (`1c35e7aa` = reference only), **then legal/imprint**, then launch.
5. Follow-ups: **#875** metric GROUP headings in English on DE/FI, needs a CPO ruling on where a group
   name lives · **#877** `GD`, `W/D/L`, `T·I·B` need the DE/FI words · **#876** rows break mid-word ·
   **#863** PROTECTED path editable with no `protected_override` · **#866** `Regular Season - 20`
   untranslated · **#873** routing matcher hand-copied, no parity test · route `seo-expert-reviewer`
   (the only reviewer with no routing row) · **#887** the PR-time DQ step cannot see the PR's own
   models · **#883** blank `competition_type` skipped by all three guards.

## OPEN — the CPO's alone
**Imprint operator + address** (#799), blocks publication, never conclude it · hosting recurring run ·
the feedback Apps Script (#687) · **#850**'s alias decision · **#875** where a group name lives ·
**#895 slim-vs-drop, which blocks the biggest remaining cost item**. (#898's threshold policy is
DECIDED and shipped: visible always, fail only on stagnation.)

## DO NOT (standing)
- Do NOT treat the tracker as agreed work; re-validate before acting.
- Do NOT write another planning document. Do NOT touch `site/` (retired/frozen).
- Do NOT derive facts in the export or frontend — select/group/rename only.
- **Never merge a PR. The CPO merges. Branch from main; never commit to main.**
- Plain language, lead with the decision, **no em dashes**, no walls of text.
- Do NOT ask him to adjudicate what a rule can settle. **But copy is ALWAYS his (§10).**
- Do NOT bring him a fix for a defect he did not ask about. Fix it and move on.

## Operational notes
- **The dbt CLI is NOT broken; the one on PATH is.** Use `.venv/Scripts/dbt.exe` (1.7.19 + bigquery
  1.7.2, the `requirements.txt` pin) with `DBT_PROFILES_DIR=C:/Users/Rami/.dbt`: `parse`, `ls`,
  `ls --select <model>+` all work. Use it for `impact_map` lineage. **Never run `dbt build`** (shared
  prod dataset).
- **SQLFluff: lint from the REPO ROOT** (root `.sqlfluff` has the jinja macro path):
  `python -m sqlfluff lint <model> --templater jinja --dialect bigquery`, FULL rule set. `dbt_utils`
  is unresolvable under the jinja templater, so `mart_player_profile` reports pre-existing TMP/PRS
  noise — check against main before believing it. BigQuery rejects a FROM-less WHERE.
- **Commit mechanics:** `git commit` runs alone (no chaining, no leading `cd`); `--amend`
  gate-blocked. Use `git commit -F <file>`. Write messages to the scratchpad. A post-commit hook
  auto-pushes and opens the **MR**. `review.md` must be COMMITTED, with `## <reviewer-name>`
  section headers — the gate parses those exactly, a `verdicts:` block alone does NOT satisfy it.
- **⚠ The Stop hook now runs the five offline gates** (~2.9s) when the tree is dirty and in scope,
  and BLOCKS the turn once if any fails. Expect it; do not end a turn on a red gate silently.
- **⚠ ON A SECOND COMMIT `--staged-hash` IS THE WRONG NUMBER** — it covers only the increment; CI
  recomputes over the whole branch. Use `check_task_artifacts.py --base origin/main`. A
  `review.md`-only commit is artifact-exempt, so rebinding is free.
- **Contract edits need a CLEAN tree** — stash-dance with explicit paths, then check `git stash list`.
- **⚠ CWD PERSISTS between Bash calls.** **⚠ `fnmatch`'s `*` CROSSES `/`**, and `scope_paths`'
  `[lang]`/`[team]` are CHARACTER CLASSES — use `site_v2/src/pages/*/teams/*.astro`.
- **⚠ Heredocs are blocked for file writes** — use Edit/Write, including for scratchpad files.
- **⚠ A line-based grep misses a phrase straddling a line break.** Sweep whitespace-collapsed.
- **Frontend:** `deploy-site-v2.yml` is manual-only. The Browser pane drives the dev server
  (`preview_start` name `v2`); accessibility tree, geometry and console work, `screenshot` fails.
  `astro build` OOMs at full scale; `git clean -fX site_v2/src/data` before a local dev build.

## Verified state reference
- **No PUBLIC site.** v2 is unlisted on `football-data-pipeline-gcp.web.app`, every page `noindex`.
  Nothing is published, which is why URLs are still free to change.
- **v2 built:** design system + 26 components, fixture page, team page (3 tabs), nav shell,
  page-spec + SEO contract (#826/#844), metric labels per locale (#879).
- **Tests:** **583 python** (measured 2026-08-03, `.venv/Scripts/python.exe -m pytest tests/ -q`),
  plus 59 site (`cd site_v2 && npm test`). The governance count is not re-measured here.
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). API-Football:
  reselling is the one hard prohibition.
