# Operations guide

Run and troubleshoot the API-Football → BigQuery loader. Ingestion behaviour lives in the `ingestion/api_football` package; raw tables and the completeness definition are documented in [`data_contract.md`](data_contract.md).

## Pipeline order

After a successful ingest (exit `0`), run dbt so staging and downstream layers reflect the raw snapshot just written:

```powershell
dbt build --project-dir .\dbt_project --selector staging
```

Extend with `--selector downstream` when those layers exist. Encode the same order in any scheduler so queries always track the last good load.

---

## Prerequisites

- [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials) for the GCP project that owns the raw dataset. The ingest merge read-back streams via the BigQuery Storage Read API (gRPC) to avoid REST's 20 MiB per-row cap on merged payloads, so the identity running the loader needs `bigquery.readsessions.create`, included in `roles/bigquery.user` and `roles/bigquery.dataViewer`.
- `.env` at the repo root, copied from `.env.example`, with `API_FOOTBALL_API_KEY` set. Never commit `.env`.
- Activated repo `.venv` (see `README.md`) with dependencies installed: `pip install -r requirements.txt`. `python-dotenv` loads `.env` automatically at startup.

---

## Running the loader

From a PowerShell terminal at the repo root (the folder containing `ingestion/` and `requirements.txt`):

```powershell
$env:PYTHONPATH = "."
python -m ingestion.api_football.main
```

The job prints phase markers such as `[api-football] league=D1 phase=fixtures` so long runs are not silent.

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Run finished; pipeline OK and completeness passed (or the check was skipped). |
| `1` | Pipeline error (exception or non-success HTTP path). |
| `2` | Another run holds the ingest lock (BigQuery lease still valid). Do not start a second writer without clearing or waiting. |
| `3` | Per-match coverage check failed while strict mode is on: lineups / events / statistics / fixture players / predictions do not yet cover every **finished** fixture (status `FT`/`AET`/`PEN`) in the merged fixtures list. Unplayed fixtures are ignored by this check. See Monitoring a run. |

---

## Environment variables

Values in `.env` override defaults. Uncomment lines in `.env.example` only when changing behaviour.

### Credentials and scope

#### `API_FOOTBALL_API_KEY` (required)

API-Football / API-Sports / RapidAPI key. Without it, the process exits immediately.

#### `API_FOOTBALL_BIGQUERY_DATASET` (optional)

BigQuery dataset id for `RAW_*` tables. Default `raw`. Must match the dbt `raw_schema` so staging reads the same dataset.

#### `API_FOOTBALL_INGEST_PROFILE` (optional)

Shapes defaults for scope, pacing, and caps.

