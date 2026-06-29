"""Unit tests for the per-entity site export pure helpers (#365).

No BigQuery — exercises slugify, payload shaping and manifest building with
fabricated rows so python-ci validates the logic offline.
"""

from scripts.export_site_data import (
    _display_group_of_type,
    _fixture_side,
    build_manifest,
    build_nav,
    fetch_glossary,
    fixture_slug,
    shape_competition_payload,
    shape_fixture_payload,
    shape_leaderboards,
    shape_matchstats,
    shape_player_payload,
    shape_team_payload,
    shape_top_players,
    slugify,
)


def test_shape_leaderboards_groups_by_metric_key_and_orders_by_rank():
    # mart_leaderboards is LONG: one row per (player, board) with metric_key + rank already
    # set by the warehouse. The export groups by metric_key and orders by rank — no Python ranking.
    rows = [
        {"metric_key": "goals", "rank": 2, "player_sk": 3, "player_name": "C"},
        {"metric_key": "goals", "rank": 1, "player_sk": 2, "player_name": "B"},
        {"metric_key": "scorer_points", "rank": 1, "player_sk": 1, "player_name": "A"},
        {"metric_key": "goals", "rank": 99, "player_sk": 4, "player_name": "D"},   # beyond the limit
    ]
    boards = shape_leaderboards(rows, metrics=("goals", "scorer_points"), limit=10)
    assert [p["player_name"] for p in boards["goals"]] == ["B", "C"]   # by rank; D dropped (> limit)
    assert [p["player_name"] for p in boards["scorer_points"]] == ["A"]
    assert len(boards["goals"]) == 2


def test_display_group_of_type_reads_seed():
    m = _display_group_of_type()                       # reads the real seed (offline, no BQ)
    assert m["domestic_league"] == "leagues"
    assert m["world_championship"] == "national-teams"
    assert m["club_friendly_domestic"] is None         # empty cell -> None (not in nav)


def test_shape_matchstats_drops_fixture_sk():
    p = shape_matchstats(
        99,
        [{"fixture_sk": 99, "team_sk": 1, "shots_total": 10}],
        [{"fixture_sk": 99, "player_sk": 7, "goals_total": 1}],
    )
    assert p["type"] == "matchstats" and p["fixture_id"] == 99
    assert "fixture_sk" not in p["team_stats"][0]
    assert p["team_stats"][0]["shots_total"] == 10
    assert p["player_stats"][0]["goals_total"] == 1


def test_fetch_glossary_reads_catalogue_seed():
    g = fetch_glossary()                       # reads the real seed (offline, no BQ)
    assert g["type"] == "glossary"
    assert len(g["metrics"]) > 10
    assert all("metric_id" in m for m in g["metrics"])


def test_build_nav_groups_and_country_hubs():
    # build_nav reads display_group off each competition (resolved from the
    # competition_types seed upstream), not a hardcoded type->group dict.
    comps = [
        {"league_code": "BL1", "name": "Bundesliga", "slug": "bundesliga",
         "country": "Germany", "competition_type": "domestic_league",
         "display_group": "leagues", "tier": 1, "sort_order": 30},
        {"league_code": "BL2", "name": "2. Bundesliga", "slug": "2-bundesliga",
         "country": "Germany", "competition_type": "domestic_league",
         "display_group": "leagues", "tier": 2, "sort_order": 60},
        {"league_code": "DFBP", "name": "DFB-Pokal", "slug": "dfb-pokal",
         "country": "Germany", "competition_type": "domestic_cup",
         "display_group": "cups", "sort_order": 30},
        {"league_code": "UCL", "name": "Champions League", "slug": "champions-league",
         "country": "Europe", "competition_type": "continental_club",
         "display_group": "continental-club", "sort_order": 10},
    ]
    nav = build_nav(comps)
    groups = {g["key"]: [c["league_code"] for c in g["competitions"]] for g in nav["groups"]}
    assert groups["leagues"] == ["BL1", "BL2"]          # by sort_order
    assert groups["cups"] == ["DFBP"]
    assert groups["continental-club"] == ["UCL"]
    # country hub = domestic comps only, tier-ordered; UCL (Europe/continental) excluded
    germany = next(c for c in nav["countries"] if c["country"] == "Germany")
    assert [c["league_code"] for c in germany["competitions"]] == ["BL1", "BL2", "DFBP"]
    assert all(c["country"] != "Europe" for c in nav["countries"])


