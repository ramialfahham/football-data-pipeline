# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-08-31**. **main `9ea88b5`** (after `!129`); `!130` is the duels MR.
METRIC CATALOGUE NAMING PROGRAMME: **STEP 3 COMPLETE**, **STEP 4 = 5 of 7** — `!125` `shooting`,
`!127` `discipline`, `!128` `defending`, `!129` `passing`, `!130` `duels`.
**GITLAB** (`glab`, MRs); runner `ci-runner-01`.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⭐⭐ NEXT ACTION: step 4, MR 6 of 7 — the `goalkeeping` group

    saves                 → saves_player          goals_against        → goals_against_player
    save_pct              → saves_player_pct      shots_on_goal_against → shots_on_goal_against_player

⛔ **THE AUTHORITY IS `.claude/task/escalations.log`**, block "THE METRIC CATALOGUE NAMING
PROGRAMME", table "⛔ PLAYER, 35 REMAINING". **CITE BY CONTENT, never a line number, never a plan
file.** `_player` before a trailing `_pct` is RULING 5. Remaining after `goalkeeping`: `goals` (10).
⚠ **VERIFIED FROM THE SEED**: `player`/`goalkeeping` is **5 rows** — these four plus `saves_per90`,
which does NOT change.

⛔⛔ **IT IS THE BIGGEST AND MOST ENTANGLED BATCH LEFT: roughly 700 tokens across ~86 files**
(before provider exclusions) versus duels' 537/46 — and **TWO dual-entity ids at once**, `saves` and
`goals_against`, where duels had one. Everything below about the collapse happens TWICE.
⚠ Substring traps in both directions: the TEAM metric **`saves_pct`** contains the stem `saves` and
must PROTECT (team `save_ratio → saves_pct` landed in step 3); `goals_against` is inside
`goals_against_per_match`, `goals_against_sum_season` and their yoy forms, all TEAM.

## ⛔⛔ THE ONE RULE STEP 4 TURNS ON — READ THIS BEFORE WRITING ANY CODE

**A REFERENCE FOLLOWS ITS SOURCE. Shape only tells you WHAT is being read; the SOURCE decides
whether it moves.**

| shape | decision |
|---|---|
| `... as X` (alias) | the metric being written — **always moves** |
| `s.X` (dotted) | follows its source — moves only if that relation renamed it |
| bare `X` | follows its source too — **not** "is it inside a self-aliasing aggregate" |
| prose | follows the SURFACE it documents — a provider payload is a reference |
| seed `base_relation` / `numerator_expr` / `denominator_expr` / `label_i18n_key` / `description` | references — **never move** |

⭐⭐ **FOUR self-aliasing `sum(X) … as X` SITES, AND ONLY ONE MOVES ITS INNER READ.** The same four
recur in every batch:

    int_player_club_season__metrics.sql      ← per_fixture ← fct_fixture_player_stats   KEEP
    int_player_season_position__metrics.sql  ← per_fixture ← fct_fixture_player_stats   KEEP
    int_player_season_record.sql             ← player_legs = int_legs__player_match     KEEP
    int_player_season__metrics.sql           ← club_season = int_player_club_season__metrics  MOVES

⚠ **THE MACRO IS THE MIRROR OF THE SEED AND THEY LOOK IDENTICAL.**
`macros/player_benchmark_metrics.sql`'s `num`/`den` are expressions over
`int_player_season_position__metrics` COLUMNS and **move**; the seed's `numerator_expr` /
`denominator_expr` name provider LEG columns and **never** move. Read the SQL, not the sentence.

## ⭐⭐ WHAT `!130` LEARNED THAT MR 6 NEEDS

**1. A RENAME CAN COLLAPSE A DISAMBIGUATION, AND THAT EDITS THE *OTHER* ENTITY.**
`sync_metric_docs_blocks._blocks()` splits a metric into `__team`/`__player` only where the rows
disagree. Renaming the PLAYER side makes the name unambiguous, so the pair collapses and
`doc('X__team')` must become `doc('X')` — **team-side edits caused by a player rename, which no
token sweep finds from the player side.** For MR 6 that is **38 references**: `saves__player` 12 +
`saves__team` 6, `goals_against__player` 8 + `goals_against__team` 12.
⚠ `_derived()` behaves DIFFERENTLY: it splits by entity ALWAYS, so `*__team` derived blocks survive
while their `__player` twins (orphans, zero refs) are DELETED. That asymmetry is the whole block-count
delta. `goals_against` has `_sum_season` / `_per_match_*` / yoy derived forms, so expect more of both.

**2. SIMULATE THE GENERATOR BEFORE WRITING ANY CODE.** Load `sync_metric_docs_blocks.py`, apply the
renames to a copy of the seed rows in memory, call `_render()`, and diff the block-name sets. `!130`
predicted 175 → 172 with exact removed/added sets and measured exactly that. `!129` had three
predictions disproved after the fact. **Write the prediction into the contract, then measure it.**

