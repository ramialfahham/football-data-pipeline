"""Fixture scheduling: coverage flags, ordering, quota budgeting, and squad HTTP pulls.

'Fanout' refers to the per-fixture HTTP bundle fetched in loads/fanout.py. This module
controls which fixtures are eligible and in what order, without making any HTTP calls
itself (except for the squad /players helper used by loads/squads.py).

Five concerns live here:

1. Coverage flags — reads GET /leagues response to determine which endpoints a
   competition supports (lineups, events, stats, players). Flags come from the
   reference (latest) season; loads/fanout.py overrides the stats flag for finished
   fixtures because an upcoming reference season may falsely report stats=false.

2. Fixture ordering — three strategies: upcoming-first (default), chronological,
   or cursor-based round-robin. The cursor is persisted in BQ so runs pick up where
   the previous left off (useful for large historical backlogs).

3. Quota budgeting — estimates HTTP calls per fixture (4) and reserves a block for
   /players squad pagination. The daily remaining call count comes from API response
   headers updated after each fetch_json call.

4. Global completeness-driven fanout — CompetitionFanoutInput + build_global_fanout_queue
   implement a two-tier priority queue across all competitions: finished fixtures with
   missing data are ordered oldest-first (fills historical gaps); upcoming fixtures are
   ordered nearest-first (keeps app fresh). The queue is budget-capped globally so quota
   is never wasted on competitions that are already complete.

5. Squad HTTP pulls — players_response_for_team fetches all /players pages for a
   given team×season, respecting free-tier page caps.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from .bigquery import load_json_to_bq
from .settings import DATASET_ID, GCP_PROJECT_ID, _env_int, raw_league_table
from .quota import append_api_errors, _last_requests_remaining
from .http_client import fetch_merged_paged, result_is_complete

# (shell_key, RAW entity suffix, coverage-flag key on the /leagues coverage dict)
# Defined here so fixture_scheduling.py can gate the fanout queue without importing loads/.
# API predictions are not ingested (we build our own), so there is no preds endpoint.
_FANOUT_ENTITY_KEYS: tuple[tuple[str, str, str], ...] = (
    ("lineups", "LINEUPS", "fixture_lineups"),
    ("events", "FIXTURE_EVENTS", "fixture_events"),
    ("fx_stats", "FIXTURE_STATISTICS", "fixture_statistics"),
    ("fx_players", "FIXTURE_PLAYERS", "fixture_players"),
)


def _fixture_needs_any_endpoint(
    fixture_id: int,
    covered: dict[str, set[int]],
    cov: dict[str, bool],
    finished_fixture_ids: set[int],
) -> bool:
    """Return True if this fixture is missing data for at least one enabled endpoint.

    For statistics, finished fixtures are always considered eligible regardless of
    the coverage flag. Coverage flags come from the reference (latest) season; for
    competitions with an upcoming reference season (e.g. WC 2026) the stats flag
    may be false even though prior seasons have data — we must not gate finished
    fixtures out of the fanout loop based on that.
    """
    for key, _entity, cov_key in _FANOUT_ENTITY_KEYS:
        effective_cov = cov.get(cov_key, True) or (
            cov_key == "fixture_statistics" and fixture_id in finished_fixture_ids
        )
        if not effective_cov:
            continue
        if fixture_id not in covered[key]:
            return True
    return False


@dataclass
class CompetitionFanoutInput:
    """Per-competition inputs for the global fanout queue builder."""
    league_code: str
    fixture_ids: set[int]
    covered: dict[str, set[int]]       # shell_key → set of already-covered fixture_ids
    cov: dict[str, bool]               # coverage flags from /leagues (which endpoints exist)
    kickoff_by_id: dict[int, date]
    finished_fixture_ids: set[int] = field(default_factory=set)


def build_global_fanout_queue(
    inputs: list[CompetitionFanoutInput],
) -> list[tuple[str, int]]:
    """Build a globally-ordered fanout queue across all competitions.

    Two-tier priority:
    - Tier 1: finished fixtures (FT/AET/PEN) missing any endpoint, ordered oldest kickoff first.
      Fills historical gaps systematically — every run makes guaranteed forward progress.
    - Tier 2: upcoming/unplayed fixtures missing any endpoint, ordered nearest kickoff first.
      Keeps app data fresh for the next matchday.

    Returns list of (league_code, fixture_id) pairs. Budget capping is done by the caller
    via _budgeted_global_fanout_ids so this function stays pure and testable.
    """
    finished_missing: list[tuple[date, str, int]] = []
    upcoming_missing: list[tuple[date, str, int]] = []

    for inp in inputs:
        for fid in inp.fixture_ids:
            if not _fixture_needs_any_endpoint(fid, inp.covered, inp.cov, inp.finished_fixture_ids):
                continue
            kickoff = inp.kickoff_by_id.get(fid, date.max)
            if fid in inp.finished_fixture_ids:
                finished_missing.append((kickoff, inp.league_code, fid))
            else:
                upcoming_missing.append((kickoff, inp.league_code, fid))

    finished_missing.sort(key=lambda x: (x[0], x[1], x[2]))
    upcoming_missing.sort(key=lambda x: (x[0], x[1], x[2]))

    queue: list[tuple[str, int]] = []
    queue.extend((lc, fid) for _, lc, fid in finished_missing)
    queue.extend((lc, fid) for _, lc, fid in upcoming_missing)
    return queue


def _budgeted_global_fanout_ids(
    queue: list[tuple[str, int]],
    all_team_ids: set[int],
    errors: list[str],
) -> list[tuple[str, int]]:
    """Apply the daily API quota budget to the global fanout queue.

    Works identically to _budgeted_fixture_fanout_ids but operates on the cross-competition
    queue rather than a single competition's list. Budget is computed once globally so quota
    is shared fairly across all competitions rather than being allocated per-competition.
    """
    if not queue:
        return []

    raw = os.getenv("API_FOOTBALL_LINEUPS_MAX_FIXTURES", "").strip()
    explicit: int | None = None if raw == "" else max(0, int(raw))

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
        cap = min(len(queue), max_fixtures)
        if explicit is not None:
            cap = min(cap, explicit)
        if cap == 0 and queue:
            soft_fb = _env_int("API_FOOTBALL_FANOUT_SOFT_CAP_FIXTURES_NO_HEADER", 6)
            if soft_fb >= 0:
                cap = min(len(queue), soft_fb)
            if explicit is not None:
                cap = min(cap, explicit)
            errors.append(
                f"global_fanout: quota header left no budget after ~{reserve_players} "
                f"reserved for /players; using soft cap {cap} of {len(queue)} fixtures instead"
            )
        elif cap < len(queue):
            errors.append(
                f"global_fanout: capped to {cap} of {len(queue)} fixtures "
                f"(~{cpf} HTTP/fixture; reserve ~{reserve_players} for /players)"
            )
        return queue[:cap]

    soft = _env_int("API_FOOTBALL_FANOUT_SOFT_CAP_FIXTURES_NO_HEADER", 6)
    cap = len(queue)
    if explicit is not None:
        cap = min(cap, explicit)
    elif soft >= 0:
        cap = min(cap, soft)
    if cap < len(queue):
        errors.append(
            f"global_fanout: capped to {cap} of {len(queue)} fixtures "
            f"(no daily quota header yet; soft cap {soft}; set API_FOOTBALL_FANOUT_SOFT_CAP_FIXTURES_NO_HEADER=-1 to disable)"
        )
    return queue[:cap]


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
    and ``/fixtures/players``. (API predictions are not ingested.)
    """
    return 4


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
    may be false even though prior seasons have stats. loads/fanout.py handles
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

    We estimate 4 HTTP calls per fixture (lineups, events, stats, players)
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
) -> tuple[list, bool]:
    """All /players pages for team+season (API paginates; free tier caps ``page`` — see env).

    Returns ``(rows, complete)``. ``complete`` is False when the provider returned a body-level
    error (the per-minute rate limit arrives as HTTP 200 with the error in the body) or the run's
    quota flag cut pagination short. In that case ``rows`` may be empty OR partial while looking
    like a successful response, and the caller MUST NOT let it supersede stored data (#896).
    """
    max_page = _env_int("API_FOOTBALL_PLAYERS_MAX_PAGE", 3)
    data = fetch_merged_paged(
        "/players",
        headers,
        {"team": team_id, "season": season},
        max_pages=max_page,
    )
    # Evaluated before any further fetch: the quota flag latches for the rest of the run.
    complete = result_is_complete(data)
    if errors is not None:
        ctx = error_context or f"players team_id={team_id}"
        append_api_errors(data, ctx, errors)
    return list(data.get("response") or []), complete


