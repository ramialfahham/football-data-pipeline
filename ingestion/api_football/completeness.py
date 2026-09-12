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
from google.cloud.exceptions import NotFound

from .bigquery import load_json_to_bq, read_latest_payload_json
from .coverage import read_coverage
from .registry import selected_competitions
from .settings import DATASET_ID, GCP_PROJECT_ID, raw_table

COMPLETENESS_SNAPSHOT_TABLE = "RAW_APIF_INGEST_COMPLETENESS_SNAPSHOT"
_STATS_ENTITY = "FIXTURE_STATISTICS"

# Batched fanout raw entities (fixture_id blocks). API predictions are not
# ingested (we build our own), so there is no PREDICTIONS endpoint.
FANOUT_ENTITIES = (
    "LINEUPS",
    "FIXTURE_EVENTS",
    "FIXTURE_STATISTICS",
    "FIXTURE_PLAYERS",
)

# PER-TEAM raw entities (#898 cause 3). These are fetched one call per team, and until now had NO
# completeness check at all: FANOUT_ENTITIES above covers fixture-level data only, so a regression
# in any of these was invisible to every test in the repo. #896 is the proof that matters — the
# table GREW while data was destroyed, so row-count, freshness and not-null checks all passed.
PER_TEAM_ENTITIES = ("PLAYERS", "SQUADS", "TRANSFERS", "COACHES")

