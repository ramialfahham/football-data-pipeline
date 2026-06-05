"""Export league JSON for GitHub Pages under artifacts/data/{league}/.

Queries unified mart_matchday_insights (all competitions, slice by league_code).
No per-competition mart relations — WC and domestic leagues all use the same mart.
Player insights export removed in #321 (mart_matchday_player_insights retired;
replacement pending #325).

Writes:
  artifacts/data/{league_lower}/matchday_insights.json   {"show": [...]}
  artifacts/data/{league_lower}/team_season_insights.json {"teams": [...]}
  artifacts/data/wc/matchday_insights.json            {"show": [...]}
  artifacts/pages_export_manifest.json
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
from datetime import date, datetime, timezone

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DBT_PROJECT_PATH = REPO_ROOT / "dbt_project" / "dbt_project.yml"
GCP_PROJECT = "football-data-pipeline-gcp"
MARTS_DATASET = "marts"
MATCHDAY_MART = f"{GCP_PROJECT}.{MARTS_DATASET}.mart_matchday_insights"
TEAM_SEASON_MART = f"{GCP_PROJECT}.{MARTS_DATASET}.mart_team_season_insights"


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


def _coerce_utc_datetime(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime(value.year, value.month, value.day)
    elif isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            return None
    else:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def next_fixture_kickoff_utc(rows: list[dict]) -> str | None:
    """Return earliest kickoff datetime in UTC ISO format from matchday rows."""
    kickoff_values: list[datetime] = []
    for row in rows:
        kickoff = _coerce_utc_datetime(row.get("kickoff_datetime"))
        if kickoff is not None:
            kickoff_values.append(kickoff)
            continue
        fixture_date = _coerce_utc_datetime(row.get("fixture_date"))
        if fixture_date is not None:
            kickoff_values.append(fixture_date)

    if not kickoff_values:
        return None
    return min(kickoff_values).isoformat()


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


def fetch_matchday_rows(client, league_code: str) -> tuple[list[dict], str]:
    print(f"Querying {MATCHDAY_MART} for league_code={league_code} ...", flush=True)
    rows = _query_matchday(client, league_code)
    return rows, "mart_matchday_insights"


def fetch_wc_matchday_rows(client) -> tuple[list[dict], str]:
    print(f"Querying {MATCHDAY_MART} for league_code=WC ...", flush=True)
    rows = _query_matchday(client, "WC")
    return rows, "mart_matchday_insights"


def fetch_team_season_rows(client, league_code: str) -> list[dict]:
    from google.cloud import bigquery

    sql = f"""
        select *
        from `{TEAM_SEASON_MART}`
        where league_code = @league_code
          and latest_rank is not null
          and latest_rank > 0
        order by latest_rank asc, team_name asc
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
                "next_fixture_kickoff_utc": next_fixture_kickoff_utc(matchday_rows),
            }
        )

    wc_rows, wc_source_mart = fetch_wc_matchday_rows(client)
    wc_path = data_root / "wc" / "matchday_insights.json"
    write_json(wc_path, {"show": wc_rows})
    print(f"Wrote {wc_path} ({len(wc_rows)} rows)", flush=True)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "domestic_leagues": leagues_manifest,
        "wc": {
            "league_code": "WC",
            "matchday_path": "data/wc/matchday_insights.json",
            "matchday_row_count": len(wc_rows),
            "matchday_source_mart": wc_source_mart,
            "next_fixture_kickoff_utc": next_fixture_kickoff_utc(wc_rows),
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
