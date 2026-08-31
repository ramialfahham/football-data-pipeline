# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-31**. **main `5e121e7`**, clean, no open MRs.
⭐⭐ **STEP 4 IS COMPLETE AND MERGED.** All 35 player metrics carry `_player`, across seven MRs —
`!125` `shooting`, `!127` `discipline`, `!128` `defending`, `!129` `passing`, `!130` `duels`,
`!131` `goalkeeping`, `!132` `goals`. Verified on main: of 48 player catalogue rows, exactly one
lacks a `_player` marker — `minutes_per_appearance` — which is the one name the record's
"UNCHANGED, all 14" list names. **GITLAB** (`glab`, MRs); runner `ci-runner-01`.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⛔⛔ NEXT ACTION: NONE. ASK THE CPO WHICH OF THE TWO RUNS NEXT.

The programme's standing instruction is explicit: **"AFTER STEP 4 — do not start either of these
without telling me; I decide when they run."** Both are ready and neither is started.

**STEP 5 — nine English `label_en` rows, "on target" → "on goal"** (RULING 2). Team:
`shots_on_goal_per_match`, `shots_on_goal_against_per_match`, `sot_difference_per_match`,
`shot_accuracy`, `finishing_efficiency`. Player: `finishing_efficiency`, `shots_on_goal`,
`shots_on_goal_against`, `shots_on_goal_per90`. ⚠ German and Finnish are NOT touched — measured, both
already mean "on goal" (Torschüsse, Maalilaukaukset), so only English was out of step.
⚠ These are the seed's `label_en` column, which every step-4 classifier deliberately PROTECTS. Step 5
is the opposite job: `label_en` only, `metric_id` never. ⭐ Confirmed still pending by the `!132`
dist measurement: the rendered EN label is still "Ø Shots on target".

**THE SAMPLE ROLL-FORWARD**, owed and unscheduled. ⚠ The obvious recipe is a trap:
`fetch_fixture_payloads` emits UPCOMING fixtures only. The comparison block has rendered **12** rows
since `!123` (16 catalogue rows minus four the committed sample cannot feed); the roll-forward is
what restores them, and it is the only thing that will.

## ⛔ OPEN, AND THE CPO'S — carried, never decided

  - ⭐ **The `__team`/`__player` doc-block split now has NO live instance.** All six dual-entity ids
    (`duels_won_pct`, `saves`, `goals_against`, `goals`, `goals_open_play`, `goals_penalty`) were
    renamed on the player side, so no catalogue metric disagrees across entities any more.
    ⛔ **Nothing was removed or weakened**: `_derived()` still suffixes unconditionally, `_blocks()`
    still splits and still aborts on rows it cannot tell apart, the synthetic fixtures stay, and one
    new seed row recreates the collision. ⚠ The cost is concrete: **five files documented the
    mechanism with a worked example the programme then falsified.** Whether a guard with no live
    instance should remain is his call.
  - **A rename frees a name from #87 only when no PROVIDER column shares it.** Measured twice
    independently (`!131`, `!132`): the hygiene gate's ambiguous-name list went 4 → 3, not 4 → 1.
    `goals_open_play` left it; `goals_penalty` and `goals_against` did not, because both are also
    provider leg columns. **#87's 49 blank columns are NOT freed by this programme.**
  - **The column-reference resolver as a committed CI gate.** `!129` found four blind spots; `!130`
    and `!131` bounded it further (dotted references only; the projection check's weak form). Not
    proposed.
  - **#99** — the export's literal board keys moved in `!132` and remain pinned by NO test.
  - **`_LEADERBOARD_METRICS` / `_LB_KEEP`** pinned by no test, confirmed by `platform-reviewer` on
    five MRs. ⭐ `!131` added that the OTHER export path is unpinned too: `shape_top_players`'
    DROP-list means `TopPlayer` fields reach the frontend with no test between mart and component.
  - **#96** — eleven reproductions; no offline gate checks `accepted_values`, only `data:build:mr`.
  - **#98**; the doc-block inheritance trap.

## ⛔ WHAT STEP 4 PROVED ABOUT THIS KIND OF WORK — read before any similar sweep

**1. A SCOPE COARSER THAN THE ROLE IT MUST RESOLVE IS THE ONE RECURRING DEFECT.** It failed review on
`!131` (5–0) and on `!132` (5–0, then 4–1, then 4–1) — **with every gate green every time.** On
`!132` I set the SAME rule three times: too wide (English prose rewritten, and `persist_docs` ships
model descriptions to BigQuery), too narrow (identifier references in doc tables left stale), then
right inside markdown tables and blind outside them. The fix is never an exemption list; it is a
finer rule with a stated, checkable property:
  - entity by enclosing model (`- name:` in yml), by the seed's `entity` column, by file for SQL
  - **role** where two meanings share a line: `t(lang, "x")` is a UI word, `player.x` is a payload
    field, `.get("x")` is a warehouse column, `"x":` is a payload key, `group=x` is a metric group
  - **a domain fact** where one exists: there is no player `goals_for`, so the scoreline family is
    the team's — that single discriminator separated 6 wrong renames from 60 right ones
  - **in a markdown TABLE the COLUMN decides**, not the backtick: `Source column`/`Atomics`/
    `numerator` are identifiers; `Payload key`/`JSON key` stay; everything else is prose
  - **outside one, an OPERAND is an identifier**: a token inside parentheses holding BOTH an
    arithmetic operator AND another underscored identifier — that is a formula quoted in a comment
  - `{placeholder}` is a template slot, never an id

**2. CENSUS THE WHOLE TREE, THEN COUNT BOTH DIRECTIONS.** Every rule above was set from a census, not
from the sites a reviewer named, and each was reported as a two-sided count: **51 in-table
occurrences → 6 move, 45 stay**; **26 comment occurrences → 2 move, 24 stay**. A one-sided claim
("the prose is fixed") is what let the over-correction through.

**3. ALLOWLIST, NEVER BLOCKLIST — AND NOTHING MAY BE CHECKED BEFORE IT.** The seed protect-list was a
blocklist of 5 of 15 columns and swept `interpretation` (`!131`); it is now
`SEED_RENAMEABLE_FIELDS = {"metric_id"}`. `!132` proved the second half: a token-level rule placed
BEFORE that allowlist silently reopened the hole.

**4. THE THINGS THAT ACTUALLY FIND DEFECTS**, in order: the **blinded review** (every defect of the
last two MRs, all with gates green); **reading the printed decisions and the applied diff** (two
defects whose token counts were identical before and after); and the **test suite** — but only where
a ruling forces code and test apart. `!132`'s payload-key ruling did exactly that and pytest caught a
real rule inversion; where a sweep edits both sides in lockstep, green means nothing.

**5. SIMULATE THE GENERATOR BEFORE PREDICTING.** Load `sync_metric_docs_blocks.py`, apply the renames
to the seed rows in memory, call `_render()`, diff the block-name sets. Held exactly on `!130`
(175→172), `!131` (172→167) and `!132` (167→163). Write the prediction into the contract, then
measure it — and **report the disproved ones**: `!132` predicted the #87 list would fall to one name
and it fell to three, which is how the provider-shares-the-name rule got its second confirmation.

**6. TWO GUARD FACTS, MEASURED.** `check_description_hygiene` DOES catch a dangling `doc()`.
`check_yml_vs_projection` has a real bound: a column dropped from the final SELECT but still named
inside a `safe_divide` on that same SELECT leaves it GREEN — it tests token presence, not projection.
Mutation-test any guard before citing it, in both its strong and its weak form.

## ⛔ TRAPS THAT COST REAL TIME

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
