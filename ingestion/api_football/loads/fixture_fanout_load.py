"""Per-fixture HTTP fanout + batched RAW_* tables (lineups, events, stats, …).

Selection is **completeness-driven**: before spending any quota, read the current
merged payloads for the five fanout tables and skip fixture ids (per endpoint)
that are already covered. A run therefore only pays for work that actually
advances completeness, which is what makes multi-day convergence monotonic
without any operator-facing knob.
"""

from __future__ import annotations

import os

from .. import errors_quota
from ..bq import load_json_to_bq, read_latest_payload_json
from ..completeness import _fixture_ids_from_fanout_payload
from ..config import raw_league_table
from ..errors_quota import append_api_errors
from ..fanout import (
    _budgeted_fixture_fanout_ids,
    _fanout_fixture_order,
    _write_fanout_cursor,
)
from ..http_client import fetch_json
from ..payload_merge import merge_fanout_batched
from .context import PipelineContext

# (shell_key, RAW entity suffix, coverage-flag key on the /leagues coverage dict)
_FANOUT_ENTITY_KEYS: tuple[tuple[str, str, str], ...] = (
    ("lineups", "LINEUPS", "fixture_lineups"),
    ("events", "FIXTURE_EVENTS", "fixture_events"),
    ("fx_stats", "FIXTURE_STATISTICS", "fixture_statistics"),
    ("fx_players", "FIXTURE_PLAYERS", "fixture_players"),
    ("preds", "PREDICTIONS", "predictions"),
)


def _batched_shell(league_code: str) -> dict[str, dict]:
    base = {"league_code": league_code, "response": []}
    return {key: dict(base) for key, _entity, _cov_key in _FANOUT_ENTITY_KEYS}


def _already_covered_per_entity(
    ctx: PipelineContext,
    league_code: str,
) -> dict[str, set[int]]:
    """Read merged fanout payloads once and return ``{shell_key: set(fixture_ids)}``."""
    covered: dict[str, set[int]] = {}
    for key, entity, _cov_key in _FANOUT_ENTITY_KEYS:
        tbl = raw_league_table(league_code, entity)
        try:
            prior = read_latest_payload_json(ctx.client, tbl)
        except Exception as e:
            ctx.errors.append(f"fanout_covered {league_code} {entity}: {e}")
            prior = None
        required_key = "statistics" if key == "fx_stats" else None
        covered[key] = _fixture_ids_from_fanout_payload(
            prior,
            required_payload_key=required_key,
        )
    return covered


def _finished_fixture_ids(fixtures_response: list[dict]) -> set[int]:
    finished: set[int] = set()
    for row in fixtures_response or []:
        fixture = row.get("fixture") or {}
        status_short = ((fixture.get("status") or {}).get("short") or "").strip().upper()
        if status_short not in {"FT", "AET", "PEN"}:
            continue
        fixture_id = fixture.get("id")
        if fixture_id is None:
            continue
        try:
            finished.add(int(fixture_id))
        except (TypeError, ValueError):
            continue
    return finished


def _fixture_needs_any_endpoint(
    fixture_id: int,
    covered: dict[str, set[int]],
    cov: dict[str, bool],
) -> bool:
    for key, _entity, cov_key in _FANOUT_ENTITY_KEYS:
        if not cov.get(cov_key, True):
            continue
        if fixture_id not in covered[key]:
            return True
    return False


def _persist_fanout_tables(
    ctx: PipelineContext,
    league_code: str,
    shells: dict[str, dict],
    valid_fixture_ids: set[int],
) -> None:
    for key, entity, _cov_key in _FANOUT_ENTITY_KEYS:
        try:
            tbl = raw_league_table(league_code, entity)
            prior = read_latest_payload_json(ctx.client, tbl)
            merged = merge_fanout_batched(
                prior,
                shells[key],
                league_code=league_code,
                valid_fixture_ids=valid_fixture_ids,
            )
            load_json_to_bq(
                ctx.client,
                tbl,
                merged,
                as_json_payload=True,
            )
            ctx.add_loaded(1)
        except Exception as e:
            ctx.errors.append(f"{entity.lower()} BQ {league_code}: {e}")


