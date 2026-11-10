"""Report, and with --confirm drop, production BigQuery relations no dbt model or source owns."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

PROJECT = "football-data-pipeline-gcp"

# A node with no custom schema rides `target.schema`, which is `dbt_analytics` in the prod profile.
LAYER_DATASETS = ("staging", "core", "intermediate", "marts")
DEFAULT_DATASET = "dbt_analytics"
RAW_DATASET = "raw"

# The only datasets this script may read or write; every other dataset is unreachable.
ALLOWED_DATASETS = (*LAYER_DATASETS, DEFAULT_DATASET, RAW_DATASET)

# Operational tables in `raw` that no source declares and that must never be dropped.
RAW_OPERATIONAL = frozenset({
    "RAW_APIF_INGEST_LOCK",
    "RAW_APIF_INGEST_COMPLETENESS_SNAPSHOT",
})

# Below this many expected relations the manifest is untrustworthy (failed parse, partial
# `--select` run, wrong path) and every relation in the warehouse would look orphaned.
MANIFEST_FLOOR = 50

PHASES = ("broken", "live-views", "tables", "all")

_PHASE_ORDER = ("broken", "live-views", "tables")

_PHASE_LABELS = {
    "broken": "BROKEN views: every reference resolved and one is gone, so any query errors",
    "live-views": "views that STILL RETURN DATA: retired SQL still answering queries",
    "tables": "orphan TABLES: these hold bytes, unlike the views",
}

# `project.dataset.table`, backticks optional around each part; dbt always emits the three-part form.
_REF_RE = re.compile(
    r"`?" + re.escape(PROJECT) + r"`?\s*\.\s*`?([A-Za-z0-9_]+)`?\s*\.\s*`?([A-Za-z0-9_]+)`?"
)


class ManifestError(RuntimeError):
    """The manifest is missing, unreadable, or too small to be trusted."""


def load_expected(manifest_path: Path) -> set[tuple[str, str]]:
    """Return every (dataset, relation) a prod dbt build would create."""
    if not manifest_path.is_file():
        raise ManifestError(
            f"No manifest at {manifest_path}. Run `dbt deps && dbt parse` in dbt_project/ first: "
            "without it this script cannot tell a live model from an orphan."
        )
    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"Could not read {manifest_path}: {exc}") from exc

    expected: set[tuple[str, str]] = set()
    for node in (manifest.get("nodes") or {}).values():
        resource_type = node.get("resource_type")
        if resource_type not in ("model", "seed", "snapshot"):
            continue
        config = node.get("config") or {}
        if config.get("materialized") == "ephemeral":
            continue
        # A snapshot names its dataset with `target_schema`, which dbt applies verbatim.
        custom = (
            config.get("target_schema") if resource_type == "snapshot" else config.get("schema")
        )
        dataset = custom.strip() if isinstance(custom, str) and custom.strip() else DEFAULT_DATASET
        expected.add((dataset, node.get("alias") or node["name"]))

    for source in (manifest.get("sources") or {}).values():
        identifier = source.get("identifier") or source.get("name")
        if identifier:
            expected.add((RAW_DATASET, identifier))

    if len(expected) < MANIFEST_FLOOR:
        raise ManifestError(
            f"Manifest yielded only {len(expected)} expected relations, below the floor of "
            f"{MANIFEST_FLOOR}. Refusing to run: treating this as the truth would mark almost "
            "every relation in production an orphan. Re-parse the manifest and try again."
        )
    return expected


def list_warehouse(client: bigquery.Client) -> dict[tuple[str, str], str]:
    """Map (dataset, relation) -> 'TABLE' | 'VIEW' | ... across the allowed datasets only."""
    found: dict[tuple[str, str], str] = {}
    for dataset in ALLOWED_DATASETS:
        for item in client.list_tables(f"{PROJECT}.{dataset}"):
            found[(dataset, item.table_id)] = item.table_type
    return found


def list_routines(client: bigquery.Client) -> set[tuple[str, str]]:
    """Every routine (UDF, procedure, table function) in the allowed datasets.

    Kept out of the warehouse map so `find_orphans()` can never select a routine for deletion.
    """
    found: set[tuple[str, str]] = set()
    for dataset in ALLOWED_DATASETS:
        for routine in client.list_routines(f"{PROJECT}.{dataset}"):
            found.add((dataset, routine.routine_id))
    return found


def find_orphans(
    warehouse: dict[tuple[str, str], str],
    expected: set[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Every relation present in the warehouse that no manifest node or source owns."""
    orphans = []
    for key in warehouse:
        dataset, name = key
        if key in expected:
            continue
        if name.endswith("__dbt_tmp"):
            continue
        if dataset == RAW_DATASET and name in RAW_OPERATIONAL:
            continue
        orphans.append(key)
    return sorted(orphans)


def view_queries(
    client: bigquery.Client,
    keys: list[tuple[str, str]],
    warehouse: dict[tuple[str, str], str],
) -> dict[tuple[str, str], str]:
    """Fetch the stored SQL of every view reachable from `keys`. Metadata reads only, so free."""
    queries: dict[tuple[str, str], str] = {}
    pending = list(keys)
    while pending:
        key = pending.pop()
        if key in queries or warehouse.get(key) != "VIEW":
            continue
        table = client.get_table(f"{PROJECT}.{key[0]}.{key[1]}")
        sql = table.view_query or ""
        queries[key] = sql
        # An unfetched upstream view would be assumed live and mis-phase its parent.
        for ref in _refs_in(sql, key):
            if ref[0] in ALLOWED_DATASETS and ref not in queries:
                pending.append(ref)
    return queries


