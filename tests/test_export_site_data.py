"""Unit tests for the site export's pure helpers, on fabricated rows with no BigQuery."""

import json

import pytest

from scripts.export_site_data import (
    _competitions_index,
    _display_group_of_type,
    _fixture_side,
    form_block,
    _shape_team_benchmark_member,
    build_manifest,
    deserved_scatter_index,
    league_strip_index,
    build_nav,
    fetch_glossary,
    group_fixtures_by_round,
    shape_competition_boards,
    shape_competition_index,
    shape_competition_payload,
    shape_team_index,
    shape_player_index,
    shape_season_summary,
    shape_fixture_payload,
    shape_next_match,
    shape_leaderboards,
    shape_player_payload,
    shape_player_peers,
    shape_team_payload,
    shape_top_players,
    player_slug_with_id,
)
from scripts import export_site_data
from scripts.export_site_data import _featured_season_row, group_upcoming_fixtures


def _mark_featured(rows: list[dict]) -> list[dict]:
    """Flag the greatest season_api_year row as the marts would, so a fixture mirrors served data."""
    top = max(rows, key=lambda r: (r.get("season_api_year") or 0))
    for r in rows:
        r["is_featured_season"] = r is top
    return rows


def test_shape_leaderboards_groups_by_metric_key_and_orders_by_rank():
    # mart_leaderboards is long: the warehouse sets metric_key and rank, so the export never ranks.
    rows = [
        {"metric_key": "goals_player", "rank": 2, "player_sk": 3, "player_name": "C"},
        {"metric_key": "goals_player", "rank": 1, "player_sk": 2, "player_name": "B"},
        {"metric_key": "scorer_points_player", "rank": 1, "player_sk": 1, "player_name": "A"},
        {"metric_key": "goals_player", "rank": 99, "player_sk": 4, "player_name": "D"},   # beyond the limit
    ]
    boards = shape_leaderboards(rows, metrics=("goals_player", "scorer_points_player"), limit=10)
    assert [p["player_name"] for p in boards["goals_player"]] == ["B", "C"]   # by rank; D dropped (> limit)
    assert [p["player_name"] for p in boards["scorer_points_player"]] == ["A"]
    assert len(boards["goals_player"]) == 2


def test_display_group_of_type_reads_seed():
    m = _display_group_of_type()                       # reads the real seed (offline, no BQ)
    assert m["domestic_league"] == "leagues"
    assert m["world_championship"] == "national-teams"
    assert m["club_friendly_domestic"] is None         # empty cell -> None (not in nav)


def test_display_group_of_type_covers_the_renamed_and_new_types():
    """Only the seed lookup resolves a competition_type; `build_nav` groups by the resolved display_group."""
    m = _display_group_of_type()
    assert "continental_club" not in m, "the old type name is back in the seed"
    assert m["continental_cup"] == "continental-club"
    assert m["club_world_cup"] == "continental-club"
    assert m["intercontinental_super_cup"] == "continental-club"


def test_every_leaderboard_read_takes_the_season_rows_only():
    """Every `mart_leaderboards` query names one window: season boards, or match boards for the played match page."""
    import inspect
    import re

    source = inspect.getsource(export_site_data)
    reads = [m.start() for m in re.finditer(r"\.mart_leaderboards`", source)]
    assert len(reads) == 4, "the competition, leaderboard, landing and played match reads"
    windows = []
    for at in reads:
        nearby = source[at:at + 400]
        named = [w for w in ("season_to_date", "match") if f"window_type = '{w}'" in nearby]
        assert len(named) == 1, source[at - 200:at + 400]
        windows.append(named[0])
    assert sorted(windows) == ["match", "season_to_date", "season_to_date", "season_to_date"]
    played = inspect.getsource(export_site_data.fetch_played_fixture_payloads)
    assert "window_type = 'match'" in played and "season_to_date" not in played


def test_player_payloads_read_only_the_named_players_and_the_marked_matches(monkeypatch):
    """The export selects on the warehouse's flags; a squad is read whole and a peer file holds the competition's players."""
    seen = []

    def fake_query(client, sql):
        seen.append(sql)
        if "from `football-data-pipeline-gcp.marts.mart_player_profile`" in sql:
            return [{"player_sk": 7, "player_name": "P7", "has_club_tab": True, "current_club_team_sk": 5}]
        if "distinct player_sk, squad_sk" in sql:
            return [{"player_sk": 7, "squad_sk": "s1"}]
        if "squad_sk in ('s1')" in sql:
            return [{"player_sk": 7, "squad_sk": "s1", "team_sk": 5, "page_tab": "club",
                     "metric_key": "goals_per90", "metric_value": 0.5}]
        if "page_tab is not null" in sql:
            return [{"player_sk": 7, "page_tab": "club", "competition_order": 1, "league_code": "BL1",
                     "season_api_year": 2026, "position_group": "ATT", "metric_key": "goals_per90"}]
        if "concat(league_code" in sql:
            return [{"league_code": "BL1", "season_api_year": 2026, "position_group": "ATT",
                     "metric_key": "goals_per90", "metric_value": 0.5}]
        return []

    monkeypatch.setattr(export_site_data, "_query", fake_query)
    payloads, peers = export_site_data.fetch_player_payloads(object(), [7, 8], sample=1)

    assert [p["player_id"] for p in payloads] == [7]
    assert [p["position_group"] for p in peers] == ["ATT"]
    (profile_sql,) = [s for s in seen if "mart_player_profile" in s]
    assert "is_featured_season and player_sk in (7)" in profile_sql
    (log_sql,) = [s for s in seen if "mart_player_fixture_stats" in s]
    assert "is_in_page_window and player_sk in (7)" in log_sql
    assert "team_goals_for as goals_for" in log_sql and "team_goals_against as goals_against" in log_sql
    (peer_sql,) = [s for s in seen if "concat(league_code" in s]
    assert "cast(season_api_year as string)" in peer_sql
    assert "in ('BL1|2026|ATT')" in peer_sql
    (next_sql,) = [s for s in seen if "mart_team_fixtures" in s]
    assert "upcoming_rank = 1 and team_sk in (5)" in next_sql


def test_player_payloads_read_nothing_for_no_players(monkeypatch):
    monkeypatch.setattr(export_site_data, "_query", lambda *_: pytest.fail("no query expected"))
    assert export_site_data.fetch_player_payloads(object(), []) == ([], [])


def test_the_players_entity_refuses_a_run_with_no_player_pages(tmp_path, monkeypatch):
    monkeypatch.setattr(export_site_data, "_query", lambda *_: [])
    with pytest.raises(ValueError, match="no player has a page"):
        export_site_data.export_all(tmp_path, ("players",), 0, client=object())


def test_the_shared_name_flag_is_the_marts_and_is_selected():
    assert "shares_name_at_club" in export_site_data._PLAYER_PROFILE_COLUMNS
    assert not hasattr(export_site_data, "mark_shared_names")


def test_the_player_files_do_not_depend_on_the_order_the_warehouse_returns(tmp_path, monkeypatch):
    monkeypatch.setattr(export_site_data, "page_player_ids", lambda _c: [1, 5, 9])
    monkeypatch.setattr(export_site_data, "_competitions_index", lambda _c: {})
    peers = [{"league_code": c, "season": 2026, "position_group": "MID", "rows": []} for c in ("PL", "BL1")]
    written = []
    for order in ([9, 1, 5], [5, 9, 1]):
        out = tmp_path / str(order[0])
        monkeypatch.setattr(export_site_data, "fetch_player_payloads", lambda _c, _ids, _s, order=order: (
            [{"type": "player", "player_id": i, "slug": f"p-{i}"} for i in order], list(reversed(peers)) if order[0] == 5 else peers))
        export_site_data.export_all(out, ("players",), 0, client=object())
        written.append(((out / "player_pages.json").read_bytes(), (out / "slug_map.json").read_bytes(),
                        [e["path"] for e in json.loads((out / "manifest.json").read_text(encoding="utf-8"))["entries"]]))
    assert written[0] == written[1]
    assert list(json.loads(written[0][0])["pages"]) == ["1", "5", "9"]


def test_the_players_with_a_page_are_the_warehouses_flag(monkeypatch):
    seen = []
    monkeypatch.setattr(export_site_data, "_query",
                        lambda _c, sql: seen.append(sql) or [{"player_sk": 3}, {"player_sk": 1}])
    assert export_site_data.page_player_ids(object()) == [1, 3]
    assert "where has_player_page" in seen[0]


def test_a_sample_takes_the_board_players_first_and_lists_its_pages(tmp_path, monkeypatch):
    (tmp_path / "landing.json").write_text(json.dumps(
        {"top_players": [{"rows": [{"player_id": 9}]}]}), encoding="utf-8")
    monkeypatch.setattr(export_site_data, "page_player_ids", lambda _c: [1, 9])
    asked = []

    def payloads(_client, ids, sample):
        asked.extend(ids[:sample])
        return [{"type": "player", "player_id": i, "slug": f"p-{i}"} for i in ids[:sample]], []

    monkeypatch.setattr(export_site_data, "fetch_player_payloads", payloads)
    monkeypatch.setattr(export_site_data, "_competitions_index", lambda _c: {})
    export_site_data.export_all(tmp_path, ("players",), 1, client=object())
    assert asked == [9]
    pages = json.loads((tmp_path / "player_pages.json").read_text(encoding="utf-8"))
    assert pages["pages"] == {"9": "p-9"}


def test_fetch_glossary_reads_catalogue_seed():
    g = fetch_glossary()                       # reads the real seed (offline, no BQ)
    assert g["type"] == "glossary"
    assert len(g["metrics"]) > 10
    assert all("metric_id" in m for m in g["metrics"])


def test_build_nav_groups_and_country_hubs():
    # build_nav reads display_group off each competition, resolved upstream from the competition_types seed.
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
         "country": "Europe", "competition_type": "continental_cup",
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


def test_fetch_nav_takes_each_leagues_tier_from_the_competition_mart(monkeypatch):
    monkeypatch.setattr(export_site_data, "_warehouse_competitions", lambda client: [
        {"league_code": "BL1", "tier": 2}, {"league_code": "BL2", "tier": 1},
    ])
    nav = export_site_data.fetch_nav(object())
    germany = next(c for c in nav["countries"] if c["country"] == "Germany")
    order = [c["league_code"] for c in germany["competitions"]]
    assert order.index("BL2") < order.index("BL1"), "the mart's tier orders the hub, not the YAML"


def test_shape_top_players_selects_by_rank_and_joins_names():
    # Selection only: ordered by the warehouse's top_player_rank, with join keys and the rank dropped.
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