- Unset or `full` / `paid` / `complete`: multi-season discovery across the configured Bundesliga window, no inter-call sleep, higher pagination caps, fanout soft cap disabled (`-1`). Intended for keys with enough daily quota for a wide pull.
- `default`, `economy`, or `free`: single inferred season (from today's date and the July rollover rule), free-tier-friendly pacing between calls, soft caps active. Intended for ~100 requests/day keys or smoke tests.

Explicit values for any individual variable override the profile defaults.

### Tuning knobs

#### `API_FOOTBALL_FIXTURES_MODE` (optional)

How `/fixtures` is queried. Default `season` (`league` + `season` only). Alternative modes: `from_to` (date range) and `next` (upcoming matches — usually paid-only).

#### `API_FOOTBALL_FIXTURE_USE_PAGE` (optional)

Whether to send `page=` on `/fixtures` in `season` mode. Default `0`. Set to `1` only if the key is known to accept paging on `/fixtures`.

#### `API_FOOTBALL_LINEUPS_MAX_FIXTURES` (optional)

Hard cap on fixtures entering the per-fixture bundle (lineups, events, statistics, fixture players, predictions) in one run. Empty default means no extra cap beyond quota math and soft caps. Set when a specific daily budget must not be exceeded.

> Fanout selection: before the per-fixture pass, the loader reads the merged payloads of the five batched raw tables and skips, per endpoint, any `fixture_id` already covered. Only fixtures that still need at least one endpoint enter the priority and budget math. The log line `[api-football] fanout_selection league=… target=… already_complete=… missing_any_endpoint=…` at the start of the phase shows how much work remains this run.

#### `API_FOOTBALL_FANOUT_SOFT_CAP_FIXTURES_NO_HEADER` (optional)

Fixture cap applied when the API does not return a daily quota header. Default `6` under economy profile, `-1` (disabled) under `full`. Set to `-1` manually when the quota is trusted and no cap is wanted.

#### `API_FOOTBALL_FANOUT_PRIORITY` (optional)

Order in which fixtures enter the per-fixture bundle.

- `upcoming` (default): next few weeks first (see `API_FOOTBALL_FRESH_HORIZON_DAYS`). Best for product freshness.
- `cursor`: walk the full list from a stored offset in `RAW_D1_APIF_INGEST_CURSOR`. Best for steadily advancing the archive across scheduled runs.
- `season_chrono` / `chrono`: earliest kickoff first.

#### `API_FOOTBALL_FRESH_HORIZON_DAYS` (optional)

Days ahead of UTC today that count as "fresh" for `upcoming` priority. Default `14`.

#### `API_FOOTBALL_SKIP_PLAYERS` (optional)

`1` / `true` / `yes` skips `/players` squad pulls. Use on cursor archive runs when squads are refreshed on a separate schedule.

#### `API_FOOTBALL_FETCH_TRANSFERS` (optional)

`1` (default) loads `/transfers`. Set to `0` / `false` / `no` to skip transfers entirely.

#### `API_FOOTBALL_TRANSFERS_USE_PAGE` (optional)

Whether to send `page=` on `/transfers`. Default `0`, because many plans (including free and several paid tiers) reject paging on this endpoint with `"The Page field do not exist."`. Pairs with `API_FOOTBALL_TRANSFERS_MAX_PAGE` (default `3`) when enabled.

#### `API_FOOTBALL_REQUEST_PAUSE_MS` (optional)

Milliseconds to sleep after each successful HTTP call. Unset gives free-tier-friendly pacing under economy profile and `0` under `full`. Set explicitly to enforce a specific rate.

#### `API_FOOTBALL_SKIP_INGEST_LOCK` (optional)

`1` / `true` / `yes` skips the BigQuery single-flight lock. Local debugging only; two overlapping jobs can corrupt merged payloads.

#### `API_FOOTBALL_INGEST_LEASE_MINUTES` (optional)

Lease duration for a successful lock holder. Default `180`. After a crash, another run can acquire the lock once `lease_until` has passed.

#### `API_FOOTBALL_SKIP_COMPLETENESS_CHECK` (optional)

`1` / `true` / `yes` skips the post-run fanout-vs-fixtures comparison and the `ingest_completeness_json` log line.

#### `API_FOOTBALL_FAIL_ON_INCOMPLETE` (optional)

`1` (default) makes the process exit `3` (HTTP `503` in Cloud Functions) when fanout coverage is incomplete. Set to `0` during a long multi-day backfill so partial-but-merged runs do not fail the scheduler before coverage catches up.

---

## Ingest lock

A single row in `RAW_APIF_INGEST_LOCK` (same dataset as raw loads) records `holder_run_id` and `lease_until`. The lock prevents two ingestion jobs from racing on the same raw tables: concurrent merges can read partial state and overwrite each other.

If a run reports "another ingestion holds the lease", either a legitimate job is still running, a prior run crashed before release, or the lease has not yet expired.

Wait until `lease_until` if another process is legitimate. If nothing is running and the lock is stale, clear it from the repo root with ADC authenticated to the same project:

```powershell
$env:PYTHONPATH = "."
python scripts\clear_apif_ingest_lock.py
```

`API_FOOTBALL_SKIP_INGEST_LOCK=1` disables the lock entirely. Local debugging only; never production.

---

## Monitoring a run

Three signals together tell you what happened.

1. **Fanout selection (start of per-fixture phase).** The log line `[api-football] fanout_selection league=D1 target=… already_complete=… missing_any_endpoint=…` reports the number of in-scope fixtures, how many are already covered in all five per-match tables, and how many still miss at least one endpoint.

2. **Completeness check (end of run).** The loader compares **finished** fixture ids in the merged `RAW_D1_APIF_FIXTURES_NEXT` payload (`status.short` in `FT`, `AET`, `PEN`) against fixture ids present in each batched per-match payload (`LINEUPS`, `FIXTURE_EVENTS`, `FIXTURE_STATISTICS`, `FIXTURE_PLAYERS`, `PREDICTIONS`) and emits `[api-football] ingest_completeness_json={...}`. Unplayed fixtures (upcoming, in-play, cancelled, postponed, abandoned) are reported separately as `fixture_unplayed_count` and do not fail the check, because the per-match tables can't legitimately cover them yet. The field `match_level_tables_cover_all_fixtures` (legacy `all_fanout_complete`) is the overall boolean. This is one slice of "complete" — squad freshness and the other raw tables are covered by source freshness, the ingestion spread model, and running dbt after ingest (see [`data_contract.md`](data_contract.md)).

   When `match_level_tables_cover_all_fixtures` is `false` during a multi-day backfill, the process exits `3` under the default `API_FOOTBALL_FAIL_ON_INCOMPLETE=1`. Set that env var to `0` until coverage catches up, or skip the check entirely with `API_FOOTBALL_SKIP_COMPLETENESS_CHECK=1` (not recommended long-term).

3. **Warehouse alignment.** The dbt model `int_apif__raw_ingestion_spread` summarises `MAX(ingested_at)` across raw D1 tables in one row, including `spread_minutes`. Build it with `dbt build --project-dir .\dbt_project --select int_apif__raw_ingestion_spread` to check alignment after deploys.

---

## Playbooks

### A) Fresh backfill

Land a wide merged snapshot (many seasons, full fanout over time) without fighting the scheduler on exit `3`.

1. Confirm `.env`: `API_FOOTBALL_API_KEY`, dataset id if non-default, and a profile that fits the daily quota (`full` for wide pulls, `default` for ~100 requests/day keys).
2. Set `API_FOOTBALL_FAIL_ON_INCOMPLETE=0` until fanout coverage catches up. Optionally cap `API_FOOTBALL_LINEUPS_MAX_FIXTURES` per day.
3. Use `API_FOOTBALL_FANOUT_PRIORITY=cursor` (and optionally `API_FOOTBALL_SKIP_PLAYERS=1` on cursor-only days) to walk the fixture list across runs.
4. Clear a stale lock (`scripts/clear_apif_ingest_lock.py`) if exit `2` appears with no job running.
5. Run `python -m ingestion.api_football.main` as often as quota allows until `ingest_completeness_json` reports `match_level_tables_cover_all_fixtures: true` for D1.
6. Return `API_FOOTBALL_FAIL_ON_INCOMPLETE` to `1` for normal operations.
7. Run `dbt build --project-dir .\dbt_project --selector staging` (and downstream where it applies) after ingest succeeds so staging matches raw.

Dropping or truncating raw tables in BigQuery is only required for a deliberate empty slate; day-to-day merges do not need it.

### B) Daily update

Refresh cheap league-wide tables daily and prioritise near-term matches for the expensive fanout.

1. Keep `API_FOOTBALL_FAIL_ON_INCOMPLETE=1` once backfill is complete so the scheduler alerts on regression.
2. Leave `API_FOOTBALL_FANOUT_PRIORITY=upcoming` so the next match window gets detail first.
3. Keep the ingest lock enabled so scheduled jobs never overlap.
4. Optionally run a second schedule with `FANOUT_PRIORITY=cursor` (and `SKIP_PLAYERS=1`) to keep advancing the long tail in smaller slices.

---

## Related documents

| Topic | Document |
|-------|----------|
| Raw tables, merge model, endpoint map | [`data_contract.md`](data_contract.md) |
| dbt layers and naming | `dbt_project/docs/layering.md` |
| Raw load-time spread (D1) | dbt model `int_apif__raw_ingestion_spread` |

---

## CI/CD guardrails

GitHub Actions workflows enforce the layer contract and run dbt:

- `.github/workflows/dbt-ci.yml`: PR/push validation (`check_layer_contract.py`, `sqlfluff lint`, `dbt parse`, `dbt build --selector staging`, focused transfer contract build `dbt build --select dim_date dim_player fct_transfer`).
- `.github/workflows/dbt-scheduled.yml`: twice-daily scheduled run (`04:00` and `16:00` UTC) with full DQ selector (`dbt build --selector dq`).
- `.github/workflows/pages-match-preview.yml`: builds `+mart_matchday_insights`, exports `matchday_insights.json` and `metric_glossary.json`, assembles `site/match-preview/` into `_site/`, and deploys to **GitHub Pages** (manual `workflow_dispatch`, daily schedule, or on push to `main` when relevant paths change).

### Shareable Bundesliga match preview (GitHub Pages)

1. In the GitHub repository, go to **Settings → Pages → Build and deployment**, set **Source** to **GitHub Actions** (not “Deploy from a branch”) the first time you enable Pages.
2. Run **Actions → Deploy match preview (GitHub Pages) → Run workflow** on `main`, or wait for the daily schedule after merging the workflow.
3. After a successful run, open **`https://<owner>.github.io/<repository>/match-preview/`** (project site). The repository root (`…/<repository>/`) redirects there; opening only `…/<repository>/` used to show **404** before that redirect existed. The workflow uses the same WIF secrets as other dbt workflows (`GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT`).

Local preview of the same HTML and JSON layout: run `scripts/export_matchday_insights.ps1`, then `.\scripts\build_match_preview_site.ps1` (Windows) or `bash scripts/build_match_preview_site.sh` (Linux/macOS), and serve the `_site` folder with a static file server (open `/match-preview/`).

Required repository secrets for Workload Identity Federation:

- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT`

Both workflows generate a temporary `/home/runner/.dbt/profiles.yml` for the
`football_data_pipeline` profile in CI to avoid relying on machine-local
profiles files.

Local equivalent hard-fail check:

```powershell
python .\scripts\check_layer_contract.py
```

### Simple operations playbook (lean baseline)

- **Where to check failed runs:** GitHub Actions tab -> `dbt-ci` / `dbt-scheduled` workflow runs.
- **What to do when marts are stale:** rerun `dbt-scheduled` via workflow_dispatch; if it still fails, inspect the failed dbt step first (`dbt deps`, contract check, then build).
- **Where WIF secrets live:** GitHub repo -> Settings -> Secrets and variables -> Actions (`GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT`).
