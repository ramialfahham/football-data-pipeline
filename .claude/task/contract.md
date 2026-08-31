# Task contract — rename the six player duels metrics (step 4, MR 5)

objective: >
  **STEP 4 of the metric catalogue naming programme, MR 5 of seven.** The `duels` family of the
  player catalogue:

      duels_total          →  duels_player
      duels_won            →  duels_won_player
      duels_won_pct        →  duels_won_player_pct
      dribbles_attempts    →  dribbles_attempts_player
      dribbles_success     →  dribbles_success_player
      dribbles_success_pct →  dribbles_success_player_pct

  `!125` shipped `shooting`, `!127` `discipline`, `!128` `defending`, `!129` `passing`. Remaining
  after this one: `goalkeeping` (5) · `goals` (10).

  ⛔⛔ **THE RULE IS UNCHANGED AND IS STILL THE WHOLE DESIGN: A REFERENCE FOLLOWS ITS SOURCE.**
  Shape only tells you WHAT is being read; the source decides whether it moves.

  ⭐⭐ **WHAT IS NEW HERE: THE SAME TOKEN MOVES ON ONE ENTITY AND STAYS ON THE OTHER.**
  `duels_won_pct` is a `metric_id` on BOTH entities. `duels_total` and `duels_won` name TEAM
  columns on the `int_legs__team_from_players → int_team_*` chain and PLAYER metric columns on the
  `int_legs__player_match → int_player_*` chain. Measured split: `duels_won_pct` **48 renamed / 46
  protected**, `duels_total` 61/30, `duels_won` 60/27.

refs: >
  **`.claude/task/escalations.log`, the block "THE METRIC CATALOGUE NAMING PROGRAMME"**, its table
  "⛔ PLAYER, 35 REMAINING" — all six renames appear in it verbatim.
  ⭐ Cited by CONTENT, never by line number and never a plan file.
  ⭐ `duels_won_player_pct` and `dribbles_success_player_pct` are **RULING 5's shape** — `_player`
  sits BEFORE a trailing `_pct` — which the table already spells out for both.
  ⚠ Group membership verified FROM THE SEED, not assumed: `player`/`duels` is **8 rows** — these
  six plus `duels_won_per90` and `dribbles_success_per90`, neither of which changes, because
  `_per90` already means player.

  ⭐ **TWO STANDING CPO RULINGS, applied unchanged:** **"re-point them"** (a reference to a renamed
  doc block moves even from a TEAM or provider column — 77 references here) and **"yes"**
  (provider and per-match surfaces keep the provider name — the leg models, the core fact and the
  two per-match marts are excluded, 46 tokens).

  ⚠ **NO NEW CPO RULING WAS NEEDED OR TAKEN FOR THIS BATCH.** Unlike `!129`, every target name is
  already in the record. One FORM decision was taken under "the transformation layer decides the
  FORM, the CPO decides the NAME" and is recorded in `decisions_taken` §3.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/macros/player_benchmark_metrics.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_player_momentum.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/mart_player_season_record.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_metric_catalogue_unique_by_entity.sql
  - docs/wireframes/01_fixture_page.md
  - docs/wireframes/03_player_profile.md
  - docs/wireframes/10_home.md
  - docs/wireframes/12_player_stats.md
  - docs/wireframes/99_gaps_register.md
  - docs/wireframes/metrics_display.md
  - scripts/export_site_data.py
  - scripts/sync_metric_docs_blocks.py
  - tests/test_export_site_data.py
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/active_work.md

