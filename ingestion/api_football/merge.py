"""In-memory merge helpers for raw API payloads.

With the move to append-only raw storage, most merge logic has been removed.
Reference tables (fixtures, standings, teams, transfers, players) now write a
fresh complete snapshot on every run — no cross-run merging needed.

The one function that remains:

1. merge_fanout_batched — used by the per-fixture fanout tables (lineups,
   events, stats, fixture players, predictions). These tables are still
   merge-on-write because each run only fetches a subset of fixtures (the
   missing ones) and the merged blob is how the pipeline tracks what has
   already been fetched. This will be replaced by the fixture coverage
   tracking table in issue #221.
"""

from __future__ import annotations

# Keys on per-fixture fanout rows — one key per RAW batched table payload.
_FANOUT_PAYLOAD_KEYS: tuple[str, ...] = (
    "lineups",
    "events",
    "statistics",
    "players",
    "predictions",
)


def _fanout_row_payload_key(row: dict) -> str | None:
    """Return which fanout payload key (lineups, events, etc.) is present in this row."""
    for key in _FANOUT_PAYLOAD_KEYS:
        if key in row:
            return key
    return None


def _fanout_payload_nonempty(row: dict, payload_key: str) -> bool:
    """Return True when the fanout endpoint payload exists and is not empty."""
    value = row.get(payload_key)
    if value is None:
        return False
    if isinstance(value, list):
        return len(value) > 0
    return bool(value)


def _keep_existing_fanout_row(existing_row: dict, incoming_row: dict) -> bool:
    """Return True when the existing fanout data should be kept instead of replaced.

    We never replace a non-empty fanout block with an empty one. An empty
    incoming block means the API returned nothing this run (quota skip or
    empty response) — not that the data is gone. Keeping the existing non-empty
    block preserves historical coverage.
    """
    payload_key = _fanout_row_payload_key(incoming_row) or _fanout_row_payload_key(existing_row)
    if payload_key is None:
        return False
    return (
        _fanout_payload_nonempty(existing_row, payload_key)
        and not _fanout_payload_nonempty(incoming_row, payload_key)
    )


def merge_fanout_batched(
    existing: dict | None,
    incoming: dict,
    *,
    league_code: str,
    valid_fixture_ids: set[int] | None,
) -> dict:
    """Merge per-fixture fanout blocks (lineups, events, stats, players, predictions).

    The merge key is fixture_id: incoming data overwrites existing data for the
    same fixture. Fixtures whose id is not in valid_fixture_ids are pruned —
    this prevents rows from cancelled or removed fixtures building up indefinitely.

    This function will be removed once the fixture coverage tracking table
    (issue #221) replaces the blob-based completeness check. At that point
    the fanout tables will switch to append-only like the reference tables.
    """
    by_id: dict[int, dict] = {}

    for row in (existing or {}).get("response") or []:
        fid = row.get("fixture_id")
        if fid is not None:
            by_id[int(fid)] = row

    for row in incoming.get("response") or []:
        fid = row.get("fixture_id")
        if fid is None:
            continue
        fid_int = int(fid)
        if fid_int in by_id and _keep_existing_fanout_row(by_id[fid_int], row):
            continue
        by_id[fid_int] = row

    if valid_fixture_ids is not None:
        by_id = {k: v for k, v in by_id.items() if k in valid_fixture_ids}

    return {
        "league_code": league_code,
        "response": [by_id[k] for k in sorted(by_id.keys())],
    }