# ...but only these may FAIL a run. COACHES is reported and never gates: ~23 of 1,265 teams have no
# coach on every single run (measured stable over five nightlies), because the
# provider genuinely has none for them. Gating that would be permanently red, and a permanently-red
# gate trains everyone to ignore the alarm — which is exactly how ten green runs came to mean
# nothing. The other three measured 0 missing when this was introduced, so the gate starts green and
# can only fire on a real regression.
PER_TEAM_GATED = ("PLAYERS", "SQUADS", "TRANSFERS")

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

    # Derive coverage ONCE for all competitions, directly from RAW_APIF_FIXTURE_DETAILS
    # (one query). FIXTURE_DETAILS — the actual fanout data, one row per fetched
    # fixture — is the source of truth for which (league_code, fixture_id, endpoint)
    # combinations have data, so coverage can never drift out of sync with it.
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
            # Look up which fixture IDs are covered for this league + endpoint.
            # read_coverage() returns dict[int, bool] per entity (fixture_id → has_data).
            # Extract just the fixture IDs where data was confirmed present.
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
    """Per-league ``max(ingested_at)`` for a snapshot table. Metadata-only, ~15 KB.

    Step ONE of a deliberate two-step read, and the two steps must stay separate. Measured on
    RAW_APIF_TRANSFERS with ``--dry_run``:
      - ``WHERE ingested_at = (SELECT MAX(...) ... )``  **7.51 GB**, a subquery predicate does NOT prune
      - ``WHERE date(ingested_at) IN (<literals>)``      **384 MB**
      - this query alone                                 **14.8 KB**
    So the cheap shape is: read the maxima here, then inline them as literals in
    :func:`read_per_team_coverage`. A future reader will want to "simplify" this into one query.
    That costs 19.6x on the largest raw table we have.

    A fixed lookback window is NOT an alternative. Poll-mode competitions go months between
    refreshes (WC and CWC sit idle for months at a time), so a recent-days filter would return zero
    rows for them and report those leagues as 100% missing.
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
    """What THIS RUN intended to fetch per competition, for the per-team completeness check.

    ``results`` is the orchestrator's list of ``CompetitionRunResult``, which contains ONLY the
    competitions that ran the full phases. Poll-mode competitions are absent by construction, and
    that is the point: ``run_poll_phases`` never fetches teams, players, squads or transfers, so
    there is nothing to judge them against.

    ⚠ DO NOT rebuild this from BigQuery. Two versions that did were both wrong against production:
    deriving the season as the calendar year reported ACN as 24 of 24 teams missing (ACN is on
    2027, and so is J1), and deriving the league set from RAW_APIF_TEAMS judged 45 leagues and
    reported 33 league/entity pairs missing, including FAC/PLAYERS 749, none of which were gaps.
    ``team_ids`` here is the exact set the loaders iterated and ``max(seasons_list)`` is the exact
    value ``load_squad_players_batch`` was called with, so expectation and fetch cannot drift.
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
    """Expected-versus-covered team counts for the PER-TEAM endpoints (#898 cause 3).

    ``expectations`` comes from the RUN, not from BigQuery:
    ``{league_code: {"team_ids": set[int], "reference_season": int | None}}``, built by the
    orchestrator from the ``CompetitionRunResult`` list. Returns
    ``out[league_code][entity] = {expected_count, missing_count}`` plus ``reference_season``.

    ⚠ EXPECTED MUST COME FROM THE RUN. Two earlier versions derived it from BigQuery and both were
    wrong against production:
      - deriving the season as the calendar year reported ACN as 24 of 24 teams missing. ACN is on
        2027, and so is J1. Here the season is ``max(seasons_list)``, the exact value
        ``load_squad_players_batch`` was called with, so the two cannot disagree.
      - deriving the league set from RAW_APIF_TEAMS judged 45 leagues and reported 33 league/entity
        pairs missing, including FAC/PLAYERS 749. Those competitions are SELECTED but run in POLL
        mode, which never fetches teams, players, squads or transfers, so nothing was missing: they
        were simply never fetched. Only competitions that returned a ``CompetitionRunResult`` ran
        the per-team phases, and only those can be judged.

    EXPECTED SETS mirror what each loader iterates: PLAYERS is season-scoped and checked as
    ``(team_id, reference_season)``; SQUADS, TRANSFERS and COACHES take the full ``team_ids`` set.

    RAW_APIF_PLAYERS is keyed per (team, season) rather than per league, so it has no per-run
    snapshot and is read in full (0.55 GiB). The others are read at their latest snapshot only.

    FIRST-RUN SAFE: every one of the four tables is existence-checked before it is queried, and when
    no table exists the query is skipped entirely rather than rendering an empty ``FROM ()``. An
    absent table degrades to "no coverage" for that entity, never an exception.
    """
    leagues = [lc for lc, e in (expectations or {}).items() if e.get("team_ids")]
    if not leagues:
        return {}
    league_list = ", ".join(f"'{lc}'" for lc in sorted(leagues))

    def _fq(name: str) -> str:
        return f"{GCP_PROJECT_ID}.{DATASET_ID}.{raw_table(name)}"

    def _snapshot_block(entity: str, name: str) -> str | None:
        """Covered team ids from each league's latest snapshot of a per-run table.

        ⚠ The league and its OWN timestamp are paired. A flat `ingested_at IN (...)` plus a flat
        `league_code IN (...)` are two INDEPENDENT filters, so a row for league A carrying league
        B's latest timestamp would satisfy both and be counted as coverage for A. That is the same
        contamination class the PLAYERS season pairing below guards against, and it fails in the
        dangerous direction: it makes a real miss look covered.
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
    # PLAYERS is keyed per (team, season): no snapshot timestamp, and the season must match THAT league's
    # reference season. A shared season list would let one league's 2027 rows satisfy another
    # league's 2026 expectation, so the pairs are spelled out per league.
    season_pairs = " OR ".join(
        f"(p.league_code = '{lc}' AND SAFE_CAST(JSON_VALUE(r, '$.season') AS INT64) = "
        f"{int(e['reference_season'])})"
        for lc, e in sorted(expectations.items())
        if lc in set(leagues) and e.get("reference_season") is not None
    )
    # The existence guard is NOT optional here. The three snapshot blocks get it for free via
    # _latest_snapshot_timestamps; PLAYERS has no maxima step, so without this an absent table
    # raises straight through the orchestrator's blanket handler and hard-fails the run instead of
    # degrading to "no coverage". Review caught exactly that.
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
    # With no blocks at all (a first-ever run where none of the raw tables exist yet) the UNION
    # would render as `FROM ()`, which is invalid SQL and would be executed unguarded. Skip the
    # query entirely and report everything as uncovered, which on such a run is the truth.
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
    """Flatten to ``{"LEAGUE/ENTITY": missing_count}`` for the run-over-run stagnation compare.

    Only GATED entities are included: COACHES is reported but never gates, so it must not reach the
    snapshot that drives a hard fail.
    """
    out: dict[str, int] = {}
    for league_code, block in (per_team or {}).items():
        for entity in PER_TEAM_GATED:
            info = block.get(entity) or {}
            missing = int(info.get("missing_count") or 0)
            if missing > 0:
                out[f"{league_code}/{entity}"] = missing
    return out


def skipped_exemption_note(exempt: list[str] | None) -> str | None:
    """The line the run prints when the gate exempts a deliberately-skipped pair, or None.

    EXTRACTED SO IT CAN BE TESTED. It began as an inline `print` in the orchestrator, which
    nothing could reach: `_load_api_football` is
    deliberately never driven end to end by any test, so the contract's promise that the
    exemption is "asserted by a test on the emitted text" was false as written. A guarantee that
    an exemption is never silent is worth exactly as much as its test.

    Returns None when there is nothing to say, so a quiet run stays quiet.
    """
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
    """(league, entity) pairs still missing teams on TWO consecutive runs.

    Same window and same reasoning as ``detect_stagnant_dropped_calls``: a hard fail skips the dbt
    build and costs daily freshness, so a single observation must not trigger it. A brand-new team
    whose first fetch fails would otherwise fail the run on the day it appears.

    ⚠ ``skipped`` HOLDS THE PAIRS THAT WERE NOT FETCHED AT ALL THIS RUN, and they are exempt.
    The whole rule above rests on "the next night's fetch would have healed it". #33 item 14 put
    transfers on a 7-day per-league cadence that skips the phase ENTIRELY, and a league that was
    never fetched cannot heal by construction — so a pre-existing gap sat unfetched and failed a
    nightly (`UCL/TRANSFERS (1 then 1 teams missing)`), with `exit(3)` before dbt ran.

    THIS NARROWS THE GUARD, IT DOES NOT REMOVE IT, and the distinction is the point. A pair that
    WAS fetched on both runs and is still short of teams is still flagged, which is the case the
    gate exists for. The alternative considered and rejected was dropping TRANSFERS from
    ``PER_TEAM_GATED`` entirely (the COACHES precedent) — that would have removed real coverage
    permanently to work around an assumption we broke ourselves.

    The caller is expected to LOG what it exempted: a league skipped for many runs would otherwise
    hide a real gap behind the cadence, silently. The 7-day cadence bounds that to 7 days.
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