def test_shape_competition_payload_orders_every_block_by_served_columns():
    """The export orders by served columns and never ranks; the Matchdays tab opens on the fixtures' served flag."""
    p = shape_competition_payload(
        "BL1", 2026, {"name": "Bundesliga", "slug": "bundesliga"},
        standings=[{"group_name": "Bundesliga", "standing_rank": 2},
                   {"group_name": "Bundesliga", "standing_rank": 1}],
        deserved=[{"name": "Dortmund", "deserved_points": 6.3, "deserved_points_gap": 2.7, "deserved_rank": 2},
                  {"name": "Mainz", "deserved_points": 6.7, "deserved_points_gap": -2.7, "deserved_rank": 1},
                  {"name": "Köln", "deserved_points": 4.2, "deserved_points_gap": -0.2, "deserved_rank": 3}],
        summary=None,
    )
    assert p["type"] == "competition" and p["slug"] == "bundesliga"
    assert [s["standing_rank"] for s in p["standings"]] == [1, 2]
    assert [d["name"] for d in p["deserved"]] == ["Mainz", "Dortmund", "Köln"]
    assert "next_matchday" not in p
    assert p["team_boards"] == [] and p["player_boards"] == []
    assert p["summary"] is None


def test_shape_competition_payload_drops_deserved_rows_the_warehouse_did_not_rank():
    p = shape_competition_payload(
        "BL1", 2026, {"name": "Bundesliga", "slug": "bundesliga"}, standings=[],
        deserved=[{"name": "A", "deserved_points": None, "deserved_points_gap": None, "deserved_rank": None},
                  {"name": "B", "deserved_points": 3.0, "deserved_points_gap": 1.0, "deserved_rank": 1}],
        summary=None,
    )
    assert [d["name"] for d in p["deserved"]] == ["B"]


def test_shape_competition_payload_surfaces_the_served_header_facts():
    p = shape_competition_payload(
        "BL1", 2026,
        {"name": "Bundesliga", "slug": "bundesliga", "logo_url": "https://x/78.png",
         "region_label_en": "Germany", "region_label_i18n_key": "regionGermany",
         "competition_type": "domestic_league", "entity_type": "club"},
        standings=[], deserved=[], summary=None,
    )
    assert p["crest"] == "https://x/78.png"
    assert p["region_label_en"] == "Germany" and p["region_label_i18n_key"] == "regionGermany"
    assert p["competition_type"] == "domestic_league" and p["entity_type"] == "club"


def test_shape_competition_payload_carries_the_served_season_label_as_is():
    split = shape_competition_payload("BL1", 2026, {"name": "Bundesliga", "slug": "bundesliga"},
                                      standings=[], deserved=[], summary=None,
                                      season_label="2026/27")
    calendar = shape_competition_payload("MLS", 2026, {"name": "MLS", "slug": "mls"},
                                         standings=[], deserved=[], summary=None,
                                         season_label="2026")
    assert split["season"] == 2026 and split["season_label"] == "2026/27"
    assert calendar["season"] == 2026 and calendar["season_label"] == "2026"


def test_fetched_competition_payloads_take_the_label_of_their_own_season(monkeypatch):
    def fake_query(client, sql):
        if "season_label" in sql and "mart_competition_fixtures" in sql:
            return [{"league_code": "BL1", "season_api_year": 2025, "season_label": "2025/26"},
                    {"league_code": "BL1", "season_api_year": 2026, "season_label": "2026/27"}]
        if "mart_competition_season_summary" in sql:
            return [{"league_code": "BL1", "season_api_year": 2026}]
        return []

    monkeypatch.setattr(export_site_data, "_query", fake_query)
    monkeypatch.setattr(export_site_data, "_warehouse_competition_meta", lambda client: {})
    monkeypatch.setattr(export_site_data, "_competition_page_meta", lambda client: {})
    monkeypatch.setattr(export_site_data, "shape_season_summary", lambda *a: None)
    (payload,) = export_site_data.fetch_competition_payloads(object())
    assert payload["season"] == 2026 and payload["season_label"] == "2026/27"


def test_shape_competition_payload_identity_absent_is_none():
    p = shape_competition_payload("XX", 2025, {"name": "X", "slug": "x"},
                                  standings=[], deserved=[], summary=None)
    assert p["crest"] is None and p["region_label_en"] is None and p["entity_type"] is None
    assert p["season_label"] is None


_TEAM_CAT = {
    "goals_per_match": {"label_i18n_key": "metrics.goals_per_match.label", "format": "decimal_1",
                        "metric_group": "goals", "per_match": True},
    "goals_against_per_match": {"label_i18n_key": "metrics.goals_against_per_match.label",
                                "format": "decimal_1", "metric_group": "goals", "per_match": True},
    "cards_red": {"label_i18n_key": "metrics.cards_red.label", "format": "integer",
                  "metric_group": "discipline", "per_match": False},
}


def _tb(key, order, rank, value, name, rank_order="desc"):
    return {"metric_key": key, "rank_order": rank_order, "rank": rank, "sort_value": value,
            "team_sk": hash(name) % 1000, "team_name": name, "team_slug": name.lower(),
            "team_logo_url": f"https://x/{name}.png", "league_leader_order": order}


def test_shape_competition_boards_groups_in_the_ruled_order_and_cuts_at_five_as_served():
    """Rows keep the warehouse's league_leader_order, cut at five, and nothing is sorted here."""
    rows = [_tb("goals_against_per_match", 1, 1, 0.0, "Mainz", "asc"),
            _tb("goals_against_per_match", 2, 2, 0.5, "Koeln", "asc")]
    rows += [_tb("goals_per_match", i, 1 if i < 3 else i - 1, 3.0 - (0 if i < 3 else i * 0.1), f"T{i}")
             for i in range(1, 8)]
    boards = shape_competition_boards(rows, ("goals_per_match", "goals_against_per_match", "cards_red"),
                                      _TEAM_CAT, "team")
    assert [b["metric_key"] for b in boards] == ["goals_per_match", "goals_against_per_match"], \
        "the ruled order, and a board with no rows is omitted"
    goals = boards[0]
    assert len(goals["rows"]) == 5 and [r["rank"] for r in goals["rows"]] == [1, 1, 2, 3, 4]
    assert goals["rank_order"] == "desc" and goals["per_match"] is True
    assert goals["metric_group"] == "goals" and goals["format"] == "decimal_1"
    assert goals["label_i18n_key"] == "metrics.goals_per_match.label"
    against = boards[1]
    assert against["rank_order"] == "asc"
    assert [r["name"] for r in against["rows"]] == ["Mainz", "Koeln"]
    assert against["rows"][0]["value"] == 0.0, "a zero on a fewest-first board is served as it is"
    assert set(against["rows"][0]) == {"rank", "value", "team_id", "slug", "name", "crest"}


def test_shape_competition_boards_player_rows_carry_the_club_and_the_export_slug():
    rows = [{"metric_key": "goals_player", "rank": 1, "sort_value": 9.0, "player_sk": 77,
             "player_name": "Harry Kane", "team_name": "Bayern", "team_slug": "bayern",
             "team_logo_url": "https://x/b.png", "league_leader_order": 1}]
    cat = {"goals_player": {"label_i18n_key": "playerMetrics.scorerPoints.goals", "format": "integer",
                            "metric_group": "goals", "per_match": False}}
    boards = shape_competition_boards(rows, ("goals_player",), cat, "player")
    row = boards[0]["rows"][0]
    assert row["slug"] == player_slug_with_id("Harry Kane", 77)
    assert row["club"] == "Bayern" and row["club_slug"] == "bayern" and row["crest"] == "https://x/b.png"
    assert boards[0]["rank_order"] == "desc", "a player row serves no rank_order; every player board is most first"


_SUMMARY_TEAMS = {
    160: {"team_sk": 160, "team_name": "SC Freiburg", "team_slug": "sc-freiburg", "team_logo_url": "c160"},
    163: {"team_sk": 163, "team_name": "Borussia Mönchengladbach", "team_slug": "gladbach", "team_logo_url": "c163"},
    1660: {"team_sk": 1660, "team_name": "SV Elversberg", "team_slug": "sv-elversberg", "team_logo_url": None},
}


def _summary_row(**overrides) -> dict:
    row = {
        "matches_played": 27, "total_goals": 104, "goals_per_match_played": 3.85,
        "home_wins": 14, "away_wins": 8, "drawn_matches": 5,
        "biggest_margin_fixture_sk": 1575154, "biggest_margin_home_team_sk": 160,
        "biggest_margin_away_team_sk": 163, "biggest_margin_goals_home": 5,
        "biggest_margin_goals_away": 0, "biggest_margin_round_name": "Regular Season - 3",
        "biggest_margin_kickoff_datetime": "2026-09-12T13:30:00",
        "most_goals_fixture_sk": 1575153, "most_goals_home_team_sk": 163,
        "most_goals_away_team_sk": 1660, "most_goals_goals_home": 3, "most_goals_goals_away": 4,
        "most_goals_round_name": "Regular Season - 2",
        "most_goals_kickoff_datetime": "2026-09-05T13:30:00",
        "longest_unbeaten_run": 3, "longest_unbeaten_team_sks": [160],
        "longest_winless_run": 3, "longest_winless_team_sks": [163, 1660],
    }
    row.update(overrides)
    return row


_SUMMARY_SLUGS = {
    1575154: "2026-09-12-sc-freiburg-vs-gladbach",
    1575153: "2026-09-05-gladbach-vs-sv-elversberg",
}


def test_shape_season_summary_resolves_teams_and_fixtures_to_what_the_page_links():
    s = shape_season_summary(_summary_row(), _SUMMARY_TEAMS, _SUMMARY_SLUGS)
    assert s["matches_played"] == 27 and s["total_goals"] == 104 and s["goals_per_match"] == 3.85
    assert s["home_wins"] == 14 and s["away_wins"] == 8 and s["drawn_matches"] == 5
    bm = s["biggest_margin"]
    assert bm["fixture_id"] == 1575154 and bm["goals_home"] == 5 and bm["goals_away"] == 0
    assert bm["slug"] == "2026-09-12-sc-freiburg-vs-gladbach", "the served slug, never built here"
    assert bm["home"]["slug"] == "sc-freiburg" and bm["away"]["name"] == "Borussia Mönchengladbach"
    assert bm["round"] == "Regular Season - 3"
    assert s["most_goals"]["away"] == {"team_id": 1660, "name": "SV Elversberg",
                                       "slug": "sv-elversberg", "crest": None}
    assert s["longest_unbeaten_run"] == 3
    assert [t["slug"] for t in s["longest_unbeaten_teams"]] == ["sc-freiburg"]
    assert [t["slug"] for t in s["longest_winless_teams"]] == ["gladbach", "sv-elversberg"]


def test_shape_season_summary_keeps_a_null_fact_null_and_a_missing_row_none():
    s = shape_season_summary(
        _summary_row(home_wins=None, away_wins=None, biggest_margin_fixture_sk=None,
                     longest_unbeaten_team_sks=[]),
        _SUMMARY_TEAMS, _SUMMARY_SLUGS,
    )
    assert s["home_wins"] is None and s["away_wins"] is None
    assert s["biggest_margin"] is None
    assert s["longest_unbeaten_teams"] == []
    assert shape_season_summary(None, _SUMMARY_TEAMS, _SUMMARY_SLUGS) is None


def test_shape_season_summary_computes_nothing():
    """A served ratio that disagrees with its own counts is passed through, never recomputed."""
    s = shape_season_summary(_summary_row(goals_per_match_played=9.99), _SUMMARY_TEAMS, _SUMMARY_SLUGS)
    assert s["goals_per_match"] == 9.99


