# API-Football MVP Scope

This document defines the minimum API-Football footprint for player-focused pre-match insights.

## Goal

Collect enough player context for fan-facing pre-match views without high API spend.

## Endpoints in Scope

- `/fixtures` with `next=20` per league
  - raw tables: `RAW_APIF_FIXTURES_NEXT_<LEAGUE>`
- `/players` per team for teams in upcoming fixtures
  - raw tables: `RAW_APIF_PLAYERS_<LEAGUE>`
- `/fixtures/lineups` per upcoming fixture
  - raw tables: `RAW_APIF_LINEUPS_<LEAGUE>`
- `/injuries` per league/season
  - raw tables: `RAW_APIF_INJURIES_<LEAGUE>`

## League Scope

- D1, E0, I1, SP1, F1

## Cost Controls

- Only upcoming fixtures (no full-season exhaustive pulls).
- Only player pulls for teams appearing in those fixtures.
- Batch schedule 2-4 times daily (not live minute-by-minute).

## Environment Variables

- `API_FOOTBALL_API_KEY` (required)

## Data Flow

1. Ingestion writes raw payload snapshots to `API_FOOTBALL` dataset.
2. `1_staging/api_football` models remain source-near and per-league.
3. `2_base/api_football` unions across leagues for downstream modeling.
