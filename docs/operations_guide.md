# Operations guide: running and troubleshooting ingestion

This guide is for **anyone operating** the API-Football → BigQuery loader: what the knobs do, why safety checks exist, and how to run a **one-off backfill** versus a **steady daily job**. For **what** we store and **which tables** map to which API calls, see [`data_contract.md`](data_contract.md). Ingestion behaviour and HTTP discipline are defined in the **`ingestion/api_football`** package in this repository.

---

## How to run ingestion (local)

1. **Credentials:** use [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials) for the GCP project that owns the raw dataset.
2. **Secrets:** copy `.env.example` to **`.env`** in the repo root and set **`API_FOOTBALL_API_KEY`**. Never commit `.env`.
3. **Dependencies:** activate the repo **`.venv`** (see `README.md`), then from the repo root run `pip install -r requirements.txt` (includes `python-dotenv`, which loads `.env` automatically when the loader starts).
4. **Command (PowerShell):** open a terminal **at the repository root** (the folder that contains `ingestion/` and `requirements.txt`), then run:

   ```powershell
   $env:PYTHONPATH = "."
   python -m ingestion.api_football.main
   ```

**Exit codes (CLI):**

| Code | Meaning |
|------|--------|
| **0** | Run finished; pipeline OK and completeness passed (or completeness was skipped). |
| **1** | Pipeline error (exception or non-success HTTP path from the job). |
| **2** | Another run holds the **ingest lock** (BigQuery lease still valid) — do not start a second writer without clearing or waiting. |
| **3** | **Completeness check** failed (fanout coverage short vs merged fixtures) while strict mode is on — see below. |

The job prints phase lines such as `[api-football] league=D1 phase=fixtures` so a long run is not silent.

---

## Environment variables (from `.env.example`, plain language)

Values in `.env` override defaults. **Commented lines in `.env.example` are optional** — uncomment and set only when you need to change behaviour.

### `API_FOOTBALL_API_KEY` (required)

Your API-Football / API-Sports (or RapidAPI) key. Without it, the process stops immediately.

### `API_FOOTBALL_INGEST_PROFILE` (optional)

Controls the **“shape” of a run”**: how many seasons we try to cover by default and how aggressive pacing and caps are.

- **Unset** (or explicitly **`full`** / aliases **`paid`** / **`complete`**): treated as a **warehouse-style** run. The code applies **paid-friendly defaults** (via internal `setdefault`): multi-season discovery within the **configured Bundesliga season-year window** in code, **no** sleep between HTTP calls unless you set one, higher pagination caps, and the **fanout soft cap turned off** (`-1`) unless you override it. Use when you have **enough daily quota** for a large pull.
- **`default`**, **`economy`**, or **`free`**: **no** those bundled defaults — you get a **single inferred season** (from today’s date and the project’s July rule) and the usual **free-tier-friendly** pause between calls unless you set `API_FOOTBALL_REQUEST_PAUSE_MS` yourself. Use for **low daily limits** or smoke tests.

**Rule of thumb:** unset = “use the big profile”; set to **`default`** when you must stay inside **~100 requests/day** style limits or want one season only.

### `API_FOOTBALL_BIGQUERY_DATASET` (optional)

BigQuery **dataset id** where `RAW_*` tables are written. Default **`raw`**. Must match dbt’s **`raw_schema`** for staging to read the same place.

### `API_FOOTBALL_FIXTURES_MODE` (optional)

How **`/fixtures`** is queried. Default **`season`** = one call style per season using `league` + `season`. Other modes (`from_to`, `next`) exist for different product needs; **`next`** often requires a paid plan.

### `API_FOOTBALL_FIXTURE_USE_PAGE` (optional)

Whether to send **`page=`** on **`/fixtures`** when in `season` mode. Many plans **reject** fixture paging — leave **`0`** / unset unless you confirmed it works on your key.

### `API_FOOTBALL_LINEUPS_MAX_FIXTURES` (optional)