def test_shape_season_summary_links_no_match_the_warehouse_gave_no_slug():
    """The slug is looked up, never built: a fixture absent from the served slugs links nowhere."""
    s = shape_season_summary(_summary_row(), _SUMMARY_TEAMS, {})
    assert s["biggest_margin"]["fixture_id"] == 1575154 and s["biggest_margin"]["slug"] is None


def _served_fixture(fid, rnd, seq, kickoff, order=None, played=False, nxt=False, top=False, pos=None):
    return {
        "fixture_id": fid, "slug": f"s{fid}", "kickoff": kickoff, "round": rnd,
        "round_order": order, "round_sequence": seq, "fixture_order": pos,
        "status": "FT" if played else "NS",
        "is_played": played, "goals_home": 2 if played else None, "goals_away": 1 if played else None,
        "home": {"team_id": 1, "name": "A", "slug": "a", "crest": None},
        "away": {"team_id": 2, "name": "B", "slug": "b", "crest": None},
        "is_next_round": nxt, "is_match_that_matters": top,
    }


def test_group_fixtures_by_round_follows_the_served_fixture_order():
    """Only the served fixture_order decides, so the kickoffs here are out of step with it."""
    rows = [
        _served_fixture(30, "Round of 16", 3, "2026-10-01T18:00:00", pos=5),
        _served_fixture(21, "Regular Season - 2", 2, "2026-09-05T13:30:00", order=2, nxt=True, top=True, pos=4),
        _served_fixture(20, "Regular Season - 2", 2, "2026-09-04T18:30:00", order=2, nxt=True, pos=3),
        _served_fixture(11, "Regular Season - 1", 1, "2026-08-28T18:30:00", order=1, played=True, pos=2),
        _served_fixture(10, "Regular Season - 1", 1, "2026-08-29T18:30:00", order=1, played=True, pos=1),
    ]
    rounds = group_fixtures_by_round(rows)
    assert [r["round"] for r in rounds] == ["Regular Season - 1", "Regular Season - 2", "Round of 16"]
    assert [r["round_sequence"] for r in rounds] == [1, 2, 3]
    assert [r["round_order"] for r in rounds] == [1, 2, None]
    assert [r["is_next_round"] for r in rounds] == [False, True, False]
    assert [f["fixture_id"] for f in rounds[0]["fixtures"]] == [10, 11], "by fixture_order, not by kickoff"
    assert [f["fixture_id"] for f in rounds[1]["fixtures"]] == [20, 21]
    assert rounds[1]["fixtures"][1]["is_match_that_matters"] is True
    assert rounds[0]["fixtures"][0]["is_played"] is True and rounds[0]["fixtures"][0]["goals_home"] == 2
    assert "round_sequence" not in rounds[0]["fixtures"][0] and "is_next_round" not in rounds[0]["fixtures"][0]
    assert "fixture_order" not in rounds[0]["fixtures"][0], "the ordering key is consumed, not shipped"
    assert rounds[0]["fixtures"][0]["slug"] == "s10", "the served slug is carried through"


def test_group_fixtures_by_round_lifts_the_served_round_name():
    name = {"round_label_i18n_key": "roundGroupMatchday", "round_number": 2, "round_letter": "A"}
    rows = [dict(_served_fixture(21, "Group A - 2", 2, "2026-09-05T13:30:00", order=2, pos=2), **name),
            dict(_served_fixture(20, "Group A - 2", 2, "2026-09-04T18:30:00", order=2, pos=1), **name)]
    (rnd,) = group_fixtures_by_round(rows)
    assert {k: rnd[k] for k in name} == name
    assert all(k not in f for f in rnd["fixtures"] for k in name)


def test_the_competition_fixture_shape_selects_and_carries_the_served_round_name():
    """The Matchdays picker, the match-day files and Home's upcoming block all read this one shape."""
    for col in ("round_label_i18n_key", "round_number", "round_letter"):
        assert col in export_site_data._COMPETITION_FIXTURE_COLUMNS
    row = {"fixture_sk": 7, "fixture_slug": "s7", "kickoff_datetime": "2026-09-05T13:30:00Z",
           "round_name": "Championship Group - 23", "round_label_i18n_key": "roundVlChampionshipMatchday",
           "round_number": 23, "round_letter": None, "round_order": 23, "round_sequence": 23,
           "fixture_order": 1, "status_short": "NS", "is_played": False,
           "home_team_sk": 1, "away_team_sk": 2, "is_next_round": True, "is_match_that_matters": False}
    out = export_site_data._competition_fixture(row)
    assert out["round_label_i18n_key"] == "roundVlChampionshipMatchday"
    assert out["round_number"] == 23 and out["round_letter"] is None


def test_the_competition_page_meta_selects_the_served_current_round():
    for col in ("current_round_label_i18n_key", "current_round_number", "current_round_letter"):
        assert col in export_site_data._COMPETITION_PAGE_META


def test_shape_competition_payload_carries_the_served_current_round():
    meta = {"name": "Veikkausliiga", "slug": "veikkausliiga",
            "current_round_label_i18n_key": "roundVlChampionshipMatchday",
            "current_round_number": 23, "current_round_letter": None}
    p = shape_competition_payload("VL", 2026, meta, standings=[], deserved=[], summary=None)
    assert p["current_round_label_i18n_key"] == "roundVlChampionshipMatchday"
    assert p["current_round_number"] == 23 and p["current_round_letter"] is None


def test_group_fixtures_by_round_is_empty_when_nothing_is_served():
    assert group_fixtures_by_round([]) == []
    p = shape_competition_payload("XX", 2025, {"name": "X", "slug": "x"},
                                  standings=[], deserved=[], summary=None)
    assert p["fixtures"] == []


def test_fixture_side_carries_identity_and_handles_missing():
    side = _fixture_side(1, {"team_name": "A", "team_slug": "a", "team_logo_url": "u", "team_country": "X"},
                         {"goals_per_match": 1.4}, None)
    assert side["team_id"] == 1 and side["name"] == "A" and side["slug"] == "a" and side["crest"] == "u"
    assert side["form"] == {"goals_per_match": 1.4}
    assert side["standing"] is None and side["top_players"] == []  # honest absence


def test_form_block_is_the_block_the_warehouse_flags():
    keys = {"upcoming_fixture_sk": 9, "team_sk": 1, "is_home": True}
    w1 = {"fixture_sk": 9, "team_sk": 1, "is_home": True, "window_type": "last_5", "goals_per_match": 1.4}
    w2 = {**keys, "window_type": "prev_season", "goals_per_match": 2.0}
    assert form_block({**w1, "is_form_window": True}, {**w2, "is_form_window": False}) == {
        "window_type": "last_5", "goals_per_match": 1.4}
    assert form_block({**w1, "is_form_window": False}, {**w2, "is_form_window": True}) == {
        "window_type": "prev_season", "goals_per_match": 2.0}
    assert form_block({**w1, "is_form_window": False}, {**w2, "is_form_window": False}) is None
    assert form_block(None, None) is None


def test_shape_fixture_payload_composes_header_and_sides():
    fix = {"fixture_sk": 7, "kickoff_datetime": "2026-06-11T19:00:00",
           "status_short": "NS", "league_code": "WC", "league_name": "World Cup",
           "season_api_year": 2026, "round_name": "Group Stage - 1",
           "venue_name_snapshot": "Estadio", "home_team_name": "Mexico",
           "away_team_name": "South Africa", "fixture_slug": "2026-06-11-mexico-vs-south-africa"}
    home = _fixture_side(1, {"team_name": "Mexico"}, None, None, None)
    away = _fixture_side(2, {"team_name": "South Africa"}, None, None, None)
    p = shape_fixture_payload(fix, home, away, {"total_meetings": 3, "wins": 2})
    assert p["type"] == "fixture" and p["fixture_id"] == 7
    assert p["slug"] == "2026-06-11-mexico-vs-south-africa", "the served fixture_slug, never built here"
    assert p["league_name"] == "World Cup" and p["round"] == "Group Stage - 1"
    assert p["home"]["team_id"] == 1 and p["away"]["team_id"] == 2
    assert p["head_to_head"] == {"total_meetings": 3, "wins": 2}


def test_shape_next_match_is_the_mart_row_unless_it_is_this_match():
    row = {"fixture_sk": 11, "league_code": "DFBP", "kickoff_datetime": "2026-10-28T19:45:00",
           "round_name": "2nd Round", "round_order": None, "round_sequence": 2, "fixture_order": 4,
           "fixture_slug": "2026-10-28-a-vs-b", "status_short": "TBD", "is_played": False,
           "goals_home": None, "goals_away": None, "is_next_round": False, "is_match_that_matters": False,
           "home_team_sk": 1, "home_team_name": "A", "home_team_slug": "a", "home_team_logo_url": "ua",
           "away_team_sk": 2, "away_team_name": "B", "away_team_slug": "b", "away_team_logo_url": "ub"}
    m = shape_next_match(row, 7)
    assert m == {**export_site_data._competition_fixture(row), "league_code": "DFBP"}, \
        "the site's one match row, with its competition"
    assert m["fixture_id"] == 11 and m["slug"] == "2026-10-28-a-vs-b" and m["status"] == "TBD"
    assert m["home"] == {"team_id": 1, "name": "A", "slug": "a", "crest": "ua"}
    assert m["away"]["team_id"] == 2 and m["is_played"] is False
    assert shape_next_match(row, 11) is None, "the page's own match is not its next match"
    assert shape_next_match(None, 7) is None
    side = _fixture_side(1, {"team_name": "A"}, None, None, None, next_match=m)
    assert side["next_match"] == m


def _match_row(fid, home, away, kickoff, home_next=False, away_next=False, next_round=True):
    return {"fixture_sk": fid, "league_code": "BL1", "season_api_year": 2026, "kickoff_datetime": kickoff,
            "round_name": "Regular Season - 5", "round_order": 5, "round_sequence": 5, "fixture_order": fid,
            "status_short": "NS", "is_played": False, "goals_home": None, "goals_away": None,
            "is_next_round": next_round, "is_match_that_matters": False,
            "venue_name_snapshot": "Arena %d" % fid,
            "fixture_slug": "slug-%d" % fid,
            "home_team_sk": home, "home_team_name": "T%d" % home, "home_team_slug": "t%d" % home,
            "home_team_logo_url": "c%d" % home,
            "away_team_sk": away, "away_team_name": "T%d" % away, "away_team_slug": "t%d" % away,
            "away_team_logo_url": "c%d" % away,
            "is_home_team_next_match": home_next, "is_away_team_next_match": away_next}


