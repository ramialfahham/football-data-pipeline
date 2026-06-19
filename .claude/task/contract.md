# Task contract — feat: mart_roster (identity-only club squad list)

> PR 1 of the split task A (CPO-directed 2026-06-19). Mart-only: add `mart_roster`, the
> Squad-block data foundation. NO export wiring — the Squad-block consumer lives in the
> PAUSED website blueprint (#391); wiring a payload nothing renders is speculative plumbing,
> so it rides with the Squad-block build. The companion `mart_leaderboards` is a separate
> later PR.

objective: >
  Add mart_roster — an identity-only squad list, one row per rostered player per
  (club team, competition-season), from dim_player_team_season_mapping joined to dim_player.
  Scoped to CLUB competitions (entity_type = 'club', resolved league_code → competition_registry
  → competition_types — never a dim_team flag). Identity columns only (name, listed position,
  nationality, birth_date, photo + keys); NO per-club season stats (the deferred per-club grain,
  #480 §8.3). Materialised as a view (flat identity projection, no aggregation).

refs: docs/content_architecture.md §3 (Squad/roster block) + §7 (new-mart list); .claude/active_work.md NEXT #2; task A (split, PR 1).

scope_paths:
  - dbt_project/models/5_marts/shared/mart_roster.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/3_core/core.yml
  - dbt_project/docs/layering.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO-directed this conversation (2026-06-19): split task A into two PRs; build mart_roster
  FIRST, mart-only, export wiring deferred (blueprint #391 PAUSED — "PR1 scope approved").
  Grain (team_sk, league_code, season_api_year, player_sk) = the mapping's membership grain
  (the mapping surrogate player_team_season_sk is reused as the mart surrogate). Club-only via
  the competition_types seed (entity_type = 'club'), mirroring mart_standings' registry→types
  join — NOT a dim_team column (per the dim_team-is-a-pure-entity ruling). Identity columns:
  name, listed position (player_position from dim_player bio), nationality, birth_date, photo.
  Age is a render-time derivation, NOT a mart column (a stored current-age would be
  non-deterministic / rebuild-dependent). LEFT join dim_player + a relationships test so a
  membership with no player entity surfaces as a test failure, never a silent drop.

decisions_reserved:
  - Export / payload wiring is OUT of scope (deferred to the Squad-block build under #391).
    If tempted to add it, STOP — that is the deferred decision, not this PR.
  - NO per-club season stats / appearances (the deferred #480 §8.3 per-club grain).
  - If the registry → types join cannot cleanly yield entity_type for a league_code present in
    the mapping, STOP and escalate — do not hardcode a club/national split or a league_code list.
  - mart_leaderboards (the companion mart, retirements, catalogue rows, export repoint) is a
    SEPARATE later PR — nothing from it belongs here.

done_when:
  - mart_roster.sql compiles; `dbt parse` is clean; sqlfluff lint passes on the new model.
  - Grain unique on (team_sk, league_code, season_api_year, player_sk); player_team_season_sk
    unique + not_null; relationships player_sk → dim_player and team_sk → dim_team; not_null on
    team_sk / player_sk / league_code / season_api_year; entity_type accepted_values ['club'].
  - Only club rows are present (national-team memberships excluded by the entity_type filter).
  - dbt_project/docs/layering.md mart inventory lists mart_roster (view) with its grain.
  - dim_player_team_season_mapping.league_code carries a relationships test to
    competition_registry.league_code, so an unregistered roster competition fails the build
    rather than being silently dropped by mart_roster's club filter.
  - reviewers: scope-auditor + analytics-engineer-reviewer PASS (>=2 named risks each);
    no FAIL; no ESCALATE.

amendments:
  - 2026-06-19: + dbt_project/models/3_core/core.yml — authority: analytics-engineer-reviewer
    FAIL on the first review round (the mart's club filter `where entity_type = 'club'` runs
    after LEFT joins, so a league_code present in the mapping but absent from the registry
    silently drops those memberships; the post-filter not_null/accepted_values tests on
    entity_type are vacuous) + DQ-non-negotiable standing rule + the fix-don't-escalate rule for
    non-§10 findings. Content: a relationships test on
    dim_player_team_season_mapping.league_code -> competition_registry.league_code (the reviewer's
    own suggested guard). Verified clean against live data first (0 unregistered league_codes;
    231,860 club / 21,657 national / 0 null entity_type), so the guard passes CI today and only
    fires on a future regression. Also dropped player_first_name / player_last_name from the mart
    SELECT (the locked spec lists only "name"; they were undocumented in shared.yml — round-1
    finding 2). No new reviewer routed (core.yml is dbt_project/** -> analytics-engineer).
