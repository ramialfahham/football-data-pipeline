"""One-time re-shape of RAW_APIF_PLAYERS to the one-row-per-(team, season) grain.

Background
----------
RAW_APIF_PLAYERS historically stored one bloated row per league (``response`` = every
team×season), which for large-roster deep leagues (LIBER/UEL/UCL) exceeds BigQuery's
100 MB per-row JSON limit and fails to load. The loader now writes one small row per
(team, season) (loads/squads.py, append-only since 2026-08-17). This script migrates the EXISTING data
to that grain so staging can read it faithfully (current-per-entity is assembled in base).

What it does
------------
For each league it takes the LATEST bloated snapshot, explodes its ``response`` array into
one row per (team, season) (payload reshaped to ``{league_code, response:[entry]}``, the
exact shape the loader now writes), then deletes every pre-migration row. Net effect:
identical player-team-season data, re-shaped into small rows. No API calls.

Safety
------
- Dry-run by default; ``--execute`` required for writes.
- Idempotency guard: if there are no bloated rows left (``response`` length > 1), the
  migration has already run (or there is nothing to migrate) and the script is a no-op.
- The re-shaped rows are inserted at one migration timestamp; the INSERT is verified BEFORE
  any delete by a SET-IDENTITY check (EXCEPT in both directions) — not a mere count — so a
  dropped or substituted player cannot pass. On any mismatch it ABORTS without deleting.
- Raw data is re-derivable from the API and BigQuery time travel is a further net.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from google.cloud import bigquery  # noqa: E402

from ingestion.api_football.settings import GCP_PROJECT_ID, DATASET_ID  # noqa: E402

TABLE = f"{GCP_PROJECT_ID}.{DATASET_ID}.RAW_APIF_PLAYERS"

# Idempotency guard: rows still in the bloated (>1 entry) grain, older than the migration ts.
_BLOATED = """
select count(*) as n from `{t}`
where ingested_at < @ts
  and array_length(json_query_array(json_query(payload, '$.response'), '$')) > 1
"""

_ROWS_NOW = "select count(*) as n from `{t}` where ingested_at < @ts"

_PRE_KEY_COUNT = """
with latest as (
  select league_code, payload from `{t}`
  where ingested_at < @ts
  qualify row_number() over (partition by league_code order by ingested_at desc) = 1
)
select count(*) as n from (
  select distinct league_code,
    safe_cast(json_value(pe, '$.player.id') as int64) as pid,
    safe_cast(json_value(tb, '$.team_id') as int64) as tid,
    safe_cast(json_value(tb, '$.season') as int64) as ssn
  from latest,
    unnest(json_query_array(json_query(payload, '$.response'), '$')) as tb,
    unnest(json_query_array(json_query(tb, '$.players_payload'), '$')) as pe
)
"""

_ROWS_TO_INSERT = """
select count(*) as n from (
  select 1 from (
    select league_code, payload from `{t}`
    where ingested_at < @ts
    qualify row_number() over (partition by league_code order by ingested_at desc) = 1
  ) latest,
    unnest(json_query_array(json_query(latest.payload, '$.response'), '$')) as entry
)
"""

_INSERT = """
insert into `{t}` (league_code, payload, ingested_at)
select latest.league_code,
       json_object('league_code', latest.league_code, 'response', json_array(entry)),
       @ts
from (
  select league_code, payload from `{t}`
  where ingested_at < @ts
  qualify row_number() over (partition by league_code order by ingested_at desc) = 1
) latest,
  unnest(json_query_array(json_query(latest.payload, '$.response'), '$')) as entry
