# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-09-19**, on `feat/109-store-failures-and-severity`. **GITLAB** (`glab`, MRs).
⚠ No SHA here on purpose: this file merges as a commit, so any hash it named would be its own parent
and wrong on arrival. Run `git log -1` and `glab mr list`; they are correct and this file cannot be._

⛔ **THE POST-COMMIT HOOK PUSHES TO `main` IF THE BRANCH TRACKS `main`.**
`git checkout -b <branch> gitlab/main` sets `main` as upstream. **Run `git branch --unset-upstream`
right after creating a branch**, and push with `git push gitlab <b>:<b>`, verifying `-> <b>`.
⛔⛔ **DO NOT TOUCH `glab auth` OR INSTALL A PROJECT TOKEN. 2026-09-03 cost a full day.** ONE
credential per MACHINE — re-authing it broke two other repos. The safeguard that the agent never
merges is **branch protection** plus the memory rule **never merge**; NOT a token, NOT a hook.
⛔ `fix/merge-guard-covers-the-api` IS DEAD (discarded as over-engineering). ⛔⛔ **CI HAS NO
FALLBACK:** `ci-runner-01` is the ONLY runner — a dead box means pipelines QUEUE. `~/.ssh/id_ed25519`
is PASSPHRASE-PROTECTED, so `ssh -o BatchMode=yes` fails `publickey` — not a broken key.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`.

## ⛔ WHERE WE ARE

**#109 STEP 3 IS IN FLIGHT: THE PLAN (FOUR MRs, A–D) IS ON THE ISSUE, APPROVED 2026-09-19; MR A IS
OPEN AS !211; NEXT = MR B, in a fresh chat, plan mode, contract first** (the four MRs are below
under #109). **#150 is merged** (!209, 2026-09-19; the 2026-09-19 nightly green). !209's rulings,
recorded in its contract: **the match slug comes from the warehouse**; **played rows are inert
until the match report page exists**; the EN/DE/FI copy shipped as drafted, his merge the ruling.
Until the next `deploy:export` (manual, still `teams,fixtures`) production shows the committed
sample, as it does for Home. **#150 is not blocked on #155.** **#156** (filed 2026-09-19 at his
word): the nightly export, build and deploy from live data, the go-live item that ends the committed
sample; its export-and-build half is worth running before go-live, since full-scale defects (#155)
show only there.

**#155 (filed 2026-09-19, Matches milestone): two unplayed meetings of the same clubs share the
match preview page's title**, 12 pairings × 3 locales; the full-scale build (15,078 match pages,
8 GB heap, 14 min) fails `audit-seo` on exactly that and nothing else; #150's `check-built-pages`
(match pages = payloads × locales = the warehouse's unplayed count) found it. The title's wording
is his; the fix is the fixture page's title template.

**What #150 left behind:** `mart_competition_fixtures` (`fixture_slug`, `fixture_order`,
`is_next_round` from mart_next_matchday) is the mart #131 reads by date; the shared row is
`site_v2/src/components/ui/MatchRow.astro` (`linkPlayed` flips when #132's report page lands;
Home's `FixtureRow.astro` still has its own markup — converge under #131); the sample carries all
279 unplayed Bundesliga payloads (`.gitignore` range 1575167–1575445; move its start as matchdays
are played, refresh with `competitions/BL1/2026.json`).

**GITHUB IS A READ-ONLY MIRROR OF `main` SINCE 2026-09-18** (his ruling; `CLAUDE.md`'s mirror
bullet is the durable text, including what the token's renewal needs). **Actions are disabled at
the repository level and that setting is never flipped** (`.github/workflows/README.md` says why).
`origin` equals GitLab's `main` after each sync; still never the base, never pushed to. Pipelines
stay members-only (his call), so the README carries a static `CI · GitLab` badge. The runbook
rewrite (operations guide and development workflow still describe GitHub Actions as live CI) is
**#154**, unscheduled.

**#153, THE DESIGN-SYSTEM MECHANISM, IS DONE AND MERGED** (!195, !196, !198): the block standard,
`system.css`, the lint, the measured check, `validate:ui` running all three on every MR.
**#151 does not merge until the check passes on its pages and on Home** (!209 did).

**#109, THE DBT TESTING STRATEGY: steps 1 and 2 merged, step 3 in flight.** Step 1 (!201): the
rules, `engineering_standards.md` §3.1–3.5. Step 2 (!202): the two catalogue-generated rate guards
`dbt_project/tests/assert_*_rates_inputs_covered.sql`. **Step 3 is four MRs, the text on #109
("Step 3 — the mechanisms and the sweep"), each its own contract, the warehouse reviewer on
`dbt_project/**`, platform on `scripts/**`:** **A** (!211, open): `store_failures` on all 54
singular tests, the §3.3 answer per test on its head, 3 flipped to `warn` (the three name-override
tests). **B** (next): a range test on the 104 rate columns without one (`expression_is_true`, the
form of the 72 existing; `shots_on_goal_difference_per_match` gets none — no range for a
difference); `relationships` on every foreign-key `_sk` without one (parent by name; 106 `_sk`
lack one, some are the model's own key — orphans measured on prod FIRST; an orphan is a defect or
a `warn` with the cause, never a dropped test; `mart_competition_fixtures.home/away_team_sk` are
two); one test on `int_team__market_value_latest`; `scripts/check_relationships_coverage.py` with
its pytest and a red proof. **C**: the 359 undescribed listed columns (116 names; `league_code` 49,
decided per site between the two blocks; a shared block for a repeated name only after reading every
model it reaches), then the column rule in `check_description_hygiene.py`. **D**:
`scripts/check_yml_vs_projection.py --catalog` (the reverse of `declare_missing_columns.py`) wired
in `data:build:main` after `dbt docs generate` — DECIDED with the plan: post-merge, where the
catalogue is whole — plus the sweep in `validate:governance`; a governance MR (`protected_override`).
B and C each rebuild most of the warehouse in `ci_mr<IID>_*` per pipeline (a description change is
`state:modified` under `persist_docs`) — cents. No census script in the repo; recount before B and C.

**One default still open, merged as a default:** the breadcrumb's current-page colour (`ink-2`,
links muted; the mocks had it inverted); its inventory row is `proposed` until he rules. ⚠ **A
ruling request is ONE question, a 2×2 table (page × variant → file), then the recommendation.**

**THE COMPETITION PAGE IS FULLY APPROVED ON #129 (2026-09-16); he will NOT re-check pages by eye.**
**Build issues:** **#150** Matchdays (merged) · **#151** Rankings + the Overview rework · **#152**
metric groups. The page-wide rules live in the block standard and `system.css`, measured — the
builds compose from them and add nothing of their own.

**The measured check is the arbiter.** `python scripts/check_design_inventory.py --dist
site_v2/dist` (build first; park untracked export payloads under `site_v2/src/data/` or the SEO
audit refuses the build). An element not in `block_standard.md` is a design decision: put to him
and rendered on every page it touches before it is ruled.

**HOME IS DONE (#127, `!187`) and THE COMPETITIONS HUB (#128, `!189`).** Go-live items (About,
Imprint) have no issue — his call. **The roadmap is the GitLab milestones in the site's menu
order: Home · Competitions · Matches · Teams · Players · Standings · Leaderboards** — one review
issue per page (#127–#140), approved on the issue before anything is built; after #153 and the
competition builds comes the Matches milestone (#130, #131, #132); dependencies the page picks up
when they land: #105, #145, #146, #148, #69.

**How we work since 2026-09-11** is `CLAUDE.md` "Which source answers which question" and
`docs/working_agreement.md` §1 / §11: the requirement is the issue, the plan its How, a decision
is recorded by the thing it changes (`escalations.log` FROZEN), the MR head is his check and
**his merge is the approval** — set the head with `glab mr update <n> --description` right after
the hook opens the MR. **The stop gate blocks a turn ending with anything in `git stash`**;
parked work goes on a pushed `parked/<branch>` (ten exist, half dead).

**Parked, real, not lost:** the built player Overview tab is on `parked/feat/player-overview-tab`
(`git stash apply` it; a KNOWN-WRONG default-season rule, see #118); the four-tab decision is on
`archive/docs-handover-player-tabs-and-seo` and recorded in #118.

⛔ **BEFORE TOUCHING ANY METRIC, READ `docs/metric_layer.md`.** A metric is NULL unless its
inputs cover every match in the window; a thinly covered competition showing blank is correct.

⚠ **THE VOLUME IS THE PROBLEM** (*"A wallpaper of text"*; *"Explain like I'm twelve. Keep it
short."*). The decision and the consequence, two sentences. Commit, push, retry, rebase and
regenerate WITHOUT asking; keep working.

⚠ **A red nightly skips every dependent mart, and an MR's `data:build:mr` then fails the singular
tests it defers to prod — retry after a green nightly** (09-17 and 09-18 were red, both handled).

## ⛔ WHAT 2026-09-08 CHANGED IN PROD — read before trusting an older measurement

Awarded results count as played; the override seed is `fixture_team_id_overrides` for all three
fixture-level feeds; the freshness guard ignores `SUSP`/`INT`.
`assert_team_season_games_not_short_of_standings` is WARN and RED on 3 rows by design (#110 plus
Al Wehda AFCCL 2021). **Prod is correct.**

⛔⛔ **A CORRECTION IN BASE DOES NOT REACH AN INCREMENTAL FACT** (`fct_fixture_event`,
`fct_fixture_player_stats`, `fct_fixture_team_stats`): a merge inserts the corrected row and
strands the old one. **The fix is a one-off `dbt build --full-refresh --select <facts>`, his to
run**, checked lossless first — on 2026-09-08 `fct_fixture_event` held 17 rows base no longer
emits. Compiling a model read-only against prod measures the LOGIC, never the TABLE's contents.

## ⛔ THE ROUND CAP (3) — the override practice, settled by use, never ruled

Past the cap, write a `rounds_cap_override:` in `review.md` that clears a standing FAIL BY REVIEW
and says he did not rule on the cap. Check a claim before asserting it.
⚠ **Never ask him to approve routine mechanics** — ask about the RULE.

## ⛔ PARKED: the dbt profile MR — TWO OPEN FAILS

Branch `fix/dbt-profile-local-to-this-repo`; WIP on `parked/fix/dbt-profile-local-to-this-repo--profile-root`.
The repo-local `profiles.yml` at the ROOT is the fix (dbt reads `--profiles-dir` → `DBT_PROFILES_DIR`
→ **CWD** → `~/.dbt`; every CI job does `cd dbt_project`). Open: (1) a stale `decisions_taken`
paragraph saying `dbt_project/`; (2) **`.mcp.json` sets `DBT_PROFILES_DIR: C:/Users/Rami/.dbt`**, a
PROTECTED path that outranks the fix. **No `prod` target** in the local profile, ever (it is the
line that overwrites prod's base tables). `dbt ls` / `parse` work with a throwaway profile in the
scratchpad (target `dev_scratch`); `~/.dbt/profiles.yml` is ANOTHER project's.

## ⛔ OPEN — DEFECTS TO FIX (not decisions to wait on)

  - **#110 — a forfeit the provider labels `FT`** with a score and no stat line, so 18 of 19 Süper
    Lig 2022 team-seasons are blank. The other 435 blanked team-seasons are CORRECT (measured: of
    9,515 fixtures with no team statistics, ZERO have any in the raw payload). The fix needs a
    competition-relative signal, not a blanket rule. Everything measured is on the issue.
  - **#111 — no test compares a metric to its own formula.** The catalogue publishes
    `base_relation` + `numerator_expr` + `denominator_expr`; the models compute the same metric in
    SQL; nothing checks they agree. `assert_metric_catalogue_expr_resolvable` parses and binds
    those expressions — it never evaluates them. No dbt unit tests exist either.
  - **#108** — rounding is business logic and `DeservedHero.astro:79` does it in the browser.
  - **The mid-season deserved-vs-actual line and its start matchday** — both open, and they gate
    showing that hero on live data.
  - **`fix/raw-players-row-chunking` is UNMERGED and its mechanism is ABSENT from main.** Commit
    `1f822a2` chunks the `RAW_APIF_PLAYERS` snapshot under BigQuery's 100MB per-row limit (UEL
    81.8MB / UCL 78.7MB when written). Settle it before those rosters grow.
  - **#101** carries its season trap on the issue now (recorded 2026-09-13).
  - **#99 / #102 / #96 / #98** — export board keys pinned by no test; `mart_leaderboards` is
    player-only under an unprefixed name; no offline gate checks `accepted_values`.

## ⛔ WHAT ACTUALLY FINDS DEFECTS — the blinded review and CI, almost never a gate

Across `!156`–`!159`, `!191`, `!195`–`!198` every FAIL came from a reviewer or the pipeline; the
offline gates were green over all of them. **Almost every defect was a claim asserted without
opening the file** — open it. Sweep the RIGHT tree, two-sided; mutation-test against the mutation
the design is defended against (`!195`); a row marked ruled while a note says "put to him" is a
decision taken (`!196`); Windows green, Linux red: an unsorted listing (`!195`), a package the
workstation has and the job's image does not (`!198`) — both found by CI.

## ⛔ TRAPS THAT COST REAL TIME

⛔⛔ **A REBASE CONFLICT CAN BE diff3, WHICH HAS FOUR MARKER KINDS** — `|||||||` too. `git add`
marks a file resolved WITHOUT reading it, and every gate and CI passed with a marker committed.
**Grep all four**, and prove a union structurally (`diff -q` each side against the resolved
head/tail; check the lengths sum).
⚠ **On a sibling-MR rebase the CODE merges cleanly and the PAPERWORK collides** — `contract.md`
and `review.md` are per-task and one side wins; regenerate and re-review.
⛔⛔ **"MERGED" IS A CLAIM TO VERIFY, and `--is-ancestor` IS NOT THE CHECK** — it called 20 of 22
landed branches unmerged. Use `git cherry gitlab/main <branch>` (`+` = not upstream). Deleting an
open MR's source branch CLOSES the MR. ⚠ A stacked branch that reverts its base's change shows
NO hunk in the cumulative patch vs `main` — give reviewers the diff vs the parent commit too.
⚠ **`git pull` on main pulls the GitHub MIRROR (`origin`), which lags GitLab by a sync.** Use `git pull --ff-only gitlab main`.
⚠ **The push guard refuses EVERY push while standing on main.** Branch to a throwaway to push
deletions. It reads the CURRENT branch, so `checkout && push` in one call is blocked as a whole.
⛔⛔ **`--review-patch` PRINTS; only a REDIRECT writes the file.** Run bare it leaves the previous
round's patch on disk, exit 0 (stale diffs served on `!132`, `!151`, `!156`). **Regenerate it
immediately before every round, after `git add -u`.**
⭐ Free tell: `--staged-hash` printing `e3b0c442…` = `sha256("")`, an empty staged diff.
⚠ **CP1252, NOT UTF-8, IN BOTH DIRECTIONS on this machine.** `subprocess.run(..., text=True)` and the
`bq` CLI's CSV output are both cp1252. Capture BYTES, decode utf-8 first with a cp1252 fallback.
⚠ **SQLFluff exits 1 ON SUCCESS when stdout is redirected** (emoji + CP1252). Read exit codes
bare, or set `PYTHONIOENCODING=utf-8`.

## Method that works

Contract FIRST on a clean tree (stash by explicit path with a `TEMP-` label; after the edit
`git stash pop` REFUSES because the stash carries the pre-edit contract — restore with
`git checkout stash@{0} -- <paths>` then `git stash drop`, inside the same turn). Then gates with
exit codes read bare, mutations watched RED, blinded reviewers, `review.md` with `--staged-hash`.
Rounds are PER REVIEWER; each section `## <exact-routing-key>`, `VERDICT:`, `risks_checked:`.
⚠ **`contract.md` is INSIDE the review hash**; amend BEFORE the round.
⚠ `acceptance_evidence.md` needs `criteria_demonstrated:` at **column 0** — `## criteria_demonstrated:`
is invisible to the parser — with one 15+ character bullet per criterion.
