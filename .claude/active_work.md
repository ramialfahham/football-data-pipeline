# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-09-18**, on `chore/session-end-2026-09-18-b`. **GITLAB** (`glab`, MRs).
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

**GITHUB IS A READ-ONLY MIRROR OF `main` SINCE 2026-09-18** (his ruling; !204, merged, wrote it
into `CLAUDE.md`, `.github/workflows/README.md`, the README and the skills). GitLab pushes `main`
only (push mirror, *Mirror only protected branches*); Actions are disabled at the repository level
— **the mirror push IS a push to GitHub `main`, and seven workflows trigger on it, so that setting
must never be flipped** (`.github/workflows/README.md` says why). The token is a fine-grained PAT
in GitLab's mirror settings, **his, expires 2026-12-17**; its replacement needs **Contents AND
Workflows read/write** — without Workflows, GitHub rejects the push because `.github/workflows/
README.md` counts as a workflow (cost one round on setup). `origin` is now reachable and equals
GitLab's `main` after each sync; still never the base and never pushed to. **Open, his:** the README
CI badge — the two dead GitHub Actions badges are gone; a live GitLab badge 404s to visitors
because pipelines are members-only (`public_jobs: false`), so it is "make pipelines public" or a
static badge; put to him in chat 2026-09-18, unanswered. Also unfiled: `docs/operations_guide.md`
and `docs/development_workflow.md:62` still describe GitHub Actions as live CI (a runbook rewrite).

**#153, THE DESIGN-SYSTEM MECHANISM, IS DONE AND MERGED** (!195, !196, !198): the block standard
`docs/wireframes/block_standard.md`, `system.css`, the lint `scripts/check_page_css.py`, the
measured check `scripts/check_design_inventory.py`, `validate:ui` running all three on every MR.
**#150/#151 do not merge until the check passes on their pages and on Home.** ⚠ The commit gate
runs from the project root: a `git worktree` commit is judged against the MAIN tree's index —
rebind a sibling branch from the main tree, stashing by explicit path.

