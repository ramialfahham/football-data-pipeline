# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-09-04**. **main `56278d5`**, clean. **ONE OPEN MR: !151** (navigation rule +
competition scaffold) — awaiting the CPO's merge. **GITLAB** (`glab`, MRs).
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

⭐ **THE NIGHTLY LIVES IN CLOUD SCHEDULER — answered, not open. Runbook `deploy/nightly/README.md`.**
Two ENABLED jobs in **europe-west1**: `fdp-nightly` (`0 4 * * *`, ingest + full prod dbt build) and
`fdp-freshness` (`7 * * * *`). **The data IS refreshed on a timer.**
⚠ `data:nightly` in `.gitlab-ci.yml` is NOT it — nothing triggers it; GitLab schedule `4379625` is
deliberately **DISABLED**. **Enabling it without disabling `fdp-nightly` runs the build twice.**
⚠ Cost **~129 GB/day ≈ $17–24/mo**. Whether `fdp-freshness` needs hourly runs is the CPO's.
⚠ Query `region-eu.INFORMATION_SCHEMA.JOBS_BY_PROJECT` — **EU, not US**; `region-us` returns a
false "0 jobs". (The 2026-09-01 cost-investigation lessons live in `CLAUDE.md` and memory.)

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
    renamed player-side. ⛔ Nothing was removed or weakened, and one new seed row recreates the
    collision. ⚠ But **five files document it with a worked example the programme falsified.**
    Whether a guard with no live instance should remain is his call.
  - **A rename frees a name from #87 only when no PROVIDER column shares it** — measured twice, the
    ambiguous list went 4 → 3, not 4 → 1. **#87's 49 blank columns are NOT freed by this programme.**
  - **The column-reference resolver as a committed CI gate.** `!129`–`!131` bounded it (dotted refs
    only; the projection check's weak form). Not proposed.
  - **#99** — the export's literal board keys moved in `!132` and remain pinned by NO test.
  - **`_LEADERBOARD_METRICS` / `_LB_KEEP`** pinned by no test (`platform-reviewer`, five MRs).
    ⭐ `!131`: the OTHER export path is unpinned too — `shape_top_players`' DROP-list means
    `TopPlayer` fields reach the frontend with no test between mart and component.
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

⛔⛔ **"MERGED" IS A CLAIM TO VERIFY, NOT A FACT TO ACT ON.** Told "140 merged", I ran cleanup
without checking; it had NOT landed, and **deleting an open MR's source branch CLOSES the MR on
GitLab.** Recovered from the reflog. ⭐ **Before deleting anything:** `git fetch gitlab` then
`git merge-base --is-ancestor <sha> gitlab/main`.
⚠ **`git pull` on main hits the DEAD GitHub `origin` and 403s.** Use `git pull --ff-only gitlab main`.
⚠ **The push guard refuses EVERY push while standing on main**, including deleting a merged branch —
so delete the remote branch BEFORE checking out main. It is a PreToolUse hook reading the CURRENT
branch, so `checkout && push` in one call is blocked as a whole; they must be separate calls.
⚠ **CWD persists between Bash calls** — a `cd` in one call breaks repo-relative paths in the next;
it aborted an apply mid-run on `!131` and again on `!132`.
⚠ `git checkout -- .` reverts the CONTRACT too if it is unstaged — exclude it explicitly.
⚠ A file that falls to ZERO renames is never reopened by the no-op-write guard, so it keeps its
previous text: restore it from base explicitly and re-reconcile `scope_paths`.
⚠ `git grep` is BRE — `[` opens a character class, so `git grep 'values: ['` silently finds nothing.
Use `-F`.
⛔⛔ **`--review-patch` PRINTS; only a REDIRECT writes the file — and it reads the INDEX, not the
working tree.** `git_discipline.py --review-patch` builds from `git diff --staged <base>`, so running
it bare emits to stdout and **leaves the previous round's `review_input.patch` on disk**, exit 0. On
`!132` that served all five reviewers the ROUND-1 diff: two FAILed on defects already fixed, quoting
offsets that no longer existed. Correct call: `git add -u` then
`… --review-patch > .claude/task/review_input.patch`.
⭐ **The tell is free: `--staged-hash` printing `e3b0c442…`** = `sha256("")`, an empty staged diff.
Never write it into `review.md`.
⭐ **When two reviewers contradict each other on the same tokens, suspect the ARTIFACT before the
code.** One reading files said clean, one reading the patch said corrupted; that resolved it in one
step.
⚠ **`subprocess.run(..., text=True)` decodes with the WINDOWS locale (cp1252), not UTF-8**, so `Ø`
arrives as `Ã˜` and a byte-identical seed looked like 32 corrupted fields. Capture BYTES and
`.decode("utf-8")` both sides; the seed's `label_en` is full of `Ø`.

## Method that works — seven MRs of evidence

Contract FIRST on a clean tree (the gate refuses otherwise; stash by explicit path with a `TEMP-`
label, verify your own entry is on top, pop immediately). Abort before writing on any
protected-count change or unlisted file. Then gates unpiped with exit codes read bare, mutations
watched RED, the site built, the blinded reviewers, `review.md` with `--staged-hash`.
**ROUND CAP 3** — past it STOP and bring the findings; a fourth round needs the CPO's word as
`rounds_cap_override:` in `review.md` or the commit gate refuses. ⚠ Rounds are PER REVIEWER and can
differ (on !151: scope 3, platform 3, BI 4). Each section needs `## <exact-routing-key>`, then
`VERDICT:`, then a `risks_checked:` block — a PASS with an empty one is rejected.
⚠ **`contract.md` is INSIDE the review hash**, so amending it after the reviewers ran invalidates
every verdict. Amend before the review round, not after.

## Standing traps (also in CLAUDE.md)

`git commit` must be the SOLE command in a Bash call. Heredocs are gate-blocked for file writes —
use Edit/Write. `review.md` must be COMMITTED. `acceptance_evidence.md` needs a
`criteria_demonstrated:` block with one 15+ character bullet per declared criterion. Contract edits
need a CLEAN tree. Never read a gate's exit code through a pipe.
