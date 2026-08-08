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

ONLY A COMPLETE FETCH MAY SUPERSEDE (#896). A response carrying a body-level error, or cut
short by the quota flag mid-pagination, is neither written nor added to ``written_keys``, so
the prior row survives untouched. Withholding the WRITE matters as much as withholding the
delete: a written row marks the (team, season) captured in ``captured_player_team_seasons``,
and a historical season would then never be re-fetched, turning a transient failure into a
permanent hole. An empty response with NO error is a complete answer ("no players") and does
supersede.

Fetch-side skip: only the live (reference) season is re-fetched every run (its per-season
stats keep accumulating); finished team-seasons already in RAW_APIF_PLAYERS are immutable and
never re-requested — see ``plan_player_team_season_fetch`` / ``captured_player_team_seasons``.
This is the API-cost twin of the merge above (bounded storage did NOT bound the fetch).
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


def captured_player_team_seasons(ctx: PipelineContext) -> set[tuple[int, int]]:
    """Read ``(team_id, season)`` pairs already stored in RAW_APIF_PLAYERS.

    The fetch-side twin of the storage-side merge: a finished season's /players response is
    immutable, so ``load_squad_players_batch`` skips team-seasons we already hold and fetches
    only the delta. Mirrors ``captured_team_seasons`` in loads/player_squads.py and the
    RAW_APIF_PLAYERS unnest in loads/player_universe.py. Returns an empty set if the table does
    not exist yet or the read fails (then everything is fetched — a duplicate download, never a
    silent miss)."""
    table = f"{GCP_PROJECT_ID}.{DATASET_ID}.{raw_table('PLAYERS')}"
    sql = f"""
        SELECT DISTINCT
            SAFE_CAST(JSON_VALUE(team_block, '$.team_id') AS INT64) AS team_id,
            SAFE_CAST(JSON_VALUE(team_block, '$.season') AS INT64) AS season
        FROM `{table}`,
            UNNEST(JSON_QUERY_ARRAY(JSON_QUERY(payload, '$.response'), '$')) AS team_block
        WHERE JSON_VALUE(team_block, '$.season') IS NOT NULL
    """
    pairs: set[tuple[int, int]] = set()
    try:
        for row in ctx.client.query(sql).result():
            if row.team_id is not None and row.season is not None:
                pairs.add((int(row.team_id), int(row.season)))
    except Exception as e:
        ctx.errors.append(f"players: captured-seasons read failed: {e}")
    return pairs


def plan_player_team_season_fetch(
    seasons_list: list[int],
    team_ids: set[int],
    reference_season: int,
    already_captured: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    """Pure policy: which ``(season, team_id)`` /players pulls this run still needs.

    The reference (current) season is always re-fetched — its per-season stats keep accumulating
    as matches are played. Every earlier season is immutable, so it is fetched only when the
    ``(team_id, season)`` is not already held. Deterministic, no I/O; keys are returned in
    ``(season, sorted team_id)`` order."""
    plan: list[tuple[int, int]] = []
    for season in seasons_list:
        for team_id in sorted(team_ids):
            if season >= reference_season or (team_id, season) not in already_captured:
                plan.append((season, team_id))
    return plan


def load_squad_players_batch(
    ctx: PipelineContext,
    league_code: str,
    seasons_list: list[int],
    team_ids: set[int],
    reference_season: int | None = None,
    already_captured: set[tuple[int, int]] | None = None,
) -> None:
    """Fetch and store the /players roster per (team, season) for one competition.

    `already_captured` is the run's single `captured_player_team_seasons()` result, read
    ONCE by the caller before the per-competition loop. That query UNNESTs all of
    RAW_APIF_PLAYERS, and this function runs once per competition, so reading it here was
    the second O(competitions^2) term (#33 item 1).

    ⚠ It is MUTATED, not just read. This loader WRITES RAW_APIF_PLAYERS, so unlike the
    fanout-coverage hoist the set genuinely goes stale between competitions — and national
    teams really do appear in more than one competition. Every key written below is added
    to it, which keeps it exactly as accurate as re-reading would. Passing None preserves
    the old read-it-yourself behaviour for any caller that has no run-level set.
    """
    if os.getenv("API_FOOTBALL_SKIP_PLAYERS", "").strip().lower() in ("1", "true", "yes"):
        ctx.errors.append(
            f"players {league_code}: skipped (API_FOOTBALL_SKIP_PLAYERS set — use on low-quota archive runs)"
        )
        return

    # Fetch-side skip: only the live season (stats still accumulating) + un-captured historical
    # (team, season) — finished seasons already in RAW_APIF_PLAYERS are immutable and never
    # re-requested. Mirrors the fixtures fanout's to_fetch/covered split.
    ref = (
        reference_season
        if reference_season is not None
        else (max(seasons_list) if seasons_list else 0)
    )
    if already_captured is None:
        already_captured = captured_player_team_seasons(ctx)
    fetch_keys = plan_player_team_season_fetch(seasons_list, team_ids, ref, already_captured)
    total = len(seasons_list) * len(team_ids)
    print(
        f"[api-football] league={league_code} phase=squad /players "
        f"to_fetch={len(fetch_keys)} skipped_cached={total - len(fetch_keys)}",
        flush=True,
    )

    rows: list[dict] = []
    written_keys: list[str] = []
    incomplete_keys: list[str] = []
    quota_cut = False
    for season, team_id in fetch_keys:
        if errors_quota._http_quota_exhausted:
            quota_cut = True
            break
        try:
            players_rows, complete = players_response_for_team(
                ctx.headers,
                team_id,
                season,
                ctx.errors,
                error_context=(
                    f"players {league_code} team_id={team_id} season={season}"
                ),
            )
            # An incomplete fetch must never supersede stored data (#896). The key is withheld from
            # `written_keys`, so `_delete_superseded_player_rows` leaves the prior row alone, and the
            # row is not written at all — writing it would ALSO mark the (team, season) captured in
            # `captured_player_team_seasons`, and a historical season would then never be re-fetched.
            # Before this guard a rate-limited response deleted the good rows it failed to replace:
            # on 2026-08-02 UCL 340 went 25 players to 0, UEL 573 24 to 0, UECL 20034 23 to 0, and
            # APD 463 46 to 40 when the limit hit mid-pagination.
            if not complete:
                incomplete_keys.append(f"{team_id}-{season}")
                continue
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
            # Keep the caller's hoisted set exact. Without this, the next competition in
            # the run would not see these (team, season) keys and would re-fetch any it
            # shares — national teams appear in club AND national competitions, so this
            # fires in practice. Only done on a SUCCESSFUL write: on the exception path
            # below the rows are not stored, so they are not captured, and re-fetching
            # them next competition is the correct behaviour.
            for key in written_keys:
                team_str, _, season_str = key.partition("-")
                already_captured.add((int(team_str), int(season_str)))
        except Exception as e:
            ctx.errors.append(f"players BQ {league_code}: {e}")

    if incomplete_keys:
        ctx.errors.append(
            f"players {league_code}: {len(incomplete_keys)} team-season(s) SKIPPED on an incomplete "
            f"fetch and kept their prior rows: {', '.join(incomplete_keys[:10])}"
            + (" ..." if len(incomplete_keys) > 10 else "")
        )

    if quota_cut:
        ctx.errors.append(
            f"players {league_code}: PARTIAL — quota exhausted mid-fetch; "
            f"{len(written_keys)} team-season(s) refreshed, the remainder keep their prior rows"
        )
