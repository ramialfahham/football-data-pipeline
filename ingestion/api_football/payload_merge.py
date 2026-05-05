"""Merge prior BigQuery payloads with this-run API data (cross-run completeness).

Every raw table holds a single JSON payload row (the "merge-on-write" pattern).
Before writing, we read the existing payload from BQ, merge it with the new API
data, and write the result back. This makes each run additive: a fixture fetched
on Monday survives Tuesday's run even if the API doesn't return it again.

Each merge function defines its own deduplication key (fixture_id, team+season,
player_id, etc.) so incoming data overwrites stale entries on the same key while
preserving everything else.
"""

from __future__ import annotations


def merge_fanout_batched(
    existing: dict | None,
    incoming: dict,
    *,
    league_code: str,
    valid_fixture_ids: set[int] | None,
) -> dict:
    """Merge per-fixture fanout blocks (lineups, events, stats, players, predictions).

    Keyed by fixture_id; incoming overwrites existing for the same id. Entries
    whose fixture_id is not in valid_fixture_ids are pruned — this prevents stale
    rows from cancelled or removed fixtures accumulating indefinitely.
    """
    by_id: dict[int, dict] = {}
    for row in (existing or {}).get("response") or []:
        fid = row.get("fixture_id")
        if fid is not None:
            by_id[int(fid)] = row
    for row in incoming.get("response") or []:
        fid = row.get("fixture_id")
        if fid is not None:
            by_id[int(fid)] = row
    if valid_fixture_ids is not None:
        by_id = {k: v for k, v in by_id.items() if k in valid_fixture_ids}
    return {"league_code": league_code, "response": [by_id[k] for k in sorted(by_id.keys())]}


def merge_players_squad(
    existing: dict | None,
    incoming: dict,
    *,
    league_code: str,
    valid_team_season: set[tuple[int, int]],
) -> dict:
    """Squad batch: blocks keyed by ``(team_id, season)``."""
    by_k: dict[tuple[int, int], dict] = {}
    for row in (existing or {}).get("response") or []:
        try:
            tid = int(row["team_id"])
            season = int(row["season"])
        except (KeyError, TypeError, ValueError):
            continue
        by_k[(tid, season)] = row
    for row in incoming.get("response") or []:
        try:
            tid = int(row["team_id"])
            season = int(row["season"])
        except (KeyError, TypeError, ValueError):
            continue
        by_k[(tid, season)] = row
    by_k = {k: v for k, v in by_k.items() if k in valid_team_season}
    return {"league_code": league_code, "response": [by_k[k] for k in sorted(by_k.keys())]}


def _fixture_id_from_match(item: dict) -> int | None:
    try:
        return int((item.get("fixture") or {}).get("id"))
    except (TypeError, ValueError):
        return None


def merge_fixtures_envelope(existing: dict | None, incoming: dict) -> dict:
    """Merge /fixtures responses across seasons and runs, keyed by fixture_id.

    Multi-season ingestion calls /fixtures once per season; this merges all
    seasons into a single payload so downstream code sees one unified fixture list.
    Incoming overwrites existing for the same fixture_id (status updates, reschedules).
    """
    by_id: dict[int, dict] = {}
    for it in (existing or {}).get("response") or []:
        fid = _fixture_id_from_match(it)
        if fid is not None:
            by_id[fid] = it
    for it in incoming.get("response") or []:
        fid = _fixture_id_from_match(it)
        if fid is not None:
            by_id[fid] = it
    resp = [by_id[k] for k in sorted(by_id.keys())]
    out = {k: v for k, v in incoming.items() if k not in ("response", "errors", "results", "paging")}
    out["response"] = resp
    out["errors"] = list(incoming.get("errors") or [])
    out["results"] = len(resp)
    out["paging"] = {"current": 1, "total": 1}
    return out


def _standing_season(item: dict) -> int | None:
    try:
        return int((item.get("league") or {}).get("season"))
    except (TypeError, ValueError):
        return None


def merge_standings_envelope(existing: dict | None, incoming: dict) -> dict:
    by_s: dict[int, dict] = {}
    for it in (existing or {}).get("response") or []:
        s = _standing_season(it)
        if s is not None:
            by_s[s] = it
    for it in incoming.get("response") or []:
        s = _standing_season(it)
        if s is not None:
            by_s[s] = it
    resp = [by_s[k] for k in sorted(by_s.keys())]
    out = {k: v for k, v in incoming.items() if k not in ("response", "errors", "results", "paging")}
    out["response"] = resp
    out["errors"] = list(incoming.get("errors") or [])
    out["results"] = len(resp)
    out["paging"] = {"current": 1, "total": 1}
    return out


