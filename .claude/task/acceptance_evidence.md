# Acceptance evidence — step 4, MR 5: the six player `duels` metrics

Branch `refactor/metric-rename-player-duels`, from main `9ea88b5`.

    duels_total          →  duels_player
    duels_won            →  duels_won_player
    duels_won_pct        →  duels_won_player_pct
    dribbles_attempts    →  dribbles_attempts_player
    dribbles_success     →  dribbles_success_player
    dribbles_success_pct →  dribbles_success_player_pct

**537 tokens across 46 files — 348 renamed, 189 protected.** All six names are in the record
verbatim; none was proposed by me, and no new CPO ruling was needed.

⭐⭐ **THE BATCH WHERE THE SAME TOKEN MOVES ON ONE ENTITY AND STAYS ON THE OTHER.** `duels_won_pct`
is a `metric_id` on BOTH entities; `duels_total` and `duels_won` name TEAM columns on the
`int_legs__team_from_players → int_team_*` chain and PLAYER metric columns on the
`int_legs__player_match → int_player_*` chain. Measured split: **`duels_won_pct` 48 renamed / 46
protected**, `duels_total` 61/30, `duels_won` 60/27.

Every gate below was run **unpiped, with its exit code read bare**.
⚠ `check_ui_i18n_metrics.py` is run because it is a real CI gate but is **NOT evidence** here — it
validates only the frozen `site/**` tree this branch never touches.

## Gates

  - `python scripts/sync_metric_docs_blocks.py --check` — **EXIT=0**, 172 blocks.
  - `python scripts/check_description_hygiene.py` — **EXIT=0**, **1604 descriptions**, 234 blocks
    resolved, every rendered length within 1024 / 16384.
  - `python scripts/check_layer_contract.py` — **EXIT=0**.
  - `python scripts/check_registry_var_sync.py` — **EXIT=0** (48 competitions).
  - `dbt parse` — **EXIT=0**, 97 models, 936 tests, 9 seeds.
  - `python -m pytest -q` — **1009 passed, 1 skipped, 14 subtests**, matching the `9ea88b5`
    baseline exactly.
  - `sqlfluff lint` on the nine changed models, from the REPO ROOT, jinja templater, full rule set —
    **byte-identical** to a re-lint of the same nine files stashed back to base content. LT05 0→0;
    rule tally `['LT02','PRS','ST11','TMP']` both sides.
  - `npm test` — **76/76**.
  - `node scripts/check-page-specs.mjs` — **EXIT=0**.
  - The site built **TWICE**, base and branch: 66 pages, `audit-seo: 67 built page(s) checked. OK.`

## ⭐ Three predictions, written into the contract BEFORE the code, then measured

`!129` had three of mine disproved by measurement, so this batch wrote them down first.

  - **Doc blocks 175 → 172.** Predicted by running the real generator against the renamed seed held
    in memory. Measured after regeneration: **172**, and the removed/added sets are identical to the
    simulation term for term — 10 removed (5 plain renames, the `__player`/`__team` pair, and 3
    `duels_won_pct_*__player` yoy orphans), 7 added. **CONFIRMED.**
  - **Description count stays 1604.** Measured: **1604**, identical to base. The "re-point them"
    ruling holds for a sixth batch. **CONFIRMED.**
  - **The "means more than one thing" list drops 5 → 4.** Measured: **4**, with `duels_won_pct` gone
    and `goals_against` / `goals_open_play` / `goals_penalty` / `league_code` remaining. The 49
    blank columns are unchanged — freeing them is **#87** and is deliberately not done here.
    **CONFIRMED.**

## ⭐⭐ The block-pair collapse — the surface this batch adds

`sync_metric_docs_blocks._blocks()` splits a metric into `__team`/`__player` only "where a metric's
rows disagree". Renaming the player row makes `duels_won_pct` unambiguous, so the pair collapses:

  - `doc('duels_won_pct__player')` → `doc('duels_won_player_pct')` — 6 references.
  - `doc('duels_won_pct__team')` → `doc('duels_won_pct')` — **5 references, a TEAM-SIDE edit with
    no team metric changing.** Nothing in this programme has required that before.
  - `_derived()` splits by entity ALWAYS, not only on disagreement, so the three
    `duels_won_pct_*__team` blocks and their 6 references are untouched, while their `__player`
    twins are deleted — that is the whole −3.

**77 `doc()` references re-point in total**, the largest doc surface of any batch: 35 `shared.yml`,
8 each `int_team_season.yml` / `int_legs.yml`, 6 each `int_momentum.yml` /
`int_player_season_position.yml` / `int_season_record.yml`, 4 each `core.yml` /
`int_player_club_season.yml`. The shipped precedent is `core.yml:776-777` from `!129` — a protected
provider column `passes_total` carrying `doc('passes_player')`.

