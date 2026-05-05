"""Post-ingest checks: fanout coverage vs merged fixture list (for monitoring / alerts)."""

from __future__ import annotations

import json
import os
from typing import Any

from google.cloud import bigquery

from .bigquery import read_latest_payload_json
from .registry import selected_leagues_map
from .settings import raw_league_table

# Batched fanout raw entities (fixture_id blocks).
FANOUT_ENTITIES = (
    "LINEUPS",
    "FIXTURE_EVENTS",
    "FIXTURE_STATISTICS",
    "FIXTURE_PLAYERS",
    "PREDICTIONS",
)

# API-Football ``fixture.status.short`` codes where the match has concluded and
# per-fixture fanout data is expected to exist. Everything else (upcoming, in-play,
# cancelled, abandoned, postponed) is excluded from the completeness expected set:
# we cannot fetch lineups / events / stats for matches that never reached a final
# whistle, so counting them as missing would generate permanent false-negative alerts.
FINISHED_STATUS_SHORT = frozenset({"FT", "AET", "PEN"})


def _fixture_ids_from_fixtures_payload(
    payload: dict | None,
    *,
    statuses: frozenset[str] | None = None,
) -> set[int]:
    """Return fixture ids from a merged ``/fixtures`` payload.

    When ``statuses`` is provided, only fixtures whose ``fixture.status.short``
    is in the set are returned.
    """
    out: set[int] = set()
    for item in (payload or {}).get("response") or []:
        fx = item.get("fixture") or {}
        fid = fx.get("id")
        if fid is None:
            continue
        if statuses is not None:
            status_short = ((fx.get("status") or {}).get("short") or "").strip()
            if status_short not in statuses:
                continue
        try:
            out.add(int(fid))
        except (TypeError, ValueError):
            continue
    return out


def _fixture_ids_from_fanout_payload(
    payload: dict | None,
    *,
    required_payload_key: str | None = None,
) -> set[int]:
    out: set[int] = set()
    for row in (payload or {}).get("response") or []:
        fid = row.get("fixture_id")
        if required_payload_key is not None:
            endpoint_payload = row.get(required_payload_key)
            if not endpoint_payload:
                continue
        if fid is not None:
            try:
                out.add(int(fid))
            except (TypeError, ValueError):
                continue
    return out


def skip_completeness_check() -> bool:
    return os.getenv("API_FOOTBALL_SKIP_COMPLETENESS_CHECK", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def fail_on_incomplete() -> bool:
    raw = os.getenv("API_FOOTBALL_FAIL_ON_INCOMPLETE", "1").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    return True


def run_ingest_completeness_checks(client: bigquery.Client) -> dict[str, Any]:
    """
    Compare merged finished-fixture ids to each fanout batched table.

    Expected is restricted to fixtures whose ``status.short`` is in
    :data:`FINISHED_STATUS_SHORT` (``FT``/``AET``/``PEN``). Unplayed matches
    (upcoming, in-play, cancelled, postponed, abandoned) are reported separately
    as ``fixture_unplayed_count`` and do not affect the ``complete`` boolean.

    Returns a JSON-serializable dict including ``match_level_tables_cover_all_fixtures``
    (same boolean as legacy ``all_fanout_complete``) and per-entity
    ``covered_count`` / ``missing_count`` / ``missing_fixture_ids_sample`` (up to 12 ids).
    """
    out: dict[str, Any] = {
        "skipped": False,
        "expected_status_short": sorted(FINISHED_STATUS_SHORT),
        "leagues": {},
        "all_fanout_complete": True,
    }
    if skip_completeness_check():
        out["skipped"] = True
        return out

    for league_code in selected_leagues_map():
        fx_tbl = raw_league_table(league_code, "FIXTURES_NEXT")
        fx_payload = read_latest_payload_json(client, fx_tbl)
        all_fixture_ids = _fixture_ids_from_fixtures_payload(fx_payload)
        expected = _fixture_ids_from_fixtures_payload(
            fx_payload, statuses=FINISHED_STATUS_SHORT
        )
        league_block: dict[str, Any] = {
            "fixture_total_count": len(all_fixture_ids),
            "fixture_expected_count": len(expected),
            "fixture_unplayed_count": len(all_fixture_ids - expected),
            "fanout": {},
        }
        all_ok = True
        if not expected:
            league_block["note"] = (
                "no finished fixtures in merged payload; fanout checks skipped"
            )
            out["leagues"][league_code] = league_block
            continue
        for entity in FANOUT_ENTITIES:
            tbl = raw_league_table(league_code, entity)
            batched = read_latest_payload_json(client, tbl)
            required_key = (
                "statistics" if entity == "FIXTURE_STATISTICS" else None
            )
            covered = _fixture_ids_from_fanout_payload(
                batched,
                required_payload_key=required_key,
            )
            missing = sorted(expected - covered)
            ok = not missing
            if not ok:
                all_ok = False
            league_block["fanout"][entity] = {
                "covered_count": len(covered & expected),
                "expected_count": len(expected),
                "missing_count": len(missing),
                "missing_fixture_ids_sample": missing[:12],
                "complete": ok,
            }
        league_block["all_fanout_complete"] = all_ok
        league_block["match_level_tables_cover_all_fixtures"] = all_ok
        out["leagues"][league_code] = league_block
        if not all_ok:
            out["all_fanout_complete"] = False

    out["match_level_tables_cover_all_fixtures"] = out["all_fanout_complete"]
    return out


def completeness_summary_line(report: dict[str, Any]) -> str:
    """Single-line JSON for log scrapers (e.g. Cloud Logging alerts on textPayload)."""
    return f"[api-football] ingest_completeness_json={json.dumps(report, ensure_ascii=True)}"
