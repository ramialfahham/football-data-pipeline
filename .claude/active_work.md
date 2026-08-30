# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-30**. **main `06ac8b3`** (after `!125`). METRIC CATALOGUE NAMING PROGRAMME:
**STEP 3 COMPLETE** (12 team renames, live). **STEP 4 = 1 of 7 done** — `!125` shipped the `shooting`
group. **Nothing is in flight.** **GITLAB** (`glab`, MRs); runner `ci-runner-01`.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ NEXT ACTION: step 4, MR 2 of 7 — the `discipline` group

    cards_yellow → cards_yellow_player · cards_red → cards_red_player
    cards_total  → cards_player        · offsides  → offsides_player
    penalty_committed → penalty_committed_player

⛔ **THE AUTHORITY IS `.claude/task/escalations.log`**, block "THE METRIC CATALOGUE NAMING
PROGRAMME", table "⛔ PLAYER, 35 REMAINING". **CITE BY CONTENT, never a line number, never a plan
file.** The `_player`-before-`_pct` shape is RULING 5. Split by the seed's `metric_group`; remaining
after `discipline`: `defending` (5) · `passing` (5) · `duels` (6) · `goalkeeping` (4) · `goals` (7).

## ⛔⛔ THE ONE RULE STEP 4 TURNS ON — READ THIS BEFORE WRITING ANY CODE

**A REFERENCE FOLLOWS ITS SOURCE. Shape only tells you WHAT is being read; the SOURCE decides
whether it moves.** These player metric names are ALSO provider stat words — `cards_yellow` is the
same identifier from `stg_apif__fixture_players` through base, core and `int_legs__player_match`.
**20 of the 35 collide this way** (`goals`, `saves`, `passes_total`, `duels_won`, `offsides`, all the
`tackles_*` and `dribbles_*`…). `!125` cost **three review rounds and two full reverts** because I
asked the right question for one shape and a different one for another.

| shape | decision |
|---|---|
| `... as X` (alias) | the metric being written — **always moves** |
| `s.X` (dotted) | follows its source — moves only if that relation renamed it |
| bare `X` | follows its source too — **not** "is it inside a self-aliasing aggregate" |
| prose | a mention documenting a PROVIDER payload is a reference, not the metric |
| seed `base_relation` / `numerator_expr` / `denominator_expr` | references — **never move** |

⛔ **PROVIDER / PER-MATCH SURFACES ARE OUT OF THE EDIT SET ENTIRELY** (CPO ruling, verbatim **"yes"**):
`mart_player_match_log`, `mart_player_fixture_stats`, `mart_team_fixture_stats`, `int_legs__*`,
`3_core`, `2_base`, `1_staging`. They carry raw per-match stats, not metrics. Precedent: `!111`
renamed team `goals_for → goals` and LEFT `int_legs__team_match.goals_for` — **a metric and its
column may legitimately differ.**
⛔ **TEAM COLUMNS BORROW PLAYER DOC BLOCKS — RE-POINT, DON'T BLANK** (CPO ruling, verbatim
**"re-point them"**). 30 such references across 4 batches. The published text is entity-neutral and
stays correct; the block NAME is internal jinja no consumer sees. **Measure it: the description
count must stay 1604.** Blanking would give 1592.

## ⛔ NO GATE RESOLVES A COLUMN REFERENCE IN A MODEL

Nine green offline gates passed a build that could not execute — **twice**. Only reviewers and the
paid `data:build:mr` caught it. ⚠ `assert_metric_catalogue_expr_resolvable` DOES resolve the SEED's
formula fields (live warehouse), so do not repeat the categorical claim; the model layer is what is
uncovered.
⭐ **A static resolver exists in the scratchpad** (`check_column_refs.py`): walks CTE/`ref()` chains
and checks dotted AND bare references against declared columns. 31 checked / 0 broken on `!125`, and
it reproduces each failed round's defect on demand. Limits: only relations whose ymls declare columns
(4_intermediate, 5_marts — staging under-declares), and it does not cover prose or seed.
⛔ **WHETHER IT BECOMES A COMMITTED CI GATE IS OPEN AND THE CPO'S** (new mechanism). Six batches and
20 colliding names still carry the exposure.