Hard cap on how many fixtures get the **per-fixture bundle** (lineups, events, statistics, fixture players, predictions) in **one** run. Empty = no extra cap beyond quota math and soft caps. Use to **fit inside a daily budget**.

### `API_FOOTBALL_FANOUT_SOFT_CAP_FIXTURES_NO_HEADER` (optional)

When the API does **not** return a daily quota header, this limits how many fixtures enter that bundle (default **`6`** in economy-style defaults). **`full`** profile sets it to **`-1`** (disabled) unless you override. Set **`-1`** yourself to disable the soft cap when you trust your quota.

### `API_FOOTBALL_FETCH_TRANSFERS` (optional)

**`1`** (default) = load **`/transfers`**. Set to **`0`** / **`false`** / **`no`** to skip transfers and save requests.

### `API_FOOTBALL_FANOUT_PRIORITY` (optional)

Order in which fixtures are considered for the expensive per-fixture bundle:

- **`upcoming`** (default): matches in the **next few weeks** (see `API_FOOTBALL_FRESH_HORIZON_DAYS`) first — good for **product freshness**.
- **`cursor`**: walk the full list from a stored **offset** (`RAW_D1_APIF_INGEST_CURSOR`) so scheduled runs **advance the archive** over many days.
- **`season_chrono`** / **`chrono`**: earliest kickoff first for the whole list.

### `API_FOOTBALL_FRESH_HORIZON_DAYS` (optional)

With **`upcoming`**, how many **calendar days ahead** of UTC “today” count as “fresh” for ordering (default **14**).

### `API_FOOTBALL_SKIP_PLAYERS` (optional)

**`1`** / **`true`** / **`yes`** skips **`/players`** squad pulls. Saves a large block of calls; use on **cursor** archive runs if squads are refreshed separately.

### `API_FOOTBALL_REQUEST_PAUSE_MS` (optional)

Milliseconds to sleep **after each successful** HTTP call. When **unset**, economy-style runs default to a slow pace (~free tier **10/min**); **`full`** profile sets **`0`** via `setdefault` unless you set this explicitly.

### `API_FOOTBALL_SKIP_INGEST_LOCK` (optional)

**`1`** / **`true`** / **`yes`** = **do not** take the BigQuery single-flight lock. **Only for local debugging.** Two overlapping jobs can corrupt merged payloads.

### `API_FOOTBALL_INGEST_LEASE_MINUTES` (optional)

How long a successful lock holder keeps the lease (default **180**). After a **crash**, another run can acquire the lock once **`lease_until`** has passed.

### `API_FOOTBALL_SKIP_COMPLETENESS_CHECK` (optional)

**`1`** / **`true`** / **`yes`** = skip the post-run **fanout vs fixtures** comparison and the `ingest_completeness_json` log line.

### `API_FOOTBALL_FAIL_ON_INCOMPLETE` (optional)

**`1`** (default) = if completeness finds missing fanout coverage, the job returns **exit code 3** (and HTTP **503** in Cloud Functions). Set to **`0`** / **`false`** / **`off`** during a **long multi-day backfill** so “partial but merged” runs do not fail the scheduler until coverage catches up.

---

## Ingest lock (single-flight)

**What it is:** a single row in BigQuery table **`RAW_APIF_INGEST_LOCK`** (same dataset as raw loads) records **`holder_run_id`** and **`lease_until`**.

**Why it exists:** two ingestion jobs writing the **same** raw tables at once can **read partial state**, merge independently, and **overwrite** each other — a classic race. The lock makes overlapping runs **wait** (or exit with code **2**) instead of corrupting data.

**If you see “another ingestion holds the lease”:** either a job is **still running**, a previous run **crashed** before release, or the lease is still inside **`lease_until`**.

**What to do:**

- **Wait** until `lease_until` if another process is legitimate.
- If nothing is running and you are sure it is **stale**, clear it from the repo root (ADC + same project):

  ```powershell
  $env:PYTHONPATH = "."
  python scripts\clear_apif_ingest_lock.py
  ```

