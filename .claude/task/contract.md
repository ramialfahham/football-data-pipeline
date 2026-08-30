# Task contract — rename the three player shooting metrics (step 4, MR 1)

objective: >
  **STEP 4 of the metric catalogue naming programme, MR 1 of seven**, REBUILT after the first
  attempt failed review 4–1 and was reverted. The `shooting` family of the player catalogue:

      shots_total           →  shots_player
      shots_on_goal         →  shots_on_goal_player
      finishing_efficiency  →  finishing_efficiency_player_pct        (PLAYER entity only)

  Step 3 closed with `!123`; all twelve team renames are merged and prod carries them. Step 4 is the
  other half — 35 player renames split into seven MRs on the seed's own `metric_group` column, the
  same key step 3 used. `shooting` goes first: smallest, and the only group with no `metric_id`
  shared between entities.

  ⛔⛔ **WHAT BROKE THE FIRST ATTEMPT, because the whole design of this one follows from it.**
  These player metric names are also PROVIDER STAT WORDS. `shots_total` is the same identifier from
  `stg_apif__fixture_players.sql:51` through base, core and `int_legs__player_match`. The renamer
  could not tell a **read** of that upstream column from a **write** of the metric alias, so it
  rewrote both halves of `sum(p.shots_total) as shots_total`. Five models then queried a column that
  was never created. `shots_on_goal` and `finishing_efficiency` were untouched by the bug because
  their upstream columns are `shots_on` and a formula — different tokens. **20 of the 35 player
  metrics collide with an upstream column this way**, so the rule below governs the whole of step 4,
  not just this MR.

refs: >
  **`.claude/task/escalations.log`, the block "THE METRIC CATALOGUE NAMING PROGRAMME"**, its table
  "⛔ PLAYER, 35 REMAINING" — all three renames appear in it verbatim.
  ⭐ Cited by CONTENT, never by line number and never a plan file.
  ⭐ The shape is **RULING 5**, verbatim: "suffix only for the player metrics", with its form
  "duels_won_player_pct not duels_won_pct_player" — which is why `_player` sits BEFORE a trailing
  `_pct`. All three also satisfy **THE RULED PATTERN**, `noun [_qualifier] [_against] [_player]
  [_form]`, cited up front because batch D burned three rounds hunting a per-name quote the pattern
  had already settled.

  ⭐ **TWO CPO RULINGS GOVERN THIS REBUILD, both quoted with what they answered:**
  1. **"re-point them"** — the 30 doc references on TEAM columns that borrow a PLAYER metric's block
     are re-pointed, not blanked. He was shown: that the published text is entity-neutral and stays
     correct while the block NAME is internal jinja no consumer sees; that blanking is permitted by
     `check_description_hygiene.py:322` but deletes 30 correct published descriptions; and a third
     option (seven TEAM catalogue rows) named as HIS and not taken. Measured proof it was the right
     call: description count holds at **1604**, exactly the base.
  2. **"yes"**, answering whether the per-match / provider surfaces keep the provider name and are
     not renamed at all. They carry raw per-match stats, not metrics. So `mart_player_match_log`,
     `mart_player_fixture_stats`, `mart_team_fixture_stats`, `int_legs__*`, `3_core`, `2_base` and
     `1_staging` are **out of the edit set entirely** — measured, every occurrence in them is a
     dotted read, so this removes a whole class of the first attempt's failures.

  ⚠ **A CORRECTION TO THE RECORD, APPENDED NOT EDITED.** The 35-row table closes "UNCHANGED, all 14:
  the 13 `_per90` names and `minutes_per_appearance`". The seed holds **48** player rows and the list
  holds **35**, so the unchanged set is **13**: `key_passes_per90` is counted twice, being both a
  `_per90` name and a rename-list entry (`key_passes_per90 → passes_key_per90`). True set: **12
  `_per90` names + `minutes_per_appearance`**. Verified both directions — every one of the 35 is a
  real player `metric_id`, none missing, none extra.

  Branched from main **`1fa7e5f`**, clean tree. `glab mr list`: no open merge requests.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/macros/player_benchmark_metrics.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_competition_benchmarks.sql
  - dbt_project/models/4_intermediate/shared/int_player_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - docs/wireframes/10_home.md
  - docs/wireframes/12_player_stats.md
  - docs/wireframes/99_gaps_register.md
  - docs/wireframes/metrics_display.md
  - scripts/export_site_data.py
  - scripts/export_metric_definitions_json.py
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/active_work.md