## ⭐ THE RENAME METHOD — proven, and its failure modes recorded

⭐ **CLASSIFY EVERY TOKEN ONCE AND PRINT THE DECISION.** Abort before writing if a protected token's
count would change; verify the post-transform token multiset per file.
⭐ Guards that each caught a real defect on `!125`, keep all three: the **layer-range refusal**; the
**yml-column-entry check** (a renamed `- name:` must exist in the model's SQL *after* the change —
compare post-transform, not the file on disk); and the **multiset verify over old ∪ new vocabulary**
(a rename that removes the stem entirely reads as data loss otherwise).
⚠ **A NO-OP WRITE IS STILL A WRITE** — the contract gate watches the file system, not the diff.
⚠ **`git grep` SCOPES TO THE CWD**; assert `cd <repo root>` in the same command as any counting grep.
⚠ Model→entity must be an EXPLICIT map that ABORTS on an unlisted model: `mart_leaderboards` is a
PLAYER mart whose name says neither.

## ⛔ TRAPS — read before reporting anything green

⛔⛔ **A CHECK THAT PASSES EQUALLY ON THE WORK AND ON ITS ABSENCE IS NOT A CHECK.** Three instances in
two days: a `sed` that failed to compile so an intersection was vacuously empty; a corroboration read
from a file that had been overwritten to zero lines; and **my own resolver scoped to dotted reads,
reporting "25 of 28 resolved, 0 broken" while a model sat broken.** Ask what it would say if the work
had not been done.
⛔⛔ **NEVER PIPE A GATE THROUGH `tail`/`head`, NEVER READ A CLOSING BANNER AS A VERDICT.** `sqlfluff
… | tail -3` hid an LT05 behind `All Finished!`, which it prints on failure too.
⛔ **A SUBSTRING TEST IS NOT A PRESENCE TEST.** Count WHOLE TOKENS, or structurally (`<div
class="mrow">` per row, `<div class="mgroup">` per heading, two blocks per fixture page).
⚠ **LT05 MEASURES TEMPLATED LENGTH.** A long line inside `{% set %}` or `{# … #}` is invisible to it.
⛔ **THE CONTRACT MAY ONLY BE (RE)WRITTEN ON A CLEAN TREE** — stash by EXPLICIT PATH, amend, pop
immediately, check `git stash list`. `.claude/active_work.md` counts as dirty; `.claude/task/` does
not. ⚠ `git checkout -- <file>` restores from the INDEX; after `git add` use
`git restore --source=HEAD --staged --worktree`.
⛔ **NEVER WRITE A REVIEWER'S VERDICT YOURSELF.** ⚠ Rewriting `review.md` for a new round DROPS the
standing verdicts — re-add every required reviewer.
⚠ **WAIT FOR EVERY REVIEWER BEFORE TOUCHING THE TREE.** Reverting mid-review made one reviewer see
the tree change under it.
⭐ **LIVING DOCUMENT → REPLACE. DATED LOG → APPEND.**
⚠ **THE ROUND CAP IS 3.** Past it, STOP and bring the findings to the CPO.
⚠ `--review-patch` writes to STDOUT — redirect it. **OPERATIONAL NOTES ARE IN `CLAUDE.md`.**
**FIRST ACTION: `git stash list`** — 17 entries. ⚠ MATCH BY MESSAGE, NEVER BY INDEX. One must never
be rebuilt: **`feat/player-overview-tab`**.

## ⛔ OPEN, ALL THE CPO'S

- ⭐ **Should the column-reference resolver become a committed CI gate?** (above) The strongest
  evidence yet is `!125`: two reverts, three rounds, nine green gates on a non-executing build.
- **#96 — SIX consecutive reproductions.** Reverting one entry of a 22-name `accepted_values` list
  survives the entire offline suite; only `data:build:mr` catches it. Check all six lists BY EYE
  every batch (three TEAM 22-name, two PLAYER 18-name, one 14-name rate-board).
