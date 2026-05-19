"""Export domestic league and WC JSON for GitHub Pages under artifacts/data/{league}/.

Queries unified marts with WHERE league_code (no per-league mart relations). BL1 matchday
uses mart_matchday_insights filtered to BL1; when empty, falls back to
mart_matchday_insights_bl1_relegation. WC matchday uses mart_matchday_insights_wc.

Writes:
  artifacts/data/{league_lower}/matchday_insights.json   {"show": [...]}
  artifacts/data/{league_lower}/team_season_insights.json {"teams": [...]}
  artifacts/data/wc/matchday_insights.json               {"show": [...]}  (WC only)
  artifacts/pages_export_manifest.json  (domestic_leagues[] + wc{})
  artifacts/matchday_insights.json (legacy BL1 compat)
  artifacts/team_season_insights.json (legacy BL1 compat)

Usage:
    python scripts/export_pages_data.py

Authentication: Application Default Credentials (CI WIF or gcloud auth locally).
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DBT_PROJECT_PATH = REPO_ROOT / "dbt_project" / "dbt_project.yml"
GCP_PROJECT = "football-data-pipeline-gcp"
MARTS_DATASET = "marts"
MATCHDAY_MART = f"{GCP_PROJECT}.{MARTS_DATASET}.mart_matchday_insights"
TEAM_SEASON_MART = f"{GCP_PROJECT}.{MARTS_DATASET}.mart_team_season_insights"
RELEGATION_MART = f"{GCP_PROJECT}.{MARTS_DATASET}.mart_matchday_insights_bl1_relegation"
WC_MATCHDAY_MART = f"{GCP_PROJECT}.{MARTS_DATASET}.mart_matchday_insights_wc"
WC_PRE_TOURNAMENT_PATH = "wc-pre-tournament/wc_pre_tournament_insights.json"


def _dbt_active_league_codes() -> list[str]:
    data = yaml.safe_load(DBT_PROJECT_PATH.read_text(encoding="utf-8"))
    raw = (data.get("vars") or {}).get("active_competition_league_codes")
    if not isinstance(raw, list):
        raise TypeError("active_competition_league_codes must be a YAML list")
    return [str(code) for code in raw]


def domestic_league_codes() -> list[str]:
    """Active competitions with domestic league matchday/team-season Pages export."""
    return sorted(
        code
        for code in _dbt_active_league_codes()
        if code != "WC" and not code.startswith("WCQ")
    )


def _bigquery_rows_to_dicts(rows) -> list[dict]:
    return [dict(row.items()) for row in rows]


def _query_matchday(client, league_code: str) -> list[dict]:
    from google.cloud import bigquery

    sql = f"""
        select *
        from `{MATCHDAY_MART}`
        where league_code = @league_code
        order by fixture_date asc, kickoff_datetime asc, fixture_sk asc
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("league_code", "STRING", league_code)
        ]
    )
    return _bigquery_rows_to_dicts(
        list(client.query(sql, job_config=job_config).result())
    )


def _query_relegation_matchday(client) -> list[dict]:
    sql = f"select * from `{RELEGATION_MART}` order by fixture_date asc, kickoff_datetime asc, fixture_sk asc"
    return _bigquery_rows_to_dicts(list(client.query(sql).result()))


def fetch_matchday_rows(client, league_code: str) -> tuple[list[dict], str]:
    print(f"Querying {MATCHDAY_MART} for league_code={league_code} ...", flush=True)
    rows = _query_matchday(client, league_code)
    if rows or league_code != "BL1":
        return rows, "mart_matchday_insights"

    print(f"BL1 regular empty; querying {RELEGATION_MART} ...", flush=True)
    relegation_rows = _query_relegation_matchday(client)
    if relegation_rows:
        return relegation_rows, "mart_matchday_insights_bl1_relegation"
    return rows, "mart_matchday_insights"