# ⚠ This list is the EXACT changed set — reconciled against `git diff --name-only` in both
# directions, nothing extra either way. Derived from the classifier's DRY RUN (files with zero
# renames are never opened), not predicted.
#
# ⭐⭐ NOTE THERE IS NO `site_v2/` ENTRY. `!129` was the first frontend source change of step 4 and
# its contract said so loudly. **THAT IS NOT CARRIED HERE**: all six `site_v2` occurrences are the
# TEAM i18n label keys `metrics.duels_per_match.label` / `metrics.duels_won_pct.label`, both of
# which must survive byte-identical. The empty-`site_v2`-diff claim is RE-DERIVED for this batch,
# not inherited — inheriting a claim in the other direction is what cost `!128` two rounds.
#
# ⭐ THREE FILES CHANGE BY HAND, NOT BY THE SWEEP — `seeds/schema.yml`,
# `tests/assert_metric_catalogue_unique_by_entity.sql` and `scripts/sync_metric_docs_blocks.py`.
# The classifier PROTECTS all of their tokens and prints "prose the rename FALSIFIES". See
# decisions_taken §3.
#
# ⚠ SWEPT BUT NOT CHANGED — 18 files the classifier read and decided, every token PROTECTED, kept
# IN the sweep so a decision is printed for each rather than being an invisible exclusion:
#  · nine TEAM models: int_team_season__metrics_cumulative, int_team_momentum__metrics,
#    int_team_season_record, int_team_profile__yoy, int_team_competition_benchmark_metrics_long,
#    mart_team_momentum, mart_team_profile, mart_team_season_record (and int_team_profile.yml)
#  · docs/wireframes/14_team_stats.md — the team Duels row
#  · tests/test_sync_metric_docs_blocks.py — its one token is the TEAM `duels_won_pct_this_season`
#  · ⭐ FOUR FRONTEND FILES: site_v2/src/i18n/strings.ts, lib/metricRows.ts,
#    specs/competition/matches/fixture.spec.json, specs/teams/team.spec.json — every token is a
#    TEAM label key, and BOTH of them are among the 12 rows that actually RENDER.
#
# ⚠ NOT IN SCOPE, each for a stated reason:
#  · `.claude/task/review_input.patch` — regenerated review paperwork, hash-excluded by design.
#  · `site_v2/src/data/**` (1,307 tokens) — the committed sample; the declared transient, refreshed
#    only by the owed sample roll-forward, which is NOT started here.
#  · the seven provider `.sql` files (46 tokens) — the CPO's "yes" ruling.

protected_override: >
  none. No guard, threshold, schedule or exemption is loosened, and no `--full-refresh` is implied:
  every renamed column is on a TABLE-materialised model or a view, not an incremental fact.

impact_map: >
  ⭐ **RUN ON THIS BRANCH BEFORE THE FIRST EDIT, AND PASTED VERBATIM** — not described, not carried
  from a previous contract. `!128` lost a round to a lineage sentence that was true of an earlier
  branch and had never been run for the batch it appeared in.

      $ dbt ls --resource-type model --select int_player_season__metrics+ \
          int_player_club_season__metrics+ int_player_momentum__metrics+ \
          int_player_season_position__metrics+ int_player_season_record+ mart_leaderboards+ \
          mart_player_momentum+ mart_player_profile+ mart_player_season_record+ \
          int_player_competition_benchmarks+ mart_player_competition_benchmarks+

      football_data_pipeline.4_intermediate.domestic_league.team_season.int_player_season__metrics
      football_data_pipeline.4_intermediate.shared.int_player_club_season__metrics
      football_data_pipeline.4_intermediate.shared.int_player_competition_benchmarks
      football_data_pipeline.4_intermediate.shared.int_player_momentum__metrics
      football_data_pipeline.4_intermediate.shared.int_player_profile__yoy
      football_data_pipeline.4_intermediate.shared.int_player_season_position__metrics
      football_data_pipeline.4_intermediate.shared.int_player_season_record
      football_data_pipeline.5_marts.shared.mart_leaderboards
      football_data_pipeline.5_marts.shared.mart_player_career
      football_data_pipeline.5_marts.shared.mart_player_competition_benchmarks
      football_data_pipeline.5_marts.shared.mart_player_momentum
      football_data_pipeline.5_marts.shared.mart_player_profile
      football_data_pipeline.5_marts.shared.mart_player_season_record

  **13 models.** Nine change by direct SQL edit; two more (`int_player_competition_benchmarks`,
  `mart_player_competition_benchmarks`) change only through `player_benchmark_metrics()` and need
  no edit of their own. ⚠ **TWO ARE AN OVER-COUNT**: `int_player_profile__yoy` and
  `mart_player_career` carry NONE of the six names — verified by whole-tree grep, not assumed.

  ⭐ `int_player_profile__yoy` carrying nothing is INDEPENDENT CONFIRMATION that the
  `duels_won_pct_this_season` / `_prev_season` / `_delta_yoy` columns are **team-only**. They live
  on `int_team_profile__yoy` and `mart_team_profile`; there is no player twin, and their
  `__player` doc blocks are orphans.

  **The whole `int_team_*` / `mart_team_*` chain is UNCHANGED SQL.**
  `int_legs__team_from_players.sql:32-35` self-aliases `sum(duels_total) as duels_total` — a
  player-named leg column in, a TEAM column out under the same word — and both stay. That differs
  from its `key_passes` neighbour on line 28, where the two names already differed and `!129` could
  reason about them separately. Here the file is excluded as a provider surface and BOTH halves are
  correctly untouched; renaming either would ship a model that cannot execute.

  Downstream of the marts: `scripts/export_site_data.py` (6 literals) and
  `tests/test_export_site_data.py` (4 fixture literals). No `site_v2/src/**` source consumes a
  renamed name.

