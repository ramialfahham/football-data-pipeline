"""Fail CI when the dbt var or the registry seed written by sync_dbt_vars.py drifts from the registry."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "competition_registry.yml"
DBT_PROJECT_PATH = REPO_ROOT / "dbt_project" / "dbt_project.yml"
REGISTRY_SEED_PATH = REPO_ROOT / "dbt_project" / "seeds" / "competition_registry.csv"

# SEED_COLUMNS is imported from the writer so the guard checks the column set that is written;
# the sys.path line makes the import work both as a script and under pytest.
sys.path.insert(0, str(REPO_ROOT))
from scripts.sync_dbt_vars import SEED_COLUMNS, _normalise  # noqa: E402


def _registry_active_codes() -> list[str]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    comps = data.get("competitions") or []
    out: list[str] = []
    for row in comps:
        if not isinstance(row, dict):
            continue
        if row.get("status") not in ("active", "in_progress"):
            continue
        code = row.get("league_code")
        if code:
            out.append(str(code))
    return out


def _dbt_var_codes() -> list[str]:
    data = yaml.safe_load(DBT_PROJECT_PATH.read_text(encoding="utf-8"))
    vars_block = data.get("vars") or {}
    raw = vars_block.get("active_competition_league_codes")
    if raw is None:
        raise KeyError("dbt_project.yml missing vars.active_competition_league_codes")
    if not isinstance(raw, list):
        raise TypeError("active_competition_league_codes must be a YAML list")
    return [str(x) for x in raw]


def _registry_missing_ingest_active() -> list[str]:
    """Return league_codes of active/in_progress entries missing the ingest_active field."""
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    comps = data.get("competitions") or []
    missing: list[str] = []
    for row in comps:
        if not isinstance(row, dict):
            continue
        if row.get("status") not in ("active", "in_progress"):
            continue
        if "ingest_active" not in row:
            missing.append(str(row.get("league_code", "<unknown>")))
    return missing


def _registry_seed_rows() -> set[tuple[str, ...]]:
    """The rows the seed should hold, derived from the registry over every SEED_COLUMNS column."""
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    comps = data.get("competitions") or []
    out: set[tuple[str, ...]] = set()
    for row in comps:
        if not isinstance(row, dict):
            continue
        code = row.get("league_code")
        ctype = row.get("competition_type")
        if code and ctype:
            out.add(tuple(_normalise(row.get(c)) for c in SEED_COLUMNS))
    return out


def _seed_rows() -> set[tuple[str, ...]]:
    """The rows the seed holds, read verbatim; only the writer's `_normalise` normalises."""
    with REGISTRY_SEED_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        for required in SEED_COLUMNS:
            if required not in cols:
                raise KeyError(
                    f"competition_registry.csv missing required column '{required}'"
                )
        return {
            tuple(r.get(c) or "" for c in SEED_COLUMNS)
            for r in reader
            if r.get("league_code") and r.get("competition_type")
        }


def _registry_dangling_parents() -> list[tuple[str, str]]:
    """Return (league_code, parent_competition) where the parent is not a known league_code."""
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    comps = data.get("competitions") or []
    codes = {
        str(r.get("league_code"))
        for r in comps
        if isinstance(r, dict) and r.get("league_code")
    }
    out: list[tuple[str, str]] = []
    for row in comps:
        if not isinstance(row, dict):
            continue
        parent = row.get("parent_competition")
        if parent and str(parent) not in codes:
            out.append((str(row.get("league_code", "<unknown>")), str(parent)))
    return out


def main() -> int:
    try:
        reg = _registry_active_codes()
        var = _dbt_var_codes()
        missing_flag = _registry_missing_ingest_active()
        reg_rows = _registry_seed_rows()
        seed_rows = _seed_rows()
        dangling_parents = _registry_dangling_parents()
    except Exception as e:
        print(f"check_registry_var_sync: {e}", file=sys.stderr)
        return 1

    if not reg:
        print(
            "check_registry_var_sync: registry has no active/in_progress codes",
            file=sys.stderr,
        )
        return 1
    if not var:
        print(
            "check_registry_var_sync: active_competition_league_codes is empty",
            file=sys.stderr,
        )
        return 1

    if missing_flag:
        print(
            f"check_registry_var_sync: missing `ingest_active` on: {missing_flag}. "
            "Every active/in_progress competition must explicitly set ingest_active: true or false.",
            file=sys.stderr,
        )
        return 1

    s_reg = sorted(set(reg))
    s_var = sorted(set(var))
    if s_reg != s_var:
        only_reg = sorted(set(reg) - set(var))
        only_var = sorted(set(var) - set(reg))
        print(
            "check_registry_var_sync: registry and dbt var lists differ.",
            file=sys.stderr,
        )
        if only_reg:
            print(f"  in registry only: {only_reg}", file=sys.stderr)
        if only_var:
            print(f"  in dbt_project.yml only: {only_var}", file=sys.stderr)
        return 1

    if dangling_parents:
        print(
            "check_registry_var_sync: parent_competition references an unknown league_code "
            "(dangling parent link):",
            file=sys.stderr,
        )
        for code, parent in sorted(dangling_parents):
            print(
                f"  {code} → parent_competition '{parent}' (no such league_code)",
                file=sys.stderr,
            )
        return 1

    if reg_rows != seed_rows:
        only_reg = sorted(reg_rows - seed_rows)
        only_seed = sorted(seed_rows - reg_rows)
        print(
            "check_registry_var_sync: competition_registry.csv is out of sync with the "
            "registry. Run `python scripts/sync_dbt_vars.py`.",
            file=sys.stderr,
        )
        # The column names tell the reader which field of a tuple drifted.
        print(f"  columns: {', '.join(SEED_COLUMNS)}", file=sys.stderr)
        if only_reg:
            print(f"  in registry only: {only_reg}", file=sys.stderr)
        if only_seed:
            print(f"  in seed only: {only_seed}", file=sys.stderr)
        return 1

    print(
        f"check_registry_var_sync: OK ({len(s_reg)} competitions; "
        f"{len(seed_rows)} registry-seed rows over {len(SEED_COLUMNS)} columns)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
