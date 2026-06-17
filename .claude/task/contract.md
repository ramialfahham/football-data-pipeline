# Task contract — feat: dim_team_competition_season_mapping (team↔competition↔season membership, Phase 1)

> CPO-approved this conversation (2026-06-17). Root cause of the BL1/BL2 directory gap: `dim_team.league_code`
> is a LATEST-INGEST PROVENANCE stamp (one row per team, latest /teams payload wins), NOT a team↔competition
> affiliation. All 19 BL1 + 19 BL2 clubs are present in dim_team but stamped `DFBP` (German Cup /teams ingested
> 2026-06-16, after the leagues' 2026-06-10) — so a `league_code='BL1'` lookup returns nothing. NOT an ingestion
> gap (raw HAS BL1/BL2 /teams). Latent for every league; PL survived only by ingest timing. The live preview is
> unaffected (it reads league_code from fixtures, not the stamp).
>
> Fix shape (CPO-approved): mirror the player entity/affiliation split (dim_player + dim_player_team_season_mapping).
> This is **Phase 1** — add the new core mapping dim ONLY. Net-new, breaks nothing, makes "teams in competition X
> this season" correct for every league. **Phase 2** (drop dim_team.league_code + repoint mart_team_market_value +
> point the season-rollup at the spine) is a SEPARATE follow-up PR — NOT in this one.
> Reviewers: scope-auditor (always) + analytics-engineer-reviewer (all paths are dbt_project/**).

objective: >
  Add a new core relationship (mapping) dimension `dim_team_competition_season_mapping` giving conformed
  team↔competition↔season membership, derived from FIXTURES (finished AND scheduled), keys-only, mirroring
  `dim_player_team_season_mapping`. Membership source = fixtures (NOT the /teams roster): a team that is in a
  competition always plays fixtures in it, so the schedule is a complete, timing-stable source — unlike players,
  where a never-played squad member forced a roster source. Scheduled (not-yet-played) fixtures are INCLUDED, so a
  team is a member from the moment its fixtures are published.
  (a) Model `dbt_project/models/3_core/dim_team_competition_season_mapping.sql` (NEW, table): read
      `base_apif__fixtures_next`; UNION DISTINCT home + away sides to one row per (team, league_code, season);
      filter NULL team ids (undetermined knockout fixtures). Columns (keys only — no measures, no team attributes):
      `team_competition_season_sk` (surrogate over team_sk+league_code+season_api_year), `team_sk`
      (cast team_id int64), `league_sk` (cast league_api_id int64), `season_sk`
      (generate_surrogate_key(league_api_id, season)), `league_code`, `season_api_year` (= season).
      Derive league_sk/season_sk the SAME way fct_fixture does (the fixtures base carries league_api_id) so keys
      conform to the fixtures fact by construction — DELIBERATELY differs from the player mapping (which used a
      nullable dim_competition_season lookup only because the roster lacked league_api_id); document this in the
      model header.
  (b) Schema `dbt_project/models/3_core/core.yml` (MODIFIED): add the model entry mirroring
      dim_player_team_season_mapping — description (relationship/mapping dim, grain, keys-only, "membership from
      fixtures, appearances live in fct_fixture"), tags [core, dimension], table-level
      dbt_utils.unique_combination_of_columns on (team_sk, league_code, season_api_year), and column tests:
      team_competition_season_sk [not_null, unique]; team_sk [not_null, relationships → dim_team];
      league_sk [not_null, relationships → dim_league]; season_sk [not_null, relationships → dim_competition_season];
      league_code [not_null]; season_api_year [not_null].
  (c) DQ test `dbt_project/tests/assert_team_competition_season_mapping_covers_fixtures.sql` (NEW): GENERIC, no
      league hardcoding — every (team_sk, league_code, season_api_year) appearing as home OR away in `fct_fixture`
      must have a row in the mapping; returns offending rows (expect zero). The BL1/BL2 regression guard, expressed
      competition-agnostically.
  (d) Docs `dbt_project/docs/layering.md` (MODIFIED): add `dim_team_competition_season_mapping` to the core
      dimension reference table (grain + source + "relationship (mapping) dim" note), beside the player mapping.

refs: >
  This conversation 2026-06-17 (root-cause investigation + CPO design sign-off). Mirrors the player model redesign
  (dim_player pure entity + dim_player_team_season_mapping; the "relationship (mapping) dimensions" clause in
  dbt_project/docs/layering.md). dim_team BL1/BL2 watch-item from the 2026-06-16 GAP-18 handover.

scope_paths:
  - dbt_project/models/3_core/dim_team_competition_season_mapping.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/tests/assert_team_competition_season_mapping_covers_fixtures.sql
  - dbt_project/docs/layering.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO (this conversation, 2026-06-17): (1) the fix mirrors the player entity/affiliation split — a new core mapping
  dim, NOT a band-aid stamp-priority tiebreak and NOT accept-and-document. (2) Name = dim_team_competition_season_mapping
  (mirrors the player _mapping suffix). (3) Membership source = FIXTURES, not the /teams roster (teams always play
  what they enter; no never-played gap). (4) INCLUDE upcoming/scheduled fixtures. (5) Explicit thin dim (not derived
  inline). (6) Two phases; THIS is Phase 1 (new dim only); Phase 2 (drop dim_team.league_code + repoint
  mart_team_market_value) is a separate PR. (7) Columns as in objective (a). (8) league_sk/season_sk derived from the
  base like fct_fixture (NOT the player mapping's nullable lookup) — fixtures carry league_api_id.

decisions_reserved:
  - PHASE 2 — dropping `dim_team.league_code`, repointing `mart_team_market_value` (its `where league_code = 'WC'`),
    and pointing the season-rollup at the new spine. NOT this PR. Do NOT touch dim_team or any mart here.
  - No consumer repointing in Phase 1: the dim is net-new and nothing reads it yet. Do NOT refactor mart_team_season
    or any existing model to consume it in this PR.
  - Status handling: include ALL fixture statuses (any scheduled or played fixture = membership). If a reviewer argues
    a specific status must be excluded (e.g. cancelled), that is a §10 product call → escalate, do not self-decide.
  - Any other §10 (grain change, naming beyond the agreed name, a new mechanism) → escalate in plain language.

done_when:
  - `dim_team_competition_season_mapping` builds (table); grain unique on (team_sk, league_code, season_api_year);
    team_sk/league_sk/season_sk relationships pass; the new completeness test passes (zero rows).
  - Read-only BQ spot-check confirms BL1 + BL2 are present in the mapping with their full team sets (the regression
    guard), and a multi-competition club (e.g. a Bundesliga side) shows multiple rows (BL1 + DFBP + any continental).
  - dbt parse clean; sqlfluff lint passes on the new SQL; validate-local clean.
  - core.yml documents the dim + columns + tests; layering.md reference table lists it.
  - reviewers: scope-auditor + analytics-engineer-reviewer both PASS (≥2 named risks each), no FAIL, every ESCALATE
    has a recorded CPO ANSWER.

amendments: (none)
