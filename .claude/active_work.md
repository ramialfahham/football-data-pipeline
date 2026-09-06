# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-09-04**. **main `448ef77`**, clean, **no open MRs** (!150 and !151 both merged).
**GITLAB** (`glab`, MRs). Branches swept 2026-09-04: 63 remote + 22 local deleted; 6 remote and 2
local remain (`backup/27-pre-rebase` holds 15 unique commits). How to check one is in TRAPS below.
⛔ **THE POST-COMMIT HOOK PUSHES TO `main` IF THE BRANCH TRACKS `main`, AND IT TRIED TO ON !151.**
`git checkout -b <branch> gitlab/main` sets `main` as upstream, so the hook's bare push follows it.
Branch protection rejected it (`! [remote rejected] … -> main`). **Run `git branch --unset-upstream`
right after creating a branch**, and always push with an explicit refspec
`git push gitlab <branch>:<branch>`, verifying the output says `-> <branch>`.
⛔⛔ **DO NOT TOUCH `glab auth` OR INSTALL A PROJECT TOKEN. 2026-09-03 cost a full day.** `glab` auth
is ONE credential per MACHINE, shared by every repo — re-authing it to a project access token broke
`claude-guardrails` and another repo. Reverted; `glab` is `rami.al-fahham` again. The safeguard that
the agent never merges is **branch protection** (main = Maintainers-only) + the hard memory rule
**never merge**; NOT a token, NOT a hook. → [remove-the-permission], [never-merge] in memory.
⛔ **THE `fix/merge-guard-covers-the-api` BRANCH IS DEAD** — 11 review rounds hardening a text hook
against shell spellings, judged over-engineering, DISCARDED. Do not resurrect it. The one-line
`_MR_MERGE` guard on main is fine as-is.
⛔⛔ **CI HAS NO FALLBACK SINCE 2026-09-02.** `shared_runners_enabled=false`, so **`ci-runner-01` is
the ONLY runner** — a dead box means pipelines QUEUE, they do not fail over. Turned off because
"CI costs zero GitLab minutes" was **false for three weeks**: nothing in `.gitlab-ci.yml` is tagged
and the runner takes untagged jobs, so **96 of 100 jobs went to GitLab's shared fleet**. Standing a
runner up does not move the work to it.
⭐ **Both things that made that scary are FIXED 2026-09-03**: the IPv6 address is **deleted at
Hetzner** (so no IPv6 route can return after a reboot), and root SSH by key works again (restored
via rescue; `/dev/sda1` is the root fs).
⚠ `~/.ssh/id_ed25519` is **PASSPHRASE-PROTECTED**, so `ssh -o BatchMode=yes` cannot log in — it
fails `Permission denied (publickey)` even though the server accepts the key. Not a broken key.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⛔ NEXT ACTION: **#40 needs a PLAN before any code** (Home page, Top players)

⛔⛔ **DO NOT START BUILDING #40 FROM THE ISSUE TEXT.** The CPO stopped exactly that on 2026-09-04:
*"we have no plan yet for top players and top teams."* Start from the MOCK, not the issue. Open
`design-mocks/top_players_mock.html` (outside the repo, beside the memory folder) and settle these
FIRST, with him:
  · **Page length** — 4 player boards + 4 team boards at 7 rows = 56 rows, on a page that already
    measured 4126px on mobile with ONE block built. Still open in `10_home.md` §0.
  · **#40's issue body is STALE.** It describes a POOLED ranking across seven leagues; that was
    withdrawn 2026-08-18 (GAP-31) for **one player per league**, which `mart_leaderboards` already
    produces. Its intro copy was replaced the same day. The spec's §0/§10 win over the issue.
  · **#101's group rotation** is decided but unwired. **#100** proposes rewriting `10_home.md`
    wholesale; **#103** = two stale summary lines in it.