acceptance_criteria:
  - ⛔ **CORRECTED AFTER MEASUREMENT — THE RENDERED-PAGE COMPARISON IS NOT THE DISCRIMINATING GUARD, AND THE FIRST DRAFT OF THIS LINE WAS WRONG.** It claimed that mis-scoping the TEAM `duels_won_pct` would make a visible label disappear from the built pages. It does not: the mis-scope was actually PERFORMED, and **the build never completes** — `prebuild` runs the label guards first, so no page is produced at all and there is nothing to compare. What actually discriminates is named and measured in `rendered_page_evidence.md`. The dist comparison stands as a CONFIRMATION that the delivered tree is correct: 12 rows / 7 headings / none added / none removed, base vs branch, measured structurally from the markup under `site_v2/dist/`, element for element, never by substring.
  - ⭐ **AND THE GUARD THAT DOES DISCRIMINATE IS STRONGER THAN THE ONE `!129` NAMED.** Under the simulated mis-scope, `npm test` fails 75/1 on "every labelKey is a label_i18n_key the catalogue actually declares" — a binding from `metricRows.ts` to the SEED's `label_i18n_key` column, not merely to `strings.ts` — and `check-page-specs.mjs` exits 1 with 2 violations, read UNPIPED.
  - ⭐ **NO `site_v2/` FILE CHANGES**, re-derived for this batch rather than inherited: all four swept frontend files are byte-identical and still carry `metrics.duels_won_pct.label`. No name is HALF-renamed — each new name appears everywhere the old one did in the models, ymls, seed, macro, export and wireframes that this MR moves, and every surviving old name is a provider read or a TEAM column, pinned by count per file.
  - `sync_metric_docs_blocks.py --check` and `check_description_hygiene.py` both pass AND are each watched going RED — the first on a stale `metric_id` in the seed, the second on a deliberately dangling `doc()`. ⚠ If the hygiene gate does NOT go red on the dangling reference, that is a finding to report, not a step to skip.
  - ⭐ Every dotted AND bare column reference to a renamed name resolves against the relation it actually reads, checked statically; and the yml-vs-projection check built on `!129` reports zero mismatches across every changed model.
  - ⛔ The three 22-name TEAM `accepted_values` lists are byte-identical, with their `duels_won_pct` and `duels_per_match` entries intact.

