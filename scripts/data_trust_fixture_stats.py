"""Fixture statistics trust diagnostics (raw -> staging -> core -> mart)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from google.cloud import bigquery


@dataclass
class TrustResult:
    raw_rows: int
    raw_rows_last_24h: int
    raw_response_rows: int
    staging_rows: int
    staging_xg_non_null_rows: int
    core_rows: int
    core_xg_non_null_rows: int
    mart_rows: int
    mart_home_xg_non_null_rows: int
    mart_away_xg_non_null_rows: int
    pass_trust_gate: bool
    reasons: list[str]


def _q(client: bigquery.Client, sql: str) -> list[bigquery.table.Row]:
    return list(client.query(sql).result())


def _single_int(client: bigquery.Client, sql: str, field: str) -> int:
    rows = _q(client, sql)
    if not rows:
        return 0
    value = rows[0].get(field)
    return int(value or 0)


def _project() -> str:
    return os.getenv("GCP_PROJECT_ID", "football-data-pipeline-gcp").strip() or "football-data-pipeline-gcp"


def run() -> TrustResult:
    project = _project()
    client = bigquery.Client(project=project)

    raw_rows = _single_int(
        client,
        f"select count(*) as c from `{project}.raw.RAW_D1_APIF_FIXTURE_STATISTICS`",
        "c",
    )
    raw_rows_last_24h = _single_int(
        client,
        f"""
        select count(*) as c
        from `{project}.raw.RAW_D1_APIF_FIXTURE_STATISTICS`
        where ingested_at >= timestamp_sub(current_timestamp(), interval 24 hour)
        """,
        "c",
    )
    raw_response_rows = _single_int(
        client,
        f"""
        with src as (
            select payload
            from `{project}.raw.RAW_D1_APIF_FIXTURE_STATISTICS`
        ),
        blocks as (
            select block_json
            from src,
            unnest(coalesce(json_query_array(payload, '$.response'), [])) as block_json
        ),
        stats_rows as (
            select stat_el
            from blocks,
            unnest(json_query_array(block_json, '$.statistics')) as stat_el
        ),
        stat_lines as (
            select json_value(line_el, '$.type') as stat_type
            from stats_rows,
            unnest(json_query_array(stat_el, '$.statistics')) as line_el
        )
        select count(*) as c from stat_lines
        """,
        "c",
    )

    staging_rows = _single_int(
        client,
        f"select count(*) as c from `{project}.staging.stg_apif__d1_fixture_statistics`",
        "c",
    )
    staging_xg_non_null_rows = _single_int(
        client,
        f"""
        select count(*) as c
        from `{project}.staging.stg_apif__d1_fixture_statistics`
        where expected_goals is not null
        """,
        "c",
    )
    core_rows = _single_int(
        client,
        f"select count(*) as c from `{project}.core.fct_fixture_team_stats`",
        "c",
    )
    core_xg_non_null_rows = _single_int(
        client,
        f"""
        select count(*) as c
        from `{project}.core.fct_fixture_team_stats`
        where expected_goals is not null
        """,
        "c",
    )
    mart_rows = _single_int(
        client,
        f"select count(*) as c from `{project}.marts.mart_matchday_insights`",
        "c",
    )
    mart_home_xg_non_null_rows = _single_int(
        client,
        f"""
        select count(*) as c
        from `{project}.marts.mart_matchday_insights`
        where home_xg_for_recent is not null
        """,
        "c",
    )
    mart_away_xg_non_null_rows = _single_int(
        client,
        f"""
        select count(*) as c
        from `{project}.marts.mart_matchday_insights`
        where away_xg_for_recent is not null
        """,
        "c",
    )

    reasons: list[str] = []
    if raw_rows == 0:
        reasons.append("raw fixture statistics table is empty")
    if raw_response_rows == 0:
        reasons.append("raw payload has zero statistics lines in response.statistics")
    if staging_rows == 0:
        reasons.append("staging fixture statistics model has zero rows")
    if staging_xg_non_null_rows == 0:
        reasons.append("staging expected_goals is entirely null")
    if core_xg_non_null_rows == 0:
        reasons.append("core fixture team stats expected_goals is entirely null")
    if mart_rows > 0 and (mart_home_xg_non_null_rows == 0 or mart_away_xg_non_null_rows == 0):
        reasons.append("mart matchday insights has missing home/away xG values")

    return TrustResult(
        raw_rows=raw_rows,
        raw_rows_last_24h=raw_rows_last_24h,
        raw_response_rows=raw_response_rows,
        staging_rows=staging_rows,
        staging_xg_non_null_rows=staging_xg_non_null_rows,
        core_rows=core_rows,
        core_xg_non_null_rows=core_xg_non_null_rows,
        mart_rows=mart_rows,
        mart_home_xg_non_null_rows=mart_home_xg_non_null_rows,
        mart_away_xg_non_null_rows=mart_away_xg_non_null_rows,
        pass_trust_gate=(len(reasons) == 0),
        reasons=reasons,
    )


def write_outputs(result: TrustResult) -> None:
    root = Path(__file__).resolve().parents[1]
    artifacts = root / "artifacts"
    artifacts.mkdir(exist_ok=True)
    data = asdict(result)

    (artifacts / "data_trust_fixture_stats.json").write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )

    md_lines = [
        "# Fixture Statistics Data Trust",
        "",
        f"- Gate status: **{'PASS' if result.pass_trust_gate else 'FAIL'}**",
        f"- raw rows: `{result.raw_rows}`",
        f"- raw rows (last 24h): `{result.raw_rows_last_24h}`",
        f"- raw response.statistics lines: `{result.raw_response_rows}`",
        f"- staging rows: `{result.staging_rows}`",
        f"- staging expected_goals non-null rows: `{result.staging_xg_non_null_rows}`",
        f"- core rows: `{result.core_rows}`",
        f"- core expected_goals non-null rows: `{result.core_xg_non_null_rows}`",
        f"- mart rows: `{result.mart_rows}`",
        f"- mart home xG non-null rows: `{result.mart_home_xg_non_null_rows}`",
        f"- mart away xG non-null rows: `{result.mart_away_xg_non_null_rows}`",
        "",
    ]
    if result.reasons:
        md_lines.append("## Failure reasons")
        md_lines.extend([f"- {reason}" for reason in result.reasons])
    else:
        md_lines.append("No trust failures detected.")

    (artifacts / "data_trust_fixture_stats.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")


def main() -> int:
    result = run()
    write_outputs(result)
    if not result.pass_trust_gate:
        print("fixture stats trust gate failed:")
        for reason in result.reasons:
            print(f" - {reason}")
        return 1
    print("fixture stats trust gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
