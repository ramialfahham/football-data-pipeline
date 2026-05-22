"""Verify dbt vars.active_competition_league_codes matches registry active/in_progress.

Registry source of truth: docs/competition_registry.yml (status active or in_progress).
dbt var: active_competition_league_codes in dbt_project/dbt_project.yml.

Singular tests under dbt_project/tests/ prove var ⊆ base rows; this script proves
registry ↔ var stay in lockstep. See docs/competition_registry.yml header and
docs/development_workflow.md.

Usage (from repo root or dbt_project/):
    python scripts/check_registry_var_sync.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "competition_registry.yml"
DBT_PROJECT_PATH = REPO_ROOT / "dbt_project" / "dbt_project.yml"


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


def main() -> int:
    try:
        reg = _registry_active_codes()
        var = _dbt_var_codes()
        missing_flag = _registry_missing_ingest_active()
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

    print(f"check_registry_var_sync: OK ({len(s_reg)} competitions).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
