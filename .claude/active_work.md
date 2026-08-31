# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-31**. **main `9ee88a4`** (after `!130`); `!131` is the goalkeeping MR.
METRIC CATALOGUE NAMING PROGRAMME: **STEP 3 COMPLETE**, **STEP 4 = 6 of 7** — `!125` `shooting`,
`!127` `discipline`, `!128` `defending`, `!129` `passing`, `!130` `duels`, `!131` `goalkeeping`.
**GITLAB** (`glab`, MRs); runner `ci-runner-01`.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ NEXT ACTION: step 4, MR 7 of 7 — the `goals` group. THE LAST BATCH.

    goals          → goals_player           assists       → assists_player
    goals_penalty  → goals_penalty_player   scorer_points → scorer_points_player
    goals_open_play → goals_open_play_player  penalty_won → penalty_won_player
    contribution_share → contribution_player_pct

⛔ **THE AUTHORITY IS `.claude/task/escalations.log`**, block "THE METRIC CATALOGUE NAMING
PROGRAMME", table "⛔ PLAYER, 35 REMAINING". **CITE BY CONTENT, never a line number, never a plan
file.**
⚠ **`contribution_player_pct` is the ONE name in the whole table the CPO did NOT rule on directly** —
the record says so itself: it was my proposal and he did not object. **Flag it; never quote it as
his.** Everything else is verbatim.
⚠ Seed-verified: `player`/`goals` is **10 rows** — these seven plus `goals_per90`, `assists_per90`
and `scorer_points_per90`, which do not change.

⛔⛔ **IT IS THE BIGGEST BATCH OF THE PROGRAMME BY FAR: ~1,645 tokens across ~112 files and 97
distinct maximal tokens** (`!131`: 676 / 76 / 50). `goals` is the most generic stem in the domain —
`goals_for`, `goals_against*`, `goals_total`, `goals_saves`, `goals_conceded`, `goals_per_match`,
`own_goals`, `goal_diff`, `goalsWord`, every scoreline field — so expect the protect side to dwarf
the rename side again (`!131` was 217 renamed / 459 protected).
⛔ **THREE dual-entity collapses at once**, the last three: `goals` (6 `__player` + 12 `__team`
refs), `goals_penalty` (4 + 6), `goals_open_play` (1 + 2) — **31 doc re-points across the six
suffixed blocks, 20 of them TEAM-side.**
⭐ **After MR 7 the `__team`/`__player` split has NO live instance left.** That is the CPO item
carried below.

## ⛔⛔ THE ONE RULE STEP 4 TURNS ON — READ THIS BEFORE WRITING ANY CODE

**A REFERENCE FOLLOWS ITS SOURCE. Shape only tells you WHAT is being read; the SOURCE decides
whether it moves.**

| shape | decision |
|---|---|
| `... as X` (alias) | the metric being written — **always moves** |
| `s.X` (dotted) | follows its source — moves only if that relation renamed it |
| bare `X` | follows its source too |
| a COMMENT | prose about this model — **test for it BEFORE shape analysis**, see below |
| prose | follows the SURFACE it documents — a provider payload is a reference |
| seed `base_relation` / `numerator_expr` / `denominator_expr` / `label_i18n_key` / `description` | references — **never move** |

⭐⭐ **FOUR self-aliasing `sum(X) … as X` SITES, AND ONLY ONE MOVES ITS INNER READ** — the same four
in every batch:

    int_player_club_season__metrics.sql      ← per_fixture ← fct_fixture_player_stats   KEEP
    int_player_season_position__metrics.sql  ← per_fixture ← fct_fixture_player_stats   KEEP
    int_player_season_record.sql             ← player_legs = int_legs__player_match     KEEP
    int_player_season__metrics.sql           ← club_season = int_player_club_season__metrics  MOVES

⚠ **THE MACRO IS THE MIRROR OF THE SEED AND THEY LOOK IDENTICAL.**
`macros/player_benchmark_metrics.sql`'s `num`/`den` are expressions over
`int_player_season_position__metrics` COLUMNS and **move**; the seed's `numerator_expr` /
`denominator_expr` name provider LEG columns and **never** move. Read the SQL, not the sentence.

## ⭐⭐ WHAT `!131` LEARNED THAT MR 7 NEEDS

