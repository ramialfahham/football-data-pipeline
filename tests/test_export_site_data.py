"""Unit tests for the per-entity site export pure helpers (#365).

No BigQuery — exercises slugify, payload shaping and manifest building with
fabricated rows so python-ci validates the logic offline.
"""

from scripts.export_site_data import (
    _display_group_of_type,
    _fixture_side,
    _shape_benchmark_member,
    _shape_benchmarks,
    _shape_career_row,
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
         "team_name": "Bayern", "team_country": "Germany", "team_logo_url": "u", "points": 78,
         "team_founded_year": 1900, "venue_name": "Old", "venue_city": "München", "venue_capacity": 70000},
        {"team_sk": 157, "season_api_year": 2025, "league_code": "BL1",
         "team_name": "Bayern München", "team_country": "Germany", "team_logo_url": "u2", "points": 82,
         "team_founded_year": 1900, "venue_name": "Allianz Arena", "venue_city": "München", "venue_capacity": 75000},
    ]
    p = shape_team_payload(rows)
    assert p["team_id"] == 157
    assert p["slug"] == "bayern-munchen-157"          # from the 2025 (latest) row
    assert p["name"] == "Bayern München"
    # GAP-01: founded year + venue from the latest row; venue is a nested block
    assert p["founded_year"] == 1900
    assert p["venue"] == {"name": "Allianz Arena", "city": "München", "capacity": 75000}
    assert [s["season_api_year"] for s in p["seasons"]] == [2025, 2024]  # desc
    # identity columns (incl. founded/venue) are stripped from per-season rows
    assert "team_name" not in p["seasons"][0]
    assert "team_founded_year" not in p["seasons"][0] and "venue_name" not in p["seasons"][0]
    assert p["seasons"][0]["points"] == 82


def test_shape_team_payload_venue_absent_is_none():
    # a team with no venue/founded data -> honest absence (venue None, founded_year None)
    p = shape_team_payload([{"team_sk": 9, "season_api_year": 2025,
                             "league_code": "BL1", "team_name": "X"}])
    assert p["venue"] is None
    assert p["founded_year"] is None


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


def test_shape_team_payload_attaches_squad_per_season_omits_null_name():
    rows = [
        {"team_sk": 157, "season_api_year": 2024, "league_code": "BL1",
         "team_name": "Bayern", "team_country": "Germany", "team_logo_url": "u"},
        {"team_sk": 157, "season_api_year": 2025, "league_code": "BL1",
         "team_name": "Bayern München", "team_country": "Germany", "team_logo_url": "u2"},
    ]

    def member(player_sk, name, *, position="Midfielder"):
        return {
            "player_team_season_sk": player_sk * 10, "team_sk": 157, "player_sk": player_sk,
            "season_sk": 1, "league_code": "BL1", "season_api_year": 2025,
            "competition_type": "domestic_league", "entity_type": "club",
            "player_name": name, "player_position": position,
            "player_nationality": "Germany", "player_birth_date": "1996-02-08",
            "player_photo_url": "p",
        }

    # deliberately out of player_sk order; one unresolved-player row (null name) to be omitted
    roster = [
        member(30, "Kimmich"),
        member(9, "Kane", position="Attacker"),
        member(1, "Neuer", position="Goalkeeper"),
        member(99, None),
    ]
    p = shape_team_payload(rows, None, roster)
    s2025 = p["seasons"][0]
    assert s2025["season_api_year"] == 2025
    # sorted by player_sk (byte-stable), the null-name member omitted
    assert [m["player_id"] for m in s2025["squad"]] == [1, 9, 30]
    assert [m["name"] for m in s2025["squad"]] == ["Neuer", "Kane", "Kimmich"]
    # each member carries only the six identity-only display keys
    assert set(s2025["squad"][0]) == {
        "player_id", "name", "position", "nationality", "birth_date", "photo"}
    for internal in ("team_sk", "league_code", "season_api_year", "player_team_season_sk",
                     "season_sk", "competition_type", "entity_type", "player_sk"):
        assert all(internal not in m for m in s2025["squad"])
    # a season with no roster rows renders the empty squad
    assert p["seasons"][1]["squad"] == []


