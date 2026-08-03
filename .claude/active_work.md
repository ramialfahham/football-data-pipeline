# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — `wc -c` counts BYTES and this file is full of multi-byte
> symbols, so it over-reports by ~220 and will send you trimming content that fits.

_Last updated **2026-08-03**. main GREEN at **bb61a51**. **NOTHING IN FLIGHT — no open PRs.**
Merged this session: #846, #886, #547-PR1, #890. The product is **Matchday Pilot**.
**FIRST ACTIONS: run `git stash list` before any git work** (`stash@{0}` is the player Overview, built,
uncommitted, do NOT rebuild) — then read the two ⭐ blocks below, in order._

## ⭐ START HERE — the ingest silently drops data and reports success (#896, #897, #898)

Found 2026-08-03 by reading a nightly log. **10 of the last 18 nightly runs dropped API calls. Every
one reported `success`.** Onset 2026-07-16, caused by volume growth, not a code change.

**Fix in this order. All three are open and none is started.**

1. **#897 — production runs UNPACED.** `settings.py:146` defaults `API_FOOTBALL_REQUEST_PAUSE_MS=0`
   under the `full` profile, and `dbt-scheduled.yml` sets no profile, so it inherits zero.
   `docs/api_football_ingestion_blueprint.md` §4 mandates 0.25s and names the **per-minute burst** as
   the binding constraint. Production violates a requirement we wrote. Cheapest fix, do it first.
2. **#896 — an empty response DELETES the previously good rows.** `loads/squads.py:35-66`
   `_delete_superseded_player_rows` writes the empty row then deletes the prior one for the same key.
   Verified by time travel on 08-02: UCL 340 `25→0` players, UEL 573 `24→0`, UECL 20034 `23→0`,
   APD 463 `46→40`. `fct_transfer` moves for UEL 376 `389→118` (−70%).
   **⚠ THE TABLES GREW WHILE THIS HAPPENED** (`RAW_APIF_PLAYERS` 721,755→721,938). No row-count,
   freshness or not-null test can see this class. This is the worst of the three.
3. **#898 — the failure is invisible in FOUR places.** The per-minute limit arrives as **HTTP 200
   with the error in the body**, so `http_client.py:31` (retries on 429) never fires and there are
   ZERO retries. `quota.py:28` only matches the *daily* text, so the completeness guard gated on it
   never runs. `completeness.py:35` covers only fanout entities. `orchestrator.py:216` never puts
   `ctx.errors` in the job summary. **Do NOT just fail the run** — that blocks the daily build and
   daily freshness is required. Threshold policy is a CPO decision.

**Verified vs not.** `coaches` never loses data (staging keeps all snapshots). `player_squads` leaves
a staging hole with **zero consumers** (`stg_apif__squads` has one grep hit, its own schema test).
`players` loss VERIFIED, healing verified in code. **`transfers` loss VERIFIED, healing INFERRED and
NOT OBSERVED** — the 08-03 run was still in flight. Confirm with:
`bq query 'select date(ingested_at), count(*) from raw.RAW_APIF_TRANSFERS where league_code="UEL" group by 1 order by 1 desc limit 3'`

**No user impact today: there is no public site.** Do not present this as a live incident.

## ⭐ COST — read #547's 2026-08-03 comment before touching anything

That comment is the durable record: baseline numbers, what landed, what is open and ranked, and the
corrections. Do not redo the analysis. Key traps:

- **⚠ NEVER set a time-based partition expiry on raw** (#892 comment). Nine biennial/quadrennial
  tournaments are `ingest_active` and go months to years without a refresh in poll mode; expiry would
  delete the ONLY surviving row and staging's `qualify` would return zero rows for that league,
  silently. Use keep-latest-per-`(table, league_code)` instead. **A fixed lookback window has the same
  defect** — the #892 fix must compute per-league maxima.
- **⚠ Do NOT claim the API quota "breaks first".** `standings.py:30` and `teams.py:28` do loop every
  configured season daily with no skip, which is real and worth fixing. But the daily quota number is
  not in the repo, and Thread 1 + #547 both assessed the API budget as fine. That claim was made this
  session without evidence and withdrawn.
- **⭐ `bq query --dry_run` is free and exact. Use it to CHOOSE a query shape.** It proved a subquery
  predicate does NOT prune (6.634 GiB, same as no filter) and that the deleted
  `apif_latest_source_partition` macro never pruned either. `python scripts/report_bq_cost.py`
  (shipped in #547 PR1, read-only, free) gives spend by workload, by dbt node, tests vs models.
- ⚠ **Paste the command output or do not claim it.** Three completeness claims in #547 were wrong.

## ⭐ REVIEW MECHANICS — what you cannot derive from the working agreement

Rules are `docs/working_agreement.md` §2 (#878). Only the traps live here.

- **Build the patch with the hook, never by hand:**
  `python .claude/hooks/git_discipline.py --review-patch > .claude/task/review_input.patch`
  Cumulative from base. Reviewers do NOT see task notes; `contract.md` + `escalations.log` ARE
  delivered, because they carry authority.
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
- **No gate records when it fires** — ~2,500 lines of enforcement, zero telemetry. Highest-value
  follow-up in the repo.
- **The copy gate is wired to nothing** (#872) — finds 16 real user-visible defects, blocks none.
  Blocked on those 16 being the CPO's copy.
- Delete or rewrite `macros/apif_latest_source_partition.sql` — zero callers and it never pruned.
- A metric-change skill · mirror the crests · reviewers as peers (#822 shipped only the model half).

## NEXT
1. **#897 → #896 → #898**, in that order.
2. **#845 + #882** — the CPO's decision. Then the player page off `stash@{0}`, one tab at a time.
3. Resume cost per #547's ranked list.
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
#898's threshold policy · #895 slim-vs-drop.

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
- **Commit mechanics:** `git commit` runs alone (no chaining); `--amend` gate-blocked. Use
  `git commit -F <file>` — an apostrophe breaks the form gate. Write messages to the scratchpad. A
  post-commit hook auto-pushes and opens the PR. `review.md` must be COMMITTED.
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
- **Tests:** 258 governance, 59 site (`cd site_v2 && npm test`), 506 python total.
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). API-Football:
  reselling is the one hard prohibition.