decisions_taken: >
  All six names come from the record, verbatim. No name in this batch was proposed by me.

  ⭐⭐ **ONE QUESTION, ASKED OF EVERY OCCURRENCE: DID THE RELATION THIS READS FROM RENAME THE
  COLUMN?** 537 tokens classified once, each decision printed — **348 renamed, 189 protected**
  across 46 files, reconciling exactly against `git grep` in both directions. 2,153 tokens
  repo-wide: 1,570 untouched (the sample, `.claude/**`, `site/**`, `docs/audits/**`, the
  regenerated `metric_columns.md`), 46 in provider `.sql`.

  ⭐⭐ **§1. THE CLASSIFIER NEEDED NO STRUCTURAL CHANGE, AND THE PLANNING NOTE THAT SAID IT DID WAS
  WRONG.** The handover for this batch asserted that "a token→decision map cannot resolve it" and
  that the fix was to re-key the map by entity. Tested rather than believed: `decide()` ALREADY
  resolves entity on every path — the enclosing `- name: <model>` for yml, the `entity` column for
  the seed, file membership for SQL — and only `PROTECT_TOKENS` is consulted before entity is
  known. The flat maps are therefore sufficient **provided no token needs both decisions**, and
  none does. Every token that must protect everywhere (`duels_won_per90`,
  `dribbles_success_per90`, the six team-only yoy forms, the three team range tests) never renames;
  every token that renames is decided per site. What DID change is that the entity now appears in
  every printed reason, so a reviewer can check the discrimination instead of trusting it.
  ⚠ One real bug was found and fixed before the first run: `seed_entity_lines()` numbered the first
  data row as physical line 1 instead of 2, shifting every entity by one row. On this seed that
  would have handed the TEAM `duels_won_pct` row (line 17) the PLAYER decision and vice versa — and
  it would have been **invisible in the diff**, because both rows carry the same token. Verified
  directly against all 11 duels/dribbles seed rows: 0 mismatches.

  ⭐⭐ **§2. THE RENAME COLLAPSES A DISAMBIGUATED BLOCK PAIR — SIMULATED, NOT PREDICTED.**
  `sync_metric_docs_blocks._blocks()` splits a metric into `__team`/`__player` only "where a
  metric's rows disagree". Once the player row renames, `duels_won_pct` is unambiguous and the pair
  collapses. Run against the real generator with the renamed seed held in memory, before any code:

      175 → 172 blocks
      REMOVED  dribbles_attempts · dribbles_success · dribbles_success_pct · duels_total ·
               duels_won · duels_won_pct__player · duels_won_pct__team ·
               duels_won_pct_{this_season,prev_season,delta_yoy}__player
      ADDED    dribbles_attempts_player · dribbles_success_player · dribbles_success_player_pct ·
               duels_player · duels_won_player · duels_won_player_pct · duels_won_pct

  Three consequences, all load-bearing:
    · **`doc('duels_won_pct__team')` → `doc('duels_won_pct')` is a TEAM-SIDE edit on 5 references
      with no team metric changing.** Nothing in this programme has required that before.
    · `_derived()` splits by entity ALWAYS, not only on disagreement, so the three
      `duels_won_pct_*__team` blocks and their 6 references are untouched — while their `__player`
      twins are DELETED, because the stem stops resolving for `player`. That is the whole −3.
    · **77 `doc()` references re-point**, the largest doc surface of any batch: 35 in `shared.yml`,
      8 each in `int_team_season.yml` / `int_legs.yml`, 6 each in `int_momentum.yml` /
      `int_player_season_position.yml` / `int_season_record.yml`, 4 each in `core.yml` /
      `int_player_club_season.yml`.

  The shipped precedent for a protected column carrying a re-pointed reference is `core.yml:776-777`
  from `!129`: `- name: passes_total` beside `description: "{{ doc('passes_player') }}"`. This batch
  does the identical thing for four more provider columns.

  ⭐ **§3. A FORM DECISION, MINE, RECORDED RATHER THAN ESCALATED.** Three prose sites cite
  `duels_won_pct` as the live EXAMPLE of a dual-entity id:
      dbt_project/seeds/schema.yml                                    "e.g. duels_won_pct exists for both team and player"
      dbt_project/tests/assert_metric_catalogue_unique_by_entity.sql  "(e.g. duels_won_pct)"
      scripts/sync_metric_docs_blocks.py                              "as duels_won + _pct, which is a REAL metric"
  After this MR every one of those sentences is FALSE — renaming the token makes the claim wrong,
  and leaving it makes the claim wrong. **And there is no durable replacement example**: all six
  dual-entity ids (`duels_won_pct`, `saves`, `goals_against`, `goals`, `goals_open_play`,
  `goals_penalty`) rename on the player side, five of them in the two remaining batches, so by the
  end of step 4 the collision has no live instance at all.
  **Decision: rewrite the phrasing to describe the rule without naming a live instance.** That is a
  FORM decision under "the transformation layer decides the FORM, the CPO decides the NAME"; no
  name is chosen and no mechanism changes. The classifier PROTECTS all four tokens and prints "prose
  the rename FALSIFIES", so the rewrite is a visible, separate, non-mechanical edit rather than a
  substitution hidden in a 348-token diff.
  ⛔ **NOTHING IS DELETED.** `_derived()` still suffixes by entity, `(metric_id, entity)` is still
  the seed's real key, and `_blocks()`'s abort still guards a future collision. The observation that
  the split loses its last live instance is CARRIED to the CPO in `decisions_reserved`, not acted on.

  ⭐ **§4. THE MACRO'S `num`/`den` MOVE; THE SEED'S DO NOT.** They look identical and are opposite.
  The seed's `numerator_expr` / `denominator_expr` reference LEG columns (`sum(duels_won)`,
  `sum(duels_total)`) on both entities — provider names, never moved; all 13 seed formula
  occurrences protect and only the 6 `metric_id`s move. `player_benchmark_metrics.sql`'s `num`/`den`
  are, by its own docstring, "expressions over the same `int_player_season_position__metrics`
  atoms", and `!129` already renamed `'num': 'passes_accurate_player', 'den': 'passes_player'`
  there. So both duels rows move all four fields — key, col, num, den — 8 in total. This also settles
  `shared.yml`'s `metric_numerator` / `metric_denominator` prose, which names the macro's atoms and
  not the seed's: read the SQL, not the sentence.

  ⭐ **§5. TWO WIREFRAMES CARRY BOTH ENTITIES, AND A FILE-LEVEL SCOPE WOULD BE WRONG FOR BOTH.**
  `10_home.md` documents the player boards AND the team boards; `metrics_display.md` the team
  comparison rows AND the player match rows. Resolved by SECTION mark, nearest preceding wins, with
  an inline entity statement in the token's own PARAGRAPH taking precedence — and the resolved
  entity is printed for every prose token:
      10_home.md:176         PROTECT — team prose (section mark '~~**Six team boards.**~~')
      metrics_display.md:141 PROTECT — team prose (section mark '## Team metrics — LOCKED')
      metrics_display.md:221 RENAME  — player prose (inline mark 'dropped team-side; stays a player metric')
  The last one matters: it sits INSIDE the team section, and the sentence that overrides it wraps
  onto the following line — the same straddling-construct shape whose line-scoped test FAILed
  `!128` round 1, which is why the inline check is paragraph-scoped too.

  ⭐ **§6. `03_player_profile.md` CARRIES BOTH SURFACES ELEVEN LINES APART**, and it is the file
  that failed `!128`. The season-stats bundle (`:95-96`) renames; the "full per-match line" expanded
  row (`:126-129`) is `mart_player_match_log`, a provider surface, and protects — four of the six
  tokens, up from two last batch, in a list that wraps across three lines. `:137`'s
  `duels_total = 0` is the bundle's zero-denominator state and renames. The classifier protects
  exactly 4 tokens in that file, matching the expanded row exactly.

  ⛔ **§7. #96 AT ITS WIDEST YET: ALL SIX `accepted_values` LISTS CONTAIN A SWEPT TOKEN**, and for
  the first time the same token sits in both a renaming list and a protecting one.
      shared.yml 14-name board          4 entries move  (dribbles_success, duels_won,
                                                         duels_won_pct, dribbles_success_pct)
      int_competition_benchmarks.yml + shared.yml, the two 18-name player lists
                                        2 entries move each  (duels_won_pct, dribbles_success_pct);
                                        duels_won_per90 and dribbles_success_per90 stay
      the three 22-name TEAM lists       0 move; duels_won_pct and duels_per_match must survive
  ⚠ `duels_per_match` contains no stem and is therefore untouched BY CONSTRUCTION rather than by a
  printed decision — a stronger guarantee, but it means the team lists are verified mechanically.

  ⭐ **§8. NINE SINGULAR RANGE TESTS, SPLIT BY ENTITY.** Six player tests rename
  (`std_player_*`, `player_profile_*`, `mart_leaderboards_*` for both ratios); three team tests
  protect (`momentum_team_`, `team_profile_`, `std_team_duels_won_pct_in_range`). `!129` had four,
  all renaming; this is the first batch where range tests split.

  ⭐ **§9. A SURFACE WITH NO PRECEDENT: `tests/test_export_site_data.py`.** Four fixture literals in
  `_shape_benchmark_member`'s player benchmark rows (`position_group: "ATT"`, ratio atoms), so
  `duels_won_pct` there is the player `metric_id`. No step-4 name appears anywhere in this file —
  it was last touched by a step-3 batch — so there is no landed precedent to copy, only the rule.

