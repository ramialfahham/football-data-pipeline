# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`; `wc -c` counts BYTES and
> over-reports by ~220 here, which will send you trimming content that fits.

_Last updated **2026-08-12**. **TWO MRs OPEN: `!27`** (home page, done, waiting on the CPO) and
**`!33`** (#57 taxonomy seed). **`!35`/#63 MERGED.** The product is **Matchday Pilot**; the repo is
on **GITLAB** (`glab`, MRs, `.gitlab-ci.yml`). GitHub is KEPT but dormant — its Actions run nothing
and its 114 issues are unreachable; `.github/workflows/README.md` says what re-arms it.
⚠ **CI WORKS AGAIN** — a self-hosted runner (`ci-runner-01`) serves this project, so jobs burn ZERO
GitLab minutes; the old "no minutes" note is dead. ⚠ **A GROUP MOVE IS COMING** and it changes the
project PATH — breaking remote URLs, the WIF binding pinned to `attribute.project_path`, and every
hardcoded `rami.al-fahham/football-data-pipeline`. Check before starting anything path-dependent._

## ⭐ CURRENT — #57 COMMITTED, `!33` OPEN (2026-08-12)

`feat/57-competition-taxonomy-seed` → **!33**, rebased onto the main that carries #63. Config +
docs only; no SQL, no shipped number moves. 3 rounds, 4 reviewers, all PASS. **The eleven CPO
rulings are verbatim in `.claude/task/escalations.log` — that entry is the authority, not this
summary.**

⚠ **DEFERRED ON PURPOSE — do not "fix":** `world_championship` keeps its name (branched on at
`int_team_momentum_window.sql:135` behind a `coalesce`, so renaming without the SQL edit silently
gives the World Cup a last-5 window with every test green) · `display_group` not deleted (its only
consumer is the block **#44** rewrites) · `confederations.csv` is read by nothing until **#62**.

**#54 the competitions page is DESIGNED AND CLOSED** — five notes supersede its description, in
order. **#62 outranks it**: every page block comes from ONE mart. Mocks live OUTSIDE the repo in
`design-mocks/`; `gen_competitions.py`'s `check_registry_still_unedited()` **now fires by design** —
drop `continental_club` from `RENAMED_TYPES` and `CWC` from `RETYPED` before re-rendering.

## ⭐ AN AUDIT FINDS; IT DOES NOT DECIDE

The 59-finding audit and its cold re-run are in **GitLab #30**. Durable lesson: **findings
replicate, prioritisation does not** — the cold run's first recommendation was deletion where the
first run's was addition. **An audit's output is LEADS TO VERIFY, never a work list.** Two of four
deletion targets did not survive checking; treating the 29 as a plan cost an afternoon.

Remaining: BUILD **#20** + a contract-claims-vs-tree check (unfiled). The rest are the CPO's: **#15,
#16, #21, #27, #5, #14, #18, #26, #28**. **#26**: a keyword matcher was tried and WITHDRAWN — a
false hit fires on a real RULE. **#28**: cause is SEQUENCING; log entry and override as ONE action.

**Why mechanism beats wording, measured in #30:** of 50 recorded corrections, **33 are prose only,
22 recurred, and every rule that got a mechanism stopped recurring.** Still unmechanised:
VERIFICATION and ESCALATION.

**⚠ OPERATIONAL NOTES LIVE IN `CLAUDE.md`** — dbt CLI, SQLFluff, commit mechanics, the stash-dance,
CWD/fnmatch/heredoc/grep traps. **Do not copy them back**: that file is not capped._

**FIRST ACTIONS: `git stash list` before any git work.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX —
indices move on every stash. The one that must not be rebuilt contains
**`feat/player-overview-tab: Overview BUILT`**._

## ⭐ The ingest cluster is CLOSED but UNVERIFIED

Four fixes merged and live; **NO PRODUCTION RUN HAS EXERCISED ANY OF THEM** — `data:nightly` has
**no SCHEDULE**, so it is reachable only by manual web dispatch. A live gap.

Verify: `glab ci list`, then `glab ci trace <id>` grepping `data:nightly` for `rateLimit: Too many
requests`. Expect **zero** drops and ~**98 min** rather than 63. If materially off, the 1.55x
pacing estimate was wrong — say so with the log output.

**What each does NOT do:** #897 cuts the failure RATE only · #896 stops the LOSS but does not make
failure visible · #898 hard-fails on STAGNATION, not completeness · cause 3 gates
players/squads/transfers but **COACHES reports only**.

**Standing facts that each corrected a wrong assumption:** Ultra plan **450/min, 75,000/day**,
daily draw ~8,300, so the PER-MINUTE limit binds, never the daily · transfers healing is OBSERVED
(append-only). **No public site, so no user impact** — never present this as a live incident.

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
- **⭐ Two FREE tools: `bq query --dry_run`** (exact bytes, nothing runs) and
  **`scripts/report_bq_cost.py`** (read-only INFORMATION_SCHEMA). The 2026-08-06 stop on the latter
  was **LIFTED 2026-08-07** (`escalations.log`). ⚠ **Paste the output or do not claim it** — three
  completeness claims in #547 were wrong.
- **The ranked list is in GitLab #3, in ITS order.** MEASURED 08-03: **$2.73/day**, prod tests
  $1.46 vs models $0.75; the top single cost is a `not_null` test on a STAGING VIEW rescanning
  6.99 GiB ($0.30/day) — staging is still a view, the same defect fixed for base on 2026-08-02.
- **⚠ #2 IS LIVE AND IT FIRED ON 2026-08-07.** `data:build:main` triggers on `data_paths`
  (`.gitlab-ci.yml:230`), which includes `.gitlab-ci.yml` and `scripts/check_*.py` — so !15, a
  governance/docs MR that changed a COMMENT and a gate script, rebuilt the whole prod warehouse.
  **Check `data_paths` before putting those files in an MR.**

## ⭐ REVIEW MECHANICS — what you cannot derive from the working agreement

Rules are `docs/working_agreement.md` §2 (#878). Only the traps live here.

- **Build the patch with the hook, never by hand:**
  `python .claude/hooks/git_discipline.py --review-patch > .claude/task/review_input.patch`
  ⚠ It is `git diff --staged <base>`, so **`git add` FIRST or it comes out EMPTY**. Reviewers do
  not see task notes; `contract.md` + `escalations.log` ARE delivered, because they carry
  authority. `site_v2/src/data/**` is a MANIFEST — grep those files directly. A trailer names any
  excluded file that IS edited (#25/!19), so absence is not evidence a file was untouched.
- **Run `check_task_artifacts.py` BARE** (#24, !15) — it resolves the live remote, and so does the
  hook since **#63**; `GOVERNANCE_BASE` overrides both. ⚠ The old "on a multi-commit branch
  `--staged-hash` is the WRONG number, collapse with `git reset --soft`" warning is **false since
  #63** and deleted: the hash is `git diff --raw` from the base and matches CI at any length.
- **A PASS may find nothing.** One `risks_checked:` entry is enough; never invent one. Cap is 3
  rounds, then STOP and bring open findings to the CPO.
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
**#846 + #886 merged:** the season a page opens on is a warehouse fact (`is_featured_season`, with a
DQ guard). **CPO: the pipeline picks, not the page**, scoped by the tab's LENS (club tabs = most
recent CLUB season).

**#845 + #882 are ONE decision and his** — which entities earn a page, and whether a past season
gets a URL or a control. Deciding apart sets the URL shape twice. Measured (×3 locales): players
51,589→154,767; **matches are BIGGER at 176,235**; h2h 51,903; teams 9,669. A 5-match per-season
gate leaves 1,274 teams and 21,979 players. Bring counts, not a general question.

**The player Overview is BUILT but UNCOMMITTED** in the stash named above, with a known-wrong
default (`seasons[0]` = most recent of ANY competition, so both samples open on WC 2026). Its mart
half IS shipped, so it is a one-line change when it resumes. Held on #845.
**#848: the player page is FOUR tabs**, International being a national-lens TAB not a toggle (a
crawler cannot follow a control). Read #848 first — four CPO-class consequences are open.

## DESIGN DISCIPLINE (the weak spot)
Never design off the cuff. Use approved wireframes and role briefs. Never invent a block to fill a
slot, never design the canonical page around an edge case, build ONE tab at a time. **Show rendered
output, not prose; copy is ALWAYS his (§10)** — gather copy decisions UP FRONT, before the branch.

## OWED — deferred, not forgotten
- **Guard telemetry is absent** — 2,684 lines of enforcement, zero records of a gate firing (#30
  finding 4) — and **the round cap only RECORDS** a builder-typed number, so nothing stops a
  fourth round while rounds run. Both unfixed.
- Delete `macros/apif_latest_source_partition.sql` — zero callers, never pruned. A metric-change
  skill · mirror the crests · reviewers as peers (#822 shipped only the model half).
- **⭐ #904 IS THE DOMINANT FAILURE — six times on 08-07, and repeatedly on 08-12** — a claim about
  the code asserted rather than run. Usually a grep scoped narrower than the sentence it supported
  ("this repo has NO linter"; `--include` filters omitting `.json`, so a `done_when` claimed a
  clean tree while a committed sample still held the old value). ⚠ **Its other face is a TEST that
  passes either way**: in #63, THREE tests written to catch a defect passed against that very
  defect, each found only by running them against a reverted copy. **A claim of ABSENCE must state
  where it looked; a test must be seen RED before it is trusted GREEN.** Prose has failed seven
  times — the strongest candidate for the next mechanism.
- **#900: blueprint §4 says a full daily run is 20-50 API calls; measured ~8,300.**

## NEXT
0. **⚠ NO NIGHTLY SCHEDULE ON GITLAB** (detail in `CLAUDE.md`) — the data goes stale silently.
   Creating one is a COST decision, so the CPO's; bring a recipe, not a question. ⚠ **#4**: a web
   dispatch from ANY branch builds prod from THAT branch's code.
1. **`!33` merges (the CPO's), then #62** — project `country`/`confederation`/`slug`/`sort_order`
   into `competition_registry.csv` via `sync_dbt_vars.py` (⚠ extend `check_registry_var_sync.py`
   with them or the guard stops covering most of the file), then build `mart_competition_index`,
   then repoint the export. ⚠ **A seed COLUMN and its first reader cannot ship in one MR** — the
   deferred DQ step resolves `ref()` to MAIN's seed. That is why #57 shipped columns only.
   Then **#55** (display name; needs an EXTERNAL source of record, like #850's 14 team names).
2. **The audit stream — see the ⭐ block above.** ⚠ **Do NOT mix it with cost**; conflating them was
   corrected explicitly. Also the CPO's, one command each: **Q2 of #21** (set `main`'s push access
   to No one — the SERVER should protect it, not a client hook; a branch cut from `gitlab/main`
   INHERITS that upstream, so the auto-push aimed at `main` twice on 08-12; always push with an
   explicit refspec) · delete the two dead `~/.claude/hooks/` copies · route or delete
   `seo-expert-reviewer`.
3. **⭐ THEN COST, SYSTEMATICALLY.** The CPO's words: the whole pipeline **including CI/CD, what
   gets triggered, when, and where**. Trigger/cost map FIRST, rank by real spend, fix in that
   order; the map goes in a GitLab ISSUE, never a document. `data_paths` (#2) ranks ~4th.
4. **#845 + #882 — the CPO's decision.** Counts are measured and in this file: bring them, not a
   general question. Unblocks the player page off the Overview stash.
5. Read the first GitLab nightly · home page (`1c35e7aa` = reference only), **then legal/imprint**,
   then launch.
6. Follow-ups — GITHUB numbers, **bodies UNREACHABLE**; re-derive from code, re-file as picked up.
   **#875** metric GROUP headings English on DE/FI · **#877** `GD`, `W/D/L`, `T·I·B` need DE/FI ·
   **#876** rows break mid-word · **#863** PROTECTED path editable with no `protected_override` ·
   **#866** `Regular Season - 20` is provider text, invisible to the copy gate · **#873** routing
   matcher hand-copied, no parity test · **#887** MR-time DQ cannot see its own models · **#883**
   blank `competition_type` skipped by all three guards.
7. **UNFILED, found 08-12:** the contract gate refusing a rewrite on a dirty tree enforces on the
   **Edit tool only** — a `sed -i` against `contract.md` went through unchallenged, the same class
   it already blocks for heredocs. Also two places where the CODE does not follow
   `metrics_context_model.md` §4: `domestic_league` BEFORE the season (rule says previous season,
   model returns no rows, defers to a `#326` fallback nobody verified) and `qualifying` WHILE
   running (rule says whole campaign, model does `last_5`, "deferred #483"). ⚠ **The agreement is
   the authority; the code is what is wrong.** #63's residuals are filed as **#64**.

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
- **No PUBLIC site.** v2 is unlisted, every page `noindex` — which is why URLs are still free.
- **v2 built:** design system + 26 components, fixture page, team page (3 tabs), nav shell,
  page-spec + SEO contract (#826/#844), metric labels per locale.
- **Tests: 764 passed + 1 skipped python** (~5 min, measured 2026-08-12 on `!33`), plus 59 site
  (`cd site_v2 && npm test`). ⚠ MEASURE, never predict (#904) — this count was 665 two weeks ago.
- **`ruff` runs in CI** as `lint:python` (!20), config **`.ruff-ci.toml`** — the filename is
  load-bearing; `tests/test_lint_config.py` pins it.
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). Reselling
  API-Football data is the one hard prohibition.
