"""Verify dbt artifacts derived from the registry stay in lockstep with it.

Checks two things against docs/competition_registry.yml:
  1. ``active_competition_league_codes`` in dbt_project.yml == registry active/in_progress.
  2. ``seeds/competition_registry.csv`` == registry (league_code → competition_type,
     parent_competition), and every parent_competition references a known league_code.

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


def _registry_seed_triples() -> set[tuple[str, str, str]]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    comps = data.get("competitions") or []
    out: set[tuple[str, str, str]] = set()
    for row in comps:
        if not isinstance(row, dict):
            continue
        code = row.get("league_code")
        ctype = row.get("competition_type")
        if code and ctype:
            parent = row.get("parent_competition") or ""
            out.add((str(code), str(ctype), str(parent)))
    return out


def _seed_triples() -> set[tuple[str, str, str]]:
    with REGISTRY_SEED_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        for required in ("league_code", "competition_type", "parent_competition"):
            if required not in cols:
                raise KeyError(
                    f"competition_registry.csv missing required column '{required}'"
                )
        return {
            (
                r["league_code"].strip(),
                r["competition_type"].strip(),
                (r.get("parent_competition") or "").strip(),
            )
            for r in reader
            if r.get("league_code") and r.get("competition_type")
        }


def _registry_dangling_parents() -> list[tuple[str, str]]:
    """Return (league_code, parent_competition) where parent_competition is set but is not a
    known league_code. A dangling parent link silently breaks parent-keyed joins (e.g. a
    tournament resolving its qualifier competitions), so it must fail CI."""
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
        reg_triples = _registry_seed_triples()
        seed_triples = _seed_triples()
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

    if reg_triples != seed_triples:
        only_reg = sorted(reg_triples - seed_triples)
        only_seed = sorted(seed_triples - reg_triples)
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
        f"{len(seed_triples)} registry-seed rows)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