def transfers_response_for_team(
    headers: dict,
    team_id: int,
    errors: list[str] | None = None,
    *,
    error_context: str = "",
) -> list:
    """All /transfers for a team (every player who moved in/out). Not season-scoped —
    one call returns the team's full transfer history. Fetching by team returns each
    move twice (once per involved team); the base model dedups.

    paginate=False: /transfers rejects the `page` param (like /teams and /standings —
    'The Page field do not exist.') and returns empty when it is sent, so we send a single
    `team=` call (verified: returns the team's full move list in one response)."""
    data = fetch_merged_paged(
        "/transfers",
        headers,
        {"team": team_id},
        paginate=False,
    )
    if errors is not None:
        ctx = error_context or f"transfers team_id={team_id}"
        append_api_errors(data, ctx, errors)
    return list(data.get("response") or [])


def squads_response_for_team(
    headers: dict,
    team_id: int,
    errors: list[str] | None = None,
    *,
    error_context: str = "",
) -> list:
    """Current squad for a team from /players/squads (id, name, age, number, position, photo).

    One call returns the whole squad. paginate=False: /players/squads is single-page for a
    `team=` query (verified team=157 → paging.total=1). Distinct from `players_response_for_team`
    (which pulls /players per team×season into RAW_APIF_PLAYERS); this is the cheaper current-squad
    endpoint and carries the shirt number."""
    data = fetch_merged_paged(
        "/players/squads",
        headers,
        {"team": team_id},
        paginate=False,
    )
    if errors is not None:
        ctx = error_context or f"squads team_id={team_id}"
        append_api_errors(data, ctx, errors)
    return list(data.get("response") or [])


