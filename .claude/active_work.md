# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`; `wc -c` counts BYTES and
> over-reports by ~220 here, which will send you trimming content that fits.

_Last updated **2026-08-07**. main GREEN at **290bac0**. **NOTHING IN FLIGHT — no open MRs.**
The product is **Matchday Pilot**. **The repo is on GITLAB** (`glab`, MRs, `.gitlab-ci.yml`).
GitHub is KEPT but dormant — its Actions run nothing and its 114 issues are unreachable;
`.github/workflows/README.md` says so at the tree, and says what re-arms it.

Merged 2026-08-06/07: **!6-!17** (see `git log`), then **!18** #29, **!19** #25, **!20** the CI
lint backstop, **!21** deleted the stale architecture plan.

## ⭐ AN AUDIT FINDS; IT DOES NOT DECIDE. Read this before touching the stream.

A 59-finding audit ran 2026-08-05/06 to align this repo with **Anthropic's guidance on working with
Claude Code**, and produced 29 issues. **Every one of them ADDS something.**

On 2026-08-07 the CPO asked whether that was replicable or an artifact of one long session. A COLD
re-run of `/audit-agent-setup` — fresh context, no knowledge of the first run's conclusions —
answered it, and the full report is **GitLab #30**:

**The findings replicate. The prioritisation does not.** Six major findings reproduced
independently. The framing did not: the cold run's FIRST recommendation was **deletion**. Same
repo, same skill, opposite first move.

⭐ **So the output of an audit is a list of LEADS TO VERIFY, never a work list to execute.** Two of
the cold run's four deletion targets did not survive checking (the ingestion blueprint is live and
referenced by `batch_fixtures.py:24`; the `~/.claude` hook copies are unversioned and inside open
#21), and it missed a third stale doc entirely. **Treating the first audit's 29 items as a plan is
what cost 2026-08-07 its afternoon.** Do not repeat it.

**What actually remains of the stream: TWO build items. Everything else is a decision.**
- BUILD: **#20** (refuses EVERY push while on `main`, even deleting a merged branch — judged by
  location, not target) · a check that a contract's factual claims hold against the tree (unfiled,
  and #30's evidence ranks it ABOVE the hook telemetry #30 itself put first).
- CPO's: **#15, #16, #21, #27**, plus **#5, #14, #18, #26, #28**, each of which concludes in its
  own text that the call is his. **#26**: a keyword matcher was tried and WITHDRAWN — rules and
  history are the same English, and a false hit fires on a real RULE. **#28**: cause is SEQUENCING;
  write the log entry and the override as ONE action.

**Why mechanism beats wording — now measured, in #30:** of 50 recorded corrections, **33 are prose
only, 22 recurred, and every rule that got a mechanism stopped recurring.** The unmechanised
clusters are VERIFICATION and ESCALATION: 10 rules, 8 recurrences, 0 mechanisms.

**⚠ GUARDS WIRED IN !8.** Stop hook runs 5 offline gates (~2.9s), blocks once · copy gate in CI ·
5 USER-LEVEL hooks in `~/.claude/settings.json` (hard deny on pushing `main`, see #20; plan-back
prompt on the first code edit) · `scope-auditor` on sonnet.

**⚠ OPERATIONAL NOTES LIVE IN `CLAUDE.md` (!9)** — dbt CLI, SQLFluff, commit mechanics, the
stash-dance, CWD/fnmatch/heredoc/grep traps, frontend. **Do not copy them back**: that file is not
capped, this one is._

**FIRST ACTIONS: `git stash list` before any git work.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX —
indices move on every stash, and this file carried a stale one twice. The one that must not be
rebuilt: message contains **`feat/player-overview-tab: Overview BUILT`**._

## ⭐ The ingest cluster is CLOSED but UNVERIFIED

Four fixes merged and live; **NO PRODUCTION RUN HAS EXERCISED ANY OF THEM**, and none will —
`data:nightly` has **no SCHEDULE**, so it is reachable only by manual web dispatch. A live gap.

