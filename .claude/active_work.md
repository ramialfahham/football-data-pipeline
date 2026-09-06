# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-09-06**. **main `3ed9569`**, clean, **no open MRs** — !150, !151, !152 and
**!153** all merged. **GITLAB** (`glab`, MRs). Branches swept 2026-09-04: 63 remote + 22 local
deleted; 6 remote and 2 local remain, each kept for a reason (`backup/27-pre-rebase` holds 15 unique
commits). Check one with `git cherry`, never `--is-ancestor` — see TRAPS.
⛔ **THE POST-COMMIT HOOK PUSHES TO `main` IF THE BRANCH TRACKS `main`, AND IT TRIED TO ON !151.**
`git checkout -b <branch> gitlab/main` sets `main` as upstream, so the hook's bare push follows it;
branch protection rejected it. **Run `git branch --unset-upstream` right after creating a branch**,
and push with an explicit refspec `git push gitlab <b>:<b>`, verifying the output says `-> <b>`.
⛔⛔ **DO NOT TOUCH `glab auth` OR INSTALL A PROJECT TOKEN. 2026-09-03 cost a full day.** It is ONE
credential per MACHINE, shared by every repo — re-authing it to a project token broke
`claude-guardrails` and another repo. Reverted; `glab` is `rami.al-fahham` again. The safeguard that
the agent never merges is **branch protection** (main = Maintainers-only) plus the memory rule
**never merge**; NOT a token, NOT a hook.
⛔ **THE `fix/merge-guard-covers-the-api` BRANCH IS DEAD** — 11 review rounds hardening a text hook
against shell spellings, judged over-engineering, DISCARDED. The one-line `_MR_MERGE` guard on main
is fine as-is.
⛔⛔ **CI HAS NO FALLBACK SINCE 2026-09-02.** `shared_runners_enabled=false`, so **`ci-runner-01` is
the ONLY runner** — a dead box means pipelines QUEUE, they do not fail over. Turned off because
"CI costs zero GitLab minutes" was **false for three weeks**: nothing in `.gitlab-ci.yml` is tagged
and the runner takes untagged jobs, so **96 of 100 jobs went to GitLab's shared fleet**. Standing a
runner up does not move the work to it. ⭐ Both things that made that scary are FIXED 2026-09-03:
the IPv6 address is **deleted at Hetzner**, and root SSH by key works again (`/dev/sda1` is root).
⚠ `~/.ssh/id_ed25519` is **PASSPHRASE-PROTECTED**, so `ssh -o BatchMode=yes` cannot log in — it
fails `Permission denied (publickey)` even though the server accepts the key. Not a broken key.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⛔ NEXT ACTION: **#40 MR B — unstash and finish the Top players block**

⭐⭐ **#40 IS PLANNED AND HALF MERGED, AND MR B IS NO LONGER BLOCKED.** !153 shipped the warehouse
half — `is_current_season` on `mart_leaderboards` plus two DQ guards — and the nightly has since put
it in prod. **Measured 2026-09-06: 189,400 rows, 42,646 flagged, 45 of 45 leagues with exactly one
flagged season.** So step 1 of the old plan is DONE; start at step 2.
The block itself is **WRITTEN AND PARKED** in the stash **`TEMP-40-mrB`** — export shaper
`shape_home_top_players` (15 unit tests), `TopPlayers.astro`, the `.board`/`.brow` CSS,
`LandingBoard` types, and copy in three locales.

  1. `git stash pop` the `TEMP-40-mrB` entry — **match it by MESSAGE, never by index**; the stack is
     shared and holds 8 other parked WIPs.
  2. Write a contract for MR B, wire `TopPlayers.astro` into `index.astro`, and build the **player
     scaffold** (`pages/*/players/*.astro` + a `stub: true` spec + a `STUB_PAGES` entry), as !151 did
     the competition page — `players` is already an export entity with `shape_player_payload` and a
     `player_slug_with_id` helper. ⚠ Without it `audit-seo.mjs` check 8 fails the build: every board
     row links to a player page.
  3. Re-export `landing.json`, then VERIFY AT 375px AS WELL AS DESKTOP. !151 shipped a 21px tap
     target and a focus ring through a divider, both invisible at desktop width.

