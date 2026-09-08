# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-09-08**. **main `4bef954`**, clean, **no open MRs** — !154, !155, **!156** and
**!157** all merged today. **GITLAB** (`glab`, MRs)._
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

## ⛔ NEXT ACTION — two candidates, the ORDER IS THE CPO'S

**(a) THE FRESHNESS GUARD, `assert_fct_fixture_no_stale_live`.** Still unfixed, still failing the
nightly intermittently. ⭐ **2026-09-08 proved it is not one broken check, it is COVER**: the nightly
was red three nights running for a known reason, so a second, unrelated defect (a nameless team
breaking `dim_team`) rode along unnoticed until an MR pipeline surfaced it. Recommendation: take this
first; it is cheap and it is actively hiding things.

**(b) #40 MR B — unstash and finish the Top players block.** Unchanged and still valid. The warehouse
half shipped in !153. The block is **WRITTEN AND PARKED** in stash **`TEMP-40-mrB`** — export shaper
`shape_home_top_players` (15 unit tests), `TopPlayers.astro`, `.board`/`.brow` CSS, `LandingBoard`
types, copy in three locales.
  1. `git stash pop` the `TEMP-40-mrB` entry — **match by MESSAGE, never by index**; the stack is
     shared and holds ~8 other parked WIPs.
  2. Contract, wire `TopPlayers.astro` into `index.astro`, build the **player scaffold**
     (`pages/*/players/*.astro` + `stub: true` spec + `STUB_PAGES` entry) as !151 did the competition
     page. ⚠ Without it `audit-seo.mjs` check 8 fails the build.
  3. Re-export `landing.json`, then VERIFY AT 375px AS WELL AS DESKTOP — !151 shipped a 21px tap
     target and a focus ring through a divider, both invisible at desktop.
⚠ **#40's issue body is STALE**: the POOLED ranking was withdrawn 2026-08-18 for **one player per
league**; the rule it justified (every row shows club AND league) stands. Page length is NOT open.
⚠ **The DE/FI board labels in the stash NEED THE CPO'S CONFIRMATION** — `metricLabel()` falls back to
English then to EMPTY, so a missing Finnish label renders a blank board title.

## ⛔ WHAT 2026-09-08 CHANGED IN PROD — read before trusting an older measurement

**!156 (awarded matches)** — `AWD`/`WO` now count as played for RESULTS; `status_short` uppercased at
staging. 32 team-seasons gain a match, 23 gain points; **0 lose a statistical metric**, because the
coverage gates moved to `games_expecting_team_stats` (played minus awarded) at all 35 sites.
**!157 (team-id overrides)** — the seed is renamed **`fixture_team_id_overrides`** and now applies to
**all three** fixture-level feeds plus `base_apif__teams`' key union, not events only. 21 player rows
and 1 team-stats row reattributed; keys `(BSA,22722)` and `(UEL,2263)` retired from `dim_team`.
⭐ **PROD WAS REPAIRED BY HAND and is CORRECT**: `data:build:main` re-run to green and the two
incremental facts `--full-refresh`ed. **Nothing is owed operationally.**

⛔⛔ **THE TRAP THAT NEARLY SHIPPED, AND IT WILL RECUR: A CORRECTION IN BASE DOES NOT REACH AN
INCREMENTAL FACT.** The fanout facts filter `raw_ingested_at > max(target)`, which a finished fixture
never advances. **Only three models in the project are incremental** — `fct_fixture_event`,
`fct_fixture_player_stats`, `fct_fixture_team_stats` — everything else is a table, so check rather
than assume either way. ⚠ A self-heal clause CANNOT always be copied: the player/team-stats surrogate
keys INCLUDE `team_id`, so correcting it changes the key and a merge INSERTS the corrected row and
strands the old one. `event_sk` excludes `team_id`, which is the only reason its #526 self-heal works.
**The fix is a one-off `dbt build --full-refresh --select <facts>`, and it is the CPO's to run**
(`dbt build` is banned here).
⚠ Check a refresh is lossless first: compare the fact's row count to its base. Equal = nothing
accumulated. On 2026-09-08 player stats and team stats matched exactly, but **`fct_fixture_event` was
858,032 against a base of 858,015** — 17 rows it retains that base no longer emits. That +17 is why
these stay incremental instead of becoming tables.
⭐ **The repo's whole verification method is BLIND to this.** Compiling a model and running it
read-only against prod measures what the LOGIC computes, never what the incremental TABLE contains.

## ⛔ THE ROUND CAP IS UNRESOLVED AND WILL BLOCK THE NEXT LONG MR