def profiles_response_for_player(
    headers: dict,
    player_id: int,
    errors: list[str] | None = None,
    *,
    error_context: str = "",
) -> list:
    """Bio for one player from /players/profiles?player= (name, DOB, birthplace, nationality,
    height, weight, number, position, photo).

    paginate=False: a `player=` query returns one page (verified player=5 → paging.total=1). The
    page-keyed directory form is far thinner; the per-player form carries the full bio."""
    data = fetch_merged_paged(
        "/players/profiles",
        headers,
        {"player": player_id},
        paginate=False,
    )
    if errors is not None:
        ctx = error_context or f"profiles player_id={player_id}"
        append_api_errors(data, ctx, errors)
    return list(data.get("response") or [])


def player_teams_response_for_player(
    headers: dict,
    player_id: int,
    errors: list[str] | None = None,
    *,
    error_context: str = "",
) -> list:
    """Career club/national history for one player from /players/teams?player= — a list of
    {team, seasons[]} entries.

    paginate=False: a `player=` query returns one page (verified player=5 → paging.total=1)."""
    data = fetch_merged_paged(
        "/players/teams",
        headers,
        {"player": player_id},
        paginate=False,
    )
    if errors is not None:
        ctx = error_context or f"player_teams player_id={player_id}"
        append_api_errors(data, ctx, errors)
    return list(data.get("response") or [])
