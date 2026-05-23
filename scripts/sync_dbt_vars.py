"""Sync active_competition_league_codes in dbt_project.yml from competition_registry.yml.

Run this after updating docs/competition_registry.yml (adding or removing a competition).
CI check_registry_var_sync.py will fail if the two are out of sync.

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
    return 0


if __name__ == "__main__":
    sys.exit(main())
