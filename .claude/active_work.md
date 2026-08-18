# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-17**. **#74 MR OPEN** (`fix/74-nightly-image-tracks-main`, not merged); main
**`f00ab21`** — `!61` (#69 dims), `!60`, `!57`,
`!59`, `!58`, `!56`, `!53`, `!50` merged, **prod rebuilt GREEN** (#75, closed — `escalations.log`
has the recovery detail). Product **Matchday
Pilot**; **GITLAB** (`glab`, MRs); runner `ci-runner-01`, ZERO GitLab minutes. ⚠ **A GROUP MOVE IS
COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ THE NEXT JOB, CPO-SET 2026-08-17: **PUT THE COMPETITIONS PAGE ON SCREEN**
⛔ **#62 steps 3 → 4 → 5, in AS FEW MRs as the rules allow.** CPO on pace: 12 MRs in a day, **only 5
product, 7 paperwork ABOUT the product**, a whole day on the substrate behind ONE line of text.
*"With this speed the website will never get done."* Correct.
⛔ **PUT `active_work.md` IN `scope_paths` ON EVERY CODE MR**, updated in the SAME commit. Seven
separate handover MRs each cost a contract + a review round; two conflicted. Biggest waste.
⛔ **Over the cap? DELETE ONE STALE SECTION** — do not shave clauses; that burned much of 08-17.
⛔ **Do NOT re-perfect the substrate.** Step 5 is mechanical now the dims exist; the mart is
WRITTEN. Build, do not redesign.

## ⭐ CURRENT — #62 STEP 3 IS BLOCKED ON #69'S FKs (step 5). DO NOT BUILD THE MART (2026-08-17)

**#62, five steps.** 1 (`!40`) and 2 (#57) done. **3 is `mart_competition_index`**, 4 repoints the
export, 5 the page spec. ⚠ A seed COLUMN and its reader cannot ship together — 3 is its own MR.
⛔ **THE MART IS WRITTEN AND PARKED** — `git stash list`, match by MESSAGE
`feat/62-mart-competition-index`. `region_label` was the blocker. **CPO: *"You don't mix up countries
and continents in one column and add a flag 'single country'."***
✅ **#69 STEPS 1-3 DONE — `!61` MERGED: `dim_country` (224 rows) + `dim_region`.** A competition
POINTS AT one; **which relationship is populated IS the answer** — no flag. **The 08-16/17 notes on
#69 are the authority.** ⚠ **Both dims are LEAVES guaranteeing NOTHING yet** — no FK, so an unknown
country still reaches the page silently. **STEP 5 = the four FKs** (league/team/player/coach country
cols): makes an unknown country FAIL rather than render, deletes `single_country`, unblocks step 3.
⚠ `countries.csv` has **no i18n key** (224x3, a copy cost, HIS) and **no confederation** (NO SOURCE).
⚠ **`layering.md` OVERRIDDEN in two places, recorded** — do not "restore" it. ⚠ **Never normalise
country names by regex** (`Guinea-Bissau` is correct, MEASURED). **The transformation layer decides
the FORM, the CPO the NAME.**
⛔ **`sort_order` IS OBSOLETE (CPO 08-16)**; the mart must not read it. **The full rule is the 08-16
ordering note on #54 — read it, do not reconstruct.** ⚠ **Mart carries FACTS, the spec declares the
ORDER BY.** ⚠ Retiring it reaches into `export_site_data.py`, `BrowseGrid.astro`, `landing.json` —
NOT scoped. ⚠ **#54's 16 is ELEMENTS, not mart columns.**

⛔ **HOME PAGE: authority is #40 + #41, NOT `10_home.md` §0** (truth is FOUR boards of ONE metric,
top 7). #367 shipped next matches → browse; Top players/teams designed NOT built, slot BETWEEN.
Follow-ups **#36** (blocks #377) · **#38** · **#42**–**#45**.
⚠ **REBASE TAX:** conflicts land in `.claude/task/*` and `active_work.md` — **MINE** for
contract/review, **UNION** `escalations.log`, then REBIND `diff_sha256`. ⚠ **NEVER `git checkout --`
to restore uncommitted work** — it restores from HEAD and wipes it.
⚠ **DEFERRED by #57 — do not "fix":** `world_championship` keeps its name (branched on at
`int_team_momentum_window.sql:135`; renaming without that edit silently gives the WC a last-5
window, every test green) · `display_group` for **#44**.