- ⚠ **`_LEADERBOARD_METRICS` / `_LB_KEEP` (`export_site_data.py:48,53`) are pinned by NO test** —
  `tests/test_export_site_data.py` uses synthetic keys. A stale board key ships silently.
  Pre-existing across every batch. Worth its own issue.
- **THE REVIEW-LOOP COST IS STRUCTURAL.** `contract.md` is hash-bound, so a one-word prose fix voids
  every verdict. `!125` hit this exactly: a factual imprecision found at round 3 had to be corrected
  in `escalations.log` (hash-excluded) because fixing the contract would have forced a round 4 past
  the cap. Whether contract NARRATIVE should be hash-excluded (keeping `scope_paths` and
  `acceptance_criteria` hashed) is a governance decision.
- **#99** — `export_site_data.py` reads `goals`/`assists` by literal key with `.get()`; step 4's
  `goals` batch (MR 7) silently nulls the Squad tab unless the read keys move with it.
- **#98** English group headings on DE/FI · **#97** `docs/roles/` sweep · **#93** `mart_team_momentum`
  duplicates ~20 formulas · **#94** naming grammar · **#89** `finishing_efficiency` tier · **#82**
  ~40 blank descriptions · **#83** no competition-classification dim · **#91** parked
  value-equivalence checker.
- **#92** FIXED (`!115`): CI datasets are PER MR (`ci_mr<IID>_*`). ⛔ Nothing expires them, by CPO
  instruction. ~6 GB, ~12¢/month.

## ⭐ AFTER STEP 4

**STEP 5** = the 9 English `label_en` rows, "on target" → "on goal". ⚠ The EN hero sentences at
`site_v2/src/i18n/strings.ts:94-95` say "shots-on-target difference" — UI sentences, not catalogue
rows, so they may fall outside the nine.
**THEN THE SAMPLE ROLL-FORWARD**, owed and **the CPO decides when**. A rerun CANNOT work:
`fetch_fixture_payloads` emits UPCOMING fixtures only, so a past id can never be re-exported — the
export exits 0, reports thousands written, and changes nothing. ROLL THE SET FORWARD; recipe in
`site_v2/src/data/README.md`. New ids mean new page URLs. Needs ingestion to have run, and **there is
still no nightly SCHEDULE on GitLab**.
⚠ Fixture rows render **12** today (16 minus C, D, F's four). Step 4's own renames do NOT reach the
built pages — the `top_players` payload carries `shots_on`, a leg column.

**THEN THE CATALOGUE→CALCULATION WIRING** — the CPO's own framing: "ensure that the metric
definitions are somehow wired to the different versions of the calculations (based on context)".
Agreed shape, agreed AFTER the renames: a value-equivalence dbt test comparing each model's metric
column to the catalogue formula applied to that context's rows, plus a small `meta:` block on the
metric-computing models (what `count(*)` means there) — **in the model's own yml, not a new
registry**. ⚠ MetricFlow is the intended destination but **premature**: "I just wanted to make sure
that we can upgrade to semantic layer with MetricFlow once there is a use case." Keep the catalogue
machine-readable; adopt nothing that must be undone.

## ⭐ OTHER STANDING STATE

✅ **SETTLED, do not re-propose.** BROWSE DROPPED (`!80`). TOP TEAMS = one per league.
⛔ **Points is a synthetic 3-1-0 tally in EVERY competition** (`int_team_season_record.sql:73`) — the
mart must emit NULL. Blocks the team Overview for cups.
⛔ **The deserved-vs-actual hero is EXACT ONLY for a COMPLETED season.** Two CPO decisions OPEN.
⚠ **The metric rows render on NO built team page today** — team 33's featured season has 1 game,
below the `>= 3 finished games` floor. Never write a criterion that reads a metric ROW off it.
⛔ **#95 — read before touching any slug or team name.** `team_slug` is PERMANENT and RE-DERIVED FROM
`team_name` ON EVERY BUILD, so correcting a name MOVES A PUBLISHED URL. Team-names programme PAUSED
part-way (97 of ~130 Pool 1).
