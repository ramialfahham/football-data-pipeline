# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-31**. **main `6f0ee07`** (after `!131`).
⛔⛔ **STEP 4 IS NOT COMPLETE. MR 7 (`goals`) IS BUILT AND REVIEWED BUT NOT COMMITTED** — branch
`refactor/metric-rename-player-goals`, 45 files STAGED, zero commits, `diff_sha256`
`0e995d62…` bound in `review.md`. Six of seven are merged: `!125` `shooting`, `!127` `discipline`,
`!128` `defending`, `!129` `passing`, `!130` `duels`, `!131` `goalkeeping`.
**GITLAB** (`glab`, MRs); runner `ci-runner-01`.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⛔⛔ NEXT ACTION: `!132` IS CLEARED TO COMMIT — ALL FIVE REVIEWERS PASS.

Round 1 FAILed 5–0, round 2 FAILed 4–1, round 3 FAILed 4–1, **round 4 PASSed** — a narrow
`scope-auditor` delta pass on the corrected log, **authorised by the CPO past the cap of 3** after he
declined my recommendation to commit without it. Every finding accepted and fixed; full account in
`review.md`. All gates green: `pytest` 1009/1/14, `sqlfluff` byte-identical, 163 blocks, 1604
descriptions, 66 pages, 12/12/12 rendered rows.

⭐ **The one durable lesson, if only one survives:** the same role rule was set THREE times — too
wide, too narrow, then right in markdown tables and blind outside them. Every gate was green at all
three stages. **Only the blinded review found any of it**, four MRs running.

AFTER `!132` merges, the standing instruction applies: **"AFTER STEP 4 — do not start either of
these without telling me; I decide when they run."** Both are ready and neither is started.

**STEP 5 — nine English `label_en` rows, "on target" → "on goal"** (RULING 2). Team:
`shots_on_goal_per_match`, `shots_on_goal_against_per_match`, `sot_difference_per_match`,
`shot_accuracy`, `finishing_efficiency`. Player: `finishing_efficiency`, `shots_on_goal`,
`shots_on_goal_against`, `shots_on_goal_per90`. ⚠ German and Finnish are NOT touched — measured, both
already mean "on goal" (Torschüsse, Maalilaukaukset), so only English was out of step.
⚠ These are the seed's `label_en` column, which the step-4 classifiers deliberately PROTECT. Step 5
is the opposite job: `label_en` only, `metric_id` never.

**THE SAMPLE ROLL-FORWARD**, owed and unscheduled. ⚠ The obvious recipe is a trap:
`fetch_fixture_payloads` emits UPCOMING fixtures only. The comparison block has rendered **12** rows
since `!123` (16 catalogue rows minus four the committed sample cannot feed); the roll-forward is
what restores them, and it is the only thing that will.

## ⛔ THE ONE ITEM STEP 4 LEAVES OPEN, AND IT IS THE CPO'S

**The `__team`/`__player` doc-block split now has NO live instance.** All six dual-entity metric ids
(`duels_won_pct`, `saves`, `goals_against`, `goals`, `goals_open_play`, `goals_penalty`) were renamed
on the player side across step 4, so no metric in the catalogue disagrees across entities any more.
⛔ **Nothing was removed or weakened**: `_derived()` still suffixes unconditionally, `_blocks()` still
splits and still aborts on rows it cannot tell apart, and the synthetic test fixtures stay. One new
seed row recreates the collision.
⚠ The cost is concrete, not theoretical: **five files documented the mechanism with a worked example
that the programme then falsified** (`!130` rewrote three, `!131` one, `!132` the last). Whether a
guard with no live instance should remain is his call.

## ⛔ WHAT STEP 4 PROVED ABOUT THIS KIND OF WORK — read before any similar sweep

**1. A SCOPE COARSER THAN THE ENTITY IT MUST RESOLVE IS THE ONE RECURRING DEFECT.** `!131` failed
review 5–0 on two instances of it with every gate green. The fix is never an exemption list; it is a
finer rule with a stated, checkable property:
  - entity by enclosing model (`- name:` in yml), by the seed's `entity` column, by file for SQL
  - **role** where two meanings share a line: `t(lang, "x")` is a UI word, `player.x` is a payload
    field, `.get("x")` is a warehouse column, `"x":` is a payload key, `group=x` is a metric group
  - **a domain fact** where one exists: there is no player `goals_for`, so the scoreline family is
    the team's — that single discriminator separated 6 wrong renames from 60 right ones
  - **a backtick** in documentation prose: an identifier reference moves, a word does not

**2. ALLOWLIST, NEVER BLOCKLIST — AND NOTHING MAY BE CHECKED BEFORE IT.** The seed protect-list was
a blocklist of 5 of 15 columns and swept `interpretation` (`!131`); it is now
`SEED_RENAMEABLE_FIELDS = {"metric_id"}`. `!132` then proved the second half: a token-level rule
placed BEFORE that allowlist silently reopened the hole.

**3. THE THREE THINGS THAT ACTUALLY FIND DEFECTS**, in order of what they caught across step 4:
the **blinded review** (5–0 on `!131`, with every gate green); **reading the printed decisions and
the applied diff** (two defects whose token counts were identical before and after the fix, so no
gate could see them); and the **test suite** — but only where the code and its test are not moved in
lockstep by the same sweep.

