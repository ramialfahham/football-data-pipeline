# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-20**. **main `d8c6635`**. Merged today: `!82` (MR1) and `!83` (MR2) of the
description-drift programme, plus the handover `!84`. **MR3 is OPEN on
`chore/description-cleanup-shared-and-seeds`.** Merged 08-19: team_name_overrides batches 1+2,
the Top teams ruling record, the Browse drop (`!80`). Product **Matchday Pilot**; **GITLAB**
(`glab`, MRs); runner `ci-runner-01`, ZERO GitLab minutes.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding
on `attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ CURRENT — description-drift programme: MR1-MR3 done, MR4 is next (2026-08-20)

⭐ **THE PLAN IS APPROVED AND WRITTEN DOWN. Read `.claude/task/escalations.log`'s 2026-08-20 entry
FIRST** — it holds the CPO's diagnosis verbatim, the audit's measured numbers, the definition of a
good description, the three rulings and the six-MR split with its ordering constraints. Plan file:
`C:\Users\Rami\.claude\plans\jazzy-greeting-teacup.md`. **Do not re-scope or re-audit any of it.**

**WHY.** `description:` fields were used as a decision log. An independent dbt audit measured 616
descriptions across 19 files; 412 healthy; 5 files hold 83% of the bad text. THREE were provably
FALSE (fixed in MR1). Root cause: descriptions have **no reader** — `persist_docs` absent, docs
site never generated — so the field had no feedback loop and became the cheapest dumping ground.

| MR | What | State |
|---|---|---|
| 1 | 3 false claims + rewrite `engineering_standards.md` §2 | ✅ `!82` |
| 2 | docs blocks for the 8 repeated columns | ✅ `!83` |
| 3 | clean `5_marts/shared/shared.yml` + `seeds/schema.yml` | ✅ open, awaiting merge |
| **4** | **clean `core.yml`, `base.yml`, `int_momentum.yml`** | **← NEXT** |
| 5 | `scripts/check_description_hygiene.py` + tests + wiring | pending, needs `protected_override` |
| 6 | `persist_docs` + `dbt docs generate` | pending |

⚠ **ORDERING IS LOAD-BEARING.** MR5 after 3-4, so the gate is green on day one (`check_copy_gate.py`
precedent). MR6 after 3-4 because **BigQuery rejects column descriptions over 1,024 chars and 15
currently exceed it** — enabling `persist_docs` first BREAKS the nightly build.

**MR4 concretely — same method as MR3, the worked example.** Rewrite each description to say what
the data MEANS: business meaning · grain · where it comes from / how calculated · known limits.
Rulings → `escalations.log` **only if absent there** (most restate an existing entry and are just
deleted); open questions → GitLab issue; dates and "UPDATED" → DELETE. **Banned: any claim about
who reads a column downstream.** All under **600 chars**, or MR5's gate is red on day one.

⭐ **MR3's METHOD, reuse it.** A scanner over both files (251 descriptions, zero violations), plus a
prose-only PROOF: parse both versions, strip every `description`, diff the rest — 1,752 nodes
identical. Beats eyeballing a 1,000-line diff. It filed **#79 #80 #81** and rescued into
`escalations.log` the 4 rulings that existed ONLY in a description.

⛔ **FIVE TRAPS, every one hit for real in MR1-MR3. Do not re-learn them.**
1. **A too-narrow grep reported as a clean sweep.** "partition key" is FALSE — zero models declare
   `partition_by`/`cluster_by`. MR3 cleared the 4 in `5_marts/shared/`; a WIDER sweep then found
   **6 more** (5 docs + `.claude/hooks/dbt_layer_gate.py:72`, which re-teaches it as PreToolUse
   context on **every mart edit**). That is **#79**, and it needs `protected_override`.
2. **A bulk-edit script that reported success while matching nothing.** Any such script must assert
   it found work (`if seen == 0: return 1`) or it silently no-ops and looks green.
3. **A shared docs block that is wrong at some call sites.** `dbt parse` cannot catch it — read
   every call site.
4. **Do not accept a reviewer finding uncritically.** One MR2 finding was a false positive.
5. **`--review-patch` writes to STDOUT.** Without `> .claude/task/review_input.patch` the patch is
   silently the PREVIOUS task's and looks plausible — check its `diff --git` list against
   `git status`. Relatedly `origin/main` is the DORMANT GitHub remote, commits behind, so
   `merge-base HEAD origin/main` gives a stale base; use `main`/`gitlab/main`.

⛔ **THE STANDING LESSON, from the Browse drop (08-19) and confirmed again here.** CPO: *"you spam
things all around the repo and then forget to clean up. and then we have contradictions in our docs
and files."* The killer instance used **no instance of the word being swept**, so text search was
structurally blind. **Sweep the CONCEPT semantically — who claims to consume/render/feed the thing
— never the feature's name.** Evidence on GitLab **#71**, whose premise is now "the duplication
that makes propagation necessary".

⛔ **TEAM NAMES — the other live thread, paused not finished.** The provider's `team_name` is often
not the display name even when unique. `team_name_overrides` (seed, joined in
`base_apif__teams_global.sql`) fires on completeness OR collision since the CPO's ruling: *"we have
to define the name we use as the single source of truth for what we display."* **97 of ~130 Pool 1
teams (PL/PD/SA/BL1/ED/L1/LP) corrected and merged**, each citing an English Wikipedia URL.
⚠ **Bayern München DELIBERATELY EXCLUDED** — locale preference is never corrected.
**NOT done**: ~15 Pool 1 teams Wikipedia didn't clearly cover; teams outside Pool 1.
**NOT investigated**: the player-name equivalent — `dim_player` has severe duplicate short-names
("M. Camara" ×33), even in Serie A/UCL. Root cause first; it blocks any player-name fix.
⚠ Duplicate provider records for ONE club are a separate, unbuilt mechanism — now GitLab **#81**.

✅ **BROWSE — DROPPED AND MERGED (`!80`).** Do not re-propose without a new ruling. Home renders
**next matches ALONE**. KEPT and NOT stale: the struck decision record, and `08_browse.md` + the
competitions index page, both LIVE. ⚠ `build_nav`/`fetch_nav`/`nav.json` NOT removed, now with
**zero frontend consumer** — see NEXT 2.

✅ **TOP TEAMS RULED AND MERGED**: **one team per league**, not pooled (mirrors Top players).
⚠ `top_teams_mock.html` (`design-mocks/`) does NOT show this shape — redo before previewing against
it. GAP-29's mart is not started; partition by league when built. Detail: `10_home.md` §0,
`99_gaps_register.md` GAP-29/31.

## ⭐⭐ THE METHOD, still the standing rule for every page (CPO's own words, do not reword)

*"the exercise is: does the mock consider the underlying mart (or mart gap)."* Per element on a
mock: (1) name the exact MART COLUMN — a seed/registry/catalogue is NOT a source, and reading one
from a page is the same violation as computing in the frontend; (2) no mart column = a GAP,
registered in `99_gaps_register.md` before building; (3) check the mock's OWN rendered numbers
against the spec's words before trusting either.

⭐ **AUTOMATION — NOT built, NOT approved to start.** A trace script (mock → element-by-element
source table + gap list) and a staleness-sweep checker would mechanize THE METHOD. Ask before
building either. **#78** tracks the next full `10_home.md` sweep this would replace.

⚠ **STANDING RULE: the handover rides in the SAME commit as the code it describes.** Broken four
times on 08-19/08-20; MR3 followed it. Between the two commits the file states something untrue,
and it conflicts with a sibling branch's handover.

## ⭐ ORIENTATION
**Audits: GitLab #30, DO NOT run another** (rejected 08-16; a TARGETED blind assessment is different
and IS allowed). **Mechanism beats wording:** of 50 corrections, 33 prose-only, 22 recurred.
**⚠ OPERATIONAL NOTES LIVE IN `CLAUDE.md`** — dbt CLI, SQLFluff, commit mechanics, the stash-dance,
CWD/fnmatch/heredoc/grep traps. **Do not copy back**: that file is not capped.
**FIRST ACTION: `git stash list` before any git work.** ⚠ MATCH BY MESSAGE, NEVER BY INDEX. ONE
must not be rebuilt: **`feat/player-overview-tab: Overview BUILT`**.

⭐ **THE REPO IS NOT THE SYSTEM**: for warehouse/cloud/scheduler facts check the system that owns
them (`bq ls`, `gcloud run jobs describe` — free metadata). `raw_archive` was called "never built"
from zero repo refs; it EXISTS — true of the repo, false as a conclusion. `#75 closed 08-17`; its
recovery detail and the permanent `!57` kickoff floor are in `escalations.log`, not repeated here.

