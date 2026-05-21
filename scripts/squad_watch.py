"""Squad-watch monitor for WC 2026 player coverage.

Question this script answers:

    For each WC 2026 participant national team, what share of squad players
    play in a league we already ingest, versus a league we do not?

The answer drives Wave 2 league-onboarding decisions. As provisional and
final WC 2026 squads are announced (typically late May / early June 2026),
re-run the script to refresh coverage and surface new gaps.

The script does NOT modify any data layer. It is a read-only API + BigQuery
report.

Usage:
    # From repo root, with .env populated:
    python scripts/squad_watch.py                       # full run, outputs to ./squad_watch_report/

    python scripts/squad_watch.py --team-id 26           # just one team (debug)
    python scripts/squad_watch.py --output-dir custom/   # custom output location
    python scripts/squad_watch.py --cache-only           # use cached API data, skip new calls
    python scripts/squad_watch.py --no-bigquery          # skip BQ participant fetch; pass --team-ids manually

Reads:
- ``.env`` for ``API_FOOTBALL_API_KEY``
- ``docs/competition_registry.yml`` for the set of ingested ``provider_league_id`` values
- BigQuery ``intermediate.int_wc__participant_teams`` joined to ``core.dim_team`` for the
  48 WC 2026 participant team IDs and names

Writes (to ``--output-dir``, default ``squad_watch_report/`` at repo root):
- ``raw_squads.json``         — last squad-endpoint response per team
- ``player_clubs.json``       — last player-endpoint response per player
- ``coverage_summary.json``   — per-team summary with covered / uncovered counts
- ``coverage_summary.md``     — human-readable Markdown report
- ``uncovered_leagues.json``  — aggregated list of leagues NOT in our registry that
                                hold one or more WC squad players, with player counts

The two JSON caches (``raw_squads.json`` and ``player_clubs.json``) double as state for
incremental runs: existing entries are skipped unless ``--force-refresh`` is set.

Exit codes:
    0 — success
    1 — input error (missing key, bad CLI args, etc.)
    2 — API quota exhausted mid-run; partial state still written
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml


APISPORTS_BASE = "https://v3.football.api-sports.io"
DEFAULT_OUTPUT_DIR = "squad_watch_report"
REQUEST_PAUSE_SECONDS = 0.15  # ~400 req/min, well under the 450/min APISports limit

# API-Football league IDs we explicitly do NOT consider "onboardable" — they're
# international or friendly competitions, not domestic leagues. Hosts and
# top-tier national-team players show up in these when the calendar year is
# friendly-heavy (pre-tournament periods). Surfacing them as gaps would be
# misleading: we can't add "Friendlies" as a domestic league.
NON_DOMESTIC_LEAGUE_IDS: set[int] = {
    10,    # Friendlies / FIFA Friendlies International
    667,   # Friendlies Clubs (pre-season etc.)
}


class QuotaExhausted(Exception):
    """Raised when the API responds with the daily-quota error."""


def _load_dotenv(repo_root: Path) -> None:
    """Minimal .env loader so the script runs standalone without python-dotenv."""
    env_path = repo_root / ".env"
    if not env_path.exists():
        return
    with env_path.open(encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def _api_key() -> str:
    key = os.getenv("API_FOOTBALL_API_KEY", "").strip()
    if not key:
        print("ERROR: API_FOOTBALL_API_KEY missing from environment.", file=sys.stderr)
        sys.exit(1)
    return key


def _api_get(path: str, params: dict[str, Any], api_key: str) -> dict:
    """Issue a single APISports GET and return the JSON payload.

    Raises QuotaExhausted if the response signals daily limit exceeded.
    """
    import requests  # imported here so the script can be parsed without requests installed

    url = f"{APISPORTS_BASE}{path}"
    headers = {"x-apisports-key": api_key}
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    errors = data.get("errors") or {}
    if isinstance(errors, dict):
        for key, value in errors.items():
            text = str(value).lower()
            if "limit" in text or "quota" in text or "too many" in text:
                raise QuotaExhausted(f"{key}: {value}")
    time.sleep(REQUEST_PAUSE_SECONDS)
    return data


def load_registered_league_ids(repo_root: Path) -> set[int]:
    """Read the registry to get the set of provider_league_id values we ingest."""
    registry_path = repo_root / "docs" / "competition_registry.yml"
    with registry_path.open(encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    out: set[int] = set()
    competitions = data.get("competitions") if isinstance(data, dict) else None
    iterable = competitions if isinstance(competitions, list) else (data if isinstance(data, list) else [])
    for entry in iterable:
        if not isinstance(entry, dict):
            continue
        pid = entry.get("provider_league_id")
        if isinstance(pid, int):
            out.add(pid)
    return out


def fetch_wc_participants_from_bq() -> list[tuple[int, str]]:
    """Query BQ for the 48 WC 2026 participant team API IDs and names."""
    try:
        from google.cloud import bigquery
    except ImportError:
        print("ERROR: google-cloud-bigquery not installed.", file=sys.stderr)
        print("  pip install google-cloud-bigquery", file=sys.stderr)
        sys.exit(1)
    client = bigquery.Client(project="football-data-pipeline-gcp")
    sql = """
        select t.team_api_id, t.team_name
        from `football-data-pipeline-gcp.intermediate.int_wc__participant_teams` p
        left join `football-data-pipeline-gcp.core.dim_team` t on t.team_sk = p.team_sk
        where t.team_api_id is not null
        order by t.team_name
    """
    return [(row.team_api_id, row.team_name) for row in client.query(sql).result()]


def fetch_squad_for_team(team_api_id: int, api_key: str) -> list[dict]:
    """Fetch the squad for one team. Returns list of player dicts.

    Uses APISports /players/squads?team={id}, which returns the active squad
    list as of now. For WC squads specifically, this picks up the FIFA-submitted
    squad once it's published.
    """
    payload = _api_get("/players/squads", {"team": team_api_id}, api_key)
    response = payload.get("response", []) or []
    if not response:
        return []
    first = response[0] if isinstance(response, list) else response
    players = first.get("players", []) if isinstance(first, dict) else []
    return players


def fetch_player_current_club(player_api_id: int, season: int, api_key: str) -> tuple[int | None, str | None, int | None, str | None]:
    """Fetch the player's primary club for a season.

    The /players endpoint returns a ``statistics[]`` array with one entry per
    (team, league) the player appeared in during the season. For our purposes
    the relevant entry is the player's CLUB — not an international or
    friendly league entry. We pick the statistics entry with the maximum
    ``games.appearences`` value, which naturally selects the player's primary
    club over national-team / friendly appearances.

    Returns (team_id, team_name, league_id, league_name) of the chosen entry,
    or (None, None, None, None) on miss.
    """
    payload = _api_get("/players", {"id": player_api_id, "season": season}, api_key)
    response = payload.get("response", []) or []
    if not response:
        return (None, None, None, None)
    item = response[0]
    statistics = item.get("statistics") or []
    if not statistics:
        return (None, None, None, None)
    def appearances(stat: dict) -> int:
        games = stat.get("games") or {}
        val = games.get("appearences")  # API spelling, "appearences"
        try:
            return int(val) if val is not None else 0
        except (TypeError, ValueError):
            return 0
    best = max(statistics, key=appearances)
    team = best.get("team") or {}
    league = best.get("league") or {}
    return (team.get("id"), team.get("name"), league.get("id"), league.get("name"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Where to write reports (default: squad_watch_report/)")
    parser.add_argument("--season", type=int, default=2026, help="Season year for /players lookups (default: 2026)")
    parser.add_argument("--team-id", type=int, action="append", help="Run only for the given team_api_id; can pass multiple times for debug")
    parser.add_argument("--no-bigquery", action="store_true", help="Skip BigQuery participant fetch; requires --team-id to be passed")
    parser.add_argument("--cache-only", action="store_true", help="Use cached API responses; do not make new API calls")
    parser.add_argument("--force-refresh", action="store_true", help="Ignore cached API responses and re-fetch everything")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    _load_dotenv(repo_root)

    registered_league_ids = load_registered_league_ids(repo_root)
    print(f"Registered (ingested) leagues: {sorted(registered_league_ids)}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    squads_cache_path = output_dir / "raw_squads.json"
    players_cache_path = output_dir / "player_clubs.json"

    squads_cache: dict[str, list[dict]] = {}
    if squads_cache_path.exists() and not args.force_refresh:
        squads_cache = json.loads(squads_cache_path.read_text(encoding="utf-8"))
    players_cache: dict[str, dict] = {}
    if players_cache_path.exists() and not args.force_refresh:
        players_cache = json.loads(players_cache_path.read_text(encoding="utf-8"))

    if args.team_id:
        participants: list[tuple[int, str]] = [(tid, f"team {tid}") for tid in args.team_id]
        print(f"Running for {len(participants)} explicit team(s): {participants}")
    elif args.no_bigquery:
        print("ERROR: --no-bigquery requires at least one --team-id.", file=sys.stderr)
        return 1
    else:
        print("Fetching WC 2026 participants from BigQuery...")
        participants = fetch_wc_participants_from_bq()
        print(f"Found {len(participants)} participants.")

    api_key = "" if args.cache_only else _api_key()

    coverage: dict[str, dict[str, Any]] = {}
    uncovered_leagues: dict[int, dict[str, Any]] = {}
    quota_hit = False

    try:
        for team_api_id, team_name in participants:
            key = str(team_api_id)
            print(f"\n=== {team_name} (id={team_api_id}) ===")

            # Squad
            if key in squads_cache and not args.force_refresh:
                squad = squads_cache[key]
                print(f"  squad: cached ({len(squad)} players)")
            elif args.cache_only:
                print("  squad: no cache, --cache-only set, skipping")
                squad = []
            else:
                try:
                    squad = fetch_squad_for_team(team_api_id, api_key)
                except QuotaExhausted as exc:
                    print(f"  squad: QUOTA EXHAUSTED ({exc})")
                    quota_hit = True
                    break
                squads_cache[key] = squad
                print(f"  squad: fetched ({len(squad)} players)")

            # Per-player club
            by_league: dict[int | None, list[str]] = defaultdict(list)
            for player in squad:
                pid = player.get("id")
                pname = player.get("name", "?")
                if pid is None:
                    continue
                pkey = str(pid)
                club_data = players_cache.get(pkey)
                if club_data is None and not args.cache_only:
                    try:
                        team_id, team_name_p, league_id, league_name = fetch_player_current_club(pid, args.season, api_key)
                    except QuotaExhausted as exc:
                        print(f"  player {pid}: QUOTA EXHAUSTED ({exc})")
                        quota_hit = True
                        break
                    club_data = {
                        "player_id": pid,
                        "player_name": pname,
                        "team_id": team_id,
                        "team_name": team_name_p,
                        "league_id": league_id,
                        "league_name": league_name,
                    }
                    players_cache[pkey] = club_data
                if club_data is None:
                    by_league[None].append(pname)
                    continue
                by_league[club_data.get("league_id")].append(pname)
            if quota_hit:
                break

            # Aggregate
            covered_count = sum(len(names) for lid, names in by_league.items() if lid in registered_league_ids)
            uncovered_count = sum(len(names) for lid, names in by_league.items() if lid not in registered_league_ids and lid is not None)
            missing_count = len(by_league.get(None, []))
            total = sum(len(names) for names in by_league.values())
            coverage[team_name] = {
                "team_api_id": team_api_id,
                "squad_size": total,
                "covered_squad_players": covered_count,
                "uncovered_squad_players": uncovered_count,
                "missing_club_data": missing_count,
                "covered_pct": round(100 * covered_count / total, 1) if total else 0,
                "by_league": {
                    str(lid) if lid is not None else "(no club)": {
                        "league_id": lid,
                        "is_covered": lid in registered_league_ids if lid is not None else False,
                        "player_count": len(names),
                        "players_sample": names[:5],
                    }
                    for lid, names in sorted(by_league.items(), key=lambda kv: -len(kv[1]))
                },
            }
            for lid, names in by_league.items():
                if lid is None or lid in registered_league_ids:
                    continue
                if lid in NON_DOMESTIC_LEAGUE_IDS:
                    # Friendlies / international categories aren't onboardable
                    # domestic competitions — don't surface them as gaps.
                    continue
                bucket = uncovered_leagues.setdefault(lid, {"league_id": lid, "total_players": 0, "by_team": {}})
                bucket["total_players"] += len(names)
                bucket["by_team"][team_name] = len(names)
            print(f"  -> covered {covered_count}/{total} ({coverage[team_name]['covered_pct']}%); uncovered {uncovered_count}; missing {missing_count}")

    finally:
        # Always persist caches so we can resume partial runs
        squads_cache_path.write_text(json.dumps(squads_cache, indent=2, ensure_ascii=False), encoding="utf-8")
        players_cache_path.write_text(json.dumps(players_cache, indent=2, ensure_ascii=False), encoding="utf-8")

    # Write reports
    summary_path = output_dir / "coverage_summary.json"
    summary_path.write_text(json.dumps(coverage, indent=2, ensure_ascii=False), encoding="utf-8")

    uncovered_path = output_dir / "uncovered_leagues.json"
    uncovered_path.write_text(json.dumps(uncovered_leagues, indent=2, ensure_ascii=False), encoding="utf-8")

    md_lines = ["# Squad-watch coverage report\n"]
    md_lines.append(f"Season: {args.season}.   Registered (ingested) leagues: {sorted(registered_league_ids)}\n")
    md_lines.append("\n## Coverage per WC participant\n")
    md_lines.append("| Team | Squad size | Covered | % | Uncovered | Missing club |")
    md_lines.append("|---|---|---|---|---|---|")
    for team_name, row in sorted(coverage.items(), key=lambda kv: -kv[1].get("uncovered_squad_players", 0)):
        md_lines.append(
            f"| {team_name} | {row['squad_size']} | {row['covered_squad_players']} | {row['covered_pct']}% | "
            f"{row['uncovered_squad_players']} | {row['missing_club_data']} |"
        )

    md_lines.append("\n## Uncovered leagues by total WC-squad-player count\n")
    md_lines.append("Sorted by impact: leagues holding the most WC squad players we cannot currently surface.\n")
    md_lines.append("| League ID | Total players in WC squads | Teams represented |")
    md_lines.append("|---|---|---|")
    for entry in sorted(uncovered_leagues.values(), key=lambda x: -x["total_players"]):
        teams_repr = ", ".join(f"{t}({n})" for t, n in sorted(entry["by_team"].items(), key=lambda kv: -kv[1]))
        md_lines.append(f"| {entry['league_id']} | {entry['total_players']} | {teams_repr} |")

    md_path = output_dir / "coverage_summary.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print("\n=== Reports written ===")
    print(f"  {summary_path}")
    print(f"  {uncovered_path}")
    print(f"  {md_path}")

    if quota_hit:
        print("\nWARNING: API quota exhausted mid-run. Reports are partial. Re-run later to fill gaps.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