⭐ Data is READY: `mart_leaderboards` has all four boards (`goals_player`, `assists_player`,
`passes_player`, `passes_key_player`) plus `team_sk`/`team_name`/`team_slug`/`team_logo_url` and a
per-league `dense_rank`. Sibling `mart_team_leaderboards` feeds **#41**.
⛔ **There is NO player page and no player route**, so Top players rows have no destination yet.
Under the navigation rule below, a row links to its SUBJECT — the player. Per §0's standing rule
(*"do not reorder the build because a destination page does not exist yet"*) that means shipping a
player scaffold alongside the block, exactly as !151 did for the competition page. `players` is
already an export entity with `shape_player_payload` and a `player_slug_with_id` helper, so the
route is cheap and mirrors `teams/[team].astro`.

## ⭐ WHAT !151 ESTABLISHED — read before touching any page

**The navigation rule is now written**, in `docs/site_architecture.md` §3, and it is **PROVISIONAL**
by the CPO's instruction (*"the rules might be subject to change. We have not built every page
yet"*). Three families — chrome / content links / controls, and **only two navigate**. Four
content-link shapes: row · heading · chip · prose. The rule: *every content link points at the one
entity it names, and a row names its subject; nothing inside a row is separately clickable.*
Confirmed for header+row structures, which is what both Home blocks are. The four rulings behind it
are in `escalations.log` (entry `2026-09-04 — THE NAVIGATION RULE`).
⭐ **The competition page exists as a SCAFFOLD** (`/{lang}/{slug}/`, 144 pages, in `STUB_PAGES`).
Its content is **#47**. The competitions index page's 48 rows are still inert but now UNBLOCKED —
a second surface, deliberately left out of !151.
⚠ **Competition names were corrected in the warehouse (!150, merged).** `league_name_overrides` →
`base_apif__leagues` → `dim_league`. 20 corrected, 28 on the provider name. The remaining
external-record verification of all 48 belongs to **#55**, which also owns removing the export's
registry reads. **#105** = compose name + season so an active World Cup reads "FIFA World Cup 2026".
⭐⭐ **#101 DECIDED 2026-09-03** (recorded as a comment ON THE ISSUE — read it):
each nightly build picks ONE `competition_group` slot by **weighted random over the IN-SEASON
slots** — `elite` 60 / `europe`+`international` merged 20 / `calendar` 20; `secondary` never.
"In season" = a slot has ≥1 league with ≥3 finished games this season (the benchmark gate). Both
blocks show the same slot; each names its leagues. **Fallback:** if nothing qualifies, show `elite`'s
last completed season + a DQ alert. Guarantee holds because split-year (~Sep–May) and calendar-year
(~Mar–Nov) tile the year. The mechanism lives in export/warehouse, never a component. Unblocks #40/#41.
⚠ Related design facts in memory: `mart_leaderboards` is player-only under an unprefixed name
(**#102** proposes renaming to `mart_player_leaderboards` — do NOT fold into #40); **#103** = two
stale summary lines in `10_home.md`.

⭐ **THE NIGHTLY LIVES IN CLOUD SCHEDULER — answered, not open.** Detail in `CLAUDE.md` and
`deploy/nightly/README.md`; not duplicated here. ⚠ The one trap worth repeating: `data:nightly` in
`.gitlab-ci.yml` is NOT the nightly, and enabling GitLab schedule `4379625` without disabling
`fdp-nightly` runs the prod build TWICE.

## ⛔ A PRODUCTION FIX THAT NEVER LANDED (found in the 2026-09-04 branch sweep)

⛔⛔ **`fix/raw-players-row-chunking` is UNMERGED and its mechanism is ABSENT from main** — which is
why the branch is kept. Commit `1f822a2` chunks the `RAW_APIF_PLAYERS` snapshot under **BigQuery's
100MB per-row limit**, citing a real failure: *"LIBER failed… UEL 81.8MB / UCL 78.7MB imminent."*
On main: `tests/test_squad_players_chunking.py` does NOT exist and `ingestion/` has no
`chunk`/`MAX_ROW`/`100MB` — yet `tests/fixtures/apif/players_cwc_sample.json` DOES. Fixture landed,
fix did not. **Settle superseded-or-abandoned before those rosters grow.** (4 other branches held
back; `fix/transfers-drop-bl1-hardcode` is verified landed, the rest superseded or shipped.)

## ⛔ CARRIED, LOW PRIORITY (not blocking #40)

  - **Naming programme leftover — 7 seed rows on ONE CPO copy call.** «on-target shots» ×4 ·
    «on-target threat» ×3 · «on-target dominance» ×1 · «on target for−against» ×1. Recommendation
    given: **LEAVE THEM** — no natural "on-goal" phrasing exists, so it is a defensible end state,
    not debt. Until decided, `shots_on_goal_player` keeps label "Shots on goal" / desc "Shots on
    target". ⚠ `label_i18n_key` (`metrics.shots_on_target_per_match.label`) STAYS — it is the join
    key and "fixing" it resolves to nothing. Four `strings.ts` chrome strings (`axPlay`,
    `heroVerdict*`, `heroCaption`) name the same metric and render on zero pages today.

## ⛔ OPEN, AND THE CPO'S — carried, never decided

  - ⭐ **The `__team`/`__player` doc-block split has NO live instance** — all six dual-entity ids were
    renamed player-side, though one new seed row recreates the collision and five files still
    document it with a worked example the programme falsified. Whether a guard with no live
    instance should remain is his call.
  - **A rename frees a name from #87 only when no PROVIDER column shares it** — measured twice, the
    ambiguous list went 4 → 3, not 4 → 1. **#87's 49 blank columns are NOT freed by this programme.**
  - **#99** — the export's literal board keys moved in `!132` and remain pinned by NO test.
  - **`_LEADERBOARD_METRICS` / `_LB_KEEP`** pinned by no test (`platform-reviewer`, five MRs), and
    so is the other export path — `shape_top_players`' DROP-list means `TopPlayer` fields reach the
    frontend with no test between mart and component.
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
"N move, M stay". ⛔⛔ One phrase had FOUR spellings in one file and my regex was wrong five times,
four too narrow then one too wide. ⚠ **A too-narrow census reports a confident ZERO, never an
error.** `\b` does not delimit `on` in `shots_on_target` (`_` is a word character); camelCase has no
separator at all. ⭐⭐ **THREE DETECTORS, THREE JOBS** — (1) DECIDES: strict. (2) COUNTS: maximally
permissive. (3) JUDGES prose only. Collapsing any two broke the sweep once each.
⭐ **Run every such assertion against BASE as well as HEAD** — mine was an absolute that main already
violated. Two-sided is the only form an MR can own: introduced 0, removed 0.

**3. ALLOWLIST, NEVER BLOCKLIST — AND NOTHING MAY BE CHECKED BEFORE IT.** A token rule placed BEFORE
the allowlist silently reopens the hole (`!132`, `!136`).

**4. WHAT ACTUALLY FINDS DEFECTS**, in order: the **blinded review** (every defect of the last five
MRs, all with gates green); reading the printed decisions and the applied diff; then the test suite
— but only where a ruling forces code and test apart. Where a sweep edits both sides in lockstep,
green means nothing. ⭐ Reconfirmed on !150/!151: **every** FAIL was found by a reviewer, none by me,
and two were product defects (a 21px tap target, a focus ring through a divider) behind a green build.

**5. TWO GUARD FACTS, MEASURED.** `check_description_hygiene` DOES catch a dangling `doc()`.
`check_yml_vs_projection` does NOT catch a column dropped from the final SELECT while still named in
a `safe_divide` on it — token presence, not projection. Mutation-test any guard before citing it.
⚠ **And mutation-test against more than the mutation you thought of**: a fixture with one case per
level cannot distinguish `max` from `min`, so my tie-break test pinned nothing until a reviewer said so.

## ⛔ TRAPS THAT COST REAL TIME

⛔⛔ **"MERGED" IS A CLAIM TO VERIFY, NOT A FACT TO ACT ON**, and **`--is-ancestor` IS NOT THE
CHECK.** Told "140 merged", I ran cleanup without checking; it had NOT landed, and **deleting an
open MR's source branch CLOSES the MR on GitLab.** Recovered from the reflog. ⚠ The check this
entry used to recommend, `git merge-base --is-ancestor`, is WRONG for a squash-merged branch: on
2026-09-04 it called 20 of 22 fully-landed branches unmerged, and `git branch -d` refuses them for
the same reason. A diff-based check is useless too — main's own progress dominates it.
⭐ **The only correct check is `git cherry gitlab/main <branch>`** — `+` = patch not upstream,
`-` = already applied. Always `git fetch gitlab` first, and check for OPEN MRs before deleting.
⚠ **`git pull` on main hits the DEAD GitHub `origin` and 403s.** Use `git pull --ff-only gitlab main`.
⚠ **The push guard refuses EVERY push while standing on main**, including deleting a merged branch.
Branch off main to a throwaway (`git checkout -b tmp/…`) to push deletions, then come back. It is a
PreToolUse hook reading the CURRENT branch, so `checkout && push` in one call is blocked as a whole.
⚠ `git checkout -- .` reverts the CONTRACT too if it is unstaged — exclude it explicitly.
⛔⛔ **`--review-patch` PRINTS; only a REDIRECT writes the file, and it reads the INDEX.** Running it
bare emits to stdout and **leaves the previous round's `review_input.patch` on disk**, exit 0 — on
`!132` that served every reviewer the ROUND-1 diff, and two FAILed on already-fixed defects. Correct
call: `git add -u` then `… --review-patch > .claude/task/review_input.patch`. ⚠ It happened AGAIN on
`!151` (staged without regenerating), caught by a reviewer, so re-read this before each round.
⭐ Free tell: `--staged-hash` printing `e3b0c442…` = `sha256("")`, an empty staged diff.
⭐ **When two reviewers contradict each other on the same tokens, suspect the ARTIFACT before the
code.**
⚠ **CP1252, NOT UTF-8, IN BOTH DIRECTIONS on this machine.** `subprocess.run(..., text=True)`
decodes with the Windows locale, so `Ø` arrives as `Ã˜` and a byte-identical seed looked like 32
corrupted fields — and the `bq` CLI's own CSV output is cp1252 too (`Süper Lig` arrives as a bare
`0xFC`, so a UTF-8 decode RAISES). Capture BYTES and decode explicitly, utf-8 first with a cp1252
fallback.

