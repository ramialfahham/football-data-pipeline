"""Sync dbt artifacts derived from competition_registry.yml.

Two artifacts are kept in lockstep with the registry:
  1. ``active_competition_league_codes`` in dbt_project.yml (active/in_progress codes).
  2. ``seeds/competition_registry.csv`` — the league_code → competition_type mapping
     that dbt models join on to resolve a competition's type (and, via the
     competition_types seed, its club/national entity_type).

Run this after updating docs/competition_registry.yml (adding/removing a competition or
changing a competition_type). CI check_registry_var_sync.py fails if either is out of sync.

Usage (from repo root):
    python scripts/sync_dbt_vars.py
"""

from __future__ import annotations

import re
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
    return sorted(out)


def _registry_league_type_rows() -> list[tuple[str, str]]:
    """Return sorted (league_code, competition_type) for every competition with both set."""
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    comps = data.get("competitions") or []
    out: list[tuple[str, str]] = []
    for row in comps:
        if not isinstance(row, dict):
            continue
        code = row.get("league_code")
        ctype = row.get("competition_type")
        if code and ctype:
            out.append((str(code), str(ctype)))
    return sorted(set(out))


def _render_registry_seed(rows: list[tuple[str, str]]) -> str:
    body = "".join(f"{code},{ctype}\n" for code, ctype in rows)
    return "league_code,competition_type\n" + body


def _write_registry_seed(rows: list[tuple[str, str]]) -> bool:
    """Write seeds/competition_registry.csv. Returns True if the file changed."""
    new_text = _render_registry_seed(rows)
    if REGISTRY_SEED_PATH.exists() and REGISTRY_SEED_PATH.read_text(encoding="utf-8") == new_text:
        return False
    REGISTRY_SEED_PATH.write_text(new_text, encoding="utf-8")
    return True


def _update_dbt_project(codes: list[str]) -> bool:
    """Replace active_competition_league_codes list in dbt_project.yml.

    Returns True if the file was changed, False if already correct.
    """
    text = DBT_PROJECT_PATH.read_text(encoding="utf-8")

    new_list = "\n".join(f"    - {c}" for c in codes)
    new_block = f"  active_competition_league_codes:\n{new_list}"

    pattern = re.compile(
        r"^  active_competition_league_codes:\n(?:    - .+\n)*",
        re.MULTILINE,
    )

    if not pattern.search(text):
        print(
            "sync_dbt_vars: could not locate active_competition_league_codes block "
            "in dbt_project/dbt_project.yml",
            file=sys.stderr,
        )
        return False

    new_text = pattern.sub(new_block + "\n", text)
    if new_text == text:
        return False

    DBT_PROJECT_PATH.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    try:
        codes = _registry_active_codes()
    except Exception as e:
        print(f"sync_dbt_vars: failed to read registry — {e}", file=sys.stderr)
        return 1

    if not codes:
        print(
            "sync_dbt_vars: no active/in_progress codes found in registry",
            file=sys.stderr,
        )
        return 1

    changed = _update_dbt_project(codes)
    if changed:
        print(f"sync_dbt_vars: updated active_competition_league_codes → {codes}")
    else:
        print(f"sync_dbt_vars: already in sync ({len(codes)} competitions: {codes})")

    try:
        type_rows = _registry_league_type_rows()
    except Exception as e:
        print(f"sync_dbt_vars: failed to read registry types — {e}", file=sys.stderr)
        return 1

    seed_changed = _write_registry_seed(type_rows)
    if seed_changed:
        print(f"sync_dbt_vars: wrote competition_registry.csv ({len(type_rows)} rows)")
    else:
        print(f"sync_dbt_vars: competition_registry.csv already in sync ({len(type_rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
