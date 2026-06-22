"""Fetch /players per team×season (batched) → RAW_*_PLAYERS.

Each run fetches squad data for all teams across all configured seasons and
appends a fresh complete snapshot row. No cross-run merge with prior BQ data.

A large-roster deep league (LIBER, UEL, UCL across many seasons) produces a
snapshot whose JSON exceeds BigQuery's 100 MB per-row limit, so the snapshot is
split into byte-bounded chunk rows written in a single atomic load job — readers
take the latest snapshot as ``ingested_at = max per league_code`` and so see the
complete chunked snapshot or none of it. See ``load_json_payload_rows_to_bq``.
"""

from __future__ import annotations

import json
import os

from .. import quota as errors_quota
from ..bigquery import load_json_payload_rows_to_bq
from ..settings import raw_table
from ..fixture_scheduling import players_response_for_team
from .context import PipelineContext


def _players_max_row_bytes() -> int:
    """Per-row chunk budget (ascii-escaped JSON bytes) for RAW_APIF_PLAYERS.

    Measured against ``json.dumps(..., ensure_ascii=True)`` because that is what the loader
    writes, and it inflates accented names (e.g. LATAM rosters) to ``\\uXXXX`` — well beyond
    their UTF-8 size, which is why LIBER overflowed the 100 MB cap. Default leaves ~2.5x
    headroom; tunable via ``API_FOOTBALL_PLAYERS_MAX_ROW_BYTES`` (floored at 1 MB).
    """
    raw = os.getenv("API_FOOTBALL_PLAYERS_MAX_ROW_BYTES", "").strip()
    if raw:
        try:
            return max(1_000_000, int(raw))
        except ValueError:
            pass
    return 40_000_000


def _entry_bytes(entry: dict) -> int:
    return len(json.dumps(entry, ensure_ascii=True).encode("utf-8"))


def chunk_players_response(
    league_code: str, response_entries: list[dict], max_row_bytes: int
) -> list[dict]:
    """Split the accumulated players response into ``{league_code, response:[...]}`` payloads.

    Each payload's ascii-escaped JSON stays under ``max_row_bytes``. Entries are kept in
    order and never dropped; an entry that alone exceeds the budget still gets its own chunk
    (it cannot be split further, and dropping it would lose data). Always returns at least
    one payload — an empty response yields a single empty-snapshot row, matching prior
    behaviour (a snapshot is always written so the run is recorded).
    """
    chunks: list[list[dict]] = []
    current: list[dict] = []
    current_bytes = 0
    for entry in response_entries:
        eb = _entry_bytes(entry)
        if current and current_bytes + eb > max_row_bytes:
            chunks.append(current)
            current = []
            current_bytes = 0
        current.append(entry)
        current_bytes += eb
    chunks.append(current)  # always flush the final (possibly empty) chunk
    return [{"league_code": league_code, "response": c} for c in chunks]


def load_squad_players_batch(
    ctx: PipelineContext,
    league_code: str,
    seasons_list: list[int],
    team_ids: set[int],
) -> None:
    players_payload = {"league_code": league_code, "response": []}
    if os.getenv("API_FOOTBALL_SKIP_PLAYERS", "").strip().lower() in ("1", "true", "yes"):
        ctx.errors.append(
            f"players {league_code}: skipped (API_FOOTBALL_SKIP_PLAYERS set — use on low-quota archive runs)"
        )
        return
    for season in seasons_list:
        if errors_quota._http_quota_exhausted:
            break
        for team_id in sorted(team_ids):
            if errors_quota._http_quota_exhausted:
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
                players_payload["response"].append(
                    {
                        "team_id": team_id,
                        "season": season,
                        "players_payload": players_rows,
                    }
                )
            except Exception as e:
                ctx.errors.append(
                    f"players {league_code} team {team_id} season={season}: {e}"
                )
    try:
        chunks = chunk_players_response(
            league_code, players_payload["response"], _players_max_row_bytes()
        )
        load_json_payload_rows_to_bq(
            ctx.client,
            raw_table("PLAYERS"),
            chunks,
            league_code=league_code,
            append=True,
        )
        ctx.add_loaded(1)
    except Exception as e:
        ctx.errors.append(f"players BQ {league_code}: {e}")
