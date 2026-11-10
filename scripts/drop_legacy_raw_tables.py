"""Drop legacy per-competition raw tables, keeping INGEST_CURSOR; dry-run unless --confirm."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

PROJECT = "football-data-pipeline-gcp"
DATASET = "raw"

_EXCLUDED_SUFFIXES = frozenset({"INGEST_CURSOR"})


def _load_league_codes() -> set[str]:
    registry_path = Path(__file__).parent.parent / "docs" / "competition_registry.yml"
    with open(registry_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    codes: set[str] = set()
    for comp in data.get("competitions") or []:
        lc = comp.get("league_code")
        if lc:
            codes.add(str(lc).strip())
    return codes


def _is_legacy_table(table_name: str, league_codes: set[str]) -> bool:
    """A legacy name is RAW_APIF_{LC}_{entity} with {LC} a registry league code."""
    prefix = "RAW_APIF_"
    if not table_name.startswith(prefix):
        return False
    remainder = table_name[len(prefix):]
    # Longest code first so WCQEU is not matched as WC.
    for lc in sorted(league_codes, key=len, reverse=True):
        if remainder.startswith(lc + "_"):
            entity = remainder[len(lc) + 1:]
            if entity in _EXCLUDED_SUFFIXES:
                return False
            return True
    return False


def _discover_legacy_tables(
    client: bigquery.Client,
    league_codes: set[str],
) -> list[str]:
    dataset_ref = f"{PROJECT}.{DATASET}"
    tables = client.list_tables(dataset_ref)
    legacy: list[str] = []
    for t in tables:
        if _is_legacy_table(t.table_id, league_codes):
            legacy.append(t.table_id)
    return sorted(legacy)


def main(confirm: bool) -> None:
    client = bigquery.Client(project=PROJECT)

    league_codes = _load_league_codes()
    print(f"Loaded {len(league_codes)} league codes from registry: {sorted(league_codes)}")

    legacy_tables = _discover_legacy_tables(client, league_codes)
    if not legacy_tables:
        print("\nNo legacy per-competition raw tables found. Nothing to drop.")
        return

    print(f"\nFound {len(legacy_tables)} legacy table(s):")
    for t in legacy_tables:
        print(f"  {t}")

    if not confirm:
        print(
            f"\nDRY RUN — pass --confirm to actually drop these {len(legacy_tables)} table(s)."
        )
        return

    print(f"\nDropping {len(legacy_tables)} table(s) …")
    dropped = 0
    errors: list[str] = []
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    for table_id in legacy_tables:
        full_id = f"{PROJECT}.{DATASET}.{table_id}"
        try:
            client.delete_table(full_id)
            print(f"  [{ts}] dropped {table_id}")
            dropped += 1
        except NotFound:
            print(f"  [{ts}] SKIP {table_id} (already gone)")
            dropped += 1
        except Exception as e:
            errors.append(f"{table_id}: {e}")
            print(f"  [{ts}] FAIL {table_id}: {e}", file=sys.stderr)

    print(f"\nDropped {dropped} table(s).")
    if errors:
        print(f"{len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Drop legacy per-competition RAW_APIF_{LC}_{entity} BigQuery tables."
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually drop tables. Without this flag the script runs in dry-run mode.",
    )
    args = parser.parse_args()
    main(confirm=args.confirm)
