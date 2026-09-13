# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-09-13**, on `feat/143-home-approved-design`. **GITLAB** (`glab`, MRs).
⚠ No SHA here on purpose: this file merges as a commit, so any hash it named would be its own parent
and wrong on arrival. Run `git log -1` and `glab mr list`; they are correct and this file cannot be._

⛔ **THE POST-COMMIT HOOK PUSHES TO `main` IF THE BRANCH TRACKS `main`.**
`git checkout -b <branch> gitlab/main` sets `main` as upstream. **Run `git branch --unset-upstream`
right after creating a branch**, and push with `git push gitlab <b>:<b>`, verifying `-> <b>`.
⛔⛔ **DO NOT TOUCH `glab auth` OR INSTALL A PROJECT TOKEN. 2026-09-03 cost a full day.** ONE
credential per MACHINE — re-authing it broke two other repos. The safeguard that the agent never
merges is **branch protection** plus the memory rule **never merge**; NOT a token, NOT a hook.
⛔ **`fix/merge-guard-covers-the-api` IS DEAD** — 11 rounds, judged over-engineering, DISCARDED.
⛔⛔ **CI HAS NO FALLBACK.** `shared_runners_enabled=false`, so **`ci-runner-01` is the ONLY runner**
— a dead box means pipelines QUEUE, they do not fail over. ⚠ `~/.ssh/id_ed25519` is
PASSPHRASE-PROTECTED, so `ssh -o BatchMode=yes` fails `publickey` — not a broken key.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`.

## ⛔ WHERE WE ARE

**HOME IS APPROVED (#127, 2026-09-13) AND ITS BUILD IS ON `feat/143-home-approved-design`.** The
approved design is the `The approved design` section of #127's description — the authority for
Home; `10_home.md` is corrected to it, not rewritten (#100 still owns the reduction). Rulings that
landed elsewhere: #101 weights **80/10/10** (build item, scope + season trap on the issue); #114
team tie-break = **underlying total** (build item); Stats → **Leaderboards** (milestone 7, #139,
#140 renamed; metric names on Home boards link there once built); menu and footer links go live
per page. #143 builds the Home-owned parts: the round-per-competition window (SQL in the export),
the 3-row `<details>` fold (`FixtureRow.astro` extracted — Astro frontmatter cannot hold JSX), no
team-board floor (`>= 1`; benchmark gates untouched), wireframe/overview/mock corrected. The
committed `landing.json` sample (≤2 per competition) cannot show the fold and was NOT refreshed
(a set roll-forward would pin 232 fixture payloads); evidence is from the dev server with a
fresh export placed then reverted. Stated to the CPO in the MR head, not decided: a postponed
match keeps its round name, so a straggler renders as a one-match matchday for a few days (BL1
3/season, BSA 16). Go-live items (About, Imprint) have no tracker issue yet — his call to file.

**THE ROADMAP IS THE GITLAB MILESTONES, IN THE SITE'S MENU ORDER: Home · Competitions · Matches ·
Teams · Players · Standings · Leaderboards.** One review issue per page under each (#127–#140): what is on
the page, where each block's data comes from, what it links to and from — rechecked and approved by
the CPO on the issue BEFORE anything is built or rebuilt, built pages included, because the earlier
agreements may be stale. Build issues are filed only against an approved review. Go-live items
(legal pages, domain, dropping `noindex`) follow the last page. The two dead roadmap documents are
gone (`!184`). **The tracker has a backup in the repo** (`!185`): `docs/tracker/gitlab_snapshot.md`,
written only by `python scripts/snapshot_tracker.py` — run it at the END of every session before
the handover commit; a hook refuses any hand edit, a test checks its checksum, and it is read only
when GitLab is unreachable. ⚠ Its checksum is self-consistency, not provenance — a forged shell
write passes; forbidden by rule, and the CPO knows. **Next: land #143's MR, then the
Competitions hub review, #128, the same way as Home (built page beside its data sources and
links; rulings one at a time; consolidate into the issue description; he ticks).**

**How we work since 2026-09-11** is in `CLAUDE.md` "Which source answers which question" and
`docs/working_agreement.md` §1 / §11: the requirement is the GitLab issue (Task template), the
plan is its How, a decision is recorded by the thing it changes (`escalations.log` is FROZEN), the
MR head is his check (`Closes #N`, ticks with links, `Locked files`) and **his merge is the
approval** — set it with `glab mr update <n> --description` right after the hook opens the MR.
**The stop gate blocks a turn that ends with anything in `git stash`**; parked work goes on a
pushed `parked/<branch>` (ten exist, five dead per `!173`, deleting them is his).

