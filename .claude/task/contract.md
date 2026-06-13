# Task contract — dim_player → pure entity (PR B of the player-model redesign)

> CPO-approved design (2026-06-13 working session; memory project-player-model-redesign).
> PR A (#444) added the rostered mapping; #446 retired transfers. PR B is the breaking
> rework: make dim_player a pure global entity and collapse the two-stage player dedup.
> See docs/working_agreement.md §2; dbt_project/docs/layering.md.

objective: >
  Make dim_player a pure entity (one row per player, identity attributes only) and remove
  the affiliation snapshot that the redesign replaced with dim_player_team_season_mapping.
  - dim_player: drop league_code, last_known_team_api_id, last_known_season_year. Keep
    player_sk (=player_api_id), player_api_id, player_name, first/last, birth_date,
    nationality, photo_url, raw_ingested_at. Grain: player_api_id.
  - base_apif__players: collapse the two-stage dedup into ONE global dedup per
    player_api_id, ordered by source_priority asc then raw_ingested_at desc (so the most
    authoritative NAMED source wins globally). Drop league_code + last_known_* from the
    source CTEs and output. Grain becomes player_api_id (was (league_code, player_api_id)).
  - DELETE base_apif__players_global (its sole consumer, dim_player, now reads
    base_apif__players directly).
  Verified: NO consumer uses dim_player.league_code or last_known_* (grep across
  4_intermediate, 5_marts, scripts/export_site_data.py — marts get league_code from facts
  and only pull name/photo/bio from dim_player; zero last_known references downstream), so
  this needs no consumer repointing.
refs: player-model redesign (memory project-player-model-redesign); relates #153→#156.

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__players.sql
  - dbt_project/models/2_base/api_football/base_apif__players_global.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/dim_player.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/docs/layering.md
  - .claude/task/contract.md
  - .claude/active_work.md

decisions_taken: >
  CPO-approved target shape (2026-06-13, memory project-player-model-redesign): dim_player
  is a pure Type-1 entity; affiliation lives in dim_player_team_season_mapping (PR A) and
  the facts, not on the entity. The single global dedup ordered by (source_priority asc,
  raw_ingested_at desc) is strictly better than the old players_global recency-only order
  (which ignored source authority) — it can only reduce null attributes, never add them, so
  not_null(player_name) is preserved or improved. Additive consumer impact: none (verified).

decisions_reserved:
  - DQ proof runs in ci-data-build (not local): not_null(dim_player.player_name) +
    unique(player_sk) + the surviving FK relationships (fct_fixture_player_stats /
    fct_fixture_event / dim_player_team_season_mapping → dim_player). Expected to hold:
    the single dedup yields exactly one row per player_api_id (unique), picks the most
    authoritative source globally (name quality ≥ before), and every player feeding those
    FKs is sourced from the same three sources that now compose dim_player. If ci-data-build
    surfaces a NEW hard failure, STOP and escalate — do not paper over it.
  - dim_player.league_code removal makes it a global (non-league-scoped) entity like
    dim_date; layering.md's "all league-scoped dims carry league_code" note still holds (it
    is no longer league-scoped). Update the inventory row accordingly.

done_when:
  - base_apif__players: single dedup per player_api_id (source_priority asc, raw_ingested_at
    desc); no league_code / last_known_* columns; grain player_api_id.
  - base_apif__players_global.sql deleted (git rm); no remaining ref() to it.
  - dim_player: reads base_apif__players; entity columns only; no league_code / last_known_*.
  - base.yml: base_apif__players grain test → [player_api_id]; base_apif__players_global block removed.
  - core.yml: dim_player block drops league_code + last_known_* columns/tests; description updated.
  - layering.md: dim_player inventory row → source base_apif__players, pure global entity, no
    last_known note.
  - grep: no ref()/column use of base_apif__players_global, dim_player.league_code, or last_known_*
    anywhere; consumers unchanged and still compile.
  - validate-local Tier 1+2 green (dbt parse, sqlfluff lint, layer contract, pytest); full DQ → ci-data-build.
  - reviewers: scope-auditor (always) + analytics-engineer-reviewer (dbt_project/**) — PASS.

amendments: (none)
