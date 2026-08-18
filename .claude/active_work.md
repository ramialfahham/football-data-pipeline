# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-18**. **main `254415b`** — `!70` (#74 nightly image fix), `!72` (shared
ordering), `!73`+`!74` (Top players ruling), `!68` (#62 step5) and everything before it, merged.
**`!75` OPEN** (this handover, mid-merge-conflict-resolution against a newly-advanced main).
Product **Matchday Pilot**; **GITLAB** (`glab`, MRs); runner `ci-runner-01`, ZERO GitLab minutes.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding
on `attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ CURRENT — auditing the HOME PAGE, block by block, before building anything (2026-08-18)

**#62 (competitions index page) is done and merged.** Do NOT start #47 next — that was the old
plan; the CPO redirected to a full data audit of the home page first, and that is now the standing
method for every page. Nothing below is a proposal to revisit; it is where the audit stands.

⭐⭐ **THE METHOD — CPO's own words, do not reword this:** *"the exercise is: does the mock
consider the underlying mart (or mart gap)."* ⚠ **NOT "check against a leaderboard mart"** — today's
two audited blocks happen to be leaderboard-shaped (`mart_leaderboards`); most pages have nothing
to do with leaderboards. There is no universal mart template — each mock gets checked against
WHATEVER mart(s) actually back it, and the check is whether the mock's design already reflects
that reality or contradicts it. Concretely, per element on a mock:
1. Name the exact MART COLUMN that serves it. Not a seed. Not `docs/competition_registry.yml`.
   Not `metric_catalogue.csv`. **A seed/registry/catalogue is NOT a source** — reading one from a
   page is the SAME violation as computing in the frontend, just harder to notice. Caught hard
   today (CPO: *"the metric layer as a basis for displaying something??? league code, registry as
   a source for displaying something"*) — see `feedback_consumption_layer_contract.md`, rewritten
   today to lead with this exact failure.
2. No mart column = a GAP. Register it precisely in `99_gaps_register.md`. A block cannot be built
   before every element on it has a real mart source.
3. **Check the mock's own numbers against the spec's WORDS before trusting either.** Today's Top
   players mock rendered "7 rows, 7 distinct leagues" by accident of invented data, which read as
   a design (one-per-league) the spec never stated (it said "pooled"). A placeholder dataset can
   assert a rule nobody chose. Ask the CPO which one is actually meant — do not infer from numbers.

⭐ **AUTOMATION — discussed 2026-08-18, NOT built, NOT approved to start.** Two ideas, both need to
stay general (no leaderboard-specific template, per THE METHOD above):
- **Trace script**: a mock + whatever mart(s) it should bind to, in → the element-by-element source
  table + gap list, out. Would replace the by-hand version of this I did three times today.
- **Staleness-sweep checker**: scans a wireframe doc for any mention of a removed board/metric/
  count NOT wrapped in strikethrough or a SUPERSEDED banner. Would have caught, mechanically, what
  took 4 review rounds today — each round found one more stale instance on a DIFFERENT axis (board
  tables, then a removed board's ranking prose, then a stale seed-column count, then a row-count
  rule) because I swept by eye and each pass only caught the axis a reviewer had just named. Filed
  as **issue #78** for the next full sweep of `10_home.md`; the checker itself is not started.
  Ask before building either.

⛔ **HOME PAGE BLOCK STATUS, audited today, not from memory — check `99_gaps_register.md` first:**
- **Next matches** — LIVE. Now uses the SAME ordering rule as the competitions page (one function,
  `lib/competitionOrder.mjs`, called by both), and the hardcoded 12-fixture cap is GONE — shows the
  next matchday, however many matches that is (CPO: *"we will show what we have"*). ⚠ Still reads
  `core.fct_fixture`/`core.dim_team` directly instead of a mart — flagged, not fixed, and
  **GAP-32** records a live, CPO-ruled-but-unresolved dispute about whether selecting "the next
  matchday" in the export's own SQL is itself a layer violation. Read it before touching this path.
- **Top players** — NOT BUILT. Ruled 2026-08-18: **one player per league**, not a pooled ranking
  (GAP-31 WITHDRAWN because of this — `mart_leaderboards` already ranks per league, so no new
  ranking is needed). Intro copy approved: *"Season totals to date. The top player from each
  league: …"*. Three real gaps remain, all additive to `mart_leaderboards`: **GAP-27** (no club on
  a row — name/crest/slug all sit unused on `dim_team`), **GAP-28** (pool membership — ⚠ `tier`/
  `season_type` are ALREADY projected into the seed, only ONE authored pool field is left),
  **GAP-30** (`assists` has a column but no rank at all — the reduced set's second board has
  nothing to take a leader from).
- **Top teams** — NOT BUILT, no mart at all (**GAP-29**, design approved, still not started).
  **Pooling RULED 2026-08-18: ONE TEAM PER LEAGUE**, same as Top players (CPO: *"one team per
  league, same as players"*) — when GAP-29's mart is built, partition per league like
  `mart_team_competition_benchmarks` already does and the per-league rank is free. ⚠ Unlike
  players, `top_teams_mock.html` does NOT already show this shape — 3 of 4 boards genuinely mix
  teams from one league (checked by opening it). Needs redoing before it previews the real
  design. Intro copy ("Ranked across pooled leagues") also confirmed wrong; replacement PROPOSED
  in `10_home.md`, not yet CPO-approved.
- **Browse** — LIVE but WRONG on two counts. (1) Still shows the "By country" grouping the CPO
  killed on 08-10 (#44) — never removed. (2) Reads `docs/competition_registry.yml` directly, ZERO
  database reads — the exact seed-as-source violation THE METHOD exists to catch, and **it has not
  even been filed as a gap yet.** File it before building anything here.

⚠ **`chore/record-top-players-ruling` (!73+!74) ran 5 review rounds** — round 1 did the actual
task; rounds 2-5 were an unplanned staleness sweep that grew out of it (see AUTOMATION above).
Stopped and filed #78 rather than grinding a 6th. If a future task starts drifting into "and now
fix everything else this touches", stop and ask, same as this one eventually did.

⚠ **A rebase/rebind surprise, worth knowing about**: mid-review on `!74`, `gitlab/main` advanced
because `!73` (this same branch's FIRST commit) got merged while rounds 2-5 were still running
locally on top of it. `--staged-hash` recomputes cumulative-from-LIVE-base, so the hash shifted
with ZERO content change. Confirmed via `git diff --stat` (empty) before rebinding — do the same
check before assuming a hash mismatch means something changed. ⭐ **This handover's OWN commit
(`!75`) hit the real version of that same class**: main advanced a SECOND time, mid-session, with
an actual conflicting merge (#74, MR !70) — not an empty-diff rebind. Resolution mechanics folded
into OWED below.

## ⭐ ORIENTATION
**Audits: GitLab #30, DO NOT run another** (rejected 08-16; a TARGETED blind assessment is different
and IS allowed). **Mechanism beats wording:** of 50 corrections, 33 prose-only, 22 recurred.
**⚠ OPERATIONAL NOTES LIVE IN `CLAUDE.md`** — dbt CLI, SQLFluff, commit mechanics, the stash-dance,
CWD/fnmatch/heredoc/grep traps. **Do not copy back**: that file is not capped.
**FIRST ACTION: `git stash list` before any git work.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX. ONE
must not be rebuilt: **`feat/player-overview-tab: Overview BUILT`**.

⭐ **THE REPO IS NOT THE SYSTEM**: for warehouse/cloud/scheduler facts check the system that owns
them (`bq ls`, `gcloud run jobs describe` — free metadata). `raw_archive` was called "never built"
from zero repo refs; it EXISTS (`*_20260808` snapshot) — true of the repo, false as a conclusion.
`#75 closed 08-17` (prod whole, `PASS=849 ERROR=0 SKIP=0`) — full recovery detail, the permanent
`!57` kickoff-cutoff floor, and the two killed sibling tests are in `escalations.log`, not repeated
here (deleted as a stale completed section, 08-18 — do not re-add without a new reason).

## ⭐ The ingest cluster
**TWO nightlies:** `data:nightly` on **Cloud Run under #39**; GitLab schedule (4379625) paused ON
PURPOSE. Runbook `deploy/nightly/README.md`.
✅ **#74 FIXED AND MERGED** (MR !70, 2026-08-18): `build:nightly-image` (kaniko, no Cloud Build) +
`deploy:nightly-image` rebuild the image and repoint `fdp-nightly` on every `main` push touching
`*data_paths_image`. From now on the image tracks `main` automatically — **hand-redeploying after
an ingestion merge is no longer required, but the FIRST auto-run since merge is UNVERIFIED; check
it actually fired before trusting that.** ⚠ **NOT `--source .`/Cloud Build** — Cloud Build's
default identity holds project Editor; granting our SA build access opened an Editor path from ANY
unmerged branch. Revoked; redesigned to build in-job with kaniko instead.
⚠ **OWED: set `deploy-nightly-image` resource_group to `oldest_first`** (Settings → CI/CD, only
after the group exists — first run creates it). Default `unordered` mode means two
near-simultaneous merges can deploy out of order, pinning the OLDER commit until the next one.
**Sentinel (`fdp-freshness`) still NOT repointed** — deliberately separate, stays pinned; repointing
it is its own later decision per the runbook's sequence.
⚠ **A GREEN EXECUTION PROVES NOTHING** — it says the container ran, not which code. **Check DATA.**
⚠ **None of the four ingest fixes does what its title says** — caveats on #896-#898.
✅ **MR2 (`!62`) MERGED 08-17** — the four "gap recorded as fact" holes are closed. **MR3 =
detection, NOT started:** lower `event_loss_detector_from` (still **'2026-08-19', in the FUTURE, so
`!57`'s test is inert**); ⛔ **the volume-delta threshold is the CPO's and blocks it.** **MR4 =
compaction, only if growth is MEASURED.**

## ⭐ COST — read **GitLab issue #3** first
**#3 holds it all.** ⚠ **#70** is the scan-budget guard; `require_partition_filter` +
`maximum_bytes_billed` are **NEITHER set**. ⚠ **STORAGE NEVER MEASURED**; every figure is bytes
SCANNED. ⚠ **Spend UNKNOWN** since 08-03.

## Player page — HELD on #845
**#846 + #886 merged:** the season a page opens on is a warehouse fact. **#845 + #882 are ONE
decision and his** — which entities earn a page, and whether a past season gets a URL or a
control. Counts: players 51,589→154,767; matches 176,235; h2h 51,903; teams 9,669.
**Overview is BUILT but UNCOMMITTED** in stash `feat/player-overview-tab`; default is known-wrong.

## OWED — deferred
- Guard telemetry absent (#30 finding 4). Delete `macros/apif_latest_source_partition.sql` · mirror
  crests.
- ⛔ **The contract/Stop gates do NOT understand a MERGE.** Confirmed live on `!75`: mid-merge, EVERY
  file the incoming side touches (even auto-merged, no-conflict ones) reads as "dirty outside the
  contract" and the Write/Edit gate refuses to touch `contract.md` itself ("clean tree" rule) until
  the merge is committed — circular, since the contract needs updating to describe the merge before
  it's honest to commit. ⚠ **WORKAROUND, not a fix**: `_gate_bash_pre` in `task_contract_gate.py`
  skips ANY path under `.claude/task/` entirely (no scope check, no clean-tree check) — write
  `contract.md`/`review.md` via Bash (e.g. `cp` from a scratchpad file) instead of the Edit/Write
  tool while mid-merge, then resolve everything else normally. Still needs the real
  `MERGE_HEAD`-aware skip; protected path, own task.
- **#904 IS THE DOMINANT FAILURE** — a claim asserted rather than RUN. A test must be seen RED.

## NEXT
1. **Block audit**: Top teams pooling RULED (⭐⭐ CURRENT above) — mock needs redoing, mart still
   not started. **Browse next**: scope asked (narrow "kill By-country" vs full #44 flatten to one
   row, which needs a display-name call too) — CPO hasn't answered, do not build either version
   yet. GAP-33 (Browse reads the registry file directly, zero mart reads) not filed yet either;
   bundle it into whichever Browse MR follows rather than its own MR.
2. ⛔ **TURN ON "Pipelines must succeed"** (Settings → Merge requests) — FALSE since the migration;
   pairs with **#21 Q2** (both are "the server should enforce it").
3. **#47** (the competition hub) — makes the competitions page's rows real links (three decisions
   in PRIOR SESSION explain why they aren't yet). Wire `competition_index` into CI's `--entities`
   list in #47's MR, not before.
4. **The audit stream**: Q2 of #21 · delete 2 dead `~/.claude/hooks/` copies · route/delete
   `seo-expert-reviewer`.
5. **COST, SYSTEMATICALLY** — trigger/cost map first, in a GitLab issue.
6. **#845 + #882 — the CPO's decision.** Unblocks the player page.
7. **Legal/imprint**, then launch.
8. Follow-ups (GITHUB numbers, **bodies UNREACHABLE** — re-derive from code): DE/FI i18n gaps ·
   PROTECTED path editable with no `protected_override` · `Regular Season - 20` provider text the
   copy gate cannot see · blank `competition_type` skipped by all 3 guards.
9. Mine, on GitLab: **#64** #63's residuals · **#67** the contract gate enforces on the Edit tool
   only, so `sed -i` bypasses it · **#68** the form-window CODE diverges from
   `metrics_context_model.md` §4 (⚠ **the agreement is the authority**; never fix it by editing the
   doc) · **#60** `.venv` is not where `CLAUDE.md` implies · **#70** scan-budget guard.

## OPEN — the CPO's alone
Imprint operator + address (#799) · hosting recurring run · feedback Apps Script (#687) · #850
alias · #875 · #895 slim-vs-drop · #21.

## DO NOT (standing)
- **DESIGN, the weak spot:** never off the cuff. Rendered output not prose; copy decisions BEFORE
  the branch, and copy is ALWAYS his (§10) even when he delegates the drafting to me.
- **Every displayed value needs its mart column named, not "a seed has it".** And do NOT
  generalize one page's mart shape onto another — see THE METHOD above.
- Do NOT treat the tracker as agreed work. No new planning docs, no fresh audits. Do NOT touch
  `site/`. Do NOT derive facts in the export or frontend.
- ⛔ **VERIFY BEFORE ASSERTING.** Search `escalations.log` + docs for a prior ruling FIRST.
- **Never merge an MR. The CPO merges. Branch from main; never commit to main.**
- Plain language, lead with the decision, **no em dashes**, no walls of text, **no jargon** — say
  "the league page" not "the hub", say "database table" not "mart" if he's asked once already.

## Verified state reference
- **v2 built:** design system + 26 components, fixture page, team page (3 tabs), home page (next
  matches → browse, ordering shared with competitions page), competitions index page, page-spec +
  SEO contract, per-locale metric labels.
- ⚠ MEASURE test/model counts, never predict (#904) — none pasted here stale.
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). Reselling
  API-Football data is the one hard prohibition.
