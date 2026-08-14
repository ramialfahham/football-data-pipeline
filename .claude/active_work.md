# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`; `wc -c` counts BYTES and
> over-reports by ~220 here, which will send you trimming content that fits.

_Last updated **2026-08-14**. **ONE MR OPEN: `!27`** (home page — code done, rebased, waiting on the
CPO). Merged since 08-12: **#63**, **#33 items 9/14/15**, **#65**, **#57**. The product is **Matchday
Pilot**; the repo is on **GITLAB** (`glab`, MRs, `.gitlab-ci.yml`). GitHub is KEPT but dormant — its
Actions run nothing and its 114 issues unreachable; `.github/workflows/README.md` re-arms it.
⚠ **CI WORKS AGAIN** — a self-hosted runner (`ci-runner-01`) serves this project, so jobs burn ZERO
GitLab minutes; the old "no minutes" note is dead. ⚠ **A GROUP MOVE IS COMING** and it changes the
project PATH — breaking remote URLs, the WIF binding pinned to `attribute.project_path`, and every
hardcoded `rami.al-fahham/football-data-pipeline`. Check before starting anything path-dependent._

## ⭐ CURRENT — `!27` IS THE ONLY THING IN FLIGHT (2026-08-14)

`feat/367-landing-page` → **!27**, collapsed to one commit, rebased onto `2644989`. 8 rounds, 5
reviewers, closed 08-09. **Home ships TWO of four modules: next matches → browse.** Top players and
Top teams are DESIGNED, NOT BUILT and slot BETWEEN the two — browse sits at the bottom deliberately
so the follow-up inserts rather than rearranges. Trending and the stats teasers were **CUT, not
deferred** (criteria 3 and 4 struck).

⛔ **THE DESIGN AUTHORITY IS GITLAB #40 (players) AND #41 (teams), NOT `10_home.md` §0**, which is
wrong on both (it says nine player boards, six team boards, top 5; the truth is FOUR boards of ONE
metric each, top 7). The reviewed mocks are gone; the issues are the record, and they carry the spec
edits the build MR must make. Open follow-ups, all with full bodies on the tracker: **#36** (blocks
go-live #377) · **#38** (blocked until !27 merges) · **#42** · **#43** · **#44** · **#45**.

⚠ **THE REBASE TAX IS THE STANDING COST, and it is paperwork-only.** Every merge to main rewrites
the four `.claude/task/*` artifacts, so EVERY open branch conflicts there and nowhere else. **MINE**
for contract/review/review_input; **UNION** `escalations.log` by ARITHMETIC, never by eye. ⚠ **Do
NOT assume the union is `main + (mine − base)`** — !27 INSERTS at the top AND appends at the bottom,
so a two-part union silently drops its head block. Diff the opcodes; refuse anything that is not a
pure insertion. Then REBIND `diff_sha256`. ⚠ **On a branch cut before #63 the LOCAL hook is the OLD
implementation**, so `--staged-hash` gives the pre-#63 number until the rebase lands: compute AFTER.