def test_shape_top_players_selects_by_rank_and_joins_names():
    # selection only: ordered by the warehouse top_player_rank, join keys + the rank
    # itself dropped from the payload.
    rows = [
        {"player_sk": 1, "upcoming_fixture_sk": 9, "team_sk": 5, "top_player_rank": 2},
        {"player_sk": 2, "upcoming_fixture_sk": 9, "team_sk": 5, "top_player_rank": 1},
        {"player_sk": 3, "upcoming_fixture_sk": 9, "team_sk": 5, "top_player_rank": None},
    ]
    names = {1: {"player_name": "A", "player_photo_url": "a"},
             2: {"player_name": "B", "player_photo_url": "b"},
             3: {"player_name": "C", "player_photo_url": "c"}}
    top = shape_top_players(rows, names, limit=5)
    assert [p["player_name"] for p in top] == ["B", "A"]   # by rank asc; null-rank C excluded
    assert "upcoming_fixture_sk" not in top[0]              # join keys dropped
    assert "top_player_rank" not in top[0]                 # selection key dropped


def test_shape_competition_payload_sorts_sections():
    p = shape_competition_payload(
        "BL1", 2025, {"name": "Bundesliga", "slug": "bundesliga"},
        standings=[{"group_name": "", "standing_rank": 2}, {"group_name": "", "standing_rank": 1}],
        top_scorers=[{"rank": 2}, {"rank": 1}],
        fixtures=[{"kickoff_datetime": "2025-09-02"}, {"kickoff_datetime": "2025-09-01"}],
    )
    assert p["type"] == "competition" and p["slug"] == "bundesliga"
    assert [s["standing_rank"] for s in p["standings"]] == [1, 2]
    assert [s["rank"] for s in p["top_scorers"]] == [1, 2]
    assert [f["kickoff_datetime"] for f in p["fixtures"]] == ["2025-09-01", "2025-09-02"]


def test_fixture_slug_date_home_vs_away():
    assert fixture_slug("2026-06-11T19:00:00", "Mexico", "South Africa", 7) \
        == "2026-06-11-mexico-vs-south-africa"


def test_fixture_slug_falls_back_to_id():
    assert fixture_slug(None, "Mexico", "South Africa", 7) == "fixture-7"


def test_fixture_side_drops_join_keys_and_handles_missing():
    w1 = {"upcoming_fixture_sk": 9, "team_sk": 1, "is_home": True, "goals_per_match": 1.4}
    side = _fixture_side(1, {"team_name": "A", "team_logo_url": "u", "team_country": "X"},
                         w1, None, None)
    assert side["team_id"] == 1 and side["name"] == "A" and side["crest"] == "u"
    assert side["w1"] == {"goals_per_match": 1.4}      # join keys dropped
    assert side["w2"] is None and side["standing"] is None  # honest absence


def test_shape_fixture_payload_composes_header_and_sides():
    fix = {"fixture_sk": 7, "kickoff_datetime": "2026-06-11T19:00:00",
           "status_short": "NS", "league_code": "WC", "league_name": "World Cup",
           "season_api_year": 2026, "round_name": "Group Stage - 1",
           "venue_name_snapshot": "Estadio", "home_team_name": "Mexico",
           "away_team_name": "South Africa"}
    home = _fixture_side(1, {"team_name": "Mexico"}, None, None, None)
    away = _fixture_side(2, {"team_name": "South Africa"}, None, None, None)
    p = shape_fixture_payload(fix, home, away, {"total_meetings": 3, "wins": 2})
    assert p["type"] == "fixture" and p["fixture_id"] == 7
    assert p["slug"] == "2026-06-11-mexico-vs-south-africa"
    assert p["league_name"] == "World Cup" and p["round"] == "Group Stage - 1"
    assert p["home"]["team_id"] == 1 and p["away"]["team_id"] == 2
    assert p["head_to_head"] == {"total_meetings": 3, "wins": 2}


def test_slugify_folds_accents_and_appends_id():
    assert slugify("Bayern München", 157) == "bayern-munchen-157"


def test_slugify_collapses_punctuation_and_spaces():
    assert slugify("Brighton & Hove Albion", 51) == "brighton-hove-albion-51"


def test_slugify_falls_back_to_id_when_name_empty():
    assert slugify("", 99) == "99"
    assert slugify(None, 99) == "99"


