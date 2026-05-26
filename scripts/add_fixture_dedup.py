"""
Add a deduplication CTE to all staging models that read from FIXTURE_DETAILS.

When the batch ingestion retries a fixture (e.g. empty statistics within the
retry window), it appends a new row to RAW_APIF_{LC}_FIXTURE_DETAILS. Without
dedup, staging unnests both rows and produces duplicate events/players/etc.

Fix: insert a `deduped_fixtures` CTE after `fixtures` that uses QUALIFY
ROW_NUMBER() to keep one row per fixture.id, then point the next CTE at it.
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

# The dedup CTE text — uses __FIXTURES_SRC__ as a placeholder so the
# regex replacement for downstream CTEs doesn't accidentally match it.
DEDUP_CTE_TEMPLATE = """\

deduped_fixtures as (
    select *
    from __FIXTURES_SRC__
    qualify
        row_number() over (
            partition by safe_cast(json_value(fixture_json, '$.fixture.id') as int64)
            order by raw_ingested_at desc
        ) = 1
),
"""


def needs_dedup(content: str) -> bool:
    return (
        "raw_apif_" in content
        and "_fixture_details" in content
        and "fixtures as (" in content
        and "deduped_fixtures" not in content
    )


def add_dedup(content: str) -> str:
    lines = content.split("\n")

    # Find the line where `fixtures as (` starts
    fixtures_start = None
    for i, line in enumerate(lines):
        if re.match(r"fixtures as \(", line.strip()):
            fixtures_start = i
            break
    if fixtures_start is None:
        return content

    # Walk forward to find the closing `)` of the fixtures CTE
    depth = 0
    fixtures_end = None
    for i in range(fixtures_start, len(lines)):
        stripped = lines[i].strip()
        depth += stripped.count("(") - stripped.count(")")
        if i > fixtures_start and depth == 0:
            fixtures_end = i
            break
    if fixtures_end is None:
        return content

    # Insert the dedup CTE (with placeholder) right after the fixtures closing paren
    dedup_text = DEDUP_CTE_TEMPLATE.replace("__FIXTURES_SRC__", "fixtures")
    dedup_lines = dedup_text.split("\n")

    new_lines = lines[: fixtures_end + 1] + dedup_lines + lines[fixtures_end + 1 :]
    new_content = "\n".join(new_lines)

    # Now find the FIRST CTE after deduped_fixtures that references `from fixtures`
    # and redirect it to `from deduped_fixtures`.  We skip past the dedup CTE block
    # itself by searching only in the portion of the string after its closing `),`.
    split_marker = "deduped_fixtures as ("
    before_dedup, _, after_dedup = new_content.partition(split_marker)

    # Find the closing `),` of the dedup CTE in the after portion
    close_match = re.search(r"\),?\n", after_dedup)
    if close_match:
        after_close = after_dedup[close_match.end():]
        after_close_replaced = re.sub(
            r"\bfrom fixtures\b",
            "from deduped_fixtures",
            after_close,
            count=1,
        )
        new_content = before_dedup + split_marker + after_dedup[: close_match.end()] + after_close_replaced
    else:
        # Fallback: just replace the second occurrence
        occurrences = [m.start() for m in re.finditer(r"\bfrom fixtures\b", new_content)]
        if len(occurrences) >= 2:
            pos = occurrences[1]
            new_content = new_content[:pos] + new_content[pos:].replace("from fixtures", "from deduped_fixtures", 1)

    return new_content


def main():
    files_found = []
    for pattern in PATTERNS:
        files_found.extend(STAGING_ROOT.rglob(pattern))
    files_found.sort()

    modified = 0
    skipped = 0

    for path in files_found:
        content = path.read_text(encoding="utf-8")
        if not needs_dedup(content):
            skipped += 1
            continue

        new_content = add_dedup(content)
        if new_content == content:
            print(f"  UNCHANGED: {path}")
            skipped += 1
            continue

        path.write_text(new_content, encoding="utf-8")
        print(f"  PATCHED: {path}")
        modified += 1

    print(f"\nDone: {modified} files patched, {skipped} skipped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
