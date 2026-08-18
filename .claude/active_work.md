# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-18**. **main `cd8531f`** — `!68` (#62 step5), `!67` (#62 step4), `!65`,
`!66`, `!61`, `!62`, `!60`, `!57`, `!59`, `!58`, `!56`, `!53`, `!50` merged. **NO MR OPEN.** Product
**Matchday Pilot**; **GITLAB** (`glab`, MRs); runner `ci-runner-01`, ZERO GitLab minutes.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding
on `attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ #62 IS DONE AND MERGED — the competitions page is LIVE ON MAIN
⛔ **All five steps shipped and merged.** !61 (#69 dims) → !65 (step3, the mart) → !67 (step4, the
export) → !68 (step5: page-spec, the Astro page, ordering, nav anchor). `/{locale}/competitions/`
builds and renders in all 3 locales, verified in the browser (not just tests) — see CURRENT for the
implementation detail, kept for now since #47 depends on it.
⛔ **PUT `active_work.md` IN `scope_paths` ON EVERY CODE MR**, updated in the SAME commit.
⛔ **Over the cap? DELETE ONE STALE SECTION** — do not shave clauses.
⛔ **NEXT**: #47 (the competition hub) is what makes this page's rows real links — see CURRENT's
gaps list before starting it.
⚠ **Hash mismatch that disagrees with `git_discipline.py --staged-hash`? CHECK FOR A SECOND GLOBAL
HOOK FIRST** (`~/.claude/settings.json` — a plugin's `commit_review_gate.py` hashes differently: no
base commit, no `--raw`, no `hash_exclude_paths`). Cost an hour on 08-18. ⚠ `acceptance_evidence.md`
bullets **must be indented 2sp** — `_block()` stops at column 0, so flush bullets = 0 evidence.

## ⭐ CURRENT — #62 STEP 5, MERGED VIA !68 (2026-08-18)

✅ **The competitions index page is MERGED** (`/{locale}/competitions/`, page + component +
page-spec + 20 i18n keys × 3 locales + the nav anchor). Build detail is in git and `08_browse.md`.
⛔ **THREE DECISIONS, #54 left them open — read before touching that page again:** (1) **width
680px**, not the mock's 1080px — #54 flagged the override "for a ruling" and it never got one;
(2) **filters single-select**, multi-select deferred; (3) **rows are INERT** — #47 isn't built, so
linking is the "browse-chip 404" its own issue names. Rows become links **in the MR that ships
#47**, with hover-lift + chevron.
⚠ **NOT wired into CI's `--entities` list** (`.gitlab-ci.yml:767`/`deploy-site-v2.yml:65` say
`teams,fixtures` only) — deliberate: nothing depends on a refreshed sample yet.
⚠ **`site_v2/src/pages/*/competitions/index.astro`, NOT `[lang]/...`, in any future contract's
`scope_paths`** — `[lang]` is a literal Astro directory name but the contract gate's fnmatch reads
`[...]` as a character class (matches one of l/a/n/g), so the literal path silently fails to match.
Cost 3 stash-dance amendments this session; documented once here so it isn't relearned.
⚠ **DEFERRED by #57 — do not "fix":** `world_championship` keeps its name (branched on at
`int_team_momentum_window.sql:135`; renaming without that edit silently gives the WC a last-5
window, every test green) · `display_group` for **#44**.

⛔ **HOME PAGE: authority is #40 + #41, NOT `10_home.md` §0** (truth is FOUR boards of ONE metric,
top 7). #367 shipped next matches → browse; Top players/teams designed NOT built, slot BETWEEN.
Follow-ups **#36** (blocks #377) · **#38** · **#42**–**#45**.
⭐ **ONE SHARED ORDERING RULE, ruled + built 2026-08-18 (`feat/shared-competition-order`).** The
08-16 key (day → `region_rank` → kickoff → `league_code`) is now the SINGLE site-wide rule for
ranking competitions against each other, implemented once in `lib/competitionOrder.mjs` and called
by BOTH the home hero and the competitions page. Home previously used raw chronology — it predated
the ruling. ⛔ **Also ruled: the hardcoded `_HERO_FIXTURE_LIMIT = 12` is RETIRED** — the hero now
shows THE NEXT MATCHDAY (every match on the earliest upcoming date). CPO: *"we will show what we
have, more matches will come, because we ingest more competitions."* Both in `escalations.log`.
⚠ **A busy matchday can carry ~57 fixtures** (`10_home.md` measurement). If that reads too long the
answer is **#908**'s "more matches" control — **NOT** a new cap. Reserved to the CPO, do not decide.
⚠ **REFRESH THE DATA SAMPLE AS A SET.** Regenerating `landing.json` changed which fixtures home
links to and broke the build (8 dead links) because `src/data/fixtures/` was still the 08-03 set.
`src/data/README.md` documents it; `audit-seo` is the ONLY thing that catches it. Update the
`.gitignore` allowlist in the same commit.
⚠ **The GAPS REGISTER was STALE for 8 days and is now CORRECTED (2026-08-18).** GAP-24/25/26 were
written against the NINE-board design the CPO reduced to FOUR on 08-10; all three are now **VOID**
(every metric they asked for was cut). ⛔ **GAP-26 in particular claimed to be "the highest-risk of
the six" about a goals-conceded board deleted 8 days earlier — and I repeated that alarm to the CPO
as live.** Survivors re-verified against the warehouse, not memory: **GAP-27** (no club on a
leaderboard row, `grep -c team_sk` = 0) · **GAP-28** (pool membership — ⚠ its `tier`/`season_type`
projection is ALREADY BUILT, only the authored pool field is left) · **GAP-29** (no
team-side mart at all). NEW: **GAP-30** `assists` is not a ranked board · **GAP-31** the mart ranks
per-league (`partition by league_code`) but the design ranks across the pool. ⭐ **A design change
does not update the register — reconcile it whenever a mock changes**, or it misleads scoping.
⚠ **REBASE TAX:** conflicts land in `.claude/task/*` and `active_work.md` — **MINE** for
contract/review, **UNION** `escalations.log`, then REBIND `diff_sha256`. ⚠ **NEVER `git checkout --`
to restore uncommitted work** — it restores from HEAD and wipes it. ⛔ **The contract/Stop gates do
NOT understand a stash-pop conflict either** — mid-pop they call the popped files "out of scope"
against the stale contract; write the fresh contract FIRST (clean tree), THEN pop.

## ⭐ ORIENTATION
**Audits: GitLab #30, DO NOT run another** (rejected 08-16; a TARGETED blind assessment is different
and IS allowed — `!59` came from two). **Mechanism beats wording:** of 50 corrections, 33 prose-only,
22 recurred.
**⚠ OPERATIONAL NOTES LIVE IN `CLAUDE.md`** — dbt CLI, SQLFluff, commit mechanics, the stash-dance,
CWD/fnmatch/heredoc/grep traps. **Do not copy back**: that file is not capped.
**FIRST ACTION: `git stash list` before any git work.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX. ONE
must not be rebuilt: **`feat/player-overview-tab: Overview BUILT`** (the #62 mart stash is now
popped and shipped, ⭐ above).

## ⭐⭐ THE RULE, 2026-08-17: **RAW APPENDS AND NEVER DELETES. BASE DECIDES.**
**`!59` IS this rule, MERGED** — all three delete paths gone. A reversal of 8b and #539's delete
half: **never "restore" a delete as a regression fix.** Record: `docs/data_contract.md` § "Raw
appends and never deletes" + `escalations.log` 08-17. Cost approved ~$1-2/mo.
⚠ **Bounding growth = compact by VERSION COUNT**, never a delete at write time, never keyed on time
(#892). ⚠ **The `LOGICAL_OR` in `_read_fetched_coverage` + `coverage.read_coverage` is LOAD-BEARING
— never "simplify" to a per-row read.**
⭐ **THE REPO IS NOT THE SYSTEM**: for warehouse/cloud/scheduler facts check the system that owns
them (`bq ls`, `gcloud run jobs describe` — free metadata).

## ⭐ The ingest cluster
**TWO nightlies:** `data:nightly` moved to **Cloud Run under #39**; the GitLab schedule (4379625)
is **paused ON PURPOSE.** Runbook `deploy/nightly/README.md`. ⚠ 04:00 FAILED 08-17.
⛔ **#74 — THE IMAGE NEVER TRACKED `main`.** `--source .` packages the WORKING TREE; nothing
redeploys on merge. It once ran 08-14 code for two days and **rebuilt prod from it, REVERTING
`!43`/`!45`**. ⭐ **THE FULL SPEC IS ON ISSUE #74 (note 3695790497): ready to implement, DO NOT
re-derive it.** Protected path → `protected_override` + impact_map + **2 OPUS reviewers**.
Redeployed by hand 08-16 and twice on 08-17 (now `d47862434f71`, carries `!62`); **until #74 ships,
redeploy from a clean `main` after EVERY ingestion merge or the fix never reaches prod.**
⚠ **A GREEN EXECUTION PROVES NOTHING** — it says the container ran, not which code. **Check DATA.**
⚠ **None of the four ingest fixes does what its title says** — caveats on #896-#898.
✅ **MR2 (`!62`) MERGED 08-17** — the four "gap recorded as fact" holes are closed. **MR3 =
detection, NOT started:** lower `event_loss_detector_from` (still **'2026-08-19', in the FUTURE, so
`!57`'s test is inert**); ⛔ **the volume-delta threshold is the CPO's and blocks it.** **MR4 =
compaction, only if growth is MEASURED.**

## ⭐ COST — read **GitLab issue #3** first
**#3 holds it all** — baselines, #547's ranked list IN ITS ORDER, the free tools (`bq query
--dry_run`, `report_bq_cost.py`; ⚠ **paste the output or do not claim it**), the traps (**never a
time-based partition expiry on raw**, #892). Read it; do not redo it. ⚠ **#70** is the scan-budget
guard; `require_partition_filter` + `maximum_bytes_billed` are **NEITHER set**.
- **⚠ STORAGE NEVER MEASURED** (**0×** in #3); every figure is bytes SCANNED. `bq show` is free.
- **⚠ Spend UNKNOWN.** Last measure 08-03 ($2.73/day) PREDATES #33 items 9/15.
- **⚠ Do NOT claim the API quota "breaks first"** — claimed once without evidence, withdrawn.

## ⭐ REVIEW MECHANICS — traps only; rules are `docs/working_agreement.md` §2 (#878)
- **Build the patch with the hook, never by hand:** `git_discipline.py --review-patch >
  .claude/task/review_input.patch`. ⚠ It is `git diff --staged <base>`, so **`git add` FIRST or it
  comes out EMPTY** (`review.md` too). `contract.md` + `escalations.log` ARE delivered; task notes
  are not, and a trailer names any excluded file that IS edited (#25).
- **Run `check_task_artifacts.py` BARE** (#24) — `--base origin/main` resolves the DORMANT GitHub
  remote and returns a fictitious hash. ⚠ **On a MERGE commit, rebind `diff_sha256` AFTER the merge
  is committed**: the merge moves its own base. **`--staged-hash` matches CI on ordinary commits.**
- **A PASS may find nothing.** One `risks_checked:` entry is enough; never invent one. Cap 3 rounds
  then STOP. ⚠ `rounds: 0` is REFUSED.
- **`.claude/task/**` is scope-exempt; `active_work.md` is NOT** — it must be in `scope_paths`; a
  commit touching `contract.md` is **never** artifact-exempt. ⚠ **The contract needs a CLEAN tree**,
  so a write mid-task = stash with EXPLICIT PATHS (`-u` if untracked), write, pop, check
  `git stash list`.
- **⭐ A correction REPLACES, never accumulates, and must replace EVERYWHERE.** ⚠ 08-14: four
  occurrences cost five rounds. **Sweep the CLASS repo-wide BEFORE review**, not the reviewer's
  list of examples.

## Player page — HELD on #845
**#846 + #886 merged:** the season a page opens on is a warehouse fact (`is_featured_season`, DQ
guarded). **CPO: the pipeline picks, not the page.**
**#845 + #882 are ONE decision and his** — which entities earn a page, and whether a past season
gets a URL or a control; deciding apart sets the URL shape twice. Measured (×3 locales): players
51,589→154,767; **matches BIGGER at 176,235**; h2h 51,903; teams 9,669; a 5-match gate leaves 1,274
teams / 21,979 players. **Bring the counts.**
**Overview is BUILT but UNCOMMITTED** in stash `feat/player-overview-tab` (⚠ NOT the #62 stash,
which is now popped and shipped); default is known-wrong (`seasons[0]` = newest of ANY comp).
**#848: FOUR tabs**, International a TAB not a toggle.

## OWED — deferred
- **Guard telemetry is absent** (#30 finding 4) — 2,684 lines of enforcement, zero records of a gate
  firing. Also: delete `macros/apif_latest_source_partition.sql` · mirror crests.
- ⛔ **The contract/Stop gates do NOT understand a MERGE or a stash-pop conflict.** Mid-merge they
  call what the other branch brings in "out of scope" and say `git checkout -- <file>` — DELETES
  it. Needs a `MERGE_HEAD`-aware skip; protected path, own task.
- **⭐ #904 IS THE DOMINANT FAILURE** — a claim asserted rather than RUN. **Absence must state where
  it looked; a test must be seen RED; green is not evidence.**

## NEXT
0. ⛔ **TURN ON "Pipelines must succeed"** (Settings → Merge requests). It is **FALSE**, so every MR
   has been mergeable while RED since the migration. CPO's, one toggle. Pairs with **#21 Q2**.
1. **THE NIGHTLY: #74** (⭐ ingest cluster above).
2. ✅ **#62 ALL FIVE STEPS DONE AND MERGED** (⭐ above). **#47** (the competition hub) is next — it's
   what makes this page's rows real links (three decisions in CURRENT explain why they aren't yet).
   Wire `competition_index` into CI's `--entities` list in #47's MR, not before.
3. **The audit stream (⭐ above).** The CPO's, one command each: **Q2 of #21** (`main` push access
   to No one) · delete the 2 dead `~/.claude/hooks/` copies · route or delete `seo-expert-reviewer`.
4. **⭐ THEN COST, SYSTEMATICALLY** — the whole pipeline **including CI/CD, what gets triggered,
   when, where** (CPO). Trigger/cost map FIRST, rank by real spend, fix in that order; the map goes
   in a GitLab ISSUE.
5. **#845 + #882 — the CPO's decision.** Counts are in this file: bring them, not a general
   question. Unblocks the player page off the stash.
6. **Legal/imprint**, then launch.
7. Follow-ups (GITHUB numbers, **bodies UNREACHABLE** — re-derive from code): DE/FI i18n gaps ·
   PROTECTED path editable with no `protected_override` · `Regular Season - 20` provider text the
   copy gate cannot see · blank `competition_type` skipped by all 3 guards.
8. Mine, on GitLab: **#64** #63's residuals · **#67** the contract gate enforces on the Edit tool
   only, so `sed -i` bypasses it · **#68** the form-window CODE diverges from
   `metrics_context_model.md` §4 (⚠ **the agreement is the authority**; never fix it by editing the
   doc) · **#60** `.venv` is not where `CLAUDE.md` implies · **#70** scan-budget guard.

## OPEN — the CPO's alone
**Imprint operator + address** (#799), blocks publication, never conclude it ·
hosting recurring run · feedback Apps Script (#687) · **#850** alias · **#875** where a group name
lives · **#895 slim-vs-drop** · **#21**.

## DO NOT (standing)
- **DESIGN, the weak spot:** never off the cuff — approved wireframes + role briefs, no block
  invented to fill a slot, never the canonical page built on an edge case, ONE tab at a time.
  Rendered output not prose; copy decisions BEFORE the branch.
- Do NOT treat the tracker as agreed work; re-validate. **No new planning docs, no fresh audits.**
  Do NOT touch `site/` (retired). Do NOT derive facts in the export or frontend.
- ⛔ **VERIFY BEFORE ASSERTING; FINISH EXPLORE BEFORE PROPOSING.** Search `escalations.log` + docs
  for a prior ruling FIRST.
- **Never merge an MR. The CPO merges. Branch from main; never commit to main.**
- Plain language, lead with the decision, **no em dashes**, no walls of text. Do NOT ask him to
  adjudicate what a rule settles (**but copy is ALWAYS his, §10**), and do NOT bring him a fix for a
  defect he never asked about — fix it and move on.

## Verified state reference
- **v2 built:** design system + 26 components, fixture page, team page (3 tabs), home page (next
  matches → browse), page-spec + SEO contract (#826/#844), per-locale metric labels.
- **Tests: 813 python + 1 skipped** (08-17; 818 collected on main), 59 site, **~1010 dbt in prod**
  (`!61` added 11; this MR adds 17 more, unbuilt until merge). ⚠ MEASURE, never predict (#904).
  `ruff` = `lint:python`, `.ruff-ci.toml`.
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). Reselling
  API-Football data is the one hard prohibition.