def fetch_wc_matchday_rows(client) -> tuple[list[dict], str]:
    sql = (
        f"select * from `{WC_MATCHDAY_MART}` "
        "order by fixture_date asc, kickoff_datetime asc, fixture_sk asc"
    )
    print(f"Querying {WC_MATCHDAY_MART} ...", flush=True)
    rows = _bigquery_rows_to_dicts(list(client.query(sql).result()))
    return rows, "mart_matchday_insights_wc"


def fetch_team_season_rows(client, league_code: str) -> list[dict]:
    from google.cloud import bigquery

    sql = f"""
        select *
        from `{TEAM_SEASON_MART}`
        where league_code = @league_code
        order by latest_rank asc
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("league_code", "STRING", league_code)
        ]
    )
    print(f"Querying {TEAM_SEASON_MART} for league_code={league_code} ...", flush=True)
    rows = list(client.query(sql, job_config=job_config).result())
    return _bigquery_rows_to_dicts(rows)


def write_json(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def export_all(artifacts_root: pathlib.Path | None = None) -> dict:
    try:
        from google.cloud import bigquery
    except ImportError as exc:
        raise RuntimeError(
            "google-cloud-bigquery is not installed. Run: pip install -r requirements.txt"
        ) from exc

    root = artifacts_root or (REPO_ROOT / "artifacts")
    data_root = root / "data"
    client = bigquery.Client(project=GCP_PROJECT)

    leagues_manifest: list[dict] = []
    for league_code in domestic_league_codes():
        suffix = league_code.lower()
        league_dir = data_root / suffix

        matchday_rows, source_mart = fetch_matchday_rows(client, league_code)
        matchday_path = league_dir / "matchday_insights.json"
        write_json(matchday_path, {"show": matchday_rows})
        print(f"Wrote {matchday_path} ({len(matchday_rows)} rows)", flush=True)

        team_rows = fetch_team_season_rows(client, league_code)
        team_path = league_dir / "team_season_insights.json"
        write_json(team_path, {"teams": team_rows})
        print(f"Wrote {team_path} ({len(team_rows)} rows)", flush=True)

        leagues_manifest.append(
            {
                "league_code": league_code,
                "matchday_path": f"data/{suffix}/matchday_insights.json",
                "team_season_path": f"data/{suffix}/team_season_insights.json",
                "matchday_row_count": len(matchday_rows),
                "team_season_row_count": len(team_rows),
                "matchday_source_mart": source_mart,
            }
        )

    wc_matchday_rows, wc_source_mart = fetch_wc_matchday_rows(client)
    wc_dir = data_root / "wc"
    wc_matchday_path = wc_dir / "matchday_insights.json"
    write_json(wc_matchday_path, {"show": wc_matchday_rows})
    print(f"Wrote {wc_matchday_path} ({len(wc_matchday_rows)} rows)", flush=True)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "domestic_leagues": leagues_manifest,
        "wc": {
            "league_code": "WC",
            "matchday_path": "data/wc/matchday_insights.json",
            "matchday_row_count": len(wc_matchday_rows),
            "matchday_source_mart": wc_source_mart,
            "wc_pre_tournament_path": WC_PRE_TOURNAMENT_PATH,
        },
        "legacy_compat": {
            "matchday_insights": "match-preview/matchday_insights.json",
            "team_season_insights": "team-season/team_season_insights.json",
        },
    }
    manifest_path = root / "pages_export_manifest.json"
    write_json(manifest_path, manifest)
    print(f"Wrote {manifest_path}", flush=True)

    bl1_matchday = data_root / "bl1" / "matchday_insights.json"
    bl1_team = data_root / "bl1" / "team_season_insights.json"
    if bl1_matchday.is_file():
        write_json(
            root / "matchday_insights.json",
            json.loads(bl1_matchday.read_text(encoding="utf-8")),
        )
    if bl1_team.is_file():
        write_json(
            root / "team_season_insights.json",
            json.loads(bl1_team.read_text(encoding="utf-8")),
        )

    return manifest


def main() -> int:
    try:
        export_all()
    except Exception as exc:
        print(f"export_pages_data failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