"""

# SET-IDENTITY check: the pre-migration key set (rows < @ts, latest snapshot per league) must
# EQUAL the re-shaped key set (rows = @ts), in BOTH directions. Returns the two diff counts.
_KEY_DIFF = """
with pre as (
  select distinct league_code,
    safe_cast(json_value(pe, '$.player.id') as int64) as pid,
    safe_cast(json_value(tb, '$.team_id') as int64) as tid,
    safe_cast(json_value(tb, '$.season') as int64) as ssn
  from (
    select league_code, payload from `{t}`
    where ingested_at < @ts
    qualify row_number() over (partition by league_code order by ingested_at desc) = 1
  ) latest,
    unnest(json_query_array(json_query(latest.payload, '$.response'), '$')) as tb,
    unnest(json_query_array(json_query(tb, '$.players_payload'), '$')) as pe
),
post as (
  select distinct league_code,
    safe_cast(json_value(pe, '$.player.id') as int64) as pid,
    safe_cast(json_value(tb, '$.team_id') as int64) as tid,
    safe_cast(json_value(tb, '$.season') as int64) as ssn
  from `{t}`,
    unnest(json_query_array(json_query(payload, '$.response'), '$')) as tb,
    unnest(json_query_array(json_query(tb, '$.players_payload'), '$')) as pe
  where ingested_at = @ts
)
select
  (select count(*) from (select * from pre except distinct select * from post)) as pre_not_post,
  (select count(*) from (select * from post except distinct select * from pre)) as post_not_pre
"""

_DELETE = "delete from `{t}` where ingested_at < @ts"


def _job_config(ts: datetime) -> bigquery.QueryJobConfig:
    return bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("ts", "TIMESTAMP", ts)]
    )


def _scalar(client: bigquery.Client, sql: str, ts: datetime) -> int:
    return int(list(client.query(sql.format(t=TABLE), job_config=_job_config(ts)).result())[0]["n"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--execute", action="store_true", help="perform the INSERT + DELETE (default: dry-run)")
    args = ap.parse_args()

    client = bigquery.Client(project=GCP_PROJECT_ID)
    ts = datetime.now(timezone.utc)

    bloated = _scalar(client, _BLOATED, ts)
    if bloated == 0:
        print(f"Table: {TABLE}")
        print("No bloated rows to migrate (already re-shaped, or empty). Nothing to do.")
        return 0

    rows_now = _scalar(client, _ROWS_NOW, ts)
    pre_keys = _scalar(client, _PRE_KEY_COUNT, ts)
    rows_to_insert = _scalar(client, _ROWS_TO_INSERT, ts)

    print(f"Table: {TABLE}")
    print(f"Migration timestamp: {ts.isoformat()}")
    print(f"Bloated (>1-entry) rows present: {bloated:,}")
    print(f"Pre-migration rows (deleted after re-shape): {rows_now:,}")
    print(f"Rows to insert (one per team x season): {rows_to_insert:,}")
    print(f"Distinct (league, player, team, season) to preserve: {pre_keys:,}")

    if not args.execute:
        print("\nDRY-RUN — nothing written. Re-run with --execute to apply.")
        return 0

    print("\nExecuting INSERT (re-shaped rows)...")
    client.query(_INSERT.format(t=TABLE), job_config=_job_config(ts)).result()

    diff = list(client.query(_KEY_DIFF.format(t=TABLE), job_config=_job_config(ts)).result())[0]
    pre_not_post, post_not_pre = int(diff["pre_not_post"]), int(diff["post_not_pre"])
    if pre_not_post or post_not_pre:
        raise SystemExit(
            f"ABORT (no delete): key-set mismatch — pre_not_post={pre_not_post}, "
            f"post_not_pre={post_not_pre}. No pre-migration rows were deleted; the "
            "migration-timestamp rows can be removed manually."
        )
    print("Verified: re-shaped key set is identical to pre-migration (EXCEPT both ways = 0). Deleting...")

    del_job = client.query(_DELETE.format(t=TABLE), job_config=_job_config(ts))
    del_job.result()
    print(f"Deleted pre-migration rows (dml_affected_rows={del_job.num_dml_affected_rows}). Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
