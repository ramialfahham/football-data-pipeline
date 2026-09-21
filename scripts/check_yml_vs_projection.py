"""Projection gate — every column a model yml lists exists in that model's projection.

The reverse of `declare_missing_columns.py`. That script reads the catalogue and adds to the
yml what the warehouse has and the yml lacks; this one reads the yml and fails on what the yml
lists and the warehouse lacks. A `.yml` can describe a column the model stopped emitting, and
with `persist_docs` on dbt attaches nothing for it and says nothing — the description simply
never reaches BigQuery. Enforces `dbt_project/docs/engineering_standards.md` §3.5 ("every
documented column exists in the model's projection") and is the mechanism it names.

Where the catalogue comes from matters more than anything else here. `catalog.json` is what
`dbt docs generate` writes, and it describes whatever warehouse that command was pointed at.
On a dev machine that is the last local run — a handful of `dev_*` relations — and checking
against it would find every model "missing" its columns, or worse, find nothing. So:

  * the models on DISK are the authority on what exists; the catalogue is the authority on what
    each of them projects; the two never come from the same file;
  * a catalogue missing any on-disk model is refused outright (the same abort as
    `declare_missing_columns.py`): a partial catalogue is not a smaller answer, it is no answer;
  * in CI this runs inside `data:build:main`, two lines after the `dbt docs generate` that wrote
    the file, so the catalogue there is always the whole prod warehouse.

A `parent.field` entry (a struct field, `recent_meetings.goals_for`) is matched by its full
path: dbt-bigquery's catalogue reads `INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`, so it holds the
parent column AND every leaf path beneath it, and a mistyped or removed field is caught like any
other column. Models match by name, columns case-insensitively, as BigQuery resolves them. A yml
block for a model with no `.sql` on disk is a finding too: `dbt parse` only warns on it, and the
descriptions it carries reach nothing.

Floors against an empty walk, as `check_relationships_coverage.py` does: fewer models or fewer
listed columns than the repo plainly has fails the gate rather than passing on nothing. Exit 1
on any finding, on an unreadable or partial catalogue, on an unparseable yml, below a floor.
Fails CLOSED.

    python scripts/check_yml_vs_projection.py --catalog dbt_project/target/catalog.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DBT_DIR = REPO_ROOT / "dbt_project"
MODELS_DIR = DBT_DIR / "models"

# Floors, set well under what the repo has (101 models, 1,915 listed columns when written) and
# well over zero, so ordinary deletion never trips them and a broken walk always does.
MIN_MODELS = 50
MIN_LISTED_COLUMNS = 800


class Abort(Exception):
    """A reason this run cannot be trusted. Printed and exit 1; nothing is judged."""


def _rel(path: pathlib.Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _skip(path: pathlib.Path) -> bool:
    rel = f"/{_rel(path)}"
    return "/target/" in rel or "/dbt_packages/" in rel


def models_on_disk() -> set[str]:
    """Model names from the SQL files, every layer."""
    return {p.stem for p in MODELS_DIR.rglob("*.sql") if not _skip(p)}


def listed_columns() -> dict[str, tuple[pathlib.Path, list[str]]]:
    """model name -> (yml that declares it, column names it lists), every yml in the project."""
    found: dict[str, tuple[pathlib.Path, list[str]]] = {}
    for path in sorted(DBT_DIR.rglob("*.yml")):
        if _skip(path):
            continue
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, UnicodeDecodeError, OSError) as exc:
            raise Abort(f"{_rel(path)}: cannot parse ({exc.__class__.__name__})") from exc
        if not isinstance(doc, dict) or not isinstance(doc.get("models"), list):
            continue
        for model in doc["models"]:
            if not isinstance(model, dict) or not isinstance(model.get("name"), str):
                continue
            name = model["name"]
            if name in found:
                raise Abort(
                    f"model {name!r} is declared twice: in {_rel(found[name][0])} "
                    f"and in {_rel(path)}. Refusing to guess which list is the model's."
                )
            cols = [
                c["name"] for c in (model.get("columns") or [])
                if isinstance(c, dict) and isinstance(c.get("name"), str)
            ]
            found[name] = (path, cols)
    return found


def catalog_columns(catalog_path: pathlib.Path) -> dict[str, set[str]]:
    """model name -> lower-cased column names the warehouse projects."""
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        raise Abort(f"{_rel(catalog_path)}: cannot read ({exc.__class__.__name__})") from exc
    if not isinstance(catalog, dict):
        raise Abort(f"{_rel(catalog_path)}: not a dbt catalogue (no object at the top)")
    out: dict[str, set[str]] = {}
    for uid, node in (catalog.get("nodes") or {}).items():
        if not uid.startswith("model.") or not isinstance(node, dict):
            continue
        cols = node.get("columns") or {}
        out[uid.rsplit(".", 1)[-1]] = {
            str(c.get("name")).lower() for c in cols.values() if isinstance(c, dict)
        }
    return out


def check(catalog_path: pathlib.Path) -> tuple[list[str], dict[str, int]]:
    """(findings, census). Every guard that can refuse the run raises Abort here."""
    models = models_on_disk()
    if len(models) < MIN_MODELS:
        raise Abort(
            f"found only {len(models)} models under {_rel(MODELS_DIR)}, expected at least "
            f"{MIN_MODELS}. The layout has moved, or this is not the repo root."
        )

    declared = listed_columns()
    catalog = catalog_columns(catalog_path)

    absent = sorted(models - catalog.keys())
    if absent:
        raise Abort(
            f"the catalogue is missing {len(absent)} of {len(models)} models on disk, so it "
            f"does not describe this warehouse: {', '.join(absent[:5])}"
            f"{' ...' if len(absent) > 5 else ''}\n"
            f"  This is almost always a stale or dev-target catalog.json. Fetch the artifact "
            f"from the most recent data:build:main. (A model that is `enabled: false` or "
            f"ephemeral is never in a catalogue; this repo has none, and one would need its "
            f"own rule here.)"
        )

    findings: list[str] = []
    listed = 0
    for name in sorted(declared):
        path, cols = declared[name]
        if name not in models:
            findings.append(
                f"{_rel(path)}: {name} is declared but has no model file on disk"
            )
            continue
        listed += len(cols)
        projected = catalog[name]
        for col in cols:
            if col.lower() not in projected:
                findings.append(
                    f"{_rel(path)}: {name}.{col} is listed but not in the model's projection"
                )

    if listed < MIN_LISTED_COLUMNS:
        raise Abort(
            f"found only {listed} listed columns across {len(declared)} declared models, "
            f"expected at least {MIN_LISTED_COLUMNS}. A check that finds nothing always passes."
        )

    return findings, {"models": len(models), "listed": listed, "absent": len(findings)}


def main(catalog_path: pathlib.Path) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    try:
        findings, census = check(catalog_path)
    except Abort as exc:
        print(f"ABORT: {exc}")
        return 1

    status = "PROJECTION" if findings else "OK"
    print(f"{status}: {census['models']} models, {census['listed']} listed columns, "
          f"{census['absent']} absent from their projection")
    if findings:
        print()
        for finding in findings:
            print(f"  - {finding}")
        print("\nThe standard is dbt_project/docs/engineering_standards.md section 3.5: remove "
              "the entry, or restore the column (or the model) it describes.")
        return 1
    return 0


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--catalog",
        type=pathlib.Path,
        default=DBT_DIR / "target" / "catalog.json",
        help="dbt catalog.json describing the PRODUCTION warehouse (a data:build:main artifact).",
    )
    args = parser.parse_args(argv)
    return main(args.catalog)


if __name__ == "__main__":
    sys.exit(_cli())
