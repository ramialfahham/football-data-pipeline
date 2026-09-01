# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-09-01**. **main `5aab198`**, clean, no open MRs.
⭐⭐ **THE NAMING PROGRAMME IS DONE AND SO IS THE WORK IT OWED.** Step 4: all 35 player metrics carry
`_player` (`!125`–`!132`) — of 48 player rows the only one without the marker is
`minutes_per_appearance`, which the record lists as UNCHANGED. Step 5 (`!134`): **0** `label_en` and
**0** `METRIC_LABELS_EN` values still say "on target". Sample roll-forward (`!136`): pins
**2026-09-01**, comparison renders **16 rows, not 12**.
**GITLAB** (`glab`, MRs); runner `ci-runner-01`.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⛔⛔ NEXT ACTION: NONE. THE QUEUE FROM THE NAMING PROGRAMME IS EMPTY.

⭐ **THE NIGHTLY LIVES IN CLOUD SCHEDULER — answered, not open. Runbook `deploy/nightly/README.md`.**
Two ENABLED jobs in **europe-west1**: `fdp-nightly` (`0 4 * * *`, ingest + full prod dbt build) and
`fdp-freshness` (`7 * * * *`). **The data IS refreshed on a timer.**
⚠ `data:nightly` in `.gitlab-ci.yml` is NOT it — nothing triggers it; GitLab schedule `4379625` is
deliberately **DISABLED**. **Enabling it without disabling `fdp-nightly` runs the build twice.**
⚠ Cost **~129 GB/day ≈ $17–24/mo**. Whether `fdp-freshness` needs hourly runs is the CPO's.
⛔ **Four rules, each bought with an error, 2026-09-01.** (1) **Identify a caller by its AUTH PATH,
not its name** — these run as `github-actions-dbt@…`, a reused legacy name, and I blamed a suspended
GitHub account for the spend. (2) **"Undocumented" is a claim about the WHOLE tree** — I said
"recorded nowhere" with no `git grep`; the runbook existed. (3) **Never quote a rate from ONE day** —
my first figure was ~$7/month, the smallest of fourteen. (4) Query
`region-eu.INFORMATION_SCHEMA.JOBS_BY_PROJECT` — **EU, not US**; `region-us` returns a false "0 jobs".

## ⛔ THE SAMPLE IS FRESH TODAY AND WILL GO STALE THE MOMENT THOSE FIXTURES KICK OFF

`!136` pinned the **2026-09-01** matchday: 4 fixtures, 3 competitions (`CIT` ×2, `DFBP`, `SPL`).
⚠ **A past fixture can NEVER be re-exported** — `fetch_fixture_payloads` emits `status_short in
('NS','TBD') and fixture_date >= current_date()`, and once a match kicks off its pre-match form rows
leave `mart_team_momentum`. **The next refresh REPLACES the set wholesale; it is never updated in
place.** ⭐ Recipe, traps and the four-list consistency check: `site_v2/src/data/README.md`.
⚠ Deliberately thin (4/3 vs the outgoing 19/13) on a CPO steer that this is infrastructure with
nothing shown. Coverage MEASURED: both competition shapes, all three form paths, the row-omission
path. 2026-09-04 (28 fixtures / 16 comps) is there if a fatter one is wanted.

