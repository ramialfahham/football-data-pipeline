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

- `API_FOOTBALL_API_KEY` (required): dashboard key from [API-Sports](https://dashboard.api-sports.io/) (header `x-apisports-key`), **or** RapidAPI key if you use that marketplace.
- `API_FOOTBALL_PROVIDER` (optional): `apisports` (default, direct `v3.football.api-sports.io`) or `rapidapi` (requires an active RapidAPI subscription to the API-Football product).
- `API_FOOTBALL_SEASON` (optional): competition season as **start year** (e.g. `2024` for 2024/25). Defaults to **previous calendar year** (`utcnow().year - 1`). Free plans may only allow a limited year range; set this explicitly if responses return empty `response` with an `errors` object.
- `API_FOOTBALL_FIXTURES_MODE` (optional): `next` (default, `next=20` — often **not** available on free tier) or `from_to` (uses `from` / `to` dates).
- `API_FOOTBALL_FIXTURE_FROM` / `API_FOOTBALL_FIXTURE_TO` (optional, with `from_to`): inclusive `yyyy-MM-dd` bounds. If omitted, defaults to **last N calendar days ending today**, with `API_FOOTBALL_FIXTURE_RANGE_DAYS` (default `14`). For free tiers you may need a **historical** window that matches an allowed `API_FOOTBALL_SEASON` (e.g. season `2024` with dates in 2024/25).

## Data Flow

1. Ingestion writes raw payload snapshots to `API_FOOTBALL` dataset.
2. `1_staging/api_football` models remain source-near and per-league.
3. `2_base/api_football` unions across leagues for downstream modeling.
