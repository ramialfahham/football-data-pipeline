"""Write the dbt var and the registry seed CSV that are derived from competition_registry.yml."""

from __future__ import annotations

import csv
import io
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs" / "competition_registry.yml"
DBT_PROJECT_PATH = REPO_ROOT / "dbt_project" / "dbt_project.yml"
REGISTRY_SEED_PATH = REPO_ROOT / "dbt_project" / "seeds" / "competition_registry.csv"

# The seed's columns in file order, imported by check_registry_var_sync.py; each is a registry
# field name projected through `_normalise`, where '' means "not declared".
# `country` is absent because dim_league already carries it from the provider.
SEED_COLUMNS: tuple[str, ...] = (
    "league_code",
    "competition_type",
    "parent_competition",
    "confederation",
    "slug",
    "sort_order",
    "season_type",
)


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


def _normalise(value: object) -> str:
    """One registry value to one seed cell; the only normalisation, so the guard compares exactly."""
    return "" if value is None else str(value).strip()


def _registry_seed_rows() -> list[tuple[str, ...]]:
    """Sorted SEED_COLUMNS rows for every competition with league_code and competition_type set."""
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    comps = data.get("competitions") or []
    out: list[tuple[str, ...]] = []
    for row in comps:
        if not isinstance(row, dict):
            continue
        code = row.get("league_code")
        ctype = row.get("competition_type")
        if code and ctype:
            out.append(tuple(_normalise(row.get(c)) for c in SEED_COLUMNS))
    return sorted(set(out))


def _render_registry_seed(rows: list[tuple[str, ...]]) -> str:
    """Render with csv.writer so values are escaped; LF-only because csv defaults to CRLF."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(SEED_COLUMNS)
    writer.writerows(rows)
    return buf.getvalue()


def _write_registry_seed(rows: list[tuple[str, ...]]) -> bool:
    """Write the seed; True if the file changed."""
    new_text = _render_registry_seed(rows)
    if REGISTRY_SEED_PATH.exists() and REGISTRY_SEED_PATH.read_text(encoding="utf-8") == new_text:
        return False
    REGISTRY_SEED_PATH.write_text(new_text, encoding="utf-8")
    return True


def _update_dbt_project(codes: list[str]) -> bool:
    """Replace the active_competition_league_codes list in dbt_project.yml; True if changed."""
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
        seed_rows = _registry_seed_rows()
    except Exception as e:
        print(f"sync_dbt_vars: failed to read registry types — {e}", file=sys.stderr)
        return 1

    seed_changed = _write_registry_seed(seed_rows)
    if seed_changed:
        print(f"sync_dbt_vars: wrote competition_registry.csv ({len(seed_rows)} rows)")
    else:
        print(f"sync_dbt_vars: competition_registry.csv already in sync ({len(seed_rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
