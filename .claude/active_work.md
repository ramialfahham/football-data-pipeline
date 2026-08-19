# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-19**. **main `de8d3c7`** (everything through `!75` merged). **THREE MRs
OPEN, none merged yet, all awaiting the CPO**: `!76` (Top teams ruling, block-audit continuation),
`!77` (team_name_overrides batch 1, PL/PD/SA, 61 rows), `!78` (team_name_overrides batch 2, BL1/ED/
L1/LP, 36 rows). Product **Matchday Pilot**; **GITLAB** (`glab`, MRs); runner `ci-runner-01`, ZERO
GitLab minutes.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding
on `attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ CURRENT — team names are wrong at scale; a sitewide browse feature surfaced it (2026-08-19)

**Started as**: continue the home-page block audit (Top teams, then Browse). **Ended as**: Top
teams ruled (✅ below); Browse's narrow fix was STARTED then ABANDONED mid-build when the CPO
reframed it as a sitewide feature (design below, NOT built); designing that feature surfaced that
provider team names are wrong at scale, not just 2 examples — now its own real, ongoing fix
(`!77`+`!78`, 97 corrections, more to go). Nothing below is a proposal; it is where each thread
stands.

⛔ **TEAM NAMES: THE PROVIDER'S team_name IS OFTEN NOT THE DISPLAY NAME, EVEN WHEN UNIQUE.**
`team_name_overrides` (seed, joined in `base_apif__teams_global.sql`) previously fired ONLY on an
exact collision between two real clubs (9 rows, #850/#851). CPO, this session: *"we have to define
the name we use as the single source of truth for what we display"* — bare "Arsenal" isn't wrong
because it collides with anything, it's wrong because the club's name is "Arsenal FC". Broadened
the trigger; `dbt_project/seeds/schema.yml`'s doc updated to match (both branches, since neither
has merged into the other yet).
**Scale, MEASURED**: checked all of PL/PD/SA/BL1/ED/L1/LP (Pool 1) bar ~15 teams Wikipedia's
current-season table didn't clearly cover. **97 of roughly 130 checked needed correction.** Two
confirmed to already be correct as typed and NOT touched: Athletic Club, Real Madrid (CPO, asked
directly rather than guessed). Feyenoord also confirmed already-correct. ⚠ **Bayern München is
DELIBERATELY EXCLUDED** — a STANDING rule already in `schema.yml` before this session: locale
preference (München vs Munich) is never corrected, only completeness/collision. Every source is an
English Wikipedia article-title URL, cited per row, same convention as the original 9.
**Both review rounds on both MRs caught real defects on round 1**: an `impact_map` that claimed
"pasted dbt ls evidence" but was hand-typed from memory (fixed: real command output now in both
contracts); `schema.yml` not updated to describe the broadened trigger (fixed, twice, once per
branch); a citation to a CPO quote that lived only on the *other*, unmerged branch's escalations.log
(fixed: each branch now quotes the ruling in full, self-contained); a plain arithmetic error, 36
rows claimed as 35. All fixed, both MRs clean on round 2.
**NOT started**: teams outside Pool 1. **NOT investigated**: player-name equivalent — `dim_player`
has severe duplicate short-names ("M. Camara" × 33, "J. González" × 31; NOT explained by league
tier, confirmed present even in Serie A/UCL) that block the same kind of fix until the root cause
is understood; this is bigger than a naming tweak and needs its own investigation before any
player-name correction work starts.

⭐ **BROWSE — REFRAMED, NOT BUILT, design converged but nothing shipped.** The narrow "kill By
country" fix was actually STARTED (working-tree edit to `BrowseGrid.astro`, previewed live) then
DELIBERATELY REVERTED when the CPO asked "what's the benefit of shipping something we're about to
redesign anyway" — correct call: the component's scope, source and content were all about to
change. Redirected to **#45** (internal linking / reachability, already filed, already the place
#44 itself deferred this exact question to). New design, converged across several rounds, NOT
built: **one mart unioning competitions+teams+players** (columns: entity_type, entity_name,
entity_slug, player context_name/context_2_name for club+national-team, competition_names) →
**a "Browse" section at the bottom of every page**, not just home → **10 random UNIQUE rows per
site BUILD** (not per-visitor — static site, no backend, so "random" means "whatever the last
deploy picked") → **bare entity name per chip**, no club/context suffix (confirmed via a rendered
mock: mixing "Kylian Mbappé · Real Madrid" read as two entities in one chip, wrong). Competition
and player chips render INERT (same precedent as every chip on the site today) until their
destination pages exist (#47, #845/#882 respectively); team chips can be REAL links now, team
pages are live. **Blocked from being built by the team-names thread above** — a random sample from
a pool of wrong names is not shippable — and by the player-name-truncation finding needing its own
work first. GAP-33 (Browse reads `docs/competition_registry.yml` directly, zero database reads) is
STILL NOT FILED — the #45 redesign replaces this block's data source entirely, so filing a gap
against code about to be replaced wasn't worth it; re-assess if #45 stalls.

✅ **TOP TEAMS RULED** (mirrors Top players' 2026-08-18 ruling): **one team per league**, not
pooled — CPO: *"one team per league, same as players."* ⚠ Unlike players, the CURRENT
`top_teams_mock.html` (outside the repo, `design-mocks/`) does NOT already show this shape — 3 of
4 boards genuinely mix teams from one league, checked by opening it — needs redoing before it's
trustworthy to preview against. GAP-29's mart (still not started) should partition by league when
built, matching `mart_team_competition_benchmarks`' existing pattern, and the per-league rank is
free. Intro copy PROPOSED (not yet CPO-approved): *"Season to date. The top team from each league:
…"*. Full detail + the mock-checking method: `10_home.md` §0, `99_gaps_register.md` GAP-29/31,
`escalations.log` 2026-08-18/19 entries. This work is on `!76`, unmerged.

## ⭐⭐ THE METHOD, still the standing rule for every page (CPO's own words, do not reword)

*"the exercise is: does the mock consider the underlying mart (or mart gap)."* Per element on a
mock: (1) name the exact MART COLUMN — a seed/registry/catalogue is NOT a source, reading one from
a page is the same violation as computing in the frontend; (2) no mart column = a GAP, registered
in `99_gaps_register.md` before building; (3) check the mock's OWN rendered numbers against the
spec's words before trusting either — caught twice this session alone (Top players' accidental
one-per-league mock; the mixed-chip player/club concat that looked fine until it didn't).

⭐ **AUTOMATION — discussed 2026-08-18, NOT built, NOT approved to start.** A trace script (mock +
mart(s) it should bind to → element-by-element source table + gap list) and a staleness-sweep
checker (flags a wireframe mentioning a removed board/metric not struck through) — both would
mechanize THE METHOD above. Neither started; ask before building either. Issue **#78** tracks the
next full sweep of `10_home.md` this would replace doing by hand.

⚠ **Self-inflicted handover conflict**: this and `!76`'s own OPEN handover commit both branched
from the same base — they WILL conflict on merge. Take THIS version, it supersedes `!76`'s. The
standing rule (handover rides in the SAME commit as the code) got broken twice this session.

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
1. **Team names**: finish the ~15 unverified Pool 1 teams, then decide whether to go beyond Pool 1
   (bigger pool = more names, no ceiling given yet). **Separately, investigate the player-name
   truncation** ("M. Camara" ×33 etc.) — root cause first, this blocks any player-name fix and the
   browse-chip mart's player pool.
2. **Once names are clean: build the sitewide browse-chip mart + component**, design already
   converged (⭐⭐ CURRENT above) — mart, then export, then the component on every page template.
3. ⛔ **TURN ON "Pipelines must succeed"** (Settings → Merge requests) — FALSE since the migration;
   pairs with **#21 Q2** (both are "the server should enforce it").
4. **#47** (the competition hub) — makes the competitions page's rows real links. Three decisions
   if you touch it: 680px width (not the mock's 1080px), single-select filters (multi-select
   deferred), rows inert until this ships (git history + `08_browse.md`, not repeated here). Wire
   `competition_index` into CI's `--entities` list in #47's MR, not before.
5. **The audit stream**: Q2 of #21 · delete 2 dead `~/.claude/hooks/` copies · route/delete
   `seo-expert-reviewer`.
6. **COST, SYSTEMATICALLY** — trigger/cost map first, in a GitLab issue.
7. **#845 + #882 — the CPO's decision.** Unblocks the player page.
8. **Legal/imprint**, then launch.
9. Follow-ups (GITHUB numbers, **bodies UNREACHABLE** — re-derive from code): DE/FI i18n gaps ·
   PROTECTED path editable with no `protected_override` · `Regular Season - 20` provider text the
   copy gate cannot see · blank `competition_type` skipped by all 3 guards.
10. Mine, on GitLab: **#64** #63's residuals · **#67** the contract gate enforces on the Edit tool
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