- **Emergency local only:** `API_FOOTBALL_SKIP_INGEST_LOCK=1` — avoid in production.

---

## Completeness check (fanout vs fixtures)

**What it is:** after loading, the job compares **fixture ids** in merged **`RAW_D1_APIF_FIXTURES_NEXT`** to fixture ids present in each batched fanout payload (**LINEUPS**, **FIXTURE_EVENTS**, **FIXTURE_STATISTICS**, **FIXTURE_PLAYERS**, **PREDICTIONS**). It does **not** validate every other table (e.g. squad **`PLAYERS`**) against that list.

**Why it exists:** under **daily caps**, one run may only refresh **some** fixtures’ detail bundles. The check answers: “**Given** our merged fixture list, do the five fanout blobs **cover every** fixture id?” Operators and alerts can watch the printed line:

`[api-football] ingest_completeness_json={...}`

**If it fails** (`all_fanout_complete: false`): expected during backfill until enough runs have merged fanout for all fixtures — **not** necessarily an API outage. With **`API_FOOTBALL_FAIL_ON_INCOMPLETE=1`** (default), the process exits **3** so schedulers can page someone. Set **`API_FOOTBALL_FAIL_ON_INCOMPLETE=0`** until the JSON shows complete, or skip the check entirely with **`API_FOOTBALL_SKIP_COMPLETENESS_CHECK=1`** (not recommended long-term).

---

## Playbooks

### A) Fresh backfill (first fill or deliberate rebuild)

**Goal:** land a **wide** merged snapshot (many seasons / full fanout over time) without fighting the scheduler on exit **3**.

1. Confirm **`.env`**: `API_FOOTBALL_API_KEY`, dataset id if non-default, and profile suitable for your **quota** (`full` vs `default`).
2. Set **`API_FOOTBALL_FAIL_ON_INCOMPLETE=0`** until fanout coverage catches up; optionally cap **`API_FOOTBALL_LINEUPS_MAX_FIXTURES`** per day.
3. Use **`API_FOOTBALL_FANOUT_PRIORITY=cursor`** (and optionally **`API_FOOTBALL_SKIP_PLAYERS=1`** on cursor-only days) to **walk** the fixture list across runs — see [`data_contract.md`](data_contract.md) for the merge model.
4. **Clear a stale lock** if you get exit **2** and no job is running (`scripts/clear_apif_ingest_lock.py`).
5. Run **`python -m ingestion.api_football.main`** as often as quota allows until **`ingest_completeness_json`** shows **`all_fanout_complete": true`** for D1.
6. Turn **`API_FOOTBALL_FAIL_ON_INCOMPLETE`** back to **`1`** for normal operations.
7. Run **`dbt build --project-dir .\dbt_project --selector staging`** when raw looks good.

**If you truly need an empty slate:** selectively drop or truncate raw tables in BigQuery only when you understand what will be re-fetched — not required for day-to-day merges.

### B) Daily update (steady state)

**Goal:** refresh **cheap** league-wide tables every day and **prioritise near-term matches** for expensive fanout.

1. Keep **`API_FOOTBALL_FAIL_ON_INCOMPLETE=1`** once backfill is complete (alerts on regression).
2. Default **`API_FOOTBALL_FANOUT_PRIORITY=upcoming`** so the next match window gets detail first.
3. Keep the **ingest lock enabled** so scheduled jobs never overlap.
4. Optionally run a **second** schedule with **`FANOUT_PRIORITY=cursor`** (and optional **`SKIP_PLAYERS`**) to advance the long tail — same pattern as in the backfill playbook, but smaller slices.

---

## Related documents

| Topic | Document |
|--------|-----------|
| Raw tables, merge idea, endpoint map | [`data_contract.md`](data_contract.md) |
| dbt layers and naming | `dbt_project/docs/layering.md` (in-repo) |
