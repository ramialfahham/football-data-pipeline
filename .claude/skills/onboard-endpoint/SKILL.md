---
name: onboard-endpoint
description: |
  Evaluate and ingest a NEW API-Football endpoint / data type the pipeline does
  not currently take (e.g. /players/profiles, /players/squads, /transfers).
  Walks through: check whether we already ingest it, make a few throwaway
  verification calls to see what it returns and how good the data is, estimate
  the cost against the daily quota, get the CPO's explicit cost approval, then
  build the ingest (raw -> staging -> base -> loads).

  Use this when bringing a new endpoint/entity online. Do NOT use for adding a
  new competition/league (that's onboard-competition) or for post-ingest health
  checks (that's verify-competition-ingest). This skill never auto-enables a
  recurring pull — the cost decision is always the CPO's.
---

# onboard-endpoint

A new API endpoint is a new recurring cost and a new chain to build. The point of
this skill is to **learn what we're buying before we build it**: confirm the data
is real and useful, size the cost, and get the CPO's explicit sign-off — then
build. It mirrors the cost-gate discipline of `onboard-competition` (Step 0a).

This skill is a **guide**. It does not make production changes by itself: the
verification calls are throwaway, and **no recurring ingest is enabled without
explicit CPO cost approval** (cost is non-negotiable — docs/working_agreement.md §5).

## When to use
- The CPO wants to ingest an endpoint/entity we don't currently take, OR you need
  to decide whether an endpoint is worth ingesting for a feature.

## When NOT to use
- Adding a new competition/league → `onboard-competition`.
- Checking an existing ingest's health → `verify-competition-ingest`.
- Anything that ingests API-Football **predictions** or provider leaderboards
  (topscorers/topassists/top*cards) — we build our own metrics; do not ingest these.

## Procedure

Run in order. Confirm what each step found before moving on.

### Step 0 — Is it already ingested?
Check BOTH — code can exist while the table is stale/empty, or vice versa:
- Ingestion code: search `ingestion/api_football/` for the endpoint path and any
  `loads/` module that already calls it.
- Raw tables: `bq ls --max_results=100 <project>:<raw-dataset>` and look for a
  `RAW_APIF_{entity}`; sample a few rows to confirm it's populated, not an empty
  shell. The raw dataset defaults to `raw` but is configurable — resolve the actual
  name from `ingestion/api_football/settings.py` rather than assuming `raw`.
Only stop if the endpoint is genuinely ingested (code AND a populated raw table).

### Step 1 — Throwaway verification calls (read-only; never store)
Confirm the response shape AND the data quality on real examples before building.

Auth (provider = apisports by default): the key is in the repo-root `.env` as
`API_FOOTBALL_API_KEY`; base URL `https://v3.football.api-sports.io`; header
`x-apisports-key`. (If `API_FOOTBALL_PROVIDER=rapidapi` is set, the base URL is
`https://api-football-v1.p.rapidapi.com/v3` and the headers are `x-rapidapi-key`
+ `x-rapidapi-host: api-football-v1.p.rapidapi.com` — see
`ingestion/api_football/settings.py`; adapt `$B` and the `-H` headers below
accordingly.) **Never print the key** — keep it only in a shell variable, pass it
as a header, and keep shell trace OFF. Load it into a shell var:

```bash
set +x                                   # never echo the key (no shell trace)
KEY=$(grep -E '^API_FOOTBALL_API_KEY=' .env | cut -d= -f2- | tr -d '"' | tr -d '\r')
B=https://v3.football.api-sports.io
```

Pick the **cheapest axis** the endpoint supports and verify it:
- Many endpoints can be pulled **by team** (one call returns all rows for that
  team's players — e.g. `/players/squads?team=`, `/transfers?team=`). By-team is
  far cheaper than **by-player** (one call per player). Always check whether a
  by-team (or paginated-directory) form exists before assuming per-player.

Call a few representative cases and summarize the JSON shape + quality — include
the **hard cases** for that data (e.g. for transfers: a clean move, a loan, a
lower-league player). Example:

```bash
curl -s -H "x-apisports-key: $KEY" "$B/<endpoint>?<param>=<id>" | python -c "
import sys, json
d = json.load(sys.stdin)
print('errors:', d.get('errors'), 'results:', d.get('results'), 'paging:', d.get('paging'))
r = d.get('response') or []
print(json.dumps(r[0], indent=1)[:1200] if r else 'EMPTY')"
```
(Build the summary with plain string concatenation, not f-strings containing
escaped quotes — Python f-strings can't hold backslashes.)

Record: which fields exist, whether the dates/identity you need are present, and
any noise (messy enum fields, duplicate rows, missing values) that will need
cleaning in staging. The `�` you may see is just the terminal mangling UTF-8
(€, ü) — the stored JSON is fine.

### Step 2 — Estimate the cost
- Get the plan + quota: `curl -s -H "x-apisports-key: $KEY" "$B/status"` →
  `subscription.plan`, `requests.limit_day`, `requests.current`.
- Size the universe from our data (e.g. distinct teams / players, active vs all)
  via `bq query` against the core dims.
- Compute **backfill** (cheapest axis × universe) and **ongoing/day** (refresh
  cadence × universe, amortized). Slow-moving data (bios, careers) refreshes
  monthly; squad/transfer data weekly during windows.
- State both as call counts against `limit_day`, and how the backfill spreads
  across days within quota.

### Step 3 — CPO cost-approval gate (do not skip)
**Ask the CPO directly** — present the cost from Step 2 in plain language and ask
for explicit approval to enable the recurring pull (this mirrors
`onboard-competition` Step 0a, which asks the user the cost questions before any
file is written). Do NOT write ingestion code or enable a schedule until that
approval is given, and **never infer or self-grant it** — cost is non-negotiable
(CLAUDE.md "Cost is non-negotiable"; docs/working_agreement.md §5). Once the CPO
gives it, the approval is recorded by the thing it changes (docs/working_agreement.md
§11): the registry entry in the MR, quoted in the contract's `decisions_taken`, and
named in the MR head as a recurring cost he is approving by merging. No new
daily run cadence without separate approval — ride the 04:00 run or a sub-schedule.

### Step 4 — CPO history-depth decision
How far back to backfill is a CPO decision stored as the source's history depth
(active-only vs full history). Get it explicitly; it's the main backfill-cost lever.

### Step 5 — Build (each piece via the normal contract -> review -> PR)
Follow the unified-raw pattern ("Path B" — all competitions share unified
`RAW_APIF_{entity}` tables discriminated by a `league_code` column; no
per-competition files):
- **Raw:** a `RAW_APIF_{entity}` table. The landing schema — including `league_code`
  (the data contract requires it on raw tables; even player/team-keyed pulls stamp the
  league they were fetched under, e.g. `loads/squads.py`) and the merge/landing key —
  must follow `docs/data_contract.md`. Do not invent a schema.
- **Ingestion:** a new `loads/` module mirroring `loads/squads.py`; registry-driven;
  respects the ingest lock + daily quota. If the endpoint is part of the per-fixture
  fanout, also wire it into the ingestion coverage/completeness CHECK (Python, not a
  dbt model) — add it to `ENDPOINT_REQUIRES_NONEMPTY` + `SHELL_KEY_TO_ENDPOINT` in
  `ingestion/api_football/coverage.py` (omitting this makes the fanout silently
  re-fetch already-covered fixtures every run). Team-/player-keyed pulls (like
  squads/transfers) are NOT fanout and do not go there.
- **Fetch-side skip (mandatory — see `docs/data_contract.md` → "Fetch-side skip").**
  Storage-side merge bounds the table, NOT the API cost. Before fetching, read the keys
  already in the target raw table and fetch only the delta; re-fetch only the live/current
  season (immutable finished data is fetched once). Because team-/player-keyed pulls are NOT
  part of the fixture fanout, they need their OWN skip — mirror `captured_player_team_seasons`
  / `players_needing`, do not ship a bare loop over every key (that re-pays the full quota
  every run). Log `to_fetch=/skipped_cached=` so a disabled skip shows up in the run log.
- **Staging:** a generic `stg_apif__{entity}` (raw cleanup only).
- **Base/Core/Marts:** as the feature needs — base dedup/clean (handle the noise
  found in Step 1), core facts/dims, marts for consumption. Ship the mart first if
  a surface needs data we don't yet expose.

## Known edge cases
- **Axis matters most for cost.** A by-team or paginated-directory pull can be 30×+
  cheaper than per-player. Always look for the cheaper axis in Step 1.
- **Provider noise.** Enum/`type` fields are often inconsistent and rows can
  duplicate; plan a dedup/clean pass in base. Verify the *keys you need* (dates,
  ids) are reliable, not the cosmetic fields.
- **Retired chains.** Re-enabling a previously-retired endpoint (e.g. transfers)
  is a rebuild + a cost reversal — treat it as a fresh onboard, with the cost gate.

## Related
- `onboard-competition` — add a new league (registry-only, zero SQL).
- `verify-competition-ingest` — post-ingest health check.
- docs/data_contract.md — raw landing + merge model.
- docs/operations_guide.md — ingest lock, env vars, quota.