def test_shape_team_payload_squad_defaults_empty_without_roster():
    rows = [{"team_sk": 9, "season_api_year": 2025, "league_code": "PL",
             "team_name": "Arsenal", "team_country": "England", "team_logo_url": "u"}]
    p = shape_team_payload(rows)
    assert p["seasons"][0]["squad"] == []


def test_shape_player_payload_orders_match_log_desc():
    profiles = [
        {"player_sk": 1090, "season_api_year": 2025, "league_code": "BL1",
         "player_name": "Jamal Musiala", "player_photo_url": "ph",
         "player_nationality": "Germany", "player_birth_date": "2003-02-26",
         "position_code": "M", "goals": 12},
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
    assert p["birth_date"] == "2003-02-26"
    assert [m["opponent_name"] for m in p["match_log"]] == ["B", "A"]  # latest first


def test_shape_player_payload_current_team_and_per_season_team():
    # GAP-16: dbt (int_player_season__team) flags the current club via is_current_team; the export
    # SELECTS current_team by that flag and never re-ranks. Here 2024 is flagged (not the latest
    # 2025 season) on purpose — to prove the export reads the flag, not its own "latest season".
    profiles = [
        {"player_sk": 7, "season_api_year": 2025, "league_code": "PD", "player_name": "Player X",
         "team_sk": 541, "is_current_team": False,
         "team_name": "Real Madrid", "team_logo_url": "rm.png", "team_country": "Spain"},
        {"player_sk": 7, "season_api_year": 2024, "league_code": "BL1", "player_name": "Player X",
         "team_sk": 157, "is_current_team": True,
         "team_name": "Bayern", "team_logo_url": "fcb.png", "team_country": "Germany"},
        {"player_sk": 7, "season_api_year": 2023, "league_code": "BL1", "player_name": "Player X",
         "team_sk": None, "is_current_team": False},   # no finished leg -> honest absence
    ]
    p = shape_player_payload(profiles, [])
    assert p["current_team"] == {"team_id": 157, "name": "Bayern",
                                 "crest": "fcb.png", "country": "Germany"}
    teams = [s["team"] for s in p["seasons"]]   # seasons are year-desc: 2025, 2024, 2023
    assert teams[0]["team_id"] == 541           # 2025 PD
    assert teams[1]["team_id"] == 157           # 2024 BL1
    assert teams[2] is None                     # 2023: no team
    # internal keys never leak into the published season rows
    assert all("team_sk" not in s and "is_current_team" not in s for s in p["seasons"])


def test_shape_benchmark_member_carries_mart_columns_and_ratio_atoms():
    # GAP-21: a RATIO metric row keeps numerator/denominator (for the {num} of {den} · {pct}% triple);
    # a per-90 row has null num/den. The export copies straight from the mart — no computation.
    ratio = {
        "metric_key": "duels_won_pct", "metric_value": 0.54, "percentile": 0.70,
        "rank": 12, "peer_count": 41, "peer_median": 0.5, "vs_median_delta": 0.04,
        "position_group": "ATT", "minutes": 2470, "appearances": 29,
        "metric_numerator": 96, "metric_denominator": 178,
    }
    m = _shape_benchmark_member(ratio)
    assert m == {
        "metric_key": "duels_won_pct", "metric_value": 0.54, "percentile": 0.70,
        "rank": 12, "peer_count": 41, "peer_median": 0.5, "vs_median_delta": 0.04,
        "numerator": 96, "denominator": 178,
    }
    per90 = {**ratio, "metric_key": "goals_per90", "metric_value": 0.82,
             "metric_numerator": None, "metric_denominator": None}
    m90 = _shape_benchmark_member(per90)
    assert m90["numerator"] is None and m90["denominator"] is None
    # grain/internal keys never leak into the member
    for internal in ("position_group", "minutes", "appearances",
                     "metric_numerator", "metric_denominator"):
        assert internal not in m


def test_shape_benchmarks_groups_by_position_and_orders_by_metric_key():
    def row(pos, key, **kw):
        base = {"position_group": pos, "metric_key": key, "metric_value": 1.0,
                "percentile": 0.5, "rank": 1, "peer_count": 10, "peer_median": 1.0,
                "vs_median_delta": 0.0, "minutes": 2000, "appearances": 24,
                "metric_numerator": None, "metric_denominator": None}
        base.update(kw)
        return base
    # one player benchmarked in two positions; metrics deliberately out of key order
    rows = [
        row("MID", "passes_per90"),
        row("ATT", "goals_per90"),
        row("ATT", "assists_per90"),
        row("MID", "duels_won_pct", metric_numerator=50, metric_denominator=90),
    ]
    groups = _shape_benchmarks(rows)
    # position groups sorted (ATT before MID)
    assert [g["position_group"] for g in groups] == ["ATT", "MID"]
    # minutes/appearances carried at the group level (the position's sample)
    assert groups[0]["minutes"] == 2000 and groups[0]["appearances"] == 24
    # metrics ordered byte-stable by metric_key
    assert [m["metric_key"] for m in groups[0]["metrics"]] == ["assists_per90", "goals_per90"]
    assert [m["metric_key"] for m in groups[1]["metrics"]] == ["duels_won_pct", "passes_per90"]
    # the ratio metric's atoms survive
    duels = groups[1]["metrics"][0]
    assert duels["numerator"] == 50 and duels["denominator"] == 90


def test_shape_player_payload_attaches_benchmarks_per_season():
    profiles = [
        {"player_sk": 7, "season_api_year": 2025, "league_code": "PD",
         "player_name": "X", "position_code": "F"},
        {"player_sk": 7, "season_api_year": 2024, "league_code": "BL1",
         "player_name": "X", "position_code": "F"},
    ]
    benchmarks = [
        {"player_sk": 7, "league_code": "PD", "season_api_year": 2025, "position_group": "ATT",
         "metric_key": "goals_per90", "metric_value": 0.9, "percentile": 0.99, "rank": 1,
         "peer_count": 40, "peer_median": 0.3, "vs_median_delta": 0.6,
         "minutes": 2500, "appearances": 30, "metric_numerator": None, "metric_denominator": None},
    ]
    p = shape_player_payload(profiles, [], benchmarks)
    s2025, s2024 = p["seasons"][0], p["seasons"][1]
    assert s2025["benchmarks"][0]["position_group"] == "ATT"
    assert s2025["benchmarks"][0]["metrics"][0]["metric_key"] == "goals_per90"
    # a season with no benchmark rows renders an empty list (honest absence)
    assert s2024["benchmarks"] == []
    # default (no benchmark_rows) also yields empty benchmarks
    p2 = shape_player_payload(profiles, [])
    assert all(s["benchmarks"] == [] for s in p2["seasons"])


def test_shape_career_row_carries_mart_columns():
    # GAP-22: one mart_player_career row -> a career entry. Counts + club identity copied straight from the
    # mart (no computation); the club identity reuses _player_team_block; internal + player-identity keys drop.
    row = {
        "player_sk": 7, "team_sk": 157, "season_sk": 900, "league_sk": 78,
        "player_career_sk": "hash", "season_api_year": 2024, "league_code": "BL1",
        "player_name": "Harry Kane", "entity_type": "club",
        "team_name": "Bayern", "team_logo_url": "fcb.png", "team_country": "Germany",
        "appearances": 32, "goals": 26, "assists": 8, "national_appearances_total": 12,
        "last_kickoff_at": "2024-05-18T15:30:00", "club_latest_kickoff_at": "2024-05-18T15:30:00",
    }
    assert _shape_career_row(row) == {
        "season": 2024, "competition": "BL1", "entity_type": "club",
        "team": {"team_id": 157, "name": "Bayern", "crest": "fcb.png", "country": "Germany"},
        "appearances": 32, "goals": 26, "assists": 8,
    }
    m = _shape_career_row(row)
    for internal in ("player_sk", "team_sk", "season_sk", "league_sk", "player_career_sk",
                     "player_name", "national_appearances_total", "last_kickoff_at",
                     "club_latest_kickoff_at"):
        assert internal not in m


def test_shape_player_payload_attaches_career_and_national_total_omits_null_team():
    # GAP-22: the career log is TOP-LEVEL (whole career, not per-season). Order is a pure sort by the mart's
    # club_latest_kickoff_at (club-block order + contiguity) then last_kickoff_at (within-club season order) —
    # no client-side aggregation. A RETURN SPELL (Spurs -> Bayern -> back to Spurs) proves contiguity: both
    # Spurs rows group together even though Bayern's season falls between them chronologically. National-entity
    # rows (with a resolved team) are ordered the same way (own team block); an unresolved-identity row (null
    # team_name = broken FK) is omitted; national_appearances_total is the precomputed per-player total.
    def row(team_sk, year, comp, name, entity, apps, last, club_latest):
        return {"player_sk": 9, "team_sk": team_sk, "season_api_year": year, "league_code": comp,
                "entity_type": entity, "team_name": name, "team_logo_url": "x.png",
                "team_country": "X", "appearances": apps, "goals": 1, "assists": 1,
                "national_appearances_total": 23,
                "last_kickoff_at": last, "club_latest_kickoff_at": club_latest}
    profiles = [
        {"player_sk": 9, "season_api_year": 2024, "league_code": "PL", "player_name": "Kane",
         "position_code": "F"},
    ]
    career = [
        row(47, 2020, "PL", "Spurs", "club", 35, "2020-07-15T19:00:00", "2024-05-19T15:00:00"),
        row(157, 2022, "BL1", "Bayern", "club", 32, "2022-05-14T15:30:00", "2022-05-14T15:30:00"),
        row(47, 2024, "PL", "Spurs", "club", 30, "2024-05-19T15:00:00", "2024-05-19T15:00:00"),
        # two national-team seasons (a real multi-national player) — resolved team, ordered like a club block
        row(500, 2021, "WC", "England", "national", 8, "2021-07-11T20:00:00", "2023-07-09T20:00:00"),
        row(500, 2023, "WC", "England", "national", 10, "2023-07-09T20:00:00", "2023-07-09T20:00:00"),
        # unresolved identity (null team_name = broken FK) -> omitted from career[]
        {"player_sk": 9, "team_sk": 999, "season_api_year": 2019, "league_code": "WC",
         "entity_type": "national", "team_name": None, "appearances": 5, "goals": 0, "assists": 0,
         "national_appearances_total": 23, "last_kickoff_at": "2019-06-01T20:00:00",
         "club_latest_kickoff_at": "2019-06-01T20:00:00"},
    ]
    p = shape_player_payload(profiles, [], None, career)
    # club_latest desc: Spurs 2024-05-19, England 2023-07-09, Bayern 2022-05-14. Spurs rows contiguous
    # (2024, 2020), then England (2023, 2021), then Bayern; the null-team row is omitted.
    assert [(c["team"]["team_id"], c["season"]) for c in p["career"]] == [
        (47, 2024), (47, 2020), (500, 2023), (500, 2021), (157, 2022)
    ]
    assert len(p["career"]) == 5
    assert p["national_appearances_total"] == 23
    # empty default (no career_rows) -> empty career + None total
    p2 = shape_player_payload(profiles, [])
    assert p2["career"] == [] and p2["national_appearances_total"] is None


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
