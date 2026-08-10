"""Out-of-band raw-data staleness sentinel. GitLab #39 Stage 2.

WHY THIS EXISTS
---------------
Every check that lives inside the nightly only runs when the nightly runs. The failure that
cost six days of stale data (2026-08-03 to 08-09) was the nightly NOT RUNNING AT ALL — a cron
silently dropped by a platform migration. Nothing inside the pipeline can see that.

This runs on its own schedule and measures the thing the product actually cares about: HOW OLD
IS THE DATA. It does not care whether the nightly ran, succeeded, or exists. A pipeline that
"succeeds" every night while writing nothing is stale, and this catches that too — job success
is a proxy, data age is the real signal.

WHY NOT AN ALERT ON THE JOB ITSELF
----------------------------------
That was the first design and the CPO rejected it. Cloud Monitoring caps `conditionAbsent` at
23h30m and MQL `absent_for` at 1d1h, and for a DAILY job every value at or below 24h fires
before each run — so the only usable number was 25h, a ceiling rather than a choice. Running
THIS hourly dissolves that: absence detection on an hourly job needs a 3h window, far inside
the cap, and the staleness threshold itself is ours to set.

COST: ZERO. `client.get_table()` is a metadata call, not a query — no bytes scanned, no query
job, nothing billed. That is why this can run hourly without thinking about it.

THRESHOLDS ARE NOT DEFINED HERE. They are read from
`dbt_project/models/1_staging/api_football/sources.yml`, which already declares
`freshness.error_after` per source and is what `dbt source freshness` uses. A second copy would
drift, and the drifted one would be the one nobody noticed.

EXIT CODES
  0  every source with a declared threshold is within it (warnings are logged, not fatal)
  1  at least one source is past `error_after` — Cloud Run marks the execution FAILED, which
     is what the alert policy fires on
  2  the check could not run (unreadable config, BigQuery unreachable). Deliberately NOT 0:
     a sentinel that cannot check must never look healthy.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
SOURCES_YML = REPO / "dbt_project" / "models" / "1_staging" / "api_football" / "sources.yml"

_PERIOD_TO_HOURS = {"minute": 1 / 60, "hour": 1, "day": 24}


def _to_hours(spec: dict) -> float | None:
    """`{count: 54, period: hour}` -> 54.0. None when the spec is absent or unusable."""
    if not isinstance(spec, dict):
        return None
    count, period = spec.get("count"), spec.get("period")
    if count is None or period not in _PERIOD_TO_HOURS:
        return None
    return float(count) * _PERIOD_TO_HOURS[period]


def load_thresholds(path: Path | None = None) -> dict[str, dict[str, float]]:
    """Read per-table freshness thresholds from the dbt sources file.

    `path` resolves to the module-level SOURCES_YML at CALL time, not as a default argument.
    A default is bound once at import, so `SOURCES_YML` could be pointed elsewhere and this
    would keep reading the original file — which made the "cannot read its thresholds" test
    pass against production data instead of the missing file it meant to simulate. A test that
    silently exercises the wrong thing is the failure mode this whole file is about.

    Only tables carrying a `freshness:` block are returned. All 11 sources declare
    `loaded_at_field`, but 3 deliberately have no thresholds — they refresh rarely and any
    threshold would false-alarm. Those must NOT be checked here either; inventing a threshold
    for them is how a sentinel starts crying wolf and gets muted.
    """
    doc = yaml.safe_load((path or SOURCES_YML).read_text(encoding="utf-8"))
    out: dict[str, dict[str, float]] = {}
    for source in doc.get("sources") or []:
        for table in source.get("tables") or []:
            fresh = table.get("freshness")
            if not fresh:
                continue
            error_h = _to_hours(fresh.get("error_after") or {})
            if error_h is None:
                continue
            entry = {"error_after_hours": error_h}
            warn_h = _to_hours(fresh.get("warn_after") or {})
            if warn_h is not None:
                entry["warn_after_hours"] = warn_h
            # `identifier` wins when present: the dbt source NAME is lowercase by convention
            # while the physical table is upper-case, and it is the physical name BigQuery
            # needs. Falling back to the name silently would look up a table that does not
            # exist, which surfaces as "cannot check" rather than a false pass.
            out[table.get("identifier") or table["name"]] = entry
    return out


def table_age_hours(client, project: str, dataset: str, table: str, now: datetime) -> float:
    """Hours since the table was last written, from its METADATA. No query, no cost."""
    meta = client.get_table(f"{project}.{dataset}.{table}")
    return (now - meta.modified).total_seconds() / 3600.0


def evaluate(ages: dict[str, float], thresholds: dict[str, dict[str, float]]) -> tuple[list, list]:
    """Pure split into (stale, warning). Separated from I/O so it is testable without BigQuery."""
    stale, warning = [], []
    for table, limits in sorted(thresholds.items()):
        age = ages.get(table)
        if age is None:
            continue
        if age > limits["error_after_hours"]:
            stale.append((table, age, limits["error_after_hours"]))
        elif "warn_after_hours" in limits and age > limits["warn_after_hours"]:
            warning.append((table, age, limits["warn_after_hours"]))
    return stale, warning


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default="football-data-pipeline-gcp")
    parser.add_argument("--dataset", default="raw")
    args = parser.parse_args(argv)

    try:
        thresholds = load_thresholds()
    except Exception as e:  # noqa: BLE001 - any failure here means we cannot check at all
        print(f"[freshness] EXIT 2 — CANNOT CHECK: unreadable thresholds: {e}", file=sys.stderr)
        return 2
    if not thresholds:
        print("[freshness] EXIT 2 — CANNOT CHECK: no source declares an error_after threshold.", file=sys.stderr)
        return 2

    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=args.project)
    except Exception as e:  # noqa: BLE001
        print(f"[freshness] EXIT 2 — CANNOT CHECK: BigQuery client unavailable: {e}", file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc)
    ages: dict[str, float] = {}
    unreadable: list[str] = []
    for table in sorted(thresholds):
        try:
            ages[table] = table_age_hours(client, args.project, args.dataset, table, now)
        except Exception as e:  # noqa: BLE001
            unreadable.append(f"{table}: {e}")

    if unreadable:
        # A table we cannot read is not a table we can call fresh.
        for u in unreadable:
            print(f"[freshness] EXIT 2 — CANNOT CHECK {u}", file=sys.stderr)
        return 2

    stale, warning = evaluate(ages, thresholds)

    for table in sorted(ages):
        print(f"[freshness] {table:<38} age={ages[table]:6.1f}h "
              f"error_after={thresholds[table]['error_after_hours']:.0f}h")

    for table, age, limit in warning:
        print(f"[freshness] WARN  {table} is {age:.1f}h old (warn_after {limit:.0f}h)")

    if stale:
        for table, age, limit in stale:
            print(f"[freshness] STALE {table} is {age:.1f}h old (error_after {limit:.0f}h)",
                  file=sys.stderr)
        # "EXIT 1" spelled out because the alert policy CANNOT tell exit 1 from exit 2 —
        # Cloud Run's execution metric carries only succeeded/failed, not the exit code. The
        # runbook tells the on-call engineer to read this line to find out which, so it has to
        # actually say it.
        print(f"[freshness] EXIT 1 — STALE: {len(stale)} source(s) past error_after. The data "
              "the product serves is out of date.", file=sys.stderr)
        return 1

    print(f"[freshness] OK — {len(ages)} source(s) within threshold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
