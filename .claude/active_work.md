# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-09-03**. **main `66e4ca9`**, clean, **no open MRs**.
**GITLAB** (`glab`, MRs).
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

## ⛔ NEXT ACTION: BUILD **#40 — the Top players block** (Home page)

⭐ Home's warehouse is DONE and #101 (which group renders) is DECIDED. Next is pure build work: the
Top players block. Its data source exists — **`mart_leaderboards`** (per-league player boards; the
reduced design is goals → assists → passes → key passes). Sibling **`mart_team_leaderboards`** feeds
**#41** (Top teams) after.
⛔⛔ **A CLOSED GAP REGISTER IS NOT A BUILT PAGE.** No block exists yet; no export payload carries
them; nothing wires the group selection to a render. `10_home.md` is the spec (**#100** proposes
rewriting it wholesale). Build **against `elite` first**, then wire in the #101 selection.
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

  - **Naming programme leftover — 7 seed rows blocked on ONE CPO copy call.** «on-target shots» 4
    sites · «on-target threat» 3 · «on-target dominance» 1 · «on target for−against» 1. My
    recommendation given to him: **LEAVE THEM** — no natural "on-goal" phrasing exists, defensible
    end state not debt. `shots_on_goal_player` keeps label "Shots on goal" / desc "Shots on target"
    until decided. ⚠ `label_i18n_key` (`metrics.shots_on_target_per_match.label`) STAYS — it is the
    join key; "fixing" it resolves to nothing. Four `strings.ts` chrome strings (`axPlay`,
    `heroVerdict*`, `heroCaption`) render on zero pages today.

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
`!131`, `!132` (×3), `!134` and `!140`, **every gate green every time**. The fix is never an
exemption list; it is a finer rule with a checkable property. Those earned so far:
  - **role** where two meanings share a line: `t(lang,"x")` is a UI word, `player.x` a payload field,
    `.get("x")` a warehouse column, `"x":` a payload key, `group=x` a metric group
  - **a domain fact** where one exists — there is no player `goals_for`, so the scoreline family is
    the team's; that one discriminator separated 6 wrong renames from 60 right ones
  - **in a markdown TABLE the COLUMN decides**, not the backtick; outside one, a token in
    parentheses beside an arithmetic operator is a quoted formula; `{placeholder}` is never an id

**2. CENSUS THE TREE, COUNT BOTH DIRECTIONS, AND MATCH A PATTERN NOT A LIST.** Report every sweep as
"N move, M stay" — a one-sided claim ("the prose is fixed") is what let an over-correction through.
⛔⛔ **ONE PHRASE HAD FOUR SPELLINGS IN ONE FILE AND MY REGEX WAS WRONG FIVE TIMES — four too NARROW,
then one too WIDE.** `on target`, `on-target`, `on_target`, **`OnTarget`**. ⚠ **A too-narrow census
reports a confident ZERO, never an error.** In order: an enumeration of spellings loses by one
variant (`!134`); **`\b` does not delimit `on` in `shots_on_target`**, `_` being a WORD character;
**camelCase has no separator at all**; the detector for the *new* word inherited the same blindness
(`"on goal"` with a literal SPACE missed "shots-**on-goal** data"); and widening THAT made
`on[ _-]?goal` match the METRIC ID `shots_on_goal_difference_per_match` quoted in a description,
inventing a split. Protected count read **0 → 1 → 3** as this was corrected.
⭐⭐ **THREE DETECTORS, THREE JOBS — collapsing any two broke the seed-prose sweep ONCE EACH.**
(1) DECIDES what changes: strict. (2) COUNTS occurrences: maximally permissive, every separator; its
only job is to miss nothing. (3) JUDGES reader-facing consistency: **prose only**.
⭐ **Resolution = ROLE, NOT PUNCTUATION (rule 1 again):** prose separates with SPACE or HYPHEN, an
identifier with an UNDERSCORE. Measured proof they differ: narrowing (2) to prose dropped the
protected count 3 → 0; widening (3) past prose invented a split. ⚠ A pattern buys false positives
too — `README.md`'s "ingesti**on target**".
⭐ **And run every such assertion against BASE as well as HEAD.** Mine was an absolute ("no cell
contains both spellings") and main already violated it, in `finishing_efficiency_pct`. Two-sided is
the only form an MR can own: introduced 0, removed 0.

**3. ALLOWLIST, NEVER BLOCKLIST — AND NOTHING MAY BE CHECKED BEFORE IT.** A blocklist of 5 of the
seed's 15 columns swept `interpretation`; the fix is a field allowlist. Then `!132` and `!136` both
proved the second half — a token rule placed BEFORE the allowlist silently reopens the hole.

**4. WHAT ACTUALLY FINDS DEFECTS**, in order: the **blinded review** (every defect of the last five
MRs, all with gates green); **reading the printed decisions and the applied diff**; and the **test
suite** — but only where a ruling forces code and test apart. Where a sweep edits both sides in
lockstep, green means nothing.

**5. TWO GUARD FACTS, MEASURED.** `check_description_hygiene` DOES catch a dangling `doc()`.
`check_yml_vs_projection` does NOT catch a column dropped from the final SELECT while still named in
a `safe_divide` on it — token presence, not projection. Mutation-test any guard before citing it.

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
label, verify your own entry is on top, pop immediately). Classify every token once and **print the
decision with its resolved entity**; abort before writing on any protected-count change or unlisted
file; maximal-token matching; multiset verify over old ∪ new; no no-op writes. Then gates unpiped
with exit codes read bare, mutations watched RED, two site builds, five blinded reviewers,
`review.md` with `--staged-hash`. **ROUND CAP 3** — past it, STOP and bring the findings; a fourth
round needs the CPO's word recorded as `rounds_cap_override:` in `review.md`, or the commit gate
refuses. Each reviewer section needs `## <exact-routing-key>`, then `VERDICT:`, then a
`risks_checked:` block — a PASS with an empty one is rejected.

## Standing traps (also in CLAUDE.md)

`git commit` must be the SOLE command in a Bash call. Heredocs are gate-blocked for file writes —
use Edit/Write. `review.md` must be COMMITTED. `acceptance_evidence.md` needs a
`criteria_demonstrated:` block with one 15+ character bullet per declared criterion. Contract edits
need a CLEAN tree. Never read a gate's exit code through a pipe.
