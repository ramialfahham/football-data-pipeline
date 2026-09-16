# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-09-16 (evening)**, on `chore/session-end-2026-09-16b`. **GITLAB** (`glab`, MRs).
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

**THE COMPETITION PAGE IS FULLY APPROVED ON #129 (2026-09-16) — content-wise done; the CPO will NOT
re-check pages by eye.** The design is #129's `The approved design`: **three tabs, Overview ·
Matchdays · Rankings** (Rounds for a cup), header identical on every tab, no page title, no sentence
outside the Overview. Overview = Table · **Deserved points table** (full table by deserved points:
# · club · Balance · Deserved · Pts · Diff) · The season in numbers (six fact rows, every one a link
to a leaderboard, #140); **Next matches struck** (the Matchdays tab opens on it). Matchdays =
`/fixtures/`, the picker ‹ MATCHDAY N › with a Next tag, the **Schedule** block, every row a link
(played → match page #132; unplayed → preview page, form as of today), **Top match** tag on the
flagged row, TBC for no kick-off. Rankings = two blocks **Team rankings** (12 boards) and **Player
rankings** (13 boards), the metric groups from the catalogue (#152: `duels` → `one_on_one`,
"One-on-one"), boards as striped tables, five rows, dense rank shown, no zero rows on a most-first
board. The four renders of record: `competition-overview`, `competition-matchdays`,
`competition-rankings`, `home`, all `_2026-09-16_01.html`, in the session scratchpad
(`C:/Users/Rami/AppData/Local/Temp/claude/D--Projects-football-data-pipeline/<session>/scratchpad`)
with their generators `gen_competition_matchdays.py`, `gen_competition_teams.py`,
`gen_overview_after_teams.py`, `gen_home_with_rules.py` and the data pulls — **#153 brings them
into `design-mocks/`; do that before anything else is rendered.**

**Build issues, all gated on #153:** **#150** Matchdays (the competition-season fixtures mart,
the picker, the tag; the build must carry every unplayed match page of every competition — a
founding requirement, `docs/north_star.md` "Scale ambition", merged today as `!193`: value decides
what is built, scale is never the argument, money is always asked with the number) · **#151** the
Rankings tab + the Overview rework + the page-wide rules (13px block names; 14px heading gap;
ordered-by number bold accent everywhere, fact values included; one hover tint for every row link,
visible against a stripe; stripes counted from the head row; every title at the block's left
edge; tab bar fits at 375px; the card metrics; `clean_sheets` → format `integer`, `points_won`
keeps `13/15`) · **#152** metric groups (key, `metric_group_order`, names as copy in EN/DE/FI;
closes #98) · **#153 the design-system mechanism: the element inventory in the block standard,
CSS only in `system.css`, a cross-page measured check in `validate:ui`, a lint on page CSS, the
render naming rule `<page>_<YYYY-MM-DD>_<nn>.html`.** Home's corrections are on **#127** (boards
as single-value tables, the Top match tag on its rows, the page rules).

⚠ **The day's lesson, his words: "you just change things and break things hidden somewhere else …
this way we will never complete this website."** Every new or changed element today (picker, tag,
table head, hover tint, heading size, stripe start, title edge) reached Home or the Table unseen.
**Before rendering anything: list every element used, mark the site's / changed / new; a new or
changed element is put to him and rendered on EVERY page it touches before it is ruled.** Measure,
never eyeball. No "clean stop" mid-page. Memory: `feedback_design_discipline.md`.

**Next:** #153 first (it gates #150/#151), then the builds; the roadmap continues with the Matches
milestone (#130, #131, #132 — #132 carries the future-match-page direction and the clean-sheets
pointer). Open dependencies the page picks up when they land: #105, #145, #146, #148, #69.

