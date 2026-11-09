"""Post-ingest completeness checks: fanout and per-team coverage against what the run expected."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from .bigquery import load_json_to_bq, read_latest_payload_json
from .coverage import read_coverage
from .registry import selected_competitions
from .settings import DATASET_ID, GCP_PROJECT_ID, raw_table

COMPLETENESS_SNAPSHOT_TABLE = "RAW_APIF_INGEST_COMPLETENESS_SNAPSHOT"
_STATS_ENTITY = "FIXTURE_STATISTICS"

FANOUT_ENTITIES = (
    "LINEUPS",
    "FIXTURE_EVENTS",
    "FIXTURE_STATISTICS",
    "FIXTURE_PLAYERS",
)

PER_TEAM_ENTITIES = ("PLAYERS", "SQUADS", "TRANSFERS", "COACHES")

# COACHES is reported but never gates: the provider has no coach for some teams on every run.
PER_TEAM_GATED = ("PLAYERS", "SQUADS", "TRANSFERS")

# Matches that never reached a final whistle have no lineups/events/stats, so they are not expected.
FINISHED_STATUS_SHORT = frozenset({"FT", "AET", "PEN"})


def _fixture_ids_from_fixtures_payload(
    payload: dict | None,
    *,
    statuses: frozenset[str] | None = None,
) -> set[int]:
    """Fixture ids from a merged ``/fixtures`` payload, optionally limited to ``statuses``."""
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
    """Compare finished-fixture ids to each fanout table; unplayed fixtures are only counted."""
    out: dict[str, Any] = {
        "skipped": False,
        "expected_status_short": sorted(FINISHED_STATUS_SHORT),
        "leagues": {},
        "all_fanout_complete": True,
    }
    if skip_completeness_check():
        out["skipped"] = True
        return out

    all_covered = read_coverage(client)

    selected, _skipped = selected_competitions()
    for comp in selected:
        league_code = comp.league_code
        fx_payload = read_latest_payload_json(
            client, raw_table("FIXTURES_NEXT"), league_code=league_code
        )
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
            covered_raw = all_covered.get(league_code, {}).get(entity)
            if covered_raw is None:
                covered: set[int] = set()
            elif isinstance(covered_raw, dict):
                covered = {fid for fid, has_data in covered_raw.items() if has_data}
            else:
                covered = covered_raw  # already a set (forward-compat)
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


def _latest_snapshot_timestamps(
    client: bigquery.Client, table_name: str
) -> dict[str, datetime]:
    """Per-league ``max(ingested_at)``, read separately so the caller can inline literals.

    A subquery predicate does not prune partitions, so merging this into one query scans far more.
    No lookback window: poll-mode competitions go months between refreshes and would read as missing.
    """
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    try:
        client.get_table(table_id)
    except NotFound:
        return {}
    q = f"SELECT league_code, MAX(ingested_at) AS mx FROM `{table_id}` GROUP BY league_code"
    return {
        row.league_code: row.mx
        for row in client.query(q).result()
        if row.league_code and row.mx
    }


def _raw_table_exists(client: bigquery.Client, entity: str) -> bool:
    """Whether a raw table exists yet, so a first-ever run degrades instead of crashing."""
    try:
        client.get_table(f"{GCP_PROJECT_ID}.{DATASET_ID}.{raw_table(entity)}")
        return True
    except NotFound:
        return False


def per_team_expectations_from_results(results: list[Any]) -> dict[str, dict[str, Any]]:
    """What this run intended to fetch per competition, taken from the run rather than BigQuery.

    Poll-mode competitions are absent from ``results`` because they never fetch teams, players,
    squads or transfers; ``team_ids`` and ``max(seasons_list)`` are exactly what the loaders used.
    """
    return {
        r.league_code: {
            "team_ids": set(r.team_ids or ()),
            "reference_season": max(r.seasons_list) if r.seasons_list else None,
        }
        for r in (results or [])
    }


def read_per_team_coverage(
    client: bigquery.Client,
    expectations: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Expected-versus-covered team counts per league and per-team entity.

    ``expectations`` is ``{league_code: {"team_ids": set[int], "reference_season": int | None}}``
    from the run. PLAYERS is checked as ``(team_id, reference_season)``; the others use all
    ``team_ids``. PLAYERS has no per-run snapshot and is read in full; the others at their latest.
    A missing raw table counts as no coverage instead of raising.
    """
    leagues = [lc for lc, e in (expectations or {}).items() if e.get("team_ids")]
    if not leagues:
        return {}
    league_list = ", ".join(f"'{lc}'" for lc in sorted(leagues))

    def _fq(name: str) -> str:
        return f"{GCP_PROJECT_ID}.{DATASET_ID}.{raw_table(name)}"

    def _snapshot_block(entity: str, name: str) -> str | None:
        """Covered team ids from each league's latest snapshot.

        Each league is paired with its own timestamp; independent filters would let one league's
        timestamp count as coverage for another.
        """
        stamps = _latest_snapshot_timestamps(client, raw_table(name))
        stamps = {lc: ts for lc, ts in stamps.items() if lc in set(leagues)}
        if not stamps:
            return None
        pairs = " OR ".join(
            f"(s.league_code = '{lc}' AND s.ingested_at = TIMESTAMP('{ts.isoformat()}'))"
            for lc, ts in sorted(stamps.items())
        )
        return f"""
            SELECT '{entity}' AS entity, s.league_code,
                   SAFE_CAST(JSON_VALUE(r, '$.team_id') AS INT64) AS team_id
            FROM `{_fq(name)}` s, UNNEST(JSON_QUERY_ARRAY(s.payload, '$.response')) r
            WHERE {pairs}
        """

    blocks = [
        b
        for b in (
            _snapshot_block("SQUADS", "SQUADS"),
            _snapshot_block("TRANSFERS", "TRANSFERS"),
            _snapshot_block("COACHES", "COACHES"),
        )
        if b
    ]
    # The season must match each league's own reference season, so a shared season list would
    # let one league's rows satisfy another's expectation.
    season_pairs = " OR ".join(
        f"(p.league_code = '{lc}' AND SAFE_CAST(JSON_VALUE(r, '$.season') AS INT64) = "
        f"{int(e['reference_season'])})"
        for lc, e in sorted(expectations.items())
        if lc in set(leagues) and e.get("reference_season") is not None
    )
    # The snapshot blocks are existence-checked inside _latest_snapshot_timestamps; PLAYERS is not.
    if season_pairs and _raw_table_exists(client, "PLAYERS"):
        blocks.append(
            f"""
            SELECT 'PLAYERS' AS entity, p.league_code,
                   SAFE_CAST(JSON_VALUE(r, '$.team_id') AS INT64) AS team_id
            FROM `{_fq('PLAYERS')}` p, UNNEST(JSON_QUERY_ARRAY(p.payload, '$.response')) r
            WHERE p.league_code IN ({league_list}) AND ({season_pairs})
            """
        )

    covered: dict[tuple[str, str], set[int]] = {}
    # With no blocks the UNION would render as invalid `FROM ()`.
    if blocks:
        q = (
            "SELECT DISTINCT entity, league_code, team_id FROM (\n"
            + "\nUNION ALL\n".join(blocks)
            + "\n)"
        )
        for row in client.query(q).result():
            if row.team_id is None:
                continue
            covered.setdefault((row.league_code, row.entity), set()).add(int(row.team_id))

    out: dict[str, dict[str, Any]] = {}
    for league_code in sorted(leagues):
        exp = expectations[league_code]
        team_ids = set(exp.get("team_ids") or ())
        block: dict[str, Any] = {"reference_season": exp.get("reference_season")}
        for entity in PER_TEAM_ENTITIES:
            got = covered.get((league_code, entity), set())
            block[entity] = {
                "expected_count": len(team_ids),
                "missing_count": len(team_ids - got),
            }
        out[league_code] = block
    return out