decisions_reserved:
  - none NEW on naming. Every target name is already in the record; the only judgement taken is the
    FORM decision in `decisions_taken` §3, which chooses no name.
  - ⭐ **CARRIED: should the column-reference resolver become a committed CI gate?** `!129` argued
    against it — four blind spots found in one MR, including a silent skip contradicting a property
    I had claimed for it — and nothing here changes that. The yml-vs-projection check remains the
    better candidate and is still NOT proposed.
  - ⭐ **NEW, CARRIED NOT DECIDED: the `__team`/`__player` block split loses its last live instance
    at the end of step 4.** All six dual-entity `metric_id`s rename on the player side; after the
    `goals` batch, `_blocks()`'s disambiguation branch will never fire on real data again. Nothing
    is proposed and nothing is removed — the guard still protects a future collision. Raised because
    it is the CPO's call whether a mechanism with no live instance should stay.
  - ⚠ CARRIED FORWARD: **#96**, now NINE reproductions and the widest exposure yet — all six lists
    carry a swept token, and the same token appears in both a renaming and a protecting list.
  - ⚠ CARRIED FORWARD: `_LEADERBOARD_METRICS` / `_LB_KEEP` pinned by NO test, independently
    confirmed by `platform-reviewer` on `!127`, `!128` and `!129`. This MR moves six more literals.
  - ⚠ CARRIED FORWARD: **#99**, the export's literal `goals`/`assists` read keys — MR 7's.
  - ⚠ CARRIED FORWARD: **#87** — the 49 columns left blank because their name means more than one
    thing. This MR takes that list from 5 names to 4, so some of those columns become describable.
    **Filling them is #87 and is deliberately NOT done here.**
  - ⚠ CARRIED FORWARD: **#98**; the doc-block inheritance trap.