# "Caller supplied nothing" and "the caller supplied the answer, and the answer is None"
# are DIFFERENT, and conflating them is a live defect rather than a style point:
# `read_prior_snapshot` legitimately returns None on a first run, on a run whose predecessor
# had API_FOOTBALL_SKIP_COMPLETENESS_CHECK set, and any time the snapshot table does not
# exist yet. With `payload=None` as the "unsupplied" sentinel, those runs made all three
# readers fetch for themselves — 1 hoisted read + 3 re-reads = 4, one MORE than the 3 this
# change set out to remove, in exactly the case each reader's docstring says it exists for.
# A unique sentinel keeps the two cases apart.
_UNREAD = object()


def read_prior_snapshot(client: bigquery.Client) -> dict | None:
    """The previous run's completeness snapshot payload, read ONCE.

    The three `load_prior_*` readers below each pull a different key out of this ONE
    payload, and each used to issue its own `read_latest_payload_json` — three reads of the
    same row, back to back, for three dict lookups (#33 item 1). Nothing writes the
    snapshot between them: `persist_fixture_statistics_missing` runs afterwards.

    Returns None when there is no prior record. Pass that None straight through to the
    readers: they distinguish it from "unsupplied" via `_UNREAD`, so a first run still costs
    ONE read, not four.
    """
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
    """Previous run's per-endpoint dropped-call counts, or None if there is no prior record.

    None means "no comparison possible" and the stagnation check stays silent, which is the same
    fail-open direction ``load_prior_fixture_statistics_missing`` takes: a first run, or a run after
    the snapshot was skipped, must not raise a false alarm.
    """
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
    """Endpoints that dropped calls on BOTH this run and the previous one (#898).

    The window is prior-versus-current, matching ``detect_stagnant_statistics_backfill`` exactly.
    Two stagnation signals share one exit path, so they must agree on what "stagnant" means.

    A single bad run is deliberately NOT a failure: the per-minute limit is transient and self-heals,
    and failing would skip the dbt build and cost daily freshness. Two consecutive runs on the same
    endpoint means it is not healing.
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
    """Store this run's statistics gap signature for stagnation checks on the next run.

    Also stores per-endpoint dropped-call counts (#898) in the same payload, so the dropped-call
    stagnation check reuses this table rather than adding one. The table has no dbt consumer
    (verified: no reference anywhere under dbt_project/ or scripts/), so the extra key changes
    nothing downstream.
    """
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
        # DELIBERATE WRITE_TRUNCATE: this table holds one current-state row, and the stagnation
        # check compares this run against the stored one. Stated explicitly because `append` is
        # a required keyword — the destructive mode must be written down, not inherited from a
        # default.
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
    # #898's dropped-call stagnation is evaluated HERE, not ORed in by the orchestrator, so it is
    # subject to exactly the same two operator kill-switches as every other completeness failure:
    # the `report["skipped"]` early return above (API_FOOTBALL_SKIP_COMPLETENESS_CHECK) and
    # `fail_on_incomplete()` below (API_FOOTBALL_FAIL_ON_INCOMPLETE=0, the documented backfill
    # escape hatch). Two stagnation signals sharing one exit code must also share when they apply;
    # the first version bypassed both and would have failed a backfill run that set the override.
    out["stagnant_dropped_calls"] = detect_stagnant_dropped_calls(
        dropped_calls or {}, prior_dropped_calls
    )
    # #898 cause 3. Evaluated HERE, never ORed in by the orchestrator, so it inherits both operator
    # kill-switches by construction: the `report["skipped"]` early return above
    # (API_FOOTBALL_SKIP_COMPLETENESS_CHECK) and `fail_on_incomplete()` below
    # (API_FOOTBALL_FAIL_ON_INCOMPLETE=0, the documented backfill override). Placing a third
    # stagnation signal anywhere else is the exact defect review caught in the previous task.
    out["stagnant_per_team_gaps"] = detect_stagnant_per_team_gaps(
        per_team_missing or {}, prior_per_team_missing, skipped_per_team
    )
    # Reported so an exemption can never be silent. A league whose transfers are skipped week
    # after week would otherwise hide a real gap behind the cadence with nothing to look at.
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
    """Write a key=value pair to the CI runner's step-output file, if it has one.

    Reads ``$CI_STEP_OUTPUT`` first (set by ``.gitlab-ci.yml``), then ``$GITHUB_OUTPUT``
    (set by GitHub Actions). Platform-neutral on purpose: the nightly build gates every
    expensive step on the ``new_data`` signal this writes, so the signal had to survive
    the move to GitLab. Setting a variable literally named ``GITHUB_OUTPUT`` on a GitLab
    runner would also have worked and would have been a lie in a filename; the fallback
    instead keeps the frozen ``.github/workflows/`` copies working unchanged.

    Returns ``True`` when written, ``False`` when neither var is set (local runs).
    No-op off-CI; safe to always call.
    """
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