**Parked, real, not lost:** the built player Overview tab is on `parked/feat/player-overview-tab`
(stash commit; untracked files in its third parent — `git stash apply parked/feat/player-overview-tab`)
and carries a KNOWN-WRONG default-season rule (see #118). The four-tab decision (2026-07-27) is
preserved on `archive/docs-handover-player-tabs-and-seo` and recorded in #118.

⛔ **BEFORE TOUCHING ANY METRIC, READ `docs/metric_layer.md`.** It is short and it is the map: where a
metric is defined, which model computes it, what makes it NULL, what CI will fail you on. The
incomplete-data rule lives there — a metric is NULL unless its inputs cover every match in the
window, and a thinly covered competition showing blank is correct output.

⚠ **HE HAS SAID, MORE THAN ONCE, THAT THE VOLUME IS THE PROBLEM** (*"A wallpaper of text"*; *"Explain
like I'm twelve. Keep it short."*). Give him the decision and the consequence, in two sentences.
Process detail, round counts, gate mechanics and hash rebinding go in the repo — never in a message
to him. Commit, push, retry, rebase and regenerate WITHOUT asking. And keep working — three times
in one session he asked "you waiting for something?".

## ⛔ WHAT 2026-09-08 CHANGED IN PROD — read before trusting an older measurement

Awarded results count as played (`games_expecting_team_stats` at every gate); the override seed is
`fixture_team_id_overrides` for all three fixture-level feeds; the freshness guard ignores
`SUSP`/`INT`. `assert_team_season_games_not_short_of_standings` is WARN and RED on **3 rows by
design**: Trabzonspor + Gaziantep FK (the Turkish forfeit — #110) and Al Wehda AFCCL 2021 (5
fixtures never ingested — a different problem, not #110). **Prod is correct; nothing is owed.**

⛔⛔ **THE TRAP THAT NEARLY SHIPPED, AND IT WILL RECUR: A CORRECTION IN BASE DOES NOT REACH AN
INCREMENTAL FACT.** The fanout facts filter `raw_ingested_at > max(target)`, which a finished fixture
never advances. **Only three models in the project are incremental** — `fct_fixture_event`,
`fct_fixture_player_stats`, `fct_fixture_team_stats` — everything else is a table, so check rather
than assume either way. ⚠ A self-heal clause CANNOT always be copied: the player/team-stats surrogate
keys INCLUDE `team_id`, so correcting it changes the key and a merge INSERTS the corrected row and
strands the old one. `event_sk` excludes `team_id`, which is the only reason its self-heal works.
**The fix is a one-off `dbt build --full-refresh --select <facts>`, and it is the CPO's to run**
(`dbt build` is banned here).
⚠ Check a refresh is lossless first: compare the fact's row count to its base. Equal = nothing
accumulated. On 2026-09-08 player stats and team stats matched exactly, but **`fct_fixture_event` was
858,032 against a base of 858,015** — 17 rows it retains that base no longer emits. That +17 is why
these stay incremental instead of becoming tables.
⭐ **The repo's whole verification method is BLIND to this.** Compiling a model and running it
read-only against prod measures what the LOGIC computes, never what the incremental TABLE contains.

## ⛔ THE ROUND CAP (3) — the override practice, settled by use, never ruled

Past the cap, write a `rounds_cap_override:` in `review.md` that clears a standing FAIL BY REVIEW
and says he did not rule on the cap (`!172`–`!174` did). Keep rounds down by checking a claim
before asserting it. ⚠ **Never ask him to approve routine mechanics** — ask about the RULE.

## ⛔ PARKED: the dbt profile MR — TWO OPEN FAILS

Branch `fix/dbt-profile-local-to-this-repo`; the WIP is on
`parked/fix/dbt-profile-local-to-this-repo--profile-root` (and `…--profile-local-3`). The repo-local
`profiles.yml` at the ROOT is the fix (dbt reads `--profiles-dir` → `DBT_PROFILES_DIR` → **CWD** →
`~/.dbt`; `--project-dir` does NOT move it, and every CI job does `cd dbt_project`, so a root profile
can never shadow CI's). Open: (1) a stale `decisions_taken` paragraph saying the file goes in
`dbt_project/`; (2) **`.mcp.json` sets `DBT_PROFILES_DIR: C:/Users/Rami/.dbt`** — a PROTECTED path
that outranks the whole fix. ⚠ There is deliberately **no `prod` target** in the local profile; that
absence is the safety mechanism. A prod target needs `dataset: dbt_analytics` to resolve the base
models, which is exactly the line that overwrites prod's base tables and seeds if a build ever
selects one — so it is only ever safe with an explicit `--select` naming core models.

## ⛔ OPEN — DEFECTS TO FIX (not decisions to wait on)

  - **#110 — a forfeit the provider labels `FT`.** An awarded result is official and counts, and
    `!156` already stops one destroying a season via `games_expecting_team_stats`. But that column
    keys on `status_short`, and the provider often files a forfeit as `FT` with a score and no stat
    line — so 18 of 19 Süper Lig 2022 team-seasons are blank. ⚠ **Not the same as the other 435**
    blanked team-seasons, which are correct: measured, of 9,515 fixtures with no team statistics,
    ZERO have statistics in the raw payload that our models discard. The provider supplied nothing
    and the rule applies. The fix needs a competition-relative signal (a fixture with no stats in a
    league where 90%+ have them), not a blanket rule. Everything measured is on the issue.
  - **#111 — no test compares a metric to its own formula.** The catalogue publishes
    `base_relation` + `numerator_expr` + `denominator_expr`; the models compute the same metric in
    SQL; nothing checks they agree. `assert_metric_catalogue_expr_resolvable` already parses those
    expressions and binds them — it just never evaluates them. No dbt unit tests exist either.
  - **#109** — no end-to-end dbt test strategy, and no rule for when a NULL is a defect rather than
    the honest answer. Filed at the CPO's instruction; #111 is one concrete piece of it.
  - **#108** — rounding is business logic and `DeservedHero.astro:79` does it in the browser.
  - **The mid-season deserved-vs-actual line and its start matchday** — both open, and they gate
    showing that hero on live data.
  - **`fix/raw-players-row-chunking` is UNMERGED and its mechanism is ABSENT from main.** Commit
    `1f822a2` chunks the `RAW_APIF_PLAYERS` snapshot under BigQuery's 100MB per-row limit, citing
    *"LIBER failed… UEL 81.8MB / UCL 78.7MB imminent."* The FIXTURE landed on main, the fix did not.
    Settle superseded-or-abandoned before those rosters grow.
  - **#101's rotation MR**, when built: a league whose new season has started but has no FINISHED
    matches produces no rows, so `is_current_season` falls back to the last season WITH data — the
    block would show last season's leaders under "Season totals to date".
  - **#99 / #102 / #96 / #98** — export board keys pinned by no test; `mart_leaderboards` is
    player-only under an unprefixed name; no offline gate checks `accepted_values`.

## ⛔ WHAT ACTUALLY FINDS DEFECTS — !156, !157 and !159, 13 review rounds

**1. The blinded review, then CI. Almost never a gate.** Every FAIL across those three MRs came from
a reviewer or the MR pipeline. `dbt parse`, SQLFluff and the offline gates were green over all of
them — including over a git conflict marker committed into the ruling log.
**2. ⛔ ALMOST EVERY DEFECT WAS A CLAIM I ASSERTED WITHOUT OPENING THE FILE** — which model is
incremental, how many keys move, which test exists, that a column named `played` came from the
standings (it was an alias of our own count, so a whole test could never fail), that I had logged the
rulings I cited. **Open the file; do not recall it.** This is the single highest-yield habit change
available.
**3. A CLASS RECURS UNTIL YOU SWEEP THE RIGHT TREE.** "A gate moved, a divisor did not" hit three
times on !156; round 3 swept every RATE in the two gate files and missed the third, which was in a
TEST encoding an invariant ABOUT a rate.
**4. Report every sweep two-sided** ("1 moves, 4 stay") and mutation-test against the mutation the
design is DEFENDED against, not the ones that come to mind.
**5. A reviewer's flagged-but-not-failed trade-off is still a trade-off** — twice it was a real loss
of coverage with a fix the reviewer had judged impossible.
**6. REWRITE THE DESIGN, REWRITE THE PAPERWORK.** Acceptance criteria describing a previous
design were left standing twice on !159, and a reviewer had to find them.

## ⛔ TRAPS THAT COST REAL TIME

⛔⛔ **A REBASE CONFLICT CAN BE diff3, WHICH HAS FOUR MARKER KINDS** — `|||||||` too. `git add`
marks a file resolved WITHOUT reading it, and every gate and CI passed with a marker committed.
**Grep all four**, and prove a union structurally (`diff -q` each side against the resolved
head/tail; check the lengths sum).
⚠ **On a sibling-MR rebase the CODE merges cleanly and the PAPERWORK collides** — `contract.md`
and `review.md` are per-task and one side wins; regenerate and re-review. (The log is frozen, so
its union problem is gone.)
⛔⛔ **"MERGED" IS A CLAIM TO VERIFY, and `--is-ancestor` IS NOT THE CHECK** — it called 20 of 22
landed branches unmerged. Use `git cherry gitlab/main <branch>` (`+` = not upstream). Deleting an
open MR's source branch CLOSES the MR.
⚠ **`git pull` on main hits the DEAD GitHub `origin` and 403s.** Use `git pull --ff-only gitlab main`.
⚠ **The push guard refuses EVERY push while standing on main.** Branch to a throwaway to push
deletions. It reads the CURRENT branch, so `checkout && push` in one call is blocked as a whole.
⛔⛔ **`--review-patch` PRINTS; only a REDIRECT writes the file.** Run bare it leaves the previous
round's patch on disk, exit 0 — that served reviewers a stale diff on `!132` and `!151`, and on !156
a patch generated BEFORE a fix made a reviewer FAIL on something already fixed.
**Regenerate it immediately before every round, after `git add -u`.**
⭐ Free tell: `--staged-hash` printing `e3b0c442…` = `sha256("")`, an empty staged diff.
⚠ **CP1252, NOT UTF-8, IN BOTH DIRECTIONS on this machine.** `subprocess.run(..., text=True)` and the
`bq` CLI's CSV output are both cp1252. Capture BYTES, decode utf-8 first with a cp1252 fallback.
⚠ **SQLFluff exits 1 ON SUCCESS when stdout is redirected** (emoji + CP1252). Read exit codes BARE
and UNREDIRECTED, or set `PYTHONIOENCODING=utf-8`.

## Method that works

Contract FIRST on a clean tree (stash by explicit path with a `TEMP-` label; after the edit
`git stash pop` REFUSES because the stash carries the pre-edit contract — restore with
`git checkout stash@{0} -- <paths>` then `git stash drop`, inside the same turn). Then gates unpiped
with exit codes read bare, mutations watched RED, blinded reviewers, `review.md` with
`--staged-hash`. Rounds are PER REVIEWER. Each section needs `## <exact-routing-key>`, `VERDICT:`,
then `risks_checked:`. ⚠ **`contract.md` is INSIDE the review hash**; amend BEFORE the round.
⚠ `acceptance_evidence.md` needs `criteria_demonstrated:` at **column 0** — `## criteria_demonstrated:`
is invisible to the parser — with one 15+ character bullet per criterion.
