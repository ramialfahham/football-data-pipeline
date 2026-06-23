# Task contract — #526 event team mis-attribution + duplicate-id correction (Path A)

objective: >
  Correct the two confirmed fixture-event team-attribution defects (CPO-approved Path A),
  via a base-layer CPO-owned override seed, and ship a permanent integrity guard:
  (a) Riga FC — provider duplicate id: alias event team 2263 -> 10124 (one club, two ids).
  (b) ASC Kara / ASKO Kara — mis-attribution: re-attribute event team 6424 -> 25274 ONLY in
      fixtures where 25274 is a participant and 6424 is not (ASC Kara's own 2019/2025 events,
      where 6424 IS the participant, stay 6424). The two ids are DISTINCT real clubs — never
      merged. Then add an integrity test (event team in {home, away}) as a permanent ERROR guard.

refs: >
  #526 (defect + full triple-verified diagnosis this session). Seeds the #546 DQ standing scan
  (the integrity test is the generic detector). #549 (proposal-gate) / #550 (automation design)
  are separate follow-ups, not built here.

scope_paths:
  - dbt_project/seeds/fixture_event_team_overrides.csv        # NEW seed (name reserved, see below)
  - dbt_project/seeds/schema.yml                              # document/test the seed
  - dbt_project/models/2_base/api_football/base_apif__fixture_events.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture_event.sql           # extend self-heal to reprocess the fixtures
  - dbt_project/tests/assert_event_team_in_fixture_participants.sql  # NEW integrity test (name reserved)
  - .claude/task/**

impact_map: >
  writers: base_apif__fixture_events derives event team_id from RAW_APIF_FIXTURE_DETAILS
    $.events[].team.id (via stg_apif__fixture_events), today with a null-team_id recovery clause.
    This task adds a seed-driven OVERRIDE of team_id in that base model. To evaluate the
    `reattribute_if_cohabiting` mode it joins base_apif__fixtures_next (fixture participants:
    home_team_id/away_team_id) on fixture_id. NO ingestion/raw writer change — provider data is
    left faithful; the correction lives in transform. The `alias` mode is unconditional.
  downstream: (dbt ls --select base_apif__fixture_events+ --resource-type model, this session)
    base_apif__fixture_events
    base_apif__players
    dim_player
    fct_fixture_event
    mart_fixture_stats__player
    mart_leaderboards
    mart_momentum_window__team
    mart_player_match_log
    mart_player_profile
    mart_roster
  layer_rules: the correction is "entity alignment", which the layer contract places in 2_base
    (1_staging is raw-cleanup-only; 3_core is canonical facts). Seed = seeds-as-configuration.
    No per-competition files; league_code flows through. check_layer_contract unaffected.
  deploy_order: base_apif__fixture_events is a VIEW (recomputes on read). fct_fixture_event is
    INCREMENTAL on raw_ingested_at and will NOT reprocess already-committed rows for a changed
    (non-null -> non-null) team_id. Chosen reprocessing: extend fct_fixture_event's existing
    self-heal clause to also re-run fixtures listed in the override seed (bounded, self-limiting;
    mirrors the #527 null-team_sk self-heal) -- NO --full-refresh. Idempotent; ci-data-build on the
    PR rebuilds and applies it; nothing is broken between merge and rebuild.
  blast_radius: the corrected team_id lands ONLY in fct_fixture_event.team_sk/team_api_id, and
    fct_fixture_event is a LEAF -- `dbt ls --select fct_fixture_event+` returns only itself and NO
    model ref()s it (grep over models/ this session). So NO mart number changes. The marts in the
    base_apif__fixture_events+ closure (mart_leaderboards / mart_roster / mart_player_profile /
    mart_player_match_log / mart_fixture_stats__player / mart_momentum_window__team) sit downstream
    of BASE via base_apif__players -> dim_player (player identity) and fct_fixture_player_stats
    (player match stats) — neither reads the event team_id. Change is bounded to 38 fct_fixture_event
    rows across 3 clubs (25274 ASKO Kara, 6424 ASC Kara, 10124/2263 Riga FC) in 15 fixtures (13 CAFCL
    2020-24 + 2 UEL 2018) -- RAW count this session: event team NOT IN (home,away) = 38 / 15 fixtures;
    recent-season baseline 0. All 15 fixtures ARE present in base_apif__fixtures_next / fct_fixture
    (verified: fct_fixture carries their home/away participants), so the reattribute_if_cohabiting
    path fires and the integrity test covers them.

decisions_taken: >
  Path A approved by the CPO this session ("Path A seems reasonable" + "yes ... open the #526 Path A
  task" + "Option 1"). Identity triple-verified and CPO-accepted this session (external Togo
  championship/CAF records mapping 1:1 to the participant id; disjoint squads across the ASC vs ASKO
  windows; intra-payload RAW trace; Riga players appearing under BOTH ids across seasons): 6424 ASC
  Kara and 25274 ASKO Kara are TWO DISTINCT clubs (Togo = mis-attribution, NEVER merge); 2263/10124
  are ONE club, Riga FC (genuine duplicate id). Mechanism = Option 1: a SINGLE override seed with a
  `mode` column -- `alias` (unconditional id replacement) for Riga; `reattribute_if_cohabiting`
  (replace only where the correct id is a participant and the wrong id is not) for Togo -- applied in
  base_apif__fixture_events. Scope = events-only; dim_team left untouched (CPO-approved; the 2263
  orphan is harmless). Reprocessing = extend the existing fct_fixture_event self-heal (the #527
  pattern), not a full-refresh. Dropping events (coverage-cut) and merging the two Togo clubs (option
  B) are both ruled out by the CPO. CPO confirmed the proposed naming (seed
  fixture_event_team_overrides; columns wrong_team_api_id/correct_team_api_id/mode/note; test
  assert_event_team_in_fixture_participants) and ERROR severity on review this session ("do it") —
  the test carries an explicit config(severity='error').

decisions_reserved:
  - Fallback only: if extending the self-heal cannot reach the committed rows, a one-time
    --full-refresh of fct_fixture_event is CPO cost-authorization — do NOT run unprompted.
  - Seed governance is manual BY DESIGN: a false row (a duplicate inferred from internal name
    similarity) would corrupt attribution until caught. Accepted control = the `note`-column
    external-evidence rule + the integrity test catching NEW violations; automating the
    detect-evidence-escalate loop is tracked by #546 / #550, not built here.

done_when:
  - Override seed carries exactly the 2 confirmed rows (2263->10124 alias; 6424->25274
    reattribute_if_cohabiting); `dbt seed` loads it.
  - base_apif__fixture_events applies the override; for the 15 fixtures the event team_id resolves
    to the correct club; ASC Kara's own 2019/2025 events (participant 6424) are untouched.
  - fct_fixture_event reprocesses the override fixtures (self-heal); team_sk corrected.
  - assert_event_team_in_fixture_participants returns 0 rows across ALL leagues (was 38).
  - dim_player row count + values unchanged (team_id is not a player-identity input).
  - validate-local passes (sqlfluff + dbt parse); ci-validate + ci-data-build green on the PR;
    no mart deltas expected (fct_fixture_event is a leaf) -- ci-data-build confirms the integrity
    test returns 0 rows and that no mart output changed.

amendments: (none)
