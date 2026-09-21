# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-09-21**, on `feat/109-projection-check-wired`. **GITLAB** (`glab`, MRs).
⚠ No SHA here on purpose: this file merges as a commit, so any hash it named would be its own parent
and wrong on arrival. Run `git log -1` and `glab mr list`; they are correct and this file cannot be._

⛔ **THE POST-COMMIT HOOK PUSHES TO `main` IF THE BRANCH TRACKS `main`.**
`git checkout -b <branch> gitlab/main` sets `main` as upstream. **Run `git branch --unset-upstream`
right after creating a branch**, and push with `git push gitlab <b>:<b>`, verifying `-> <b>`.
⛔⛔ **DO NOT TOUCH `glab auth` OR INSTALL A PROJECT TOKEN. 2026-09-03 cost a full day.** ONE
credential per MACHINE — re-authing it broke two other repos. The safeguard that the agent never
merges is **branch protection** plus the memory rule **never merge**; NOT a token, NOT a hook.
⛔ `fix/merge-guard-covers-the-api` IS DEAD (over-engineering). ⛔⛔ **CI HAS NO
FALLBACK:** `ci-runner-01` is the ONLY runner — a dead box means pipelines QUEUE. `~/.ssh/id_ed25519`
is PASSPHRASE-PROTECTED, so `ssh -o BatchMode=yes` fails `publickey` — not a broken key.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`.

## ⛔ WHERE WE ARE

**#109 STEP 3: A (!211), B (!212), C (!213) MERGED; D IS BUILT, REVIEWED (2 rounds, 4 PASS) AND OPEN
AS !214 — HIS MERGE CLOSES STEP 3.** Governance MR (`.gitlab-ci.yml` locked): the projection check
(`scripts/check_yml_vs_projection.py --catalog <path>`, 101 models / 1,915 listed columns / 0 absent
against the prod catalogue), its pytest, the two CI lines, the pin, §3.5 "in place". ⚠ The issue
line said a struct entry is matched by its PARENT; that was false — dbt-bigquery's catalogue holds
the leaf paths too (`COLUMN_FIELD_PATHS`), so the check matches the FULL PATH (strictly stronger;
the platform reviewer caught it in round 1; contract, MR head and the #109 line all corrected).
Merging !214 does not fire `data:build:main` (path filter), so the check's first live run is the
next model/yml merge; a red there also drops that merge's docs artifacts (no `when: always`, as
the docs line always did). To run it locally, fetch a prod catalogue: `glab api
"projects/85168767/jobs/<id>/artifacts/dbt_project/target/catalog.json"` from the latest
`data:build:main`; the dev `dbt_project/target/catalog.json` aborts (partial) by design.
**After #109 step 3, `glab issue list` decides what is next — not this file.**
**#150 is merged** (!209). !209's rulings, recorded in its
contract: **the match slug comes from the warehouse**; **played rows are inert until the match
report page exists**; the EN/DE/FI copy shipped as drafted. Until the next `deploy:export` (manual,
still `teams,fixtures`) production shows the committed sample, as it does for Home. **#150 is not
blocked on #155.** **#156** (filed 2026-09-19 at his word): the nightly export, build and deploy from
live data, the go-live item that ends the committed sample; its export-and-build half is worth
running before go-live, since full-scale defects (#155) show only there.

**#155 (filed 2026-09-19, Matches milestone): two unplayed meetings of the same clubs share the
match preview page's title**, 12 pairings × 3 locales; the full-scale build (15,078 match pages,
8 GB heap, 14 min) fails `audit-seo` on exactly that and nothing else; #150's `check-built-pages`
(match pages = payloads × locales = the warehouse's unplayed count) found it. The title's wording
is his; the fix is the fixture page's title template.

**What #150 left behind:** `mart_competition_fixtures` is the mart #131 reads by date; the shared
row is `site_v2/src/components/ui/MatchRow.astro` (`linkPlayed` flips when #132's report page
lands; Home's `FixtureRow.astro` still has its own markup — converge under #131); the sample
carries all 279 unplayed Bundesliga payloads (`.gitignore` range 1575167–1575445; move its start as
matchdays are played, refresh with `competitions/BL1/2026.json`).

**GITHUB IS A READ-ONLY MIRROR OF `main` SINCE 2026-09-18** (his ruling; `CLAUDE.md`'s mirror
bullet is the durable text, including what the token's renewal needs). **Actions are disabled at
the repository level and that setting is never flipped** (`.github/workflows/README.md` says why).
`origin` equals GitLab's `main` after each sync; still never the base, never pushed to. Pipelines
stay members-only (his call), so the README carries a static `CI · GitLab` badge. The runbook
rewrite (operations guide and development workflow still describe GitHub Actions as live CI) is
**#154**, unscheduled.

**#153, THE DESIGN-SYSTEM MECHANISM, IS DONE AND MERGED**: the block standard, `system.css`, the
lint, the measured check, `validate:ui` running all three on every MR. **#151 does not merge until
the check passes on its pages and on Home.**

**#109, THE DBT TESTING STRATEGY: steps 1 and 2 merged, step 3 in flight.** Step 1 (!201): the
rules, `engineering_standards.md` §3.1–3.5. Step 2 (!202): the two catalogue-generated rate guards
`dbt_project/tests/assert_*_rates_inputs_covered.sql`. **Step 3 is four MRs, the text on #109
("Step 3 — the mechanisms and the sweep"), each its own contract, the warehouse reviewer on
`dbt_project/**`, platform on `scripts/**`:** **A** (!211, merged): `store_failures` on all 54
singular tests, 3 flipped to `warn`. **B** (!212, merged): range tests on 153 rates; `relationships`
on 76 foreign keys; **the declared soft link** (`meta: soft_link:` on the 4 keys that name clubs
and players outside the tracked competitions, stated in `engineering_standards.md` §3.1);
`scripts/check_relationships_coverage.py`, enforced by its pytest on the real tree in
`test:python`. **C** (!213, merged): every listed column described — 359 blanks filled (54 new blocks
in `shared_columns.md`, `league_code` split per site: 9 provenance, 75 competition), ~52 inline
texts converted to references; `check_description_hygiene.py` gains `_column_coverage`
(every listed model column described, floor `MIN_LISTED_COLUMNS`); §3.5 says both mechanisms are
in place. **D** (!214, open, WHERE WE ARE above): `scripts/check_yml_vs_projection.py`, the two
CI lines, the pin, §3.5's last two bullets "in place". ⚠ Noted on B, not touched:
`int_player_season__metrics` (in `int_team_season.yml`) still bounds the three player
provider-subset ratios [0,1] at season grain. ⚠ Noted on C, not touched: the generated
`shots_inside_box_sum_season__team` block's catalogue sentence ("can be understated rather than
null") is false on the season surface; C referenced a hand block instead — the fix is the
catalogue seed's description.

**One default still open, merged as a default:** the breadcrumb's current-page colour (`ink-2`,
links muted; the mocks had it inverted); its inventory row is `proposed` until he rules. ⚠ **A
ruling request is ONE question, a 2×2 table, then the recommendation.**

**THE COMPETITION PAGE IS FULLY APPROVED ON #129 (2026-09-16); he will NOT re-check pages by eye.**
**Build issues:** **#150** Matchdays (merged) · **#151** Rankings + the Overview rework · **#152**
metric groups. The page-wide rules live in the block standard and `system.css`, measured — the
builds compose from them and add nothing of their own.

**The measured check is the arbiter.** `python scripts/check_design_inventory.py --dist
site_v2/dist` (build first). An element not in `block_standard.md` is a design decision: put to
him and rendered on every page it touches before it is ruled.

**HOME IS DONE (#127, `!187`) and THE COMPETITIONS HUB (#128, `!189`).** Go-live items (About,
Imprint) have no issue — his call. **The roadmap is the GitLab milestones in the site's menu
order: Home · Competitions · Matches · Teams · Players · Standings · Leaderboards** — one review
issue per page (#127–#140), approved on the issue before anything is built; after #153 and the
competition builds comes the Matches milestone (#130, #131, #132); dependencies the page picks up
when they land: #105, #145, #146, #148, #69.

**How we work** is `CLAUDE.md` "Which source answers which question" and `working_agreement.md`
§1 / §11: the requirement is the issue, the plan its How, a decision is recorded by the thing it
changes, the MR head is his check and **his merge is the approval** — set the head with
`glab mr update <n> --description` right after the hook opens the MR. **The stop gate blocks a
turn ending with anything in `git stash`**; parked work goes on a pushed `parked/<branch>`.

**Parked, real, not lost:** the built player Overview tab is on `parked/feat/player-overview-tab`
(a KNOWN-WRONG default-season rule, see #118); the four-tab decision is recorded in #118.

⛔ **BEFORE TOUCHING ANY METRIC, READ `docs/metric_layer.md`.** A metric is NULL unless its
inputs cover every match in the window; a thinly covered competition showing blank is correct.

⚠ **THE VOLUME IS THE PROBLEM** (*"A wallpaper of text"*; *"Explain like I'm twelve. Keep it
short."*). The decision and the consequence, two sentences. Commit, push, retry, rebase and
regenerate WITHOUT asking; keep working.

⚠ **A red nightly skips every dependent mart, and an MR's `data:build:mr` then fails the singular
tests it defers to prod — retry after a green nightly.**

## ⛔ WHAT 2026-09-08 CHANGED IN PROD — read before trusting an older measurement

Awarded results count as played; the override seed is `fixture_team_id_overrides` for all three
fixture-level feeds; the freshness guard ignores `SUSP`/`INT`.
`assert_team_season_games_not_short_of_standings` is WARN and RED on 3 rows by design (#110 plus
Al Wehda AFCCL 2021). **Prod is correct.**

⛔⛔ **A CORRECTION IN BASE DOES NOT REACH AN INCREMENTAL FACT** (`fct_fixture_event`,
`fct_fixture_player_stats`, `fct_fixture_team_stats`): a merge inserts the corrected row and
strands the old one. **The fix is a one-off `dbt build --full-refresh --select <facts>`, his to
run**, checked lossless first (`fct_fixture_event` held 17 rows base no longer emits).

## ⛔ THE ROUND CAP (3) — the override practice, settled by use, never ruled

Past the cap, write a `rounds_cap_override:` in `review.md` that clears a standing FAIL BY REVIEW
and says he did not rule on the cap. Check a claim before asserting it.
⚠ **Never ask him to approve routine mechanics** — ask about the RULE.

## ⛔ PARKED: the dbt profile MR — TWO OPEN FAILS

Branch `fix/dbt-profile-local-to-this-repo`; WIP on `parked/fix/dbt-profile-local-to-this-repo--profile-root`.
The repo-local `profiles.yml` at the ROOT is the fix (dbt reads `--profiles-dir` → `DBT_PROFILES_DIR`
→ **CWD** → `~/.dbt`). Open: (1) a stale `decisions_taken` paragraph saying `dbt_project/`;
(2) **`.mcp.json` sets `DBT_PROFILES_DIR: C:/Users/Rami/.dbt`**, a PROTECTED path that outranks
the fix. **No `prod` target** in the local profile, ever. `dbt ls` / `parse` work with a throwaway
profile in the scratchpad (target `dev_scratch`).

## ⛔ OPEN — DEFECTS TO FIX (not decisions to wait on)

  - **#110 — a forfeit the provider labels `FT`** with a score and no stat line, so 18 of 19 Süper
    Lig 2022 team-seasons are blank; the other 435 blanked team-seasons are CORRECT. The fix needs
    a competition-relative signal, not a blanket rule. Everything measured is on the issue.
  - **#111 — no test compares a metric to its own formula.** The catalogue publishes the
    expressions; the models compute the same metric in SQL; nothing checks they agree
    (`assert_metric_catalogue_expr_resolvable` binds, never evaluates). No dbt unit tests exist.
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

Across `!156`–`!213` every FAIL came from a reviewer or the pipeline; the offline gates were green
over all of them. **Almost every defect was a claim asserted without opening the file** — open it
(on #109: a job named by its name, a "NULL when" sentence beside a not_null, "not wired into CI"
while a pytest ran the gate). Sweep the RIGHT tree, two-sided; mutation-test against the mutation
the design is defended against; Windows green, Linux red: an unsorted listing, a package the
workstation has and the job's image does not.

## ⛔ TRAPS THAT COST REAL TIME

⛔⛔ **A REBASE CONFLICT CAN BE diff3, WHICH HAS FOUR MARKER KINDS** — `|||||||` too. `git add`
marks a file resolved WITHOUT reading it. **Grep all four**, prove a union structurally.
⚠ **On a sibling-MR rebase the CODE merges cleanly and the PAPERWORK collides** — `contract.md`
and `review.md` are per-task and one side wins; regenerate and re-review.
⛔⛔ **"MERGED" IS A CLAIM TO VERIFY, and `--is-ancestor` IS NOT THE CHECK.** Use
`git cherry gitlab/main <branch>` (`+` = not upstream). Deleting an open MR's source branch CLOSES
the MR. ⚠ A stacked branch that reverts its base's change shows NO hunk in the cumulative patch
vs `main` — give reviewers the diff vs the parent commit too.
⚠ **`git pull` on main pulls the GitHub MIRROR (`origin`).** Use `git pull --ff-only gitlab main`.
⚠ **The push guard refuses EVERY push while standing on main**, and reads the CURRENT branch, so
`checkout && push` in one call is blocked as a whole.
⛔⛔ **`--review-patch` PRINTS; only a REDIRECT writes the file.** Run bare it leaves the previous
round's patch on disk, exit 0. **Regenerate it immediately before every round, after `git add -u`.**
⭐ Free tell: `--staged-hash` printing `e3b0c442…` = `sha256("")`, an empty staged diff.
⚠ **CP1252, NOT UTF-8, IN BOTH DIRECTIONS on this machine.** `subprocess.run(..., text=True)` and the
`bq` CLI's CSV output are both cp1252; a Python `print` of `→` or `§` dies. Use `PYTHONIOENCODING=utf-8`.
⚠ **SQLFluff exits 1 ON SUCCESS when stdout is redirected** (emoji + CP1252). Read exit codes bare.
⚠ **The auto-mode classifier refuses `2>/dev/null` and `2>&1` as "outside scope"** — never redirect
stderr; the contract gate reads it as a file write.

## Method that works

Contract FIRST on a clean tree (stash by explicit path with a `TEMP-` label; after the edit
`git stash pop` REFUSES because the stash carries the pre-edit contract — restore with
`git checkout stash@{0} -- <paths>` then `git stash drop`, inside the same turn). Then gates with
exit codes read bare, mutations watched RED, blinded reviewers, `review.md` with `--staged-hash`.
Rounds are PER REVIEWER; each section `## <exact-routing-key>`, `VERDICT:`, `risks_checked:`.
⚠ **`contract.md` is INSIDE the review hash**; amend BEFORE the round.
⚠ `acceptance_evidence.md` needs `criteria_demonstrated:` at **column 0** — `## criteria_demonstrated:`
is invisible to the parser — with one 15+ character bullet per criterion.
