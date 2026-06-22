# Task contract — Codify the read-all staging class (#539)

objective: >
  Accurately codify the "read-all" staging snapshot-selection class in layering.md §1_staging,
  and give the fixture-detail staging models the header/yml read-all rationale they currently
  lack. Corrected premise (traced to source this session): RAW_APIF_FIXTURE_DETAILS is NOT
  accumulate-and-grow — batch_fixtures.py only fetches finished fixtures that are missing-entirely
  or empty-stats-within-the-3-day-retry-window, deletes-on-retry, and skips fixtures with good
  stats, so it holds one row per (league_code, fixture_id) — bounded, same outcome as
  RAW_APIF_PLAYERS' per-(team,season) upsert. So both are merge-on-write/per-key; the accurate
  staging rule is: a raw table keyed at a SUB-league_code grain reads ALL rows (no
  `partition by league_code` qualify, which would drop entities) and base resolves
  current-per-entity. #539's "accumulate-vs-upsert distinction" was based on a reviewer misread
  (the staging yml's "duplicates possible" is defensive robustness, not a real accumulation path);
  CPO directed "make it solid" → proceed with the corrected, slimmed scope.

refs: >
  Issue #539 (split from the #518 impact-map-gate PR #540). Source of truth:
  ingestion/api_football/loads/batch_fixtures.py:211-280 (skip-if-present + delete-on-retry);
  docs/data_contract.md (already accurate — fixture_details merge-on-write, one row per fixture).
  CPO direction this session ("Make it solid"). First real exercise of the #540 impact-map gate.

scope_paths:
  - .claude/task/**
  - dbt_project/docs/layering.md
  - dbt_project/models/1_staging/api_football/stg_apif__fixture_events.sql
  - dbt_project/models/1_staging/api_football/stg_apif__fixture_players.sql
  - dbt_project/models/1_staging/api_football/stg_apif__fixture_statistics.sql
  - dbt_project/models/1_staging/api_football/stg_apif__lineups.sql
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml

decisions_taken: >
  CPO-approved framing (this session): codify ONE read-all staging rule (sub-league grain →
  read all rows, no league_code qualify, base resolves current-per-entity) with the loader
  reasons as sub-cases (skip-if-present incremental-accumulation; per-key merge-on-write) —
  do NOT mint a rigid class that mischaracterises fixture_details. The premise correction
  (fixture_details is bounded one-row-per-fixture, not accumulate) is a FACT established by
  reading the loader, not a new decision. DOC + model-comment change only — no SQL/grain edits.

decisions_reserved:
  - none. Framing CPO-approved; the corrected facts are source-verified. If a reviewer surfaces
    a genuinely new CPO-class question (e.g. renaming an existing staging class), escalate it.

impact_map: >
  Change class: DOCUMENTATION ONLY — staging model HEADER COMMENTS + yml `description:` text +
  layering.md prose. No SQL, no grain, no column, no materialization change.
  Writers (NOT edited by this task): RAW_APIF_FIXTURE_DETAILS <- ingestion/api_football/loads/
  batch_fixtures.py (skip-if-present fetch of finished fixtures missing data + delete-on-retry ->
  one row per (league_code, fixture_id)); RAW_APIF_PLAYERS <- loads/squads.py (delete+append per
  (team,season)). Both bounded one-row-per-key.
  Downstream lineage of the edited staging models (`dbt ls --select stg_apif__fixture_*+
  stg_apif__lineups+`, 2026-06-22): base_apif__fixture_{events,players,statistics} ->
  fct_fixture_event / fct_fixture_player_stats / fct_fixture_team_stats -> int_legs__*,
  int_momentum__*, int_season_record__*, int_player_season__metrics,
  int_team_season__full_season_metrics, int_competition_benchmarks__team -> ~20 marts
  (mart_fixture_stats__{player,team}, mart_momentum__*, mart_season_record__*, mart_leaderboards,
  mart_player_profile, mart_roster, mart_team_season, mart_head_to_head, ...).
  Layer rules that apply: check_layer_contract.py staging-purity — staging reads ALL rows with NO
  `partition by league_code` qualify (sub-league grain), which is legal; entity dedup stays in
  base. This task changes no SELECT, so every rule remains satisfied (header comments are stripped
  by the purity check's comment-stripper).
  Deploy ordering: none — comment/description/doc text only; no shared-warehouse migration; the
  next CI rebuild is byte-identical.
  Blast radius: NONE. No shipped number changes — edits are restricted to SQL header comments,
  yml `description` fields, and layering.md prose; no compiled SQL changes.

done_when:
  - layering.md §1_staging codifies the read-all class accurately: sub-league grain -> read all
    rows (no league_code qualify) + base resolves current-per-entity; skip-if-present and
    per-key merge-on-write as the two loader reasons; fixture_details + players both bounded.
  - stg_apif__fixture_{events,players,statistics}.sql and stg_apif__lineups.sql carry a header
    comment stating the read-all rationale (mirroring stg_apif__players.sql).
  - stg_apif__generic.yml entries for those models state the read-all rationale; the "multiple
    ingestions may produce duplicate rows" language is clarified to "base dedups defensively".
  - check_layer_contract.py still passes; dbt parse green; reviewers PASS (scope-auditor +
    analytics-engineer).
  - Tree matches scope_paths.

amendments: (none)