def test_shape_team_payload_identity_from_latest_and_seasons_desc():
    rows = [
        {"team_sk": 157, "season_api_year": 2024, "league_code": "BL1",
         "team_name": "Bayern", "team_country": "Germany",
         "team_logo_url": "u", "points": 78},
        {"team_sk": 157, "season_api_year": 2025, "league_code": "BL1",
         "team_name": "Bayern München", "team_country": "Germany",
         "team_logo_url": "u2", "points": 82},
    ]
    p = shape_team_payload(rows)
    assert p["team_id"] == 157
    assert p["slug"] == "bayern-munchen-157"          # from the 2025 (latest) row
    assert p["name"] == "Bayern München"
    assert [s["season_api_year"] for s in p["seasons"]] == [2025, 2024]  # desc
    # identity columns are stripped from per-season rows
    assert "team_name" not in p["seasons"][0]
    assert p["seasons"][0]["points"] == 82


def test_shape_team_payload_attaches_fixtures_per_season_newest_first():
    rows = [
        {"team_sk": 157, "season_api_year": 2024, "league_code": "BL1",
         "team_name": "Bayern", "team_country": "Germany", "team_logo_url": "u"},
        {"team_sk": 157, "season_api_year": 2025, "league_code": "BL1",
         "team_name": "Bayern München", "team_country": "Germany", "team_logo_url": "u2"},
    ]

    def fx(opponent, *, upcoming=None, recency=None, is_home=True):
        return {
            "team_sk": 157, "league_code": "BL1", "season_api_year": 2025,
            "fixture_sk": 0, "opponent_team_sk": 5, "opponent_name": opponent,
            "opponent_logo_url": "x", "is_home": is_home, "kickoff_datetime": "2025-10-01",
            "round_name": "MD1", "goals_for": 1, "goals_against": 0, "result": "W",
            "status_short": "FT", "has_result": recency is not None,
            "is_upcoming": upcoming is not None, "upcoming_rank": upcoming,
            "recency_rank": recency,
        }

    fixtures = [
        fx("Dortmund", upcoming=1),
        fx("Leipzig", recency=1), fx("Mainz", recency=2), fx("Koln", recency=3),
        fx("Bremen", recency=4), fx("Wolfsburg", recency=5), fx("Freiburg", recency=6),
    ]
    p = shape_team_payload(rows, fixtures)
    s2025 = p["seasons"][0]
    assert s2025["season_api_year"] == 2025
    assert s2025["next_fixture"]["opponent_name"] == "Dortmund"
    # recent results newest-first (recency_rank asc), capped at 5 — the rank-6 row is excluded
    assert [f["opponent_name"] for f in s2025["recent_results"]] == [
        "Leipzig", "Mainz", "Koln", "Bremen", "Wolfsburg"]
    # every internal key is stripped from each shaped fixture row (next + recent)
    for internal in ("team_sk", "fixture_sk", "opponent_team_sk", "league_code",
                     "season_api_year", "upcoming_rank", "recency_rank",
                     "has_result", "is_upcoming"):
        assert internal not in s2025["next_fixture"]
        assert all(internal not in r for r in s2025["recent_results"])
    # a season with no fixture rows renders the empty state
    s2024 = p["seasons"][1]
    assert s2024["next_fixture"] is None
    assert s2024["recent_results"] == []


def test_shape_player_payload_orders_match_log_desc():
    profiles = [
        {"player_sk": 1090, "season_api_year": 2025, "league_code": "BL1",
         "player_name": "Jamal Musiala", "player_photo_url": "ph",
         "player_nationality": "Germany", "position_code": "M", "goals": 12},
    ]
    matches = [
        {"player_sk": 1090, "kickoff_datetime": "2025-09-01T18:30:00",
         "opponent_name": "A", "goals_total": 1},
        {"player_sk": 1090, "kickoff_datetime": "2025-10-01T18:30:00",
         "opponent_name": "B", "goals_total": 0},
    ]
    p = shape_player_payload(profiles, matches)
    assert p["player_id"] == 1090
    assert p["slug"] == "jamal-musiala-1090"
    assert p["position"] == "M"
    assert [m["opponent_name"] for m in p["match_log"]] == ["B", "A"]  # latest first


def test_build_manifest_counts_by_type():
    entries = [
        {"type": "team", "id": 1, "slug": "a-1", "path": "teams/1.json", "sha256": "x"},
        {"type": "team", "id": 2, "slug": "b-2", "path": "teams/2.json", "sha256": "y"},
        {"type": "player", "id": 3, "slug": "c-3", "path": "players/3.json", "sha256": "z"},
    ]
    m = build_manifest(entries)
    assert m["counts"] == {"team": 2, "player": 1}
    assert len(m["entries"]) == 3
    assert "generated_at" in m
