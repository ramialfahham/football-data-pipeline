"""Post-ingest checks: fanout coverage vs merged fixture list (for monitoring / alerts)."""

from __future__ import annotations

import json
import os
from typing import Any

from google.cloud import bigquery

from .bq import read_latest_payload_json
from .config import LEAGUES, raw_league_table

# Batched fanout raw entities (fixture_id blocks).
FANOUT_ENTITIES = (
    "LINEUPS",
    "FIXTURE_EVENTS",
    "FIXTURE_STATISTICS",
    "FIXTURE_PLAYERS",
    "PREDICTIONS",
)


def _fixture_ids_from_fixtures_payload(payload: dict | None) -> set[int]:
    out: set[int] = set()
    for item in (payload or {}).get("response") or []:
        fx = item.get("fixture") or {}
        fid = fx.get("id")
        if fid is not None:
            try:
                out.add(int(fid))
            except (TypeError, ValueError):
                continue
    return out


def _fixture_ids_from_fanout_payload(payload: dict | None) -> set[int]:
    out: set[int] = set()
    for row in (payload or {}).get("response") or []:
        fid = row.get("fixture_id")
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
    Compare merged fixture ids to each fanout batched table.

    Returns a JSON-serializable dict including ``match_level_tables_cover_all_fixtures``
    (same boolean as legacy ``all_fanout_complete``) and per-entity ``covered`` /
    ``missing_count`` / ``missing_fixture_ids_sample`` (up to 12 ids).
    """
    out: dict[str, Any] = {
        "skipped": False,
        "leagues": {},
        "all_fanout_complete": True,
    }
    if skip_completeness_check():
        out["skipped"] = True
        return out

    for league_code in LEAGUES:
        fx_tbl = raw_league_table(league_code, "FIXTURES_NEXT")
        fx_payload = read_latest_payload_json(client, fx_tbl)
        expected = _fixture_ids_from_fixtures_payload(fx_payload)
        league_block: dict[str, Any] = {
            "fixture_expected_count": len(expected),
            "fanout": {},
        }
        all_ok = True
        if not expected:
            league_block["note"] = "no fixtures in merged payload; fanout checks skipped"
            out["leagues"][league_code] = league_block
            continue
        for entity in FANOUT_ENTITIES:
            tbl = raw_league_table(league_code, entity)
            batched = read_latest_payload_json(client, tbl)
            covered = _fixture_ids_from_fanout_payload(batched)
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