def per_team_missing_by_league_entity(
    per_team: dict[str, dict[str, Any]],
) -> dict[str, int]:
    """``{"LEAGUE/ENTITY": missing_count}`` for gated entities only, for the stagnation compare."""
    out: dict[str, int] = {}
    for league_code, block in (per_team or {}).items():
        for entity in PER_TEAM_GATED:
            info = block.get(entity) or {}
            missing = int(info.get("missing_count") or 0)
            if missing > 0:
                out[f"{league_code}/{entity}"] = missing
    return out


def skipped_exemption_note(exempt: list[str] | None) -> str | None:
    """The line printed when the gate exempts a deliberately-skipped pair, or None."""
    if not exempt:
        return None
    return (
        "[api-football] completeness: not gating "
        + ", ".join(exempt)
        + " — deliberately skipped this run by the re-fetch cadence, so a gap there cannot heal "
        "and is not evidence of a stalled ingest."
    )


def detect_stagnant_per_team_gaps(
    current: dict[str, int],
    prior: dict[str, int] | None,
    skipped: set[str] | None = None,
) -> list[dict[str, Any]]:
    """(league, entity) pairs still missing teams on two consecutive runs.

    A single observation must not trigger a hard fail, which skips the dbt build. ``skipped`` pairs
    were not fetched this run and are exempt, since an unfetched pair cannot heal; the caller logs
    what it exempted.
    """
    if not prior:
        return []
    exempt = skipped or set()
    stagnant: list[dict[str, Any]] = []
    for key, count in sorted(current.items()):
        if key in exempt:
            continue
        prev = prior.get(key, 0)
        if count > 0 and prev > 0:
            league_code, _, entity = key.partition("/")
            stagnant.append(
                {
                    "league_code": league_code,
                    "entity": entity,
                    "prior_count": prev,
                    "count": count,
                }
            )
    return stagnant


