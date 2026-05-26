"""Migrate fanout staging SQL models to read from raw_apif_{lc}_fixture_details.

Changes per SQL file:
  1. Source table: raw_apif_{lc}_{entity} → raw_apif_{lc}_fixture_details
  2. CTE rename: blocks → fixtures
  3. Column rename: block_json → fixture_json
  4. Fixture ID path: $.fixture_id → $.fixture.id
  5. League code: coalesce(json_value(src.payload, '$.league_code'), 'LC') → 'LC'

Changes in sources.yml:
  - Remove 4 old fanout source entries per competition
  - Add raw_apif_{lc}_fixture_details source entry for all 20 competitions
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STAGING_DIR = REPO_ROOT / "dbt_project" / "models" / "1_staging" / "api_football"
SOURCES_YML = STAGING_DIR / "sources.yml"

# All 20 competitions and their staging subfolder paths
COMPETITIONS = {
    # domestic leagues
    "BL1": STAGING_DIR / "domestic_league" / "bl1",
    "BL2": STAGING_DIR / "domestic_league" / "bl2",
    "ED":  STAGING_DIR / "domestic_league" / "ed",
    "L1":  STAGING_DIR / "domestic_league" / "l1",
    "LMX": STAGING_DIR / "domestic_league" / "lmx",
    "LP":  STAGING_DIR / "domestic_league" / "lp",
    "MLS": STAGING_DIR / "domestic_league" / "mls",
    "PD":  STAGING_DIR / "domestic_league" / "pd",
    "PL":  STAGING_DIR / "domestic_league" / "pl",
    "SA":  STAGING_DIR / "domestic_league" / "sa",
    "SPL": STAGING_DIR / "domestic_league" / "spl",
    "VL":  STAGING_DIR / "domestic_league" / "vl",
    # WCQ
    "WCQAF": STAGING_DIR / "qualifying" / "wcq",
    "WCQAS": STAGING_DIR / "qualifying" / "wcq",
    "WCQCA": STAGING_DIR / "qualifying" / "wcq",
    "WCQEU": STAGING_DIR / "qualifying" / "wcq",
    "WCQIP": STAGING_DIR / "qualifying" / "wcq",
    "WCQOC": STAGING_DIR / "qualifying" / "wcq",
    "WCQSA": STAGING_DIR / "qualifying" / "wcq",
    # WC
    "WC":  STAGING_DIR / "world_championship" / "wc",
}

# Competitions that have lineups (domestic + WC, not WCQ)
LINEUPS_COMPS = {lc for lc in COMPETITIONS if not lc.startswith("WCQ")}

# Entity files to migrate per competition
ENTITY_FILES = {
    "fixture_events": set(COMPETITIONS.keys()),     # all 20
    "fixture_statistics": set(COMPETITIONS.keys()), # all 20
    "fixture_players": set(COMPETITIONS.keys()),    # all 20
    "lineups": LINEUPS_COMPS,                        # 13 (no WCQ)
}

OLD_SOURCE_TABLES = {"lineups", "fixture_events", "fixture_statistics", "fixture_players"}


def transform_sql(content: str, lc: str, entity: str) -> str:
    """Apply all required transformations to a staging SQL file."""
    lc_lower = lc.lower()

    # 1. Source table reference
    old_source = f"raw_apif_{lc_lower}_{entity}"
    new_source = f"raw_apif_{lc_lower}_fixture_details"
    content = content.replace(f"source('api_football', '{old_source}')",
                              f"source('api_football', '{new_source}')")

    # 2. Remove coalesce league_code pattern, replace with hardcoded string
    # Pattern: coalesce(json_value(src.payload, '$.league_code'), 'LC')
    coalesce_pattern = re.compile(
        r"coalesce\(json_value\(src\.payload,\s*'\$\.league_code'\),\s*'" + re.escape(lc) + r"'\)"
    )
    content = coalesce_pattern.sub(f"'{lc}'", content)

    # 3. Rename CTE: blocks → fixtures  (as declaration)
    content = content.replace("blocks as (", "fixtures as (")

    # 4. Rename CTE references: from blocks, → from fixtures,
    content = content.replace("from blocks,", "from fixtures,")

    # 5. Rename column: block_json → fixture_json
    content = content.replace("block_json", "fixture_json")

    # 6. Fix fixture_id path: $.fixture_id → $.fixture.id
    content = content.replace("'$.fixture_id'", "'$.fixture.id'")

    return content


def migrate_sql_files(dry_run: bool = False) -> list[str]:
    """Rewrite all fanout staging SQL files. Returns list of modified file paths."""
    modified = []
    errors = []

    for entity, comps in ENTITY_FILES.items():
        for lc in sorted(comps):
            folder = COMPETITIONS[lc]
            lc_lower = lc.lower()
            filename = f"stg_apif__{lc_lower}_{entity}.sql"
            filepath = folder / filename

            if not filepath.exists():
                errors.append(f"MISSING: {filepath}")
                continue

            original = filepath.read_text(encoding="utf-8")
            transformed = transform_sql(original, lc, entity)

            if transformed == original:
                print(f"  SKIP (no change): {filename}")
                continue

            if dry_run:
                print(f"  DRY RUN: would rewrite {filepath.relative_to(REPO_ROOT)}")
            else:
                filepath.write_text(transformed, encoding="utf-8")
                print(f"  UPDATED: {filepath.relative_to(REPO_ROOT)}")

            modified.append(str(filepath))

    if errors:
        print("\nERRORS:")
        for e in errors:
            print(f"  {e}")

    return modified


# ---------------------------------------------------------------------------
# sources.yml surgery
# ---------------------------------------------------------------------------

SOURCE_ENTRY_TEMPLATE = """\
      - name: raw_apif_{lc_lower}_fixture_details
        identifier: RAW_APIF_{lc_upper}_FIXTURE_DETAILS
        loaded_at_field: ingested_at
        freshness:
          warn_after: {{count: 30, period: hour}}
          error_after: {{count: 54, period: hour}}"""


def _make_source_entry(lc: str) -> str:
    return SOURCE_ENTRY_TEMPLATE.format(
        lc_lower=lc.lower(),
        lc_upper=lc.upper(),
    )


def migrate_sources_yml(dry_run: bool = False) -> None:
    """Remove old fanout source entries and add fixture_details entries."""
    content = SOURCES_YML.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)

    # Build a set of names to remove
    names_to_remove: set[str] = set()
    for entity in OLD_SOURCE_TABLES:
        for lc in COMPETITIONS:
            names_to_remove.add(f"raw_apif_{lc.lower()}_{entity}")

    # Parse and filter: remove 6-line blocks starting with "      - name: <name_to_remove>"
    # Each source entry is exactly 6 lines:
    #   - name: ...
    #     identifier: ...
    #     loaded_at_field: ...
    #     freshness:
    #       warn_after: ...
    #       error_after: ...
    new_lines: list[str] = []
    i = 0
    removed = 0
    while i < len(lines):
        line = lines[i]
        # Check if this is the start of an entry we should remove
        stripped = line.strip()
        if stripped.startswith("- name: "):
            name = stripped[len("- name: "):].strip()
            if name in names_to_remove:
                # Skip this entry (6 lines)
                i += 6
                removed += 1
                continue
        new_lines.append(line)
        i += 1

    print(f"  sources.yml: removed {removed} old fanout source entries")

    # Now add fixture_details entries. Insert them after each competition's
    # last existing entry. Strategy: find the last entry for each LC and append after.
    # Simpler: bulk-append all fixture_details entries at the end of the sources list
    # (before the closing of the tables: list).
    # Actually, let's find a good insertion point: after the last entry for each LC,
    # but that's complex. Instead, group all new entries and insert them before the
    # end of the source tables list.
    #
    # Find the last "      - name: raw_apif_" line and insert after the 6-line block.
    rebuilt = "".join(new_lines)

    # Find insertion point: last occurrence of a source entry (any raw_apif_ entry)
    # We'll append fixture_details entries for each competition right after the
    # competition's existing entries. But for simplicity, append all new entries
    # together after the last existing source entry in the file.

    # Build new entries block
    new_entries_block = "\n"
    for lc in sorted(COMPETITIONS.keys()):
        new_entries_block += _make_source_entry(lc) + "\n"

    # Find insertion: after the last "error_after:" line in the sources tables section
    # (which is the end of the last source entry)
    last_error_after = rebuilt.rfind("          error_after: {count: 54, period: hour}")
    if last_error_after == -1:
        print("  ERROR: Could not find insertion point in sources.yml")
        return

    # Find the end of that line
    end_of_line = rebuilt.find("\n", last_error_after) + 1
    rebuilt = rebuilt[:end_of_line] + new_entries_block + rebuilt[end_of_line:]

    if dry_run:
        print(f"  DRY RUN: would rewrite sources.yml ({len(new_entries_block.splitlines())} new lines)")
        return

    SOURCES_YML.write_text(rebuilt, encoding="utf-8")
    print(f"  sources.yml: added {len(COMPETITIONS)} fixture_details entries")


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("=== DRY RUN — no files will be written ===\n")

    print("=== Migrating SQL staging models ===")
    modified = migrate_sql_files(dry_run=dry_run)
    print(f"\nTotal SQL files updated: {len(modified)}")

    print("\n=== Migrating sources.yml ===")
    migrate_sources_yml(dry_run=dry_run)

    print("\nDone.")


if __name__ == "__main__":
    main()
