"""Fixture statistics trust diagnostics (raw -> staging -> core -> mart)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from google.cloud import bigquery


@dataclass
class TrustResult:
    raw_rows: int
    raw_rows_last_24h: int
    raw_response_rows: int
    staging_rows: int
    staging_shots_on_goal_non_null_rows: int
    core_rows: int
    core_shots_on_goal_non_null_rows: int
    upcoming_bl1_fixture_rows: int
    mart_rows: int
    mart_relegation_rows: int
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

    raw_rows = _single_int(client, f"select count(*) as c from `{project}.raw.RAW_APIF_BL1_FIXTURE_STATISTICS`", "c")
    raw_rows_last_24h = _single_int(
        client,
        f"""
        select count(*) as c
        from `{project}.raw.RAW_APIF_BL1_FIXTURE_STATISTICS`
        where ingested_at >= timestamp_sub(current_timestamp(), interval 24 hour)
        """,
        "c",
    )
    raw_response_rows = _single_int(
        client,
        f"""
        with src as (
            select payload
            from `{project}.raw.RAW_APIF_BL1_FIXTURE_STATISTICS`
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

    staging_rows = _single_int(client, f"select count(*) as c from `{project}.staging.stg_apif__bl1_fixture_statistics`", "c")
    staging_shots_on_goal_non_null_rows = _single_int(
        client,
        f"""
        select count(*) as c
        from `{project}.staging.stg_apif__bl1_fixture_statistics`
        where shots_on_goal is not null
        """,
        "c",
    )
    core_rows = _single_int(client, f"select count(*) as c from `{project}.core.fct_fixture_team_stats`", "c")
    core_shots_on_goal_non_null_rows = _single_int(
        client,
        f"""
        select count(*) as c
        from `{project}.core.fct_fixture_team_stats`
        where shots_on_goal is not null
        """,
        "c",
    )
    upcoming_bl1_fixture_rows = _single_int(
        client,
        f"""
        select count(*) as c
        from `{project}.intermediate.int_matchday__upcoming_round_fixtures`
        where league_code = 'BL1'
        """,
        "c",
    )
    mart_rows = _single_int(client, f"select count(*) as c from `{project}.marts.mart_matchday_insights`", "c")
    mart_relegation_rows = _single_int(
        client,
        f"select count(*) as c from `{project}.marts.mart_matchday_insights_bl1_relegation`",
        "c",
    )

    reasons: list[str] = []
    if raw_rows == 0:
        reasons.append("raw fixture statistics table is empty")
    if raw_response_rows == 0:
        reasons.append("raw payload has zero statistics lines in response.statistics")
    if staging_rows == 0:
        reasons.append("staging fixture statistics model has zero rows")
    if staging_shots_on_goal_non_null_rows == 0:
        reasons.append("staging shots_on_goal is entirely null")
    if core_shots_on_goal_non_null_rows == 0:
        reasons.append("core fixture team stats shots_on_goal is entirely null")
    consumer_mart_rows = mart_rows + mart_relegation_rows
    if consumer_mart_rows == 0 and upcoming_bl1_fixture_rows > 0:
        reasons.append(
            "mart_matchday_insights and mart_matchday_insights_bl1_relegation are both "
            "empty but BL1 has upcoming round fixtures"
        )

    return TrustResult(
        raw_rows=raw_rows,
        raw_rows_last_24h=raw_rows_last_24h,
        raw_response_rows=raw_response_rows,
        staging_rows=staging_rows,
        staging_shots_on_goal_non_null_rows=staging_shots_on_goal_non_null_rows,
        core_rows=core_rows,
        core_shots_on_goal_non_null_rows=core_shots_on_goal_non_null_rows,
        upcoming_bl1_fixture_rows=upcoming_bl1_fixture_rows,
        mart_rows=mart_rows,
        mart_relegation_rows=mart_relegation_rows,
        pass_trust_gate=(len(reasons) == 0),
        reasons=reasons,
    )


def main() -> int:
    result = run()
    if not result.pass_trust_gate:
        print("fixture stats trust gate failed:")
        for reason in result.reasons:
            print(f" - {reason}")
        return 1
    print(
        "fixture stats trust gate passed "
        f"(mart_rows={result.mart_rows}, mart_relegation_rows={result.mart_relegation_rows}, "
        f"upcoming_bl1={result.upcoming_bl1_fixture_rows})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