def run_fixture_fanout_and_persist(
    ctx: PipelineContext,
    league_code: str,
    fixtures_merged: dict,
    fixture_ids: set[int],
    team_ids: set[int],
    cov: dict[str, bool],
) -> None:
    ordered_fanout, chrono_all, cursor_start = _fanout_fixture_order(
        ctx.client,
        fixtures_merged.get("response", []),
        fixture_ids,
        league_code,
        ctx.errors,
    )

    covered = _already_covered_per_entity(ctx, league_code)
    ordered_missing = [
        fid for fid in ordered_fanout if _fixture_needs_any_endpoint(fid, covered, cov)
    ]
    missing_index = {fixture_id: idx for idx, fixture_id in enumerate(ordered_missing)}
    finished_fixture_ids = _finished_fixture_ids(fixtures_merged.get("response", []))
    ordered_missing = sorted(
        ordered_missing,
        key=lambda fixture_id: (
            0
            if (
                cov.get("fixture_statistics", True)
                and fixture_id in finished_fixture_ids
                and fixture_id not in covered["fx_stats"]
            )
            else 1,
            missing_index[fixture_id],
        ),
    )

    print(
        f"[api-football] fanout_selection league={league_code} "
        f"target={len(fixture_ids)} "
        f"already_complete={len(fixture_ids) - len(ordered_missing)} "
        f"missing_any_endpoint={len(ordered_missing)}"
    )

    fanout_ids = _budgeted_fixture_fanout_ids(
        ordered_missing, team_ids, league_code, ctx.errors
    )
    sh = _batched_shell(league_code)

    for fixture_id in fanout_ids:
        if errors_quota._http_quota_exhausted:
            break
        if cov["fixture_lineups"] and fixture_id not in covered["lineups"]:
            try:
                lineups = fetch_json(
                    "/fixtures/lineups",
                    headers=ctx.headers,
                    params={"fixture": fixture_id},
                )
                append_api_errors(
                    lineups, f"lineups {league_code} fixture {fixture_id}", ctx.errors
                )
                sh["lineups"]["response"].append(
                    {"fixture_id": fixture_id, "lineups": lineups.get("response", [])}
                )
            except Exception as e:
                ctx.errors.append(f"lineups {league_code} fixture {fixture_id}: {e}")
        if cov["fixture_events"] and fixture_id not in covered["events"]:
            try:
                ev = fetch_json(
                    "/fixtures/events",
                    headers=ctx.headers,
                    params={"fixture": fixture_id},
                )
                append_api_errors(
                    ev, f"fixtures/events {league_code} fixture {fixture_id}", ctx.errors
                )
                sh["events"]["response"].append(
                    {"fixture_id": fixture_id, "events": ev.get("response", [])}
                )
            except Exception as e:
                ctx.errors.append(f"fixtures/events {league_code} fixture {fixture_id}: {e}")
        # Always fetch stats for finished fixtures: coverage flags reflect the reference
        # (latest) season, which for multi-season competitions like WC can be an upcoming
        # edition whose API coverage says statistics_fixtures=false — but completed
        # fixtures from prior editions do have stats available.
        if (cov["fixture_statistics"] or fixture_id in finished_fixture_ids) and fixture_id not in covered["fx_stats"]:
            try:
                fxs = fetch_json(
                    "/fixtures/statistics",
                    headers=ctx.headers,
                    params={"fixture": fixture_id},
                )
                append_api_errors(
                    fxs,
                    f"fixtures/statistics {league_code} fixture {fixture_id}",
                    ctx.errors,
                )
                sh["fx_stats"]["response"].append(
                    {"fixture_id": fixture_id, "statistics": fxs.get("response", [])}
                )
            except Exception as e:
                ctx.errors.append(
                    f"fixtures/statistics {league_code} fixture {fixture_id}: {e}"
                )
        if cov["fixture_players"] and fixture_id not in covered["fx_players"]:
            try:
                fxp = fetch_json(
                    "/fixtures/players",
                    headers=ctx.headers,
                    params={"fixture": fixture_id},
                )
                append_api_errors(
                    fxp,
                    f"fixtures/players {league_code} fixture {fixture_id}",
                    ctx.errors,
                )
                sh["fx_players"]["response"].append(
                    {"fixture_id": fixture_id, "players": fxp.get("response", [])}
                )
            except Exception as e:
                ctx.errors.append(
                    f"fixtures/players {league_code} fixture {fixture_id}: {e}"
                )
        if cov["predictions"] and fixture_id not in covered["preds"]:
            try:
                pr = fetch_json(
                    "/predictions",
                    headers=ctx.headers,
                    params={"fixture": fixture_id},
                )
                append_api_errors(
                    pr, f"predictions {league_code} fixture {fixture_id}", ctx.errors
                )
                sh["preds"]["response"].append(
                    {"fixture_id": fixture_id, "predictions": pr.get("response", [])}
                )
            except Exception as e:
                ctx.errors.append(f"predictions {league_code} fixture {fixture_id}: {e}")

    pri = os.getenv("API_FOOTBALL_FANOUT_PRIORITY", "upcoming").strip().lower()
    if pri == "cursor" and chrono_all and cursor_start is not None:
        try:
            new_off = (cursor_start + len(fanout_ids)) % max(len(chrono_all), 1)
            _write_fanout_cursor(ctx.client, league_code, new_off, len(chrono_all))
            ctx.add_loaded(1)
        except Exception as e:
            ctx.errors.append(f"ingest_cursor {league_code}: {e}")

    _persist_fanout_tables(ctx, league_code, sh, fixture_ids)
