"""Fixture ordering, fanout budgeting, coverage flags, and /players squad pulls.

'Fanout' refers to the per-fixture HTTP bundle: for every finished fixture we
fetch lineups, events, statistics, player ratings, and predictions — five API
calls per match. This module controls which fixtures get fetched and in what order,
respecting the daily API quota.

Coverage flags (from GET /leagues) tell us which endpoints a competition supports.
They are read once per run for the reference season (the latest season ingested)
and applied to all fixtures. See fixture_fanout_load.py for how finished fixtures
override the stats flag when the reference season is upcoming.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from .bq import load_json_to_bq
from .config import DATASET_ID, GCP_PROJECT_ID, _env_int, raw_league_table
from .errors_quota import append_api_errors, _last_requests_remaining
from .http_client import fetch_merged_paged


def team_ids_for_league(
    headers: dict,
    league_id: int,
    season: int,
    errors: list[str] | None = None,
) -> set[int]:
    """Bootstrap team IDs when fixtures return none (see API-Football /teams docs)."""
    data = fetch_merged_paged(
        "/teams",
        headers,
        {"league": league_id, "season": season},
        paginate=False,
    )
    if errors is not None:
        append_api_errors(data, f"teams league_id={league_id}", errors)
    ids: set[int] = set()
    for item in data.get("response", []):
        team = item.get("team") or {}
        tid = team.get("id")
        if tid:
            ids.add(int(tid))
    return ids


def _fixture_fanout_http_estimate() -> int:
    """
    HTTP calls per fixture for the detailed bundle: events, statistics, lineups,
    ``/fixtures/players``, and ``/predictions``.
    """
    return 5


def _bool_at(coverage: dict, *path: str, default: bool = True) -> bool:
    cur: object = coverage
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
    return bool(cur) if isinstance(cur, bool) else default


def _coverage_for_season(leagues_envelope: dict, season: int) -> dict[str, bool]:
    """Extract API coverage flags for a specific season from the /leagues catalog response.

    The API declares per-season which endpoints it supports (e.g. lineups, statistics).
    We read these to avoid spending quota on endpoints that will always return empty.
    Unknown or missing paths default to True — better to attempt and get an empty
    response than to silently skip an endpoint that exists.

    Important: these flags reflect the declared season, which is always the reference
    (latest) season. For competitions with an upcoming reference season the stats flag
    may be false even though prior seasons have stats. fixture_fanout_load.py handles
    this by always attempting stats for finished fixtures regardless of this flag.
    """
    cov: dict = {}
    try:
        for league_entry in leagues_envelope.get("response") or []:
            for s in league_entry.get("seasons") or []:
                if int(s.get("year") or -1) != int(season):
                    continue
                raw = s.get("coverage")
                if isinstance(raw, dict):
                    cov = raw
                    break
            if cov:
                break
    except (TypeError, ValueError):
        pass

    def b(*path: str) -> bool:
        return _bool_at(cov, *path, default=True) if cov else True

    return {
        "standings": b("standings"),
        "injuries": b("injuries"),
        "predictions": b("predictions"),
        "fixture_events": b("fixtures", "events"),
        "fixture_lineups": b("fixtures", "lineups"),
        "fixture_statistics": b("fixtures", "statistics_fixtures"),
        "fixture_players": b("fixtures", "statistics_players"),
    }


def _fixture_kickoff_by_id(fixtures_response: list) -> dict[int, date]:
    """Map fixture id → kickoff date (UTC calendar day) from ``/fixtures`` response rows."""
    out: dict[int, date] = {}
    for item in fixtures_response or []:
        fx = item.get("fixture") or {}
        fid = fx.get("id")
        if not fid:
            continue
        raw_d = fx.get("date")
        if isinstance(raw_d, str) and len(raw_d) >= 10:
            try:
                out[int(fid)] = date.fromisoformat(raw_d[:10])
            except ValueError:
                continue
    return out


def _chronological_fixture_ids(fixture_ids: set[int], by_id: dict[int, date]) -> list[int]:
    return sorted(fixture_ids, key=lambda i: (by_id.get(i, date.max), i))


def _upcoming_first_fixture_order(
    chrono: list[int],
    by_id: dict[int, date],
) -> list[int]:
    """Place fixtures in ``[today, today+horizon]`` first (kickoff order), then the rest."""
    today = datetime.utcnow().date()
    horizon = today + timedelta(days=_env_int("API_FOOTBALL_FRESH_HORIZON_DAYS", 14))
    upcoming: list[int] = []
    seen: set[int] = set()
    for fid in chrono:
        d = by_id.get(fid)
        if d is not None and today <= d <= horizon:
            upcoming.append(fid)
            seen.add(fid)
    rest = [fid for fid in chrono if fid not in seen]
    return upcoming + rest


def _read_fanout_cursor(client: bigquery.Client, league_code: str) -> int:
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{raw_league_table(league_code, 'INGEST_CURSOR')}"
    try:
        client.get_table(table_id)
    except NotFound:
        return 0
    try:
        job = client.query(
            f"SELECT fanout_offset FROM `{table_id}` ORDER BY updated_utc DESC NULLS LAST LIMIT 1"
        )
        rows = list(job.result())
        if not rows:
            return 0
        row = rows[0]
        try:
            return int(row["fanout_offset"])
        except (KeyError, TypeError, ValueError, IndexError):
            try:
                return int(row[0])
            except (TypeError, ValueError, IndexError):
                return 0
    except Exception:
        return 0


def _write_fanout_cursor(
    client: bigquery.Client, league_code: str, new_offset: int, fixture_total: int
) -> None:
    payload = {
        "league_code": league_code,
        "fanout_offset": new_offset,
        "fixture_total": fixture_total,
        "updated_utc": datetime.utcnow().isoformat() + "Z",
    }
    load_json_to_bq(
        client,
        raw_league_table(league_code, "INGEST_CURSOR"),
        payload,
        as_json_payload=True,
    )


def _fanout_fixture_order(
    client: bigquery.Client,
    fixtures_response: list,
    fixture_ids: set[int],
    league_code: str,
    errors: list[str],
) -> tuple[list[int], list[int], int | None]:
    """
    Build the fixture list fed into ``_budgeted_fixture_fanout_ids``.

    Returns ``(ordered_for_budget, chronological_ids, cursor_start_or_none)``.
    ``cursor_start`` is set only for ``API_FOOTBALL_FANOUT_PRIORITY=cursor`` so the caller
    can advance the stored offset after HTTP work.
    """
    by_id = _fixture_kickoff_by_id(fixtures_response)
    chrono = _chronological_fixture_ids(fixture_ids, by_id)
    pri = os.getenv("API_FOOTBALL_FANOUT_PRIORITY", "upcoming").strip().lower()
    if pri in ("season_chrono", "chronological", "chrono"):
        return chrono, chrono, None
    if pri == "cursor":
        off = _read_fanout_cursor(client, league_code)
        tail = chrono[off:] if chrono else []
        return tail, chrono, off
    # Default: next-match-window first (freshness on a free-tier budget).
    return _upcoming_first_fixture_order(chrono, by_id), chrono, None


def _budgeted_fixture_fanout_ids(
    ordered_fixture_ids: list[int],
    team_ids: set[int],
    league_code: str,
    errors: list[str],
) -> list[int]:
    """Return the fixtures that fit within today's remaining API quota.

    We estimate 5 HTTP calls per fixture (lineups, events, stats, players, predictions)
    and reserve a block for /players squad pagination. The daily remaining call count
    comes from the x-ratelimit-requests-remaining response header, updated after each
    HTTP call. If the header has not yet been seen (first call of the day), we fall back
    to a soft cap controlled by API_FOOTBALL_FANOUT_SOFT_CAP_FIXTURES_NO_HEADER.

    The paid/full ingest profile sets the soft cap to -1 (unlimited) and relies entirely
    on the header-based budget. The free-tier default is 6 fixtures per run.
    """
    sorted_ids = list(ordered_fixture_ids)
    if not sorted_ids:
        return []

    raw = os.getenv("API_FOOTBALL_LINEUPS_MAX_FIXTURES", "").strip()
    explicit: int | None
    if raw == "":
        explicit = None
    else:
        explicit = max(0, int(raw))

    # Reserve only a bounded amount for /players. Over-reserving by team_count * page_cap
    # can starve fixture fanout entirely and leave statistics payloads empty.
    buf = _env_int("API_FOOTBALL_QUOTA_BUFFER", 5)
    players_reserve_calls = _env_int("API_FOOTBALL_PLAYERS_RESERVE_CALLS", 20)
    if os.getenv("API_FOOTBALL_SKIP_PLAYERS", "").strip().lower() in ("1", "true", "yes"):
        reserve_players = buf
    else:
        reserve_players = max(buf, players_reserve_calls + buf)
    cpf = _fixture_fanout_http_estimate()

    if _last_requests_remaining is not None:
        budget = max(0, _last_requests_remaining - reserve_players)
        max_fixtures = budget // cpf if cpf else 0
        cap = min(len(sorted_ids), max_fixtures)
        if explicit is not None:
            cap = min(cap, explicit)
        # After a long run the daily header can dip below the pessimistic /players reserve, which
        # would yield zero fanout fixtures. Fall back to the soft cap so upcoming data still loads.
        if cap == 0 and sorted_ids:
            soft_fb = _env_int("API_FOOTBALL_FANOUT_SOFT_CAP_FIXTURES_NO_HEADER", 6)
            if soft_fb >= 0:
                cap = min(len(sorted_ids), soft_fb)
            if explicit is not None:
                cap = min(cap, explicit)
            errors.append(
                f"fixture_fanout {league_code}: quota header left no budget after ~{reserve_players} "
                f"reserved for /players; using soft cap {cap} of {len(sorted_ids)} fixtures instead"
            )
        elif cap < len(sorted_ids):
            errors.append(
                f"fixture_fanout {league_code}: capped to {cap} of {len(sorted_ids)} fixtures "
                f"(~{cpf} HTTP/fixture; reserve ~{reserve_players} for /players)"
            )
        return sorted_ids[:cap]

    soft = _env_int("API_FOOTBALL_FANOUT_SOFT_CAP_FIXTURES_NO_HEADER", 6)
    cap = len(sorted_ids)
    if explicit is not None:
        cap = min(cap, explicit)
    elif soft >= 0:
        cap = min(cap, soft)
    if cap < len(sorted_ids):
        errors.append(
            f"fixture_fanout {league_code}: capped to {cap} of {len(sorted_ids)} fixtures "
            f"(no daily quota header yet; soft cap {soft}; set API_FOOTBALL_FANOUT_SOFT_CAP_FIXTURES_NO_HEADER=-1 to disable)"
        )
    return sorted_ids[:cap]


def players_response_for_team(
    headers: dict,
    team_id: int,
    season: int,
    errors: list[str] | None = None,
    *,
    error_context: str = "",
) -> list:
    """All /players pages for team+season (API paginates; free tier caps ``page`` — see env)."""
    max_page = _env_int("API_FOOTBALL_PLAYERS_MAX_PAGE", 3)
    data = fetch_merged_paged(
        "/players",
        headers,
        {"team": team_id, "season": season},
        max_pages=max_page,
    )
    if errors is not None:
        ctx = error_context or f"players team_id={team_id}"
        append_api_errors(data, ctx, errors)
    return list(data.get("response") or [])
