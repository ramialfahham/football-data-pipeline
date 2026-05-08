"""Post-ingest checks: fanout coverage vs merged fixture list (for monitoring / alerts).

Two distinct signals come out of this module:

1. **Pipeline health** — does the machinery work? The orchestrator hard-fails the
   workflow only when an *active* competition is incomplete (registry status
   ``active``). ``in_progress`` competitions are by definition still backfilling
   on the current API tier and stay green; they surface as warnings in the
   completeness report.

2. **Data completeness** — how much data do we have? The full per-competition,
   per-endpoint coverage report is rendered as a markdown table to
   ``$GITHUB_STEP_SUMMARY`` on every run, so the state is visible without
   scrolling logs.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from google.cloud import bigquery

from .bigquery import read_latest_payload_json
from .registry import selected_competitions
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

    selected, _skipped = selected_competitions()
    for comp in selected:
        league_code = comp.league_code
        fx_tbl = raw_league_table(league_code, "FIXTURES_NEXT")
        fx_payload = read_latest_payload_json(client, fx_tbl)
        all_fixture_ids = _fixture_ids_from_fixtures_payload(fx_payload)
        expected = _fixture_ids_from_fixtures_payload(
            fx_payload, statuses=FINISHED_STATUS_SHORT
        )
        league_block: dict[str, Any] = {
            "registry_status": comp.status,
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


def evaluate_completeness_outcome(report: dict[str, Any]) -> dict[str, Any]:
    """Decide whether the run should hard-fail or stay green based on registry status.

    Hard-fail when an ``active`` competition has incomplete fanout coverage on
    finished fixtures. ``in_progress`` competitions are by design still
    backfilling on the current API tier; their incompleteness is a soft warning.

    Returns a dict with::

        {
            "hard_fail": bool,
            "active_failures":   [ {league_code, missing_endpoints: [...], total_missing: int}, ... ],
            "in_progress_partial": [ {league_code, missing_endpoints: [...], total_missing: int}, ... ],
        }

    The orchestrator uses ``hard_fail`` for the exit code and the
    ``active_failures`` list to compose a precise failure message.
    """
    out: dict[str, Any] = {
        "hard_fail": False,
        "active_failures": [],
        "in_progress_partial": [],
    }
    if report.get("skipped"):
        return out
    for league_code, block in (report.get("leagues") or {}).items():
        if block.get("match_level_tables_cover_all_fixtures", True):
            continue
        missing_endpoints = []
        total_missing = 0
        for entity, info in (block.get("fanout") or {}).items():
            if not info.get("complete", True):
                missing_endpoints.append({
                    "endpoint": entity,
                    "missing_count": info.get("missing_count", 0),
                    "expected_count": info.get("expected_count", 0),
                })
                total_missing += info.get("missing_count", 0)
        record = {
            "league_code": league_code,
            "missing_endpoints": missing_endpoints,
            "total_missing": total_missing,
        }
        status = (block.get("registry_status") or "").strip().lower()
        if status == "active":
            out["active_failures"].append(record)
        else:
            out["in_progress_partial"].append(record)
    if out["active_failures"] and fail_on_incomplete():
        out["hard_fail"] = True
    return out


_GREEN = "✅"
_YELLOW = "🟡"


def _coverage_cell(block: dict[str, Any]) -> str:
    """Render the per-competition coverage cell for the markdown table."""
    if block.get("note"):
        return "—"
    fanout = block.get("fanout") or {}
    if not fanout:
        return "—"
    if all(info.get("complete") for info in fanout.values()):
        return f"{_GREEN} all {len(fanout)} endpoints 100%"
    parts = []
    for entity, info in fanout.items():
        cov = info.get("covered_count", 0)
        exp = info.get("expected_count", 0)
        pct = f"{(cov / exp * 100):.1f}%" if exp else "n/a"
        if info.get("complete"):
            parts.append(f"{entity} {pct}")
        else:
            parts.append(f"{_YELLOW} {entity} {pct}")
    return ", ".join(parts)


def completeness_markdown_summary(
    report: dict[str, Any],
    *,
    notes: list[str] | None = None,
    now: datetime | None = None,
) -> str:
    """Render the run's completeness state as a GitHub-flavoured markdown summary.

    Designed for ``$GITHUB_STEP_SUMMARY`` so the per-competition coverage table
    is visible on the workflow run page without scrolling logs.
    """
    when = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [f"## Ingestion completeness — {when}", ""]
    if report.get("skipped"):
        lines.append("Completeness check was skipped (`API_FOOTBALL_SKIP_COMPLETENESS_CHECK`).")
        return "\n".join(lines) + "\n"

    leagues = report.get("leagues") or {}
    if not leagues:
        lines.append("No competitions reported.")
        return "\n".join(lines) + "\n"

    lines.append("| Competition | Status | Finished / Total | Coverage | Backfill remaining |")
    lines.append("|---|---|---|---|---|")
    for league_code in sorted(leagues.keys()):
        block = leagues[league_code]
        status = block.get("registry_status") or "?"
        finished = block.get("fixture_expected_count", 0)
        total = block.get("fixture_total_count", 0)
        coverage = _coverage_cell(block)
        missing = sum(
            (info.get("missing_count") or 0)
            for info in (block.get("fanout") or {}).values()
        )
        backfill = "—" if missing == 0 else f"{missing} fixture-endpoint pairs"
        lines.append(
            f"| {league_code} | {status} | {finished} / {total} | {coverage} | {backfill} |"
        )

    if notes:
        lines.extend(["", "### Run notes", ""])
        for n in notes:
            lines.append(f"- {n}")
    return "\n".join(lines) + "\n"


def write_step_summary_if_configured(markdown: str) -> bool:
    """Append ``markdown`` to ``$GITHUB_STEP_SUMMARY`` when running in GitHub Actions.

    Returns ``True`` when the file was written, ``False`` when the env var is
    unset (e.g. local runs). No-op outside GitHub Actions; safe to always call.
    """
    path = os.getenv("GITHUB_STEP_SUMMARY", "").strip()
    if not path:
        return False
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(markdown)
        return True
    except OSError:
        return False