⚠ **#40's issue body is STALE and must not be followed literally**: it describes a POOLED ranking
across seven leagues, withdrawn 2026-08-18 (GAP-31) for **one player per league**. The rule it
justified — every row shows club AND league — still stands. Page length is NOT open either
(`10_home.md:392-396`, settled by the 2026-08-10 reduction to four boards at seven rows).
⚠ **The DE/FI board labels in the stash NEED THE CPO'S CONFIRMATION.** They are written rather than
omitted because `metricLabel()` falls back to English and then to EMPTY, so a missing Finnish label
renders a blank board title.
⭐ **A real question for #101's rotation MR**, found while building: a league whose new season has
started but has no FINISHED matches produces no rows upstream, so `is_current_season` falls back to
the last season WITH data — the block would show last season's leaders under a heading reading
"Season totals to date". #101's in-season gate (">= 3 finished games") is what settles it.
⚠ **#100** proposes rewriting `10_home.md` wholesale; **#103** = two stale summary lines in it.

## ⭐ WHAT !151 ESTABLISHED — read before touching any page

**The navigation rule is now written**, in `docs/site_architecture.md` §3 — read it there, it is not
duplicated here. It is **PROVISIONAL** by the CPO's instruction (*"the rules might be subject to
change. We have not built every page yet"*), and confirmed for header+row structures, which is what
both Home blocks are. The four rulings behind it are in `escalations.log`
(entry `2026-09-04 — THE NAVIGATION RULE`).
⭐ **The competition page exists as a SCAFFOLD** (`/{lang}/{slug}/`, 144 pages, in `STUB_PAGES`); its
content is **#47**. The competitions index page's 48 rows are still inert but now UNBLOCKED.
⚠ **Competition names were corrected in the warehouse (!150).** `league_name_overrides` →
`base_apif__leagues` → `dim_league`; 20 corrected, 28 on the provider name. Verifying all 48 against
external records is **#55**, which also owns removing the export's registry reads. **#105** =
compose name + season so an active World Cup reads "FIFA World Cup 2026".
⭐⭐ **#101 DECIDED 2026-09-03** (recorded as a comment ON THE ISSUE — read it):
each nightly build picks ONE `competition_group` slot by **weighted random over the IN-SEASON
slots** — `elite` 60 / `europe`+`international` merged 20 / `calendar` 20; `secondary` never.
"In season" = a slot has ≥1 league with ≥3 finished games this season. Both blocks show the same
slot; each names its leagues. **Fallback:** `elite`'s last completed season + a DQ alert. The
mechanism lives in export/warehouse, never a component. Unblocks #40/#41.
⚠ `mart_leaderboards` is player-only under an unprefixed name — **#102** proposes renaming it to
`mart_player_leaderboards`; do NOT fold that into #40.

⭐ **THE NIGHTLY LIVES IN CLOUD SCHEDULER — answered, not open.** Detail in `CLAUDE.md` and
`deploy/nightly/README.md`. ⚠ The one trap worth repeating: `data:nightly` in `.gitlab-ci.yml` is
NOT the nightly, and enabling GitLab schedule `4379625` without disabling `fdp-nightly` runs the
prod build TWICE.

## ⛔ A PRODUCTION FIX THAT NEVER LANDED (found in the 2026-09-04 branch sweep)

⛔⛔ **`fix/raw-players-row-chunking` is UNMERGED and its mechanism is ABSENT from main** — which is
why the branch is kept. Commit `1f822a2` chunks the `RAW_APIF_PLAYERS` snapshot under **BigQuery's
100MB per-row limit**, citing a real failure: *"LIBER failed… UEL 81.8MB / UCL 78.7MB imminent."*
On main: `tests/test_squad_players_chunking.py` does NOT exist and `ingestion/` has no
`chunk`/`MAX_ROW`/`100MB` — yet `tests/fixtures/apif/players_cwc_sample.json` DOES. Fixture landed,
fix did not. **Settle superseded-or-abandoned before those rosters grow.**

