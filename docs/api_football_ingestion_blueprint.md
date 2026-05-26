# API-Football v3 Ingestion Blueprint

Source: Condensed from the official API-Football v3 documentation (130 pages).
Purpose: Authoritative reference for the ingestion layer. All design decisions
in `ingestion/api_football/` must be consistent with this document.

---

## 1. Two-Step Ingestion Pattern

The API documentation describes a canonical two-step flow for fixture data:

```
Step 1 — Schedule (one call per competition per season)
  GET /fixtures?league={id}&season={YYYY}
  → Returns metadata only: fixture IDs, kickoff times, venue, status, round
  → No pagination — all fixtures returned in one response
  → Call once daily to detect new fixtures and status changes

Step 2 — Batch sub-data (one call per 20 finished fixtures)
  GET /fixtures?ids=ID1-ID2-...-ID20
  → Returns full embedded sub-data for up to 20 fixture IDs in one call
  → Embedded data: events, lineups, statistics, players, predictions (all inline)
  → Structurally identical to calling each sub-endpoint individually
  → Replaces: /fixtures/lineups, /fixtures/events, /fixtures/statistics,
               /fixtures/players, /predictions
```

This means: **5 separate sub-endpoint calls per fixture → 1 batch call per 20 fixtures** (100× reduction).

---

## 2. Batch Response JSON Structure

The `/fixtures?ids=...` response embeds all sub-data inline. Key paths:

```
response[i]
  .fixture.id                      # int — fixture ID
  .fixture.date                    # ISO 8601 string — kickoff UTC
  .fixture.status.short            # str — e.g. "FT", "NS", "1H"
  .fixture.status.elapsed          # int | null — minutes played
  .league.id                       # int — API-Football league ID
  .league.name                     # str
  .league.season                   # int — season year (YYYY)
  .league.round                    # str — e.g. "Regular Season - 5",
                                   #        "Group Stage - 1", "Quarter-Finals"
  .teams.home.id / .away.id        # int
  .teams.home.name / .away.name    # str
  .goals.home / .goals.away        # int | null
  .score.halftime.home / .away     # int | null
  .score.fulltime.home / .away     # int | null
  .score.extratime.home / .away    # int | null
  .score.penalty.home / .away      # int | null
  .events[j]                       # array — match events (goals, cards, subs)
    .time.elapsed                  # int
    .team.id                       # int
    .player.id / .player.name      # int / str
    .assist.id / .assist.name      # int | null / str | null
    .type                          # str — "Goal", "Card", "subst", etc.
    .detail                        # str — "Normal Goal", "Yellow Card", etc.
  .lineups[j]                      # array — one entry per team
    .team.id                       # int
    .formation                     # str — e.g. "4-3-3"
    .startXI[k].player.id          # int
    .startXI[k].player.name        # str
    .startXI[k].player.number      # int
    .startXI[k].player.pos         # str — "G", "D", "M", "F"
    .substitutes[k].player.id      # int
  .statistics[j]                   # array — one entry per team; [] if unavailable
    .team.id                       # int
    .statistics[k].type            # str — e.g. "Shots on Goal"
    .statistics[k].value           # int | str | null
  .players[j]                      # array — one entry per team
    .team.id                       # int
    .players[k].player.id          # int
    .players[k].player.name        # str
    .players[k].statistics[0]      # object — per-player stats (rating, shots, etc.)
```

**No `group` field exists in the `/fixtures` response.** Group assignment for
knockout/group-stage competitions requires the `/standings` endpoint separately.

---

## 3. Missing Statistics Behaviour

- Statistics are returned as `response[i].statistics = []` (empty array) when unavailable.
- They are **never** `null` or absent from the response structure.
- Non-livescore leagues have a documented **up to 48-hour delay** before statistics
  are available after a match ends.
- Design implication: a fixture with status `FT` and empty statistics is not
  permanently uncovered — retry within a **3-day sliding window** from kickoff.
  After 3 days, treat as permanently uncovered (statistics not coming).

---

## 4. Rate Limits and Burst Management

| Plan    | Daily quota | Per-minute burst |
|---------|-------------|-----------------|
| Free    | 100         | 10/min          |
| Starter | 7,500       | 30/min          |
| Pro     | 75,000      | 300/min         |

**Implementation rules (non-negotiable):**