⚠ **DEFERRED ON PURPOSE by #57 — do not "fix":** `world_championship` keeps its name (branched on at
`int_team_momentum_window.sql:135` behind a `coalesce`, so renaming without the SQL edit silently
gives the World Cup a last-5 window, every test green) · `display_group` not deleted (its only
consumer is the block **#44** rewrites) · `confederations.csv` is read by nothing until **#62**.

**#54 the competitions page is DESIGNED AND CLOSED** — its five notes supersede the description, in
order. **#62 outranks it**: every page block comes from ONE mart. Mocks live OUTSIDE the repo in
`design-mocks/`; `gen_competitions.py`'s `check_registry_still_unedited()` **fires by design now
that #57 merged** — drop `continental_club` from `RENAMED_TYPES` and `CWC` from `RETYPED` first.

## ⭐ AN AUDIT FINDS; IT DOES NOT DECIDE

The 59-finding audit and its cold re-run are in **GitLab #30**. Durable lesson: **findings replicate,
prioritisation does not** — the cold run's first recommendation was deletion where the first run's
was addition. **An audit's output is LEADS TO VERIFY, never a work list**; 2 of 4 deletion targets
failed checking. Remaining work is ON THE TRACKER, not here — BUILD **#20** plus a
contract-claims-vs-tree check (unfiled); the rest are the CPO's and #30 lists them.
**Why mechanism beats wording (#30):** of 50 corrections, **33 are prose only, 22 recurred, and
every rule that got a mechanism stopped recurring.** Unmechanised: VERIFY, ESCALATE.

**⚠ OPERATIONAL NOTES LIVE IN `CLAUDE.md`** — dbt CLI, SQLFluff, commit mechanics, the stash-dance,
CWD/fnmatch/heredoc/grep traps. **Do not copy back**: that file is not capped._

**FIRST ACTIONS: `git stash list` before any git work.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX. The one
that must not be rebuilt contains **`feat/player-overview-tab: Overview BUILT`**._

## ⭐ The ingest cluster is CLOSED but UNVERIFIED

Four fixes merged and live; **NO `data:nightly` RUN HAS EXERCISED ANY OF THEM** — it has **no
SCHEDULE** (manual dispatch only). ⚠ `data:build:main` DID run on 08-13, so prod is fresh; that is a
different job and does not exercise ingest pacing. Verify with `glab ci trace <id>`, grepping
`data:nightly` for `rateLimit: Too many requests`. Expect **zero** drops and ~**98 min** rather than
63; if materially off, the 1.55x pacing estimate was wrong — say so with the log output.

⚠ **None of the four does what its title suggests** — the per-issue caveats are on #896-#898; read
them before claiming coverage. **Facts that each corrected a wrong assumption:** Ultra plan
**450/min, 75,000/day**, daily draw ~8,300, so the PER-MINUTE limit binds, never the daily ·
transfers healing is OBSERVED (append-only). **No public site, so no user impact** — never present
this as a live incident.

## ⭐ COST — read **GitLab issue #3** before touching anything

#547's comment is unreachable (GitHub). Everything recoverable is in **GitLab #3** — baselines, the
ranked list **in ITS order**, the free tools, MEASURED vs UNMEASURED. Read it; do not redo it. Traps:

- **⚠ NEVER set a time-based partition expiry on raw** (#892). Nine biennial/quadrennial tournaments
  are `ingest_active` and go months without a refresh; expiry would delete the ONLY surviving row and
  staging's `qualify` would silently return zero rows for that league. Use
  keep-latest-per-`(table, league_code)`. **A fixed lookback window has the same defect.**
- **⚠ Do NOT claim the API quota "breaks first"** — claimed once without evidence, withdrawn. The
  number is not in the repo and #547 assessed the API budget as fine. (`standings.py:30` and
  `teams.py:28` DO loop every configured season daily with no skip — real, worth fixing.)
- **⭐ Two FREE tools: `bq query --dry_run`** (exact bytes, nothing runs) and
  **`scripts/report_bq_cost.py`** (read-only INFORMATION_SCHEMA; the 08-06 stop was LIFTED 08-07).
  ⚠ **Paste the output or do not claim it** — three completeness claims in #547 were wrong.
- **MEASURED 08-03: $2.73/day**, prod tests $1.46 vs models $0.75. ⚠ That baseline PREDATES both
  fixes to its top item — staging became a TABLE on 08-13 (#33 item 9) and `/injuries` ingest is
  gone (item 15). **Re-measure before ranking anything; do not quote 08-03 as current.**
- **⚠ #2 IS LIVE; it fired 08-07 and 08-13.** `data:build:main` triggers on `data_paths`, which
  includes `.gitlab-ci.yml` and `scripts/check_*.py`, so a governance-only MR rebuilds the whole prod
  warehouse — costly by default, though on 08-13 it is what un-staled prod. **Check `data_paths`
  before putting those files in an MR.**

## ⭐ REVIEW MECHANICS — what the working agreement does not give you

Rules are `docs/working_agreement.md` §2 (#878). Only the traps live here.

- **Build the patch with the hook, never by hand:**
  `python .claude/hooks/git_discipline.py --review-patch > .claude/task/review_input.patch`
  ⚠ It is `git diff --staged <base>`, so **`git add` FIRST or it comes out EMPTY**. Reviewers do
  not see task notes; `contract.md` + `escalations.log` ARE delivered, because they carry authority.
  `site_v2/src/data/**` is a MANIFEST — grep those directly. A trailer names any excluded file that
  IS edited (#25/!19), so absence is not evidence a file was untouched.
- **Run `check_task_artifacts.py` BARE** (#24, !15) — it resolves the live remote, as does the hook
  since **#63**; `GOVERNANCE_BASE` overrides both. `--staged-hash` is `git diff --raw` from the base
  and matches CI at any branch length. ⚠ On an UNCOMMITTED branch it prints "empty diff — OK", which
  is vacuous, not green.
- **A PASS may find nothing.** One `risks_checked:` entry is enough; never invent one. Cap is 3
  rounds, then STOP and bring findings to the CPO.
- **`.claude/task/**` is scope-exempt; `active_work.md` is NOT** — it must be in `scope_paths`.
  A commit touching `contract.md` is **never** artifact-exempt.
- **The org does NOT change** (CPO ruling): low activation is not a defect; do not cut reviewers.
- **⭐ A correction REPLACES, never accumulates.** No "an earlier version said X", no round tallies.
  ⚠ And it must replace in the PERMANENT artifacts too, not only the contract — !20 fixed a false
  premise in `contract.md` while leaving it verbatim in the CI comment and the config header.

## Player page + the next CPO decision
**#846 + #886 merged:** the season a page opens on is a warehouse fact (`is_featured_season`, with a
DQ guard). **CPO: the pipeline picks, not the page**, scoped by the tab's LENS (club tabs = most
recent CLUB season).

**#845 + #882 are ONE decision and his** — which entities earn a page, and whether a past season
gets a URL or a control. Deciding apart sets the URL shape twice. Measured (×3 locales): players
51,589→154,767; **matches are BIGGER at 176,235**; h2h 51,903; teams 9,669. A 5-match per-season
gate leaves 1,274 teams and 21,979 players. Bring counts, not a general question.

**The player Overview is BUILT but UNCOMMITTED** in the stash named above, with a known-wrong default
(`seasons[0]` = most recent of ANY competition, so both samples open on WC 2026). Its mart half IS
shipped, so it is a one-line change when it resumes. Held on #845. **#848: the page is FOUR tabs**,
International a national-lens TAB not a toggle (a crawler cannot follow a control) — read #848
first, four CPO-class consequences are open.

## DESIGN DISCIPLINE (the weak spot)
Never design off the cuff. Approved wireframes + role briefs; never invent a block to fill a slot,
never design the canonical page around an edge case, build ONE tab at a time. **Rendered output not
prose; copy is ALWAYS his (§10)** — gather copy decisions BEFORE the branch.

## OWED — deferred, not forgotten
- **Guard telemetry is absent** — 2,684 lines of enforcement, zero records of a gate firing (#30
  finding 4) — and **the round cap only RECORDS** a builder-typed number, so nothing stops a fourth
  round. Both unfixed. Also: delete `macros/apif_latest_source_partition.sql` (zero callers) · a
  metric-change skill · mirror the crests · reviewers as peers (#822 shipped only the model half).
- **⭐ #904 IS THE DOMINANT FAILURE — 6× on 08-07, repeatedly since** — a claim about the code
  asserted rather than run, usually a grep scoped narrower than the sentence it supported ("this
  repo has NO linter"; `--include` omitting `.json`). ⚠ **Its other face is a TEST that passes either
  way**: in #63, THREE tests written to catch a defect passed against that very defect. **A claim of
  ABSENCE must state where it looked; a test must be seen RED before it is trusted GREEN.** Prose has
  failed 7× — the strongest candidate for the next mechanism.

## NEXT
0. **⚠ NO NIGHTLY SCHEDULE exists**, so data refreshes only when a merge matches `.data_paths_prod`
   — exactly how prod went stale for four days. Creating one is a recurring-COST decision, so the
   **CPO's**; bring a recipe, not a question. ⚠ **#4**: a web dispatch from ANY branch builds prod
   from THAT branch's code.
1. **`!27` merges (the CPO's), then #62** — project `country`/`confederation`/`slug`/`sort_order`
   into `competition_registry.csv` via `sync_dbt_vars.py` (⚠ extend `check_registry_var_sync.py`
   with them or the guard stops covering most of the file), build `mart_competition_index`, then
   repoint the export. ⚠ **A seed COLUMN and its first reader cannot ship in one MR** — the deferred
   DQ step resolves `ref()` to MAIN's seed; #57 shipped columns only for this reason, and it is why
   **#38** waits on !27. Then **#55** (display name; needs an EXTERNAL source of record).
2. **The audit stream — see the ⭐ block above.** ⚠ **Do NOT mix it with cost**; conflating them was
   corrected explicitly. Also the CPO's, one command each: **Q2 of #21** (set `main`'s push access to
   No one — the SERVER should protect it, not a client hook; a branch cut from `gitlab/main` INHERITS
   that upstream, so always push an explicit refspec) · delete the 2 dead `~/.claude/hooks/` copies ·
   route or delete `seo-expert-reviewer`.
3. **⭐ THEN COST, SYSTEMATICALLY.** The CPO's words: the whole pipeline **including CI/CD, what gets
   triggered, when, and where**. Trigger/cost map FIRST, rank by real spend, fix in that order; the
   map goes in a GitLab ISSUE, never a doc. `data_paths` (#2) ranks ~4th.
4. **#845 + #882 — the CPO's decision.** Counts are measured and in this file: bring them, not a
   general question. Unblocks the player page off the stash.
5. First GitLab nightly · **then legal/imprint**, then launch.
6. Follow-ups — GITHUB numbers, **bodies UNREACHABLE**; re-derive from code, re-file as picked up.
   **#875** metric GROUP headings English on DE/FI · **#877** `GD`, `W/D/L`, `T·I·B` need DE/FI ·
   **#876** rows break mid-word · **#863** PROTECTED path editable with no `protected_override` ·
   **#866** `Regular Season - 20` is provider text the copy gate cannot see · **#873** routing
   matcher hand-copied, no parity test · **#887** MR-time DQ cannot see its own models · **#883**
   blank `competition_type` skipped by all 3 guards.
7. Mine to build: **#64** #63's residuals · **#67** the contract gate enforces on the Edit tool only,
   so `sed -i` bypasses it · **#68** the form-window CODE diverges from `metrics_context_model.md`
   §4 in 2 places (⚠ **the agreement is the authority** — never fix it by editing the doc to match
   the code) · **#60** the canonical clone is parked on a feature branch, so `.venv` is not where
   `CLAUDE.md` implies.

## OPEN — the CPO's alone
**Imprint operator + address** (#799), blocks publication, never conclude it · hosting recurring
run · the feedback Apps Script (#687) · **#850**'s alias decision · **#875** where a group name
lives · **#895 slim-vs-drop, blocking the biggest remaining cost item** · **#21** (see NEXT 1).

## DO NOT (standing)
- Do NOT treat the tracker as agreed work; re-validate first.
- Do NOT write another planning doc. Do NOT touch `site/` (retired/frozen).
- Do NOT derive facts in the export or frontend — select/group/rename only.
- **Never merge a PR. The CPO merges. Branch from main; never commit to main.**
- Plain language, lead with the decision, **no em dashes**, no walls of text.
- Do NOT ask him to adjudicate what a rule can settle. **But copy is ALWAYS his (§10).**
- Do NOT bring him a fix for a defect he did not ask about; fix it and move on.

## Verified state reference
- **No PUBLIC site.** v2 is unlisted, every page `noindex` — which is why URLs are free.
- **v2 built:** design system + 26 components, fixture page, team page (3 tabs), nav shell,
  page-spec + SEO contract (#826/#844), per-locale metric labels.
- **Tests: 764 passed + 1 skipped python** (~5 min, measured 08-12 on `!33`), plus 59 site
  (`cd site_v2 && npm test`). ⚠ MEASURE, never predict (#904) — this was 665 two weeks ago.
- **`ruff` runs in CI** as `lint:python` (!20), config **`.ruff-ci.toml`** — the filename is
  load-bearing; `tests/test_lint_config.py` pins it.
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). Reselling
  API-Football data is the one hard prohibition.