## ⛔ CARRIED, LOW PRIORITY (not blocking #40)

  - **Naming programme leftover — 7 seed rows («on-target shots» ×4, «on-target threat» ×3, plus
    «on-target dominance» and «on target for−against») on ONE CPO copy call.** Recommendation given:
    **LEAVE THEM** — no natural "on-goal" phrasing exists, so it is a defensible end state, not debt.
    ⚠ `label_i18n_key` (`metrics.shots_on_target_per_match.label`) STAYS regardless — it is the join
    key, and "fixing" it resolves to nothing.

## ⛔ OPEN, AND THE CPO'S — carried, never decided

  - ⭐ **The `__team`/`__player` doc-block split has NO live instance** — all six dual-entity ids were
    renamed player-side, though one new seed row recreates the collision and five files still
    document it with a falsified example. Whether a guard with no live instance stays is his call.
  - **A rename frees a name from #87 only when no PROVIDER column shares it** — measured twice, the
    ambiguous list went 4 → 3, not 4 → 1. **#87's 49 blank columns are NOT freed by this programme.**
  - **#99 / `_LEADERBOARD_METRICS` / `_LB_KEEP`** — the export's literal board keys moved in `!132`
    and are pinned by NO test (`platform-reviewer`, five MRs); nor is `shape_top_players`' DROP-list,
    so `TopPlayer` fields reach the frontend with no test between mart and component.
  - **#96** — no offline gate checks `accepted_values`, only `data:build:mr`. **#98**; the doc-block
    inheritance trap.

## ⛔ WHAT THE SWEEP MRs PROVED — read before any similar rename or text sweep

Programme merged; the MR-by-MR account is in git and `feedback_fix_the_class_not_the_instance`.
What survives is the method.

**1. A SCOPE COARSER THAN THE ROLE IT MUST RESOLVE IS THE ONE RECURRING DEFECT** — FAILed review on
`!131`, `!132` (×3), `!134`, `!140`, **every gate green every time**. The fix is never an exemption
list; it is a finer rule with a checkable property — resolve by **ROLE** (`t(lang,"x")` is a UI
word, `.get("x")` a warehouse column, `"x":` a payload key), by a **domain fact** where one exists,
and in a markdown TABLE by the COLUMN, not the backtick.

**2. CENSUS THE TREE, COUNT BOTH DIRECTIONS, MATCH A PATTERN NOT A LIST.** Report every sweep as
"N move, M stay", and run the assertion against BASE as well as HEAD. ⚠ **A too-narrow census
reports a confident ZERO, never an error** — `\b` does not delimit `on` in `shots_on_target` (`_` is
a word character) and camelCase has no separator at all. ⭐⭐ **THREE DETECTORS, THREE JOBS** —
(1) DECIDES: strict. (2) COUNTS: maximally permissive. (3) JUDGES prose only. Collapsing any two
broke the sweep once each. **3. ALLOWLIST, NEVER BLOCKLIST, and nothing may be checked before it** —
a token rule placed ahead of the allowlist silently reopens the hole (`!132`, `!136`).

**4. WHAT ACTUALLY FINDS DEFECTS**, in order: the **blinded review**; reading the printed decisions
and the applied diff; then the test suite — but only where a ruling forces code and test apart.
⭐ Reconfirmed on !150, !151 and !153: **every** FAIL was found by a reviewer, none by me, and three
were real defects behind a green build (a 21px tap target, a focus ring through a divider, and a DQ
guard that passed a broken model).

**5. TWO GUARD FACTS, MEASURED.** `check_description_hygiene` DOES catch a dangling `doc()`.
`check_yml_vs_projection` does NOT catch a column dropped from the final SELECT while still named in
a `safe_divide` on it — token presence, not projection. Mutation-test any guard before citing it.
⛔⛔ **AND MUTATION-TEST AGAINST THE MUTATION THE DESIGN IS DEFENDED AGAINST, NOT THE ONES THAT COME
TO MIND. Twice now, the mutations I chose could not change the answer, so they tested nothing.**
!151: a fixture with one case per level cannot distinguish `max` from `min`. !153, one level deeper:
`assert_one_current_season_per_league` checked how many seasons carried the flag and which one — so
reverting the model's `rank()` to `row_number()` left it **GREEN while the flag was false on 711 of
712 rows**, the exact mutation the contract calls the whole reason for choosing `rank()`. Both found
by a reviewer READING the test, neither by running it. A third mutation of mine (`rank() <= 2`) was
inert — `rank()` skips, so it flags nothing new. **Read the result, don't assume the mutation bit.**