**HOME IS DONE (#127 approved, #143 merged as `!187`)** — with today's corrections on #127. **THE
COMPETITIONS HUB IS DONE (#128, `!189`).** Go-live items (About, Imprint) have no issue — his call.

**THE ROADMAP IS THE GITLAB MILESTONES, IN THE SITE'S MENU ORDER: Home · Competitions · Matches ·
Teams · Players · Standings · Leaderboards.** One review issue per page (#127–#140), approved by
the CPO on the issue before anything is built; build issues only against an approved review.
**The tracker has a backup in the repo** (`docs/tracker/gitlab_snapshot.md`, written only by
`python scripts/snapshot_tracker.py`, run at the END of every session before the handover commit).

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

Awarded results count as played; the override seed is `fixture_team_id_overrides` for all three
fixture-level feeds; the freshness guard ignores `SUSP`/`INT`.
`assert_team_season_games_not_short_of_standings` is WARN and RED on 3 rows by design (#110 plus
Al Wehda AFCCL 2021). **Prod is correct; nothing is owed.**

⛔⛔ **A CORRECTION IN BASE DOES NOT REACH AN INCREMENTAL FACT.** Only three models are
incremental — `fct_fixture_event`, `fct_fixture_player_stats`, `fct_fixture_team_stats`; their
filter `raw_ingested_at > max(target)` never advances for a finished fixture, and the stats keys
INCLUDE `team_id`, so a merge inserts a corrected row and strands the old one. **The fix is a
one-off `dbt build --full-refresh --select <facts>`, the CPO's to run.** Check it is lossless
first (fact rows vs base): on 2026-09-08 `fct_fixture_event` held 17 rows base no longer emits.
⭐ Compiling a model and running it read-only against prod measures the LOGIC, never what the
incremental TABLE contains.

## ⛔ THE ROUND CAP (3) — the override practice, settled by use, never ruled

Past the cap, write a `rounds_cap_override:` in `review.md` that clears a standing FAIL BY REVIEW
and says he did not rule on the cap (`!172`–`!174` did). Keep rounds down by checking a claim
before asserting it. ⚠ **Never ask him to approve routine mechanics** — ask about the RULE.

## ⛔ PARKED: the dbt profile MR — TWO OPEN FAILS

Branch `fix/dbt-profile-local-to-this-repo`; the WIP is on
`parked/fix/dbt-profile-local-to-this-repo--profile-root` (and `…--profile-local-3`). The repo-local
`profiles.yml` at the ROOT is the fix (dbt reads `--profiles-dir` → `DBT_PROFILES_DIR` → **CWD** →
`~/.dbt`; every CI job does `cd dbt_project`, so a root profile never shadows CI's). Open: (1) a
stale `decisions_taken` paragraph saying the file goes in `dbt_project/`; (2) **`.mcp.json` sets
`DBT_PROFILES_DIR: C:/Users/Rami/.dbt`**, a PROTECTED path that outranks the fix. ⚠ Deliberately
**no `prod` target** in the local profile: a prod target needs `dataset: dbt_analytics`, the line
that overwrites prod's base tables and seeds if a build ever selects one. Meanwhile `dbt ls` /
`parse` / `compile` work with a throwaway profile in the scratchpad (`DBT_PROFILES_DIR`, target
`dev_scratch`) — `~/.dbt/profiles.yml` currently holds ANOTHER project's profile; never edit it.

## ⛔ OPEN — DEFECTS TO FIX (not decisions to wait on)

  - **#110 — a forfeit the provider labels `FT`** with a score and no stat line, so 18 of 19 Süper
    Lig 2022 team-seasons are blank. The other 435 blanked team-seasons are CORRECT (measured: of
    9,515 fixtures with no team statistics, ZERO have any in the raw payload). The fix needs a
    competition-relative signal, not a blanket rule. Everything measured is on the issue.
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
    `1f822a2` chunks the `RAW_APIF_PLAYERS` snapshot under BigQuery's 100MB per-row limit (UEL
    81.8MB / UCL 78.7MB when written). Settle superseded-or-abandoned before those rosters grow.
  - **#101** carries its season trap on the issue now (recorded 2026-09-13).
  - **#99 / #102 / #96 / #98** — export board keys pinned by no test; `mart_leaderboards` is
    player-only under an unprefixed name; no offline gate checks `accepted_values`.

## ⛔ WHAT ACTUALLY FINDS DEFECTS — the blinded review and CI, almost never a gate

Across `!156`/`!157`/`!159` (13 rounds) and `!191` (5 rounds) every FAIL came from a reviewer or
the pipeline; parse, lint and the offline gates were green over all of them. **Almost every
defect was a claim asserted without opening the file** — open it, do not recall it. A class recurs
until the RIGHT tree is swept, two-sided ("1 moves, 4 stay"); mutation-test against the mutation
the design is defended against; a reviewer's flagged-but-not-failed trade-off is still a trade-off;
**rewrite the design, rewrite the paperwork** (acceptance criteria describing a previous design
were found by reviewers on `!159` and on `!191`). What `!191` added: an invented locale format
(a German score colon) with no authority; a catalogue flag set against its own direction; a
`ruff` finding only CI runs.

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
