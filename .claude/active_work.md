# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-30**. **main `3e5b25b`**. METRIC CATALOGUE NAMING PROGRAMME: **STEP 3
COMPLETE** (12 team renames, live). **STEP 4 = 2 of 7** — `!125` shipped `shooting`, MR 2 shipped
`discipline`. **GITLAB** (`glab`, MRs); runner `ci-runner-01`.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ NEXT ACTION: step 4, MR 3 of 7 — the `defending` group

    tackles_total → tackles_player · tackles_interceptions → interceptions_player
    tackles_blocks → blocks_player · defensive_actions → defensive_actions_player
    dribbles_past → dribbles_past_player

⛔ **THE AUTHORITY IS `.claude/task/escalations.log`**, block "THE METRIC CATALOGUE NAMING
PROGRAMME", table "⛔ PLAYER, 35 REMAINING". **CITE BY CONTENT, never a line number, never a plan
file.** The `_player`-before-`_pct` shape is RULING 5. Split by the seed's `metric_group`; remaining
after `defending`: `passing` (5) · `duels` (6) · `goalkeeping` (4) · `goals` (7).
⚠ Confirm the group's membership FROM THE SEED before writing the contract — `discipline` was
exactly 5 rows and the table agreed, but that is a check, not an assumption.

## ⛔⛔ THE ONE RULE STEP 4 TURNS ON — READ THIS BEFORE WRITING ANY CODE

**A REFERENCE FOLLOWS ITS SOURCE. Shape only tells you WHAT is being read; the SOURCE decides
whether it moves.** These player metric names are ALSO provider stat words — `tackles_total` is the
same identifier from `stg_apif__fixture_players` through base, core and `int_legs__player_match`.

| shape | decision |
|---|---|
| `... as X` (alias) | the metric being written — **always moves** |
| `s.X` (dotted) | follows its source — moves only if that relation renamed it |
| bare `X` | follows its source too — **not** "is it inside a self-aliasing aggregate" |
| prose | follows the SURFACE it documents — a provider payload is a reference |
| seed `base_relation` / `numerator_expr` / `denominator_expr` / `label_i18n_key` | references — **never move** |

⭐⭐ **MR 2 PROVED THE RULE AGAINST ITSELF: THREE `sum(X) … as X` SITES, TWO OPPOSITE ANSWERS.**
`int_player_club_season__metrics` (← `fct_fixture_player_stats`) and `int_player_season_record`
(← `int_legs__player_match`) KEEP the inner read; `int_player_season__metrics` (← `club_season` =
`int_player_club_season__metrics`, a metric relation the same branch renames) MOVES it. Expect the
same three models in every remaining batch. The landed code shows both answers side by side.
⭐ **`label_i18n_key` WAS THE FOURTH SURFACE** — `playerMetrics.offsides.label` matched a stem inside
a dotted i18n key. It does not move; `!125`'s diff proves it (`playerMetrics.shots.label` stayed).
**Expect a fifth. Ask of every occurrence: is this the metric, or a reference to something upstream?**

⛔ **PROVIDER / PER-MATCH SURFACES ARE OUT OF THE EDIT SET ENTIRELY** (CPO ruling, verbatim **"yes"**):
`mart_player_match_log`, `mart_player_fixture_stats`, `mart_team_fixture_stats`, `int_legs__*`,
`3_core`, `2_base`, `1_staging`. Precedent: `!111` renamed team `goals_for → goals` and LEFT
`int_legs__team_match.goals_for` — **a metric and its column may legitimately differ.**
⛔ **COLUMNS BORROWING A PLAYER DOC BLOCK — RE-POINT, DON'T BLANK** (CPO ruling, verbatim
**"re-point them"**). MR 2 moved 48 doc refs while 16 columns kept their provider name.
**Measure it: the description count must stay 1604.** Blanking would give 1592.

## ⛔ NO GATE RESOLVES A COLUMN REFERENCE IN A MODEL

Nine green offline gates passed a build that could not execute — twice, on `!125`. ⚠
`assert_metric_catalogue_expr_resolvable` DOES resolve the SEED's formula fields (live warehouse);
the MODEL layer is what is uncovered.
⭐ **A static resolver exists in the scratchpad** (`check_column_refs.py`): walks CTE/`ref()` chains
and checks dotted AND bare references. MR 2: 42 checked / 0 broken / 2 reported unresolved.
⭐ **PROVE IT BEFORE TRUSTING IT — the CPO's instruction, and MR 2 did it three times**: a dotted
break and a bare break on the base tree, then an exact reproduction of the `!125` round-2 defect on
the POST-RENAME tree. Limits: only relations whose ymls declare columns (staging under-declares);
no prose, no seed.
⛔ **WHETHER IT BECOMES A COMMITTED CI GATE IS OPEN AND THE CPO'S** (new mechanism).

## ⭐ THE RENAME METHOD — proven twice, adapt `rename_s4_discipline.py`

