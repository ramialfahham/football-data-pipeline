# Task contract — feat: player-core PR-b (bio enrichment)

> Player-data initiative, PR-b — reduced to BIO ONLY (CPO 2026-06-16). The player-season
> appearances rollup was found to already exist (duplicated in mart_player_season + mart_player_profile,
> plus an orphaned int_player_season__metrics, with DIVERGENT metric derivations); that consolidation
> is its own governed task (#480). This PR enriches the player ENTITY with bio from the 100%-backfilled
> profiles and surfaces it on the player-profile mart. Pure dbt (base + core + one mart); additive to
> the mart; no protected paths. Reviewers: scope-auditor + analytics-engineer-reviewer.

objective: >
  (a) base_apif__player_profiles (NEW base): current-per-player bio from stg_apif__player_profiles
      (union-all snapshots reduced to the latest row per player_id, mirroring base_apif__players).
      Identity-level only (no league/team/season). Grain: player_api_id.
  (b) dim_player (MODIFIED): join base_apif__player_profiles on player_api_id; ADD five bio columns —
      player_birth_place, player_birth_country, player_height, player_weight, player_position. The four
      OVERLAPPING descriptors (name, birth_date, nationality, photo) are refreshed from the richer
      profile via coalesce(profile, players) — they may CHANGE for players whose profile differs from
      the roster source (a deliberate data-quality preference, CPO-approved); no metric/numeric column
      exists on dim_player, so no number changes. EXCLUDE age (point-in-time) and squad_number
      (affiliation, not entity). dim_player stays a pure Type-1 entity; grain unchanged (player_sk).
  (c) mart_player_profile (MODIFIED): surface the five new bio columns from dim_player (the player
      page). ADDITIVE only — existing columns, metrics, grain, and row counts unchanged.

refs: >
  CPO 2026-06-16 (this conversation). Player-season consolidation split out as #480. Sources:
  stg_apif__player_profiles (PR-a2, 100% backfilled), base_apif__players + dim_player (#448),
  mart_player_profile (#325). Player insights chain #153 -> #156.

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__player_profiles.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/dim_player.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - .claude/task/contract.md

decisions_taken: >
  CPO 2026-06-16: ship BIO only now; player-season consolidation is its own task (#480). Five bio
  fields added to dim_player from the profiles base; profile-wins coalesce on the four overlapping
  descriptors (richer source preferred — may refresh some names/nationalities/photos; no metrics
  affected); exclude age + squad_number; dim_player stays pure Type-1; surface the bio on
  mart_player_profile additively (no changed metrics/grain/rows).

decisions_reserved:
  - base_apif__player_profiles current-per-player tiebreak (latest raw_ingested_at per player_id) —
    follow the base_apif__players precedent.
  - dim_player.player_position (general bio position) vs mart_player_profile's existing position_code
    (season modal position from match stats): keep BOTH, distinct meanings; do not merge/redefine.
  - The player-season consolidation + metric reconciliation is #480 — NOT here.
  - Any §10 question -> escalate in plain language; do not self-rule.

done_when:
  - dbt parse clean; `dbt build --select base_apif__player_profiles dim_player mart_player_profile`
    succeeds on real BQ; dim_player unique on player_sk with the five bio columns populated for the
    backfilled universe (profiles ~= 31,920 distinct players); mart_player_profile EXISTING
    columns/grain/row-count UNCHANGED (additive bio columns only) — verify pre/post on the existing columns.
  - base.yml documents base_apif__player_profiles; core.yml documents dim_player's new columns;
    shared.yml documents mart_player_profile's new columns; sqlfluff lint passes on the changed models.
  - validate-local clean.
  - reviewers: scope-auditor (always) + analytics-engineer-reviewer (dbt_project/**) both PASS.

amendments: (none)