# ⚠ This list is the EXACT changed set — reconciled against `git diff --name-only` in both
# directions, nothing extra either way.
#
# ⚠ NOT IN SCOPE, each for a stated reason:
#  · the PROVIDER / per-match surfaces named in `refs` — the CPO's "yes". `core.yml` and
#    `int_legs.yml` ARE in scope, but ONLY to re-point a `doc()` reference; no column on them moves.
#  · site_v2/src/** — the fixture `top_players` payload carries `shots_on` (the leg column) and none
#    of these three names, so no frontend change is required. Verified, not assumed.
#  · site/** — the frozen MVP tree has no catalogue-id plumbing for these three.
#  · every TEAM metric containing a stem: `shots_on_goal_pct`, `shots_on_goal_per_match`,
#    `shots_on_goal_against_per_match`, `shots_on_goal_difference_per_match`, `finishing_efficiency_pct`
#    and their yoy forms, `opponent_shots_*`, and `shots_on_goal_sum_season` (a TEAM column despite
#    decomposing onto a player stem).
#  · `shots_on_goal_per90` (one of the UNCHANGED 12) and `shots_on_goal_against` (goalkeeping, MR 6).

protected_override: >
  none required. No file in scope_paths is a protected command-class file.

impact_map: >
  writers: the three metrics are computed in `int_player_season__metrics`,
    `int_player_club_season__metrics`, `int_player_season_position__metrics` and
    `int_player_momentum__metrics`; `int_player_profile__yoy` derives the four `shots_on_goal_*`
    yoy forms; `mart_leaderboards`, `mart_player_profile` and the benchmark chain consume them.

  downstream: `dbt ls --select int_player_season__metrics+ int_player_club_season__metrics+
    int_player_season_position__metrics+ int_player_momentum__metrics+ --resource-type model`, run on
    this branch BEFORE the first edit:
      4_intermediate.domestic_league.team_season.int_player_season__metrics
      4_intermediate.shared.int_player_club_season__metrics
      4_intermediate.shared.int_player_competition_benchmarks
      4_intermediate.shared.int_player_momentum__metrics
      4_intermediate.shared.int_player_season_position__metrics
      5_marts.shared.mart_leaderboards
      5_marts.shared.mart_player_career
      5_marts.shared.mart_player_competition_benchmarks
      5_marts.shared.mart_player_momentum
      5_marts.shared.mart_player_profile
    ⚠ **THE LINEAGE IS EVIDENCE, NOT THE FILE LIST.** It under-counts (`int_player_profile__yoy`,
    every yml, `core.yml`, `int_legs.yml`, the wireframes and both scripts are edited and absent)
    and over-counts (`mart_player_career` carries none of these three names).

  layer_rules: `check_layer_contract.py`. Coupled guards:
      · the PLAYER `accepted_values` lists — `int_competition_benchmarks.yml:105`, `shared.yml:2186`,
        `shared.yml:1756`. The three 22-name TEAM lists are untouched.
      · `mart_leaderboards_finishing_efficiency_in_range` — the PLAYER board's range test, which
        `!123` deliberately left as the seventh of seven. **It renames HERE**, because here the
        player metric is the one moving.
    ⛔ #96: no offline gate enforces those lists — five consecutive reproductions. Checked by eye.

  deploy_order: none needed. No touched model is incremental.

  blast_radius: three metric columns rename across the player season, club-season, position,
    momentum, yoy and mart models; two `metric_key` VALUES change on the player benchmark chain and
    the leaderboard boards. **No number changes** — every formula, floor and null policy is
    byte-identical, and the catalogue's own formulas still read the leg columns they always did.

