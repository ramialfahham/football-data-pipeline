"""Per-entity export for the v2 site (#365, epic #361).

Turns the dbt marts into one JSON file per entity the website has a page for, so
the Astro build (#368) can render "one template x N entities". This is the engine
of the programmatic site: marts -> per-entity JSON -> templates -> pages.

ADDITIVE and isolated: it does not touch the legacy ``export_pages_data.py`` or
the live Pages deploy. The current Matchday IQ MVP keeps running until cutover
(#377). Output is a build artifact (gitignored), not committed.

Contract: ``docs/site_architecture.md`` section 5 (template -> export file -> mart).
Data is locale-independent; display labels resolve at build time from the metric
catalogue i18n keys. Nulls are preserved (the UI renders "-", never a fake zero).

This first slice covers the two cleanest complete marts — team profiles and
player profiles (+ match log) — and establishes the framework (slug map +
manifest). Fixtures, competitions, standings, leaderboards and the landing feed
are fast-follows that reuse these helpers.

Run:
    python scripts/export_site_data.py --out artifacts/site_data
    python scripts/export_site_data.py --entities teams --sample 50   # quick check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import unicodedata
from datetime import datetime, timezone

GCP_PROJECT = "football-data-pipeline-gcp"
MARTS_DATASET = "marts"
DEFAULT_OUT = "artifacts/site_data"
ENTITY_TYPES = ("teams", "players")


# --------------------------------------------------------------------------- #
# Pure helpers (unit-tested without BigQuery)
# --------------------------------------------------------------------------- #
def slugify(name: str | None, entity_id: int) -> str:
    """Stable, locale-independent URL slug: ``{kebab-name}-{id}``.

    The id suffix guarantees uniqueness and stability across renames (a rename
    keeps the same slug). Accents are folded to ASCII (Bayern Munchen, not
    Bayern Munich) and non-alphanumerics collapse to single hyphens. Matches
    docs/site_architecture.md section 3.
    """
    base = name or ""
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^a-zA-Z0-9]+", "-", base).strip("-").lower()
    return f"{base}-{entity_id}" if base else str(entity_id)


def _bigquery_rows_to_dicts(rows) -> list[dict]:
    return [dict(row.items()) for row in rows]


def _latest_season_row(rows: list[dict]) -> dict:
    """The row with the greatest season_api_year (identity comes from it)."""
    return max(rows, key=lambda r: (r.get("season_api_year") or 0))


def shape_team_payload(rows: list[dict]) -> dict:
    """One team's mart_team_profile rows -> the team page payload.

    rows: every (team, competition-season) row for a single team_sk.
    """
    latest = _latest_season_row(rows)
    team_id = int(latest["team_sk"])
    seasons = sorted(
        rows,
        key=lambda r: (r.get("season_api_year") or 0, r.get("league_code") or ""),
        reverse=True,
    )
    return {
        "type": "team",
        "team_id": team_id,
        "slug": slugify(latest.get("team_name"), team_id),
        "name": latest.get("team_name"),
        "country": latest.get("team_country"),
        "crest": latest.get("team_logo_url"),
        "seasons": [_strip_identity(r) for r in seasons],
    }


def shape_player_payload(profile_rows: list[dict], match_rows: list[dict]) -> dict:
    """One player's profile rows + match-log rows -> the player page payload."""
    latest = _latest_season_row(profile_rows)
    player_id = int(latest["player_sk"])
    seasons = sorted(
        profile_rows,
        key=lambda r: (r.get("season_api_year") or 0, r.get("league_code") or ""),
        reverse=True,
    )
    matches = sorted(
        match_rows,
        key=lambda r: (r.get("kickoff_datetime") or datetime.min),
        reverse=True,
    )
    return {
        "type": "player",
        "player_id": player_id,
        "slug": slugify(latest.get("player_name"), player_id),
        "name": latest.get("player_name"),
        "nationality": latest.get("player_nationality"),
        "photo": latest.get("player_photo_url"),
        "position": latest.get("position_code"),
        "seasons": [_strip_identity(r) for r in seasons],
        "match_log": matches,
    }


def _strip_identity(row: dict) -> dict:
    """Drop the repeated identity columns from a per-season row (they live once
    at the top of the payload, not on every season)."""
    drop = {
        "team_name", "team_country", "team_logo_url",
        "player_name", "player_first_name", "player_last_name",
        "player_nationality", "player_birth_date", "player_photo_url",
    }
    return {k: v for k, v in row.items() if k not in drop}