# Distinguishes "payload not supplied" from a supplied None (no prior snapshot).
_UNREAD = object()


def read_prior_snapshot(client: bigquery.Client) -> dict | None:
    """The previous run's snapshot payload, read once and shared by the `load_prior_*` readers."""
    return read_latest_payload_json(client, COMPLETENESS_SNAPSHOT_TABLE)


def load_prior_per_team_missing(
    client: bigquery.Client, payload: Any = _UNREAD
) -> dict[str, int] | None:
    """Previous run's per-team gaps, or None when there is no prior record (fail-open)."""
    if payload is _UNREAD:
        payload = read_latest_payload_json(client, COMPLETENESS_SNAPSHOT_TABLE)
    if not payload:
        return None
    raw = payload.get("per_team_missing")
    if not isinstance(raw, dict):
        return None
    return {str(k): int(v) for k, v in raw.items()}


def fixture_statistics_missing_by_league(report: dict[str, Any]) -> dict[str, int]:
    """Per-league count of finished fixtures still missing FIXTURE_STATISTICS."""
    out: dict[str, int] = {}
    for league_code, block in (report.get("leagues") or {}).items():
        stats = (block.get("fanout") or {}).get(_STATS_ENTITY) or {}
        out[league_code] = int(stats.get("missing_count") or 0)
    return out


def load_prior_fixture_statistics_missing(
    client: bigquery.Client, payload: Any = _UNREAD
) -> dict[str, int] | None:
    """Previous run's per-league statistics missing counts, or None if first run."""
    if payload is _UNREAD:
        payload = read_latest_payload_json(client, COMPLETENESS_SNAPSHOT_TABLE)
    if not payload:
        return None
    raw = payload.get("fixture_statistics_missing")
    if not isinstance(raw, dict):
        return None
    return {str(k): int(v) for k, v in raw.items()}


def load_prior_dropped_calls(
    client: bigquery.Client, payload: Any = _UNREAD
) -> dict[str, int] | None:
    """Previous run's per-endpoint dropped-call counts, or None (no comparison, fail-open)."""
    if payload is _UNREAD:
        payload = read_latest_payload_json(client, COMPLETENESS_SNAPSHOT_TABLE)
    if not payload:
        return None
    raw = payload.get("dropped_calls_by_endpoint")
    if not isinstance(raw, dict):
        return None
    return {str(k): int(v) for k, v in raw.items()}


def detect_stagnant_dropped_calls(
    current: dict[str, int],
    prior: dict[str, int] | None,
) -> list[dict[str, Any]]:
    """Endpoints that dropped calls on both this run and the previous one.

    One bad run is not a failure: the per-minute limit self-heals and a hard fail skips the dbt build.
    """
    if not prior:
        return []
    stagnant: list[dict[str, Any]] = []
    for endpoint, count in sorted(current.items()):
        prev = prior.get(endpoint, 0)
        if count > 0 and prev > 0:
            stagnant.append(
                {"endpoint": endpoint, "prior_count": prev, "count": count}
            )
    return stagnant


