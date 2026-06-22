"""Fetch /players per team×season (batched) → RAW_APIF_PLAYERS.

Storage model: ONE row per (team, season) (each row's ``response`` carries a single
``{team_id, season, players_payload}`` entry), not one giant per-league row — so no row
approaches BigQuery's 100 MB per-row JSON limit, for any league. This mirrors
RAW_APIF_FIXTURE_DETAILS (one row per fixture).

Merge-on-write: each run appends the freshly-fetched per-(team,season) rows, then deletes
the superseded prior rows for exactly those keys, so the table holds one row per
(league, team, season) — bounded, not append-accumulating. Only re-written keys are
touched, so a quota cut mid-run leaves un-fetched keys' prior rows intact (a warning is
logged). Staging reads all rows faithfully (no latest-snapshot qualify); current-per-entity
is assembled in base.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from google.cloud import bigquery

from .. import quota as errors_quota
from ..bigquery import load_json_payload_rows_to_bq
from ..settings import GCP_PROJECT_ID, DATASET_ID, raw_table
from ..fixture_scheduling import players_response_for_team
from .context import PipelineContext


def _delete_superseded_player_rows(
    client: bigquery.Client,
    table_name: str,
    league_code: str,
    keys: list[str],
    before: datetime,
) -> None:
    """Drop rows for the just-written (team, season) ``keys`` (``"{team_id}-{season}"``) that
    predate this run, so RAW_APIF_PLAYERS holds one row per (league, team, season). Only the
    re-written keys are touched — un-fetched keys keep their prior row (quota-cut safe)."""
    if not keys:
        return
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    q = f"""
        delete from `{table_id}`
        where league_code = @lc
          and ingested_at < @before
          and concat(
                ifnull(json_value(payload, '$.response[0].team_id'), 'x'), '-',
                ifnull(json_value(payload, '$.response[0].season'), 'x')
              ) in unnest(@keys)
    """
    client.query(
        q,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("lc", "STRING", league_code),
                bigquery.ScalarQueryParameter("before", "TIMESTAMP", before),
                bigquery.ArrayQueryParameter("keys", "STRING", keys),
            ]
        ),
    ).result()


def load_squad_players_batch(
    ctx: PipelineContext,
    league_code: str,
    seasons_list: list[int],
    team_ids: set[int],
) -> None:
    if os.getenv("API_FOOTBALL_SKIP_PLAYERS", "").strip().lower() in ("1", "true", "yes"):
        ctx.errors.append(
            f"players {league_code}: skipped (API_FOOTBALL_SKIP_PLAYERS set — use on low-quota archive runs)"
        )
        return

    rows: list[dict] = []
    written_keys: list[str] = []
    quota_cut = False
    for season in seasons_list:
        if errors_quota._http_quota_exhausted:
            quota_cut = True
            break
        for team_id in sorted(team_ids):
            if errors_quota._http_quota_exhausted:
                quota_cut = True
                break
            try:
                players_rows = players_response_for_team(
                    ctx.headers,
                    team_id,
                    season,
                    ctx.errors,
                    error_context=(
                        f"players {league_code} team_id={team_id} season={season}"
                    ),
                )
                rows.append(
                    {
                        "league_code": league_code,
                        "response": [
                            {
                                "team_id": team_id,
                                "season": season,
                                "players_payload": players_rows,
                            }
                        ],
                    }
                )
                written_keys.append(f"{team_id}-{season}")
            except Exception as e:
                ctx.errors.append(
                    f"players {league_code} team {team_id} season={season}: {e}"
                )

    if rows:
        try:
            ts = datetime.now(timezone.utc)
            load_json_payload_rows_to_bq(
                ctx.client,
                raw_table("PLAYERS"),
                rows,
                league_code=league_code,
                append=True,
                ingested_at=ts.isoformat(),
            )
            _delete_superseded_player_rows(
                ctx.client, raw_table("PLAYERS"), league_code, written_keys, ts
            )
            ctx.add_loaded(1)
        except Exception as e:
            ctx.errors.append(f"players BQ {league_code}: {e}")

    if quota_cut:
        ctx.errors.append(
            f"players {league_code}: PARTIAL — quota exhausted mid-fetch; "
            f"{len(written_keys)} team-season(s) refreshed, the remainder keep their prior rows"
        )