!156 finished at **round 9** against a cap of 3. The `rounds_cap_override` on file was given at round
3 and its text covers rounds 1–4. `scope-auditor` ruled that rounds 5–9 needed a CURRENT ruling and
that **no reviewer can supply it**. It was put to the CPO, who merged without answering — so the
precedent is unsettled and the next long MR faces the same question.
⚠ **Do not ask him to approve routine mechanics** (commit, push, retry a pipeline, regenerate an
artifact, rebase onto a merged sibling). Recorded in `escalations.log`, entry
`2026-09-08 — chore/handover-2026-09-08 — DO NOT ASK FOR MECHANICS`, with what prompted it and what
it does NOT license. Ask about the RULE, do the mechanics without asking.

## ⛔ PARKED: the dbt profile MR — TWO OPEN FAILS

Branch `fix/dbt-profile-local-to-this-repo`, stash **`TEMP-profile-root`**. The repo-local
`profiles.yml` at the ROOT is the fix (dbt reads `--profiles-dir` → `DBT_PROFILES_DIR` → **CWD** →
`~/.dbt`; `--project-dir` does NOT move it, and every CI job does `cd dbt_project`, so a root profile
can never shadow CI's). Open: (1) a stale `decisions_taken` paragraph saying the file goes in
`dbt_project/`; (2) **`.mcp.json` sets `DBT_PROFILES_DIR: C:/Users/Rami/.dbt`** — a PROTECTED path
that outranks the whole fix. ⚠ There is deliberately **no `prod` target** in the local profile; that
absence is the safety mechanism. A prod target needs `dataset: dbt_analytics` to resolve the base
models, which is exactly the line that overwrites prod's base tables and seeds if a build ever
selects one — so it is only ever safe with an explicit `--select` naming core models.

## ⛔ OPEN, AND THE CPO'S

  - **#109** — no end-to-end dbt test strategy, and no rule for when a NULL is a defect rather than
    the honest answer. Filed at his instruction; not attempted.
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

## ⛔ WHAT ACTUALLY FINDS DEFECTS — reconfirmed hard on !156/!157

**1. The blinded review, then CI. Almost never a gate.** On !156 every FAIL came from a reviewer or
the MR pipeline; `dbt parse`, SQLFluff and four offline gates were green over all of them.
**2. THREE OF MY DEFECTS WERE SENTENCES I WROTE FROM MEMORY** — which model is incremental, how many
keys move, which test exists. Each was checkable in seconds. **Open the file; do not recall it.**
**3. A CLASS RECURS UNTIL YOU SWEEP THE RIGHT TREE.** The same defect — a gate moved, a divisor did
not — hit three times on !156. Round 3 swept every RATE in the two gate files and found nothing,
because the third instance was in a **TEST** encoding an invariant ABOUT a rate.
**4. Report every sweep two-sided** ("1 moves, 4 stay") and mutation-test against the mutation the
design is DEFENDED against, not the ones that come to mind.
**5. A reviewer's flagged-but-not-failed trade-off is still a trade-off.** On !156 one was a real
loss of coverage with a fix the reviewer had judged impossible.

## ⛔ TRAPS THAT COST REAL TIME

⛔⛔ **A REBASE CONFLICT CAN BE diff3, WHICH HAS FOUR MARKER KINDS.** I grepped for `<<<<<<<`,
`=======`, `>>>>>>>` and missed **`|||||||`**, committing it into `escalations.log` above the rulings
the contract cites. `git add` marks a file resolved WITHOUT reading it, and `dbt parse`, SQLFluff,
four gates and CI's `validate:governance` ALL passed with it committed. **Grep all four**, and prove
a union structurally (`diff -q` each side against the resolved head/tail; check the lengths sum).
⚠ **On a sibling-MR rebase the CODE merges cleanly and the PAPERWORK collides.** `escalations.log`
must be a UNION — each branch's version deletes the other's entries, and reviewers check those
citations verbatim.
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

Contract FIRST on a clean tree (stash by explicit path with a `TEMP-` label, pop immediately). Then
gates unpiped with exit codes read bare, mutations watched RED, blinded reviewers, `review.md` with
`--staged-hash`. Rounds are PER REVIEWER. Each section needs `## <exact-routing-key>`, `VERDICT:`,
then `risks_checked:`. ⚠ **`contract.md` is INSIDE the review hash**; amend BEFORE the round.
⚠ `acceptance_evidence.md` needs `criteria_demonstrated:` at **column 0** — `## criteria_demonstrated:`
is invisible to the parser — with one 15+ character bullet per criterion.