**#109, THE DBT TESTING STRATEGY, IS TWO STEPS OF THREE DONE — NEXT = STEP 3, in a fresh chat.**
Step 1 (!201, merged): the connective rules in `dbt_project/docs/engineering_standards.md` §3.1–3.5
(the column class decides the tests; a rate is one definition gated by its inputs, a range test on
every rate, the guard generated from the catalogue; severity by one question, "would a fan see a
wrong number"; `store_failures` on every singular test; what holds each rule). The census behind
them is a comment on #109. Step 2 (!202, merged): the two rate guards in `dbt_project/tests/
assert_*_rates_inputs_covered.sql`, generated at run time from `metric_catalogue.csv`, the first
tests with `store_failures`; every rate gated on the coverage count of each of its inputs (about
1,200 form windows and 1,500 team-seasons went to "—", correctly). The nightly of
2026-09-18 had failed on `shots_on_goal_pct` > 1 — that gate is fixed: **check that the nightly of
2026-09-19 (04:00 UTC, the first after !202) is green BEFORE starting step 3** — it had not run
when the 2026-09-18 session ended. **Step 3, the plan is §3.5 and the census:** `store_failures`
on the other 49 singular tests; a range test on the 92 rates without one; the severity audit of
the 941 `error` tests under §3.3; the three remaining mechanisms — every listed column described
(365 undescribed today; a rule to add to `check_description_hygiene.py`), a yml-vs-projection
check, a `relationships` sweep of the `_sk` columns. Plan mode; contract first; the warehouse
reviewer routes on `dbt_project/**`.

**One default still open, merged as a default:** the breadcrumb's current-page colour keeps the
site's (the page you are on `ink-2`, links muted; the mocks had it inverted); its inventory row is
`proposed` — measured, never fails — until he rules. The 2026-09-17 rulings (the two heading
lines, the table's head rule only, the DE tab label "Rankings") are written into #129. ⚠ **A ruling
request is ONE question, then a 2×2 table (page × variant → file), then the recommendation** —
four files with a caption got "What am I supposed to decide?"; his answer may split by context.

**THE COMPETITION PAGE IS FULLY APPROVED ON #129 (2026-09-16); he will NOT re-check pages by eye.**
#129's `The approved design` is the text: three tabs, Overview · Matchdays · Rankings. **Build
issues, gated on #153:** **#150** Matchdays · **#151** Rankings + the Overview rework · **#152**
metric groups; Home's corrections on **#127**. The page-wide rules live in the block standard and
`system.css`, measured — the builds compose from them and add nothing of their own.

**The measured check is the arbiter now.** `python scripts/check_design_inventory.py --dist
site_v2/dist` (build first; park any untracked export payload under `site_v2/src/data/` or the
SEO audit refuses the build); `--no-built` for the mocks alone. An element not in
`block_standard.md` is a design decision: put to him and rendered on every page it touches before
it is ruled. `gen_competitions.py` (#54's index) is off the pages list until it runs against
today's registry.

**HOME IS DONE (#127, `!187`) and THE COMPETITIONS HUB (#128, `!189`).** Go-live items (About,
Imprint) have no issue — his call. **The roadmap is the GitLab milestones in the site's menu
order: Home · Competitions · Matches · Teams · Players · Standings · Leaderboards** — one review
issue per page (#127–#140), approved on the issue before anything is built; after #153 and the
competition builds comes the Matches milestone (#130, #131, #132); dependencies the page picks up
when they land: #105, #145, #146, #148, #69.

**How we work since 2026-09-11** is `CLAUDE.md` "Which source answers which question" and
`docs/working_agreement.md` §1 / §11: the requirement is the issue (Task template), the plan its
How, a decision is recorded by the thing it changes (`escalations.log` FROZEN), the MR head is his
check and **his merge is the approval** — set the head with `glab mr update <n> --description`
right after the hook opens the MR. **The stop gate blocks a turn ending with anything in
`git stash`**; parked work goes on a pushed `parked/<branch>` (ten exist, half dead).

**Parked, real, not lost:** the built player Overview tab is on `parked/feat/player-overview-tab`
(stash commit; untracked files in its third parent — `git stash apply parked/feat/player-overview-tab`)
and carries a KNOWN-WRONG default-season rule (see #118). The four-tab decision (2026-07-27) is
preserved on `archive/docs-handover-player-tabs-and-seo` and recorded in #118.

⛔ **BEFORE TOUCHING ANY METRIC, READ `docs/metric_layer.md`** — where a metric is defined, which
model computes it, what makes it NULL, what CI fails you on. A metric is NULL unless its inputs
cover every match in the window; a thinly covered competition showing blank is correct output.

⚠ **THE VOLUME IS THE PROBLEM** (*"A wallpaper of text"*; *"Explain like I'm twelve. Keep it
short."*). The decision and the consequence, two sentences; process detail stays in the repo.
Commit, push, retry, rebase and regenerate WITHOUT asking; keep working.

⚠ **THE NIGHTLY WAS RED ON 2026-09-17 AND 2026-09-18, both handled** (a stale `2H` fixture that
cleared itself; `shots_on_goal_pct` > 1 from a one-input provider payload, fixed by !202). A red
nightly with `severity: error` skips every dependent mart, and an MR's
`data:build:mr` then fails the singular tests it defers to prod — retry them after a green
nightly, do not chase them in the MR.

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
and says he did not rule on the cap. Keep rounds down by checking a claim before asserting it.
⚠ **Never ask him to approve routine mechanics** — ask about the RULE.

## ⛔ PARKED: the dbt profile MR — TWO OPEN FAILS

Branch `fix/dbt-profile-local-to-this-repo`; WIP on `parked/fix/dbt-profile-local-to-this-repo--profile-root`.
The repo-local `profiles.yml` at the ROOT is the fix (dbt reads `--profiles-dir` → `DBT_PROFILES_DIR`
→ **CWD** → `~/.dbt`; every CI job does `cd dbt_project`). Open: (1) a stale `decisions_taken`
paragraph saying `dbt_project/`; (2) **`.mcp.json` sets `DBT_PROFILES_DIR: C:/Users/Rami/.dbt`**, a
PROTECTED path that outranks the fix. **No `prod` target** in the local profile, ever (it is the
line that overwrites prod's base tables). `dbt ls` / `parse` / `compile` work with a throwaway
profile in the scratchpad (target `dev_scratch`); `~/.dbt/profiles.yml` is ANOTHER project's.

## ⛔ OPEN — DEFECTS TO FIX (not decisions to wait on)

  - **#110 — a forfeit the provider labels `FT`** with a score and no stat line, so 18 of 19 Süper
    Lig 2022 team-seasons are blank. The other 435 blanked team-seasons are CORRECT (measured: of
    9,515 fixtures with no team statistics, ZERO have any in the raw payload). The fix needs a
    competition-relative signal, not a blanket rule. Everything measured is on the issue.
  - **#111 — no test compares a metric to its own formula.** The catalogue publishes
    `base_relation` + `numerator_expr` + `denominator_expr`; the models compute the same metric in
    SQL; nothing checks they agree. `assert_metric_catalogue_expr_resolvable` parses and binds
    those expressions — it never evaluates them. No dbt unit tests exist either.
  - **#109** — no end-to-end dbt test strategy, and no rule for when a NULL is a defect rather than
    the honest answer. Filed at his instruction; #111 is one concrete piece of it.
  - **#108** — rounding is business logic and `DeservedHero.astro:79` does it in the browser.
  - **The mid-season deserved-vs-actual line and its start matchday** — both open, and they gate
    showing that hero on live data.
  - **`fix/raw-players-row-chunking` is UNMERGED and its mechanism is ABSENT from main.** Commit
    `1f822a2` chunks the `RAW_APIF_PLAYERS` snapshot under BigQuery's 100MB per-row limit (UEL
    81.8MB / UCL 78.7MB when written). Settle superseded-or-abandoned before those rosters grow.
  - **#101** carries its season trap on the issue now (recorded 2026-09-13).
  - **#99 / #102 / #96 / #98** — export board keys pinned by no test; `mart_leaderboards` is
    player-only under an unprefixed name; no offline gate checks `accepted_values`.

## ⛔ WHAT ACTUALLY FINDS DEFECTS — the blinded review and CI, almost never a gate

Across `!156`–`!159`, `!191`, `!195`–`!198` every FAIL came from a reviewer or the pipeline; the
offline gates were green over all of them. **Almost every defect was a claim asserted without
opening the file** — open it. Sweep the RIGHT tree, two-sided; mutation-test against the mutation
the design is defended against (`!195` round 2); a row marked ruled while a note says "put to him"
is a decision taken (`!196` round 1); Windows green, Linux red: an unsorted listing (`!195`), a
package the workstation has and the job's image does not (`!198`) — both found by CI.

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