def _refs_in(sql: str, key: tuple[str, str]) -> set[tuple[str, str]]:
    """The (dataset, relation) pairs a view body references, excluding itself."""
    return {(m.group(1), m.group(2)) for m in _REF_RE.finditer(sql)} - {key}


def resolves(
    key: tuple[str, str],
    warehouse: dict[tuple[str, str], str],
    queries: dict[tuple[str, str], str],
    routines: set[tuple[str, str]] | None = None,
    _stack: frozenset[tuple[str, str]] = frozenset(),
) -> bool:
    """True if querying this relation would succeed, following views transitively.

    Anything unprovable resolves to True, because calling a live view broken offers it for deletion.
    A reference naming a routine is not a relation, so pass `routines` to recognise it.
    """
    routines = routines if routines is not None else set()
    if key in routines:
        return True
    if key not in warehouse:
        return False
    if warehouse[key] != "VIEW":
        return True
    if key in _stack:
        return True
    sql = queries.get(key)
    if sql is None:
        return True
    for ref in _refs_in(sql, key):
        if ref[0] not in ALLOWED_DATASETS:
            continue
        if not resolves(ref, warehouse, queries, routines, _stack | {key}):
            return False
    return True


def classify(
    orphans: list[tuple[str, str]],
    warehouse: dict[tuple[str, str], str],
    queries: dict[tuple[str, str], str],
    routines: set[tuple[str, str]] | None = None,
) -> dict[str, list[tuple[str, str]]]:
    """Split the orphans into the three phases: disjoint, and together the whole set."""
    phases: dict[str, list[tuple[str, str]]] = {p: [] for p in _PHASE_ORDER}
    for key in orphans:
        if warehouse.get(key) != "VIEW":
            phases["tables"].append(key)
        elif resolves(key, warehouse, queries, routines):
            phases["live-views"].append(key)
        else:
            phases["broken"].append(key)
    return phases


def select(phases: dict[str, list[tuple[str, str]]], phase: str) -> list[tuple[str, str]]:
    """The relations a phase name selects. 'all' is every phase, in phase order."""
    if phase == "all":
        return [key for name in _PHASE_ORDER for key in phases[name]]
    return list(phases[phase])


def _report(phases: dict[str, list[tuple[str, str]]], phase: str) -> None:
    """Print every phase, marking the selected one. The report never depends on --confirm."""
    for name in _PHASE_ORDER:
        items = phases[name]
        mark = "->" if phase in (name, "all") else "  "
        print(f"\n{mark} {name}: {len(items)} - {_PHASE_LABELS[name]}")
        for dataset, relation in items:
            print(f"      {dataset}.{relation}")


def _drop(client: bigquery.Client, chosen: list[tuple[str, str]]) -> int:
    """Drop the selected relations. Returns a process exit code."""
    print(f"\nDropping {len(chosen)} relation(s) ...")
    errors: list[str] = []
    for dataset, relation in chosen:
        full_id = f"{PROJECT}.{dataset}.{relation}"
        try:
            client.delete_table(full_id)
            print(f"  dropped {dataset}.{relation}")
        except NotFound:
            print(f"  SKIP {dataset}.{relation} (already gone)")
        except Exception as e:
            errors.append(f"{dataset}.{relation}: {e}")
            print(f"  FAIL {dataset}.{relation}: {e}", file=sys.stderr)

    if errors:
        print(f"\n{len(errors)} error(s):", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1
    print(f"\nDropped {len(chosen)} relation(s).")
    return 0


def main(
    phase: str,
    confirm: bool,
    manifest_path: Path,
    client: bigquery.Client | None = None,
) -> int:
    try:
        expected = load_expected(manifest_path)
    except ManifestError as exc:
        print(f"ABORT: {exc}", file=sys.stderr)
        return 2

    print(f"Manifest expects {len(expected)} relation(s) across {', '.join(ALLOWED_DATASETS)}.")

    client = client if client is not None else bigquery.Client(project=PROJECT)
    warehouse = list_warehouse(client)
    print(f"Warehouse holds {len(warehouse)} relation(s) in those datasets.")

    missing = sorted(expected - set(warehouse))
    if missing:
        # The manifest may be ahead of the warehouse because the last build did not finish.
        print(f"\nWARNING: {len(missing)} expected relation(s) are NOT in the warehouse:")
        for dataset, relation in missing:
            print(f"      {dataset}.{relation}")

    orphans = find_orphans(warehouse, expected)
    if not orphans:
        print("\nNo orphaned relations. Nothing to do.")
        return 0

    routines = list_routines(client)
    phases = classify(orphans, warehouse, view_queries(client, orphans, warehouse), routines)
    _report(phases, phase)
    chosen = select(phases, phase)
    print(f"\n{len(orphans)} orphan relation(s) total; phase '{phase}' selects {len(chosen)}.")

    if not chosen:
        print("Nothing selected for this phase.")
        return 0
    if not confirm:
        print(f"\nDRY RUN: nothing was changed. Pass --confirm to drop these {len(chosen)}.")
        return 0
    return _drop(client, chosen)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Report, and with --confirm drop, BigQuery relations no dbt model owns.",
    )
    parser.add_argument(
        "--phase",
        choices=PHASES,
        default="all",
        help=(
            "Which orphans to select. 'broken' is the low-risk set: every reference in the view "
            "was resolved and at least one no longer exists, so any query against it errors. "
            "Default 'all'. The choice only matters with --confirm; the report always shows "
            "every phase."
        ),
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually drop the selected relations. Without this flag nothing is changed.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).parent.parent / "dbt_project" / "target" / "manifest.json",
        help="Path to dbt's manifest.json (default: dbt_project/target/manifest.json).",
    )
    args = parser.parse_args()
    sys.exit(main(phase=args.phase, confirm=args.confirm, manifest_path=args.manifest))
