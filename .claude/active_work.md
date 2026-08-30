# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-30**. **main `a3fb952`** (after `!127`). METRIC CATALOGUE NAMING PROGRAMME:
**STEP 3 COMPLETE**. **STEP 4 = 3 of 7** — `!125` `shooting`, `!127` `discipline`, MR 3 `defending`.
**GITLAB** (`glab`, MRs); runner `ci-runner-01`.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ NEXT ACTION: step 4, MR 4 of 7 — the `passing` group

    passes_total → passes_player · passes_accurate → passes_accurate_player
    passes_key → passes_key_player · pass_accuracy_pct → passes_accuracy_player_pct
    key_passes_per90 → passes_key_per90

⛔ **THE AUTHORITY IS `.claude/task/escalations.log`**, block "THE METRIC CATALOGUE NAMING
PROGRAMME", table "⛔ PLAYER, 35 REMAINING". **CITE BY CONTENT, never a line number, never a plan
file.** The `_player`-before-`_pct` shape is RULING 5. Remaining after `passing`: `duels` (6) ·
`goalkeeping` (4) · `goals` (7).
⚠ **VERIFIED FROM THE SEED, and it has a trap**: `player`/`passing` is **6 rows** — the five above
plus `passes_per90`, which does NOT change. **`key_passes_per90 → passes_key_per90` is the ONE
`_per90` name in the whole programme that DOES rename** (it is the entry the record's own "13 not
14 unchanged" correction is about), and it sits in **both 18-name player `accepted_values` lists**
— so MR 4 is the first batch where TWO of the six #96 lists change.
⚠ `passes_total` and `passes_key` are provider column names as well as metric ids — the usual
collision.

## ⛔⛔ THE ONE RULE STEP 4 TURNS ON — READ THIS BEFORE WRITING ANY CODE

**A REFERENCE FOLLOWS ITS SOURCE. Shape only tells you WHAT is being read; the SOURCE decides
whether it moves.**

| shape | decision |
|---|---|
| `... as X` (alias) | the metric being written — **always moves** |
| `s.X` (dotted) | follows its source — moves only if that relation renamed it |
| bare `X` | follows its source too — **not** "is it inside a self-aliasing aggregate" |
| prose | follows the SURFACE it documents — a provider payload is a reference |
| seed `base_relation` / `numerator_expr` / `denominator_expr` / `label_i18n_key` | references — **never move** |

⭐⭐ **FOUR self-aliasing `sum(X) … as X` SITES, AND ONLY ONE MOVES ITS INNER READ.** Expect the same
four in every remaining batch:

    int_player_club_season__metrics.sql      ← per_fixture ← fct_fixture_player_stats   KEEP
    int_player_season_position__metrics.sql  ← per_fixture ← fct_fixture_player_stats   KEEP
    int_player_season_record.sql             ← player_legs = int_legs__player_match     KEEP
    int_player_season__metrics.sql           ← club_season = int_player_club_season__metrics  MOVES

⭐ **`int_player_profile__yoy` COMPOSES A METRIC ACROSS A MODEL BOUNDARY** and carries derived
`_this_season` / `_prev_season` / `_prev_season_full` / `_delta_yoy` forms plus `__player` block
names. They follow the metric — precedent is landed and readable
(`shots_on_goal_this_season → shots_on_goal_player_this_season`), not a new decision.
⛔ **PROVIDER / PER-MATCH SURFACES ARE OUT OF THE EDIT SET** (CPO **"yes"**): `mart_player_match_log`,
`mart_player_fixture_stats`, `mart_team_fixture_stats`, `int_legs__*`, `3_core`, `2_base`,
`1_staging`. ⚠ **`int_legs__team_from_players` IS THE LOAD-BEARING ONE**: it reads player columns and
emits TEAM names (`sum(passes_total) as passes` and friends). Renaming there ships a model that
cannot execute. RULING 5 named its seven team metrics — **key passes is on that list**, so MR 4 hits
it too.
⛔ **BORROWED DOC BLOCKS — RE-POINT, DON'T BLANK** (CPO **"re-point them"**).
**Measure it: the description count must stay 1604.**

## ⛔ NO GATE RESOLVES A COLUMN REFERENCE IN A MODEL

Nine green offline gates passed a build that could not execute — twice, on `!125`.
⭐ **The scratchpad resolver** (`check_column_refs.py`) walks CTE/`ref()` chains for dotted AND bare
reads. MR 3: 48 checked / 0 broken / 5 reported unresolved.
⛔⛔ **IT HAD A FALSE-POSITIVE CLASS AND IT FIRED ON AN UNMODIFIED `main`** — a column CREATED by an
expression alias inside a CTE chain is not emitted by the underlying relation, and calling that
broken is wrong. Fixed (exempt `as <name>` in the same model, **report, never skip silently**), then
re-proved RED on the `!125` round-2 defect so the fix is known not to have blunted it.
⭐⭐ **A CHECK THAT CRIES WOLF IS THE SAME DEFECT AS ONE THAT GIVES FALSE CONFIDENCE.**
⛔ **WHETHER IT BECOMES A COMMITTED CI GATE IS OPEN AND THE CPO'S** — and MR 3 changed the shape of
that question: it argues for HARDENING first, since a false positive on a correct main turns the
pipeline red for nothing.

## ⭐ THE RENAME METHOD — proven three times; adapt `rename_s4_defending.py`

⭐ **CLASSIFY EVERY TOKEN ONCE AND PRINT THE DECISION**, grouped by `(old,new)` PAIR. Abort before
writing if a protected token's count would change; verify the post-transform multiset over **old
stems ∪ new names**. Keep all three guards: **layer-range refusal**, **yml-column entry check**
(against POST-transform SQL), **multiset verify**. **ABORT ON AN UNLISTED FILE** — that is how MR 2
found `docs/ui_design_brief.md` and MR 3 found the five frontend files.
⭐ **WRITE THE CONTRACT FIRST, ON THE CLEAN TREE, THEN APPLY.** MR 3 did this and skipped the
stash-dance entirely; MR 2 did it backwards and had to stash 22 files to write the contract.
⚠ **A NO-OP WRITE IS STILL A WRITE.** ⚠ **`git grep` SCOPES TO THE CWD.** ⚠ Model→entity must be an
EXPLICIT map that ABORTS: `mart_leaderboards` is a PLAYER mart whose name says neither.
⛔⛔ **A CHECK MUST NAME THE TREE IT READS AND THE SHAPES IT CANNOT SEE.** Three instances now: MR 2
passed `HEAD` to `git grep` and read the committed base; MR 3 counted protected tokens across the
whole repo and failed on occurrences inside `contract.md` itself; MR 3's yml check called a
`select *` projection a defect. **A literal grep cannot see a wildcard-projected column.**
⚠ **WHEN YOU TOUCH THE THING THAT EXPLAINS A DECISION, RE-READ IT FOR EVERY SHAPE.** MR 3
reintroduced the lying-decision-list defect while fixing it: the `alias` case fell into the bare-read
branch and got labelled "bare read of int_legs__player_match, which renames it" — false twice over.

## ⛔ TRAPS — read before reporting anything green

⛔⛔ **A CHECK THAT PASSES EQUALLY ON THE WORK AND ON ITS ABSENCE IS NOT A CHECK.** A whole-file
whitelist is the wrong question for a file that PARTLY moves — pin the protected COUNT instead.
⛔⛔ **NEVER PIPE A GATE THROUGH `tail`/`head`.** MR 3 nearly shipped `HYGIENE_EXIT=0` that was
`tail`'s exit code. sqlfluff prints `All Finished!` on failure too. ⚠ **LT05 MEASURES TEMPLATED
LENGTH.** ⚠ sqlfluff FAILs on `dbt_utils` TMP/PRS noise: prove pre-existing by re-linting the
stashed base and diffing BYTE-FOR-BYTE.
⛔ **A SUBSTRING TEST IS NOT A PRESENCE TEST.** Count WHOLE TOKENS or structurally (`<div
class="mrow">` per row, `<div class="mgroup">` per heading, two blocks per fixture page).
⛔ **THE CONTRACT MAY ONLY BE (RE)WRITTEN ON A CLEAN TREE** — stash by EXPLICIT PATH with a `TEMP-`
label, verify your own entry is on TOP before popping, pop immediately, check `git stash list`.
⛔ **NEVER WRITE A REVIEWER'S VERDICT YOURSELF.** ⚠ Rewriting `review.md` for a new round DROPS the
standing verdicts. ⚠ **WAIT FOR EVERY REVIEWER BEFORE TOUCHING THE TREE.**
⭐ **LIVING DOCUMENT → REPLACE. DATED LOG → APPEND.** ⚠ **THE ROUND CAP IS 3.**
⚠ `--review-patch` writes to STDOUT — redirect it. ⚠ The contract gate parses a shell `2>` as a
PATH and refuses it; drive redirect-heavy verification from a Python script.
**OPERATIONAL NOTES ARE IN `CLAUDE.md`.**
**FIRST ACTION: `git stash list`** — 17 entries. ⚠ MATCH BY MESSAGE, NEVER BY INDEX. One must never
be rebuilt: **`feat/player-overview-tab`**.

## ⛔ OPEN, ALL THE CPO'S

- ⭐ **Should the column-reference resolver become a committed CI gate?** Evidence spans three MRs.
  MR 3 adds the counter-weight: it had a false-positive class that fired on a correct `main`, so
  the honest form of the question is now "harden, then commit?"
- **#96 — SEVEN reproductions.** MR 3: `shared.yml:1756` changed while the two 18-name player lists
  had to be checked as PROTECTIONS (`defensive_actions_per90` must NOT move). **MR 4 will change
  TWO lists** (`key_passes_per90 → passes_key_per90`). Check all six BY EYE every batch, then pin
  the board key mechanically as a SET across the mart, the list and the export.
- ⚠ **`_LEADERBOARD_METRICS` / `_LB_KEEP` (`export_site_data.py:48,53`) are pinned by NO test.**
  `platform-reviewer` independently confirmed this on `!127`. Pre-existing across every batch.
- **THE REVIEW-LOOP COST IS STRUCTURAL.** `contract.md` is hash-bound, so a one-word prose fix voids
  every verdict. Whether contract NARRATIVE should be hash-excluded is a governance decision.
- **#99** — `export_site_data.py` reads `goals`/`assists` by literal key; step 4's `goals` batch
  (MR 7) silently nulls the Squad tab unless the read keys move with it.
- **#98** English group headings on DE/FI · **#97** `docs/roles/` sweep · **#93** `mart_team_momentum`
  duplicates ~20 formulas · **#94** naming grammar · **#89** `finishing_efficiency` tier · **#82**
  ~40 blank descriptions · **#83** no competition-classification dim · **#91** parked
  value-equivalence checker · **#87** 49 blank ambiguous columns.

## ⭐ AFTER STEP 4

**STEP 5** = the 9 English `label_en` rows, "on target" → "on goal". ⚠ The EN hero sentences at
`site_v2/src/i18n/strings.ts:94-95` say "shots-on-target difference" — UI sentences, not catalogue
rows, so they may fall outside the nine. **Flag it, do not silently fix it — wording is the CPO's.**
**THEN THE SAMPLE ROLL-FORWARD**, owed and **the CPO decides when**. A rerun CANNOT work:
`fetch_fixture_payloads` emits UPCOMING fixtures only, so a past id can never be re-exported — the
export exits 0, reports thousands written, and changes nothing. ROLL THE SET FORWARD; recipe in
`site_v2/src/data/README.md`. New ids mean new page URLs. Needs ingestion to have run, and **there
is still no nightly SCHEDULE on GitLab**.
⚠ **What reaches the built pages, measured not assumed**: MR 2's four names ARE in the committed
`top_players[]` payload (from `mart_player_momentum`, a METRIC mart — `export_site_data.py:871`), so
the roll-forward changes those payload KEYS. But whole-token grep over `site_v2/dist` finds them in
**ZERO** built files: Astro renders server-side and no component reads them. Fixture rows render
**12** today (16 minus C, D, F's four).
⛔ **MR 3 IS THE EXCEPTION THAT PROVES THE FRONTEND DOES MATTER**: `defensive_actions_per_match` is a
RENDERED row whose stem was the player metric being renamed. Before every remaining batch, check
whether a PROTECTED token is one of the 12 rendered rows — if it is, criterion 1 becomes a real
check rather than a confirmed prediction.

**THEN THE CATALOGUE→CALCULATION WIRING** — the CPO's framing: "ensure that the metric definitions
are somehow wired to the different versions of the calculations (based on context)". Agreed shape,
AFTER the renames: a value-equivalence dbt test comparing each model's metric column to the
catalogue formula applied to that context's rows, plus a small `meta:` block on the metric-computing
models — **in the model's own yml, not a new registry**. ⚠ MetricFlow is the intended destination
but **premature**: "I just wanted to make sure that we can upgrade to semantic layer with MetricFlow
once there is a use case." Keep the catalogue machine-readable; adopt nothing that must be undone.

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