- Use `time.sleep(0.25)` between calls (Pro plan: 4 calls/sec, safely under 300/min).
- **Synchronous HTTP only** — async/threading triggers a permanent IP ban per the ToS.
- The daily quota is not the binding constraint at Pro tier; per-minute burst is.
- With the two-step batch pattern, a full daily run over all competitions is
  approximately 20–50 API calls total — well within any plan tier.

---

## 5. Coverage Flag Lifecycle

Coverage flags (returned by `/leagues`) declare which endpoints a competition
supports (e.g., `fixtures.lineups`, `fixtures.statistics`).

- Flags are **dynamic**: they may be `false` before a season starts and flip to
  `true` once the first match data is available.
- Flags are not 100% reliable — a flag may be `false` for the reference season
  while data exists for prior seasons.
- **Design implication**: treat coverage flags as a recommendation, not a hard
  constraint. Always attempt a statistics fetch for finished fixtures within the
  3-day window regardless of the flag value.

---

## 6. Round and Group Stage Fields

- **`league.round`** is always present at `response[i].league.round` as a string.
- Format examples:
  - Domestic leagues: `"Regular Season - 5"`
  - World Cup group stage: `"Group Stage - 1"`, `"Group Stage - 2"`, `"Group Stage - 3"`
  - Knockout rounds: `"Round of 16"`, `"Quarter-Finals"`, `"Semi-Finals"`, `"Final"`
  - Qualifiers: `"Qualifying Round - 1"`, etc.
- **There is no `group` field** in the `/fixtures` response. To determine which
  group a team belongs to (e.g., Group A, Group B), use the `/standings` endpoint.

---

## 7. Implications for the Raw Layer

The batch pattern collapses all sub-endpoint raw tables into one:

| Current (5 tables per competition) | Target (1 table per competition) |
|------------------------------------|----------------------------------|
| `RAW_APIF_{LC}_LINEUPS`           | `RAW_APIF_{LC}_FIXTURES`        |
| `RAW_APIF_{LC}_FIXTURE_EVENTS`    |                                  |
| `RAW_APIF_{LC}_FIXTURE_STATISTICS`|                                  |
| `RAW_APIF_{LC}_FIXTURE_PLAYERS`   |                                  |
| `RAW_APIF_{LC}_PREDICTIONS`       |                                  |

Each row in `RAW_APIF_{LC}_FIXTURES` is the full batch response for one run's
set of fixtures — the same structure as `/fixtures?ids=...` returns directly.

---

## 8. Implications for the Ingestion Layer

Files affected by the refactor:

| File | Action |
|------|--------|
| `ingestion/api_football/loads/fanout.py` | Replace with simple batch loop |
| `ingestion/api_football/fixture_scheduling.py` | Delete (budget management not needed) |
| `ingestion/api_football/coverage.py` | Simplify or delete |
| `scripts/populate_coverage_table.py` | Delete (coverage table eliminated) |

The new ingestion loop for finished fixtures:

```python
# Pseudocode — the canonical ingestion pattern
finished_ids = [fid for fid in all_fixture_ids if status[fid] in {"FT", "AET", "PEN"}]
# Retry window: finished within last 3 days OR statistics not yet fetched
to_fetch = [fid for fid in finished_ids if needs_fetch(fid)]

for chunk in batches(to_fetch, size=20):
    ids_param = "-".join(str(fid) for fid in chunk)
    data = get(f"/fixtures?ids={ids_param}")
    store(data)  # one append row per chunk
    time.sleep(0.25)
```

---

## 9. Staging Layer Consequences

Staging models currently read from 5 separate raw tables with flat JSON keys
(e.g., `response[i].fixture_id` was injected by the old pipeline). After the
refactor, all staging models read from `RAW_APIF_{LC}_FIXTURES` and use the
native API paths documented in Section 2.

Key path changes:

| Old (injected key) | New (native API path) |
|--------------------|-----------------------|
| `response[i].fixture_id` | `response[i].fixture.id` |
| `response[i].lineups[j]` | `response[i].lineups[j]` (same) |
| `response[i].events[j]` | `response[i].events[j]` (same) |
| `response[i].statistics[j]` | `response[i].statistics[j]` (same) |
| `response[i].players[j]` | `response[i].players[j]` (same) |

Staging is a 1:1 mapping of raw — no deduplication, no business logic.
Deduplication belongs at the base layer (QUALIFY + ROW_NUMBER).
