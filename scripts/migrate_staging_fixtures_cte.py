"""
Update the `fixtures` CTE in all FIXTURE_DETAILS staging models.

Old pattern (batch-blob storage — one row = one batch of up to 20 fixtures):
    from src,
        unnest(coalesce(json_query_array(src.payload, '$.response'), [])) as fixture_json

New pattern (per-fixture storage — one row = one fixture):
    from src  -- src.payload IS the fixture_json

The rest of each model (events/statistics/players/lineups CTEs) is unchanged
because they already reference `fixture_json` and the JSON paths are identical.
"""

import re
import sys
from pathlib import Path

STAGING_ROOT = Path("dbt_project/models/1_staging")

PATTERNS = [
    "stg_apif__*_fixture_events.sql",
    "stg_apif__*_fixture_statistics.sql",
    "stg_apif__*_fixture_players.sql",
    "stg_apif__*_lineups.sql",
]

# Regex to match the full `fixtures` CTE body that unnests $.response
FIXTURES_CTE_PATTERN = re.compile(
    r"(fixtures as \(\n)"                           # opening line
    r"    select\n"
    r"((?:.*\n)*?)"                                 # columns before the FROM
    r"    from src,\n"
    r"        unnest\(coalesce\(json_query_array\(src\.payload, '\$\.response'\), \[\]\)\) as fixture_json\n"
    r"(\))",
    re.MULTILINE,
)

REPLACEMENT = (
    r"\1"                                           # fixtures as (
    r"    select\n"
    r"\2"                                           # columns (league_code, raw_ingested_at)
    r"    from src\n"                               # src.payload IS fixture_json — no unnest
    r"\3"                                           # closing )
)


def migrate(content: str) -> str:
    """Return updated content, or original if nothing matched."""
    # Also handle the WC variant where league_code comes first
    new = FIXTURES_CTE_PATTERN.sub(REPLACEMENT, content)
    # After the sub, `fixture_json` in select list must become `src.payload as fixture_json`
    # The columns section already has `fixture_json` as the bare UNNEST alias.
    # We need to change that column reference to `src.payload as fixture_json`.
    # Replace bare `fixture_json` column reference in the select list with
    # `src.payload as fixture_json`. The column may or may not have a trailing
    # comma depending on whether it is the last item in the select list.
    new = re.sub(
        r"^        fixture_json(,?)$",
        r"        src.payload as fixture_json\1",
        new,
        flags=re.MULTILINE,
    )
    return new


def main() -> int:
    files: list[Path] = []
    for pattern in PATTERNS:
        files.extend(STAGING_ROOT.rglob(pattern))
    files.sort()

    modified = skipped = 0
    for path in files:
        content = path.read_text(encoding="utf-8")

        if "_fixture_details" not in content:
            skipped += 1
            continue
        if "unnest(coalesce(json_query_array(src.payload, '$.response'), []))" not in content:
            print(f"  SKIP (already migrated?): {path}")
            skipped += 1
            continue

        new_content = migrate(content)
        if new_content == content:
            print(f"  NO CHANGE: {path}")
            skipped += 1
            continue

        path.write_text(new_content, encoding="utf-8")
        print(f"  PATCHED: {path}")
        modified += 1

    print(f"\nDone: {modified} patched, {skipped} skipped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
