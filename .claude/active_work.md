# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — `wc -c` counts BYTES and this file is full of multi-byte
> symbols, so it over-reports by ~220 and will send you trimming content that fits.

_Last updated **2026-08-07**. main GREEN at **6238dc4**. **NOTHING IN FLIGHT — no open MRs.**
The product is **Matchday Pilot**. **The repo is on GITLAB** (`glab`, MRs, `.gitlab-ci.yml`).
GitHub is KEPT but dormant — its Actions run nothing and its 114 issues are unreachable;
`.github/workflows/README.md` says so at the tree, and says what re-arms it.

Merged 2026-08-06/07 (`git log` for detail): **!6** web dispatch, **!7** copy-gate defects, **!8**
six guards wired, **!9** GitHub marked dormant, **!10 + !11** handover, **!12** GitLab #1.

## ⭐ THE COLLABORATION AUDIT IS CLOSED OUT — its follow-ups are ISSUES, not this file

A 59-finding audit ran 2026-08-05/06 and its 12-item plan is **SPENT** (8 executed in !7–!11, 3
filed, 1 dropped). Do NOT re-derive it. **What remains is `glab issue list`.** That half was left
deliberately: each item needs a judgement about what a rule should SAY, not where to plug it in.

- **#1 is DONE (!12).** `tests/test_governance_doc_parity.py` derives the guard-path counts and the
  protected-path list from `review_routing.json` + `task_contract_gate.py` and fails when prose
  disagrees. Lists are matched by CONTENT, not phrasing, so a new one anywhere is checked. It found
  a TWELFTH restatement site on its first run (#22). **#19 IS NEXT** and is its own session:
  "compile, don't append", every governing artifact 50-60% its own changelog; nothing deleted, only
  moved to git + `escalations.log`.
- **#5** Confirm still has no real enforcement — the installed hook is an ADVISORY, it cannot
  deny. Related and unfiled: `docs/working_agreement.md` is **opt-in**, 26KB of "non-negotiable"
  rules with zero `@` imports. That was the audit's top-ranked finding.
- **#14** plugin injects 10 unpinned MCP servers · **#15** escalation default · **#16 + #18** the
  two ways the scope boundary bounds itself · **#17** three dead i18n keys.
- **Filed 2026-08-07.** **#20** `branch_discipline.py` refuses EVERY push while you are on `main`,
  including deleting a merged branch, because it judges by location not target; blocked on **#21**
  (in OPEN below). GitLab `main` IS protected, but at Maintainer while the account is Owner, so the
  hook is the only hard block. · **#22 + #23** two protected-path prose fixes, same class · **#24**
  the governance base, see REVIEW MECHANICS.

**Why mechanism beats wording:** every WIRED guard held; the only failures were commitments left in
PROSE. `/audit-agent-setup` at user level re-runs this audit on any project.

**⚠ GUARDS WIRED IN !8 — expect different behaviour.** Stop hook runs 5 offline gates (~2.9s) and
blocks once on failure · copy gate runs in CI · 5 USER-LEVEL hooks in `~/.claude/settings.json`
(hard deny on pushing `main`, see **#20**; plan-back prompt on your first code edit) ·
`scope-auditor` on sonnet.

**⚠ OPERATIONAL NOTES ARE IN `CLAUDE.md` NOW (!9), not here** — dbt CLI, SQLFluff, commit
mechanics, stash-dance, CWD/fnmatch/heredoc/grep traps, frontend. This file is capped at 16,000
chars and DROPS ITS TAIL; `CLAUDE.md` is never truncated. **Do not copy them back.**_

**FIRST ACTIONS: run `git stash list` before any git work.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX —
indices move whenever anything is stashed, and this file carried a stale one twice, which would
have sent a session to pop the landing page instead. The entry that must not be rebuilt is the one
whose message contains **`feat/player-overview-tab: Overview BUILT`**._

## ⭐ START HERE — the ingest cluster is CLOSED but UNVERIFIED. Cost is next.

The four fixes below are merged and live. **NO PRODUCTION RUN HAS EXERCISED ANY OF THEM**, and
none will: `data:nightly` moved into `.gitlab-ci.yml` and **no SCHEDULE exists**, so it is
reachable only by a manual web dispatch. A live gap, not a background detail.

Verify with `glab ci list --per-page 5` then `glab ci trace <job-id>`, grepping the `data:nightly`
log for `rateLimit: Too many requests`. Expect **zero** drops and ingest near **98 min** rather
than 63 (08-03 baseline: 6 drops in 1h16m38s; 08-02: 26). If it lands materially off, the 1.55x
pacing estimate was wrong — say so with the log output rather than explaining it away.

**What each fix does NOT do, which is the part that matters:** #897 pacing reduces the failure RATE
only · #896 stops the data LOSS but does NOT make failure visible · #898 hard-fails on STAGNATION
only and does NOT measure completeness · cause 3 gates players/squads/transfers but **COACHES
reports only** (~23 teams genuinely have no coach).

**Standing facts, each of which corrected a wrong assumption:** plan is Ultra **450/min,
75,000/day**, daily draw ~8,300 (~11%), so the per-minute limit is the constraint, never the daily
· transfers healing is OBSERVED (`load_transfers_batch` is append-only, so a gap is staging masking
and recoverable) · per-team data was COMPLETE at 08-03, so cause 3's gate starts green.

**No user impact: there is no public site.** Do not present any of this as a live incident.

## ⭐ COST — read **GitLab issue #3** before touching anything

#547's comment was the durable record and is unreachable (GitHub). Everything recoverable is in
**GitLab #3 "Cost knowledge recovery"** — baselines, the ranked list, the free tools, and which
figures are MEASURED vs UNMEASURED. Read it there; do not redo the analysis. Key traps:

- **⚠ NEVER set a time-based partition expiry on raw** (#892). Nine biennial/quadrennial
  tournaments are `ingest_active` and go months to years without a refresh in poll mode; expiry
  would delete the ONLY surviving row and staging's `qualify` would silently return zero rows for
  that league. Use keep-latest-per-`(table, league_code)`. **A fixed lookback window has the same
  defect** — #892 must compute per-league maxima.
- **⚠ Do NOT claim the API quota "breaks first".** `standings.py:30` and `teams.py:28` do loop every
  configured season daily with no skip, which is real and worth fixing. But the daily quota number
  is not in the repo and #547 assessed the API budget as fine. Claimed once without evidence and
  withdrawn.
- **⭐ Two FREE tools, use them: `bq query --dry_run`** (exact bytes, nothing runs — use it to CHOOSE
  a query shape) and **`python scripts/report_bq_cost.py`** (read-only INFORMATION_SCHEMA, spend by
  workload/node). ⚠ The CPO instructed on 2026-08-06 that `report_bq_cost.py` not be run — check
  `escalations.log` before running it.
- ⚠ **Paste the command output or do not claim it.** Three completeness claims in #547 were wrong.
- **#547's ranked list is in GitLab #3, in ITS order.** Still live, in that order: fetch-side skip
  on `/standings` `/teams` `/coachs` `/injuries` (an API-VOLUME finding, NOT a proven quota breach)
  · **#895** ~$9.96/35d, needs the slim-vs-drop call · **#892** ~$2/mo · two unset guards
  (`require_partition_filter`, `maximum_bytes_billed`) · merge-on-write.
- **MEASURED 08-03: $2.73/day**, prod tests $1.46 vs models $0.75. The top cost is now
  `not_null_stg_apif__transfers_raw_ingested_at` at $0.30/day — a test on a STAGING view rescanning
  6.99 GiB. **The two-step read is the proven cheap shape**: subquery-MAX predicate 7.51 GB vs
  literal timestamps 384 MB vs maxima alone 14.8 KB. Rationale in
  `completeness.py::_latest_snapshot_timestamps`.

## ⭐ REVIEW MECHANICS — what you cannot derive from the working agreement

Rules are `docs/working_agreement.md` §2 (#878). Only the traps live here.

- **Build the patch with the hook, never by hand:**
  `python .claude/hooks/git_discipline.py --review-patch > .claude/task/review_input.patch`
  Cumulative from base. Reviewers do NOT see task notes; `contract.md` + `escalations.log` ARE
  delivered, because they carry authority. `site_v2/src/data/**` is summarised as a MANIFEST,
  not pasted — it still binds the hash, so reviewers must grep those files directly.
- **⚠ LOCALLY THE ARTIFACT GATE NEEDS `--base gitlab/main`.** `origin` is the DORMANT GITHUB
  remote here and GitLab only in CI, so the `origin/main` spelling in `CLAUDE.md:120` and in the
  script's own default diffs against a stale tree and FALSE-FAILS, naming reviewers that are not
  required. Observed 2026-08-07. Filed as **#24**; until it is fixed, pass the base explicitly.
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

**The player Overview is BUILT but UNCOMMITTED**, in the stash whose message contains
`feat/player-overview-tab: Overview BUILT` (NEVER by index), with a known-wrong default rule
(`seasons[0]` = most recent of ANY competition, so both samples open on World Cup 2026). Its mart half
IS shipped, so it is a one-line change when it resumes. Held on #845.
**#848: the player page is FOUR tabs** — Overview/Performance/Career are **club only**; International
is a national-lens TAB (not a toggle: a crawler cannot follow a control), shown only when
`national_appearances_total >= 1`. Read #848 before shaping it; four CPO-class consequences are open.

## DESIGN DISCIPLINE (the weak spot)
Never design off the cuff. Use approved wireframes and role briefs. Never invent a block to fill a
slot. Never design the canonical page around an edge case. Build ONE tab at a time. **Show rendered
output; never ask the CPO to rule on prose in the abstract. Copy is ALWAYS his (§10)** — gather
copy decisions UP FRONT in one pass, before the branch.

## OWED — deferred, not forgotten
- **The round cap only RECORDS.** `ROUND_CAP = 3` is checked at commit against a number the builder
  types; nothing stops a fourth round while rounds run. CPO: tighten it later. Not tightened.
- **No gate records when it fires** — ~2,500 lines of enforcement, near-zero telemetry.
  Highest-value follow-up in the repo. Partly addressed 2026-08-06: the commit gate and routing
  loader emit a CANARY when they fail open. Nothing else is instrumented.
- Delete or rewrite `macros/apif_latest_source_partition.sql` — zero callers and it never pruned.
- A metric-change skill · mirror the crests · reviewers as peers (#822 shipped only the model half).
- **#904: contract claims about the code are unverified.** SEVEN false statements in one
  `contract.md`, all caught in review, five rounds, on a task whose CODE passed cleanly. Cause: the
  contract is written BEFORE the code, so its claims are predictions and nothing re-reads it
  against the finished tree. Measurements never failed, because producing them verified them.
  **Grep every "is tested / is read / has N callers" claim before writing it**; never count
  test-file call sites.
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
5. Follow-ups. ⚠ **GITHUB numbers — bodies UNREACHABLE.** The line here is all that survives:
   re-derive from code, and re-file on GitLab as you pick each up. **#875** metric GROUP headings
   English on DE/FI (needs a CPO ruling on where a group name lives) · **#877** `GD`, `W/D/L`,
   `T·I·B` need DE/FI words · **#876** rows break mid-word · **#863** PROTECTED path editable with
   no `protected_override` · **#866** `Regular Season - 20` untranslated, provider text so the copy
   gate cannot see it · **#873** routing matcher hand-copied, no parity test · route
   `seo-expert-reviewer`, still the only unrouted reviewer · **#887** MR-time DQ cannot see its own
   models · **#883** blank `competition_type` skipped by all three guards.

## OPEN — the CPO's alone
**Imprint operator + address** (#799), blocks publication, never conclude it · hosting recurring run ·
the feedback Apps Script (#687) · **#850**'s alias decision · **#875** where a group name lives ·
**#895 slim-vs-drop, which blocks the biggest remaining cost item** · **#21** which layer owns
branch protection, and whether `~/.claude` gets version control.

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
- **Tests:** **645 python** (measured 2026-08-07, `.venv/Scripts/python.exe -m pytest tests/ -q`,
  ~4.5 min), plus 59 site (`cd site_v2 && npm test`).
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). API-Football:
  reselling is the one hard prohibition.
