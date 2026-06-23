# Task contract — dim_coach + dim_coach_team_mapping (Coach entity)

objective: >
  Build the coach entity surface from the ALREADY-INGESTED RAW_APIF_COACHES (no new ingest, no cost
  gate). Mirror the dim_player/dim_team entity/affiliation split:
  (1) dim_coach — pure coach ENTITY (one row per coach; identity: name/nationality/birth/photo; NO
      league_code).
  (2) dim_coach_team_mapping — coach<->team AFFILIATION from the coach `career[]` stints (one row per
      (coach, team, stint) with start/end dates). The "clubs managed" history; current-coach-per-team
      is derivable from the open/latest stint (left to the deferred consumption PR).
  Chain: sources.yml + staging (entity flatten + career unnest) + base (dedup x2) + core (the 2 dims).
  Data-forced design: career[] clubs EXCEED our dim_team set (youth/reserve/untracked sides), so the
  mapping carries the provider team_id + team_name and team_sk is a SOFT link (no strict FK) — keep
  full history over a strict link. Affiliation source = career[] (authoritative), NOT coach.team
  (the fetch-context provenance team).

refs: >
  content_architecture.md (Coach thin SEO entity: header chip + Team History + Coach page Overview =
  current club + clubs managed). CPO this session: coaches after the career mart (done); names
  dim_coach + dim_coach_team_mapping (incl start/end); entity + affiliation this PR, defer the
  consumption (website #391 PAUSED). Pattern: project_player_model_redesign / project_team_model_redesign.

scope_paths:
  - dbt_project/models/1_staging/api_football/sources.yml
  - dbt_project/models/1_staging/api_football/stg_apif__coaches.sql
  - dbt_project/models/1_staging/api_football/stg_apif__coach_career.sql
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/2_base/api_football/base_apif__coaches.sql
  - dbt_project/models/2_base/api_football/base_apif__coach_career.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/dim_coach.sql
  - dbt_project/models/3_core/dim_coach_team_mapping.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/docs/layering.md
  - .claude/task/**

impact_map: >
  writers: 6 NEW additive models reading the existing RAW_APIF_COACHES (newly declared as a dbt source)
    + dim_team (soft team_sk link in the mapping). stg_apif__coaches (flatten $.response[].coach),
    stg_apif__coach_career (unnest coach.career[]); base_apif__coaches (dedup -> 1 row/coach_api_id),
    base_apif__coach_career (dedup stints); dim_coach (pure entity, no league_code, mirrors dim_player),
    dim_coach_team_mapping (coach<->team stints + start/end, soft team_sk). NO existing model modified.
  downstream: NONE — new LEAF dims; nothing ref()s them (Coach page/chip consumption deferred, website
    #391 PAUSED). `dbt ls --select dim_coach+ dim_coach_team_mapping+` would return only themselves once
    built. Source: RAW_APIF_COACHES (629 rows / 45 leagues, verified this session); dim_team read for the
    soft team link.
  layer_rules: staging = raw flatten/unnest (one source -> two grains, exactly like RAW_APIF_FIXTURE_DETAILS
    -> stg events/players/statistics); base = dedup + entity resolution; core = canonical dims. dim_coach
    is a pure entity (drops league_code, mirrors dim_player). league_code flows through staging/base. No
    per-competition logic; check_layer_contract unaffected.
  deploy_order: additive — 6 new relations, no existing model changed, nothing depends on them. ci-data-build
    creates them. No shipped-number change.
  blast_radius: NONE — additive only; no existing mart/number moves. New data = coach entity + career
    mapping. The mapping's team_sk is a SOFT link (no strict relationships test) because career[] clubs
    (youth/reserve/foreign-untracked) exceed dim_team — a strict FK would fail on untracked clubs.

decisions_taken: >
  CPO this session: (a) coaches ingest ALREADY exists (RAW_APIF_COACHES) — no new ingest / no cost gate;
  (b) NAMES = dim_coach (entity) + dim_coach_team_mapping (affiliation, incl start/end dates); (c) scope =
  entity + affiliation this PR, defer the Coach page mart + the team-header current-coach chip (website
  #391 PAUSED). Pattern = the dim_player/dim_team entity/affiliation split. Affiliation source = career[]
  (authoritative coach history), NOT coach.team (fetch-context provenance). The mapping carries provider
  team_id + team_name; team_sk soft-links to dim_team where tracked, NO strict FK (career clubs exceed our
  tracked set — data-forced, keeps full history).
  base_apif__coach_career guards `start_date is not null` (currently 0 rows; prevents a future
  null-start surrogate-key collision / not_null CI break). The staging snapshot rule (read-all vs
  latest-per-league) was a §10 escalated + ruled this session — see decisions_reserved + escalations.log.

decisions_reserved:
  - SNAPSHOT RULE (§10, ESCALATED + RULED this session): read-all vs latest-per-league for the
    complete-snapshot RAW_APIF_COACHES — the two reviewers split. Put to the CPO with the ~120-coach
    delta evidence (no anchoring). CPO ANSWER: read-all / all-time ("all") — preserve every coach ever
    seen (mirrors dim_player/dim_team). Durable record: escalations.log (2026-06-23) + review.md.
  - The Coach consumption (thin page Overview = current club + clubs managed; the team-header current-coach
    chip + its "open/latest stint" derivation) is a later mart — website #391 PAUSED, not this PR.
  - Display enrichment (dim_team-resolved names vs the provider team_name on the mapping) is the consumption
    PR's call.

done_when:
  - sources.yml declares raw_apif_coaches; stg_apif__coaches + stg_apif__coach_career flatten/unnest cleanly.
  - base_apif__coaches: one row per coach_api_id; base_apif__coach_career: one row per (coach, team, start).
  - dim_coach: pure entity (coach_sk + identity), grain coach_sk unique+not_null; dim_coach_team_mapping:
    (coach_sk, team_api_id, start_date) grain unique, start/end dates, coach_sk relationship to dim_coach.
  - layering.md dimension inventory lists dim_coach + dim_coach_team_mapping.
  - validate-local (dbt parse + sqlfluff + check_layer_contract) green; ci-data-build green (build + tests).

amendments: (none)
