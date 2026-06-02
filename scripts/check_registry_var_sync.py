"""Verify dbt artifacts derived from the registry stay in lockstep with it.

Checks two things against docs/competition_registry.yml:
  1. ``active_competition_league_codes`` in dbt_project.yml == registry active/in_progress.
  2. ``seeds/competition_registry.csv`` == registry league_code → competition_type.

Both are written by scripts/sync_dbt_vars.py; this script fails CI if either drifts.
Singular tests under dbt_project/tests/ prove var ⊆ base rows. See
docs/competition_registry.yml header and docs/development_workflow.md.

Usage (from repo root or dbt_project/):
    python scripts/check_registry_var_sync.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "competition_registry.yml"
DBT_PROJECT_PATH = REPO_ROOT / "dbt_project" / "dbt_project.yml"
REGISTRY_SEED_PATH = REPO_ROOT / "dbt_project" / "seeds" / "competition_registry.csv"


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


def _registry_league_type_pairs() -> set[tuple[str, str]]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    comps = data.get("competitions") or []
    out: set[tuple[str, str]] = set()
    for row in comps:
        if not isinstance(row, dict):
            continue
        code = row.get("league_code")
        ctype = row.get("competition_type")
        if code and ctype:
            out.add((str(code), str(ctype)))
    return out


def _seed_league_type_pairs() -> set[tuple[str, str]]:
    with REGISTRY_SEED_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        if "league_code" not in cols or "competition_type" not in cols:
            raise KeyError(
                "competition_registry.csv missing league_code/competition_type columns"
            )
        return {
            (r["league_code"].strip(), r["competition_type"].strip())
            for r in reader
            if r.get("league_code") and r.get("competition_type")
        }


def main() -> int:
    try:
        reg = _registry_active_codes()
        var = _dbt_var_codes()
        missing_flag = _registry_missing_ingest_active()
        reg_pairs = _registry_league_type_pairs()
        seed_pairs = _seed_league_type_pairs()
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

    if reg_pairs != seed_pairs:
        only_reg = sorted(reg_pairs - seed_pairs)
        only_seed = sorted(seed_pairs - reg_pairs)
        print(
            "check_registry_var_sync: competition_registry.csv is out of sync with the "
            "registry. Run `python scripts/sync_dbt_vars.py`.",
            file=sys.stderr,
        )
        if only_reg:
            print(f"  in registry only: {only_reg}", file=sys.stderr)
        if only_seed:
            print(f"  in seed only: {only_seed}", file=sys.stderr)
        return 1

    print(
        f"check_registry_var_sync: OK ({len(s_reg)} competitions; "
        f"{len(seed_pairs)} registry-seed rows)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