## ⛔ TRAPS THAT COST REAL TIME

⛔⛔ **"MERGED" IS A CLAIM TO VERIFY, and `--is-ancestor` IS NOT THE CHECK.** Told "140 merged", I
ran cleanup without checking; it had NOT landed, and **deleting an open MR's source branch CLOSES
the MR on GitLab.** ⚠ `git merge-base --is-ancestor` is WRONG for a squash-merged branch — on
2026-09-04 it called 20 of 22 fully-landed branches unmerged, and `git branch -d` refuses them for
the same reason; a diff-based check is useless too, main's own progress dominates it.
⭐ **The only correct check is `git cherry gitlab/main <branch>`** — `+` = patch not upstream,
`-` = already applied. Always `git fetch gitlab` first, and check for OPEN MRs before deleting.
⚠ **`git pull` on main hits the DEAD GitHub `origin` and 403s.** Use `git pull --ff-only gitlab main`.
⚠ **The push guard refuses EVERY push while standing on main**, including deleting a merged branch.
Branch off main to a throwaway (`git checkout -b tmp/…`) to push deletions, then come back. It is a
PreToolUse hook reading the CURRENT branch, so `checkout && push` in one call is blocked as a whole.
⚠ `git checkout -- .` reverts the CONTRACT too if it is unstaged — exclude it explicitly.
⛔⛔ **`--review-patch` PRINTS; only a REDIRECT writes the file, and it reads the INDEX.** Run bare
it emits to stdout and **leaves the previous round's `review_input.patch` on disk**, exit 0 — on
`!132` that served every reviewer the ROUND-1 diff and two FAILed on already-fixed defects; it
happened AGAIN on `!151`. Correct call: `git add -u`, then
`… --review-patch > .claude/task/review_input.patch`. Re-read this before every round.
⭐ Free tell: `--staged-hash` printing `e3b0c442…` = `sha256("")`, an empty staged diff.
⭐ **When two reviewers contradict each other on the same tokens, suspect the ARTIFACT before the
code.**
⚠ **CP1252, NOT UTF-8, IN BOTH DIRECTIONS on this machine.** `subprocess.run(..., text=True)` decodes
with the Windows locale (a byte-identical seed looked like 32 corrupted fields), and the `bq` CLI's
own CSV output is cp1252 too (`Süper Lig` arrives as a bare `0xFC`, so a UTF-8 decode RAISES).
Capture BYTES and decode explicitly, utf-8 first with a cp1252 fallback.

## Method that works — seven MRs of evidence

Contract FIRST on a clean tree (stash by explicit path with a `TEMP-` label, verify your entry is on
top, pop immediately). Then gates unpiped with exit codes read bare, mutations watched RED, the site
built, blinded reviewers, `review.md` with `--staged-hash`.
**ROUND CAP 3** — past it STOP and bring the findings; a fourth needs the CPO's word as
`rounds_cap_override:`, as !153 has (*"all rounds were fixes not disagreements"* — the distinction
the cap exists to test). ⚠ Rounds are PER REVIEWER and differ (!151: scope 3, platform 3, BI 4). Each
section needs `## <exact-routing-key>`, `VERDICT:`, then `risks_checked:` — an empty one is rejected.
⚠ **`contract.md` is INSIDE the review hash**; amending it after the reviewers ran voids every
verdict. Amend BEFORE the round.

## Standing traps (also in CLAUDE.md)

`git commit` SOLE in its Bash call, heredocs gate-blocked, `review.md` must be COMMITTED, contract
edits need a CLEAN tree, never read a gate's exit code through a pipe — all in `CLAUDE.md`. The one
that is NOT: `acceptance_evidence.md` needs a `criteria_demonstrated:` marker **at column 0**
— `## criteria_demonstrated:` is invisible to the parser (it matches `^criteria_demonstrated:`),
which reads as "0 of N demonstrated" — with one 15+ character bullet per declared criterion.