acceptance_criteria:
  - Every player metric name the BUILT site renders reads the same words after the rename as before, in all three locales, measured structurally from the markup of the pages under `site_v2/dist/` and compared element-for-element against the same pages built from the base commit — never by substring.
  - No built page and no `site_v2/src` source file outside the generated sample contains `shots_total`, `shots_on_goal` or the player `finishing_efficiency` as a standalone key, by whole-token grep; and no name is HALF-renamed — each new name appears everywhere the old one did.
  - `sync_metric_docs_blocks.py --check` and `check_description_hygiene.py` both pass AND are each watched going RED — the first on a stale `metric_id` in the seed, the second on a deliberately dangling `doc()`. These replace the `npm test` label guard used for MRs B–F, which reaches NONE of the 35 player metrics: measured, `asked = rowKeys ∪ heroKeys` is 17 + 3 keys and every one is a team `metrics.*` key.
  - ⭐ **NEW, AND THE ONE THIS MR EXISTS TO SATISFY: every dotted column reference to a renamed name resolves against the relation it actually reads**, checked statically and watched going RED against a reproduction of the exact defect that failed round 1.

decisions_taken: >
  All three names come from the record; both governing rulings are quoted with what they answered in
  `refs`. The four acceptance criteria are NEW — the B–F set expired with `!123` and its criterion 3
  rested on a guard that does not reach player metrics.

  ⭐⭐ **THE RULE, CORRECTED AFTER ROUND 2 FAILED 5–0 ON IT. THERE IS ONE QUESTION, NOT THREE:
  DID THE RELATION THIS READS FROM RENAME THE COLUMN?** Shape only tells you *what* is being read;
  the SOURCE decides whether it moves.
    · **alias** (`... as X`) — the metric being written. Always moves. 13 sites.
    · **dotted** (`s.shots_total`) — follows its source. All 14 in the player metric models
      enumerated: **12 read a metric relation and move, 2 read a provider relation and do not**
      (`int_player_club_season__metrics` `s` = `fct_fixture_player_stats`,
      `int_player_momentum__metrics` `p` = `int_legs__player_match`).
    · **bare** — follows its source too. 2 move (`int_player_season__metrics` aggregates
      `club_season` = `ref('int_player_club_season__metrics')`, a metric relation this branch
      renames), 4 are protected because their aggregate reads a provider relation.
    · **prose** — a mention that documents a PROVIDER payload is a reference, not the metric.
      1 protected (`03_player_profile.md`'s per-match line describes `mart_player_fixture_stats`).
    · **seed** — `base_relation` / `numerator_expr` / `denominator_expr` are references. 10 protected.

  ⛔⛔ **WHAT I GOT WRONG, TWICE, AND IT IS ONE MISTAKE NOT TWO.** For dotted reads I asked the right
  question — does the source relation rename this column? For bare reads I asked a different one:
  does the alias happen to match the inner name (`sum(X) ... as X`)? That is not the same question,
  and where the two diverge the rule fails. `int_player_season__metrics.sql:45-46` diverged: the
  pattern matched, so the inner read was protected, but its source had renamed the column, so the
  model could not execute. **FOUR reviewers found it independently.** The earlier prose defect
  (`03_player_profile.md`) is the same mistake in a fifth surface. Corrected to a single rule applied
  uniformly, above.
  ⚠ An earlier version of the dotted rule protected ALL dotted reads, which would have left
  `mart_player_profile` and `int_player_profile__yoy` reading columns their own upstream had just
  renamed. The yml-column guard caught that one before review.

  ⛔ **AND THE SAME DEFECT IN A THIRD SURFACE, caught here before review.** The catalogue's
  `numerator_expr` / `denominator_expr` / `base_relation` are LEG COLUMN REFERENCES, not the metric's
  own name. The sweep had rewritten `sum(shots_total)` → `sum(shots_player)` while `base_relation`
  stayed `int_legs__player_match`, which emits `shots_total` — the formula would have named a column
  that exists nowhere, exactly what `football-analytics-expert-reviewer` failed round 1 on. The
  correct sibling proves the rule: `shots_on_goal_player` keeps `sum(shots_on)`. Seed occurrences are
  now decided BY CSV FIELD; 10 reference-field occurrences protected.
  ⭐ **THE GENERAL FORM, which governs the six remaining batches: a reference to an upstream column
  is not the metric's own name.** It has now appeared in three surfaces — dotted SQL reads,
  self-aliasing aggregates, and the seed's formula fields. Same cause, different shape each time.

  ⛔ **THE CHECK THAT WAS MISSING, AND IT IS THE REASON ROUND 1 SHIPPED.** No gate in this repo
  resolves a column reference. Round 1 went green on `sync_metric_docs_blocks --check`,
  `check_description_hygiene`, `check_layer_contract`, `check_ui_i18n_metrics`, `dbt parse`, pytest,
  sqlfluff, `npm test` AND the site build — nine gates — while five models could not execute. Four
  human reviewers caught it by reading SQL.
  ⚠ **AND THE FIRST VERSION OF MY OWN RESOLVER REPEATED THE MISTAKE.** It handled DOTTED references
  only, so it reported "25 of 28 resolved, 0 broken" while `int_player_season__metrics` sat broken on
  a BARE read. `platform-reviewer` named that gap exactly. A check that gives false confidence is
  worse than no check.
  ⭐ **Now extended to follow sources through CTE chains for BOTH shapes: 31 references checked, 0
  broken.** Run against either earlier round's state it flags that round's defect with the right
  diagnosis. Two limits stated rather than implied: it only checks relations whose ymls declare their
  columns (4_intermediate and 5_marts — staging under-declares, which produced a false positive that
  had to be removed), and it does not cover the prose or seed surfaces, which have their own rules
  above. `data:build:mr` remains the authority.

  ⚠ **A NO-OP WRITE IS STILL A WRITE.** Files with zero renames are never opened; the contract gate
  watches the file system, not the diff.

  ⛔ **THE PREDICTION, before any code: the built pages do NOT change.** None of these three names is
  among the 16 locked rows in `metricRows.ts`, and the fixture `top_players` payload carries
  `shots_on` — the leg column, which does not move. So the row count HOLDS AT 12 where `!123` left
  it. Measured after: identical in all three locales, label sets element-for-element equal.

  THRESHOLD DECLARATIONS. NEW MECHANISM: none in the shipped tree — the reference resolver is a
  scratchpad verification tool, not a committed gate. Whether it should BECOME one is raised in
  `decisions_reserved`. RECURRING COST: none. NEW DEPENDENCY: none.

decisions_reserved:
  - none NEW on naming: all three are ruled and quoted.
  - ⭐ **RAISED, NOT TAKEN: should the column-reference resolver become a committed CI gate?** It
    caught nothing here only because it was used during the build; it would have caught round 1
    outright. Committing it is a NEW MECHANISM and therefore the CPO's/CTO's call. Six batches
    remain, all with the same exposure.
  - ⚠ CARRIED FORWARD: **#96**, five consecutive reproductions; the offline test is a new mechanism.
  - ⚠ CARRIED FORWARD: **#99**, the export's literal `goals`/`assists` read keys — MR 7's, verified
    none of these three names has the same problem.
  - ⚠ CARRIED FORWARD: **#98**, English group headings on DE/FI. Untouched.
  - ⚠ CARRIED FORWARD: the latent inheritance trap the doc re-pointing leaves (a `_player`-named
    block feeding six team columns), filed rather than guarded.

done_when:
  - `sync_metric_docs_blocks.py --check` passes after regeneration, with three bare blocks for these names.
  - `check_description_hygiene.py`, `check_layer_contract.py`, `check_ui_i18n_metrics.py` pass, and `dbt parse` is clean with zero dangling `doc()`.
  - The static column-reference resolver reports zero broken references, and was watched going RED on a reproduction of the round-1 defect.
  - `python -m pytest -q` matches the `1fa7e5f` baseline: **1009 passed, 1 skipped, 14 subtests**.
  - `sqlfluff lint` on every changed model, FROM THE REPO ROOT, UNPIPED, exit code read bare; any FAIL proved pre-existing by re-linting the file unmodified and diffing.
  - `npm test` green, the two label-independent mutations watched going RED, and the built site measured structurally at 12 rows / 7 headings, unchanged.
