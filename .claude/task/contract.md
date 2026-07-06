# Task contract — exclude non-entity (All-Star) teams from the player affiliation mapping

> Written on a CLEAN tree (branch `fix/roster-exclude-non-entity-teams` off main @ #657 merged).
> CPO approved option 1 this session (2026-07-06): exclude non-entity teams from the mapping.
> See plan `C:\Users\Rami\.claude\plans\logical-moseying-noodle.md`.

objective: >
  The nightly build has failed since ~Jun 30 on two relationship DQ tests (138 orphan rows each):
  team_sk in dim_player_team_season_mapping / mart_roster with no dim_team match. Diagnosed
  (BigQuery/prod): the orphans are two MLS All-Star exhibition squads — 17664 "Liga MX All-Stars",
  17665 "MLS All-Stars" (118 players) — surfaced only by /players squad data; /teams does not model
  them, so they are absent from dim_team (0 in /teams, 0 in fct_fixture). An All-Star selection is
  not a club/national affiliation. Fix: keep only team_sks that exist in dim_team (a core→core
  semi-join), so the affiliation mapping and mart_roster contain real team entities only.
refs: plan logical-moseying-noodle.md; CPO ruling 2026-07-06 (option 1); failing tests
  relationships_dim_player_team_season_mapping_team_sk__team_sk__ref_dim_team_ +
  relationships_mart_roster_team_sk__team_sk__ref_dim_team_.

scope_paths:
  - dbt_project/models/3_core/dim_player_team_season_mapping.sql
  - .claude/task/**

impact_map: >
  writers: dim_player_team_season_mapping (3_core) — this change adds a WHERE semi-join to
    dim_team; no grain change, no new column, no ref() change beyond adding sibling core dim_team.
  downstream (grep dbt_project/models for the model name): only mart_roster (5_marts/shared)
    JOINs it — it correctly sheds the 118 All-Star player rows. mart_player_career.sql and
    dim_team_competition_season_mapping.sql name it in DOC COMMENTS ONLY (no join, no impact).
    dbt CLI broken locally; downstream asserted from the grep + model reads, no dbt ls.
  layer_rules: core→core ref (dim_team is 3_core) is layer-legal; check_layer_contract.py stays
    green (no per-competition file, no cross-layer violation).
  deploy_order: table model; the PR slim build (state:modified+) rebuilds dim_player_team_season_
    mapping + mart_roster and re-runs the relationship tests. No --full-refresh (not incremental).
  blast_radius: dim_player_team_season_mapping loses the 138 orphan rows; mart_roster loses the
    118 All-Star player rows (junk). Both relationship tests flip FAIL(138)->PASS. No other mart
    consumes the mapping. No user-facing surface consumes All-Star rows today.

decisions_taken: >
  CPO ruling this session: option 1 — exclude non-entity teams from the affiliation mapping (vs
  adding All-Star teams to dim_team, or downgrading the test). The mapping records real team
  affiliations only; an affiliation to a team that is not even a modelled entity is not usable.

decisions_reserved:
  - The relationship test becomes correct-by-construction (kept as a regression guard). If the
    signal for a REAL team accidentally missing from dim_team is wanted back, a warn-level count of
    excluded (team_id) could be added — NOT in this PR unless the CPO asks.
  - Whether to also stop the squad ingest from fetching exhibition-team squads (upstream option 2)
    is a separate, deferred question — not touched here.

done_when:
  - dim_player_team_season_mapping keeps only team_sks present in dim_team (semi-join); docstring
    notes the entity-integrity filter.
  - `python scripts/check_layer_contract.py` passes; sqlfluff lint clean on the model.
  - PR ci-data-build rebuilds the mapping + mart_roster; both team_sk->dim_team relationship tests
    PASS; prod orphan re-query = 0; mart_roster drops exactly the 118 All-Star rows.
  - scope-auditor + analytics-engineer-reviewer PASS (>=2 risks each); review.md hash binds; CPO merges.

amendments: (none)