## Method that works — seven MRs of evidence

Contract FIRST on a clean tree (stash by explicit path with a `TEMP-` label, verify your entry is on
top, pop immediately). Then gates unpiped with exit codes read bare, mutations watched RED, the site
built, blinded reviewers, `review.md` with `--staged-hash`.
**ROUND CAP 3** — past it STOP and bring the findings; a fourth needs the CPO's word as
`rounds_cap_override:`. ⚠ Rounds are PER REVIEWER and differ (!151: scope 3, platform 3, BI 4). Each
section needs `## <exact-routing-key>`, `VERDICT:`, then `risks_checked:` — an empty one is rejected.
⚠ **`contract.md` is INSIDE the review hash**; amending it after the reviewers ran voids every
verdict. Amend BEFORE the round.

## Standing traps (also in CLAUDE.md)

`git commit` SOLE in its Bash call. Heredocs gate-blocked for file writes — use Edit/Write.
`review.md` must be COMMITTED. Contract edits need a CLEAN tree. Never read a gate's exit code
through a pipe. ⚠ `acceptance_evidence.md` needs a `criteria_demonstrated:` marker **at column 0**
— `## criteria_demonstrated:` is invisible to the parser (it matches `^criteria_demonstrated:`),
which reads as "0 of N demonstrated" — with one 15+ character bullet per declared criterion.