⭐ **CLASSIFY EVERY TOKEN ONCE AND PRINT THE DECISION** (grouped by `(old,new)` PAIR, never by
`old` alone). Abort before writing if a protected token's count would change; verify the
post-transform multiset per file over **old stems ∪ new names** (`cards_total → cards_player`
removes the stem entirely). Keep all three guards: the **layer-range refusal**, the **yml-column
entry check** (compare against POST-transform SQL), the **multiset verify**.
⭐ **ABORT ON AN UNLISTED FILE.** That is how `docs/ui_design_brief.md` was found in MR 2 — two
prose uses of the English word "offsides". A search would not have raised it.
⚠ **A NO-OP WRITE IS STILL A WRITE.** ⚠ **`git grep` SCOPES TO THE CWD.** ⚠ Model→entity must be an
EXPLICIT map that ABORTS: `mart_leaderboards` is a PLAYER mart whose name says neither.
⚠ **NAME THE TREE A CHECK READS.** MR 2's verifier passed `HEAD` to `git grep`, read the committed
base instead of the worktree, and reported 107 false findings. Fourth instance of that class.

## ⛔ TRAPS — read before reporting anything green

⛔⛔ **A CHECK THAT PASSES EQUALLY ON THE WORK AND ON ITS ABSENCE IS NOT A CHECK.** Ask what it
would say if the work had not been done. A whole-file whitelist is the wrong question for a file
that PARTLY moves — pin the protected count instead.
⛔⛔ **NEVER PIPE A GATE THROUGH `tail`/`head`, NEVER READ A CLOSING BANNER AS A VERDICT.** sqlfluff
prints `All Finished!` on failure too. ⚠ **LT05 MEASURES TEMPLATED LENGTH** — invisible inside
`{% set %}`. ⚠ sqlfluff FAILs on `dbt_utils` TMP/PRS noise: prove pre-existing by re-linting the
stashed base and diffing BYTE-FOR-BYTE.
⛔ **A SUBSTRING TEST IS NOT A PRESENCE TEST.** Count WHOLE TOKENS or structurally (`<div
class="mrow">` per row, `<div class="mgroup">` per heading, two blocks per fixture page).
⛔ **THE CONTRACT MAY ONLY BE (RE)WRITTEN ON A CLEAN TREE** — stash by EXPLICIT PATH with a `TEMP-`
label, verify your own entry is on TOP before popping, pop immediately, check `git stash list`.
`.claude/active_work.md` counts as dirty; `.claude/task/` does not.
⛔ **NEVER WRITE A REVIEWER'S VERDICT YOURSELF.** ⚠ Rewriting `review.md` for a new round DROPS the
standing verdicts — re-add every required reviewer. ⚠ **WAIT FOR EVERY REVIEWER BEFORE TOUCHING THE
TREE.** ⭐ **LIVING DOCUMENT → REPLACE. DATED LOG → APPEND.**
⚠ **THE ROUND CAP IS 3.** Past it, STOP and bring the findings to the CPO.
⚠ `--review-patch` writes to STDOUT — redirect it. ⚠ The contract gate parses a shell `2>` as a
PATH and refuses it; drive redirect-heavy verification from a Python script instead.
**OPERATIONAL NOTES ARE IN `CLAUDE.md`.**
**FIRST ACTION: `git stash list`** — 17 entries. ⚠ MATCH BY MESSAGE, NEVER BY INDEX. One must never
be rebuilt: **`feat/player-overview-tab`**.

## ⛔ OPEN, ALL THE CPO'S

- ⭐ **Should the column-reference resolver become a committed CI gate?** Evidence now spans two
  MRs: `!125`'s two reverts, and MR 2's three identically-shaped bare reads with two opposite
  correct answers — the discrimination no offline gate performs.
- **#96 — SEVEN consecutive reproductions.** MR 2's instance: `shared.yml:1756`, the 14-name
  `mart_leaderboards.metric_key` list, held `cards_total`. Check all six lists BY EYE every batch,
  then pin the board key mechanically as a SET across the mart, the list and the export.
- ⚠ **`_LEADERBOARD_METRICS` / `_LB_KEEP` (`export_site_data.py:48,53`) are pinned by NO test** —
  `tests/test_export_site_data.py` uses synthetic keys. Pre-existing across every batch.
- **THE REVIEW-LOOP COST IS STRUCTURAL.** `contract.md` is hash-bound, so a one-word prose fix voids
  every verdict. Whether contract NARRATIVE should be hash-excluded (keeping `scope_paths` and
  `acceptance_criteria` hashed) is a governance decision.
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
`site_v2/src/data/README.md`. New ids mean new page URLs and a different built-page count. Needs
ingestion to have run, and **there is still no nightly SCHEDULE on GitLab**.
⚠ **CORRECTED IN MR 2 — the old blanket claim that step 4's renames never reach the built pages was
FALSE.** MR 2's four per-player names ARE in the committed `top_players[]` payload, which comes from
`mart_player_momentum` (`export_site_data.py:871`), a METRIC mart. What holds is narrower and was
measured: whole-token grep over `site_v2/dist` finds them in **ZERO** built files, because Astro
renders server-side and no component reads them. So the roll-forward changes those payload KEYS and
still changes no page. Fixture rows render **12** today (16 minus C, D, F's four).

**THEN THE CATALOGUE→CALCULATION WIRING** — the CPO's own framing: "ensure that the metric
definitions are somehow wired to the different versions of the calculations (based on context)".
Agreed shape, agreed AFTER the renames: a value-equivalence dbt test comparing each model's metric
column to the catalogue formula applied to that context's rows, plus a small `meta:` block on the
metric-computing models — **in the model's own yml, not a new registry**. ⚠ MetricFlow is the
intended destination but **premature**: "I just wanted to make sure that we can upgrade to semantic
layer with MetricFlow once there is a use case." Keep the catalogue machine-readable; adopt nothing
that must be undone.

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