Verify: `glab ci list`, then `glab ci trace <id>` grepping `data:nightly` for `rateLimit: Too many
requests`. Expect **zero** drops and ~**98 min** rather than 63 (08-03: 6 drops in 1h16m38s; 08-02:
26). If materially off, the 1.55x pacing estimate was wrong — say so with the log output.

**What each does NOT do:** #897 cuts the failure RATE only · #896 stops the LOSS but does not make
failure visible · #898 hard-fails on STAGNATION, not completeness · cause 3 gates
players/squads/transfers but **COACHES reports only** (~23 teams genuinely have none).

**Standing facts, each of which corrected a wrong assumption:** Ultra plan **450/min, 75,000/day**,
daily draw ~8,300, so the PER-MINUTE limit binds, never the daily · transfers healing is OBSERVED
(`load_transfers_batch` is append-only) · per-team data was COMPLETE at 08-03, so cause 3 starts
green. **No public site, so no user impact** — never present this as a live incident.

## ⭐ COST — read **GitLab issue #3** before touching anything

#547's comment is unreachable (GitHub). Everything recoverable is in **GitLab #3** — baselines, the
ranked list, the free tools, MEASURED vs UNMEASURED. Read it there; do not redo it. Traps:

- **⚠ NEVER set a time-based partition expiry on raw** (#892). Nine biennial/quadrennial
  tournaments are `ingest_active` and go months without a refresh in poll mode; expiry would delete
  the ONLY surviving row and staging's `qualify` would silently return zero rows for that league.
  Use keep-latest-per-`(table, league_code)`. **A fixed lookback window has the same defect.**
- **⚠ Do NOT claim the API quota "breaks first".** `standings.py:30` and `teams.py:28` do loop every
  configured season daily with no skip, which is real and worth fixing. But the daily quota number
  is not in the repo and #547 assessed the API budget as fine. Claimed once without evidence,
  withdrawn.
- **⭐ Two FREE tools: `bq query --dry_run`** (exact bytes, nothing runs — use it to CHOOSE a query
  shape) and **`scripts/report_bq_cost.py`** (read-only INFORMATION_SCHEMA, spend by workload/node).
  The 2026-08-06 stop on the latter was **LIFTED 2026-08-07** (`escalations.log`).
- ⚠ **Paste the command output or do not claim it.** Three completeness claims in #547 were wrong.
- **#547's ranked list lives in GitLab #3, in ITS order** — read it there. Top items: fetch-side
  skip on `/standings` `/teams` `/coachs` `/injuries` (API VOLUME, not a proven quota breach) ·
  **#895** ~$9.96/35d, needs the slim-vs-drop call · **#892** ~$2/mo.
- **MEASURED 08-03: $2.73/day**, prod tests $1.46 vs models $0.75; top single cost
  `not_null_stg_apif__transfers_raw_ingested_at` at $0.30/day — a test on a STAGING view rescanning
  6.99 GiB. **The two-step read is the cheap shape** (7.51 GB vs 384 MB vs 14.8 KB); see
  `completeness.py::_latest_snapshot_timestamps`.
- **⚠ #2 IS LIVE AND IT FIRED ON 2026-08-07.** `data:build:main` triggers on `data_paths`
  (`.gitlab-ci.yml:230`), which includes `.gitlab-ci.yml` and `scripts/check_*.py` — so !15, a
  governance/docs MR that changed a COMMENT and a gate script, rebuilt the whole prod warehouse.
  **Check `data_paths` before putting those files in an MR.**

## ⭐ REVIEW MECHANICS — what you cannot derive from the working agreement

Rules are `docs/working_agreement.md` §2 (#878). Only the traps live here.

- **Build the patch with the hook, never by hand:**
  `python .claude/hooks/git_discipline.py --review-patch > .claude/task/review_input.patch`
  Cumulative from base. Reviewers do NOT see task notes; `contract.md` + `escalations.log` ARE
  delivered, because they carry authority. `site_v2/src/data/**` is a MANIFEST, not pasted — it
  still binds the hash, so grep those files directly. Now also emits a trailer naming any excluded
  file that IS edited (#25/!19), so absence is no longer evidence a file was untouched.
- **Run `check_task_artifacts.py` BARE** (#24, !15) — it resolves the live remote itself.
  `GOVERNANCE_BASE` overrides. ⚠ On a multi-commit branch `--staged-hash` is the WRONG number; it
  covers only the increment. Collapse with `git reset --soft <base>` so local and CI agree.
- **A PASS may find nothing.** One `risks_checked:` entry is enough. Never invent a finding. Cap is
  3 rounds, then STOP and bring open findings to the CPO.
- **`.claude/task/**` is scope-exempt; `.claude/active_work.md` is NOT** — it must be in
  `scope_paths`. A commit touching `contract.md` is **never** artifact-exempt.
- **The org does NOT change** (CPO ruling): low activation is not a defect. Do not cut reviewers.
- **⭐ A correction REPLACES, never accumulates.** No "an earlier version said X", no round tallies.
  ⚠ And it must replace in the PERMANENT artifacts too, not only the contract — !20 corrected a
  false premise in `contract.md` while leaving it verbatim in the CI comment and the config header.

## THE GOAL
A football-stats site a fan actually uses. Data honesty is non-negotiable — the CPO cannot verify
numbers by hand, so every number is covered by an automated test. **Daily freshness is required.**

## Player page + the next CPO decision
**#846 + #886 merged:** the season a page opens on is a warehouse fact (`is_featured_season` on both
profile marts, with a DQ guard). **CPO ruling: the pipeline picks, not the page**, and "most recent"
is scoped by the LENS the tab shows (club tabs = most recent CLUB season).

**#845 + #882 are ONE decision and his.** Which entities earn a page, and whether a past season gets
a URL or a control. Deciding apart sets the URL shape twice. Measured (×3 locales): players
51,589→154,767 pages; **matches are BIGGER at 176,235**; h2h 51,903; teams 9,669. With a per-season
gate of 5 matches: 1,274 teams and 21,979 players qualify. Bring counts, not a general question.

**The player Overview is BUILT but UNCOMMITTED**, in the stash named above, with a known-wrong
default (`seasons[0]` = most recent of ANY competition, so both samples open on WC 2026). Its mart
half IS shipped, so it is a one-line change when it resumes. Held on #845.
**#848: the player page is FOUR tabs** — Overview/Performance/Career are **club only**;
International is a national-lens TAB (not a toggle: a crawler cannot follow a control), shown only
when `national_appearances_total >= 1`. Read #848 first; four CPO-class consequences are open.

## DESIGN DISCIPLINE (the weak spot)
Never design off the cuff. Use approved wireframes and role briefs. Never invent a block to fill a
slot, never design the canonical page around an edge case, build ONE tab at a time. **Show rendered
output, not prose; copy is ALWAYS his (§10)** — gather copy decisions UP FRONT, before the branch.

## OWED — deferred, not forgotten
- **The round cap only RECORDS.** `ROUND_CAP = 3` is checked at commit against a number the builder
  types; nothing stops a fourth round while rounds run. CPO: tighten it later. Not tightened.
- **No gate records when it fires** — 2,684 lines of enforcement, zero telemetry (#30, finding 4).
  Only the commit gate and routing loader emit a CANARY on fail-open.
- Delete or rewrite `macros/apif_latest_source_partition.sql` — zero callers and it never pruned.
- A metric-change skill · mirror the crests · reviewers as peers (#822 shipped only the model half).
- **⭐ #904 IS THE DOMINANT FAILURE, SIX times on 2026-08-07** — a claim about the code asserted
  rather than run. Twice it was the same shape: a grep scoped narrower than the sentence it
  supported ("this repo has NO linter"; "no orphaned pointer survives", which missed `.html`).
  **A claim of ABSENCE must state where it looked, and the scope must be as wide as the claim.**
  Prose has not fixed this in six tries; it is the strongest candidate for the next mechanism.
- **#900: blueprint §4 says a full daily run is 20-50 API calls; measured ~8,300.**

## NEXT
0. **⚠ NO NIGHTLY SCHEDULE EXISTS ON GITLAB.** `data:nightly` is written and reachable only by a
   manual web dispatch. Until a schedule is created, the pipeline does not refresh and the data
   goes stale silently. Creating one is a COST decision (a nightly prod build), so it is the
   CPO's — bring it as a recipe, not a question. ⚠ **#4**: a web dispatch from ANY branch builds
   prod from THAT branch's code.
1. **The audit stream — see the ⭐ block above for what actually remains** (two build items; the
   rest decisions). ⚠ **Do NOT mix this with cost.** Separate streams; conflating them was
   corrected explicitly. Also the CPO's, unblocked and one command each: **Q2 of #21** (set
   `main`'s push access to No one, so the SERVER protects it rather than a client hook) · delete
   the two dead `~/.claude/hooks/` copies · route or delete `seo-expert-reviewer`.
2. **⭐ THEN COST, SYSTEMATICALLY — not one fix at a time.** The CPO's words: across the whole
   pipeline **including CI/CD, what gets triggered, when, and where**. Build the trigger/cost map
   FIRST, rank by real spend, then fix in that order. **The measurement stop is LIFTED
   (`escalations.log`): run `scripts/report_bq_cost.py`.** Biggest live item per GitLab #3 is that
   **staging is still a VIEW so tests re-scan raw** ($0.30/day on one test) — the same defect fixed
   for base models on 2026-08-02. `data_paths` (#2) ranks ~4th; do not start there. Map goes in a
   GitLab ISSUE, never a document.
3. **#845 + #882 — the CPO's decision.** Counts are measured and in this file: bring them, not a
   general question. Unblocks the player page off the Overview stash.
4. Read the first GitLab nightly (⭐ block above) · home page (`1c35e7aa` = reference only), **then
   legal/imprint**, then launch.
5. Follow-ups — GITHUB numbers, **bodies UNREACHABLE**; re-derive from code and re-file on GitLab
   as picked up. **#875** metric GROUP headings English on DE/FI · **#877** `GD`, `W/D/L`, `T·I·B`
   need DE/FI words · **#876** rows break mid-word · **#863** PROTECTED path editable with no
   `protected_override` · **#866** `Regular Season - 20` is provider text, invisible to the copy
   gate · **#873** routing matcher hand-copied, no parity test · **#887** MR-time DQ cannot see its
   own models · **#883** blank `competition_type` skipped by all three guards.

## OPEN — the CPO's alone
**Imprint operator + address** (#799), blocks publication, never conclude it · hosting recurring
run · the feedback Apps Script (#687) · **#850**'s alias decision · **#875** where a group name
lives · **#895 slim-vs-drop, which blocks the biggest remaining cost item** · **#21** (see NEXT 1).

## DO NOT (standing)
- Do NOT treat the tracker as agreed work; re-validate before acting.
- Do NOT write another planning document. Do NOT touch `site/` (retired/frozen).
- Do NOT derive facts in the export or frontend — select/group/rename only.
- **Never merge a PR. The CPO merges. Branch from main; never commit to main.**
- Plain language, lead with the decision, **no em dashes**, no walls of text.
- Do NOT ask him to adjudicate what a rule can settle. **But copy is ALWAYS his (§10).**
- Do NOT bring him a fix for a defect he did not ask about. Fix it and move on.

## Verified state reference
- **No PUBLIC site.** v2 is unlisted on `football-data-pipeline-gcp.web.app`, every page `noindex`.
  Nothing is published, which is why URLs are still free to change.
- **v2 built:** design system + 26 components, fixture page, team page (3 tabs), nav shell,
  page-spec + SEO contract (#826/#844), metric labels per locale (#879).
- **Tests:** **665 python** (`pytest --collect-only -q`; a run gives 664 passed + 1 skipped, ~5
  min), plus 59 site (`cd site_v2 && npm test`). ⚠ MEASURE, never predict (#904).
- **`ruff` runs in CI** as `lint:python` (!20), config **`.ruff-ci.toml`** — that filename is
  load-bearing. `tests/test_lint_config.py` says why, and pins it.
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). API-Football:
  reselling is the one hard prohibition.