def test_fixture_payloads_read_the_match_and_each_teams_next_match_from_the_mart(monkeypatch):
    """A team's next match is the row the mart flags for it, and none when that is the page's own match."""
    page = _match_row(20, 1, 2, "2026-10-31T17:30:00Z", away_next=True, next_round=False)
    team1_next = _match_row(10, 3, 1, "2026-10-10T13:30:00Z", away_next=True)
    captured: list[str] = []

    def fake_query(client, sql):
        captured.append(sql)
        if "mart_competition_fixtures" in sql and "status_short in" in sql:
            return [{**page, "home_team_country": "Germany", "away_team_country": "Germany"}]
        if "mart_competition_fixtures" in sql and "next_match" in sql:
            return [team1_next, page]
        if "mart_competition_index" in sql:
            return [{"league_code": "BL1", "competition_name": "Bundesliga"}]
        return []

    monkeypatch.setattr(export_site_data, "_query", fake_query)
    (p,) = export_site_data.fetch_fixture_payloads(object())

    assert not any(".core." in s for s in captured), "every read is a mart"
    assert p["venue"] == "Arena 20" and p["league_name"] == "Bundesliga" and p["slug"] == "slug-20"
    assert p["home"]["name"] == "T1" and p["home"]["crest"] == "c1" and p["home"]["country"] == "Germany"
    assert p["is_next_round"] is False, "the served flag says which page this fixture gets"
    assert p["home"]["next_match"]["fixture_id"] == 10, "team 1's flagged row, though it plays away there"
    assert p["home"]["next_match"]["status"] == "NS" and p["home"]["next_match"]["league_code"] == "BL1"
    assert p["away"]["next_match"] is None, "team 2's next match is this page's own match"


def test_fixture_payloads_carry_the_served_window_round_slugs_and_season_players(monkeypatch):
    """Form is the flagged block, and Players to watch are mart_player_season_record's top five by rank."""
    page = _match_row(20, 1, 2, "2026-10-31T17:30:00Z")
    keys = {"upcoming_fixture_sk": 20, "is_home": True}

    def fake_query(client, sql):
        if "mart_competition_fixtures" in sql and "status_short in" in sql:
            return [page]
        if "mart_team_window_metrics`" in sql:
            form_keys = {"fixture_sk": 20, "is_home": True}
            return [{**form_keys, "team_sk": 1, "window_type": "last_5", "goals_per_match": 1.4, "is_form_window": True},
                    {**form_keys, "team_sk": 2, "window_type": "last_5", "goals_per_match": 0.9, "is_form_window": False}]
        if "mart_team_season_record" in sql:
            return [{**keys, "team_sk": 2, "window_type": "prev_season", "goals_per_match": 2.0, "is_form_window": True}]
        if "mart_player_season_record" in sql:
            return [{**keys, "team_sk": 1, "player_sk": 7, "player_name": "P7", "player_photo_url": "u7",
                     "top_player_rank": 1, "goals_total": 3, "goals_assists": 1,
                     "window_type": "season_to_date", "league_code": "BL1"}]
        return []

    monkeypatch.setattr(export_site_data, "_query", fake_query)
    (p,) = export_site_data.fetch_fixture_payloads(object())

    assert p["round_order"] == 5
    assert p["home"]["slug"] == "t1" and p["away"]["slug"] == "t2"
    assert p["home"]["form"] == {"window_type": "last_5", "goals_per_match": 1.4}
    assert p["away"]["form"] == {"window_type": "prev_season", "goals_per_match": 2.0}, "the flagged season record"
    assert p["home"]["top_players"] == [{"player_sk": 7, "goals_total": 3, "goals_assists": 1,
                                          "window_type": "season_to_date", "player_name": "P7",
                                          "player_photo_url": "u7"}]


def test_player_slug_folds_accents_and_appends_id():
    assert player_slug_with_id("Bayern München", 157) == "bayern-munchen-157"


def test_player_slug_collapses_punctuation_and_spaces():
    assert player_slug_with_id("Brighton & Hove Albion", 51) == "brighton-hove-albion-51"


def test_player_slug_falls_back_to_id_when_name_empty():
    assert player_slug_with_id("", 99) == "99"
    assert player_slug_with_id(None, 99) == "99"


def test_player_slug_still_drops_undecomposable_letters():
    """`_kebab` drops characters with no NFKD decomposition; team slugs are served, player slugs still use it."""
    assert player_slug_with_id("Sigurðsson", 1) == "sigursson-1"
    assert player_slug_with_id("Preußen", 2) == "preuen-2"


def test_shape_team_payload_identity_from_latest_and_seasons_desc():
    rows = [
        {"team_sk": 157, "season_api_year": 2024, "league_code": "BL1",
         "team_name": "Bayern", "team_slug": "bayern-munchen", "team_country": "Germany",
         "team_logo_url": "u", "points": 78,
         "team_founded_year": 1900, "venue_name": "Old", "venue_city": "München", "venue_capacity": 70000},
        {"team_sk": 157, "season_api_year": 2025, "league_code": "BL1",
         "team_name": "Bayern München", "team_slug": "bayern-munchen", "team_country": "Germany",
         "team_logo_url": "u2", "points": 82,
         "team_founded_year": 1900, "venue_name": "Allianz Arena", "venue_city": "München", "venue_capacity": 75000},
    ]
    p = shape_team_payload(_mark_featured(rows))
    assert p["team_id"] == 157
    # The slug is served by mart_team_profile and carries no provider id.
    assert p["slug"] == "bayern-munchen"              # from the 2025 (latest) row
    assert p["name"] == "Bayern München"
    # Founded year and venue come from the latest row; venue is a nested block.
    assert p["founded_year"] == 1900
    assert p["venue"] == {"name": "Allianz Arena", "city": "München", "capacity": 75000}
    assert [s["season_api_year"] for s in p["seasons"]] == [2025, 2024]  # desc
    # identity columns (incl. founded/venue and the slug) are stripped from per-season rows
    assert "team_name" not in p["seasons"][0]
    assert "team_slug" not in p["seasons"][0]
    assert "team_founded_year" not in p["seasons"][0] and "venue_name" not in p["seasons"][0]
    assert p["seasons"][0]["points"] == 82


def test_shape_team_payload_venue_absent_is_none():
    p = shape_team_payload(_mark_featured([{"team_sk": 9, "season_api_year": 2025,
                                            "league_code": "BL1", "team_name": "X"}]))
    assert p["venue"] is None
    assert p["founded_year"] is None


def test_deserved_scatter_index_groups_by_league_season_and_excludes_null():
    rows = [
        {"team_sk": 1, "league_code": "PL", "season_api_year": 2024,
         "shots_on_goal_difference_per_match": 2.4, "points": 84, "deserved_points": 77.0},
        {"team_sk": 2, "league_code": "PL", "season_api_year": 2024,
         "shots_on_goal_difference_per_match": -0.3, "points": 65, "deserved_points": 50.0},
        # a tournament / non-single-ladder row: deserved is null -> excluded entirely
        {"team_sk": 3, "league_code": "WC", "season_api_year": 2026,
         "shots_on_goal_difference_per_match": 1.0, "points": 6, "deserved_points": None},
        # a different league-season -> its own bucket
        {"team_sk": 4, "league_code": "BL1", "season_api_year": 2024,
         "shots_on_goal_difference_per_match": 1.1, "points": 70, "deserved_points": 66.0},
    ]
    idx = deserved_scatter_index(rows)
    assert set(idx.keys()) == {("PL", 2024), ("BL1", 2024)}   # WC dropped (deserved null)
    pl = idx[("PL", 2024)]
    assert len(pl) == 2
    # raw values passed through (no rounding, no derivation)
    assert pl[0] == {"team_sk": 1, "name": None, "sotd": 2.4, "points": 84, "deserved": 77.0}


def test_shape_team_payload_attaches_deserved_scatter_and_flags_self():
    rows = [{"team_sk": 2, "season_api_year": 2024, "league_code": "PL",
             "team_name": "Forest", "points": 65, "deserved_points": 50.0,
             "shots_on_goal_difference_per_match": -0.3}]
    idx = deserved_scatter_index([
        {"team_sk": 1, "league_code": "PL", "season_api_year": 2024,
         "shots_on_goal_difference_per_match": 2.4, "points": 84, "deserved_points": 77.0},
        {"team_sk": 2, "league_code": "PL", "season_api_year": 2024, "team_name": "Forest",
         "shots_on_goal_difference_per_match": -0.3, "points": 65, "deserved_points": 50.0},
    ])
    p = shape_team_payload(_mark_featured(rows), scatter_index=idx)
    sc = p["seasons"][0]["deserved_scatter"]
    assert len(sc) == 2
    self_dot = next(d for d in sc if d["is_self"])
    assert self_dot == {"name": "Forest", "sotd": -0.3, "points": 65, "deserved": 50.0, "is_self": True}
    assert sum(1 for d in sc if d["is_self"]) == 1          # exactly one self


def test_league_strip_lists_every_club_of_the_featured_season_and_flags_self():
    rows = [
        {"team_sk": 2, "season_api_year": 2025, "league_code": "PL", "team_name": "Forest"},
        {"team_sk": 2, "season_api_year": 2024, "league_code": "PL", "team_name": "Forest"},
    ]
    bench = [
        {"team_sk": t, "team_name": n, "league_code": "PL", "season_api_year": y,
         "metric_key": k, "metric_value": v}
        for y in (2024, 2025)
        for t, n, k, v in [(2, "Forest", "goals_per_match", 1.2), (1, "City", "goals_per_match", 2.4),
                           (1, "City", "fouls_per_match", 9.0), (2, "Forest", "fouls_per_match", 12.0)]
    ]
    idx = league_strip_index(bench)
    p = shape_team_payload(_mark_featured(rows), strip_index=idx)
    featured, other = p["seasons"]
    assert [m["metric_key"] for m in featured["league_strip"]] == ["fouls_per_match", "goals_per_match"]
    goals = featured["league_strip"][1]["clubs"]
    assert goals == [{"name": "City", "value": 2.4, "is_self": False},
                     {"name": "Forest", "value": 1.2, "is_self": True}]
    assert "league_strip" not in other


def test_the_featured_season_lists_its_competitions_in_the_served_order():
    rows = [
        {"team_sk": 165, "season_api_year": 2026, "league_code": "BL1", "team_name": "Dortmund"},
        {"team_sk": 165, "season_api_year": 2025, "league_code": "BL1", "team_name": "Dortmund"},
    ]
    comps = [
        {"team_sk": 165, "league_code": "UCL", "season_api_year": 2026, "competition_order": 3,
         "competition_type": "continental_cup", "standing_rank": 18, "reached_round_stage_kind": "table",
         "cup_status": None, "internal": "x"},
        {"team_sk": 165, "league_code": "BL1", "season_api_year": 2026, "competition_order": 1,
         "competition_type": "domestic_league", "standing_rank": 2, "latest_played_round_number": 6},
        {"team_sk": 165, "league_code": "DFBP", "season_api_year": 2026, "competition_order": 2,
         "competition_type": "domestic_cup", "reached_round_label_i18n_key": "roundSecondRound",
         "reached_round_stage_kind": "knockout", "cup_status": "through"},
        {"team_sk": 165, "league_code": "DFBP", "season_api_year": 2025, "competition_order": 2,
         "competition_type": "domestic_cup", "cup_status": "knocked_out"},
    ]
    p = shape_team_payload(_mark_featured(rows), competition_rows=comps)
    featured, other = p["seasons"]
    assert [c["league_code"] for c in featured["competitions"]] == ["BL1", "DFBP", "UCL"]
    assert featured["competitions"][1]["cup_status"] == "through"
    assert set(featured["competitions"][0]) == set(export_site_data._TEAM_COMPETITION_FIELDS)
    assert "competitions" not in other


