"""Post-ingest health check for one or all competitions.

Why this exists
---------------
Three classes of data defect have each shipped to production and only surfaced
later as failing dbt relationship tests or empty UI panels. This script detects
all three up front — run it after onboarding a competition or after any ingest
that changed provider IDs — so the defect is caught at the source instead of
four layers downstream.

Checks (each is registry-driven and competition-agnostic)
---------------------------------------------------------
1. NULL fixture_id            (bug #297) — rows in RAW_APIF_FIXTURE_DETAILS whose
                               fixture_id column is NULL although the payload
                               carries $.fixture.id. Recoverable via
                               backfill_fixture_ids.py.
2. Stale wrong-ID rows        (bug #296) — fixture-details rows whose payload
                               $.league.id does not match the registry
                               provider_league_id for that league_code. Left
                               behind by WRITE_APPEND after an ID correction.
                               Purgeable via purge_stale_fixture_details.py.
3. Orphaned team_sk           (Inter Miami / GCUP class) — teams present in
                               core.fct_fixture_team_stats or core.fct_standings
                               whose team_sk is absent from core.dim_team. Breaks
                               the severity=error relationships tests.
4. Coverage sanity            — fixture-details row counts, distinct seasons, and
                               whether the registry current_season is represented.
                               A zero here usually means ingestion never ran for
                               the competition.

Checks 1, 2 and 4 read the raw layer only and work even before dbt has built.
Check 3 reads the modeled `core` dataset and is skipped (with a notice) if those
tables do not yet exist.

Usage
-----
    python scripts/diagnostics/verify_competition_ingest.py [--league CODE] [--strict]

Options
-------
    --league CODE   Restrict every check to a single league_code (e.g. MLS).
                    Default: all competitions in the registry.
    --strict        Exit non-zero if any check reports a problem. Without it the
                    script always exits 0 (report-only) so it can be run ad hoc
                    without failing a shell. Use --strict in CI / gating contexts.

Exit codes
----------
    0   No problems found, or problems found without --strict.
    1   Problems found and --strict was set.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from ingestion.api_football.settings import GCP_PROJECT_ID, DATASET_ID, raw_table  # noqa: E402

# Modeled layer datasets. The project convention (generate_schema_name.sql) maps
# each dbt layer name directly to a BigQuery dataset of the same name.
_CORE_DATASET = "core"


def _fixture_details_table() -> str:
    return f"{GCP_PROJECT_ID}.{DATASET_ID}.{raw_table('FIXTURE_DETAILS')}"


def _core_table(name: str) -> str:
    return f"{GCP_PROJECT_ID}.{_CORE_DATASET}.{name}"


def _registry() -> list[dict]:
    path = _ROOT / "docs" / "competition_registry.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data["competitions"]


def _registry_ids(competitions: list[dict]) -> dict[str, int]:
    """league_code -> provider_league_id for entries that have an ID."""
    out: dict[str, int] = {}
    for entry in competitions:
        lid = entry.get("provider_league_id")
        if lid is not None:
            out[entry["league_code"]] = int(lid)
    return out


def _league_filter_sql(league: str | None, column: str = "league_code") -> str:
    return f"AND {column} = '{league}'" if league else ""


# ---------------------------------------------------------------------------
# Check 1 — NULL fixture_id (bug #297)
# ---------------------------------------------------------------------------
def check_null_fixture_id(
    client: bigquery.Client, table: str, league: str | None
) -> list[tuple[str, int, int]]:
    """Return [(league_code, recoverable_nulls, unrecoverable_nulls), ...]."""
    q = f"""
        SELECT
          league_code,
          COUNTIF(fixture_id IS NULL
                  AND JSON_VALUE(payload, '$.fixture.id') IS NOT NULL) AS recoverable,
          COUNTIF(fixture_id IS NULL
                  AND JSON_VALUE(payload, '$.fixture.id') IS NULL) AS unrecoverable
        FROM `{table}`
        WHERE TRUE {_league_filter_sql(league)}
        GROUP BY 1
        HAVING recoverable > 0 OR unrecoverable > 0
        ORDER BY league_code
    """
    return [
        (r.league_code, int(r.recoverable), int(r.unrecoverable))
        for r in client.query(q).result()
    ]


# ---------------------------------------------------------------------------
# Check 2 — stale wrong-ID rows (bug #296)
# ---------------------------------------------------------------------------
def check_stale_league_id(
    client: bigquery.Client, table: str, ids: dict[str, int], league: str | None
) -> list[tuple[str, int, object, int]]:
    """Return [(league_code, expected_id, payload_id, rows), ...] for mismatches."""
    q = f"""
        SELECT
          league_code,
          SAFE_CAST(JSON_VALUE(payload, '$.league.id') AS INT64) AS payload_league_id,
          COUNT(*) AS n
        FROM `{table}`
        WHERE TRUE {_league_filter_sql(league)}
        GROUP BY 1, 2
        ORDER BY league_code, n DESC
    """
    stale: list[tuple[str, int, object, int]] = []
    for r in client.query(q).result():
        expected = ids.get(r.league_code)
        if expected is None:
            continue  # competition has no registry ID — nothing to reconcile
        if r.payload_league_id != expected:
            stale.append((r.league_code, expected, r.payload_league_id, int(r.n)))
    return stale


# ---------------------------------------------------------------------------
# Check 3 — orphaned team_sk (Inter Miami / GCUP class)
# ---------------------------------------------------------------------------
def check_orphaned_teams(
    client: bigquery.Client, league: str | None
) -> tuple[list[tuple[str, str, int, int]], bool]:
    """Return ([(source_model, league_code, team_sk, rows), ...], checked).

    `checked` is False when the core tables do not exist yet (skip, not a pass).
    """
    dim_team = _core_table("dim_team")
    try:
        client.get_table(dim_team)
    except NotFound:
        return [], False

    sources = ["fct_fixture_team_stats", "fct_standings"]
    available = []
    for s in sources:
        try:
            client.get_table(_core_table(s))
            available.append(s)
        except NotFound:
            continue
    if not available:
        return [], False

    union_sql = "\n        UNION ALL\n".join(
        f"""        SELECT '{s}' AS source_model, f.league_code, f.team_sk
        FROM `{_core_table(s)}` AS f
        LEFT JOIN `{dim_team}` AS d USING (team_sk)
        WHERE d.team_sk IS NULL {_league_filter_sql(league, 'f.league_code')}"""
        for s in available
    )
    q = f"""
        WITH orphans AS (
{union_sql}
        )
        SELECT source_model, league_code, team_sk, COUNT(*) AS n
        FROM orphans
        GROUP BY 1, 2, 3
        ORDER BY n DESC, source_model, team_sk
    """
    rows = [
        (r.source_model, r.league_code, int(r.team_sk), int(r.n))
        for r in client.query(q).result()
    ]
    return rows, True


# ---------------------------------------------------------------------------
# Check 4 — coverage sanity
# ---------------------------------------------------------------------------
def check_coverage(
    client: bigquery.Client,
    table: str,
    competitions: list[dict],
    league: str | None,
) -> list[tuple[str, int, int, str, bool]]:
    """Return [(league_code, rows, distinct_seasons, seasons_csv, current_present), ...].

    Only competitions with ingest_active are expected to have rows; the report
    flags an active competition with zero fixture-details rows as a problem.
    """
    q = f"""
        SELECT
          league_code,
          COUNT(*) AS n_rows,
          COUNT(DISTINCT JSON_VALUE(payload, '$.league.season')) AS n_seasons,
          STRING_AGG(DISTINCT JSON_VALUE(payload, '$.league.season') ORDER BY
                     JSON_VALUE(payload, '$.league.season')) AS seasons
        FROM `{table}`
        WHERE TRUE {_league_filter_sql(league)}
        GROUP BY 1
    """
    by_code = {
        r.league_code: (int(r.n_rows), int(r.n_seasons), r.seasons or "")
        for r in client.query(q).result()
    }

    out: list[tuple[str, int, int, str, bool]] = []
    for entry in competitions:
        lc = entry["league_code"]
        if league and lc != league:
            continue
        if not entry.get("ingest_active"):
            continue  # not expected to have data
        rows, n_seasons, seasons = by_code.get(lc, (0, 0, ""))
        current = str(entry.get("current_season", ""))
        current_present = current in {s for s in seasons.split(",") if s}
        out.append((lc, rows, n_seasons, seasons, current_present))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post-ingest health check for one or all competitions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--league", help="Restrict checks to a single league_code.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any problem is found.",
    )
    args = parser.parse_args()
    league = args.league.strip().upper() if args.league else None

    client = bigquery.Client(project=GCP_PROJECT_ID)
    competitions = _registry()
    ids = _registry_ids(competitions)
    table = _fixture_details_table()

    scope = f"league={league}" if league else "all competitions"
    print(f"\nVerifying ingest health ({scope})")
    print(f"Fixture-details table: {table}")
    print("=" * 78)

    problems = 0

    # --- Check 1 -----------------------------------------------------------
    print("\n[1] NULL fixture_id (bug #297)")
    null_rows = check_null_fixture_id(client, table, league)
    if not null_rows:
        print("    OK — every fixture-details row has fixture_id populated.")
    else:
        for lc, rec, unrec in null_rows:
            problems += 1
            print(
                f"    !! {lc:<8} recoverable={rec:,} (run backfill_fixture_ids.py)"
                + (f"  unrecoverable={unrec:,} (malformed payload)" if unrec else "")
            )

    # --- Check 2 -----------------------------------------------------------
    print("\n[2] Stale wrong-ID rows (bug #296)")
    stale = check_stale_league_id(client, table, ids, league)
    if not stale:
        print("    OK — every row's payload $.league.id matches the registry ID.")
    else:
        for lc, expected, got, n in stale:
            problems += 1
            print(
                f"    !! {lc:<8} expected league.id={expected} "
                f"stale league.id={got} rows={n:,} "
                f"(run purge_stale_fixture_details.py)"
            )

    # --- Check 3 -----------------------------------------------------------
    print("\n[3] Orphaned team_sk vs core.dim_team (Inter Miami / GCUP class)")
    orphans, checked = check_orphaned_teams(client, league)
    if not checked:
        print("    -- skipped: core.dim_team / fact tables not built yet.")
    elif not orphans:
        print("    OK — every team_sk in facts exists in dim_team.")
    else:
        for src, lc, team_sk, n in orphans:
            problems += 1
            print(f"    !! {src:<24} {lc:<8} team_sk={team_sk} rows={n:,}")
        print(
            "       Fix the team source (e.g. base_apif__teams coverage) or "
            "full-refresh the incremental fact if these are stale ghosts."
        )

    # --- Check 4 -----------------------------------------------------------
    print("\n[4] Coverage sanity (active competitions)")
    coverage = check_coverage(client, table, competitions, league)
    if not coverage:
        print("    (no active competitions in scope)")
    for lc, rows, n_seasons, seasons, current_present in coverage:
        if rows == 0:
            # Not a hard defect: a tournament that has not kicked off yet (e.g. WC
            # 2026, off-season continental cups) legitimately has zero *finished*
            # fixtures, and FIXTURE_DETAILS only stores finished ones. Flag as a
            # notice so --strict does not trip on expected pre-tournament emptiness.
            print(
                f"    ~  {lc:<8} 0 fixture-details rows — no finished fixtures yet "
                f"(pre-tournament/off-season) or ingestion has not run."
            )
        elif not current_present:
            print(
                f"    ~  {lc:<8} rows={rows:,} seasons={n_seasons} [{seasons}] "
                f"— current_season not yet represented (may be pre-season)."
            )
        else:
            print(f"    OK {lc:<8} rows={rows:,} seasons={n_seasons} [{seasons}]")

    # --- Summary -----------------------------------------------------------
    print("\n" + "=" * 78)
    if problems == 0:
        print("RESULT: healthy — no problems found.")
    else:
        print(f"RESULT: {problems} problem group(s) found. See !! lines above.")
        if args.strict:
            sys.exit(1)


if __name__ == "__main__":
    main()
