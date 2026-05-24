"""In-memory merge helpers for raw API payloads.

With the move to append-only raw storage, most merge logic has been removed.
Reference tables (fixtures, standings, teams, transfers, players) now write a
fresh complete snapshot on every run — no cross-run merging needed.

The two functions that remain:

1. merge_rounds_season_blocks — still used WITHIN a single run to assemble
   round names from multiple seasons into one payload before writing. This is
   not cross-run merging; it is building the run's snapshot from multiple API
   calls made in the same session.

2. merge_fanout_batched — used by the per-fixture fanout tables (lineups,
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


def _rounds_legacy_flat(payload: dict | None) -> bool:
    """Return True if the payload uses the old flat-list format (pre-season-block migration)."""
    r = (payload or {}).get("response") or []
    if not r:
        return False
    return isinstance(r[0], str)


def merge_rounds_season_blocks(
    existing: dict | None,
    season: int,
    rounds_pl: dict,
) -> dict:
    """Assemble round names from multiple seasons into a single payload.

    The API returns a flat list of round name strings for one season at a time.
    This function wraps each season's list in a {season, rounds} block and
    merges them together so the final payload covers all seasons fetched in
    this run.

    Note: 'existing' here refers to the payload accumulated so far WITHIN this
    run (starting as None on the first season). It is NOT the prior BigQuery row —
    we no longer read prior rows for reference tables. Each run builds a fresh
    complete snapshot from the API responses fetched that day.

    Legacy flat-list payloads (written before this format was introduced) are
    detected and discarded on first write rather than corrupting the merge.
    """
    raw_names = rounds_pl.get("response") or []
    block = {"season": int(season), "rounds": list(raw_names)}

    by_s: dict[int, dict] = {}
    ex = existing or {}
    if not _rounds_legacy_flat(ex):
        for blk in ex.get("response") or []:
            if isinstance(blk, dict) and blk.get("season") is not None:
                try:
                    by_s[int(blk["season"])] = blk
                except (TypeError, ValueError):
                    continue

    by_s[int(season)] = block
    resp = [by_s[s] for s in sorted(by_s.keys())]
    out = {
        k: v
        for k, v in rounds_pl.items()
        if k not in ("response", "errors", "results", "paging")
    }
    out["response"] = resp
    out["errors"] = list(rounds_pl.get("errors") or [])
    out["results"] = len(resp)
    out["paging"] = {"current": 1, "total": 1}
    return out
