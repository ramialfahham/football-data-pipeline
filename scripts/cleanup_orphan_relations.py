"""Report, and optionally drop, production BigQuery relations that no dbt model owns (#84).

WHY THIS EXISTS
---------------
`check_layer_contract.py` blocks the per-competition pattern in the REPO. Nothing reconciles the
WAREHOUSE. So when `6e4ba18` (2026-05-27) replaced the per-competition staging and base models with
generic unified ones, the models left the repo and 310 relations stayed behind in production,
unnoticed for three months. 244 of them sat in `staging` alone, against 15 real staging models.

Most are inert: they read raw tables that no longer exist, so any query against them errors. The
dangerous ones are the minority that still resolve. Those answer queries with plausible numbers,
computed by SQL that left the repo and is neither tested nor rebuilt, which is how someone walks
away with a confident wrong answer.

THE AUTHORITY IS THE MANIFEST, NOT A LIST OF NAMES
--------------------------------------------------
Every run recomputes what is expected from `dbt_project/target/manifest.json` and compares it with
what BigQuery actually holds. Nothing here hardcodes a table name, so this does not rot the way a
captured list of today's 310 would: run it next year and it reports whatever is orphaned then. That
also makes it usable as a standing reconciliation check, not only as a one-off cleanup.

Expected relations come from two places, because two different things declare them:
  - dbt models and seeds, keyed on `config.schema`, the raw custom schema from dbt_project.yml.
    Deliberately NOT `node['schema']`, which has already been through `generate_schema_name.sql`
    and so reads `dev_staging` under a dev target and `staging` under prod. Keying on the resolved
    name would make the answer depend on who last parsed.
  - dbt snapshots, keyed on `config.target_schema`. Snapshots use a different config key, and dbt
    applies it verbatim without passing it through `generate_schema_name.sql` - dbt_project.yml
    says exactly that above its `snapshots:` block. Reading `config.schema` for a snapshot returns
    None and would file every snapshot under DEFAULT_DATASET, putting a name in that dataset's
    expected set that will never be built there. No snapshots exist today and `snapshots` is not in
    ALLOWED_DATASETS, so the mapping is inert right now, but it has to be right before the first
    one lands: a snapshot is an SCD2 history table, and history cannot be rebuilt.
  - dbt sources, which declare the `raw` dataset by explicit `identifier`.

READ-ONLY BY DEFAULT. Without `--confirm` nothing is dropped. Reporting uses the BigQuery metadata
API only (`list_tables`, `get_table`), which is not billed, and issues no query, so it scans no
bytes and costs nothing to run.

SAFETY
------
  - Dry-run unless `--confirm` is passed.
  - A relation that any manifest node or source owns is never selectable.
  - The manifest sanity floor aborts the run rather than treating an unreadable or half-parsed
    manifest as "everything is orphaned". That is the one bug here that could drop the warehouse.
  - Only the datasets in ALLOWED_DATASETS are ever read or written. `raw_archive` (a deliberate
    archive), `dbt_scratch`, and every `ci_*`/`dev_*` dataset are out of reach by construction.
  - `__dbt_tmp` relations are skipped: they are transient artifacts of an incremental merge and
    carry a dbt-set 12-hour expiration.
  - BigQuery time travel can restore a dropped TABLE for 7 days. A dropped VIEW is not recoverable
    that way, but a view is pure definition and `git show 6e4ba18^` still has the SQL.

USAGE
    python scripts/cleanup_orphan_relations.py                        # report everything
    python scripts/cleanup_orphan_relations.py --phase broken         # report, phase 1 selected
    python scripts/cleanup_orphan_relations.py --phase broken --confirm
    python scripts/cleanup_orphan_relations.py --phase all --confirm

Requires the same credentials as the rest of the pipeline (`gcloud auth application-default
login`, or a service-account key via GOOGLE_APPLICATION_CREDENTIALS).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

PROJECT = "football-data-pipeline-gcp"

# dbt's `config.schema` -> the dataset a `prod` build writes to. A node with no custom schema rides
# `target.schema`, and prod's profile `dataset:` is `dbt_analytics` (the base models and the seeds).
# See macros/generate_schema_name.sql.
LAYER_DATASETS = ("staging", "core", "intermediate", "marts")
DEFAULT_DATASET = "dbt_analytics"
RAW_DATASET = "raw"

# The only datasets this script may read or write. Everything else is unreachable by construction:
# `raw_archive` is a deliberate archive, `dbt_scratch`/`dev_*`/`ci_*` are not production, and
# `snapshots` holds nothing. Widening this list is a separate, separately reviewed decision.
ALLOWED_DATASETS = (*LAYER_DATASETS, DEFAULT_DATASET, RAW_DATASET)

# Operational tables in `raw` that no source declares and that must never be dropped. They are
# written by the ingest lock and completeness machinery rather than by a loader, so the source list
# cannot vouch for them and an explicit exclusion is the honest way to say so.
RAW_OPERATIONAL = frozenset({
    "RAW_APIF_INGEST_LOCK",
    "RAW_APIF_INGEST_COMPLETENESS_SNAPSHOT",
})

# Below this many expected relations the manifest is not trustworthy, and every relation in the
# warehouse would look orphaned. 117 are expected today (106 nodes + 11 sources); a floor of 50 sits
# far enough below to avoid false alarms and far enough above zero to catch a manifest that failed
# to parse, was written by a partial `--select` run, or was read from the wrong path.
MANIFEST_FLOOR = 50

PHASES = ("broken", "live-views", "tables", "all")

_PHASE_ORDER = ("broken", "live-views", "tables")

_PHASE_LABELS = {
    "broken": "BROKEN views: already error on any query, so nothing can be reading them",
    "live-views": "views that STILL RETURN DATA: retired SQL still answering queries",
    "tables": "orphan TABLES: these hold bytes, unlike the views",
}

# `project.dataset.table`, backticks optional around each part, as BigQuery renders a stored view
# definition. dbt always emits the fully qualified three-part form, so an unqualified name in a view
# body is not something this needs to resolve.
_REF_RE = re.compile(
    r"`?" + re.escape(PROJECT) + r"`?\s*\.\s*`?([A-Za-z0-9_]+)`?\s*\.\s*`?([A-Za-z0-9_]+)`?"
)


class ManifestError(RuntimeError):
    """The manifest is missing, unreadable, or too small to be trusted."""


def load_expected(manifest_path: Path) -> set[tuple[str, str]]:
    """Return every (dataset, relation) a prod dbt build would create.

    Raises ManifestError rather than returning a short set, because a short set silently becomes
    "drop almost everything".
    """
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
            continue                    # tests and analyses create no relation
        config = node.get("config") or {}
        if config.get("materialized") == "ephemeral":
            continue                    # inlined into its consumers, never built
        # A snapshot names its dataset with `target_schema`, not `schema`. See the module
        # docstring: getting this wrong files every snapshot under DEFAULT_DATASET.
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
            continue                    # transient; dbt sets a 12-hour expiration on these
        if dataset == RAW_DATASET and name in RAW_OPERATIONAL:
            continue                    # written by the ingest lock/completeness machinery
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
        # Follow the references so a view's upstream views are fetched too: resolution is
        # transitive, and an unfetched upstream would be assumed live and mis-phase the parent.
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
    _stack: frozenset[tuple[str, str]] = frozenset(),
) -> bool:
    """True if querying this relation would succeed, following views transitively.

    A one-level check gets this wrong in the direction that matters. `base_apif__bl1_teams` names
    only relations that exist, but one of them is itself a view over a dropped raw table, so a real
    query against it errors. Calling a broken view "live" only puts it in the cautious phase, which
    is harmless; calling a live view "broken" would put it in the phase advertised as risk-free,
    which is not. So anything unprovable resolves to True.
    """
    if key not in warehouse:
        return False                    # the relation is gone
    if warehouse[key] != "VIEW":
        return True                     # an existing table always resolves
    if key in _stack:
        return True                     # cycle; BigQuery forbids these, so do not recurse
    sql = queries.get(key)
    if sql is None:
        return True                     # definition unavailable: assume live, the safe side
    for ref in _refs_in(sql, key):
        if ref[0] not in ALLOWED_DATASETS:
            continue                    # cannot see it; assume it resolves, again the safe side
        if not resolves(ref, warehouse, queries, _stack | {key}):
            return False
    return True


def classify(
    orphans: list[tuple[str, str]],
    warehouse: dict[tuple[str, str], str],
    queries: dict[tuple[str, str], str],
) -> dict[str, list[tuple[str, str]]]:
    """Split the orphans into the three phases: disjoint, and together the whole set."""
    phases: dict[str, list[tuple[str, str]]] = {p: [] for p in _PHASE_ORDER}
    for key in orphans:
        if warehouse.get(key) != "VIEW":
            phases["tables"].append(key)
        elif resolves(key, warehouse, queries):
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
        # Not this script's job to fix, but anyone deciding what to drop should see it: it means the
        # last build did not finish, so the manifest may be ahead of the warehouse.
        print(f"\nWARNING: {len(missing)} expected relation(s) are NOT in the warehouse:")
        for dataset, relation in missing:
            print(f"      {dataset}.{relation}")

    orphans = find_orphans(warehouse, expected)
    if not orphans:
        print("\nNo orphaned relations. Nothing to do.")
        return 0

    phases = classify(orphans, warehouse, view_queries(client, orphans, warehouse))
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
            "Which orphans to select. 'broken' is the risk-free set (they already error). "
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