def persist_fixture_statistics_missing(
    client: bigquery.Client,
    report: dict[str, Any],
    *,
    run_id: str,
    dropped_calls: dict[str, int] | None = None,
    per_team_missing: dict[str, int] | None = None,
) -> None:
    """Store this run's gap signatures (statistics, dropped calls, per-team) for the next run."""
    if report.get("skipped"):
        return
    payload = {
        "run_id": run_id,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "fixture_statistics_missing": fixture_statistics_missing_by_league(report),
        "dropped_calls_by_endpoint": dict(dropped_calls or {}),
        "per_team_missing": dict(per_team_missing or {}),
    }
    load_json_to_bq(
        client,
        COMPLETENESS_SNAPSHOT_TABLE,
        payload,
        as_json_payload=True,
        # WRITE_TRUNCATE on purpose: the table holds one current-state row.
        append=False,
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
            stagnant.append(
                {
                    "league_code": league_code,
                    "missing_count": now,
                    "prior_missing_count": prev,
                }
            )
    return stagnant


def completeness_summary_line(report: dict[str, Any]) -> str:
    """Single-line JSON for log scrapers (e.g. Cloud Logging alerts on textPayload)."""
    return f"[api-football] ingest_completeness_json={json.dumps(report, ensure_ascii=True)}"


def evaluate_completeness_outcome(
    report: dict[str, Any],
    *,
    prior_fixture_statistics_missing: dict[str, int] | None = None,
    dropped_calls: dict[str, int] | None = None,
    prior_dropped_calls: dict[str, int] | None = None,
    per_team_missing: dict[str, int] | None = None,
    prior_per_team_missing: dict[str, int] | None = None,
    skipped_per_team: set[str] | None = None,
) -> dict[str, Any]:
    """Decide whether the run hard-fails: a hard-gated league is incomplete or a stagnation fired."""
    out: dict[str, Any] = {
        "hard_fail": False,
        "hard_gated_failures": [],
        "active_failures": [],
        "in_progress_partial": [],
        "soft_partial": [],
        "stagnant_statistics": [],
        "stagnant_dropped_calls": [],
        "stagnant_per_team_gaps": [],
        "skipped_per_team_exempt": [],
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
                missing_endpoints.append(
                    {
                        "endpoint": entity,
                        "missing_count": info.get("missing_count", 0),
                        "expected_count": info.get("expected_count", 0),
                    }
                )
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
    # Stagnation signals are evaluated here so both operator kill-switches apply: the `skipped`
    # early return above and `fail_on_incomplete()` below.
    out["stagnant_dropped_calls"] = detect_stagnant_dropped_calls(
        dropped_calls or {}, prior_dropped_calls
    )
    out["stagnant_per_team_gaps"] = detect_stagnant_per_team_gaps(
        per_team_missing or {}, prior_per_team_missing, skipped_per_team
    )
    # Reported so an exemption is never silent.
    out["skipped_per_team_exempt"] = sorted(
        k for k in (skipped_per_team or set()) if (per_team_missing or {}).get(k, 0) > 0
    )

    if fail_on_incomplete() and (
        out["hard_gated_failures"]
        or out["stagnant_statistics"]
        or out["stagnant_dropped_calls"]
        or out["stagnant_per_team_gaps"]
    ):
        out["hard_fail"] = True
    return out


_GREEN = "✅"
_YELLOW = "🟡"


def _coverage_cell(block: dict[str, Any]) -> str:
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
    """Render the per-competition coverage table as a markdown step summary."""
    when = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [f"## Ingestion completeness — {when}", ""]
    if report.get("skipped"):
        lines.append(
            "Completeness check was skipped (`API_FOOTBALL_SKIP_COMPLETENESS_CHECK`)."
        )
        return "\n".join(lines) + "\n"

    leagues = report.get("leagues") or {}
    if not leagues:
        lines.append("No competitions reported.")
        return "\n".join(lines) + "\n"

    lines.append(
        "| Competition | Status | Finished / Total | Coverage | Backfill remaining |"
    )
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


def write_ci_output(key: str, value: str) -> bool:
    """Write key=value to ``$CI_STEP_OUTPUT`` or else ``$GITHUB_OUTPUT``; False when neither is set."""
    path = (os.getenv("CI_STEP_OUTPUT", "").strip()
            or os.getenv("GITHUB_OUTPUT", "").strip())
    if not path:
        return False
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")
        return True
    except OSError:
        return False


def write_step_summary_if_configured(markdown: str) -> bool:
    """Append ``markdown`` to ``$GITHUB_STEP_SUMMARY``; False when the variable is unset."""
    path = os.getenv("GITHUB_STEP_SUMMARY", "").strip()
    if not path:
        return False
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(markdown)
        return True
    except OSError:
        return False
