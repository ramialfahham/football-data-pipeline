"""Per-entity export for the v2 site (#365, epic #361).

Turns the dbt marts into one JSON file per entity the website has a page for, so
the Astro build (#368) can render "one template x N entities". This is the engine
of the programmatic site: marts -> per-entity JSON -> templates -> pages.

ADDITIVE and isolated: it does not touch the legacy ``export_pages_data.py``.
The Matchday IQ MVP it once ran alongside is RETIRED (offline, Pages deleted,
``site/`` frozen), so there is no cutover to wait for; #377 is now the go-live of
v2 itself. Output is a build artifact (gitignored), not committed.

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
# Seeds carry no `+schema`, so they ride the profile's own `dataset:` rather than a layer dataset —
# prod's is `dbt_analytics` (CLAUDE.md). Verified, not assumed: a dry run against
# `marts.competition_registry` fails "not found", against `dbt_analytics.competition_registry` it
# validates at 260 bytes.
SEEDS_DATASET = "dbt_analytics"
DEFAULT_OUT = "artifacts/site_data"
ENTITY_TYPES = ("teams", "players", "fixtures", "competitions", "nav",
                "leaderboards", "matchstats", "glossary", "landing", "competition_index")
REGISTRY_PATH = "docs/competition_registry.yml"
CATALOGUE_SEED_PATH = "dbt_project/seeds/metric_catalogue.csv"
COMPETITION_TYPES_SEED_PATH = "dbt_project/seeds/competition_types.csv"

# Player leaderboards: the 9 COUNT boards from mart_leaderboards (LONG, one row per
# board, pre-ranked by the warehouse). metric_key drives the board; the 5 rate boards
# are deferred (#506). The order here is the display order.
_LEADERBOARD_METRICS = ("goals_player", "scorer_points_player", "shots_on_goal_player", "dribbles_success_player",
                        "passes_player", "passes_key_player", "duels_won_player", "defensive_actions_player",
                        "cards_player")
# The HOME page's Top players boards (#40): four boards, one metric each, in display order.
# ⚠ SEPARATE from _LEADERBOARD_METRICS below, which serves the per-league leaderboards payload — a
# different consumer with a different board set. Sharing one list would couple two surfaces that
# have changed independently (the home set was cut from nine boards to four while the leaderboards
# set was not).
# ⚠ These are the MART's keys. #40's own table lists the CATALOGUE ids (`goals`, `passes_total`);
# the mart suffixes them `_player`. The board's NAME still comes from the catalogue's `label_en`.
_HOME_PLAYER_BOARDS = ("goals_player", "assists_player", "passes_player", "passes_key_player")
# The HOME page's Top teams boards (#41), four boards in display order, locked alongside the player
# set. These are `mart_team_leaderboards`' own `metric_key` values and the catalogue's team
# `metric_id`s — the same string, unlike the player boards where the mart suffixes `_player`.
# ⚠ They do NOT share a number format: goals and shots on goal are `decimal_1`, passes and duels are
# `decimal_0`. The format travels with each board from the catalogue for that reason.
_HOME_TEAM_BOARDS = (
    "goals_per_match", "shots_on_goal_per_match", "passes_per_match", "duels_per_match",
)
# Top 7 per board, raised from 5, and applying to Top teams as well.
_HOME_BOARD_ROWS = 7

_LB_KEEP = ("player_sk", "player_name", "player_photo_url", "player_position",
            "appearances", "minutes", "rank", "sort_value",
            "goals_player", "assists_player", "shots_on_goal_player", "dribbles_success_player", "dribbles_attempts_player",
            "passes_player", "passes_key_player", "duels_won_player", "duels_player",
            "tackles_player", "interceptions_player", "blocks_player",
            "cards_yellow_player", "cards_red_player",
            "scorer_points_player", "defensive_actions_player", "cards_player")

# Join/identity keys dropped from each per-side block in the fixture payload
# (they live at the fixture top level or are join plumbing, not display data).
_W1_DROP = {"upcoming_fixture_sk", "team_sk", "is_home"}
_W2_DROP = {"upcoming_fixture_sk", "team_sk", "is_home"}
_CTX_DROP = {"fixture_sk", "team_sk", "season_sk"}
_H2H_DROP = {"team_sk", "opponent_team_sk", "pair_key", "is_canonical"}
_FW_DROP = {"upcoming_fixture_sk", "team_sk", "entity_type", "season_api_year", "window_type"}
_TOPPLAYER_DROP = {"upcoming_fixture_sk", "team_sk", "is_home", "entity_type",
                   "season_api_year", "window_type", "league_code", "top_player_rank"}

# The competition_type -> nav group MAPPING now lives in the competition_types seed
# (display_group column, GAP-19.3), read via _display_group_of_type() — no hardcoded
# dict here. _GROUP_ORDER is the display ORDER of the groups (site_architecture.md
# section 4): a presentation constant, not a per-competition-type mapping.
_GROUP_ORDER = ["leagues", "cups", "continental-club", "national-teams"]
# Only these types get a country hub (real nations); international comps live in groups only.
_DOMESTIC_TYPES = {"domestic_league", "domestic_cup", "domestic_super_cup"}

# ⚠ `_HERO_FIXTURE_LIMIT = 12` USED TO LIVE HERE and is GONE. It was reasoned — 10_home.md measured
# that twelve filled the first screenful across two or three competitions on every day sampled —
# but it does not SCALE: as competitions are onboarded, twelve slots hold fewer and fewer of them,
# so the block narrows exactly as the site broadens. The ruling: "we will show what we have, more
# matches will come, because we ingest more competitions."
#
# The replacement is the natural unit, not another number: every match on the NEXT DAY THAT HAS
# FOOTBALL (`group_upcoming_fixtures`). That does not reopen what GAP-02 settled — "today's
# matches" was rejected for rendering one row on some days, and "the next day that HAS matches" is
# never empty by construction.


# --------------------------------------------------------------------------- #
# Pure helpers (unit-tested without BigQuery)
# --------------------------------------------------------------------------- #
def _kebab(name: str | None) -> str:
    """Lowercase ASCII kebab of a name (accents folded; non-alphanumerics -> '-')."""
    base = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "-", base).strip("-").lower()


def player_slug_with_id(name: str | None, entity_id: int) -> str:
    """PLAYER URL slug: ``{kebab-name}-{id}``.

    Named for its one remaining caller on purpose. Team slugs are NOT built here any
    more -- they are derived in the warehouse and served on ``mart_team_profile`` as
    ``team_slug`` (#852), because assigning an identifier is derivation and this script
    is the consumption layer (#846). Calling this for a team would put the provider id
    back in a team URL, which is ruled out.

    Two things a reader should not trust from the old version of this docstring:
    it claimed the id suffix gave "stability across renames" -- it does not, because
    the name half is recomputed from the current name on every export, which is #843.
    And ``_kebab`` DELETES any character NFKD cannot decompose, so a player named
    Sigurðsson still loses a letter here. The transliteration fix landed for teams
    only; players inherit it when player slugs move to the warehouse.
    """
    base = _kebab(name)
    return f"{base}-{entity_id}" if base else str(entity_id)


def group_fixtures_by_round(rows: list[dict]) -> list[dict]:
    """A competition-season's fixtures as the Matchdays tab reads them: one entry per round, the
    rows in the warehouse's fixture_order (rounds in sequence, each round by kick-off), so the
    round order and the row order are both served. Every value is a served column of
    mart_competition_fixtures; the slug is the warehouse's, the played flag and the two matchday
    flags are carried through. Nothing is selected, ranked or computed here."""
    rounds: dict = {}
    for r in sorted(rows, key=lambda r: r["fixture_order"]):
        rnd = rounds.setdefault(r["round"], {
            "round": r["round"],
            "round_order": r.get("round_order"),
            "round_sequence": r.get("round_sequence"),
            "is_next_round": bool(r.get("is_next_round")),
            "fixtures": [],
        })
        rnd["fixtures"].append({k: v for k, v in r.items()
                                if k not in ("round", "round_order", "round_sequence", "is_next_round",
                                             "fixture_order")})
    return list(rounds.values())


def _drop(row: dict, keys: set[str]) -> dict:
    return {k: v for k, v in row.items() if k not in keys}


def _bigquery_rows_to_dicts(rows) -> list[dict]:
    return [dict(row.items()) for row in rows]


def _featured_season_row(rows: list[dict]) -> dict:
    """The row the entity's page opens on, and the row its top-level identity comes from.

    SELECTION of a served flag, never a decision. `is_featured_season` is computed in
    mart_team_profile / mart_player_profile (#846), because picking here was window selection in
    the consumption layer (layering.md) and because the same rule was written three times and had
    already drifted. It picked on recency alone, which is wrong for a player: their most recent
    football is genuinely the summer tournament, so a player who has just played one took their
    top-level position from that squad rather than from their club.

    Raises rather than falling back. A fallback to recency is the exact defect this removes, and a
    missing flag is a data gap to fix in the mart -- never to bridge here.
    """
    featured = [r for r in rows if r.get("is_featured_season")]
    if len(featured) != 1:
        raise ValueError(
            f"expected exactly 1 row with is_featured_season, found {len(featured)}. "
            "The warehouse decides the opening season (#846); the export must not choose one."
        )
    return featured[0]


# Display fields kept from a mart_team_fixtures row (GAP-15). Internal keys
# (team_sk, fixture_sk, opponent_team_sk, league_code, season_api_year, the ranks,
# has_result, is_upcoming) are dropped — the published row is display-only. The
# per-fixture deep-link (fixture URL identity) is GAP-19, deliberately absent here.
_TEAM_FIXTURE_FIELDS = (
    "opponent_name", "opponent_logo_url", "is_home", "kickoff_datetime",
    "round_name", "goals_for", "goals_against", "result", "status_short",
)


def _shape_team_fixture(row: dict) -> dict:
    return {k: row.get(k) for k in _TEAM_FIXTURE_FIELDS}


def _shape_squad_member(row: dict, career: dict | None = None) -> dict:
    """One mart_roster row -> a squad member. Identity from the roster row; the per-club
    season stats (appearances / mins-per-app / goals_player / assists_player) are JOINED from that
    player's mart_player_career row for the same (league_code, season) — selection, not
    derivation: minutes_per_appearance is the mart's precomputed column, never divided
    here. A member with no career row never appeared in a finished-match squad -> stats
    null (the Squad tab shows only members with >= 1 appearance). player_position is
    carried RAW — the GK/DEF/MID/ATT grouping is frontend display. Internal keys
    (team_sk, season_sk, ...) are dropped; no slug (the frontend slugifies)."""
    return {
        "player_id": int(row["player_sk"]),
        "name": row.get("player_name"),
        "position": row.get("player_position"),
        "nationality": row.get("player_nationality"),
        "birth_date": row.get("player_birth_date"),
        "photo": row.get("player_photo_url"),
        "appearances": career.get("appearances") if career else None,
        "minutes_per_appearance": career.get("minutes_per_appearance") if career else None,
        "goals": career.get("goals_player") if career else None,
        "assists": career.get("assists_player") if career else None,
    }


def _venue_block(row: dict) -> dict | None:
    """The team's home venue -> {name, city, capacity}, or None when the team has no venue
    data (honest absence). Identity from dim_team (via the mart); the export does not derive it."""
    name = row.get("venue_name")
    city = row.get("venue_city")
    capacity = row.get("venue_capacity")
    if name is None and city is None and capacity is None:
        return None
    return {"name": name, "city": city, "capacity": capacity}


def deserved_scatter_index(all_profile_rows: list[dict]) -> dict:
    """Index the deserved-vs-actual scatter by (league_code, season_api_year).

    The team page's hero plots every team in the league-season: shots-on-target
    difference per match (x) against points won (y), with the model's
    `deserved_points` as the trend line. That is a LEAGUE-SEASON property, not a
    team one, so it is built once from the whole `mart_team_profile` and attached
    to each team's matching season. Selection only — every value is a column the
    model already computed (`deserved_points` is its least-squares fit); nothing
    is derived or re-fitted here (consumption-layer contract).

    Only rows with a non-null `deserved_points` are included, so non-domestic /
    non-single-ladder league-seasons yield no entry and the hero renders its
    absent state rather than a broken scatter.
    """
    idx: dict = {}
    for r in all_profile_rows:
        if r.get("deserved_points") is None:
            continue
        key = (r.get("league_code"), r.get("season_api_year"))
        idx.setdefault(key, []).append({
            "team_sk": int(r["team_sk"]),
            "sotd": r.get("shots_on_goal_difference_per_match"),
            "points": r.get("points"),
            "deserved": r.get("deserved_points"),
        })
    return idx


def shape_team_payload(
    profile_rows: list[dict],
    fixture_rows: list[dict] | None = None,
    roster_rows: list[dict] | None = None,
    benchmark_rows: list[dict] | None = None,
    scatter_index: dict | None = None,
    career_rows: list[dict] | None = None,
) -> dict:
    """One team's mart_team_profile rows (+ mart_team_fixtures + mart_roster +
    mart_team_competition_benchmarks rows) -> the team page payload.

    profile_rows: every (team, competition-season) profile row for a single team_sk.
    fixture_rows: that team's mart_team_fixtures rows (next + last-5 per season; GAP-15).
    roster_rows: that team's mart_roster rows (the roster identity, per season; GAP-20).
    career_rows: that team's mart_player_career rows — per-player season stats joined onto the
        roster below (GAP-22).
    benchmark_rows: that team's mart_team_competition_benchmarks rows (rank-vs-league per season; GAP-23).
    """
    featured = _featured_season_row(profile_rows)
    team_id = int(featured["team_sk"])
    seasons = sorted(
        profile_rows,
        key=lambda r: (r.get("season_api_year") or 0, r.get("league_code") or ""),
        reverse=True,
    )
    fixtures_by_season: dict = {}
    for fr in fixture_rows or []:
        fixtures_by_season.setdefault(
            (fr.get("league_code"), fr.get("season_api_year")), []
        ).append(fr)
    roster_by_season: dict = {}
    for rr in roster_rows or []:
        roster_by_season.setdefault(
            (rr.get("league_code"), rr.get("season_api_year")), []
        ).append(rr)
    benchmark_by_season: dict = {}
    for br in benchmark_rows or []:
        benchmark_by_season.setdefault(
            (br.get("league_code"), br.get("season_api_year")), []
        ).append(br)
    # Squad tab: per-player season stats keyed by (league_code, season, player_sk), joined onto each
    # squad member below. mart_player_career is per-club, so this key uniquely picks the member's row.
    career_by_key: dict = {}
    for cr in career_rows or []:
        career_by_key[
            (cr.get("league_code"), cr.get("season_api_year"), cr.get("player_sk"))
        ] = cr

    seasons_out = []
    for r in seasons:
        s = _strip_identity(r)
        frs = fixtures_by_season.get((s.get("league_code"), s.get("season_api_year")), [])
        nxt = next((fr for fr in frs if fr.get("upcoming_rank") == 1), None)
        recent = sorted(
            (fr for fr in frs if 1 <= (fr.get("recency_rank") or 0) <= 5),
            key=lambda fr: fr["recency_rank"],
        )
        s["next_fixture"] = _shape_team_fixture(nxt) if nxt else None
        s["recent_results"] = [_shape_team_fixture(fr) for fr in recent]
        # GAP-20 + Squad tab: the roster for this (competition, season), each member joined to its
        # per-player career stats (career_by_key) below. Omit unresolved-player
        # rows (null player_name — guarded upstream by the player_sk->dim_player relationships
        # DQ test); byte-stable order by player_sk (the frontend groups by position + sorts).
        squad_rows = roster_by_season.get((s.get("league_code"), s.get("season_api_year")), [])
        s["squad"] = [
            _shape_squad_member(
                rr,
                career_by_key.get(
                    (rr.get("league_code"), rr.get("season_api_year"), rr.get("player_sk"))
                ),
            )
            for rr in sorted(squad_rows, key=lambda rr: rr["player_sk"])
            if rr.get("player_name") is not None
        ]
        # GAP-23: rank-vs-league benchmark for this (competition, season) — a flat metrics[] list
        # (no position dimension); the frontend renders the LOCKED 16 per metrics_display.md.
        s["benchmarks"] = _shape_team_benchmarks(
            benchmark_by_season.get((s.get("league_code"), s.get("season_api_year")), [])
        )
        # Deserved-vs-actual hero scatter: every team in this league-season (sotd, points, deserved),
        # with the self team flagged. Present only for fittable (domestic single-ladder) seasons; its
        # absence is what makes the hero render its absent state (§ deserved-vs-actual, points).
        entries = (scatter_index or {}).get((s.get("league_code"), s.get("season_api_year")))
        if entries:
            s["deserved_scatter"] = [
                {"sotd": e["sotd"], "points": e["points"], "deserved": e["deserved"],
                 "is_self": e["team_sk"] == team_id}
                for e in entries
            ]
        seasons_out.append(s)

    return {
        "type": "team",
        "team_id": team_id,
        # Served, not computed: mart_team_profile carries team_slug, derived in the warehouse
        # from the corrected name (#852). A slug built here would be identity generation in the
        # consumption layer, and would reintroduce the provider id that is ruled out.
        "slug": featured.get("team_slug"),
        "name": featured.get("team_name"),
        "country": featured.get("team_country"),
        "crest": featured.get("team_logo_url"),
        "founded_year": featured.get("team_founded_year"),
        "venue": _venue_block(featured),
        "seasons": seasons_out,
    }


def _player_team_block(row: dict) -> dict | None:
    """The player's affiliated club for a profile row -> {team_id, name, crest, country},
    or None when the player-season has no team (honest absence). team_sk + is_current_team
    are computed in dbt (int_player_season__team); identity is joined from dim_team. The
    export only selects/reshapes — it never decides which club is current."""
    team_sk = row.get("team_sk")
    if team_sk is None:
        return None
    return {
        "team_id": int(team_sk),
        "name": row.get("team_name"),
        "crest": row.get("team_logo_url"),
        "country": row.get("team_country"),
    }


def _shape_benchmark_member(row: dict) -> dict:
    """One mart_player_competition_benchmarks row -> a Stats-screen metric entry (GAP-21).
    Select/reshape only — the "top X%"/"median"/"bottom X%" label and the good/bad reading are
    applied at render from the catalogue direction (the mart is direction-agnostic). numerator +
    denominator come straight from the mart (non-null only for the 5 ratio metrics) so the
    no-naked-% triple {num} of {den} · {pct}% can render; the export never computes them."""
    return {
        "metric_key": row.get("metric_key"),
        "metric_value": row.get("metric_value"),
        "percentile": row.get("percentile"),
        "rank": row.get("rank"),
        "peer_count": row.get("peer_count"),
        "peer_median": row.get("peer_median"),
        "vs_median_delta": row.get("vs_median_delta"),
        "numerator": row.get("metric_numerator"),
        "denominator": row.get("metric_denominator"),
    }


def _shape_benchmarks(rows: list[dict]) -> list[dict]:
    """A season's mart_player_competition_benchmarks rows -> position-group blocks (GAP-21). Grouped
    by position_group (a player benchmarked in >1 role appears once per role); minutes + appearances
    are the position's sample (constant across its metrics); metrics ordered byte-stable by metric_key
    (the frontend re-orders per the metrics_display block order and selects the position). No derivation."""
    by_pos: dict = {}
    for r in rows:
        by_pos.setdefault(r.get("position_group"), []).append(r)
    out = []
    for pos in sorted(by_pos):
        prs = by_pos[pos]
        out.append({
            "position_group": pos,
            "minutes": prs[0].get("minutes"),
            "appearances": prs[0].get("appearances"),
            "metrics": [
                _shape_benchmark_member(r)
                for r in sorted(prs, key=lambda r: r.get("metric_key") or "")
            ],
        })
    return out


def _shape_team_benchmark_member(row: dict) -> dict:
    """One mart_team_competition_benchmarks row -> a Team-Stats metric entry (GAP-23). Select/reshape
    only — the "k of N" / vs-median / spread-bar labels and the direction-mirror (only lower_better rows)
    are applied at render from the catalogue direction (the mart is direction-agnostic: rank is by value
    DESC). No num/den atoms — the team mart carries none; team ratios use the adjacent-count-row mechanism
    (metrics_display.md). The frontend renders the LOCKED 16 (dropping shots_on_goal_pct + the T/I/B sub-display)."""
    return {
        "metric_key": row.get("metric_key"),
        "metric_value": row.get("metric_value"),
        "rank": row.get("rank"),
        "team_count": row.get("team_count"),
        "league_median": row.get("league_median"),
        "league_p25": row.get("league_p25"),
        "league_p75": row.get("league_p75"),
        "vs_median_delta": row.get("vs_median_delta"),
    }


def _shape_team_benchmarks(rows: list[dict]) -> list[dict]:
    """A season's mart_team_competition_benchmarks rows -> a flat metrics[] list (GAP-23). No position
    grouping (teams have no positional peers, unlike the player Stats screen); ordered byte-stable by
    metric_key (the frontend re-orders per the metrics_display block order). No derivation."""
    return [
        _shape_team_benchmark_member(r)
        for r in sorted(rows, key=lambda r: r.get("metric_key") or "")
    ]


def _shape_career_row(row: dict) -> dict:
    """One mart_player_career row -> a Career-screen entry (GAP-22): the player's counts at one club in one
    competition-season. Select/reshape only — club grouping and the per-club/career subtotals are frontend
    display (the export computes nothing); national_appearances_total is a precomputed per-player total carried
    at the payload top level. entity_type (club/national) is carried raw so the frontend splits the sections;
    the club identity reuses _player_team_block. Internal keys (player_sk / season_sk / league_sk /
    player_career_sk) + player identity (already top-level) are dropped."""
    return {
        "season": row.get("season_api_year"),
        "competition": row.get("league_code"),
        "entity_type": row.get("entity_type"),
        "team": _player_team_block(row),
        "appearances": row.get("appearances"),
        "goals": row.get("goals_player"),
        "assists": row.get("assists_player"),
    }


def shape_player_payload(
    profile_rows: list[dict],
    match_rows: list[dict],
    benchmark_rows: list[dict] | None = None,
    career_rows: list[dict] | None = None,
) -> dict:
    """One player's profile rows + match-log rows (+ benchmark rows + career rows) -> the player page payload."""
    featured = _featured_season_row(profile_rows)
    player_id = int(featured["player_sk"])
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
    # GAP-21: per-(competition, season) benchmark rows, grouped into position-group blocks (§12).
    benchmarks_by_season: dict = {}
    for br in benchmark_rows or []:
        benchmarks_by_season.setdefault(
            (br.get("league_code"), br.get("season_api_year")), []
        ).append(br)
    # Per-season club + the single current club. is_current_team is the dbt flag
    # (int_player_season__team) — the export selects by it, it never re-ranks.
    current_team = None
    seasons_out = []
    for r in seasons:
        team = _player_team_block(r)
        if current_team is None and r.get("is_current_team"):
            current_team = team
        s = _strip_identity(r)
        for k in ("team_sk", "is_current_team"):
            s.pop(k, None)
        s["team"] = team
        s["benchmarks"] = _shape_benchmarks(
            benchmarks_by_season.get((s.get("league_code"), s.get("season_api_year")), [])
        )
        seasons_out.append(s)
    # GAP-22: the whole per-club career log (one member per club x competition x season), attached TOP-LEVEL
    # because the Career screen (13) shows the full career, not a per-season slice. Omit unresolved-identity
    # rows (null team_name = a broken team_sk FK, guarded upstream by the relationships DQ test). Order is a
    # pure SORT by two mart-shipped recency signals (no client-side aggregation): primary =
    # club_latest_kickoff_at (the club's latest match, precomputed in mart_player_career) so a club's rows are
    # CONTIGUOUS and clubs sort most-recent-first; then last_kickoff_at (within-club season order); then
    # team_sk (deterministic tie-break) — all descending. Handles a mid-season transfer / return spell
    # correctly. The frontend groups the already-club-contiguous rows and sums each club/career subtotal
    # (display only). national_appearances_total is the precomputed per-player total (constant across the
    # rows); None when the player has no career rows (honest absence — the frontend decides page generation).
    career = [
        _shape_career_row(r)
        for r in sorted(
            (cr for cr in (career_rows or []) if cr.get("team_name") is not None),
            key=lambda cr: (
                cr.get("club_latest_kickoff_at") or datetime.min,
                cr.get("last_kickoff_at") or datetime.min,
                cr["team_sk"],
            ),
            reverse=True,
        )
    ]
    national_appearances_total = (
        career_rows[0].get("national_appearances_total") if career_rows else None
    )
    return {
        "type": "player",
        "player_id": player_id,
        "slug": player_slug_with_id(featured.get("player_name"), player_id),
        "name": featured.get("player_name"),
        "nationality": featured.get("player_nationality"),
        "birth_date": featured.get("player_birth_date"),
        "photo": featured.get("player_photo_url"),
        # From the FEATURED season, not the most recent one: modal position is per season, so a
        # player fresh off a tournament was showing the position they played for their country.
        "position": featured.get("position_code"),
        "current_team": current_team,
        "seasons": seasons_out,
        "match_log": matches,
        "career": career,
        "national_appearances_total": national_appearances_total,
    }


def _fixture_side(team_id: int, identity: dict | None, w1: dict | None,
                  w2: dict | None, ctx: dict | None,
                  form_window: list | None = None, top_players: list | None = None) -> dict:
    """One team's block on the fixture page: identity + W1 form + W2 season-to-date
    + standings context + the form-window drill-down list + top players. Each
    sub-block is None/[] when that mart has no row for the side (honest absence —
    the UI renders the empty state)."""
    return {
        "team_id": team_id,
        "name": (identity or {}).get("team_name"),
        "crest": (identity or {}).get("team_logo_url"),
        "country": (identity or {}).get("team_country"),
        "w1": _drop(w1, _W1_DROP) if w1 else None,
        "w2": _drop(w2, _W2_DROP) if w2 else None,
        "standing": _drop(ctx, _CTX_DROP) if ctx else None,
        "form_window": form_window or [],
        "top_players": top_players or [],
    }


def shape_top_players(rows: list[dict], names: dict, limit: int = 5) -> list[dict]:
    """Top N players for a fixture side, SELECTED by the warehouse top_player_rank
    (goals_player -> assists_player -> key passes, computed in mart_player_momentum; the export
    does not rank). Names/photos joined from dim_player. Relies on the mart column
    being present (ship-the-mart-first); a Python ranking fallback is intentionally
    NOT provided — re-deriving the rank here would violate the consumption-layer
    contract (anti-pattern A5)."""
    ranked = sorted(
        [r for r in rows if r.get("top_player_rank") is not None and r["top_player_rank"] <= limit],
        key=lambda r: r["top_player_rank"],
    )
    out = []
    for r in ranked:
        p = _drop(r, _TOPPLAYER_DROP)
        ident = names.get(int(r["player_sk"])) or {}
        p["player_name"] = ident.get("player_name")
        p["player_photo_url"] = ident.get("player_photo_url")
        out.append(p)
    return out


def build_nav(competitions: list[dict]) -> dict:
    """Hybrid navigation from registry rows: a `groups` axis (leagues / cups /
    continental-club / national-teams) and a `countries` axis (domestic comps only).
    Pure — unit-tested without the registry file."""
    groups: dict[str, list] = {g: [] for g in _GROUP_ORDER}
    countries: dict[str, list] = {}
    for c in competitions:
        ctype = c.get("competition_type")
        group = c.get("display_group")
        if group:
            groups[group].append(c)
        if ctype in _DOMESTIC_TYPES and c.get("country"):
            countries.setdefault(c["country"], []).append(c)

    def _by_order(rows):
        return sorted(rows, key=lambda r: (r.get("sort_order") or 0, r.get("name") or ""))

    def _by_tier(rows):
        return sorted(rows, key=lambda r: (r.get("tier") or 99, r.get("sort_order") or 0))

    return {
        "groups": [
            {"key": g, "competitions": _by_order(groups[g])}
            for g in _GROUP_ORDER if groups[g]
        ],
        "countries": [
            {"country": ctry, "competitions": _by_tier(countries[ctry])}
            for ctry in sorted(countries)
        ],
    }


def _team_ref(team: dict | None) -> dict:
    """The identity a page needs to name and link a team: id, name, slug, crest."""
    return {
        "team_id": int(team["team_sk"]) if team and team.get("team_sk") is not None else None,
        "name": (team or {}).get("team_name"),
        "slug": (team or {}).get("team_slug"),
        "crest": (team or {}).get("team_logo_url"),
    }


def _fixture_ref(slug: str | None, kickoff, round_name, home: dict | None, away: dict | None,
                 fixture_id: int, goals_home=None, goals_away=None) -> dict:
    """A match the page names and links: the served slug, kickoff, round, both sides, the score
    if played. The slug is mart_competition_fixtures' fixture_slug, never built here."""
    ref = {
        "fixture_id": fixture_id,
        "slug": slug,
        "kickoff": kickoff,
        "round": round_name,
        "home": _team_ref(home),
        "away": _team_ref(away),
    }
    if goals_home is not None or goals_away is not None:
        ref["goals_home"] = goals_home
        ref["goals_away"] = goals_away
    return ref


def shape_season_summary(row: dict | None, teams: dict, slugs: dict) -> dict | None:
    """One competition-season's headline facts, each team and fixture resolved to what a page
    needs to name and link it. A null fact stays null: the page renders no row for it. No number
    is computed here — every value is a column of mart_competition_season_summary, and a match's
    slug is looked up by fixture_sk in `slugs`, the served fixture_slug column."""
    if not row:
        return None

    def _match(prefix: str) -> dict | None:
        if row.get(f"{prefix}_fixture_sk") is None:
            return None
        return _fixture_ref(
            slugs.get(int(row[f"{prefix}_fixture_sk"])),
            row.get(f"{prefix}_kickoff_datetime"), row.get(f"{prefix}_round_name"),
            teams.get(int(row[f"{prefix}_home_team_sk"])) if row.get(f"{prefix}_home_team_sk") is not None else None,
            teams.get(int(row[f"{prefix}_away_team_sk"])) if row.get(f"{prefix}_away_team_sk") is not None else None,
            int(row[f"{prefix}_fixture_sk"]),
            row.get(f"{prefix}_goals_home"), row.get(f"{prefix}_goals_away"),
        )

    def _holders(key: str) -> list[dict]:
        return [_team_ref(teams.get(int(sk))) for sk in (row.get(key) or [])]

    return {
        "matches_played": row.get("matches_played"),
        "total_goals": row.get("total_goals"),
        "goals_per_match": row.get("goals_per_match_played"),
        "home_wins": row.get("home_wins"),
        "away_wins": row.get("away_wins"),
        "drawn_matches": row.get("drawn_matches"),
        "biggest_margin": _match("biggest_margin"),
        "most_goals": _match("most_goals"),
        "longest_unbeaten_run": row.get("longest_unbeaten_run"),
        "longest_unbeaten_teams": _holders("longest_unbeaten_team_sks"),
        "longest_winless_run": row.get("longest_winless_run"),
        "longest_winless_teams": _holders("longest_winless_team_sks"),
    }


def shape_competition_payload(league_code: str, season: int, meta: dict,
                              standings: list[dict], next_matchday: list[dict],
                              deserved: list[dict], summary: dict | None,
                              fixtures: list[dict] | None = None) -> dict:
    """A competition-season page: header facts, the standings sections, the next matchday, the
    deserved-points rows, the season summary and every fixture of the season by round. Selection
    and ordering by served columns only: standings by section then rank, the matchday by kickoff,
    deserved rows by the served gap rank, rounds by the served round sequence."""
    meta = meta or {}
    return {
        "type": "competition",
        "league_code": league_code,
        "season": season,
        "slug": meta.get("slug"),
        "name": meta.get("name"),
        "crest": meta.get("logo_url"),
        "region_label_en": meta.get("region_label_en"),
        "region_label_i18n_key": meta.get("region_label_i18n_key"),
        "competition_type": meta.get("competition_type"),
        "entity_type": meta.get("entity_type"),
        "standings": sorted(
            standings, key=lambda r: (r.get("group_name") or "", r.get("standing_rank") or 999)
        ),
        "next_matchday": sorted(next_matchday, key=lambda r: r.get("kickoff") or datetime.max),
        "deserved": sorted(
            [r for r in deserved if r.get("deserved_points_gap_rank") is not None],
            key=lambda r: r["deserved_points_gap_rank"],
        ),
        "summary": summary,
        "fixtures": group_fixtures_by_round(fixtures or []),
    }


def shape_fixture_payload(fix: dict, home_side: dict, away_side: dict,
                          h2h: dict | None) -> dict:
    """The fixture page payload: header + both teams' form/standing blocks + the
    home-vs-away head-to-head record. Composed from the source marts (momentum,
    season-to-date, standing context, head-to-head) — NOT mart_matchday_insights,
    which is the MVP's presentation pivot. The slug is the served fixture_slug."""
    fid = int(fix["fixture_sk"])
    return {
        "type": "fixture",
        "fixture_id": fid,
        "slug": fix.get("fixture_slug"),
        "kickoff": fix.get("kickoff_datetime"),
        "status": fix.get("status_short"),
        "league_code": fix.get("league_code"),
        "league_name": fix.get("league_name"),
        "season": fix.get("season_api_year"),
        "round": fix.get("round_name"),
        "venue": fix.get("venue_name_snapshot"),
        "home": home_side,
        "away": away_side,
        "head_to_head": h2h,
    }


def _strip_identity(row: dict) -> dict:
    """Drop the repeated identity columns from a per-season row (they live once
    at the top of the payload, not on every season)."""
    drop = {
        "team_name", "team_slug", "team_country", "team_logo_url",
        "team_founded_year", "venue_name", "venue_city", "venue_capacity",
        "player_name", "player_first_name", "player_last_name",
        "player_nationality", "player_birth_date", "player_photo_url",
    }
    return {k: v for k, v in row.items() if k not in drop}


def build_manifest(entries: list[dict], source_counts: dict | None = None) -> dict:
    """Export manifest: per-entity type counts + the file index (for incremental
    Astro builds — each entry carries a content checksum). `source_counts` records what the
    warehouse held when the export ran — today the number of unplayed fixtures — so the site
    build can prove it carries every one of them, not only every file written."""
    counts: dict[str, int] = {}
    for e in entries:
        counts[e["type"]] = counts.get(e["type"], 0) + 1
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "source_counts": dict(source_counts or {}),
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
    # Hero scatter index — built from the WHOLE table (a league-season property), then attached to
    # each team's matching season. Built before sampling so a sampled team still gets its full league.
    scatter_idx = deserved_scatter_index(rows)
    team_ids = list(grouped.keys())[:sample] if sample else list(grouped.keys())
    # GAP-15: next fixture + last-5 results, already rank-tagged in mart_team_fixtures. Filter on
    # the precomputed ranks (selection, not derivation); scope to sampled teams on a sample run.
    fx_table = f"`{GCP_PROJECT}.{MARTS_DATASET}.mart_team_fixtures`"
    fx_where = "(upcoming_rank = 1 or recency_rank <= 5)"
    if sample:
        id_list = ", ".join(str(int(t)) for t in team_ids)
        fx_sql = f"select * from {fx_table} where {fx_where} and team_sk in ({id_list})"
    else:
        fx_sql = f"select * from {fx_table} where {fx_where}"
    fixtures_by_team = _group_by(_query(client, fx_sql), "team_sk")
    # GAP-20: the roster (identity) per (team, competition-season) from mart_roster. Scope to the
    # sampled teams on a sample run; whole-table otherwise (selection, not derivation).
    roster_table = f"`{GCP_PROJECT}.{MARTS_DATASET}.mart_roster`"
    if sample:
        id_list = ", ".join(str(int(t)) for t in team_ids)
        roster_sql = f"select * from {roster_table} where team_sk in ({id_list})"
    else:
        roster_sql = f"select * from {roster_table}"
    roster_by_team = _group_by(_query(client, roster_sql), "team_sk")
    # GAP-23: rank-vs-league benchmark per (team, competition-season) from
    # mart_team_competition_benchmarks. Scope to the sampled teams on a sample run; whole-table
    # otherwise (selection, not derivation), exactly like the roster block above.
    bench_table = f"`{GCP_PROJECT}.{MARTS_DATASET}.mart_team_competition_benchmarks`"
    if sample:
        id_list = ", ".join(str(int(t)) for t in team_ids)
        bench_sql = f"select * from {bench_table} where team_sk in ({id_list})"
    else:
        bench_sql = f"select * from {bench_table}"
    bench_by_team = _group_by(_query(client, bench_sql), "team_sk")
    # Squad tab: per-player season stats from mart_player_career, scoped by team_sk on a sample run
    # (like the roster/benchmark blocks); shape_team_payload joins them onto squad members. Selection.
    career_table = f"`{GCP_PROJECT}.{MARTS_DATASET}.mart_player_career`"
    if sample:
        id_list = ", ".join(str(int(t)) for t in team_ids)
        career_sql = f"select * from {career_table} where team_sk in ({id_list})"
    else:
        career_sql = f"select * from {career_table}"
    career_by_team = _group_by(_query(client, career_sql), "team_sk")
    return [
        shape_team_payload(
            grouped[t], fixtures_by_team.get(t, []), roster_by_team.get(t, []),
            bench_by_team.get(t, []), scatter_idx, career_by_team.get(t, []),
        )
        for t in team_ids
    ]


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
    # GAP-21: per-player benchmark rows from mart_player_competition_benchmarks (scoped to the
    # sampled players on a sample run, like the match log). Selection only.
    bench_table = f"`{GCP_PROJECT}.{MARTS_DATASET}.mart_player_competition_benchmarks`"
    if sample:
        bench_sql = f"select * from {bench_table} where player_sk in ({id_list})"
    else:
        bench_sql = f"select * from {bench_table}"
    by_player_bench = _group_by(_query(client, bench_sql), "player_sk")
    # GAP-22: per-player career rows from mart_player_career (scoped to the sampled players on a sample run,
    # like the match log + benchmark rows). Selection only.
    career_table = f"`{GCP_PROJECT}.{MARTS_DATASET}.mart_player_career`"
    if sample:
        career_sql = f"select * from {career_table} where player_sk in ({id_list})"
    else:
        career_sql = f"select * from {career_table}"
    by_player_career = _group_by(_query(client, career_sql), "player_sk")
    return [
        shape_player_payload(
            by_player[pid],
            by_player_log.get(pid, []),
            by_player_bench.get(pid, []),
            by_player_career.get(pid, []),
        )
        for pid in player_ids
        if pid in wanted
    ]


def fetch_fixture_payloads(client, sample: int = 0, source_counts: dict | None = None) -> list[dict]:
    """One payload per unplayed fixture, every competition. The slug is joined from
    mart_competition_fixtures, the one place a match's URL segment is built. When `source_counts`
    is given it receives the number of unplayed fixtures the warehouse held before any sampling,
    for the manifest."""
    marts = f"{GCP_PROJECT}.{MARTS_DATASET}"
    fixtures = _query(client, f"""
        select f.fixture_sk, f.league_sk, f.league_code, f.season_api_year, f.kickoff_datetime,
               f.round_name, f.status_short, f.venue_name_snapshot, f.home_team_sk, f.away_team_sk,
               c.fixture_slug
        from `{GCP_PROJECT}.core.fct_fixture` as f
        inner join `{marts}.mart_competition_fixtures` as c on f.fixture_sk = c.fixture_sk
        where f.status_short in ('NS', 'TBD') and f.fixture_date >= current_date()
    """)
    fixtures.sort(key=lambda r: r.get("kickoff_datetime") or datetime.max)
    if source_counts is not None:
        source_counts["fixtures_unplayed"] = len(fixtures)
    if sample:
        fixtures = fixtures[:sample]
    if not fixtures:
        return []
    fid_in = ", ".join(str(int(f["fixture_sk"])) for f in fixtures)

    teams = {
        int(r["team_sk"]): r
        for r in _query(client, f"select team_sk, team_name, team_logo_url, team_country "
                                f"from `{GCP_PROJECT}.core.dim_team`")
    }
    leagues = {
        int(r["league_sk"]): r.get("league_name")
        for r in _query(client, f"select league_sk, league_name "
                                f"from `{GCP_PROJECT}.core.dim_league`")
    }
    w1 = {
        (int(r["upcoming_fixture_sk"]), int(r["team_sk"])): r
        for r in _query(client, f"select * from `{marts}.mart_team_momentum` "
                                f"where upcoming_fixture_sk in ({fid_in})")
    }
    w2 = {
        (int(r["upcoming_fixture_sk"]), int(r["team_sk"])): r
        for r in _query(client, f"select * from `{marts}.mart_team_season_record` "
                                f"where upcoming_fixture_sk in ({fid_in})")
    }
    ctx = {
        (int(r["fixture_sk"]), int(r["team_sk"])): r
        for r in _query(client, f"select * from `{marts}.mart_fixture_standing_context` "
                                f"where fixture_sk in ({fid_in})")
    }
    # Pure selection of exactly the directed (home, away) H2H rows — one per fixture —
    # filtered by the natural (team_sk, opponent_team_sk) key the fixtures already carry.
    # No pair identity is derived here (the canonical pair_key lives in mart_head_to_head,
    # GAP-19.4) and the directed filter does not over-fetch (no team-id cross product).
    pairs = [
        (int(f["home_team_sk"]), int(f["away_team_sk"]))
        for f in fixtures
        if f.get("home_team_sk") is not None and f.get("away_team_sk") is not None
    ]
    h2h: dict = {}
    if pairs:
        conds = " or ".join(
            f"(team_sk = {h} and opponent_team_sk = {a})" for h, a in pairs
        )
        for r in _query(client, f"select * from `{marts}.mart_head_to_head` where {conds}"):
            h2h[(int(r["team_sk"]), int(r["opponent_team_sk"]))] = r

    # Drill-down: the last-5 form-window list and top players per side.
    form_window: dict = {}
    for r in _query(client, f"select * from `{marts}.mart_team_momentum_window` "
                            f"where upcoming_fixture_sk in ({fid_in})"):
        form_window.setdefault((int(r["upcoming_fixture_sk"]), int(r["team_sk"])), []).append(
            _drop(r, _FW_DROP)
        )
    mom_players: dict = {}
    for r in _query(client, f"select * from `{marts}.mart_player_momentum` "
                            f"where upcoming_fixture_sk in ({fid_in})"):
        mom_players.setdefault((int(r["upcoming_fixture_sk"]), int(r["team_sk"])), []).append(r)
    player_names = {
        int(r["player_sk"]): r
        for r in _query(client, f"select player_sk, player_name, player_photo_url "
                                f"from `{GCP_PROJECT}.core.dim_player`")
    }

    def _side(fid, team_id):
        return _fixture_side(
            team_id, teams.get(team_id), w1.get((fid, team_id)), w2.get((fid, team_id)),
            ctx.get((fid, team_id)),
            form_window=sorted(form_window.get((fid, team_id), []),
                               key=lambda r: r.get("recency_rank") or 99),
            top_players=shape_top_players(mom_players.get((fid, team_id), []), player_names),
        )

    payloads = []
    for f in fixtures:
        fid = int(f["fixture_sk"])
        h, a = int(f["home_team_sk"]), int(f["away_team_sk"])
        f["league_name"] = leagues.get(int(f["league_sk"])) if f.get("league_sk") is not None else None
        f["home_team_name"] = (teams.get(h) or {}).get("team_name")
        f["away_team_name"] = (teams.get(a) or {}).get("team_name")
        h2h_row = h2h.get((h, a))
        payloads.append(
            shape_fixture_payload(f, _side(fid, h), _side(fid, a),
                                  _drop(h2h_row, _H2H_DROP) if h2h_row else None)
        )
    return payloads


def _display_group_of_type(seed_path: str = COMPETITION_TYPES_SEED_PATH) -> dict:
    """competition_type -> nav display_group, from the competition_types seed
    (GAP-19.3). Empty cell -> None (the type does not appear in the nav). Reading
    the seed is the sanctioned taxonomy lookup; the mapping is not hardcoded here."""
    import csv

    with open(seed_path, encoding="utf-8", newline="") as fh:
        return {
            row["competition_type"]: (row.get("display_group") or None)
            for row in csv.DictReader(fh)
        }


def _registry_competitions(registry_path: str = REGISTRY_PATH) -> list[dict]:
    import yaml

    data = yaml.safe_load(open(registry_path, encoding="utf-8"))
    fields = ("league_code", "name", "slug", "country", "confederation",
              "tier", "sort_order", "competition_type")
    group_of_type = _display_group_of_type()
    return [
        {**{k: o.get(k) for k in fields},
         "display_group": group_of_type.get(o.get("competition_type"))}
        for o in (data.get("competitions") or [])
        if isinstance(o, dict) and "competition_type" in o
    ]


def fetch_nav(registry_path: str = REGISTRY_PATH) -> dict:
    """nav.json — registry-driven hybrid navigation (no BigQuery)."""
    return build_nav(_registry_competitions(registry_path))


def _warehouse_competition_meta(client) -> dict[str, dict]:
    """league_code -> the competition facts the SITE displays, from `mart_competition_index`.

    ⛔ THE REGISTRY IS INPUT; THE WAREHOUSE IS WHAT THE SITE DISPLAYS. Both carry a competition
    name and they are NOT the same string: `docs/competition_registry.yml` carries the formal name,
    the mart carries the standardised one. Swept across the whole registry — 37 identical,
    11 DIFFERENT:

        BL1   `1. Fußball-Bundesliga`          -> `Bundesliga`
        BL2   `2. Fußball-Bundesliga`          -> `2. Bundesliga`
        UECL  `UEFA Europa Conference League`  -> `UEFA Conference League`
        WCQ*  `WC Qualification <x>`           -> `World Cup Qualification <x>`  (all seven)
        WC    `FIFA World Cup 2026`            -> `FIFA World Cup`

    The last one is the reason this is a rule and not a preference: a YEAR INSIDE A NAME is a
    defect, not a naming choice — a season-scoped label is COMPOSED in the warehouse, an entity row
    carries its name only. Reading the registry would have shown `FIFA World Cup 2026` for all of
    2027. And 37 of 48 being identical is exactly why it hid: the wrong source looks right until it
    meets a competition that standardisation actually changed.

    ⚠ `region_rank` comes from the same read for the related reason: the registry carries
    `confederation`, and turning that into a rank is a taxonomy mapping the consumption-layer
    contract forbids here. Same mart `fetch_competition_index` reads.

    ONE helper, both consumers — `fetch_landing_payload`'s `meta` (the fixtures hero's group
    headings and both board blocks' league names) and `_competitions_index`
    (`competitions.json`, which TeamHeader renders on every team page). They read the registry for
    everything else and overlay this; splitting the rule across the two call sites is what let one
    of them drift."""
    served = {}
    for row in _query(client, f"select league_code, competition_name, region_rank "
                              f"from `{GCP_PROJECT}.{MARTS_DATASET}.mart_competition_index`"):
        # A NULL name is left to the registry rather than blanking the heading. Nothing is
        # renamed here and no name is composed — the served string is carried across as-is.
        entry = {"region_rank": row.get("region_rank")}
        if row.get("competition_name"):
            entry["name"] = row["competition_name"]
        served[row["league_code"]] = entry
    return served


def _competitions_index(client=None, registry_path: str = REGISTRY_PATH) -> dict:
    """league_code -> {name, slug} for every registry competition.

    The frontend's competition slug/name lookup for ALL active leagues
    (site_v2/src/data/competitions.json): the fixture page resolves its URL competition segment from
    it and TeamHeader reads the display name. Same shape already built inline for leaderboards.

    The SLUG is the registry's — it is an assigned identifier, not a display string. The NAME is
    the warehouse's whenever a client is given; see `_warehouse_competition_meta` for why. Without
    a client this falls back to registry names, which is the offline shape the unit test uses —
    never the shape a real export runs, because `export_all` always has a client."""
    served = _warehouse_competition_meta(client) if client is not None else {}
    return {
        c["league_code"]: {
            "name": served.get(c["league_code"], {}).get("name") or c.get("name"),
            "slug": c.get("slug"),
        }
        for c in _registry_competitions(registry_path)
    }


_COMPETITION_INDEX_KEEP = (
    "league_code", "competition_type", "entity_type", "slug",
    "category_label_en", "category_label_i18n_key", "confederation", "region_rank",
    "competition_name", "logo_url", "next_kickoff_datetime", "last_kickoff_datetime",
    "region_label_en", "region_label_i18n_key",
)


def shape_competition_index(rows: list[dict]) -> list[dict]:
    """mart_competition_index rows, projected to the columns the competitions index page (#54)
    renders. Pure passthrough otherwise -- the mart already resolves the category label, the
    region label and the ordering FACTS (region_rank, next/last kickoff); this function adds no
    logic. It does not sort or filter: the mart carries facts, the page spec declares the ORDER BY
    (#62 step 4)."""
    return [{k: r.get(k) for k in _COMPETITION_INDEX_KEEP} for r in rows]


def fetch_competition_index(client) -> dict:
    """competition_index.json -- mart_competition_index, one row per competition: the single
    source for the competitions index page (#54, #62 step 4). Ordered by league_code only, for a
    deterministic export diff -- NOT the page's display order, which the page spec applies at
    render time from the ordering facts this mart carries (region_rank, next/last kickoff)."""
    rows = _query(
        client,
        f"select * from `{GCP_PROJECT}.{MARTS_DATASET}.mart_competition_index` "
        f"order by league_code",
    )
    return {"type": "competition_index", "competitions": shape_competition_index(rows)}


def _group2(rows: list[dict], k1: str, k2: str) -> dict:
    g: dict = {}
    for r in rows:
        g.setdefault((r[k1], int(r[k2])), []).append(r)
    return g


_STANDING_DROP = {"standing_sk", "season_sk", "league_sk", "competition_type",
                  "entity_type", "team_api_id", "season_api_year", "league_code",
                  "group_description"}


_COMPETITION_PAGE_META = ("logo_url", "region_label_en", "region_label_i18n_key",
                          "competition_type", "entity_type")


def _competition_page_meta(client) -> dict[str, dict]:
    """league_code -> the header facts the competition page shows, from `mart_competition_index`:
    the crest, the region label and its copy key, the competition and entity kind. The name and
    the slug come through `_warehouse_competition_meta` and the registry as everywhere else."""
    return {
        row["league_code"]: {k: row.get(k) for k in _COMPETITION_PAGE_META}
        for row in _query(client, f"select league_code, {', '.join(_COMPETITION_PAGE_META)} "
                                  f"from `{GCP_PROJECT}.{MARTS_DATASET}.mart_competition_index`")
    }


def fetch_competition_payloads(client, sample: int = 0, registry_path: str = REGISTRY_PATH) -> list[dict]:
    """competitions/{league_code}/{season}.json — one per competition-season with standings.

    Every block is a mart read whole or filtered by served columns: the standings row as
    published (with its section kind), the next matchday with the warehouse's "match that
    matters" flag, the team profile's deserved-points columns, the season summary. Team identity
    is joined from dim_team so a row can be named and linked; nothing is computed."""
    marts = f"{GCP_PROJECT}.{MARTS_DATASET}"
    meta = {
        c["league_code"]: {"name": c.get("name"), "slug": c.get("slug")}
        for c in _registry_competitions(registry_path)
    }
    for league_code, served in _warehouse_competition_meta(client).items():
        if league_code in meta:
            meta[league_code].update(served)
    for league_code, served in _competition_page_meta(client).items():
        if league_code in meta:
            meta[league_code].update(served)
    for m in meta.values():
        m.pop("region_rank", None)

    teams = {
        int(r["team_sk"]): r
        for r in _query(client, f"select team_sk, team_name, team_slug, team_logo_url "
                                f"from `{GCP_PROJECT}.core.dim_team`")
    }
    standings = _group2(
        _query(client, f"select * from `{marts}.mart_standings`"),
        "league_code", "season_api_year",
    )
    matchday = _group2(
        _query(client, f"""
            select fixture_sk, league_code, season_api_year, kickoff_datetime, round_name,
                   home_team_sk, away_team_sk, is_match_that_matters
            from `{marts}.mart_next_matchday`
        """),
        "league_code", "season_api_year",
    )
    deserved = _group2(
        _query(client, f"""
            select league_code, season_api_year, team_sk, points, deserved_points,
                   deserved_points_gap, deserved_points_gap_rank
            from `{marts}.mart_team_profile`
        """),
        "league_code", "season_api_year",
    )
    summaries = {
        (r["league_code"], int(r["season_api_year"])): r
        for r in _query(client, f"select * from `{marts}.mart_competition_season_summary`")
    }
    # Every fixture of every competition-season, whole: the Matchdays tab's rows, and the one
    # source of a match's slug for every other block that links a match.
    fixture_rows = _query(client, f"""
        select fixture_sk, league_code, season_api_year, round_name, round_order, round_sequence,
               fixture_order, kickoff_datetime, status_short, is_played, goals_home, goals_away,
               home_team_sk, home_team_name, home_team_slug, home_team_logo_url,
               away_team_sk, away_team_name, away_team_slug, away_team_logo_url,
               fixture_slug, is_next_round, is_match_that_matters
        from `{marts}.mart_competition_fixtures`
    """)
    fixtures = _group2(fixture_rows, "league_code", "season_api_year")
    slugs = {int(r["fixture_sk"]): r.get("fixture_slug") for r in fixture_rows}

    # A competition-season has a page when any block has something to show: a cup has no
    # standings but a next round, a season summary and its rounds.
    combos = sorted(set(standings) | set(matchday) | set(summaries) | set(fixtures))
    if sample:
        combos = combos[:sample]
    if not combos:
        return []

    def _standing(r: dict) -> dict:
        row = _drop(r, _STANDING_DROP)
        row["team_slug"] = (teams.get(int(r["team_sk"])) or {}).get("team_slug")
        return row

    def _next(r: dict) -> dict:
        home = teams.get(int(r["home_team_sk"])) if r.get("home_team_sk") is not None else None
        away = teams.get(int(r["away_team_sk"])) if r.get("away_team_sk") is not None else None
        ref = _fixture_ref(slugs.get(int(r["fixture_sk"])), r.get("kickoff_datetime"),
                           r.get("round_name"), home, away, int(r["fixture_sk"]))
        ref["is_match_that_matters"] = bool(r.get("is_match_that_matters"))
        return ref

    def _fixture(r: dict) -> dict:
        return {
            "fixture_id": int(r["fixture_sk"]),
            "slug": r.get("fixture_slug"),
            "kickoff": r.get("kickoff_datetime"),
            "round": r.get("round_name"),
            "round_order": r.get("round_order"),
            "round_sequence": r.get("round_sequence"),
            "fixture_order": int(r["fixture_order"]),
            "status": r.get("status_short"),
            "is_played": bool(r.get("is_played")),
            "goals_home": r.get("goals_home"),
            "goals_away": r.get("goals_away"),
            "home": {"team_id": int(r["home_team_sk"]), "name": r.get("home_team_name"),
                     "slug": r.get("home_team_slug"), "crest": r.get("home_team_logo_url")},
            "away": {"team_id": int(r["away_team_sk"]), "name": r.get("away_team_name"),
                     "slug": r.get("away_team_slug"), "crest": r.get("away_team_logo_url")},
            "is_next_round": bool(r.get("is_next_round")),
            "is_match_that_matters": bool(r.get("is_match_that_matters")),
        }

    def _deserved(r: dict) -> dict:
        return {
            **_team_ref(teams.get(int(r["team_sk"]))),
            "points": r.get("points"),
            "deserved_points": r.get("deserved_points"),
            "deserved_points_gap": r.get("deserved_points_gap"),
            "deserved_points_gap_rank": r.get("deserved_points_gap_rank"),
        }

    payloads = []
    for (lc, season) in combos:
        payloads.append(shape_competition_payload(
            lc, season, meta.get(lc),
            [_standing(r) for r in standings.get((lc, season), [])],
            [_next(r) for r in matchday.get((lc, season), [])],
            [_deserved(r) for r in deserved.get((lc, season), [])],
            shape_season_summary(summaries.get((lc, season)), teams, slugs),
            [_fixture(r) for r in fixtures.get((lc, season), [])],
        ))
    return payloads


def shape_leaderboards(rows: list[dict], metrics=_LEADERBOARD_METRICS,
                       limit: int = 10) -> dict:
    """Per-board player leaderboards from mart_leaderboards (LONG): the warehouse already
    ranked (DENSE_RANK, top-10 inclusive of ties) and tagged each row with metric_key + rank.
    The export groups by metric_key and orders by rank — it does not rank. Ties share a rank,
    so a board may exceed `limit` when ranks tie at the cut."""
    boards: dict = {m: [] for m in metrics}
    for r in rows:
        m = r.get("metric_key")
        if m in boards and r.get("rank") is not None and r["rank"] <= limit:
            boards[m].append(r)
    for m in boards:
        boards[m] = [{k: r.get(k) for k in _LB_KEEP}
                     for r in sorted(boards[m], key=lambda r: r["rank"])]
    return boards


def fetch_leaderboard_payloads(client, sample: int = 0, registry_path: str = REGISTRY_PATH) -> list[dict]:
    meta = {
        c["league_code"]: {"name": c.get("name"), "slug": c.get("slug")}
        for c in _registry_competitions(registry_path)
    }
    grouped = _group2(
        _query(client, f"select * from `{GCP_PROJECT}.{MARTS_DATASET}.mart_leaderboards`"),
        "league_code", "season_api_year",
    )
    keys = sorted(grouped.keys())
    if sample:
        keys = keys[:sample]
    out = []
    for (lc, season) in keys:
        boards = shape_leaderboards(grouped[(lc, season)])
        if not any(boards.values()):
            continue
        out.append({
            "type": "leaderboards", "league_code": lc, "season": season,
            "slug": (meta.get(lc) or {}).get("slug"),
            "name": (meta.get(lc) or {}).get("name"), "boards": boards,
        })
    return out


def group_upcoming_fixtures(fixtures: list[dict], teams: dict, meta: dict) -> list[dict]:
    """The landing hero: THE NEXT MATCHDAY — every fixture on the earliest upcoming kickoff date —
    grouped by competition.

    ⚠ THIS FUNCTION NO LONGER SELECTS ANYTHING. It groups every fixture it is handed and truncates
    nothing — the retired `_HERO_FIXTURE_LIMIT = 12` slice is gone, and the matchday
    restriction is a WHERE clause in `fetch_landing_payload`'s query, beside the
    upcoming-window filter that has always lived there. Keeping the day selection out of Python is
    the same call #846 forced on `_featured_season_row`.

    GROUPING ONLY — no ordering business rule lives here either. `fixtures` arrives kickoff-ordered
    from the caller, so the payload's group order is first-appearance order, which is a
    deterministic export diff and NOT the display order: the PAGE applies the site-wide ordering
    key (`site_v2/src/lib/competitionOrder.mjs`), per the ruling "the mart carries facts, the spec
    declares the ORDER BY".
    """
    groups: dict = {}
    for f in fixtures:
        league_code = f.get("league_code")
        comp = meta.get(league_code) or {}
        group = groups.setdefault(league_code, {
            "league_code": league_code,
            "league_name": comp.get("name"),
            "competition_slug": comp.get("slug"),
            # The page's ordering key needs this; it is SERVED, never derived here. It comes from
            # mart_competition_index (which publishes it from the confederations seed) — mapping
            # confederation -> rank in this file would be a taxonomy mapping, which the
            # consumption-layer contract forbids outright.
            "region_rank": comp.get("region_rank"),
            "season": f.get("season_api_year"),
            "fixtures": [],
        })
        home = teams.get(int(f["home_team_sk"])) if f.get("home_team_sk") is not None else None
        away = teams.get(int(f["away_team_sk"])) if f.get("away_team_sk") is not None else None
        fixture_id = int(f["fixture_sk"])
        group["fixtures"].append({
            "fixture_id": fixture_id,
            "slug": f.get("fixture_slug"),
            "kickoff": f.get("kickoff_datetime"),
            "round": f.get("round_name"),
            "home": _landing_side(home),
            "away": _landing_side(away),
        })
    return list(groups.values())


def _landing_side(team: dict | None) -> dict:
    """One side of a hero fixture row: display identity only, no stats."""
    return {
        "team_id": int(team["team_sk"]) if team and team.get("team_sk") is not None else None,
        "name": (team or {}).get("team_name"),
        "slug": (team or {}).get("team_slug"),
        "crest": (team or {}).get("team_logo_url"),
    }


def _board_catalogue(
    boards: tuple[str, ...] = _HOME_PLAYER_BOARDS,
    entity: str = "player",
    seed_path: str = CATALOGUE_SEED_PATH,
) -> dict[str, dict[str, str]]:
    """metric_id -> {label_i18n_key, format} for a set of home boards, from the catalogue seed.

    The board's NAME and its NUMBER FORMAT are both the metric's, and the catalogue is the only
    source of either (#327). Carrying the KEY rather than the words keeps the name governed: the
    export ships an identifier, the frontend resolves it per locale through `metricLabel()`, and
    nothing hand-types a board name in either place. The format travels for the same reason and a
    sharper one — the TEAM boards do not share a single format (goals and shots on goal are
    `decimal_1`, passes and duels are `decimal_0`), so a frontend that picked one would render half
    of them wrong.

    ⚠ KEYED ON (metric_id, entity), and the entity leg is load-bearing now that both a player and a
    team board set read this. export_metric_definitions_json.py had exactly this bug from keying
    on metric_id alone.
    ⚠ An earlier version of this docstring claimed "two of the ids here also carry a TEAM row".
    That was false and is corrected rather than softened: measured over the seed, 0 of 86 metric_ids
    are defined for more than one entity. The filter guards a collision the catalogue PERMITS —
    `assert_metric_catalogue_unique_by_entity` enforces uniqueness per (metric_id, entity), not
    globally — rather than one it currently contains.
    """
    import csv

    with open(seed_path, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("entity") == entity]
    by_id = {r["metric_id"]: r for r in rows}
    missing = [k for k in boards if not (by_id.get(k) or {}).get("label_i18n_key")]
    if missing:
        raise KeyError(
            f"no {entity} label_i18n_key in {seed_path} for: {', '.join(missing)}. "
            "A board name is a governed value; it is never defaulted to the metric id."
        )
    no_format = [k for k in boards if not by_id[k].get("format")]
    if no_format:
        raise KeyError(
            f"no {entity} format in {seed_path} for: {', '.join(no_format)}. "
            "A board's number format is the catalogue's, never the component's."
        )
    return {
        k: {"label_i18n_key": by_id[k]["label_i18n_key"], "format": by_id[k]["format"]}
        for k in boards
    }


def shape_home_top_players(rows: list[dict], meta: dict, label_keys: dict[str, str]) -> list[dict]:
    """The home page's Top players block: four boards, one metric each, one player per league.

    ⚠ NOT `shape_top_players` above — that is the FIXTURE page's players-to-watch list. Different
    block, different mart, different shape; the names are one word apart on purpose because they
    are both "top players" to a reader and nothing else about them is shared.

    Design: GitLab #40, which `design-mocks/README.md` names as the authority. Four boards in a
    fixed order, ranked descending, top 7. The board is a `metric_key` in `mart_leaderboards`; the
    board's NAME is the catalogue's `label_en` and is resolved by the frontend, not here.

    ONE PLAYER PER LEAGUE, not a pooled ranking (GAP-31 withdrawn). The warehouse decides which
    player that is, via `league_leader_order`; this function only groups the rows it
    is handed into boards, keeps their order, and cuts each at 7. It sorts nothing.
    ⚠ #40's text still says "a pooled board ranks across seven leagues"; that sentence is
    superseded, though the rule it justified (every row shows club AND league) stands.
    ⚠ `rank == 1` is NOT one per league and was the defect here: the mart ranks with DENSE_RANK, so
    ties share rank 1. Fixing it in Python was ALSO wrong — the ruling is "All ranking and
    ordering lives in the warehouse. The page renders the order it is served."

    A BOARD WITH NO ROWS IS OMITTED ENTIRELY (the ruling: *"if a board is missing, the user may
    not even notice, so don't show"*) — no placeholder, no empty state — and the survivors keep
    their order. An empty result here means the block does not render at all.
    ⚠ That is invisible to the reader BY DESIGN, so it is invisible to us too:
    `assert_mart_leaderboards_every_home_board_has_a_leader` is what notices, not the page.

    Selection only: `elite`, current season, rank 1. `is_current_season` is a SERVED column —
    picking the season here would be the window selection #846 moved out of this file.
    """
    by_board: dict[str, list[dict]] = {key: [] for key in _HOME_PLAYER_BOARDS}
    for row in rows:
        key = row.get("metric_key")
        if key not in by_board:
            continue
        league_code = row.get("league_code")
        by_board[key].append({
            "player_id": row.get("player_sk"),
            "slug": player_slug_with_id(row.get("player_name"), row.get("player_sk")),
            "name": row.get("player_name"),
            "club": row.get("team_name"),
            "club_slug": row.get("team_slug"),
            "crest": row.get("team_logo_url"),
            "league_code": league_code,
            "league_name": (meta.get(league_code) or {}).get("name"),
            "value": row.get("sort_value"),
        })

    boards = []
    for key in _HOME_PLAYER_BOARDS:
        # NO SORTING HERE, DELIBERATELY. The rows arrive in the order the query asked the warehouse
        # for, and this preserves it — "the page renders the order it is served". An earlier
        # version of this file deduped and sorted in Python; that was ranking in the consumption
        # layer.
        # One row per league is now a WAREHOUSE fact too: `league_leader_order = 1` in the query
        # below, a column whose tie rule (fewer minutes, then player_sk) lives in
        # `mart_leaderboards` and is asserted by `assert_mart_leaderboards_one_leader_per_league`.
        entries = by_board[key]
        if not entries:
            continue
        boards.append({
            "metric_key": key,
            "label_i18n_key": label_keys[key]["label_i18n_key"],
            "rows": entries[:_HOME_BOARD_ROWS],
        })
    return boards


def shape_home_top_teams(rows: list[dict], meta: dict, catalogue: dict[str, dict]) -> list[dict]:
    """The home page's Top teams block (#41): four boards, one metric each, one team per league.

    The team mirror of `shape_home_top_players`, and deliberately the same shape — group the served
    rows into boards, keep their order, cut each at 7. It sorts nothing and picks nothing: the
    warehouse decides which team represents a league (`league_leader_order`) and in what order the
    representatives appear (`board_leader_order`), per the ruling that all ranking and ordering
    lives there. Reaching that state took #40 several failed reviews; this starts in it.

    ⚠ THE FORMAT IS CARRIED PER BOARD, unlike the player block where all four are integers. Goals
    and shots on goal are `decimal_1`, passes and duels are `decimal_0`, and the catalogue is what
    says so — a component that chose a formatter would render one pair of boards wrong.

    ⚠ EVERY ROW CARRIES A SLUG AND EVERY ROW LINKS OUT, exactly like the player rows. #41: "Every
    row links out. That is why the block exists." The payloads those links resolve to are committed
    — 20 of them, allowlisted in `.gitignore` — which is the procedure `site_v2/src/data/README.md`
    already sets out for a committed sample that is a SET, and the same reason the linked fixtures
    are committed.
    ⛔ THIS PARAGRAPH ONCE SAID THE OPPOSITE. It claimed "NO SLUG AND NO LINK", justified by only
    one team payload being committed — while the code seven lines below
    set a slug and `TopTeams.astro` wrapped every row in an anchor. The correction was swept through
    the component, the tests and the contract and missed HERE, in the docstring of the very function
    that emits the slug. Replaced, not softened.

    A BOARD WITH NO ROWS IS OMITTED ENTIRELY, and if none survives the block does not render at all
    — the same rule as the player block.
    """
    by_board: dict[str, list[dict]] = {key: [] for key in _HOME_TEAM_BOARDS}
    for row in rows:
        key = row.get("metric_key")
        if key not in by_board:
            continue
        league_code = row.get("league_code")
        by_board[key].append({
            "team_id": row.get("team_sk"),
            # SERVED, never derived: `dim_team.team_slug` is the assigned slug (#852), so this file
            # generates no identity — the same rule the fixture and player slugs follow.
            "slug": row.get("team_slug"),
            "name": row.get("team_name"),
            "crest": row.get("team_logo_url"),
            "league_code": league_code,
            "league_name": (meta.get(league_code) or {}).get("name"),
            "value": row.get("sort_value"),
        })

    boards = []
    for key in _HOME_TEAM_BOARDS:
        entries = by_board[key]
        if not entries:
            continue
        boards.append({
            "metric_key": key,
            "label_i18n_key": catalogue[key]["label_i18n_key"],
            "format": catalogue[key]["format"],
            "rows": entries[:_HOME_BOARD_ROWS],
        })
    return boards


def shape_landing_payload(
    upcoming: list[dict],
    top_players: list[dict] | None = None,
    top_teams: list[dict] | None = None,
) -> dict:
    """landing.json — the home modules, in the order the spec composes them.

    Pure assembly of already-shaped parts, so the whole payload is unit-testable without
    BigQuery. Spec: docs/wireframes/10_home.md §0, which is that spec's stated authority.

    ALL THREE modules: next matches -> Top players -> Top teams (10_home.md §0). Top players
    landed with #40 and Top teams with #41; the composition is complete.

    Three blocks were removed rather than carried, and all three removals deleted
    consumption-layer violations as a side effect:

    - The stats teasers (top scorers + a league-table snippet), ruled useless. Their helpers
      `eligible_stats_competitions` and `pick_stats_competition` judged season eligibility and
      then ranked competitions by registry sort_order — result judgement and business ranking in
      the export, which `layering.md` forbids outright.
    - Trending, which is not in the composition above. It was also stale against the last ruling
      that touched it (three team streak types, winning/unbeaten/clean-sheet, with "winless and
      losing are both dropped"), while the built mart still served five signals including
      `winless`, no player streaks and no start dates.
    - Browse, DROPPED (not deferred): "drop the browse section". Its only real
      value was reachability into the long-tail team/player pages, and both are already blocked
      on the team/player-name data-quality work, so a competitions-only version had nothing left
      to solve — the competitions index page already covers that pool. `build_nav`/`fetch_nav`
      are NOT removed with it: `nav.json` is an independently-selectable export target
      (`--entities nav`), untouched by this change.
    """
    payload = {
        "type": "landing",
        "upcoming": upcoming,
    }
    # Present only when a board survived. #40: a board with no data is not rendered, and if no
    # board has data the block itself does not render — so an EMPTY list must not reach the page as
    # a key it then has to guard against. Absent means absent.
    if top_players:
        payload["top_players"] = top_players
    if top_teams:
        payload["top_teams"] = top_teams
    return payload


def fetch_landing_payload(client, registry_path: str = REGISTRY_PATH) -> dict:
    """Read the landing module that exists today: upcoming fixtures.

    THREE BigQuery reads, unchanged by dropping browse below (it was registry-driven and read
    nothing either way): `mart_next_matchday` and `core.dim_team` for the hero, plus
    `mart_competition_index` for `region_rank` (below). The stats teasers
    (`mart_leaderboards` + `mart_standings`) and trending (`mart_landing_trending`) were removed,
    and browse (registry-driven, read nothing) was dropped (see `shape_landing_payload`) — their
    queries and, for browse, its `fetch_nav` call here, went with them.
    """
    meta = {
        c["league_code"]: {
            "name": c.get("name"), "slug": c.get("slug"),
        }
        for c in _registry_competitions(registry_path)
    }

    # ⚠ THE DISPLAY NAME IS OVERWRITTEN FROM THE MART — see `_warehouse_competition_meta`, which
    # holds the rule and the evidence for it. `group_upcoming_fixtures` reads `comp["name"]` from
    # this dict, so the fixtures hero's group headings are fixed by the same overlay as the boards.
    #
    # ⚠ `sort_order` is deliberately NOT carried any more: it is retired as an ordering basis and
    # nothing in this payload consumed it.
    for league_code, served in _warehouse_competition_meta(client).items():
        if league_code in meta:
            meta[league_code].update(served)

    # THE MATCHDAY IS SERVED, NOT SELECTED. `mart_next_matchday` is every competition's next round
    # — the warehouse decides which round that is and which fixtures belong to it; this read
    # takes the table whole. The fixture pages use the same upcoming definition the mart does, so
    # the hero can never advertise a match that has no page.
    fixtures = _query(client, f"""
        select n.fixture_sk, n.league_code, n.season_api_year, n.kickoff_datetime, n.round_name,
               n.home_team_sk, n.away_team_sk, c.fixture_slug
        from `{GCP_PROJECT}.{MARTS_DATASET}.mart_next_matchday` as n
        inner join `{GCP_PROJECT}.{MARTS_DATASET}.mart_competition_fixtures` as c
            on n.fixture_sk = c.fixture_sk
    """)
    fixtures.sort(key=lambda r: r.get("kickoff_datetime") or datetime.max)

    teams = {
        int(r["team_sk"]): r
        for r in _query(client, f"select team_sk, team_name, team_slug, team_logo_url "
                                f"from `{GCP_PROJECT}.core.dim_team`")
    }
    upcoming = group_upcoming_fixtures(fixtures, teams, meta)

    # Top players (#40). One player per league across the `elite` group, current season only.
    # ⚠ Every part of the selection AND the order is a SERVED column: `competition_group` from the
    # registry seed, `is_current_season` and `league_leader_order` from the mart. The WHERE filters
    # facts and the ORDER BY reads them back in the ruled order; neither computes anything. Picking
    # the season in Python is what #846 moved out of this file, and picking the league's
    # representative is what the ranking ruling moved out of it.
    # ⚠ `league_leader_order = 1`, NOT `rank = 1`. `rank` is a DENSE_RANK, so joint leaders share it
    # and a league returns several rows — measured, 12 of the 28 league-boards this renders are tied.
    # ⚠ THE ORDER BY IS ONE SERVED COLUMN AND NOTHING ELSE. `board_leader_order` is the position of
    # a league's leader among ALL league leaders on that board, computed in `mart_leaderboards` from
    # the ruled keys. This file compares nothing — "the page renders the order it is served".
    # ⚠ An earlier version restated the three ruled keys here instead, and it was FAILed: it was the
    # same ranking rule, relocated from Python into SQL that still lives in the frontend. The claim
    # that it HAD to live here — because the row order is scoped to a POOL of leagues and the mart
    # knows nothing about pools — was simply wrong. The ruled order is TOTAL, and a total order
    # restricted to a subset keeps its sequence, so ranking every leader globally lets this pool
    # filter inherit the right order for free.
    # ⚠ No `metric_key` leg is needed: the rows arrive interleaved across boards and the shaper
    # buckets them, so each board still receives its own rows in the served order.
    # ⚠ `competition_group = 'elite'` is a LITERAL, and deliberately temporary: #101 decided the
    # group is chosen per nightly build by weighted random over the in-season groups, and wiring
    # that is its own MR. Until then the block renders the group named as the default.
    top_player_rows = _query(client, f"""
        select l.metric_key, l.league_code, l.sort_value,
               l.player_sk, l.player_name,
               l.team_name, l.team_slug, l.team_logo_url
        from `{GCP_PROJECT}.{MARTS_DATASET}.mart_leaderboards` as l
        join `{GCP_PROJECT}.{SEEDS_DATASET}.competition_registry` as r
            on l.league_code = r.league_code
        where l.is_current_season
          and l.league_leader_order = 1
          and r.competition_group = 'elite'
          and l.metric_key in ({", ".join(f"'{k}'" for k in _HOME_PLAYER_BOARDS)})
        order by l.board_leader_order
    """)

    # Top teams (#41). The same selection as the players block above, against the team mart, and
    # every clause is the same KIND of served column — see that comment, which is not repeated here.
    # ⚠ The tie inside `league_leader_order` is broken by `team_sk` and MEANS NOTHING: teams have no
    # minutes, and for a per-match RATE fewer games is less evidence rather than better performance,
    # so there is no criterion by ruling (GitLab #114 to improve).
    top_team_rows = _query(client, f"""
        select t.metric_key, t.league_code, t.sort_value,
               t.team_sk, t.team_name, t.team_slug, t.team_logo_url
        from `{GCP_PROJECT}.{MARTS_DATASET}.mart_team_leaderboards` as t
        join `{GCP_PROJECT}.{SEEDS_DATASET}.competition_registry` as r
            on t.league_code = r.league_code
        where t.is_current_season
          and t.league_leader_order = 1
          and r.competition_group = 'elite'
          and t.metric_key in ({", ".join(f"'{k}'" for k in _HOME_TEAM_BOARDS)})
        order by t.board_leader_order
    """)

    return shape_landing_payload(
        upcoming,
        shape_home_top_players(top_player_rows, meta, _board_catalogue()),
        shape_home_top_teams(
            top_team_rows, meta, _board_catalogue(_HOME_TEAM_BOARDS, "team")
        ),
    )


def shape_matchstats(fixture_id: int, team_rows: list[dict], player_rows: list[dict]) -> dict:
    """One played fixture's full stat lines (the form-window click-through):
    both teams' team-stat rows + every player's row."""
    return {
        "type": "matchstats",
        "fixture_id": fixture_id,
        "team_stats": [_drop(r, {"fixture_sk"}) for r in team_rows],
        "player_stats": [_drop(r, {"fixture_sk"}) for r in player_rows],
    }


def fetch_matchstats_payloads(client, sample: int = 0) -> list[dict]:
    marts = f"{GCP_PROJECT}.{MARTS_DATASET}"
    fids = sorted({
        int(r["played_fixture_sk"])
        for r in _query(client, f"select distinct played_fixture_sk "
                                f"from `{marts}.mart_team_momentum_window` "
                                f"where played_fixture_sk is not null")
    })
    if sample:
        fids = fids[:sample]
    if not fids:
        return []
    fid_in = ", ".join(str(i) for i in fids)
    team = _group_by(
        _query(client, f"select * from `{marts}.mart_team_fixture_stats` where fixture_sk in ({fid_in})"),
        "fixture_sk",
    )
    player = _group_by(
        _query(client, f"select * from `{marts}.mart_player_fixture_stats` where fixture_sk in ({fid_in})"),
        "fixture_sk",
    )
    out = []
    for fid in fids:
        ts, ps = team.get(fid, []), player.get(fid, [])
        if ts or ps:
            out.append(shape_matchstats(fid, ts, ps))
    return out


def fetch_glossary(seed_path: str = CATALOGUE_SEED_PATH) -> dict:
    """metrics.json — the metric catalogue (definitions + i18n keys + format).
    No BigQuery; the seed is the single source of metric definitions (#327)."""
    import csv

    with open(seed_path, encoding="utf-8") as f:
        return {"type": "glossary", "metrics": list(csv.DictReader(f))}


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def write_file(out_root: pathlib.Path, relpath: str, payload: dict) -> str:
    path = out_root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _payload_bytes(payload)
    path.write_bytes(data)
    return _sha256(data)


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
    source_counts: dict[str, int] = {}

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
    if "fixtures" in entities:
        for p in fetch_fixture_payloads(client, sample, source_counts):
            e = write_entity(out_root, "fixtures", p["fixture_id"], p)
            entries.append(e)
            slug_map[p["slug"]] = {"type": "fixture", "id": p["fixture_id"]}
    if "competitions" in entities:
        for p in fetch_competition_payloads(client, sample):
            relpath = f"competitions/{p['league_code']}/{p['season']}.json"
            sha = write_file(out_root, relpath, p)
            entries.append({"type": "competition",
                            "id": f"{p['league_code']}-{p['season']}",
                            "slug": p.get("slug"), "path": relpath, "sha256": sha})
            if p.get("slug"):
                slug_map[f"{p['slug']}-{p['season']}"] = {
                    "type": "competition", "league_code": p["league_code"], "season": p["season"]}
    if "nav" in entities:
        nav = fetch_nav()
        sha = write_file(out_root, "nav.json", nav)
        entries.append({"type": "nav", "id": "nav", "slug": None,
                        "path": "nav.json", "sha256": sha})
    if "leaderboards" in entities:
        for p in fetch_leaderboard_payloads(client, sample):
            relpath = f"leaderboards/{p['league_code']}/{p['season']}.json"
            sha = write_file(out_root, relpath, p)
            entries.append({"type": "leaderboards",
                            "id": f"{p['league_code']}-{p['season']}",
                            "slug": p.get("slug"), "path": relpath, "sha256": sha})
    if "matchstats" in entities:
        for p in fetch_matchstats_payloads(client, sample):
            relpath = f"matchstats/{p['fixture_id']}.json"
            sha = write_file(out_root, relpath, p)
            entries.append({"type": "matchstats", "id": p["fixture_id"],
                            "slug": None, "path": relpath, "sha256": sha})
    if "glossary" in entities:
        sha = write_file(out_root, "metrics.json", fetch_glossary())
        entries.append({"type": "glossary", "id": "metrics", "slug": None,
                        "path": "metrics.json", "sha256": sha})
    if "landing" in entities:
        sha = write_file(out_root, "landing.json", fetch_landing_payload(client))
        entries.append({"type": "landing", "id": "landing", "slug": None,
                        "path": "landing.json", "sha256": sha})
    if "competition_index" in entities:
        sha = write_file(out_root, "competition_index.json", fetch_competition_index(client))
        entries.append({"type": "competition_index", "id": "competition_index", "slug": None,
                        "path": "competition_index.json", "sha256": sha})

    # Full league_code -> {name, slug} map (registry-only) — the frontend's competition lookup for
    # every active league. Always emitted (site_v2/src/data/competitions.json consumes it, even on a
    # teams-only run: the team page reads the competition display name from it).
    sha = write_file(out_root, "competitions.json", _competitions_index(client))
    entries.append({"type": "competitions_index", "id": "competitions", "slug": None,
                    "path": "competitions.json", "sha256": sha})

    (out_root / "slug_map.json").write_text(
        json.dumps(slug_map, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    manifest = build_manifest(entries, source_counts)
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
