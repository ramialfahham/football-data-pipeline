# Task contract — feat: squad capture for finished competitions (club + national, team-keyed)

> Forward-looking fix for the squads watch-item (resolved this session as ingest-mode behaviour,
> NOT a bug): finished/idle competitions run in `poll` mode, which skips every per-team phase,
> so RAW_APIF_SQUADS (a new table) only ever held the currently in-season comps — recently-ended
> comps (PL/PD/BL1/BL2 …) are absent. This adds a squad CATCH-UP for finished comps.
> Ingestion CODE + TESTS only — NO dbt models, NO protected paths, and NO API spend in the PR
> itself (the catch-up rides the daily run / a CPO-approved dispatch, like PR-a's code↔backfill
> split). Reviewers: scope-auditor + data-engineer-reviewer.

objective: >
  Capture a team's current squad (/players/squads) even when ALL its competitions have finished,
  so RAW_APIF_SQUADS covers recently-ended comps, not only those in-season. A squad is a TEAM
  property, so the catch-up is keyed by TEAM and deduped across competitions; it covers CLUB and
  NATIONAL teams alike (validated on real rows: /players/squads returns full national call-ups —
  WC 26.0 players/team, ACN 27.6, UNL 27.3 — i.e. selected-but-unused players the appearance fact
  cannot give). The rule uses signals we already have per competition (still-playing? +
  last-recorded season):
    - In-season (full mode) -> squads captured every run (UNCHANGED, Phase 3b).
    - Finished (poll / idle_complete) -> for that comp's teams, if we do NOT already have the
      team's squad for its last-recorded season, capture it ONCE and stamp the snapshot with that
      season.
  Team lists for finished comps come from the latest-season fixtures already fetched in the poll
  phase (NO extra API calls beyond the squad calls themselves). Dedup is by team: across all comps,
  against teams captured in-season this run (active comps), and against squads already stored for
  that season. No day-count window — season + still-playing fully decide it; daily runs catch each
  comp within ~a day of its season ending.

refs: >
  Squads watch-item (handover 2026-06-15) resolved this session: poll-mode (idle_complete) comps
  skip per-team phases, so the new RAW_APIF_SQUADS held only the 14 in-season comps. CPO rulings
  2026-06-16: (1) key by team/club, dedup across comps; (2) national teams use the SAME
  /players/squads membership source — the appearance fact (PR-b) is complementary, NOT a substitute
  (it misses non-playing squad members). Historical per-edition membership parked as #477.

scope_paths:
  - ingestion/api_football/orchestrator.py
  - ingestion/api_football/loads/competition_runner.py
  - ingestion/api_football/loads/player_squads.py
  - docs/data_contract.md
  - tests/test_player_squads_catchup.py
  - .claude/task/contract.md

decisions_taken: >
  CPO 2026-06-16: (1) squad capture/catch-up keyed by TEAM, deduped across all competitions —
  capture a team while active anywhere, catch up a team idle everywhere. (2) /players/squads is the
  squad-MEMBERSHIP source for BOTH club and national teams (validated: real national rosters incl.
  non-players); the appearance fact (fct_player_team_season, PR-b) is a complementary playing-time
  layer, never the roster. (3) No recency day-window — the per-comp signals (still-playing? +
  last-recorded season) plus a season stamp decide capture; daily runs make it timely. (4) The
  season is stamped on the squad snapshot so per-season dedup is exact and the raw row is
  self-describing (additive payload key — existing stg_apif__squads response[] shape is unchanged).

decisions_reserved:
  - Historical / per-edition squad membership (/players/squads is current-only) — PARKED as #477;
    do NOT build here.
  - National-team rosters/caps in the player CORE/MARTS layer (how they surface downstream) are
    PR-b / PR-c, NOT this ingestion PR.
  - Surfacing the new `season` field in stg_apif__squads is a downstream staging change — NOT in
    this PR; flag for the analytics-engineer when staging next changes.
  - Any §10-class question that surfaces (e.g. a NEW ingest mechanism beyond "catch up finished
    comps", or reshaping the merged per-league landing) -> escalate BLINDED, do not self-rule.

done_when:
  - National-squad data quality re-confirmed on real rows (DONE pre-contract: WC/ACN/UNL full
    rosters at ~26-28 players/team).
  - Pure team-selection function unit-tested (tests/test_player_squads_catchup.py): given
    finished-comp team_ids, active team_ids, and already-captured (team, season), returns exactly
    the teams to fetch — excludes active + already-have-for-season, dedupes across comps. No network.
  - Squad snapshots carry the stamped season (both in-season Phase 3b and the catch-up); the
    catch-up writes finished comps' not-yet-captured teams once; in-season Phase 3b behaviour
    otherwise unchanged.
  - docs/data_contract.md documents the catch-up + the season-stamped squads payload.
  - validate-local clean (python lint + the ingestion pytest); dbt parse unaffected (no model edits).
  - reviewers: scope-auditor (always) + data-engineer-reviewer (ingestion) both PASS.
  - POST-MERGE (separate, CPO cost decision — NOT in this PR): on the next dispatched/daily run,
    RAW_APIF_SQUADS gains the finished club comps (PL/PD/BL1/BL2); verify read-only.

amendments: (none)