def test_a_sampled_team_export_scopes_its_competitions_to_the_sample(monkeypatch):
    profile = [{"team_sk": 1, "season_api_year": 2026, "league_code": "PL", "team_name": "City",
                "is_featured_season": True}]
    seen = []

    def fake_query(client, sql):
        seen.append(sql)
        return profile if "mart_team_profile" in sql else []

    monkeypatch.setattr(export_site_data, "_query", fake_query)
    export_site_data.fetch_team_payloads(client=None, sample=1)
    comp_sql = next(s for s in seen if "mart_team_competitions" in s)
    assert "team_sk in (1)" in comp_sql


def test_the_team_payload_lists_its_recent_matches_newest_first():
    rows = [{"team_sk": 165, "season_api_year": 2026, "league_code": "BL1", "team_name": "Dortmund"}]
    recent = [
        {"upcoming_fixture_sk": None, "team_sk": 165, "league_code": None, "is_home": None,
         "entity_type": "club", "season_api_year": 2026, "window_type": "last_5", "recency_rank": r,
         "played_fixture_sk": 900 + r, "played_league_code": "BL1", "result": res}
        for r, res in [(2, "D"), (1, "W"), (3, "L")]
    ]
    p = shape_team_payload(_mark_featured(rows), recent_rows=recent)
    assert [m["played_fixture_sk"] for m in p["recent_matches"]] == [901, 902, 903]
    assert set(p["recent_matches"][0]) == {"recency_rank", "played_fixture_sk", "played_league_code", "result"}
    assert shape_team_payload(_mark_featured(rows))["recent_matches"] == []


def test_a_sampled_team_export_reads_the_team_window_of_the_sample(monkeypatch):
    profile = [{"team_sk": 1, "season_api_year": 2026, "league_code": "PL", "team_name": "City",
                "is_featured_season": True}]
    seen = []

    def fake_query(client, sql):
        seen.append(sql)
        return profile if "mart_team_profile" in sql else []

    monkeypatch.setattr(export_site_data, "_query", fake_query)
    export_site_data.fetch_team_payloads(client=None, sample=1)
    recent_sql = next(s for s in seen if "mart_team_momentum_window" in s)
    assert "upcoming_fixture_sk is null" in recent_sql
    assert "team_sk in (1)" in recent_sql


def test_a_sampled_team_export_reads_every_club_for_the_strip(monkeypatch):
    # A sample run scopes most queries to the sampled teams, but the strip shows the whole league,
    # so the benchmark query must read every club.
    profile = [
        {"team_sk": t, "season_api_year": 2025, "league_code": "PL", "team_name": n,
         "is_featured_season": True}
        for t, n in [(1, "City"), (2, "Forest")]
    ]
    bench = [
        {"team_sk": t, "team_name": n, "league_code": "PL", "season_api_year": 2025,
         "metric_key": "goals_per_match", "metric_value": v}
        for t, n, v in [(1, "City", 2.4), (2, "Forest", 1.2)]
    ]
    seen = []

    def fake_query(client, sql):
        seen.append(sql)
        if "mart_team_profile" in sql:
            return profile
        if "mart_team_competition_benchmarks" in sql:
            return bench
        return []

    monkeypatch.setattr(export_site_data, "_query", fake_query)
    payloads = export_site_data.fetch_team_payloads(client=None, sample=1)
    bench_sql = next(s for s in seen if "mart_team_competition_benchmarks" in s)
    assert "where" not in bench_sql.lower()
    clubs = payloads[0]["seasons"][0]["league_strip"][0]["clubs"]
    assert [c["name"] for c in clubs] == ["City", "Forest"]


def test_shape_team_payload_no_scatter_when_season_not_fittable():
    # a season with no deserved value (not in the index) -> no deserved_scatter key (absent state)
    rows = [{"team_sk": 9, "season_api_year": 2026, "league_code": "WC",
             "team_name": "X", "points": 6}]
    p = shape_team_payload(_mark_featured(rows), scatter_index={})
    assert "deserved_scatter" not in p["seasons"][0]


def test_deserved_scatter_preserves_the_fitted_line():
    # deserved_points is linear in sotd within a league-season, so the export must pass it through
    # unrounded for the trend line to stay true.
    intercept, slope = 40.0, 8.0
    sotds = [-2.0, -0.5, 0.5, 1.5, 3.0]
    league = [
        {"team_sk": i, "league_code": "PL", "season_api_year": 2024,
         "shots_on_goal_difference_per_match": x, "points": 50 + i,
         "deserved_points": intercept + slope * x}
        for i, x in enumerate(sotds)
    ]
    idx = deserved_scatter_index(league)
    self_rows = [{"team_sk": 2, "season_api_year": 2024, "league_code": "PL",
                  "team_name": "Self", "points": 52,
                  "shots_on_goal_difference_per_match": 0.5,
                  "deserved_points": intercept + slope * 0.5}]
    sc = shape_team_payload(_mark_featured(self_rows), scatter_index=idx)["seasons"][0]["deserved_scatter"]
    assert len(sc) == len(sotds)
    for d in sc:                                   # every dot on intercept + slope*sotd
        assert d["deserved"] == intercept + slope * d["sotd"]
    self_dot = next(d for d in sc if d["is_self"])
    assert self_dot["deserved"] == intercept + slope * self_dot["sotd"]


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
    p = shape_team_payload(_mark_featured(rows), fixtures)
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


def test_the_team_schedule_lists_every_match_ahead_and_every_result_of_the_featured_year():
    rows = [{"team_sk": 165, "season_api_year": 2026, "league_code": "BL1", "team_name": "Dortmund"}]

    def fx(sk, kickoff, year, *, upcoming=None, recency=None, order=None, league="BL1"):
        return {"team_sk": 165, "fixture_sk": sk, "league_code": league, "season_api_year": year,
                "kickoff_datetime": kickoff, "opponent_team_sk": 5, "opponent_name": f"O{sk}",
                "opponent_logo_url": "x", "is_home": True, "round_name": "R", "goals_for": None,
                "goals_against": None, "result": None, "status_short": "NS",
                "has_result": recency is not None, "is_upcoming": upcoming is not None,
                "upcoming_rank": upcoming, "recency_rank": recency,
                "upcoming_order": order if upcoming is not None else None,
                "result_order": order if recency is not None else None}

    # the kick-offs disagree with the served orders on purpose: the export follows the mart's order
    fixtures = [
        fx(3, "2026-11-08 14:30:00+00:00", 2026, upcoming=2, order=3),
        fx(4, "2026-11-04 20:00:00+00:00", 2026, upcoming=1, order=2, league="UCL"),
        fx(1, "2026-11-09 14:30:00+00:00", 2026, upcoming=1, order=1),
        fx(7, "2027-07-30 18:00:00+00:00", 2027, upcoming=1, order=4),
        fx(10, "2026-10-25 14:30:00+00:00", 2026, recency=1, order=1),
        fx(9, "2026-10-28 19:00:00+00:00", 2026, recency=1, order=2, league="UCL"),
        fx(8, "2026-05-16 14:30:00+00:00", 2025, recency=1, order=1),
    ]
    sched = shape_team_payload(_mark_featured(rows), fixtures)["schedule"]
    assert [f["fixture_id"] for f in sched["upcoming"]] == [1, 4, 3, 7]
    assert [f["fixture_id"] for f in sched["results"]] == [10, 9], "last season's result is not listed"
    assert sched["upcoming"][1] == {
        "fixture_id": 4, "league_code": "UCL", "upcoming_rank": 1, "opponent_name": "O4",
        # the payload carries no order key: its list order is the order
        "opponent_logo_url": "x", "is_home": True, "kickoff_datetime": "2026-11-04 20:00:00+00:00",
        "round_name": "R", "goals_for": None, "goals_against": None, "result": None,
        "status_short": "NS"}
    assert shape_team_payload(_mark_featured(rows))["schedule"] == {"upcoming": [], "results": []}


def test_each_team_season_carries_its_competitions_season_label():
    rows = [{"team_sk": 1, "season_api_year": 2026, "league_code": "PL", "team_name": "City"},
            {"team_sk": 1, "season_api_year": 2026, "league_code": "MLS", "team_name": "City"}]
    labels = {("PL", 2026): "2026/27", ("MLS", 2026): "2026"}
    p = shape_team_payload(_mark_featured(rows), season_labels=labels)
    assert {s["league_code"]: s["season_label"] for s in p["seasons"]} == {"PL": "2026/27", "MLS": "2026"}
    assert shape_team_payload(_mark_featured(rows))["seasons"][0]["season_label"] is None


def test_a_team_export_reads_each_seasons_label_from_the_warehouse(monkeypatch):
    profile = [{"team_sk": 1, "season_api_year": 2026, "league_code": "PL", "team_name": "City",
                "season_label": "2026/27", "is_featured_season": True}]

    def fake_query(client, sql):
        return profile if "mart_team_profile" in sql else []

    monkeypatch.setattr(export_site_data, "_query", fake_query)
    (payload,) = export_site_data.fetch_team_payloads(client=None, sample=1)
    assert payload["seasons"][0]["season_label"] == "2026/27"


def test_a_sampled_team_export_reads_every_ranked_fixture(monkeypatch):
    profile = [{"team_sk": 1, "season_api_year": 2026, "league_code": "PL", "team_name": "City",
                "is_featured_season": True}]
    seen = []

    def fake_query(client, sql):
        seen.append(sql)
        return profile if "mart_team_profile" in sql else []

    monkeypatch.setattr(export_site_data, "_query", fake_query)
    export_site_data.fetch_team_payloads(client=None, sample=1)
    fx_sql = next(s for s in seen if "mart_team_fixtures" in s)
    assert "(upcoming_rank is not null or recency_rank is not null)" in fx_sql
    assert "team_sk in (1)" in fx_sql


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
    p = shape_team_payload(_mark_featured(rows), None, roster)
    s2025 = p["seasons"][0]
    assert s2025["season_api_year"] == 2025
    # sorted by player_sk (byte-stable), the null-name member omitted
    assert [m["player_id"] for m in s2025["squad"]] == [1, 9, 30]
    assert [m["name"] for m in s2025["squad"]] == ["Neuer", "Kane", "Kimmich"]
    # each member carries the identity keys + the four per-season stat keys (null here: no career rows)
    assert set(s2025["squad"][0]) == {
        "player_id", "name", "position", "nationality", "birth_date", "photo",
        "appearances", "minutes_per_appearance", "goals", "assists"}
    assert all(
        m["appearances"] is None and m["minutes_per_appearance"] is None
        and m["goals"] is None and m["assists"] is None
        for m in s2025["squad"]
    )
    for internal in ("team_sk", "league_code", "season_api_year", "player_team_season_sk",
                     "season_sk", "competition_type", "entity_type", "player_sk"):
        assert all(internal not in m for m in s2025["squad"])
    # a season with no roster rows renders the empty squad
    assert p["seasons"][1]["squad"] == []


