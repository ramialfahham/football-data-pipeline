"""Post-ingest checks: fanout coverage vs merged fixture list (for monitoring / alerts).

Two distinct signals come out of this module:

1. **Pipeline health** — the orchestrator hard-fails when any competition with
   ``ingest_completeness_gate: hard`` is incomplete on finished fixtures, or when
   fixture-statistics backfill is stagnant run-over-run. ``gate: soft`` competitions
   are reported only.

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

from .bigquery import load_json_to_bq, read_latest_payload_json
from .registry import selected_competitions
from .settings import raw_league_table

COMPLETENESS_SNAPSHOT_TABLE = "RAW_APIF_INGEST_COMPLETENESS_SNAPSHOT"
_STATS_ENTITY = "FIXTURE_STATISTICS"

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
            "ingest_completeness_gate": comp.ingest_completeness_gate,
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


def fixture_statistics_missing_by_league(report: dict[str, Any]) -> dict[str, int]:
    """Per-league count of finished fixtures still missing FIXTURE_STATISTICS."""
    out: dict[str, int] = {}
    for league_code, block in (report.get("leagues") or {}).items():
        stats = (block.get("fanout") or {}).get(_STATS_ENTITY) or {}
        out[league_code] = int(stats.get("missing_count") or 0)
    return out


def load_prior_fixture_statistics_missing(
    client: bigquery.Client,
) -> dict[str, int] | None:
    """Previous run's per-league statistics missing counts, or None if first run."""
    payload = read_latest_payload_json(client, COMPLETENESS_SNAPSHOT_TABLE)
    if not payload:
        return None
    raw = payload.get("fixture_statistics_missing")
    if not isinstance(raw, dict):
        return None
    return {str(k): int(v) for k, v in raw.items()}


def persist_fixture_statistics_missing(
    client: bigquery.Client,
    report: dict[str, Any],
    *,
    run_id: str,
) -> None:
    """Store this run's statistics gap signature for stagnation checks on the next run."""
    if report.get("skipped"):
        return
    payload = {
        "run_id": run_id,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "fixture_statistics_missing": fixture_statistics_missing_by_league(report),
    }
    load_json_to_bq(
        client,
        COMPLETENESS_SNAPSHOT_TABLE,
        payload,
        as_json_payload=True,
    )


def detect_stagnant_statistics_backfill(
    report: dict[str, Any],
    prior_missing: dict[str, int] | None,
) -> list[dict[str, Any]]:
    """Leagues with hard gate whose FIXTURE_STATISTICS missing_count did not decrease."""
    if prior_missing is None:
        return []
    stagnant: list[dict[str, Any]] = []
    current = fixture_statistics_missing_by_league(report)
    for league_code, block in (report.get("leagues") or {}).items():
        if (block.get("ingest_completeness_gate") or "soft") != "hard":
            continue
        prev = prior_missing.get(league_code, 0)
        now = current.get(league_code, 0)
        if now > 0 and now >= prev:
            stagnant.append({
                "league_code": league_code,
                "missing_count": now,
                "prior_missing_count": prev,
            })
    return stagnant


def completeness_summary_line(report: dict[str, Any]) -> str:
    """Single-line JSON for log scrapers (e.g. Cloud Logging alerts on textPayload)."""
    return f"[api-football] ingest_completeness_json={json.dumps(report, ensure_ascii=True)}"


def evaluate_completeness_outcome(
    report: dict[str, Any],
    *,
    prior_fixture_statistics_missing: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Decide whether the ingest run should hard-fail.

    Hard-fail when any competition with ``ingest_completeness_gate: hard`` is
    incomplete, or when statistics backfill for a hard-gated league is stagnant
    (missing_count unchanged and still > 0 vs the prior run).

    Returns ``hard_gated_failures``, ``soft_partial``, ``stagnant_statistics``,
    and legacy ``active_failures`` (subset of hard-gated with registry status active).
    """
    out: dict[str, Any] = {
        "hard_fail": False,
        "hard_gated_failures": [],
        "active_failures": [],
        "in_progress_partial": [],
        "soft_partial": [],
        "stagnant_statistics": [],
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
        gate = (block.get("ingest_completeness_gate") or "soft").strip().lower()
        status = (block.get("registry_status") or "").strip().lower()
        if gate == "hard":
            out["hard_gated_failures"].append(record)
            if status == "active":
                out["active_failures"].append(record)
        else:
            out["soft_partial"].append(record)
            if status == "in_progress":
                out["in_progress_partial"].append(record)

    out["stagnant_statistics"] = detect_stagnant_statistics_backfill(
        report, prior_fixture_statistics_missing
    )

    if fail_on_incomplete() and (
        out["hard_gated_failures"] or out["stagnant_statistics"]
    ):
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
        reg_status = block.get("registry_status") or "?"
        gate = block.get("ingest_completeness_gate") or "soft"
        status = f"{reg_status} ({gate} gate)"
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