done_when:
  - `sync_metric_docs_blocks.py --check` passes after regeneration at **172** blocks, reconciled term by term against the simulation in `decisions_taken` §2 — 10 removed, 7 added, the −3 being the deleted `__player` yoy orphans.
  - `check_description_hygiene.py`, `check_layer_contract.py` pass, `dbt parse` is clean, the description count reads **1604** — identical to the base — and the "means more than one thing" list drops from **5 names to 4**.
  - The resolver reports zero broken references and was watched going RED; the yml-vs-projection check reports zero mismatches.
  - `python -m pytest -q` matches the `9ea88b5` baseline.
  - `sqlfluff lint` on every changed model, FROM THE REPO ROOT, UNPIPED, proved byte-identical to a re-lint of the stashed base.
  - `npm test` green (76/76), the mutations watched going RED, and the site built TWICE — with `"% Duels won"` and `"Ø Duels"` still rendering in all three locales. ⚠ That is a CONFIRMATION, not a discriminating check: the correction in `acceptance_criteria` records what the mis-scope actually does.
  - All six `accepted_values` lists read by eye: the three that change named entry by entry, and the three team lists asserted byte-identical.
  - ⚠ `check_ui_i18n_metrics.py` is run because it is a real CI gate, but it is **NOT evidence** for this MR — it validates only the frozen `site/**` tree this branch never touches.