**1. TWO STANDING RULINGS INTERACT: A RENAME CANNOT DISAMBIGUATE A NAME THE PROVIDER ALSO USES.**
I predicted the hygiene gate's "means more than one thing" list would drop 4 → 3. **It stayed at 4**,
the entry only changing from `goals_against__player, goals_against__team` to
`goals_against, goals_against_player`. The gate groups by COLUMN NAME, and provider PLAYER columns
keep the name under **"yes"** while their `doc()` moves under **"re-point them"**.
⛔ **This corrects `!130`'s contract**, which said the programme frees some of #87's 49 blank
columns. **It does not — the blank count is unchanged at 49.** MR 7's `goals` is a provider column
name too, so expect the same. **Predict it, then measure it; do not assume it resolves.**

**2. SIMULATE THE GENERATOR BEFORE WRITING ANY CODE.** Load `sync_metric_docs_blocks.py`, apply the
renames to a copy of the seed rows in memory, call `_render()`, diff the block-name sets. Held
exactly for two batches running (`!130` 175→172, `!131` 172→167 with the exact sets). Write the
prediction into the contract, then measure it.
⚠ `_blocks()` collapses `__team`/`__player` when the rows stop disagreeing; `_derived()` splits by
entity ALWAYS, so `*__team` derived blocks survive while their `__player` twins are DELETED as
orphans. Verify each deleted block is at 0 refs.

**3. READ THE PRINTED REASONS, NOT ONLY THE COUNTS.** `!131` found a real tool defect that no total,
guard or gate could show: a `{# … #}` docstring ending a sentence in `safe_divide.` made
`sql_shape()` report "dotted", so a correct decision carried a FALSE reason. **The comment test must
run BEFORE shape analysis** — it is hoisted in `rename_s4_goalkeeping.py`; keep it there. The token
counts were identical before and after the fix.

**4. THE FRONTEND CHAIN IS UNGUARDED, AND MR 7 TOUCHES IT AGAIN.** `mart_player_momentum` →
`_TOPPLAYER_DROP` (a DROP-list, so renamed columns reach the payload with **no export edit**) →
`TopPlayer` in `lib/types.ts` → `components/fixture/PlayerRow.astro`. There is **no typecheck**
(`build` is bare `astro build`), **no test references PlayerRow/TopPlayer/top_players**, and the row
may render on **zero** sample pages. `PlayerRow.astro` shows `goals · assists` for outfielders — so
MR 7 hits it squarely. **Read the chain end to end and say in the evidence that no gate covers it.**
⚠ `types.ts` needs INTERFACE-granularity entity resolution (`TopPlayer` = player; `FormMatch`,
`RecentMeeting`, `HeadToHead`, `TeamFixture`, `TeamSeason` = team), and `PlayerRow.astro` needs ROLE
resolution: `player.<field>` moves, `t(lang, "…")` is a UI word and does not.

**5. ORDINARY ENGLISH WORDS ARE A TRAP CLASS.** `saves` cost four protect-only files on `!131`
("saves gigabytes", "what the macro saves"). **`goals` and `assists` are worse** — expect prose,
i18n words (`goalsWord`), and provider fields (`goals_saves`, `goals_conceded`) throughout.

**6. ⛔⛔ `!131` FAILED ROUND 1 5–0 WITH EVERY GATE GREEN, AND BOTH DEFECTS WERE ONE HABIT: A SCOPE
COARSER THAN THE ENTITY IT HAD TO RESOLVE. MR 7 INHERITS BOTH DIRECTLY.**
  - **The TEAM scoreline pair.** `goals_for` / `goals_against` is the team per-fixture scoreline from
    `int_legs__team_match`, reaching `mart_team_fixtures`, `mart_head_to_head` and
    `mart_team_momentum_window`. ⚠ **MR 7's stem is `goals`, and `goals_for` CONTAINS it** — so
    `goals_for`, `goals_against`, `goals_conceded` and every scoreline field are swept and must
    PROTECT. `!131` renamed six of them and `_TEAM_FIXTURE_FIELDS` (a KEEP-list applied with
    `row.get(k)`) would have emitted `null` for every team fixture forever, with no crash, while
    `TeamFixtureRow.astro` still read `fx.goals_against`. **`in_team_scoreline()` is in
    `rename_s4_goalkeeping.py`; keep it and widen it.**
  - **The seed's `interpretation` column.** The protect list was a BLOCKLIST of 5 of the seed's 15
    columns, so free prose was swept. It is now an ALLOWLIST — `SEED_RENAMEABLE_FIELDS =
    {"metric_id"}`. **Keep that shape; never go back to naming the columns to protect.**
  - ⛔ **THE TEST WAS MUTATED TO MATCH THE BUG.** The sweep renamed a fixture dict key in lockstep
    with the code, so `pytest` stayed green. **When an automated rename edits code and test together,
    the test cannot disagree** — running the suite proves nothing about that class.
  - ⚠ **A FILE THAT FALLS TO ZERO RENAMES IS NEVER REOPENED.** The no-op-write guard skips it, so it
    keeps its PREVIOUS text while every other file is rewritten from base. **After tightening a
    classifier, restore the newly-zero files from base explicitly**, and re-reconcile `scope_paths`.

