# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-20**. **main `dc6d7eb`**. Merged today: `!82`-`!86` — MR1-MR4 of the
description-drift programme plus its handover. **MR5 is OPEN on
`feat/description-hygiene-gate`.** Merged 08-19: team_name_overrides batches 1+2,
the Top teams ruling record, the Browse drop (`!80`). Product **Matchday Pilot**; **GITLAB**
(`glab`, MRs); runner `ci-runner-01`, ZERO GitLab minutes.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding
on `attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ CURRENT — description-drift programme: MR1-MR5 done, MR6 is LAST (2026-08-20)

⭐ **THE PLAN IS APPROVED AND WRITTEN DOWN. Read `.claude/task/escalations.log`'s 2026-08-20
entries FIRST** — the CPO's diagnosis verbatim, the audit's numbers, the definition of a good
description, the rulings, and the six-MR split with its ordering constraints. Plan file:
`C:\Users\Rami\.claude\plans\jazzy-greeting-teacup.md`. **Do not re-scope or re-audit any of it.**

**WHY.** `description:` fields were used as a decision log. An audit measured 616 descriptions
across 19 files; 5 files held 83% of the bad text; three were provably FALSE. Root cause: they
have **no reader** — `persist_docs` absent, docs site never generated — so the field had no
feedback loop and became the cheapest dumping ground.

| MR | What | State |
|---|---|---|
| 1 | 3 false claims + rewrite `engineering_standards.md` §2 | ✅ `!82` |
| 2 | docs blocks for the 8 repeated columns | ✅ `!83` |
| 3 | clean `5_marts/shared/shared.yml` + `seeds/schema.yml` | ✅ `!85` |
| 4 | clean `core.yml`, `base.yml`, `int_momentum.yml` | ✅ `!86` |
| 5 | `check_description_hygiene.py` + tests + wiring | ✅ open, awaiting merge |
| **6** | **`persist_docs` + `dbt docs generate`** | **← LAST** |

⚠ **ORDERING IS LOAD-BEARING.** MR5 after 3-4, so the gate is green on day one (`check_copy_gate.py`
precedent). MR6 after 3-4 because **BigQuery rejects column descriptions over 1,024 chars and 15
currently exceed it** — enabling `persist_docs` first BREAKS the nightly build.

**MR6 concretely, and it is the one that can BREAK PROD.** Turn on `+persist_docs: {relation: true,
columns: true}` in `dbt_project.yml` and publish `dbt docs generate` from CI. That finally gives
descriptions a reader, which is the root cause the whole programme was about.
⚠ There is **NO `seeds:` block** in `dbt_project.yml` — one must be added, and seeds were the worst
offender. ⚠ BigQuery hard-rejects a column description over 1,024 chars; the gate holds everything
at 600, so verify that still holds before enabling. Test on a **dev target only**
(`dbt run --select competition_types`, then `bq show --schema`); never `dbt build` against prod.

✅ **THE GATE IS LIVE (MR5).** `check_description_hygiene.py`, 6 rules, wired in CI AND in
`stop_gate.py`'s FAST_GATES — CPO approved both ("do both"), logged in `escalations.log`.
618 descriptions pass; 21 tests, one per banned class. **Seen RED on real content, then restored.**
⚠ Its rules match ANNOTATION forms, not plain verbs, deliberately and measurably: a
case-insensitive `CORRECTED` hits six legitimate "the country corrections from the seed" uses. A
rule that fires on correct text gets weakened, not obeyed.

⛔ **SIX TRAPS, every one hit for real in MR1-MR5. Do not re-learn them.**
1. **A too-narrow grep reported as a clean sweep.** "partition key" is FALSE — zero models declare
   `partition_by`/`cluster_by`. MR3 cleared the 4 in `5_marts/shared/`; a WIDER sweep found **6
   more** (5 docs + `.claude/hooks/dbt_layer_gate.py:72`, which re-teaches it as PreToolUse
   context on **every mart edit**). That is **#79**, and it needs `protected_override`.
1b. **A KEYWORD SCAN IS BLIND TO A FALSE CLAIM THAT USES NO KEYWORD.** Three `base.yml`
   descriptions claimed "explicit ref() per competition staging" — the pattern the repo FORBIDS —
   with no ref, date or emoji and under 600 chars. Found by READING the SQL, not scanning.
2. **A bulk-edit script that reported success while matching nothing.** Any such script must assert
   it found work (`if seen == 0: return 1`) or it silently no-ops and looks green.
3. **A shared docs block that is wrong at some call sites.** `dbt parse` cannot catch it — read
   every call site.
4. **Verify a reviewer finding, then act.** One MR2 finding was a false positive; both MR3
   findings were real and one was a lie I had just written. Check the code either way.
5. **`--review-patch` writes to STDOUT.** Without `> .claude/task/review_input.patch` the patch is
   silently the PREVIOUS task's and looks plausible — check its `diff --git` list against
   `git status`. Relatedly `origin/main` is the DORMANT GitHub remote, commits behind, so
   `merge-base HEAD origin/main` gives a stale base; use `main`/`gitlab/main`.

⛔ **THE STANDING LESSON, from the Browse drop (08-19), confirmed twice more since.** CPO: *"you
spam things all around the repo and then forget to clean up. and then we have contradictions in our
docs and files."* The killer instance used **no instance of the word being swept**, so text search
was structurally blind. **Sweep the CONCEPT semantically — who claims to consume/render/feed the
thing — never the feature's name.** Evidence on GitLab **#71**.

⛔ **TEAM NAMES — the other live thread, paused not finished.** The provider's `team_name` is often
not the display name even when unique. `team_name_overrides` (joined in
`base_apif__teams_global.sql`) fires on completeness OR collision since the CPO's ruling: *"we have
to define the name we use as the single source of truth for what we display."* **97 of ~130 Pool 1
teams (PL/PD/SA/BL1/ED/L1/LP) corrected and merged**, each citing an English Wikipedia URL.
⚠ **Bayern München DELIBERATELY EXCLUDED** — locale preference is never corrected.
**NOT done**: ~15 Pool 1 teams Wikipedia didn't clearly cover; teams outside Pool 1.
**NOT investigated**: the player-name equivalent — `dim_player` has duplicate short-names
("M. Camara" ×33), even in Serie A/UCL. Root cause first. ⚠ Duplicate provider records for ONE
club are a separate, unbuilt mechanism — GitLab **#81**.

✅ **BROWSE — DROPPED AND MERGED (`!80`).** Do not re-propose without a new ruling. Home renders
**next matches ALONE**. KEPT and NOT stale: the struck decision record, and `08_browse.md` + the
competitions index page, both LIVE. ⚠ `build_nav`/`fetch_nav`/`nav.json` NOT removed, now with
**zero frontend consumer** — see NEXT 2.

✅ **TOP TEAMS RULED AND MERGED**: **one team per league**, not pooled (mirrors Top players).
⚠ `top_teams_mock.html` does NOT show this shape — redo before previewing against it. GAP-29's
mart is not started. Detail: `10_home.md` §0, `99_gaps_register.md` GAP-29/31.

## ⭐⭐ THE METHOD, still the standing rule for every page (CPO's own words, do not reword)

*"the exercise is: does the mock consider the underlying mart (or mart gap)."* Per element on a
mock: (1) name the exact MART COLUMN — a seed/registry/catalogue is NOT a source, and reading one
from a page is the same violation as computing in the frontend; (2) no mart column = a GAP,
registered in `99_gaps_register.md` before building; (3) check the mock's OWN rendered numbers
against the spec's words before trusting either.

⭐ **AUTOMATION — NOT built, NOT approved.** A trace script (mock → element-by-element source table
+ gap list) and a staleness checker would mechanize THE METHOD. Ask before building either. **#78**
tracks the next `10_home.md` sweep this would replace.

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
detail and the permanent `!57` kickoff floor are in `escalations.log`.

## ⭐ The ingest cluster
**TWO nightlies:** `data:nightly` on **Cloud Run under #39**; GitLab schedule (4379625) paused ON
PURPOSE. Runbook `deploy/nightly/README.md`.
✅ **#74 FIXED AND MERGED** (`!70`): the nightly image tracks `main` automatically on any push
touching `*data_paths_image`, so hand-redeploying after an ingestion merge is no longer required —
**but the FIRST auto-run since merge is UNVERIFIED; check it fired.** ⚠ **NOT Cloud Build** — its
default identity holds project Editor, an Editor path from ANY unmerged branch. Revoked; builds
in-job with kaniko.
⚠ **OWED: set `deploy-nightly-image` resource_group to `oldest_first`** (Settings → CI/CD, only
after the group exists — first run creates it). Default `unordered` means two near-simultaneous
merges can deploy out of order, pinning the OLDER commit. **Sentinel (`fdp-freshness`) still NOT
repointed** — deliberately separate; repointing it is its own later decision.
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
decision and his** — which entities earn a page, and whether a past season gets a URL or a control.
Counts: players 51,589→154,767; matches 176,235; h2h 51,903; teams 9,669.
**Overview is BUILT but UNCOMMITTED** in stash `feat/player-overview-tab`; default is known-wrong.

## OWED — deferred
- Guard telemetry absent (#30 finding 4). Delete `macros/apif_latest_source_partition.sql` ·
  mirror crests.
- ⛔ **The contract/Stop gates do NOT understand a MERGE.** Mid-merge every incoming file reads as
  "dirty outside the contract", and the clean-tree rule then blocks editing `contract.md` to
  describe the merge — circular. ⚠ **WORKAROUND, not a fix**: `_gate_bash_pre` skips paths under
  `.claude/task/`, so write `contract.md`/`review.md` via Bash while mid-merge. Needs a real
  `MERGE_HEAD`-aware skip; protected path, own task.
- **#904 IS THE DOMINANT FAILURE** — a claim asserted rather than RUN. A test must be seen RED.
  ⚠ Checks that told me what I wanted: a bulk-edit script matching nothing, a `pytest --timeout`
  run erroring on an unknown flag and exiting 0, and a `--review-patch` that wrote to stdout while
  the stale file stayed put. **Read the output, never the exit code.**

## NEXT
0. ⭐ **MR5 of the description programme** — see ⭐⭐ CURRENT. This is the live task.
1. **Team names**: finish the ~15 unverified Pool 1 teams, then decide whether to go beyond Pool 1.
   Separately, investigate the player-name truncation. Detail in ⛔ TEAM NAMES above.
2. **Decide `nav.json`'s fate** — zero frontend consumers since `!80`. Give it one, or delete
   `build_nav`/`fetch_nav`/the `--entities nav` branch, which then unblocks deleting the
   `display_group` seed column (#57). ⚠ Check no CI job or runbook invokes `--entities nav` first
   (`.gitlab-ci.yml` asks only for `teams,fixtures`). ⚠ `display_group` is NOT deletable alone:
   `mart_competition_index.sql:90-91` reads its blank-ness as the browsable gate.
2b. **A trending-doc-rot pass.** Several docs describe the "trending" block as if it exists; it was
   cut 2026-08-08. Two fixed in `!80`; `09_chrome.md` §4/§10 remains. SEMANTIC sweep, not a word
   search.
3. ⛔ **TURN ON "Pipelines must succeed"** (Settings → Merge requests) — FALSE since the migration;
   pairs with **#21 Q2** ("the server should enforce it").
4. **#47** (the competition hub) — makes the competitions page's rows real links. Three decisions
   if you touch it: 680px width (not the mock's 1080px), single-select filters, rows inert until
   it ships. Wire `competition_index` into CI's `--entities` list in #47's MR, not before.
5. **Audit stream**: Q2 of #21 · delete 2 dead `~/.claude/hooks/` copies · route/delete
   `seo-expert-reviewer`.
6. **COST, SYSTEMATICALLY** — trigger/cost map first, in a GitLab issue.
7. **#845 + #882 — the CPO's decision.** Unblocks the player page.
8. **Legal/imprint**, then launch.
9. Follow-ups (GITHUB numbers, **bodies UNREACHABLE** — re-derive from code): DE/FI i18n gaps ·
   PROTECTED path editable with no `protected_override` · `Regular Season - 20` the copy gate
   cannot see · blank `competition_type` skipped by all 3 guards.
10. Mine, on GitLab: **#64** #63's residuals · **#67** the contract gate enforces on Edit only, so
   `sed -i` bypasses it · **#68** the form-window CODE diverges from `metrics_context_model.md` §4
   (⚠ the agreement is the authority; never fix by editing the doc) · **#60** `.venv` · **#70**
   scan-budget guard · **#71** the duplication mechanism.

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
  competitions index, page-spec + SEO contract, per-locale metric labels.
- ⚠ MEASURE test/model counts, never predict (#904) — none pasted here stale.
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). Reselling
  API-Football data is the one hard prohibition.
