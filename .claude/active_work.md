# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-21**. **main `2ef94e8`**. #84 + its fix MERGED. **#82 MR1 OPEN as `!91`.**
Product **Matchday Pilot**; **GITLAB** (`glab`, MRs); runner `ci-runner-01`, ZERO GitLab minutes.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding
on `attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ CURRENT — **#82 coverage: MR1 OPEN as `!91` (green), MRs 2-5 to go** (2026-08-21)

⭐ **READ `escalations.log`'s 08-20 and 08-21 entries FIRST** — the CPO's diagnosis, the numbers,
every ruling, each MR's defects. **Do not re-scope or re-audit any of it.**

Description programme `!82`-`!89` ALL MERGED and verified in prod. #82 is the follow-on.
**`!91` = MR1**: the 12 object-level gaps (11 of 11 SOURCE TABLES + `int_team__market_value_latest`,
which was in NO yml) plus a presence rule in the gate. Plan `cozy-orbiting-quail.md`.

⛔ **A TOO-LONG DESCRIPTION BREAKS PROD.** `persist_docs` is on for all 97 models + 9 seeds.
Bracketed live: **1,024** chars/column, **16,384**/relation; one over = HTTP 400, NOT swallowed, so
the model FAILS. Headroom: column 588, relation 601. `data:build:main` publishes **`catalog.json`**
plus the docs page. ⚠ `seeds:` is persist_docs-ONLY: a `+schema` there relocates all 9.
⚠ **A SPLIT-MERGED OR REBASED BRANCH FAILS F11 and it is NOT a stale artifact** — the merge-base
MOVES so the diff shrinks. Fix is the one-value `review.md` rebind: NO re-review owed.

✅ **THE GATE** (`check_description_hygiene.py`) runs in CI and `stop_gate.py`'s FAST_GATES: 6
content rules **plus object-level coverage as of `!91`**. ⚠ Rules match ANNOTATION forms, not plain
verbs: bare `ruled` hits "goal ruled out for offside". A rule firing on correct text gets weakened.

⛔ **#82's HEADLINE NUMBER IS WRONG.** It says 262 columns lack a description; that counted only
columns already in a yml. **1,694 EXIST** in core/int/marts, **974 declared NOWHERE**. True gap
1,236, but names repeat: 500 distinct, 251 defined, so the job is **249 definitions**.
**MRs 2-5:** declare the 974 · wire blocks + enforce · write the 249 (highest reach first) · turn
column presence on.
⛔ **THE PROVIDER SENDS NO DESCRIPTIONS — CHECKED.** Stats arrive as a label and a number
(`$.type` = "Total Shots"). All 249 are OURS to author. Coverage is uneven (xG on 57% of fixtures)
and 6 stat types appear on 4-78 rows of ~98,000. For ambiguous ones (`passes_total` attempted or
completed?) derive from our own fixtures and state it as ours.
⚠ **CPO RULINGS 08-21:** "every column, no exception" (staging+base OUT) · no thin filler · docs
blocks kept **only with a mechanism enforcing them** (hand-wiring failed 112×) · **NO osmosis**.
⛔ **INHERITING UPSTREAM PROSE CARRIES AN INHERITED ERROR.** MR1 shipped a FALSE description
("the newest is the fullest" for retried fixtures) by compressing staging prose without reading the
contract section governing it. **GRAIN claims are safe to inherit; BEHAVIOUR-ACROSS-VERSIONS claims
are not** and must be traced to the base dedup logic. Governs MRs 2-5.
⛔ **THE LOG LIED ABOUT HIM AND HE CAUGHT IT.** It claimed he "explicitly" rejected osmosis; his
answer was two words. **Record the OPTION chosen and nothing else.**

⛔ **#83 — COMPETITION CLASSIFICATION HAS NO CORE DIM.** `competition_type`/`entity_type` live only
in seeds (`dim_league.league_type` is the PROVIDER's, not ours), so 12 models join the seed direct
— incl. the two `int_legs__*` underlying 68 of 80 metrics. ⚠ **SEEDS ARE SOURCES, settled, and dbt
agrees.** The defect is LAYERING: consume a seed ONCE at base/core, publish a dim. ⚠ The registry
is NOT ingestion-only — it carries both, and the sync already projects only the product half.

⛔ **SEVEN TRAPS, every one hit for real. Do not re-learn them.**
1. **A too-narrow grep reported as a clean sweep.** Hit AGAIN on `!91` (I "found" a data-contract
   gap by grepping one table's rows). "partition key" is FALSE; 6 survivors = **#79**.
1b. **A KEYWORD SCAN IS BLIND TO A CLAIM USING NO KEYWORD.** Three `base.yml` descriptions claimed
   the FORBIDDEN "explicit ref() per competition staging" with no ref, date or emoji. Found by
   READING the SQL. Corollary: a grep also matches the DOCUMENTATION of a defect as the defect.
2. **A bulk-edit script reporting success while matching nothing.** Assert it found work.
3. **A shared docs block wrong at some call sites.** `dbt parse` cannot catch it.
4. **Verify a reviewer finding, then act** — both directions. Some are false positives; one was a
   lie I had just written.
5. **`--review-patch` writes to STDOUT**, so without redirect the patch is silently the PREVIOUS
   task's. Check its `diff --git` list. `origin/main` is the DORMANT GitHub remote — use `gitlab`.
6. ⛔ **NEVER WRITE A REVIEWER'S VERDICT YOURSELF.** MR5 recorded PASS for two who returned FAIL.
   Send the round-2 confirm and WAIT. ⚠ Never edit any file while the suite runs.

⛔ **THE STANDING LESSON (Browse drop, confirmed repeatedly).** CPO: *"you spam things all around
the repo and then forget to clean up. and then we have contradictions in our docs and files."* The
killer instance used **no instance of the word being swept**. **Sweep the CONCEPT semantically —
who claims to consume/render/feed the thing — never the feature's name.** Evidence: **#71**.

⛔ **TEAM NAMES — the other live thread, paused not finished.** The provider's `team_name` is often
not the display name even when unique. `team_name_overrides` (joined in
`base_apif__teams_global.sql`) fires on completeness OR collision: *"we have to define the name we
use as the single source of truth for what we display."* **97 of ~130 Pool 1 teams corrected**,
each citing an English Wikipedia URL. ⚠ **Bayern München DELIBERATELY EXCLUDED** — locale
preference is never corrected. **NOT done**: ~15 Pool 1 teams Wikipedia didn't cover; teams outside
Pool 1. **NOT investigated**: the player-name equivalent, `dim_player` has duplicate short-names
("M. Camara" ×33). ⚠ Duplicate provider records for ONE club are separate and unbuilt — **#81**.

✅ **BROWSE — DROPPED (`!80`).** Do not re-propose without a new ruling. Home renders **next
matches ALONE**. NOT stale: the struck record, `08_browse.md` + the competitions page, both LIVE.
⚠ `build_nav`/`fetch_nav`/`nav.json` NOT removed, **zero frontend consumer** — see NEXT 2.

✅ **TOP TEAMS RULED**: **one team per league**, not pooled. ⚠ `top_teams_mock.html` does NOT show
this shape. GAP-29's mart not started. Detail: `10_home.md` §0, `99_gaps_register.md` GAP-29/31.

## ⭐⭐ THE METHOD, standing rule for every page (CPO's own words, do not reword)

*"the exercise is: does the mock consider the underlying mart (or mart gap)."* Per element:
(1) name the exact MART COLUMN — a seed/registry/catalogue is NOT a source, and reading one from a
page is the same violation as computing in the frontend; (2) no mart column = a GAP, registered in
`99_gaps_register.md` BEFORE building; (3) check the mock's OWN rendered numbers against the spec.
⭐ **AUTOMATION (trace script + staleness checker) NOT built, NOT approved.** Ask first. **#78**.

⚠ **STANDING RULE: the handover rides in the SAME commit as the code it describes.**

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

## ⭐ #84 — 310 ORPHANED RELATIONS: script MERGED, **nothing dropped yet**
Nothing reconciles the WAREHOUSE (the guard governs only the REPO): 310 orphans sat for 3 months.
**250 broken** · **26 STILL RETURN DATA** (retired SQL, plausible numbers — the hazard) · **34
tables** (42.5 MiB, so cost is NOT the argument). Also 9 `raw.RAW_WC26_APIF_*` nothing writes.
`scripts/cleanup_orphan_relations.py` derives it from the MANIFEST, dry-run default.
⛔ **RUNNING IT WITH `--confirm` IS THE CPO'S, still OWED.** A recurring check is a NEW MECHANISM,
not built.

## ⭐ COST — read **GitLab issue #3** first
**#3 holds it all.** ⚠ **#70** is the scan-budget guard; `require_partition_filter` +
`maximum_bytes_billed` are **NEITHER set**. ⚠ **Spend UNKNOWN** since 08-03. Storage measured only
for #84's orphans; else bytes SCANNED.

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
0. ⭐ **#82 (MR7)** — see ⭐⭐ CURRENT. Needs its `catalog.json`.
1. **Team names**: finish the ~15 unverified Pool 1 teams, then decide whether to go beyond Pool 1.
   Separately, investigate the player-name truncation. Detail in ⛔ TEAM NAMES above.
2. **Decide `nav.json`'s fate** — zero frontend consumers since `!80`. Give it one, or delete
   `build_nav`/`fetch_nav`/the `--entities nav` branch, which then unblocks deleting the
   `display_group` seed column (#57). ⚠ Check no CI job or runbook invokes `--entities nav` first
   (`.gitlab-ci.yml` asks only for `teams,fixtures`). ⚠ `display_group` is NOT deletable alone:
   `mart_competition_index.sql:90-91` reads its blank-ness as the browsable gate.
2b. **A trending-doc-rot pass.** Several docs describe the "trending" block as if it exists; it was
   cut 2026-08-08. Two fixed in `!80`; `09_chrome.md` §4/§10 remains. SEMANTIC sweep.
3. ⛔ **TURN ON "Pipelines must succeed"** (Settings → Merge requests) — FALSE since the migration;
   pairs with **#21 Q2** ("the server should enforce it").
4. **#47** (the competition hub) — makes the competitions page's rows real links. Decisions if you
   touch it: 680px width (not the mock's 1080px), single-select filters, rows inert until it
   ships. Wire `competition_index` into CI's `--entities` list in #47's MR, not before.
5. **Audit stream**: Q2 of #21 · delete 2 dead `~/.claude/hooks/` copies · route/delete
   `seo-expert-reviewer`.
6. **COST, SYSTEMATICALLY** — trigger/cost map first, in a GitLab issue.
7. **#845 + #882 — the CPO's decision.** Unblocks the player page.
8. **Legal/imprint**, then launch.
9. Follow-ups (GITHUB numbers, **bodies UNREACHABLE** — re-derive from code): DE/FI i18n gaps ·
   PROTECTED path editable with no `protected_override` · `Regular Season - 20` the copy gate
   cannot see · blank `competition_type` skipped by all 3 guards (see **#83**).
10. Mine, on GitLab: **#64** #63's residuals · **#67** the contract gate enforces on Edit only, so
   `sed -i` bypasses it · **#68** the form-window CODE diverges from `metrics_context_model.md` §4
   (⚠ the agreement is the authority; never fix by editing the doc) · **#60** `.venv` · **#70**
   scan-budget guard · **#71** the duplication mechanism.

## OPEN — the CPO's alone
Imprint operator + address (#799) · hosting recurring run · feedback Apps Script (#687) · **#81**
duplicate-club alias · #875 · #895 slim-vs-drop · #21 · **#82**'s "business-facing" definition.

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
  page (next matches ONLY since the browse drop; ordering shared with competitions), competitions
  index, page-spec + SEO contract, per-locale metric labels.
- ⚠ MEASURE test/model counts, never predict (#904) — none pasted here stale.
- ⚠️ `appearances` = played legs, not squad selections. No player photos (CPO). Reselling
  API-Football data is the one hard prohibition.