## ⭐ The ingest cluster
**TWO nightlies:** `data:nightly` on **Cloud Run under #39**; GitLab schedule (4379625) paused ON
PURPOSE. Runbook `deploy/nightly/README.md`.
✅ **#74 FIXED AND MERGED** (`!70`): the nightly image tracks `main` automatically on any push
touching `*data_paths_image`, so hand-redeploying after an ingestion merge is no longer required —
**but the FIRST auto-run since merge is UNVERIFIED; check it fired.** ⚠ **NOT Cloud Build** — its
default identity holds project Editor, an Editor path from ANY unmerged branch. Revoked; builds
in-job with kaniko.
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
- ⛔ **The contract/Stop gates do NOT understand a MERGE.** Mid-merge, every file the incoming side
  touches reads as "dirty outside the contract", and the clean-tree rule then blocks editing
  `contract.md` to describe the merge — circular. ⚠ **WORKAROUND, not a fix**: `_gate_bash_pre` in
  `task_contract_gate.py` skips any path under `.claude/task/`, so write `contract.md`/`review.md`
  via Bash (`cp` from a scratchpad) while mid-merge. Needs a real `MERGE_HEAD`-aware skip;
  protected path, own task.
- **#904 IS THE DOMINANT FAILURE** — a claim asserted rather than RUN. A test must be seen RED.
  ⚠ Twice on 08-20 a check told me what I wanted: a bulk-edit script that matched nothing and
  reported success, and a `pytest --timeout=900` run that errored on the unknown flag and still
  exited 0. **Read the output, never the exit code.**