def test_shape_team_payload_squad_defaults_empty_without_roster():
    rows = [{"team_sk": 9, "season_api_year": 2025, "league_code": "PL",
             "team_name": "Arsenal", "team_country": "England", "team_logo_url": "u"}]
    p = shape_team_payload(_mark_featured(rows))
    assert p["seasons"][0]["squad"] == []


def test_shape_team_payload_joins_career_stats_to_squad_by_player_sk():
    rows = [{"team_sk": 157, "season_api_year": 2025, "league_code": "BL1",
             "team_name": "Bayern", "team_country": "Germany", "team_logo_url": "u"}]
    roster = [
        {"team_sk": 157, "player_sk": 9, "league_code": "BL1", "season_api_year": 2025,
         "player_name": "Kane", "player_position": "Attacker", "player_nationality": "England",
         "player_birth_date": "1993-07-28", "player_photo_url": "p"},
        {"team_sk": 157, "player_sk": 1, "league_code": "BL1", "season_api_year": 2025,
         "player_name": "Neuer", "player_position": "Goalkeeper", "player_nationality": "Germany",
         "player_birth_date": "1986-03-27", "player_photo_url": "p"},
    ]
    career = [
        # Kane: a career row for THIS season -> stats join; his 2024 row must NOT match 2025
        {"team_sk": 157, "player_sk": 9, "league_code": "BL1", "season_api_year": 2025,
         "appearances": 30, "minutes_per_appearance": 88.0, "goals_player": 26, "assists_player": 8},
        {"team_sk": 157, "player_sk": 9, "league_code": "BL1", "season_api_year": 2024,
         "appearances": 32, "minutes_per_appearance": 90.0, "goals_player": 36, "assists_player": 8},
        # Neuer: no career row -> stats null (never appeared in a finished-match squad)
    ]
    p = shape_team_payload(_mark_featured(rows), None, roster, None, None, career)
    squad = {m["player_id"]: m for m in p["seasons"][0]["squad"]}
    # joined by (league_code, season, player_sk); the 2024 row did not leak into 2025
    assert squad[9]["appearances"] == 30
    assert squad[9]["minutes_per_appearance"] == 88.0
    assert squad[9]["goals"] == 26 and squad[9]["assists"] == 8
    # no career row -> nulls (the frontend shows only members with >= 1 appearance)
    assert squad[1]["appearances"] is None
    assert squad[1]["minutes_per_appearance"] is None
    assert squad[1]["goals"] is None and squad[1]["assists"] is None


def test_shape_team_benchmark_member_carries_mart_columns():
    # Select and reshape only: eight columns, with no num/den as the team mart has none.
    m = _shape_team_benchmark_member({
        "team_benchmark_sk": 1, "team_sk": 157, "season_sk": 2, "league_sk": 3,
        "league_code": "BL1", "season_api_year": 2025, "metric_key": "goals_per_match",
        "metric_value": 2.2, "league_mean": 1.6, "league_median": 1.5,
        "league_p25": 1.1, "league_p75": 2.0, "team_count": 18, "rank": 3,
        "vs_median_delta": 0.7, "metric_value_prev_season": 1.9,
    })
    assert m == {
        "metric_key": "goals_per_match", "metric_value": 2.2, "metric_value_prev_season": 1.9,
        "rank": 3, "team_count": 18,
        "league_median": 1.5, "league_p25": 1.1, "league_p75": 2.0, "vs_median_delta": 0.7,
    }
    # internal keys + league_mean (unbound by the screen) are not carried
    for k in ("team_benchmark_sk", "team_sk", "season_sk", "league_sk", "league_mean"):
        assert k not in m


def test_shape_team_payload_attaches_benchmarks_per_season_flat_and_ordered():
    rows = [
        {"team_sk": 157, "season_api_year": 2024, "league_code": "BL1",
         "team_name": "Bayern", "team_country": "Germany", "team_logo_url": "u"},
        {"team_sk": 157, "season_api_year": 2025, "league_code": "BL1",
         "team_name": "Bayern München", "team_country": "Germany", "team_logo_url": "u2"},
    ]

    def bench(metric, value, *, season=2025):
        return {"team_sk": 157, "league_code": "BL1", "season_api_year": season,
                "metric_key": metric, "metric_value": value, "rank": 1, "team_count": 18,
                "league_median": 1.0, "league_p25": 0.5, "league_p75": 1.5, "vs_median_delta": 0.2}

    # deliberately out of metric_key order; one row on the other season
    benchmark = [bench("shots_per_match", 14.1), bench("goals_per_match", 2.2),
                 bench("goals_against_per_match", 0.8, season=2024)]
    p = shape_team_payload(_mark_featured(rows), None, None, benchmark)
    s2025 = p["seasons"][0]
    assert s2025["season_api_year"] == 2025
    # flat metrics list (no position nesting), byte-stable by metric_key
    assert [m["metric_key"] for m in s2025["benchmarks"]] == ["goals_per_match", "shots_per_match"]
    # rows are routed to the right season by (league_code, season_api_year)
    s2024 = p["seasons"][1]
    assert [m["metric_key"] for m in s2024["benchmarks"]] == ["goals_against_per_match"]


def test_shape_team_payload_benchmarks_default_empty_without_rows():
    rows = [{"team_sk": 9, "season_api_year": 2025, "league_code": "PL",
             "team_name": "Arsenal", "team_country": "England", "team_logo_url": "u"}]
    p = shape_team_payload(_mark_featured(rows))
    assert p["seasons"][0]["benchmarks"] == []


def _player_profile(**kw):
    return {"player_sk": 184, "player_name": "H. Kane", "player_full_name": "Harry Edward Kane",
            "player_age": 33, "player_nationality": "England", "player_height": "188 cm",
            "player_photo_url": "p.png", "position_group": "ATT", "has_club_tab": True,
            "has_national_team_tab": True, "national_team_sk": 10, "current_club_team_sk": 157,
            "season_label": "2026/27", **kw}


_PLAYER_TEAMS = {157: {"team_id": 157, "name": "Bayern München", "crest": "b.png", "slug": "bayern-munchen"},
                 10: {"team_id": 10, "name": "England", "crest": "e.png", "slug": "england"}}


def _player_match(fixture_sk, kickoff, page_tab="club", **kw):
    return {"player_sk": 184, "fixture_sk": fixture_sk, "page_tab": page_tab, "league_code": "BL1",
            "kickoff_datetime": kickoff, "is_home": True, "goals_for": 2, "goals_against": 1,
            "result": "W", "opponent_name": "Mainz", "opponent_logo_url": "m.png",
            "minutes_played": 90, "goals_total": 1, "goals_assists": 0, "ball_actions_player": 40,
            "match_involvement": "played", **kw}


def _shape_player(profile=None, windows=(), benchmarks=(), squads=(), matches=(), next_rows=()):
    return shape_player_payload(profile or _player_profile(), list(windows), list(benchmarks),
                                list(squads), list(matches), list(next_rows), _PLAYER_TEAMS)


def test_player_payload_header_comes_from_the_profile_and_the_slug_from_the_board_name():
    p = _shape_player()
    assert p["slug"] == player_slug_with_id("H. Kane", 184)
    assert p["name"] == "Harry Edward Kane"
    assert p["club"]["slug"] == "bayern-munchen"
    assert [t["tab"] for t in p["tabs"]] == ["club", "national_team"]
    assert p["tabs"][1]["team"]["name"] == "England"


def test_player_payload_carries_only_the_tabs_the_data_marks():
    p = _shape_player(_player_profile(has_club_tab=False, current_club_team_sk=None))
    assert p["club"] is None
    assert [t["tab"] for t in p["tabs"]] == ["national_team"]
    assert [t["tab"] for t in _shape_player(_player_profile(has_national_team_tab=False))["tabs"]] == ["club"]


def test_player_cards_keep_a_blank_and_stay_on_their_tab():
    windows = [
        {"page_tab": "club", "metric_key": "appearances", "is_card": True, "metric_value": 12.0},
        {"page_tab": "club", "metric_key": "goals_player", "is_card": True, "metric_value": None},
        {"page_tab": "national_team", "metric_key": "appearances", "is_card": True, "metric_value": 3.0},
    ]
    club, nation = _shape_player(windows=windows)["tabs"]
    assert club["cards"] == {"appearances": 12.0, "goals_player": None}
    assert nation["cards"] == {"appearances": 3.0}


def test_player_last_season_is_absent_without_last_season_minutes_and_on_the_national_tab():
    row = {"page_tab": "club", "metric_key": "goals_per90", "is_comparison": True, "minutes": 982,
           "metric_value": 0.9, "minutes_prev_season": 3958, "metric_value_prev_season": 1.1}
    club, nation = _shape_player(windows=[row])["tabs"]
    assert club["last_season"] == {"minutes": 982, "minutes_prev": 3958, "metrics": [
        {"metric_key": "goals_per90", "value": 0.9, "value_prev": 1.1}]}
    assert nation["last_season"] is None
    gone = _shape_player(windows=[{**row, "minutes_prev_season": None}])["tabs"][0]
    assert gone["last_season"] is None


def test_player_competition_filters_follow_the_marts_order_and_show_the_best_first_rank():
    def row(order, league, key, **kw):
        return {"page_tab": "club", "competition_order": order, "league_code": league,
                "season_api_year": 2026, "season_label": "2026/27", "position_group": "ATT",
                "position_player_count": 35, "metric_key": key, "metric_value": 0.5,
                "rank_best_first": 3, "peer_median": 0.3, **kw}
    club = _shape_player(benchmarks=[row(2, "UCL", "goals_per90"), row(1, "BL1", "passes_per90"),
                                     row(1, "BL1", "fouls_per90", rank_best_first=1)])["tabs"][0]
    assert [c["league_code"] for c in club["competitions"]] == ["BL1", "UCL"]
    first = club["competitions"][0]
    assert first["player_count"] == 35 and first["season_label"] == "2026/27"
    assert first["metrics"][0] == {"metric_key": "fouls_per90", "value": 0.5, "rank": 1, "median": 0.3}


def test_player_squad_filter_leaves_the_player_out_of_the_dots_and_is_absent_without_a_squad():
    def row(player, value, rank):
        return {"page_tab": "club", "team_sk": 157, "player_sk": player, "metric_key": "goals_per90",
                "metric_value": value, "squad_player_count": 3, "squad_median": 0.4, "rank": rank}
    club, nation = _shape_player(squads=[row(184, 0.9, 1), row(2, 0.4, 2), row(3, 0.1, 3)])["tabs"]
    assert club["squad"]["team"]["name"] == "Bayern München" and club["squad"]["player_count"] == 3
    assert club["squad"]["metrics"] == [{"metric_key": "goals_per90", "value": 0.9, "rank": 1,
                                         "median": 0.4, "others": [0.1, 0.4]}]
    assert nation["squad"] is None


def test_player_recent_matches_are_latest_first_and_played_only():
    matches = [_player_match(1, "2026-09-01"), _player_match(2, "2026-10-01"),
               _player_match(3, "2026-11-01", match_involvement="on_bench"),
               _player_match(4, "2026-11-02", match_involvement=None)]
    club = _shape_player(matches=matches)["tabs"][0]
    assert [m["played_fixture_sk"] for m in club["recent_matches"]] == [2, 1]
    assert club["recent_matches"][0]["home_away"] == "home"
    assert club["recent_matches"][0]["ball_actions"] == 40
    assert club["recent_matches"][0]["on_bench"] is False