**3. THE CLASSIFIER ALREADY HANDLES DUAL ENTITY — do not rebuild it.** `!130`'s planning note
claimed "a token→decision map cannot resolve it"; that was **wrong**. `decide()` resolves entity on
every path (enclosing `- name: <model>` for yml, the `entity` column for the seed, file membership
for SQL); only `PROTECT_TOKENS` is consulted before entity is known, which is sound as long as no
token needs BOTH decisions. Start from `scratchpad/rename_s4_duels.py`.
⚠ **`seed_entity_lines()` numbers the first data row as physical line 2, not 1.** `!130` had that
off-by-one and it would have swapped the team and player `duels_won_pct` rows **invisibly in the
diff**, because both carry the same token. **Verify the resolver against the seed rows directly.**

**4. THE RENDERED-PAGE COMPARISON DOES NOT DISCRIMINATE. Stop claiming it does.** `!130` claimed it
would (the team labels really do render), performed the mis-scope, and found **the build never
completes** — `prebuild` runs the label guards first, so there is no dist to compare. ⚠ The failed
build leaves the PREVIOUS dist in place and measuring it looks perfectly healthy. What actually
discriminates: `npm test`'s **"every labelKey is a label_i18n_key the catalogue actually declares"**,
which binds `metricRows.ts` to the SEED's `label_i18n_key` column (a consistent two-sided frontend
rename cannot satisfy it), and `check-page-specs.mjs`.

**5. GUARD FACTS, MEASURED.** `check_description_hygiene` **does** catch a dangling `doc()`
("unresolved docs block") — `!130`'s contract wrongly speculated it did not; no new guard is needed.
`sync_metric_docs_blocks --check` does NOT catch that, but does catch a stale seed `metric_id`.
⚠ The `check_yml_vs_projection.py` tool has a real bound: a column dropped from the final SELECT but
still named inside a `safe_divide(...)` in that same SELECT leaves it **GREEN** — it tests token
PRESENCE, not projection. The resolver covers only **dotted** references.

## Method that works — five MRs of evidence

Contract FIRST on a clean tree (the gate refuses otherwise; stash by explicit path with a `TEMP-`
label, verify your own entry is on top, pop immediately). Then: classify every token once and
**print the decision with its resolved entity**; abort before writing on any protected-count change;
maximal-token matching; multiset verify over old ∪ new vocabulary; abort on an unlisted file; no
no-op writes. Then gates unpiped with exit codes read bare, mutations watched RED, two site builds,
five blinded reviewers, `review.md` with `--staged-hash`. **ROUND CAP 3.**

⚠ `#96` — no offline gate checks `accepted_values` lists; only `data:build:mr` does. `!130` hit
**all six lists** (8 entries across 3; the three 22-name TEAM lists must not move). Check them by eye
every batch, and compare base-vs-branch **in file order** with a length assertion — a sort-keyed
comparison mis-pairs the lists and reports phantom changes.

## ⛔ AFTER STEP 4 — do not start either without telling the CPO

  - **STEP 5**: nine English `label_en` rows, "on target" → "on goal" (5 team, 4 player). German and
    Finnish are already correct and are NOT touched.
  - **THE SAMPLE ROLL-FORWARD**, owed and unscheduled. ⚠ The obvious recipe is a trap:
    `fetch_fixture_payloads` emits UPCOMING fixtures only. The comparison block has rendered **12**
    rows since `!123` (16 catalogue rows minus four the committed sample cannot feed); the roll-forward
    is what restores them.

## ⛔ OPEN, AND THE CPO'S — carried, never decided

  - **The column-reference resolver as a committed CI gate.** `!129` found four blind spots in one MR
    and argued against committing it; `!130` added that it covers dotted references only. The
    yml-vs-projection check is the better candidate but has the bound in §5 above. Neither is proposed.
  - **`_LEADERBOARD_METRICS` / `_LB_KEEP` in `scripts/export_site_data.py` are pinned by NO test.**
    Confirmed independently by `platform-reviewer` on `!127`, `!128`, `!129`. `!130` moved six more.
  - **#96** — nine reproductions now.
  - ⭐ **NEW from `!130`: the `__team`/`__player` block split loses its last live instance at the end
    of step 4.** All six dual-entity ids (`duels_won_pct`, `saves`, `goals_against`, `goals`,
    `goals_open_play`, `goals_penalty`) rename on the player side. Nothing was removed or weakened —
    `_derived()` still suffixes by entity and the abort still guards a future collision — but whether
    a mechanism with no live instance should stay is his call.
  - **#87** — 49 columns blank because their name means more than one thing. `!130` took that list
    from 5 names to 4; MR 6 takes it to 2. Filling them is #87 and is out of scope for the renames.

## Standing traps (also in CLAUDE.md)

`git commit` must be the SOLE command in a Bash call. Heredocs are gate-blocked for file writes —
use Edit/Write. `review.md` must be COMMITTED with `## <exact-routing-key>` headers.
`acceptance_evidence.md` bullets need 2-space indent or the gate reads zero criteria. ⚠ **CWD
persists between Bash calls** — a `cd` in one call silently breaks repo-relative paths in the next,
which is how a mutation nearly went un-reverted on `!130`. Never read a gate's exit code through a
pipe. Contract edits need a CLEAN tree.