## Mutations — each watched going RED, then reverted and re-run green

  - **A stale `metric_id` in the seed** → `sync_metric_docs_blocks --check` **EXIT=1**
    ("has drifted from … metric_catalogue.csv"). Reverted: EXIT=0.
  - **A `doc()` naming a block that does not exist** → `check_description_hygiene` **EXIT=1**,
    `core.yml :: core/fct_fixture_player_stats/duels_total - unresolved docs block:
    'duels_player_NO_SUCH_BLOCK'`. Reverted: EXIT=0.
    ⭐ **This corrects a claim in my own contract.** It speculated that the hygiene gate "has no
    dangling-reference check that I could find" and that one might need writing. It has one; I had
    grepped for the wrong wording ("dangling" / "unknown block" rather than "unresolved docs
    block"). **No new guard is needed, and none is proposed.** ⚠ `sync_metric_docs_blocks --check`
    does NOT catch this (EXIT=0) — the two gates are complementary, not redundant.
  - **The MR 4 round-2 defect, reproduced** — `mart_player_season_record`'s final SELECT reverted to
    the old names while its yml and CTEs carry the new ones → the yml-vs-projection check
    **EXIT=1**, `yml declares ['duels_won_player'] but the final SELECT does not project them`.
    Reverted: EXIT=0.
  - **The frontend mis-scope, reproduced** — see `rendered_page_evidence.md`. `npm test` **75/1**
    and `check-page-specs.mjs` **EXIT=1**.

⛔ **AND ONE MUTATION EXPOSED A REAL BOUND ON THE yml-vs-projection CHECK, reported rather than
glossed.** A NARROWER version of the round-2 defect — the column dropped from the projection but
still named inside a `safe_divide(...)` in the same final SELECT — leaves the check **GREEN**. It
tests token PRESENCE in the final SELECT, not that the column is projected as an output. The model
still could not compile. The check catches the defect it was built for, and this MR's tree is clean
under both forms, but it is weaker than `!129`'s write-up implied — and the resolver does not cover
the gap either: it checks **dotted** references only (42 here) and reports bare ones as unresolved.

## An independent check, and the resolver

`check_yml_vs_projection.py` (built on `!129`, not committed): **20 models checked, zero
mismatches.** One model is reported as not checkable — `int_team_season__metrics`, whose final
select is a wildcard — rather than silently passed.

The column-reference resolver: **42 dotted references resolved, zero broken**; 4 bare reads in
`int_player_momentum__metrics.sql` reported as unresolved rather than skipped silently.

## The entity discrimination, verified where it is invisible

The seed is the one file where an entity error leaves no trace in the diff, because both
`duels_won_pct` rows carry the same token. `seed_entity_lines()` had an off-by-one — it numbered the
first data row as physical line 1 instead of 2 — which would have handed the TEAM row (line 17) the
PLAYER decision and vice versa. Found and fixed before the first run, then verified directly against
all 11 duels/dribbles seed rows: **0 mismatches**, line 17 → `team`, line 18 → `player`.

⭐ The planning note for this batch asserted that "a token→decision map cannot resolve it" and that
the classifier needed re-keying by entity. **Tested rather than believed, and it was wrong:**
`decide()` already resolves entity on every path, and only `PROTECT_TOKENS` is consulted before
entity is known — which is sound because no token here needs both decisions. What changed is that
the entity is now printed in every reason, so the discrimination is checkable rather than trusted.

## #96, at its widest yet — all six lists, verified in file order

  - `shared.yml:1756`, the 14-name board list — **4 entries move**: `dribbles_success`,
    `duels_won`, `duels_won_pct`, `dribbles_success_pct`.
  - `int_competition_benchmarks.yml:105` and `shared.yml:2186`, the two 18-name player lists —
    **2 entries move each**: `duels_won_pct`, `dribbles_success_pct`. `duels_won_per90` and
    `dribbles_success_per90` stay.
  - `int_competition_benchmarks.yml:27` and `:66`, and `shared.yml:2080`, the three 22-name TEAM
    lists — **0 entries move**, `duels_won_pct` and `duels_per_match` intact.

**8 entries across 3 of 6 lists; no list changed length.** ⚠ The first comparison script mis-paired
base and branch lists (its sort key differed between the two sides) and reported four lists as
length-changed; it was rewritten to compare in file order with an identity assertion. The figures
above are from the corrected run.

## Nine singular range tests, split by entity — a first

Six PLAYER tests rename (`std_player_*`, `player_profile_*`, `mart_leaderboards_*`, for both
ratios); three TEAM tests protect (`momentum_team_`, `team_profile_`, `std_team_`). `!129` had four,
all renaming.

## The junction, and why nothing there moves

`int_legs__team_from_players.sql:32-35` self-aliases `sum(duels_total) as duels_total` — a
player-named leg column in, a TEAM column out under the same word. Its `key_passes` neighbour on
line 28 already had two different names, so `!129` could reason about the halves separately; here
they are the same word. The file is excluded as a provider surface and BOTH halves stay: renaming
either would ship a model that cannot execute. Its two consumers, `int_team_momentum__metrics` and
`int_team_season_record`, read `p.duels_total` / `pl.duels_total` from it and are unchanged.

## Prose the rename falsifies, rewritten by hand

Three sites cite `duels_won_pct` as the live example of a dual-entity id, and after this MR every
one is false either way. There is no durable replacement — all six dual-entity ids rename on the
player side, five of them in the two remaining batches. Each was rewritten to state the rule without
naming an instance; `sync_metric_docs_blocks.py`'s is marked historical rather than deleted, because
the trap it warns about is still real. The classifier PROTECTS all four tokens and prints "prose the
rename FALSIFIES", so these are visible separate edits, not substitutions buried in a 348-token diff.