## NEXT
0. ⭐ **MR4 of the description programme** — see ⭐⭐ CURRENT. This is the live task.
1. **Team names**: finish the ~15 unverified Pool 1 teams, then decide whether to go beyond Pool 1.
   Separately, investigate the player-name truncation. Detail in ⛔ TEAM NAMES above.
2. **Decide `nav.json`'s fate** — zero frontend consumers since `!80`. Either give it one or delete
   `build_nav`/`fetch_nav`/the `--entities nav` branch, which then unblocks deleting the
   `display_group` seed column (#57). ⚠ Check no CI job or runbook invokes `--entities nav` first —
   `.gitlab-ci.yml` currently asks only for `teams,fixtures`. ⚠ `display_group` itself is NOT
   deletable on its own: `mart_competition_index.sql:90-91` reads its blank-ness as the browsable
   gate, so that signal needs a replacement first.
2b. **A trending-doc-rot pass.** Several docs describe the "trending" block as if it exists; it was
   cut 2026-08-08. Two were fixed in `!80`; `09_chrome.md` §4/§10 is the known remainder. Use the
   SEMANTIC sweep, not a word search.
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
10. Mine, on GitLab: **#64** #63's residuals · **#67** the contract gate enforces on Edit only, so
   `sed -i` bypasses it · **#68** the form-window CODE diverges from `metrics_context_model.md` §4
   (⚠ the agreement is the authority; never fix by editing the doc) · **#60** `.venv` is not where
   `CLAUDE.md` implies · **#70** scan-budget guard · **#71** the duplication mechanism.

## OPEN — the CPO's alone
Imprint operator + address (#799) · hosting recurring run · feedback Apps Script (#687) · **#81**
duplicate-club alias · #875 · #895 slim-vs-drop · #21.

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
- **v2 built:** design system + 28 components (measured), fixture page, team page (3 tabs), home
  page (next matches ONLY since the browse drop; ordering shared with the competitions page),
  competitions index page, page-spec + SEO contract, per-locale metric labels.
- ⚠ MEASURE test/model counts, never predict (#904) — none pasted here stale.
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). Reselling
  API-Football data is the one hard prohibition.