def test_a_national_squad_member_with_no_minutes_lists_the_bench_and_a_club_player_does_not():
    bench = {"minutes_played": None, "match_involvement": "on_bench"}
    matches = [_player_match(1, "2026-09-01", "national_team", **bench),
               _player_match(2, "2026-10-01", "national_team", match_involvement=None),
               _player_match(4, "2026-10-03", "club", **bench)]
    club, nation = _shape_player(matches=matches)["tabs"]
    assert [m["played_fixture_sk"] for m in nation["recent_matches"]] == [1]
    assert nation["recent_matches"][0]["on_bench"] is True
    assert club["recent_matches"] == []


def test_player_next_matches_are_the_tabs_own_team_in_the_marts_order():
    def row(team, fixture, order):
        return {"team_sk": team, "fixture_sk": fixture, "league_code": "BL1", "upcoming_rank": 1,
                "upcoming_order": order, "kickoff_datetime": "2026-11-07"}
    club, nation = _shape_player(next_rows=[row(157, 2, 2), row(157, 1, 1), row(10, 3, 1)])["tabs"]
    assert [m["fixture_id"] for m in club["next_matches"]] == [1, 2]
    assert [m["fixture_id"] for m in nation["next_matches"]] == [3]


def test_player_peers_make_one_sorted_file_per_competition_season_and_position():
    rows = [{"league_code": "BL1", "season_api_year": 2026, "position_group": "ATT",
             "metric_key": "goals_per90", "metric_value": v} for v in (0.9, 0.1)]
    rows.append({"league_code": "BL1", "season_api_year": 2026, "position_group": "MID",
                 "metric_key": "goals_per90", "metric_value": 0.2})
    att, mid = shape_player_peers(rows)
    assert (att["league_code"], att["season"], att["position_group"]) == ("BL1", 2026, "ATT")
    assert att["values"] == {"goals_per90": [0.1, 0.9]}
    assert mid["values"] == {"goals_per90": [0.2]}


def test_board_players_are_those_of_the_home_and_competition_boards(tmp_path):
    (tmp_path / "landing.json").write_text(json.dumps(
        {"top_players": [{"rows": [{"player_id": 3}, {"player_id": None}]}]}), encoding="utf-8")
    comp = tmp_path / "competitions" / "BL1"
    comp.mkdir(parents=True)
    (comp / "2026.json").write_text(json.dumps(
        {"player_boards": [{"rows": [{"player_id": 3}, {"player_id": 1}]}]}), encoding="utf-8")
    assert export_site_data.linked_player_ids(tmp_path) == [1, 3]
    assert export_site_data.linked_player_ids(tmp_path / "empty") == []


def test_player_metric_rows_hold_the_seven_key_metrics_in_catalogue_order():
    rows = export_site_data.fetch_player_metric_rows()["rows"]
    assert [r["metric_id"] for r in rows if r["is_key_metric"]] == [
        "scorer_points_per90", "shots_on_goal_per90", "passes_per90", "ball_actions_per90",
        "passes_key_per90", "duels_won_per90", "defensive_actions_per90"]
    fouls = next(r for r in rows if r["metric_id"] == "fouls_per90")
    assert fouls["direction"] == "lower_better"


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
    assert m["source_counts"] == {}, "no source count recorded when none was measured"


def test_build_manifest_records_what_the_warehouse_held():
    """The build compares its pages to this count, not to files written, since a sampled export writes fewer."""
    m = build_manifest([], {"fixtures_unplayed": 4321})
    assert m["source_counts"] == {"fixtures_unplayed": 4321}


def test_competitions_index_maps_every_served_competition_to_its_slug_and_name(monkeypatch):
    # site_v2/src/data/competitions.json carries this; the fixture page resolves its URL from it.
    monkeypatch.setattr(export_site_data, "_warehouse_competitions", lambda client: [
        {"league_code": "BL1", "name": "Bundesliga", "slug": "bundesliga", "confederation": "UEFA"},
        {"league_code": "PL", "name": "Premier League", "slug": "premier-league",
         "confederation": "UEFA"},
    ])
    assert _competitions_index(object()) == {
        "BL1": {"name": "Bundesliga", "slug": "bundesliga"},
        "PL": {"name": "Premier League", "slug": "premier-league"},
    }


def test_shape_competition_index_projects_the_keep_list_and_changes_nothing():
    # The mart resolves labels and ordering, so this only projects to the columns the page renders.
    # WC is listed first although alphabetical and region_rank sorts would both put PL first, so
    # only preserved input order passes.
    rows = [
        {
            "league_code": "WC", "competition_type": "world_championship", "entity_type": "national",
            "slug": "fifa-world-cup", "category_label_en": "World Cup",
            "category_label_i18n_key": "compTypeWorldChampionship", "confederation": "FIFA",
            "region_rank": 2, "competition_name": "FIFA World Cup 2026", "logo_url": None,
            "next_kickoff_datetime": None, "last_kickoff_datetime": "2026-06-14T18:00:00+00:00",
            "region_label_en": "World", "region_label_i18n_key": "confedFifa",
        },
        {
            "league_code": "PL", "competition_type": "domestic_league", "entity_type": "club",
            "slug": "premier-league", "category_label_en": "Domestic leagues",
            "category_label_i18n_key": "compTypeDomesticLeague", "confederation": "UEFA",
            "region_rank": 1, "competition_name": "Premier League",
            "logo_url": "https://example.test/pl.png",
            "next_kickoff_datetime": "2026-08-22T19:00:00+00:00", "last_kickoff_datetime": None,
            "region_label_en": "England", "region_label_i18n_key": None,
            "some_column_the_page_does_not_render": "must be dropped",
        },
    ]
    shaped = shape_competition_index(rows)
    assert [c["league_code"] for c in shaped] == ["WC", "PL"]   # input order

    wc = shaped[0]
    assert wc["region_label_en"] == "World"             # the confederation-region case
    assert wc["region_label_i18n_key"] == "confedFifa"
    assert wc["logo_url"] is None                       # nulls preserved, never coerced

    pl = shaped[1]
    assert "some_column_the_page_does_not_render" not in pl   # projected, not passed through raw
    assert pl["region_label_en"] == "England"          # the domestic-country case
    assert pl["region_label_i18n_key"] is None          # a country name is not chrome


def _team_index_row(**over) -> dict:
    row = {
        "team_sk": "x", "team_name": "A", "team_slug": "a", "team_logo_url": "https://x/a.png",
        "team_country": "Spain", "entity_type": "club", "region_key": "UEFA", "region_rank": 1,
        "region_label_i18n_key": "confedUefa", "country_region_key": "UEFA", "country_order": 2,
        "league_code": "PD", "league_tier": 1,
        "team_order_in_country": 3, "top_club_rank": 1, "national_team_rank": None,
        "national_team_region_rank": None, "national_teams_first": False,
    }
    return {**row, **over}


def test_shape_team_index_projects_in_input_order_and_lifts_the_page_flag():
    # The export orders by team name, which is the order of teams sharing a place; a page that
    # re-sorted by name or rank here would change it.
    rows = [_team_index_row(team_name="Zeta", top_club_rank=2),
            _team_index_row(team_name="Alpha", top_club_rank=1, team_logo_url=None)]
    shaped = shape_team_index(rows)
    assert shaped["type"] == "teams_index"
    assert shaped["national_teams_first"] is False
    assert [t["team_name"] for t in shaped["teams"]] == ["Zeta", "Alpha"]
    zeta, alpha = shaped["teams"]
    assert zeta["crest"] == "https://x/a.png" and alpha["crest"] is None
    for dropped in ("team_logo_url", "team_sk", "league_tier", "national_teams_first"):
        assert dropped not in zeta
    assert zeta["region_rank"] == 1 and zeta["country_order"] == 2


def test_fetch_team_index_orders_by_name_and_reads_the_mart_alone(monkeypatch):
    # The name order is the order of teams sharing a place; the mart serves the region rank and
    # label key that order and name the region groups.
    seen = []

    def fake_query(client, sql):
        seen.append(" ".join(sql.split()))
        return [_team_index_row()]

    monkeypatch.setattr(export_site_data, "_query", fake_query)
    payload = export_site_data.fetch_team_index(object())
    (sql,) = seen
    assert payload["type"] == "teams_index"
    assert "marts.mart_team_index`" in sql and "join" not in sql
    assert sql.endswith("order by team_name, team_slug")


def test_shape_team_index_refuses_rows_that_disagree_on_the_page_flag():
    with pytest.raises(ValueError, match="national_teams_first"):
        shape_team_index([_team_index_row(), _team_index_row(national_teams_first=True)])


def _player_index_row(**over) -> dict:
    row = {
        "player_sk": 184, "player_name": "Harry Kane", "player_photo_url": "https://x/184.png",
        "position_group": "ATT", "player_nationality": "England", "region_key": "UEFA",
        "nation_order": 4, "order_in_nation": 1, "current_club_name": "Bayern München",
        "award": None, "award_edition_year": None, "worlds_best_list": None, "worlds_best_order": None,
    }
    return {**row, **over}


def test_shape_player_index_keeps_the_served_order_and_lists_the_nominees():
    rows = [_player_index_row(player_sk=2, player_name="B Two", nation_order=1, award="yashin_trophy",
                              award_edition_year=2026, worlds_best_list="GK", worlds_best_order=1),
            _player_index_row(player_sk=1, player_name="A One", nation_order=2, award="ballon_dor",
                              award_edition_year=2026, worlds_best_list="ATT", worlds_best_order=2),
            _player_index_row(player_sk=3, player_name="C Three", nation_order=2, order_in_nation=2,
                              award="ballon_dor", award_edition_year=2026, worlds_best_list="ATT",
                              worlds_best_order=1),
            _player_index_row(player_sk=4, player_nationality=None, region_key=None, nation_order=3,
                              current_club_name=None)]
    shaped = shape_player_index(rows)
    assert shaped["type"] == "players_index"
    assert [p["player_id"] for p in shaped["players"]] == [2, 1, 3, 4]
    assert [(w["list"], w["order"], w["player_id"]) for w in shaped["worlds_best"]] == [
        ("ATT", 1, 3), ("ATT", 2, 1), ("GK", 1, 2)]
    assert shaped["worlds_best"][2] == {"player_id": 2, "list": "GK", "award": "yashin_trophy",
                                        "edition_year": 2026, "order": 1}
    first = shaped["players"][0]
    assert first == {"player_id": 2, "slug": player_slug_with_id("B Two", 2), "name": "B Two",
                     "photo": "https://x/184.png", "position_group": "ATT", "nation": "England",
                     "region_key": "UEFA", "nation_order": 1, "order_in_nation": 1,
                     "club": "Bayern München"}
    last = shaped["players"][3]
    assert last["nation"] is None and last["region_key"] is None and last["club"] is None