def _team_row_key(item: dict) -> tuple[int, int] | None:
    try:
        tid = int((item.get("team") or {}).get("id"))
        season = int((item.get("league") or {}).get("season"))
        return (tid, season)
    except (TypeError, ValueError):
        return None


def merge_teams_envelope(existing: dict | None, incoming: dict) -> dict:
    by_k: dict[tuple[int, int], dict] = {}
    for it in (existing or {}).get("response") or []:
        k = _team_row_key(it)
        if k is not None:
            by_k[k] = it
    for it in incoming.get("response") or []:
        k = _team_row_key(it)
        if k is not None:
            by_k[k] = it
    resp = [by_k[k] for k in sorted(by_k.keys())]
    out = {k: v for k, v in incoming.items() if k not in ("response", "errors", "results", "paging")}
    out["response"] = resp
    out["errors"] = list(incoming.get("errors") or [])
    out["results"] = len(resp)
    out["paging"] = {"current": 1, "total": 1}
    return out


def _injury_key(item: dict) -> tuple | None:
    try:
        season = int((item.get("league") or {}).get("season"))
        pid = int((item.get("player") or {}).get("id"))
        tid = int((item.get("team") or {}).get("id"))
        fx = (item.get("fixture") or {}).get("id")
        fid = int(fx) if fx is not None else -1
        typ = str(item.get("type") or "")
        reason = str(item.get("reason") or "")
        return (season, pid, tid, fid, typ, reason)
    except (TypeError, ValueError):
        return None


def merge_injuries_envelope(existing: dict | None, incoming: dict) -> dict:
    by_k: dict[tuple, dict] = {}
    for it in (existing or {}).get("response") or []:
        k = _injury_key(it)
        if k is not None:
            by_k[k] = it
    for it in incoming.get("response") or []:
        k = _injury_key(it)
        if k is not None:
            by_k[k] = it
    resp = list(by_k.values())
    out = {k: v for k, v in incoming.items() if k not in ("response", "errors", "results", "paging")}
    out["response"] = resp
    out["errors"] = list(incoming.get("errors") or [])
    out["results"] = len(resp)
    out["paging"] = {"current": 1, "total": 1}
    return out


def _transfer_player_key(row: dict) -> int | None:
    try:
        return int((row.get("player") or {}).get("id"))
    except (TypeError, ValueError):
        return None


def merge_transfers_envelope(existing: dict | None, incoming: dict) -> dict:
    by_p: dict[int, dict] = {}
    for r in (existing or {}).get("response") or []:
        k = _transfer_player_key(r)
        if k is not None:
            by_p[k] = r
    for r in incoming.get("response") or []:
        k = _transfer_player_key(r)
        if k is not None:
            by_p[k] = r
    resp = [by_p[k] for k in sorted(by_p.keys())]
    meta = {k: v for k, v in incoming.items() if k not in ("response", "errors", "results", "paging")}
    out = dict(meta)
    out["response"] = resp
    out["errors"] = list(incoming.get("errors") or [])
    out["results"] = len(resp)
    out["paging"] = {"current": 1, "total": 1}
    return out


def _rounds_legacy_flat(payload: dict | None) -> bool:
    r = (payload or {}).get("response") or []
    if not r:
        return False
    el0 = r[0]
    return isinstance(el0, str)


def merge_rounds_season_blocks(
    existing: dict | None,
    season: int,
    rounds_pl: dict,
) -> dict:
    """Merge rounds per season into a list of {season, rounds} blocks.

    The API returns a flat list of round name strings per season call. We wrap
    each in a season-tagged block so multi-season payloads stay mergeable across
    runs. Legacy flat-list payloads (written before this format) are detected and
    discarded on first tagged write rather than corrupting the merge.
    """
    raw_names = rounds_pl.get("response") or []
    names: list = []
    for x in raw_names:
        if isinstance(x, str):
            names.append(x)
        elif isinstance(x, dict):
            names.append(x)
        else:
            names.append(x)
    block = {"season": int(season), "rounds": names}
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
    out = {k: v for k, v in rounds_pl.items() if k not in ("response", "errors", "results", "paging")}
    out["response"] = resp
    out["errors"] = list(rounds_pl.get("errors") or [])
    out["results"] = len(resp)
    out["paging"] = {"current": 1, "total": 1}
    return out
