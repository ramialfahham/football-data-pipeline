"""Sync dbt artifacts derived from competition_registry.yml.

Two artifacts are kept in lockstep with the registry:
  1. ``active_competition_league_codes`` in dbt_project.yml (active/in_progress codes).
  2. ``seeds/competition_registry.csv`` — the registry's own fields, projected into the warehouse
     so the website never has to read an authoring file to render a page (#62). Models join it on
     league_code to resolve a competition's type (and, via the competition_types seed, its
     club/national entity_type), its parent competition (qualifier → tournament, domestic cup →
     league), and its display fields: confederation, slug, sort_order, tier, season_type.
     See SEED_COLUMNS for the column list and for why ``country`` is not among them.

Run this after updating docs/competition_registry.yml (adding/removing a competition or
changing a competition_type). CI check_registry_var_sync.py fails if either is out of sync.

Usage (from repo root):
    python scripts/sync_dbt_vars.py
"""

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

# The seed's columns, in file order. THE single declaration:
# scripts/check_registry_var_sync.py IMPORTS this tuple rather than restating it, so the guard
# cannot end up checking a different column set from the one that is written. An earlier draft of
# this task duplicated it and leaned on a parity test; that was #873's shape and it was corrected
# in review. `tests/test_registry_seed_projection.py` asserts the two names are the same object,
# so restoring a local copy goes red.
#
# Every entry is a registry field name, projected through `_normalise`; '' means "not declared",
# the convention parent_competition already used.
#
# ⚠ `country` is deliberately absent (#69). It is NOT registry-owned data: `dim_league` already
# carries `league_country` and `country_flag_url` from the provider, so projecting the registry's
# hand-typed copy would make a third — and for 24 of 45 competitions that copy holds a region word
# ("Europe", "International") rather than a country at all. Countries become their own entity under
# #69; the competitions mart takes country and flag from `dim_league`.
SEED_COLUMNS: tuple[str, ...] = (
    "league_code",
    "competition_type",
    "parent_competition",
    "confederation",
    "slug",
    "sort_order",
    "tier",
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
    """One registry value → one seed cell. THE only place normalisation happens.

    Absent becomes '', the convention parent_competition already used for "no parent", and
    surrounding whitespace is stripped.

    ⚠ Stripping HERE rather than when reading the seed back is the point, and it was a real defect
    in the first draft (platform-reviewer, round 1). That version stripped the SEED side while
    comparing against an unstripped registry, so a seed cell of "UEFA " was normalised to "UEFA"
    before the comparison and matched — the guard passed on a corrupted file. Normalising once, on
    the way in, lets `check_registry_var_sync` compare the seed byte-for-byte and actually catch it.
    """
    return "" if value is None else str(value).strip()


def _registry_seed_rows() -> list[tuple[str, ...]]:
    """Return sorted rows of SEED_COLUMNS for every competition with league_code and
    competition_type set.

    A field absent from a competition becomes '', the convention parent_competition already used
    for "no parent". That is load-bearing for `tier`, which is declared on exactly the 16
    domestic_league competitions and on no other competition_type — structurally N/A for a cup
    rather than missing data, which is why the seed does not test it `not_null`.
    """
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
    """Render the seed with csv.writer rather than by joining values on commas.

    The previous f-string form would have emitted a broken file the first time any value contained
    a comma or a quote. None does today — but this projection adds five columns of authored text,
    and the failure mode is a silently malformed seed in the warehouse rather than an error.
    `lineterminator="\\n"` keeps the file LF-only on Windows, where csv defaults to CRLF.
    """
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(SEED_COLUMNS)
    writer.writerows(rows)
    return buf.getvalue()


def _write_registry_seed(rows: list[tuple[str, ...]]) -> bool:
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
