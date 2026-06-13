# Task contract — player↔team↔season rostered mapping (PR A of player-model redesign)

> CPO-approved design (2026-06-13 working session; see memory project-player-model-redesign
> + .claude/task/escalations.log 2026-06-13). PR A is the ADDITIVE step: introduce the
> rostered affiliation models. Nothing existing changes behaviour. The breaking rework
> (dim_player → pure entity, drop base_apif__players_global, repoint consumers) is PR B.
> See docs/working_agreement.md §2; dbt_project/docs/layering.md.

objective: >
  Add the rostered player↔team↔season affiliation, sourced single-source from the
  /players roster (stg_apif__players), at its natural grain — capturing squad members
  who never played a match (which no fact can express). Two new models, additive only:
  - base_apif__player_team_season (2_base view) ← stg_apif__players. Grain
    (league_code, player_id, team_id, season_year); dedup to latest ingest. Drops rows
    missing player_id / team_id / season_year.
  - dim_player_team_season_mapping (3_core table) — conformed rostered membership mapping.
    Keys: player_sk (=player_id), team_sk (=team_id), season_sk + league_sk via lookup
    join to dim_competition_season on (league_code, season_api_year=season_year),
    league_code, season_api_year. PK player_team_season_sk = surrogate_key(player_id,
    team_id, league_code, season_year). The season-lookup CTE dedups dim_competition_season
    to one row per (league_code, season_api_year) (row_number qualify) so the join cannot
    fan out — the league_code↔league_api_id 1:1 is untested.
  Definition = ROSTERED only (CPO ruling: NOT "any affiliation evidence" — that would
  duplicate facts and rebuild the multi-source union bug).
refs: player-model redesign (memory project-player-model-redesign); relates #153→#156.

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__player_team_season.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/dim_player_team_season_mapping.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/docs/layering.md
  - .claude/task/contract.md
  - .claude/active_work.md   # artifact-only: handover write-out at close (amendment A1)

decisions_taken: >
  CPO-approved target shape + classification (2026-06-13; recorded in escalations.log).
  Additive only for the warehouse models — no existing MODEL SQL or consumer is touched
  (dim_player, base_apif__players(_global), marts unchanged; they are PR B). CPO ruling:
  the conformed mapping is a CORE object named `dim_player_team_season_mapping` — keeps the
  dim_ prefix (its core home) + a _mapping suffix (it is a conformed many-to-many
  RELATIONSHIP, not an entity). layering.md's dimension rules are EXTENDED to sanction a
  "relationship (mapping) dimension": exempt from the Entity condition + the
  degenerate-dimension exclusion, but still required to satisfy Reuse + Conformance and to
  carry a single tested unique grain key (the property that earns any table its place in
  core). season_sk is resolved by LOOKUP join to dim_competition_season (mirrors
  mart_player_season), not recomputed, because the roster source has league_code not
  league_api_id. Materialisation follows the layer contract: base = view, dim = table.

decisions_reserved:
  - FK test severities / coverage, to be confirmed by the analytics-engineer reviewer and
    proven by ci-data-build (the authoritative DQ gate; not run locally):
    * player_sk → dim_player: holds BY CONSTRUCTION (same source stg_apif__players,
      player_id not null) → relationships ERROR is safe.
    * team_sk → dim_team: roster /players is fetched only for already-discovered team_ids
      AFTER load_teams runs (competition_runner), and dim_team unions /teams + fixture
      team_ids, so roster teams ⊆ dim_team by construction → relationships ERROR is safe.
      If ci-data-build shows a real gap, STOP and escalate, do NOT silently downgrade.
    * season_sk → dim_competition_season: resolved by the dedup-guarded left join; season_sk
      left NULLABLE (no not_null) to tolerate a roster season with no /leagues
      competition-season row; relationships ERROR validates non-null values.
  - Whether the mapping later needs an "is_current"/as-of flag is a PR-B/consumer question.

done_when:
  - base_apif__player_team_season.sql exists (2_base view), grain
    (league_code, player_id, team_id, season_year), reads ref('stg_apif__players').
  - dim_player_team_season_mapping.sql exists (3_core table) with the keys above + the
    dedup-guarded season lookup.
  - base.yml carries the base grain test; core.yml carries a NEW dim block:
    PK not_null+unique; grain unique_combination; not_null on player_sk/team_sk/league_code;
    relationships player_sk→dim_player, team_sk→dim_team, season_sk→dim_competition_season,
    league_sk→dim_league.
  - layering.md: a "relationship (mapping) dimensions" clause added to the dimension
    qualification rules, + an inventory row for dim_player_team_season_mapping (doc-sync).
  - NO existing MODEL SQL or consumer modified (additive); the only edits to existing files
    are appended yml test blocks + the layering.md rule/inventory. grep shows dim_player,
    base_apif__players, base_apif__players_global unchanged on this branch.
  - validate-local Tier 1+2 green (dbt parse, sqlfluff lint); full DQ build → ci-data-build.
  - reviewers: scope-auditor (always) + analytics-engineer-reviewer (dbt_project/**) — PASS.

amendments:
  - 2026-06-13 A1: + dbt_project/docs/layering.md and + .claude/active_work.md to scope;
    model renamed dim_player_team_season → dim_player_team_season_mapping. authority: CPO
    ruling 2026-06-13 (escalations.log) resolving the iteration-2 scope-auditor FAIL — keep
    dim_ + _mapping suffix and extend layering.md to recognize relationship (mapping) dims;
    plus the standing handover rule for active_work.md. content: the layering.md clause +
    inventory row, and the rename. Also added the season-lookup dedup guard (fan-out fix,
    analytics-engineer iter-1 finding).
