"""Per-fixture HTTP fanout + batched RAW_* tables (lineups, events, stats, …)."""

from __future__ import annotations

import os

from .. import errors_quota
from ..bq import load_json_to_bq, read_latest_payload_json
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


def _batched_shell(league_code: str) -> dict[str, dict]:
    base = {"league_code": league_code, "response": []}
    return {
        "lineups": dict(base),
        "events": dict(base),
        "fx_stats": dict(base),
        "fx_players": dict(base),
        "preds": dict(base),
    }


def _persist_fanout_tables(
    ctx: PipelineContext,
    league_code: str,
    shells: dict[str, dict],
    valid_fixture_ids: set[int],
) -> None:
    specs = (
        ("lineups", "LINEUPS", "lineups BQ"),
        ("events", "FIXTURE_EVENTS", "fixture_events BQ"),
        ("fx_stats", "FIXTURE_STATISTICS", "fixture_statistics BQ"),
        ("fx_players", "FIXTURE_PLAYERS", "fixture_players BQ"),
        ("preds", "PREDICTIONS", "predictions BQ"),
    )
    for key, entity, err_prefix in specs:
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
            ctx.errors.append(f"{err_prefix} {league_code}: {e}")


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
    fanout_ids = _budgeted_fixture_fanout_ids(
        ordered_fanout, team_ids, league_code, ctx.errors
    )
    sh = _batched_shell(league_code)

    for fixture_id in fanout_ids:
        if errors_quota._http_quota_exhausted:
            break
        if cov["fixture_lineups"]:
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
        if cov["fixture_events"]:
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
        if cov["fixture_statistics"]:
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
        if cov["fixture_players"]:
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
        if cov["predictions"]:
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