**6. RETIRING A COLLISION RETIRES EVERY WORKED EXAMPLE BUILT ON IT.** `!130` rewrote three prose
sites; `!131` rewrote four more, all of which argued the entity suffix is mandatory using
`goals_against` as the example. **MR 7 will hit the same class again** — `sync_metric_docs_blocks.py`'s
module docstring uses **`goals_open_play`** as its headline example, and that one renames here.
Rewrite to state the RULE and mark the example historical; delete nothing; keep the synthetic
fixtures, which exercise a mechanism that still exists.

## Method that works — six MRs of evidence

Contract FIRST on a clean tree (the gate refuses otherwise; stash by explicit path with a `TEMP-`
label, verify your own entry is on top, pop immediately). Start from
`scratchpad/rename_s4_goalkeeping.py` — **do not rebuild the entity machinery**, `decide()` already
resolves entity on every path. Then: classify every token once and **print the decision with its
resolved entity**; abort before writing on any protected-count change; maximal-token matching;
multiset verify over old ∪ new; abort on an unlisted file; no no-op writes.
⚠ **Verify `seed_entity_lines()` against the seed rows directly** — the first data row is physical
line **2**, and an entity error there is invisible in the diff. Three dual pairs to check this time.
Then gates unpiped with exit codes read bare, mutations watched RED (including the yml-vs-projection
check in BOTH its strong and known-weak form), two site builds, five blinded reviewers, `review.md`
with `--staged-hash`. **ROUND CAP 3.**

⚠ `#96` — no offline gate checks `accepted_values`; only `data:build:mr`. Compare base-vs-branch
**in file order with a length assertion** — a sort-keyed comparison mis-pairs the lists.

## ⛔ AFTER STEP 4 — do not start either without telling the CPO

  - **STEP 5**: nine English `label_en` rows, "on target" → "on goal" (5 team, 4 player). German and
    Finnish are already correct and are NOT touched.
  - **THE SAMPLE ROLL-FORWARD**, owed and unscheduled. ⚠ The obvious recipe is a trap:
    `fetch_fixture_payloads` emits UPCOMING fixtures only. The comparison block has rendered **12**
    rows since `!123` (16 catalogue rows minus four the committed sample cannot feed).

## ⛔ OPEN, AND THE CPO'S — carried, never decided

  - **The column-reference resolver as a committed CI gate.** `!129` found four blind spots; `!130`
    added that it covers dotted references only; `!131` re-confirmed the yml-vs-projection check's
    own bound (a column dropped from the projection but still named in a `safe_divide` on the same
    SELECT leaves it GREEN). Neither is proposed.
  - **`_LEADERBOARD_METRICS` / `_LB_KEEP` pinned by NO test.** ⭐ `!131` showed the OTHER export path
    is unpinned too: `shape_top_players`' DROP-list means `TopPlayer` fields reach the frontend with
    no test between the mart and the component.
  - **#96** — ten reproductions.
  - ⭐ **The `__team`/`__player` block split loses its last live instance when MR 7 lands.** Nothing
    has been removed or weakened, and the guard still protects a future collision — but four files
    now document it with an example that no longer exists. Whether a mechanism with no live instance
    should stay is his call.
  - **#87** — 49 blank columns, and `!131` established the programme does **not** free them.
  - **#98**; **#99** (the export's literal `goals`/`assists` read keys — **MR 7's**).

## Standing traps (also in CLAUDE.md)

`git commit` must be the SOLE command in a Bash call. Heredocs are gate-blocked for file writes —
use Edit/Write. `review.md` must be COMMITTED with `## <exact-routing-key>` headers.
`acceptance_evidence.md` bullets need 2-space indent. ⚠ **CWD persists between Bash calls** — a `cd`
in one call silently breaks repo-relative paths in the next; it bit `!131` twice, once aborting an
apply mid-run. Never read a gate's exit code through a pipe. Contract edits need a CLEAN tree.