## ⭐ ORIENTATION
**Audits: GitLab #30, DO NOT run another** (rejected 08-16; a TARGETED blind assessment is different
and IS allowed — `!59` came from two). **Mechanism beats wording:** of 50 corrections, 33 prose-only,
22 recurred.
**⚠ OPERATIONAL NOTES LIVE IN `CLAUDE.md`** — dbt CLI, SQLFluff, commit mechanics, the stash-dance,
CWD/fnmatch/heredoc/grep traps. **Do not copy back**: that file is not capped.
**FIRST ACTION: `git stash list` before any git work.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX. TWO
must not be rebuilt: **`feat/player-overview-tab: Overview BUILT`** and the **#62 mart** (⭐ above)._

## ⭐⭐ THE RULE, 2026-08-17: **RAW APPENDS AND NEVER DELETES. BASE DECIDES.**
**`!59` IS this rule, MERGED** — all three delete paths gone. A reversal of 8b and #539's delete
half: **never "restore" a delete as a regression fix.** Record: `docs/data_contract.md` § "Raw
appends and never deletes" + `escalations.log` 08-17. Cost approved ~$1-2/mo.
⚠ **Bounding growth = compact by VERSION COUNT**, never a delete at write time, never keyed on time
(#892). ⚠ **The `LOGICAL_OR` in `_read_fetched_coverage` + `coverage.read_coverage` is LOAD-BEARING
— never "simplify" to a per-row read.**
⭐ **THE REPO IS NOT THE SYSTEM**: for warehouse/cloud/scheduler facts check the system that owns
them (`bq ls`, `gcloud run jobs describe` — free metadata). `raw_archive` was called "never built"
from zero repo refs; it EXISTS (`*_20260808` snapshot) — true of the repo, false as a conclusion.

## ⭐ The ingest cluster
**TWO nightlies:** `data:nightly` on **Cloud Run under #39**; GitLab schedule (4379625) paused ON
PURPOSE. Runbook `deploy/nightly/README.md`.
✅ **#74 FIXED, MR OPEN** (`fix/74-nightly-image-tracks-main`, NOT yet merged): `build:nightly-image`
(kaniko, no Cloud Build) + `deploy:nightly-image` rebuild the image and repoint `fdp-nightly` on
every `main` push touching `*data_paths_image`. ⚠ **NOT `--source .`/Cloud Build** — Cloud
Build's default identity holds project Editor; granting our SA build access opened an Editor
path from ANY unmerged branch. Revoked; redesigned to build in-job.
⚠ **OWED: set `deploy-nightly-image` resource_group to `oldest_first`** (Settings → CI/CD, only
after the group exists — first run creates it). Default `unordered` mode means two
near-simultaneous merges can deploy out of order, pinning the OLDER commit until the next one.
**Sentinel (`fdp-freshness`) still NOT repointed** — deliberately separate, stays pinned.
**Until MERGED, keep redeploying by hand after every ingestion merge.**
⚠ **A GREEN EXECUTION PROVES NOTHING** — it says the container ran, not which code. **Check DATA.**
⚠ **None of the four ingest fixes does what its title says** — caveats on #896-#898.

## ⭐ COST — read **GitLab issue #3** first
**#3 holds it all** — baselines, #547's ranked list IN ITS ORDER, the free tools (`bq query
--dry_run`, `report_bq_cost.py`; ⚠ **paste the output or do not claim it**), the traps (**never a
time-based partition expiry on raw**, #892). Read it; do not redo it. ⚠ **#70** is the scan-budget
guard; `require_partition_filter` + `maximum_bytes_billed` are **NEITHER set**.
- **⚠ STORAGE NEVER MEASURED** (**0×** in #3); every figure is bytes SCANNED. `bq show` is free.
  ⚠ **`!59` makes raw grow again** — no post-8b figure is a size, only a floor.
- **⚠ Spend UNKNOWN.** Last measure 08-03 ($2.73/day) PREDATES #33 items 9/15.
- **⚠ Do NOT claim the API quota "breaks first"** — claimed once without evidence, withdrawn.
  (`standings.py:30`/`teams.py:28` DO loop every season daily with no skip — real.)

## ⭐ REVIEW MECHANICS — traps only; rules are `docs/working_agreement.md` §2 (#878)
- **Build the patch with the hook, never by hand:** `git_discipline.py --review-patch >
  .claude/task/review_input.patch`. ⚠ It is `git diff --staged <base>`, so **`git add` FIRST or it
  comes out EMPTY** (`review.md` too). `contract.md` + `escalations.log` ARE delivered; task notes
  are not, and a trailer names any excluded file that IS edited (#25).
- **Run `check_task_artifacts.py` BARE** (#24) — `--base origin/main` resolves the DORMANT GitHub
  remote and returns a fictitious hash. ⚠ **On a MERGE commit, rebind `diff_sha256` AFTER the merge
  is committed**: the merge moves its own base, so a hash taken from the staged index binds nothing
  and CI fails F11. `--staged-hash` matches CI on ordinary commits (#63).
- **A PASS may find nothing.** One `risks_checked:` entry is enough; never invent one. Cap 3 rounds
  then STOP. ⚠ `rounds: 0` is REFUSED.
- **`.claude/task/**` is scope-exempt; `active_work.md` is NOT** — it must be in `scope_paths`; a
  commit touching `contract.md` is **never** artifact-exempt. ⚠ **The contract needs a CLEAN tree**,
  so an amendment mid-task = stash with EXPLICIT PATHS, edit, pop, check `git stash list`.
- ⚠ **`git rebase` replays commits IN ORDER**, so a scope amendment committed LAST does not apply
  to an earlier commit's conflict. **`git merge` applies the tip at once — use it.**
- **⭐ A correction REPLACES, never accumulates, and must replace EVERYWHERE.** ⚠ 08-14: four
  occurrences cost five rounds. **Sweep the CLASS repo-wide BEFORE review**, not the reviewer's
  list of examples: on `!59` fixing the three files a reviewer NAMED left six more. **#71**.

## Player page — HELD on #845
**#846 + #886 merged:** the season a page opens on is a warehouse fact (`is_featured_season`, DQ
guarded). **CPO: the pipeline picks, not the page.**
**#845 + #882 are ONE decision and his** — which entities earn a page, and whether a past season
gets a URL or a control; deciding apart sets the URL shape twice. Measured (×3 locales): players
51,589→154,767; **matches BIGGER at 176,235**; h2h 51,903; teams 9,669; a 5-match gate leaves 1,274
teams / 21,979 players. **Bring the counts.**
**Overview is BUILT but UNCOMMITTED** in stash `feat/player-overview-tab` (⚠ NOT the #62 stash);
default is known-wrong (`seasons[0]` = newest of ANY comp). **#848: FOUR tabs**, International a
TAB not a toggle.

## OWED — deferred
- **Guard telemetry is absent** (#30 finding 4) — 2,684 lines of enforcement, zero records of a gate
  firing. Also: delete `macros/apif_latest_source_partition.sql` · mirror crests.
- ⛔ **The contract/Stop gates do NOT understand a MERGE.** Mid-merge they call what the other
  branch brings in "out of scope" and say `git checkout -- <file>` — which DELETES it. Needs a
  `MERGE_HEAD`-aware skip; protected path, own task.
- **⭐ #904 IS THE DOMINANT FAILURE** — a claim asserted rather than RUN. Faces seen: a grep scoped
  narrower than its sentence (`!59`); a TEST that passes either way (#63 shipped three); a column
  read without its VALUES (`!43`); a number repeated out of this file (`!47`); a JOB STATUS read
  instead of the data (`!49`); a "verified" absence that only checked the REPO (`raw_archive`).
  **Absence must state where it looked; a test must be seen RED; green is not evidence.**

## NEXT
0. ⛔ **TURN ON "Pipelines must succeed"** (Settings → Merge requests). It is **FALSE**, so every MR
   has been mergeable while RED since the migration — the enforcement never came across with the
   jobs. Unsafe while the orphan blocked every build; **now cleared, so this is the moment.**
   CPO's, one toggle. Pairs with **#21 Q2**: both are "the server should enforce it".
0b. ✅ **MR2 (`!62`) MERGED 08-17** — the four "gap recorded as fact" holes are closed and the image
   was redeployed. **MR3 = detection, NOT started:** lower `event_loss_detector_from` (still
   **'2026-08-19', in the FUTURE, so `!57`'s test is inert**) and extend loss detection past events;
   ⛔ **the volume-delta threshold is the CPO's and blocks it.** **MR4 = compaction, only if growth
   is MEASURED.**
1. ✅ **PROD IS HEALED** (#75, closed) — rebuilt green 08-17 by retrying `data:build:main` on
   `main`. ⚠ `.data_paths_prod` EXCLUDES `.gitlab-ci.yml` and `ingestion/**` but INCLUDES
   `dbt_project/models/**`. ⚠ **#4: a web dispatch from ANY branch builds prod from THAT branch's
   code** — retry the job on `main` instead.
2. ✅ **#74 MR OPEN**, review + merge (⭐ ingest cluster above). Then decide the sentinel repoint.
3. **#69 STEP 5 (the four FKs), then #62 step 3** (⭐ CURRENT). Steps 1-3 are merged. Then #62
   step 4 repoints the export, 5 the page spec.
4. **The audit stream (⭐ above).** The CPO's, one command each: **Q2 of #21** (`main` push access
   to No one) · delete the 2 dead `~/.claude/hooks/` copies · route or delete `seo-expert-reviewer`.
5. **⭐ THEN COST, SYSTEMATICALLY** — the whole pipeline **including CI/CD, what gets triggered,
   when, where** (CPO). Trigger/cost map FIRST, rank by real spend, fix in that order; the map goes
   in a GitLab ISSUE.
6. **#845 + #882 — the CPO's decision.** Counts are in this file: bring them, not a general
   question. Unblocks the player page off the stash.
7. **Legal/imprint**, then launch.
8. Follow-ups (GITHUB numbers, **bodies UNREACHABLE** — re-derive from code): DE/FI i18n gaps ·
   PROTECTED path editable with no `protected_override` · `Regular Season - 20` provider text the
   copy gate cannot see · blank `competition_type` skipped by all 3 guards.
9. Mine, on GitLab: **#64** #63's residuals · **#67** the contract gate enforces on the Edit tool
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
  for a prior ruling FIRST — on #75 four fixes were invented while **#896** already answered it
  (CPO: *"you are always coming up with something new. THAT is the real defect"*).
- **Never merge an MR. The CPO merges. Branch from main; never commit to main.**
- Plain language, lead with the decision, **no em dashes**, no walls of text. Do NOT ask him to
  adjudicate what a rule settles (**but copy is ALWAYS his, §10**), and do NOT bring him a fix for a
  defect he never asked about — fix it and move on.

## Verified state reference
- **v2 built:** design system + 26 components, fixture page, team page (3 tabs), home page (next
  matches → browse), page-spec + SEO contract (#826/#844), per-locale metric labels.
- **Tests: 813 python + 1 skipped** (08-17; 818 collected on main), 59 site, **~1010 dbt in prod**
  (`!61` added 11). ⚠ MEASURE, never predict (#904). `ruff` = `lint:python`, `.ruff-ci.toml`.
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). Reselling
  API-Football data is the one hard prohibition.