def test_fetch_player_index_reads_the_mart_alone_in_the_served_order(monkeypatch):
    seen = []

    def fake_query(client, sql):
        seen.append(" ".join(sql.split()))
        return [_player_index_row()]

    monkeypatch.setattr(export_site_data, "_query", fake_query)
    payload = export_site_data.fetch_player_index(object())
    (sql,) = seen
    assert payload["type"] == "players_index" and len(payload["players"]) == 1
    assert "marts.mart_player_index`" in sql and "join" not in sql
    assert sql.endswith("order by nation_order, order_in_nation")
    selected = {c.strip() for c in sql.split(" from ")[0].removeprefix("select ").split(",")}
    assert selected == set(_player_index_row())


def test_featured_season_row_refuses_to_choose():
    """With no served flag the export must fail loudly rather than fall back to recency."""
    import pytest

    with pytest.raises(ValueError):
        _featured_season_row([{"season_api_year": 2026}, {"season_api_year": 2025}])
    with pytest.raises(ValueError):
        _featured_season_row([
            {"season_api_year": 2026, "is_featured_season": True},
            {"season_api_year": 2025, "is_featured_season": True},
        ])


# ------------------------------------------------------------------------------------------
# The landing hero's matchday selection.


def _hero_fixtures(*specs):
    """(league_code, kickoff) pairs -> mart_competition_fixtures rows, in the order supplied."""
    return [
        {"fixture_sk": i, "league_code": lc, "season_api_year": 2026,
         "kickoff_datetime": ko, "round_name": "R1", "fixture_order": i,
         "status_short": "NS", "is_played": False,
         "home_team_sk": 1, "home_team_name": "Home", "home_team_slug": "home",
         "away_team_sk": 2, "away_team_name": "Away", "away_team_slug": "away"}
        for i, (lc, ko) in enumerate(specs, start=1)
    ]


def test_hero_grouping_truncates_nothing():
    """This function groups everything it is handed: thirteen matches in, thirteen out."""
    thirteen = [("PL", f"2026-08-20 1{i % 10}:00:00+00:00") for i in range(13)]
    groups = group_upcoming_fixtures(
        _hero_fixtures(*thirteen),
        {"PL": {"name": "Premier League", "slug": "premier-league"}},
    )
    assert [g["league_code"] for g in groups] == ["PL"]
    assert len(groups[0]["fixtures"]) == 13, "every match handed in"


def test_hero_carries_no_ordering_key():
    """Competitions arrive in the served order, so a group carries nothing to sort by."""
    groups = group_upcoming_fixtures(
        _hero_fixtures(("PL", "2026-08-20 19:00:00+00:00")),
        {"PL": {"name": "Premier League", "slug": "premier-league", "region_rank": 1}},
    )
    assert "region_rank" not in groups[0]


_BOARDS = export_site_data._in_catalogue_order(export_site_data._MATCH_PLAYER_BOARDS, "player")
_CATALOGUE = export_site_data._board_catalogue(export_site_data._MATCH_PLAYER_BOARDS, "player")


def _played_row(fid, **over):
    row = {"fixture_sk": fid, "league_code": "DFBP", "season_api_year": 2026,
           "kickoff_datetime": "2026-08-22T13:30:00Z", "round_name": "Round of 64", "round_order": None,
           "status_short": "PEN", "venue_name": "Sportpark", "fixture_slug": f"slug-{fid}",
           "goals_home": 1, "goals_away": 1, "shootout_home": 4, "shootout_away": 5,
           "winner_team_sk": 2, "award_kind": None, "awarded_to_team_sk": None, "on_pitch_home": None,
           "on_pitch_away": None,
           "goal_data_state": "goals", "lineup_state": "confirmed",
           "goals": [
               {"side": "away", "player_api_id": 70, "player_name": "P. Scobel", "minute_elapsed": 56,
                "minute_extra": None, "goals": 1, "penalties": 0, "is_own_goal": False,
                "assist_player_api_id": 71, "assist_player_name": "A. Markhiev",
                "score_home_after": 0, "score_away_after": 1},
               {"side": "home", "player_api_id": 80, "player_name": "M. Sponsel", "minute_elapsed": 90,
                "minute_extra": 6, "goals": 1, "penalties": 0, "is_own_goal": False,
                "assist_player_api_id": None, "assist_player_name": None,
                "score_home_after": 1, "score_away_after": 1},
           ],
           "home_team_sk": 1, "home_team_name": "Köln", "home_team_slug": "koln", "home_team_logo_url": "c1",
           "home_team_formation": "4-4-2",
           "away_team_sk": 2, "away_team_name": "Nürnberg", "away_team_slug": "nurnberg",
           "away_team_logo_url": "c2", "away_team_formation": None}
    row.update(over)
    return row


def _leader(fid, key, order, player, rank=None):
    return {"fixture_sk": fid, "metric_key": key, "rank": rank or order, "match_leader_order": order,
            "sort_value": 10 - order, "player_sk": player, "player_name": f"Player {player}",
            "team_sk": 1, "team_name": "Köln", "team_slug": "koln", "team_logo_url": "c1"}


def _sheet(fid, team, player, order, starter=True, on=None, replaced=None, minutes=90):
    return {"fixture_sk": fid, "team_sk": team, "player_sk": player, "player_name": f"Player {player}",
            "player_photo_url": None, "position_code": "M", "is_starter": starter,
            "minute_on": on, "minute_on_extra": None, "minute_off": None, "minute_off_extra": None,
            "replaced_player_sk": replaced, "minutes_played": minutes, "lineup_order": order}


def test_shape_played_fixture_payload_copies_the_served_result_and_goals():
    p = export_site_data.shape_played_fixture_payload(
        _played_row(9), "DFB-Pokal", [], [], [], {}, _CATALOGUE, _BOARDS)
    assert p["type"] == "fixture" and p["is_played"] is True and p["is_next_round"] is False
    assert p["slug"] == "slug-9" and p["league_name"] == "DFB-Pokal" and p["venue"] == "Sportpark"
    assert p["result"] == {"goals_home": 1, "goals_away": 1, "shootout_home": 4, "shootout_away": 5,
                           "winner_team_id": 2, "award_kind": None, "awarded_to_team_id": None,
                           "on_pitch_home": None, "on_pitch_away": None}, \
        "the served result, no score worked out here"
    first, second = p["goals"]
    assert (first["score_home_after"], first["score_away_after"]) == (0, 1), "the served running score"
    assert first["player_id"] == 70 and "player_slug" not in first, "no page address is built here"
    assert second["minute"] == 90 and second["minute_extra"] == 6 and second["assist_player_name"] is None
    assert p["home"]["formation"] == "4-4-2" and p["away"]["formation"] is None
    assert p["home"]["match_stats"] is None and p["home"]["has_team_stats"] is False


def test_shape_match_leaders_keeps_the_catalogue_order_and_the_served_rows():
    rows = [_leader(9, "fouls_player", 1, 5), _leader(9, "shots_player", 2, 4, rank=1),
            _leader(9, "shots_player", 1, 3)]
    boards = export_site_data.shape_match_leaders(rows, _CATALOGUE, _BOARDS)
    assert [b["metric_key"] for b in boards] == ["shots_player", "fouls_player"], \
        "the catalogue's order; a board without a row is left out"
    assert [r["player_id"] for r in boards[0]["rows"]] == [3, 4], "the served match_leader_order"
    assert [r["rank"] for r in boards[0]["rows"]] == [1, 1], "a shared count keeps its served rank"
    assert boards[0]["label_i18n_key"] == "playerMetrics.shots.label"
    assert "slug" not in boards[0]["rows"][0], "no page address is built here"


def test_shape_match_leaders_refuses_a_board_it_does_not_list():
    import pytest

    with pytest.raises(KeyError):
        export_site_data.shape_match_leaders([_leader(9, "goals_player", 1, 3)], _CATALOGUE, _BOARDS)


def test_shape_lineup_lists_the_starters_then_the_substitutes_who_came_on():
    rows = [_sheet(9, 1, 12, 13, starter=False), _sheet(9, 1, 11, 12, starter=False, on=73, replaced=1),
            _sheet(9, 1, 1, 1)]
    sheet = export_site_data.shape_lineup(rows)
    assert [r["player_id"] for r in sheet] == [1, 11], "served order; a substitute who stayed on the bench is left out"
    assert sheet[1]["replaced_player_name"] == "Player 1" and sheet[1]["minute_on"] == 73
    assert sheet[0]["minutes"] == 90 and sheet[0]["player_id"] == 1 and "slug" not in sheet[0]


def test_played_payloads_walk_each_mart_once_in_fixture_order(monkeypatch):
    """Every mart is read once and each match's rows reach that match only."""
    streamed: list[str] = []
    stats = [{"fixture_sk": 5, "team_sk": 1, "is_home": True, "games_with_team_stats": 1,
              "games_with_player_stats": 0, "shots_per_match": 9},
             {"fixture_sk": 9, "team_sk": 2, "is_home": False, "games_with_team_stats": 1,
              "games_with_player_stats": 1, "shots_per_match": 14}]
    leaders = [_leader(9, "shots_player", 1, 3)]
    lineups = [_sheet(5, 1, 1, 1), _sheet(9, 2, 7, 1)]

    def fake_stream(client, sql):
        streamed.append(sql)
        if "mart_team_window_metrics" in sql:
            return iter(stats)
        if "mart_leaderboards" in sql:
            return iter(leaders)
        if "mart_player_fixture_stats" in sql:
            return iter(lineups)
        return iter([_played_row(5, goals=[]), _played_row(7, goals=[]), _played_row(9)])

    def fake_query(client, sql):
        if "count(*)" in sql:
            return [{"n": 3}]
        if "core.dim_league" in sql:
            return [{"league_code": "DFBP", "league_name": "DFB-Pokal"}]
        return []

    monkeypatch.setattr(export_site_data, "_stream", fake_stream)
    monkeypatch.setattr(export_site_data, "_query", fake_query)
    counts: dict = {}
    payloads = list(export_site_data.fetch_played_fixture_payloads(object(), source_counts=counts))

    assert counts == {"fixtures_played": 3}
    assert len(streamed) == 4 and all("order by fixture_sk" in s for s in streamed)
    assert [p["fixture_id"] for p in payloads] == [5, 7, 9]
    five, seven, nine = payloads
    assert five["home"]["has_team_stats"] is True and five["home"]["has_player_stats"] is False
    assert five["home"]["match_stats"] == {"games_with_team_stats": 1, "games_with_player_stats": 0,
                                           "shots_per_match": 9}
    assert seven["leaders"] == [] and seven["home"]["lineup"] == [] and seven["away"]["match_stats"] is None
    assert [b["metric_key"] for b in nine["leaders"]] == ["shots_player"]
    assert [r["player_id"] for r in nine["away"]["lineup"]] == [7] and nine["home"]["lineup"] == []


def test_played_payloads_take_the_listed_matches_only(monkeypatch):
    streamed: list[str] = []
    monkeypatch.setattr(export_site_data, "_stream", lambda client, sql: streamed.append(sql) or iter([]))
    monkeypatch.setattr(export_site_data, "_query", lambda client, sql: [])
    assert list(export_site_data.fetch_played_fixture_payloads(object(), fixture_ids=(11, 12))) == []
    assert all("fixture_sk in (11, 12)" in s for s in streamed)
