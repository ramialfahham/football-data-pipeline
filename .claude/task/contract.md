# Task contract — rename the team metric `goals_for` to `goals`

objective: >
  Step 1 of 4 in the catalogue naming work the CPO ruled this session. It is deliberately alone,
  because it is the only rename in the programme that is not a suffix or a spelling change.

  The team's scored goals were `goals_for` while the player's were `goals`, and the team's own rate
  and every breakdown already said plain `goals` (`goals_per_match`, `goals_penalty`, `goals_own`,
  `goals_open_play`). One word out of step in its own family. The CPO ruled `goals_for` becomes
  `goals`.

  ⛔ THE COLUMNS KEEP THEIR NAME. `goals_for` is also a real column on the match-row, momentum,
  season-record and mart models, where it pairs with `goals_against` and reads correctly. Only the
  CATALOGUE METRIC is renamed. Whether those columns follow is a separate question the CPO has not
  been asked and this task does not answer.

  ⛔ MEASURED ON THE BRANCH, AND IT IS BIGGER THAN THE FIRST DRAFT OF THIS CONTRACT SAID.
  Renaming the metric does not merely move one block. `goals` now exists for BOTH entities and the
  two define it differently (team `sum(goals_for)` from the scoreline, player `sum(goals_total)`
  from the player stats), so `sync_metric_docs_blocks.py` applies its one-name-two-meanings rule
  and REPLACES the bare `goals` block with `goals__team` and `goals__player`. That dangles the
  existing `doc('goals')` references as well as the `doc('goals_for')` ones.

  **18 references move, not 12**, counted on the branch:
    · 12 × `doc('goals_for')` → `doc('goals__team')`
    · 6 × `doc('goals')` → `doc('goals__player')`

  Every one classified by reading which MODEL the column sits on, never by the name:
    TEAM (12): int_legs__team_match, int_team_momentum__metrics, int_team_momentum_window,
    int_team_season_record, mart_team_season_insights, mart_team_momentum_window,
    mart_team_fixture_stats, mart_team_profile, mart_team_season, mart_head_to_head,
    mart_team_fixtures, and mart_player_match_log — that last one sits on a PLAYER model but its
    `goals_for` is the TEAM's scoreline for that match
    (`mart_player_match_log.sql:90`), so it takes the team block.
    PLAYER (6): int_player_season__metrics, int_player_club_season__metrics,
    int_player_season_position__metrics, mart_player_profile, mart_player_career, and
    mart_leaderboards, whose grain is one row per player and board.

refs: >
  **`.claude/task/escalations.log`, 2026-08-26, "THE METRIC CATALOGUE NAMING PROGRAMME", RULING 1**,
  which records the CPO's own words verbatim: "goals_for becomes goals", given while he reviewed the
  full list of 38 team metrics. That entry is the authority for all four renaming MRs and carries
  the other five rulings, the resulting naming pattern, and two places where a later instruction
  reversed an earlier one.

  ⛔ AMENDED AFTER A ROUND-1 FAIL, and the amendment is the point. The first version of this
  contract cited a PLAN FILE outside the repo as its sole authority for a §10 naming decision, and
  `escalations.log` held no entry at all. scope-auditor FAILed it and quoted the 2026-08-26 entry
  above back at me, where the CPO had already called out this exact failure class: claiming a record
  supports something the record does not. This was worse than that instance, because it did not
  cite the log at all, it substituted something uncommitted for it. The ruling is now recorded, and
  the log entry discloses on its face that it was written after the fact.
  Branched from main `d95a04f`, clean tree.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/5_marts/shared/shared.yml
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

# ⚠ NO model SQL is touched. No column is renamed. No frontend file is touched, so the acceptance
# gate does not fire. `metric_columns.md` is GENERATED — regenerate, never hand-edit.

protected_override: >
  none required. No file in scope_paths is protected.

