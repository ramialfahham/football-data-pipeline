"""Report what BigQuery actually cost, and what caused it (#547).

WHY THIS EXISTS
---------------
Cost is a CTO threshold that every task contract must declare, and until now the declaration was a
guess. There was no way to answer "what does this cost" short of hand-writing an INFORMATION_SCHEMA
query, so "RECURRING COST: none" got written from intuition and nobody could challenge it. Twice in
one day that declaration was made on changes that did add cost.

It is also how the May 2026 regression should have been caught. A cost optimisation was signed off
on the 25th and undone by an unrelated refactor on the 27th; the only signal was the monthly bill,
because nothing in the repo reported bytes. Run this and the jump is obvious in one line.

READ-ONLY. It queries INFORMATION_SCHEMA metadata only, which BigQuery does not bill for, so running
it costs nothing.

USAGE
    python scripts/report_bq_cost.py                 # last 35 days
    python scripts/report_bq_cost.py --days 7
    python scripts/report_bq_cost.py --days 90 --top 25

Requires the same credentials as the rest of the pipeline (`gcloud auth application-default login`,
or a service-account key via GOOGLE_APPLICATION_CREDENTIALS).
"""

from __future__ import annotations

import argparse
import sys

GCP_PROJECT = "football-data-pipeline-gcp"
REGION = "region-eu"

# On-demand analysis price per TiB, EU multi-region, USD. A constant here rather than an API lookup
# because the point is orders of magnitude, not invoicing: if this drifts, the RANKING is unchanged.
USD_PER_TIB = 6.25

_MONTHLY = """
select format_date('%Y-%m', date(creation_time)) as period,
       count(*) as jobs,
       round(sum(total_bytes_billed) / pow(2, 40), 3) as tib,
       round(sum(total_bytes_billed) / pow(2, 40) * {price}, 2) as usd
from `{region}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
where creation_time >= timestamp_sub(current_timestamp(), interval {days} day)
  and job_type = 'QUERY'
group by period order by period
"""

_BY_WORKLOAD = """
select case
         when strpos(query, '"target_name": "prod"') > 0 then 'dbt (prod build + tests)'
         when strpos(query, '"app": "dbt"') > 0 then 'dbt (CI target)'
         when strpos(query, 'raw.RAW_APIF') > 0 then 'raw payload reads (python ingestion)'
         else 'other'
       end as workload,
       count(*) as jobs,
       round(sum(total_bytes_billed) / pow(2, 40) * {price}, 2) as usd
from `{region}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
where creation_time >= timestamp_sub(current_timestamp(), interval {days} day)
  and job_type = 'QUERY'
group by workload order by usd desc
"""

# dbt stamps a JSON comment on every query it issues, so spend attributes to a model or test by name.
_BY_NODE = """
select regexp_extract(query, r'"node_id": "([^"]+)"') as node,
       count(*) as jobs,
       round(sum(total_bytes_billed) / pow(2, 40) * {price}, 2) as usd
from `{region}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
where creation_time >= timestamp_sub(current_timestamp(), interval {days} day)
  and job_type = 'QUERY'
  and strpos(query, '"target_name": "prod"') > 0
group by node having node is not null order by usd desc limit {top}
"""

# Tests vs models is the ratio that exposed #547: tests cost 4x what building the models cost,
# because staging and base were both views so every test re-executed the chain down to raw.
_TESTS_VS_MODELS = """
select case
         when starts_with(node, 'test.') then 'tests'
         when starts_with(node, 'model.') then 'models'
         else 'other'
       end as kind,
       count(*) as jobs,
       round(sum(bytes) / pow(2, 40) * {price}, 2) as usd
from (
  select regexp_extract(query, r'"node_id": "([^"]+)"') as node,
         total_bytes_billed as bytes
  from `{region}`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
  where creation_time >= timestamp_sub(current_timestamp(), interval {days} day)
    and job_type = 'QUERY'
    and strpos(query, '"target_name": "prod"') > 0
)
group by kind order by usd desc
"""


def _run(client, sql: str) -> list:
    return list(client.query(sql).result())


def _table(title: str, rows: list, note: str = "") -> None:
    print(f"\n{title}")
    print("-" * len(title))
    if not rows:
        print("  (no rows)")
        return
    fields = list(rows[0].keys())
    widths = [max(len(f), max(len(str(r[f])) for r in rows)) for f in fields]
    print("  " + "  ".join(f.ljust(w) for f, w in zip(fields, widths)))
    for r in rows:
        print("  " + "  ".join(str(r[f]).ljust(w) for f, w in zip(fields, widths)))
    if note:
        print(f"  {note}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=35, help="lookback window (default 35)")
    ap.add_argument("--top", type=int, default=15, help="how many nodes to list (default 15)")
    args = ap.parse_args()

    try:
        from google.cloud import bigquery
    except ImportError:
        print("google-cloud-bigquery is not installed. pip install -r requirements.txt")
        return 1

    client = bigquery.Client(project=GCP_PROJECT)
    fmt = {"region": REGION, "days": args.days, "top": args.top, "price": USD_PER_TIB}

    print(f"BigQuery query spend, last {args.days} days, project {GCP_PROJECT}")
    print(f"Estimated at ${USD_PER_TIB}/TiB on-demand. Storage is NOT included.")

    _table("By month", _run(client, _MONTHLY.format(**fmt)))
    _table("By workload", _run(client, _BY_WORKLOAD.format(**fmt)))
    _table(
        "Prod build: tests vs models",
        _run(client, _TESTS_VS_MODELS.format(**fmt)),
        note="If tests cost more than models, something upstream is a view being re-scanned per test.",
    )
    _table(f"Top {args.top} prod nodes", _run(client, _BY_NODE.format(**fmt)))

    print("\nTo declare RECURRING COST in a task contract, quote a figure from here rather than")
    print("writing 'none' from intuition. See dbt_project/docs/layering.md for the #547 example.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