def build_manifest(entries: list[dict]) -> dict:
    """Export manifest: per-entity type counts + the file index (for incremental
    Astro builds — each entry carries a content checksum)."""
    counts: dict[str, int] = {}
    for e in entries:
        counts[e["type"]] = counts.get(e["type"], 0) + 1
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "entries": entries,
    }


def _payload_bytes(payload: dict) -> bytes:
    return json.dumps(payload, indent=2, default=str, ensure_ascii=False).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------- #
# BigQuery fetch (lazy import so the pure helpers stay test-friendly)
# --------------------------------------------------------------------------- #
def _client():
    from google.cloud import bigquery

    return bigquery.Client(project=GCP_PROJECT)


def _query(client, sql: str) -> list[dict]:
    return _bigquery_rows_to_dicts(list(client.query(sql).result()))


def _group_by(rows: list[dict], key: str) -> dict:
    grouped: dict = {}
    for r in rows:
        grouped.setdefault(r[key], []).append(r)
    return grouped


def fetch_team_payloads(client, sample: int = 0) -> list[dict]:
    rows = _query(client, f"select * from `{GCP_PROJECT}.{MARTS_DATASET}.mart_team_profile`")
    grouped = _group_by(rows, "team_sk")
    payloads = [shape_team_payload(v) for v in grouped.values()]
    return payloads[:sample] if sample else payloads


def fetch_player_payloads(client, sample: int = 0) -> list[dict]:
    profiles = _query(
        client, f"select * from `{GCP_PROJECT}.{MARTS_DATASET}.mart_player_profile`"
    )
    by_player = _group_by(profiles, "player_sk")
    player_ids = list(by_player.keys())[:sample] if sample else list(by_player.keys())
    wanted = set(player_ids)
    log_table = f"`{GCP_PROJECT}.{MARTS_DATASET}.mart_player_match_log`"
    if sample:
        # Don't pull the whole match log for a sample run — scope it to the
        # sampled players (player_sk is an int64 surrogate, safe to inline).
        id_list = ", ".join(str(int(pid)) for pid in player_ids)
        log_sql = f"select * from {log_table} where player_sk in ({id_list})"
    else:
        log_sql = f"select * from {log_table}"
    logs = _query(client, log_sql)
    by_player_log = _group_by(logs, "player_sk")
    return [
        shape_player_payload(by_player[pid], by_player_log.get(pid, []))
        for pid in player_ids
        if pid in wanted
    ]


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def write_entity(out_root: pathlib.Path, subdir: str, entity_id: int, payload: dict) -> dict:
    path = out_root / subdir / f"{entity_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _payload_bytes(payload)
    path.write_bytes(data)
    return {
        "type": payload["type"],
        "id": entity_id,
        "slug": payload["slug"],
        "path": f"{subdir}/{entity_id}.json",
        "sha256": _sha256(data),
    }


def export_all(out_root: pathlib.Path, entities: tuple[str, ...], sample: int, client=None) -> dict:
    client = client or _client()
    entries: list[dict] = []
    slug_map: dict[str, dict] = {}

    if "teams" in entities:
        for p in fetch_team_payloads(client, sample):
            e = write_entity(out_root, "teams", p["team_id"], p)
            entries.append(e)
            slug_map[p["slug"]] = {"type": "team", "id": p["team_id"]}
    if "players" in entities:
        for p in fetch_player_payloads(client, sample):
            e = write_entity(out_root, "players", p["player_id"], p)
            entries.append(e)
            slug_map[p["slug"]] = {"type": "player", "id": p["player_id"]}

    (out_root / "slug_map.json").write_text(
        json.dumps(slug_map, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    manifest = build_manifest(entries)
    (out_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description="Per-entity site export (#365)")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--entities", default=",".join(ENTITY_TYPES),
                    help="comma-separated: teams,players")
    ap.add_argument("--sample", type=int, default=0,
                    help="cap entities per type (0 = all; for quick checks)")
    args = ap.parse_args()
    entities = tuple(e.strip() for e in args.entities.split(",") if e.strip())
    out_root = pathlib.Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    manifest = export_all(out_root, entities, args.sample)
    print(f"[export_site_data] wrote {manifest['counts']} to {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