**4. SIMULATE THE GENERATOR BEFORE PREDICTING.** Load `sync_metric_docs_blocks.py`, apply the renames
to the seed rows in memory, call `_render()`, diff the block-name sets. Held exactly on `!130`
(175→172), `!131` (172→167) and `!132` (167→163). Write the prediction into the contract, then
measure it — `!129` had three disproved after the fact.

**5. TWO GUARD FACTS, MEASURED.** `check_description_hygiene` DOES catch a dangling `doc()`
("unresolved docs block"). `check_yml_vs_projection` has a real bound: a column dropped from the
final SELECT but still named inside a `safe_divide` on that same SELECT leaves it GREEN — it tests
token presence, not projection. Mutation-test any guard before citing it, in both its strong and its
weak form.

**6. TRAPS THAT COST TIME.** ⚠ **CWD persists between Bash calls** — a `cd` in one call breaks
repo-relative paths in the next; it aborted an apply mid-run on `!131` and again on `!132`.
⚠ `git checkout -- .` reverts the CONTRACT too if it is unstaged — exclude it explicitly.
⚠ A file that falls to ZERO renames is never reopened by the no-op-write guard, so it keeps its
previous text: restore it from base explicitly and re-reconcile `scope_paths`.
⚠ `git grep` is BRE — `[` opens a character class, so `git grep 'values: ['` silently finds nothing.
Use `-F`.
⛔⛔ **`--review-patch` PRINTS; only a REDIRECT writes the file — and it reads the INDEX, not the
working tree.** `git_discipline.py --review-patch` builds from `git diff --staged <base>`, so
`python .claude/hooks/git_discipline.py --review-patch` on its own emits to stdout and **leaves the
previous round's `review_input.patch` untouched on disk**, while exiting 0. On `!132` round 2 that
served all five reviewers the ROUND-1 diff: two FAILed on defects that were already fixed, quoting
patch offsets that no longer existed. The correct call is
`… --review-patch > .claude/task/review_input.patch` **after `git add -u`** — with nothing staged the
patch would be empty anyway.
⭐ **The tell is free and immediate: `--staged-hash` printing `e3b0c442…`** — that is
`sha256("")`, so an empty staged diff. The hook's own docstring names that value as the signature of
a binding covering zero bytes. Never write it into `review.md`.
⭐ And the cross-check that resolved it in one step: a reviewer reading the FILES said clean while a
reviewer reading the PATCH said corrupted. **When two reviewers contradict each other on the same
tokens, suspect the artifact before the code.**
⚠ **`subprocess.run(..., text=True)` decodes with the WINDOWS locale (cp1252), not UTF-8.** Comparing
`git show <base>:file` against a UTF-8 read of the same file reports every non-ASCII character as a
difference — `Ø` arrives as `Ã˜` — and made a byte-identical seed look like 32 corrupted fields.
Capture BYTES and `.decode("utf-8")` both sides. The seed's `label_en` column is full of `Ø`.

## Method that works — seven MRs of evidence

Contract FIRST on a clean tree (the gate refuses otherwise; stash by explicit path with a `TEMP-`
label, verify your own entry is on top, pop immediately). Classify every token once and **print the
decision with its resolved entity**; abort before writing on any protected-count change or unlisted
file; maximal-token matching; multiset verify over old ∪ new; no no-op writes. Then gates unpiped
with exit codes read bare, mutations watched RED, two site builds, five blinded reviewers,
`review.md` with `--staged-hash`. **ROUND CAP 3.** The classifiers are in the scratchpad
(`rename_s4_goals.py` is the most developed) and are deliberately **not committed**.

## ⛔ OPEN, AND THE CPO'S — carried, never decided

  - ⭐ **The block split with no live instance** — see above. The item step 4 leaves behind.
  - **The column-reference resolver as a committed CI gate.** `!129` found four blind spots; `!130`
    and `!131` bounded it further (dotted references only; the projection check's weak form). Neither
    is proposed.
  - **#99** — the export's literal board keys moved in `!132` and remain pinned by NO test.
  - **`_LEADERBOARD_METRICS` / `_LB_KEEP`** pinned by no test, confirmed by `platform-reviewer` on
    four MRs. ⭐ `!131` added that the OTHER export path is unpinned too: `shape_top_players`'
    DROP-list means `TopPlayer` fields reach the frontend with no test between mart and component.
  - **#96** — eleven reproductions; no offline gate checks `accepted_values`, only `data:build:mr`.
  - **#87** — 49 blank columns. `!131` established the naming programme does **not** free them: the
    "yes" and "re-point them" rulings interact so a metric rename cannot disambiguate a name the
    PROVIDER also uses.
  - **#98**; the doc-block inheritance trap.

## Standing traps (also in CLAUDE.md)

`git commit` must be the SOLE command in a Bash call. Heredocs are gate-blocked for file writes —
use Edit/Write. `review.md` must be COMMITTED with `## <exact-routing-key>` headers.
`acceptance_evidence.md` needs a `criteria_demonstrated:` block with one 15+ character bullet per
declared criterion, or the commit gate refuses. Contract edits need a CLEAN tree. Never read a
gate's exit code through a pipe.