impact_map: >
  writers: NONE. No model computes anything differently. No SQL expression changes, no column is
    added, renamed or removed. The seed's `metric_id` and `label_i18n_key` change on one row; the
    rest is generated blocks and the references that point at them.

  downstream: no lineage change. No model `ref()`s the seed, only tests do, so editing a row
    cannot alter any model's `depends_on`. Confirmed the same way as the previous catalogue task:
    the seed's only dependents in the manifest are tests.

  the 18 references, per file, counted not estimated:
    `doc('goals_for')` → int_legs.yml 1 · int_momentum.yml 1 · int_momentum_window.yml 1 ·
    int_season_record.yml 1 · domestic_league.yml 1 · shared.yml 7.
    `doc('goals')` → int_team_season.yml 1 (the player model's section) ·
    int_player_club_season.yml 1 · int_player_season_position.yml 1 · shared.yml 3.

  ⚠ BLOCKS: 183 → 182, measured. Gone: `goals`, `goals_for` and five derived
    `goals_for_*` / `last_meeting_goals_for__team` names whose stem stops being a catalogue metric.
    New: `goals__team`, `goals__player` and four derived `goals_*` names. Every disappearing
    DERIVED block was counted and has **0 references**, so only the two bare ones dangle and both
    are repointed above.

  blast_radius: `persist_docs` is on, so the 12 columns get their description re-pushed on the next
    build. The TEXT does not change, only the block name behind it, so no warehouse description
    actually changes value.

  layer_rules: none engaged. A seed row and description references; no model, no materialisation.

  deploy_order: none. Descriptions reach BigQuery the next time each model builds.

decisions_taken: >
  THRESHOLD DECLARATION — NEW MECHANISM: none. One seed row and existing generated blocks.
  THRESHOLD DECLARATION — RECURRING COST: none.

  ⛔ BUILDER'S CALL, AND IT IS THE ONE TO ATTACK: after this change a docs block named `goals`
    describes 12 columns named `goals_for`. That is deliberate. The block is named for the METRIC,
    the column is named for what the model holds, and the two are allowed to differ; the same
    already happens elsewhere. The alternative was renaming those 12 columns, which the CPO has not
    ruled on and which would drag the match-row `goals_for` / `goals_against` pair into a rename
    that is not about it.

  BUILDER'S CALL 2: `label_i18n_key` follows the metric_id, `metrics.goals_for.label` becomes
    `metrics.goals.label`. Checked: that key is referenced nowhere in the frontend, because this
    metric is not one of the sixteen displayed rows. So no locale dictionary changes.

decisions_reserved:
  - Whether the COLUMNS named `goals_for` follow the metric. Not asked, not answered, not done.
  - The other three steps of the naming programme: the team `_pct` and spelling sweep, the player
    `_player` sweep, and the nine "on target" labels. Each ships on its own.
  - `assert_metric_catalogue_value_equivalence`, the parked checker (#91), still waits until the
    renaming is finished. Shipping it first would bind it to names that are about to move.

done_when:
  - The seed parses at 86 rows, 15 fields, line endings preserved as BYTES, and every seed test
    re-derived offline: unique `(metric_id, entity)`, unique `label_i18n_key`, unique
    `(entity, label_en)`, every `accepted_values`, every `not_null`.
  - `python scripts/sync_metric_docs_blocks.py` regenerates and `--check` is green. The block count
    moves by a delta MEASURED on the branch, not predicted.
  - `dbt parse` CLEAN, ZERO dangling `{{ doc() }}` anywhere, asserted across every model yml and not
    only the edited ones.
  - `check_description_hygiene.py` green repo-wide, read from its OUTPUT.
  - ⛔ ZERO occurrences of the metric_id `goals_for` remain in the catalogue, and every REMAINING
    `goals_for` in the repo is confirmed to be a COLUMN name, by reading the model.
  - Offline gates green plus `ruff` and `python -m pytest tests/`.
  - ⚠ EVERY INTEGER IN THE ARTIFACTS RE-DERIVED before commit (#71).
