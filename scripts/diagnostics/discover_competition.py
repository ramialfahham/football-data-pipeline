"""Discover and verify competitions in the API-Football catalog.

Searches /leagues by name (and optionally country + type), prints results with
coverage flags, and cross-references every returned ID against
docs/competition_registry.yml to flag collisions or mismatches.

Lookup rules:
  Domestic league   : --country <nation>  --type league
  Domestic cup      : --country <nation>  --type cup
  Continental club  : --country World     --type cup
  Intl national team: --country World     --type cup
  WC qualifiers     : --country World     (search sub-zone names)

Usage:
    # Search by name only
    python scripts/diagnostics/discover_competition.py --search "Copa del Rey"

    # Narrow by country and type (recommended)
    python scripts/diagnostics/discover_competition.py --search "Copa del Rey" --country Spain --type cup

    # Audit a specific registry entry by league_code
    python scripts/diagnostics/discover_competition.py --audit CDR

    # Run full registry audit (all competitions)
    python scripts/diagnostics/discover_competition.py --audit-all
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests
import yaml

# ---------------------------------------------------------------------------
# Project root on sys.path so settings imports work from any cwd
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from ingestion.api_football.settings import base_url, get_headers  # noqa: E402


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------

def _load_registry() -> list[dict]:
    path = _ROOT / "docs" / "competition_registry.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data["competitions"]


def _registry_by_id(registry: list[dict]) -> dict[int, list[dict]]:
    """Map provider_league_id → list of registry entries with that ID."""
    mapping: dict[int, list[dict]] = {}
    for entry in registry:
        lid = entry.get("provider_league_id")
        if lid is not None:
            mapping.setdefault(lid, []).append(entry)
    return mapping


def _registry_by_code(registry: list[dict]) -> dict[str, dict]:
    return {e["league_code"]: e for e in registry}


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _search_leagues(keyword: str, country: str | None, comp_type: str | None) -> list[dict]:
    params: dict[str, str] = {"search": keyword}
    if country:
        params["country"] = country
    if comp_type:
        params["type"] = comp_type
    resp = requests.get(
        f"{base_url()}/leagues",
        headers=get_headers(),
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("response", [])


def _fetch_league(league_id: int) -> dict | None:
    resp = requests.get(
        f"{base_url()}/leagues",
        headers=get_headers(),
        params={"id": league_id},
        timeout=30,
    )
    resp.raise_for_status()
    items = resp.json().get("response", [])
    return items[0] if items else None


def _active_season(item: dict) -> str:
    """Return the year of the season where current=true, or 'none active'."""
    for s in item.get("seasons", []):
        if s.get("current"):
            return str(s["year"])
    return "none active"


def _coverage_flags(item: dict) -> dict:
    """Extract key coverage flags from the most recent season."""
    seasons = item.get("seasons", [])
    # Prefer current season; fall back to last
    target = next((s for s in seasons if s.get("current")), seasons[-1] if seasons else {})
    cov = target.get("coverage", {}).get("fixtures", {})
    return {
        "statistics_fixtures": cov.get("statistics_fixtures", False),
        "statistics_players": cov.get("statistics_players", False),
        "lineups": cov.get("lineups", False),
        "events": cov.get("events", False),
    }


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

SEP = "-" * 100

def _print_item(item: dict, registry_by_id: dict[int, list[dict]], highlight_code: str | None = None) -> None:
    league = item["league"]
    country_meta = item["country"]
    lid = league["id"]
    active = _active_season(item)
    cov = _coverage_flags(item)

    collision_entries = registry_by_id.get(lid, [])
    collision_note = ""
    if collision_entries:
        codes = ", ".join(e["league_code"] for e in collision_entries)
        if highlight_code and any(e["league_code"] == highlight_code for e in collision_entries):
            collision_note = f"  [registry: {codes} — MATCHES expected code]"
        else:
            collision_note = f"  [registry: {codes}]"

    print(f"  ID {lid:>5}  {league['name']:<45}  {country_meta['name']:<22}  season={active}")
    print(f"          type={league['type']:<8}  "
          f"stats_fix={str(cov['statistics_fixtures']):<6}  "
          f"stats_players={str(cov['statistics_players']):<6}  "
          f"lineups={str(cov['lineups']):<6}  "
          f"events={str(cov['events'])}")
    if collision_note:
        print(f"         {collision_note}")


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def cmd_search(args: argparse.Namespace) -> None:
    registry = _load_registry()
    registry_by_id = _registry_by_id(registry)

    items = _search_leagues(args.search, args.country, args.type)
    if not items:
        print(f"No results for search='{args.search}'"
              + (f" country='{args.country}'" if args.country else "")
              + (f" type='{args.type}'" if args.type else ""))
        return

    print(f"\nFound {len(items)} result(s) for '{args.search}'"
          + (f" / country={args.country}" if args.country else "")
          + (f" / type={args.type}" if args.type else ""))
    print(SEP)
    for item in items:
        _print_item(item, registry_by_id)
        print()


def cmd_audit_one(league_code: str, registry: list[dict], registry_by_id: dict[int, list[dict]]) -> str:
    """
    Audit a single registry entry.  Returns 'ok', 'mismatch', or 'not_found'.
    Prints a single result line with status emoji.
    """
    by_code = _registry_by_code(registry)
    entry = by_code.get(league_code)
    if not entry:
        print(f"  {league_code:<8}  UNKNOWN — not in registry")
        return "not_found"

    lid = entry.get("provider_league_id")
    if lid is None:
        print(f"  {league_code:<8}  SKIP — provider_league_id is null")
        return "ok"

    item = _fetch_league(lid)
    if item is None:
        print(f"  {league_code:<8}  ERR  ID {lid} not found on API at all")
        return "mismatch"

    league = item["league"]
    country_meta = item["country"]
    active = _active_season(item)
    cov = _coverage_flags(item)

    # Check for other registry entries sharing the same ID
    collision_entries = [e for e in registry_by_id.get(lid, []) if e["league_code"] != league_code]

    registry_name = entry.get("name", "")
    api_name = league["name"]

    # -----------------------------------------------------------------------
    # Mismatch detection
    # - HARD FAIL (ERR): same provider_league_id assigned to multiple codes
    # - REVIEW (printed, no ERR): api name shares no significant tokens with
    #   registry name.  Name differences are common (abbreviations, locale
    #   variants) — print both and let the human decide.
    # -----------------------------------------------------------------------
    status = "ok"
    hard_flags: list[str] = []
    review_flags: list[str] = []

    if collision_entries:
        hard_flags.append(
            f"ID COLLISION: ID {lid} ALSO assigned to "
            f"{', '.join(e['league_code'] for e in collision_entries)}"
        )
        status = "mismatch"

    # Name review: flag when no significant tokens overlap
    _SKIP = {"cup", "the", "league", "and", "for", "of", "de", "la", "les", "world"}
    api_name_lower = api_name.lower()
    registry_name_lower = registry_name.lower()
    reg_tokens = {w for w in registry_name_lower.split() if len(w) > 3 and w not in _SKIP}
    api_tokens = {w for w in api_name_lower.split() if len(w) > 3 and w not in _SKIP}
    if reg_tokens and api_tokens and not (reg_tokens & api_tokens):
        review_flags.append(
            f"NAME REVIEW: registry='{registry_name}'  api='{api_name}' ({country_meta['name']})"
        )

    icon = "OK " if status == "ok" else "ERR"
    print(f"  {league_code:<8}  {icon}  ID {lid:<6}  api='{api_name:<43}'  registry='{registry_name}'")
    print(f"           country={country_meta['name']:<22}  season={active}  "
          f"stats_players={str(cov['statistics_players']):<6}")
    for flag in hard_flags:
        print(f"           !!!  {flag}")
    for flag in review_flags:
        print(f"           ---  {flag}")

    return status


def cmd_audit(args: argparse.Namespace) -> None:
    registry = _load_registry()
    registry_by_id = _registry_by_id(registry)

    if args.audit_all:
        codes = [e["league_code"] for e in registry if e.get("status") in ("active", "in_progress")]
        print(f"\nAuditing {len(codes)} active/in_progress competitions against live API...\n")
        print(SEP)
    else:
        codes = [args.audit]

    results: dict[str, str] = {}
    for code in codes:
        result = cmd_audit_one(code, registry, registry_by_id)
        results[code] = result

    if args.audit_all:
        print(SEP)
        ok = sum(1 for v in results.values() if v == "ok")
        bad = sum(1 for v in results.values() if v == "mismatch")
        print(f"\nSummary: {ok} ok, {bad} mismatches out of {len(codes)} competitions audited")
        if bad:
            bad_codes = [k for k, v in results.items() if v == "mismatch"]
            print(f"Mismatches: {', '.join(bad_codes)}")
            sys.exit(1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover and verify API-Football competition IDs against the registry.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--search", metavar="KEYWORD",
                       help="Search /leagues by keyword")
    group.add_argument("--audit", metavar="LEAGUE_CODE",
                       help="Audit a single registry entry by league_code")
    group.add_argument("--audit-all", action="store_true",
                       help="Audit all active/in_progress registry entries")

    parser.add_argument("--country", metavar="COUNTRY",
                        help="Filter by country (use 'World' for continental/international)")
    parser.add_argument("--type", metavar="TYPE", choices=["league", "cup"],
                        help="Filter by type: league or cup")

    args = parser.parse_args()

    if args.search:
        cmd_search(args)
    else:
        cmd_audit(args)


if __name__ == "__main__":
    main()
