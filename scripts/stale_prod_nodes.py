"""Name the prod models a prod build left older than their inputs, so a merge request build rebuilds them.

A merge request build defers to prod for every model it does not build. When a prod build was cut
short (an errored node, and every node below it skipped, or an interrupted run), a prod model can be
older than a parent table, and a deferred read then meets a child that no longer matches its inputs.
A table model is stale when one of its parent tables was modified after it. Seeds and sources are
not compared; a view or an ephemeral model is passed through to its table parents.

Reads the prod manifest the job compiles and the last-modified times in BigQuery's `__TABLES__`
metadata (no table data is read). Prints a dbt selection, `<model>+` per stale model, on one line.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from google.cloud import bigquery

PASS_THROUGH = frozenset({"view", "ephemeral"})
IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]+$")


def _models(manifest: dict) -> dict[str, dict]:
    return {uid: node for uid, node in manifest["nodes"].items() if node["resource_type"] == "model"}


def _relation(node: dict) -> tuple[str, str]:
    return node["schema"], node.get("alias") or node["name"]


def _table_parents(uid: str, models: dict[str, dict]) -> list[str]:
    """The table models a model reads, looking through views and ephemeral models."""
    found: list[str] = []
    for parent in models[uid]["depends_on"]["nodes"]:
        if parent not in models:
            continue
        if models[parent]["config"].get("materialized") in PASS_THROUGH:
            found.extend(_table_parents(parent, models))
        else:
            found.append(parent)
    return found


def stale_models(manifest: dict, modified: dict[tuple[str, str], int]) -> list[str]:
    """The names of the table models older than a parent table, or missing from the warehouse."""
    models = _models(manifest)
    stale = []
    for uid, node in models.items():
        if node["config"].get("materialized") in PASS_THROUGH:
            continue
        own = modified.get(_relation(node))
        if own is None:
            stale.append(node["name"])
            continue
        parents = (modified.get(_relation(models[p])) for p in _table_parents(uid, models))
        if any(p is not None and p > own for p in parents):
            stale.append(node["name"])
    return sorted(stale)


def last_modified(client: bigquery.Client, manifest: dict) -> dict[tuple[str, str], int]:
    """Last-modified milliseconds of every table in the datasets the manifest's models live in."""
    datasets = sorted({(n["database"], n["schema"]) for n in _models(manifest).values()})
    for part in (p for d in datasets for p in d):
        if not IDENTIFIER.match(part):
            raise ValueError(f"not a project or dataset identifier: {part!r}")
    sql = " union all ".join(
        f"select '{schema}' as dataset, table_id, last_modified_time from `{database}.{schema}.__TABLES__`"
        for database, schema in datasets
    )
    return {(r.dataset, r.table_id): int(r.last_modified_time) for r in client.query(sql).result()}


def main(argv: list[str]) -> int:
    manifest = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    project = next(iter(_models(manifest).values()))["database"]
    stale = stale_models(manifest, last_modified(bigquery.Client(project=project), manifest))
    print(f"{len(stale)} stale prod model(s): {', '.join(stale) or 'none'}", file=sys.stderr)
    print(" ".join(f"{name}+" for name in stale))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