## ⛔ ONE FOLLOW-UP STEP 5 LEFT — plus 7 rows waiting on ONE copy call

  - ✅ **The seed's prose — MERGED (`!140`), deliberately only PARTLY done.** 5 phrases moved across
    4 rows; 34 stay. Rows split 9 → 7: **2 fixed, 0 newly split.**
    ⛔ **THE UNIT IS THE ROW, NOT THE CELL** — the first rule converted whichever column held a
    movable phrase and froze its sibling, producing exactly the label=goal / desc=goal /
    interp=target state the CPO named when he widened the scope. Two reviewers FAILed it separately;
    `fetch_glossary()` ships both fields into `metrics.json` side by side. ⚠ A "don't make it WORSE"
    guard was ALSO wrong — those rows were already split by their label, so it passed them. **The
    condition must be "the end state is right", not "the delta is non-negative".**
    ⛔ **7 ROWS BLOCKED ON ONE CPO COPY DECISION**, inventory DERIVED from the seed (my hand-written
    one FAILed round 2): **«on-target shots» 4 sites · «on-target threat» 3 · «on-target dominance»
    1 · «on target for − against» 1.** Deciding the first three frees **6 of 7**. ⚠ Two blocks sit
    in the DESCRIPTION, not the interpretation. **"On-goal threat" is not English** and there is no
    "off-goal" as there is "off-target", so there is no substitution — only a rewrite, which the
    copy gate reserves to him permanently. **My recommendation, given to him: LEAVE THEM** — the
    football reviewer confirmed no natural on-goal phrasing exists, so it is a defensible end state,
    not debt. Until decided, `shots_on_goal_player` keeps label "Shots on goal" / description "Shots
    on target."
    ⚠ `saves_pct`, `deserved_points`, `deserved_points_gap` are HELD but NOT split — every field
    already agrees; converting only their movable part is what would split them. Not debt either.
  - **Four CHROME strings in `strings.ts`'s `Dict`** naming the same metric in rendered English:
    `axPlay` ("Shots on target difference / match", the team hero's x-axis) and
    `heroVerdictUnder`/`heroVerdictOver`/`heroCaption`. ⚠ **When the team Performance surface ships,
    that axis reads "Shots on target difference" beside a row reading "Ø Shots on goal difference".**
    Neither renders today.
  ⛔ **`label_i18n_key` is NOT one of these.** `metrics.shots_on_target_per_match.label` stays — the
  join key across the seed, `strings.ts`, `metricRows.ts`, three parsers and the page specs, and the
  catalogue declares no `..._on_goal_...` variant, so "fixing" it resolves the label to nothing.

⛔ **NOTHING PINS THE WORDING of the four rendered labels.** Mutation-tested, two reviewers: emptying
a label goes RED, `"Ø Bananas per fortnight"` leaves `npm test` **green**. Structural — the
byte-identical gate compares only keys in BOTH `strings.ts` and the frozen `site/i18n` corpus; three
of the four are absent, the fourth is skipped by name, and those three render on zero built pages.

## ⛔ OPEN, AND THE CPO'S — carried, never decided

  - ⭐ **The `__team`/`__player` doc-block split has NO live instance.** All six dual-entity ids were
    renamed on the player side, so no catalogue metric disagrees across entities any more.
    ⛔ **Nothing was removed or weakened** — `_derived()` still suffixes unconditionally, `_blocks()`
    still splits and aborts on rows it cannot tell apart, the fixtures stay, and one new seed row
    recreates the collision. ⚠ But **five files document it with a worked example the programme
    falsified.** Whether a guard with no live instance should remain is his call.
  - **A rename frees a name from #87 only when no PROVIDER column shares it.** Measured twice
    (`!131`, `!132`): the ambiguous-name list went 4 → 3, not 4 → 1 — `goals_penalty` and
    `goals_against` stayed, both being provider leg columns too. **#87's 49 blank columns are NOT
    freed by this programme.**
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
  - entity by enclosing model (`- name:` in yml), by the seed's `entity` column, by file for SQL
  - **role** where two meanings share a line: `t(lang,"x")` is a UI word, `player.x` a payload field,
    `.get("x")` a warehouse column, `"x":` a payload key, `group=x` a metric group
  - **a domain fact** where one exists — there is no player `goals_for`, so the scoreline family is
    the team's; that one discriminator separated 6 wrong renames from 60 right ones
  - **in a markdown TABLE the COLUMN decides**, not the backtick (`Source column`/`Atomics`/
    `numerator` are identifiers; `Payload key`/`JSON key` stay; the rest is prose)
  - **outside one, an OPERAND is an identifier**: a token in parentheses holding BOTH an arithmetic
    operator AND another underscored identifier is a formula quoted in a comment
  - `{placeholder}` is a template slot, never an id

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

**5. SIMULATE THE GENERATOR BEFORE PREDICTING**, and **report the disproved predictions** — that is
how the "a rename frees a name from #87 only if no provider column shares it" rule got confirmed.

**6. TWO GUARD FACTS, MEASURED.** `check_description_hygiene` DOES catch a dangling `doc()`.
`check_yml_vs_projection` does NOT catch a column dropped from the final SELECT while still named in
a `safe_divide` on it — token presence, not projection. Mutation-test any guard before citing it.

## ⛔ TRAPS THAT COST REAL TIME

⛔⛔ **"MERGED" IS A CLAIM TO VERIFY, NOT A FACT TO ACT ON — this cost a recovery on `!140`.** Told
"140 merged", I ran cleanup without checking; the merge had NOT landed, and **deleting an open MR's
source branch CLOSES the MR on GitLab.** Recovered from the reflog (branch recreated at the same
commit, `glab mr reopen 140`), nothing lost — but do not repeat it.
⭐ **The check, before deleting anything:** `git fetch gitlab` then
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
⚠ **`subprocess.run(..., text=True)` decodes with the WINDOWS locale (cp1252), not UTF-8.** Comparing
`git show <base>:file` against a UTF-8 read reports every non-ASCII character as a difference — `Ø`
arrives as `Ã˜` — and made a byte-identical seed look like 32 corrupted fields. Capture BYTES and
`.decode("utf-8")` both sides. The seed's `label_en` column is full of `Ø`.

## Method that works — seven MRs of evidence

Contract FIRST on a clean tree (the gate refuses otherwise; stash by explicit path with a `TEMP-`
label, verify your own entry is on top, pop immediately). Classify every token once and **print the
decision with its resolved entity**; abort before writing on any protected-count change or unlisted
file; maximal-token matching; multiset verify over old ∪ new; no no-op writes. Then gates unpiped
with exit codes read bare, mutations watched RED, two site builds, five blinded reviewers,
`review.md` with `--staged-hash`. **ROUND CAP 3** — past it, STOP and bring the findings; a fourth
round needs the CPO's word recorded as `rounds_cap_override:` in `review.md`, or the commit gate
refuses. Each reviewer section needs `## <exact-routing-key>`, then `VERDICT:`, then a
`risks_checked:` block — a PASS with an empty one is rejected. The classifiers are in the scratchpad
(`rename_s4_goals.py` is the most developed) and are deliberately **not committed**.

## Standing traps (also in CLAUDE.md)

`git commit` must be the SOLE command in a Bash call. Heredocs are gate-blocked for file writes —
use Edit/Write. `review.md` must be COMMITTED. `acceptance_evidence.md` needs a
`criteria_demonstrated:` block with one 15+ character bullet per declared criterion. Contract edits
need a CLEAN tree. Never read a gate's exit code through a pipe.
