"""The Statistics pages' payload: the full ranked field of every board of the Players and Teams tabs."""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import export_site_data as export  # noqa: E402

PLAYER_TOTALS = {
    "goals_player", "assists_player", "scorer_points_player", "goals_penalty_player", "saves_player",
    "cards_yellow_player", "cards_red_player", "penalty_committed_player",
}
PLAYER_PERCENTAGES = {
    "shots_on_goal_player_pct", "finishing_efficiency_player_pct", "passes_accuracy_player_pct",
    "dribbles_success_player_pct", "duels_won_player_pct", "saves_player_pct", "contribution_player_pct",
}
TEAM_TOTALS = {"goals", "goals_against", "clean_sheets", "goals_penalty", "cards_yellow", "cards_red"}


def _catalogue(entity: str) -> dict[str, dict[str, str]]:
    path = REPO / export.CATALOGUE_SEED_PATH
    with path.open(newline="", encoding="utf-8") as f:
        return {r["metric_id"]: r for r in csv.DictReader(f) if r["entity"] == entity}


def test_the_player_boards_have_the_forms_the_design_lists():
    totals = {k for k in export._STATISTICS_PLAYER_BOARDS if k.endswith("_player")}
    per90 = {k for k in export._STATISTICS_PLAYER_BOARDS if k.endswith("_per90")}
    percentages = {k for k in export._STATISTICS_PLAYER_BOARDS if k.endswith("_pct")}
    assert totals == PLAYER_TOTALS
    assert percentages == PLAYER_PERCENTAGES
    assert len(per90) == 21
    assert {"goals_per90", "assists_per90", "scorer_points_per90", "saves_per90"} <= per90
    assert "goals_against_per90" in per90
    assert len(totals | per90 | percentages) == len(export._STATISTICS_PLAYER_BOARDS) == 36


def test_the_player_boards_leave_out_what_the_design_leaves_out():
    kept = set(export._STATISTICS_PLAYER_BOARDS)
    assert not kept & {
        "goals_open_play_player", "penalty_won_player", "dribbles_past_player", "dribbles_past_per90",
        "cards_player", "appearances", "minutes_per_appearance", "passes_player", "shots_player",
        "shots_on_goal_player", "duels_player", "dribbles_attempts_player", "defensive_actions_player",
    }


def test_the_team_boards_have_the_forms_the_design_lists():
    kept = set(export._STATISTICS_TEAM_BOARDS)
    assert {k for k in kept if not k.endswith(("_per_match", "_pct"))} == TEAM_TOTALS
    assert {"goals_per_match", "goals_against_per_match"} <= kept
    assert not kept & {
        "goals_open_play", "goals_own", "shots_off_target_per_match", "shots_blocked_per_match",
        "shots_share_pct", "free_kicks_per_match", "cards_yellow_per_match", "cards_red_per_match",
    }
    assert len(kept) == 38


def test_every_statistics_board_has_a_place_in_the_catalogue_and_the_payload_follows_it():
    for entity, boards in (("player", export._STATISTICS_PLAYER_BOARDS), ("team", export._STATISTICS_TEAM_BOARDS)):
        cat = _catalogue(entity)
        assert [k for k in boards if not cat[k]["metric_order"]] == []
        served = export._in_catalogue_order(boards, entity)
        assert sorted(served) == sorted(boards)
        places = [(int(cat[k]["metric_group_order"]), int(cat[k]["metric_order"])) for k in served]
        assert places == sorted(places)


def _player_row(key: str, rank: int, value: float, sk: int, name: str, club: str = "FC A", slug: str = "fc-a") -> dict:
    return {"metric_key": key, "rank_order": "desc", "rank": rank, "display_value": value, "player_sk": sk,
            "player_name": name, "team_name": club, "team_slug": slug, "team_logo_url": f"{slug}.png"}


def test_a_board_keeps_every_ranked_row_in_the_served_order_with_the_marts_rank_and_value():
    rows = [
        _player_row("goals_player", 1, 20, 1, "A"),
        _player_row("goals_player", 2, 15, 2, "B"),
        _player_row("goals_player", 2, 15, 3, "C"),
        _player_row("goals_player", 4, 9.5, 4, "D"),
    ] + [_player_row("goals_player", 5, 1, 100 + i, f"P{i}") for i in range(300)]
    boards, entities = export.shape_statistics_boards(
        rows, ("goals_player",), export._board_catalogue(("goals_player",), "player"), "player")
    (board,) = boards
    assert len(board["rows"]) == 304, "no cut: every ranked player stays"
    assert [r[0] for r in board["rows"][:4]] == [1, 2, 2, 4], "the rank is the mart's: ties share, the next is skipped"
    assert [r[1] for r in board["rows"][:4]] == [20, 15, 15, 9.5], "the shown value is the mart's display_value"
    assert [entities[r[2]]["name"] for r in board["rows"][:4]] == ["A", "B", "C", "D"]
    assert board["rank_order"] == "desc" and board["format"] == "integer" and board["metric_group"] == "goals"


def test_a_player_and_a_team_are_said_once_however_many_boards_they_stand_on():
    rows = [_player_row(k, 1, 3, 7, "Seven") for k in ("goals_player", "assists_player", "goals_penalty_player")]
    boards, entities = export.shape_statistics_boards(
        rows, ("goals_player", "assists_player", "goals_penalty_player"),
        export._board_catalogue(("goals_player", "assists_player", "goals_penalty_player"), "player"), "player")
    assert len(boards) == 3 and len(entities) == 1
    assert {b["rows"][0][2] for b in boards} == {0}
    assert entities[0]["club"] == "FC A" and entities[0]["club_slug"] == "fc-a" and entities[0]["crest"] == "fc-a.png"
    assert entities[0]["slug"] == export.player_slug_with_id("Seven", 7)


def test_a_player_on_two_clubs_in_one_competition_season_is_two_entities():
    rows = [_player_row("goals_player", 1, 5, 7, "Seven", "FC A", "fc-a"),
            _player_row("assists_player", 1, 5, 7, "Seven", "FC B", "fc-b")]
    _, entities = export.shape_statistics_boards(
        rows, ("goals_player", "assists_player"),
        export._board_catalogue(("goals_player", "assists_player"), "player"), "player")
    assert [e["club_slug"] for e in entities] == ["fc-a", "fc-b"]


def test_a_board_without_rows_and_a_row_of_an_unlisted_board_are_left_out():
    rows = [_player_row("goals_player", 1, 5, 1, "A"), _player_row("passes_player", 1, 500, 1, "A")]
    boards, _ = export.shape_statistics_boards(
        rows, ("goals_player", "assists_player"),
        export._board_catalogue(("goals_player", "assists_player"), "player"), "player")
    assert [b["metric_key"] for b in boards] == ["goals_player"]


def test_a_fewest_first_board_carries_the_direction_the_mart_served():
    row = {"metric_key": "goals_against_per_match", "rank_order": "asc", "rank": 1, "display_value": 0.5,
           "team_sk": 3, "team_name": "T", "team_slug": "t", "team_logo_url": "t.png"}
    boards, entities = export.shape_statistics_boards(
        [row], ("goals_against_per_match",), export._board_catalogue(("goals_against_per_match",), "team"), "team")
    assert boards[0]["rank_order"] == "asc" and boards[0]["per_match"] is True
    assert entities == [{"slug": "t", "name": "T", "crest": "t.png"}]


def test_a_zero_difference_row_the_mart_ranks_is_kept():
    rows = [{"metric_key": "shots_on_goal_difference_per_match", "rank_order": "desc", "rank": r, "display_value": v,
             "team_sk": r, "team_name": f"T{r}", "team_slug": f"t{r}", "team_logo_url": "c"}
            for r, v in ((1, 1.5), (2, 0.0), (3, -2.0))]
    boards, _ = export.shape_statistics_boards(
        rows, ("shots_on_goal_difference_per_match",),
        export._board_catalogue(("shots_on_goal_difference_per_match",), "team"), "team")
    assert [r[1] for r in boards[0]["rows"]] == [1.5, 0.0, -2.0]


def test_the_competitions_are_the_seeds_in_its_order_with_pl_first_and_the_nations_last():
    places = export._statistics_competitions()
    ordered = sorted(places, key=places.get)
    assert ordered[0] == "PL" and ordered[-1] == "CNL" and len(ordered) == 35
    assert sorted(places.values()) == list(range(1, 36))
    assert not set(ordered) & {"WCQEU", "WCQAF", "FAC", "COPA", "SUPERCUP"}


def _fake_client(monkeypatch, player_rows=(), team_rows=(), seen=None):
    def fake_query(client, sql):
        if seen is not None:
            seen.append(sql)
        if "mart_team_leaderboards" in sql:
            return list(team_rows)
        if "mart_leaderboards" in sql:
            return list(player_rows)
        if "mart_competition_fixtures" in sql:
            return [{"league_code": "PL", "season_api_year": 2026, "season_label": "2026/27"},
                    {"league_code": "WC", "season_api_year": 2026, "season_label": "2026"}]
        return []

    monkeypatch.setattr(export, "_query", fake_query)
    monkeypatch.setattr(export, "_warehouse_competitions", lambda c: [
        {"league_code": "PL", "name": "Premier League (registry)", "slug": "premier-league"},
        {"league_code": "WC", "name": "World Cup", "slug": "world-cup"}])
    monkeypatch.setattr(export, "_warehouse_competition_meta", lambda c: {"PL": {"name": "Premier League"}})
    monkeypatch.setattr(export, "_competition_page_meta", lambda c: {
        "PL": {"entity_type": "club"}, "WC": {"entity_type": "national"}})


def _season(lc: str, row: dict) -> dict:
    return {**row, "league_code": lc, "season_api_year": 2026}


def test_the_payloads_are_one_per_competition_in_dropdown_order_with_their_header_facts(monkeypatch):
    team = {"metric_key": "goals", "rank_order": "desc", "rank": 1, "display_value": 4, "team_sk": 1,
            "team_name": "T", "team_slug": "t", "team_logo_url": "t.png"}
    _fake_client(monkeypatch,
                 player_rows=[_season("WC", _player_row("goals_player", 1, 6, 1, "A"))],
                 team_rows=[_season("WC", team), _season("PL", team)])
    wc, pl = None, None
    payloads = export.fetch_statistics_payloads(object())
    assert [p["league_code"] for p in payloads] == ["PL", "WC"]
    pl, wc = payloads
    assert (pl["name"], pl["slug"], pl["entity_type"], pl["season"], pl["season_label"]) == (
        "Premier League", "premier-league", "club", 2026, "2026/27")
    assert pl["statistics_order"] == 1 and wc["statistics_order"] == 28
    assert pl["player_boards"] == [] and pl["players"] == []
    assert [b["metric_key"] for b in pl["team_boards"]] == ["goals"]
    assert wc["entity_type"] == "national" and wc["player_boards"][0]["rows"] == [[1, 6, 0]]


def test_the_fetched_boards_follow_the_catalogue_order_whatever_order_the_warehouse_serves(monkeypatch):
    player_rows = [_season("PL", _player_row(k, 1, 1, 1, "A")) for k in reversed(export._STATISTICS_PLAYER_BOARDS)]
    team_rows = [_season("PL", {"metric_key": k, "rank_order": "desc", "rank": 1, "display_value": 1, "team_sk": 1,
                                "team_name": "T", "team_slug": "t", "team_logo_url": "t.png"})
                 for k in reversed(export._STATISTICS_TEAM_BOARDS)]
    _fake_client(monkeypatch, player_rows=player_rows, team_rows=team_rows)
    (payload,) = export.fetch_statistics_payloads(object())
    assert [b["metric_key"] for b in payload["player_boards"]] == list(
        export._in_catalogue_order(export._STATISTICS_PLAYER_BOARDS, "player"))
    assert [b["metric_key"] for b in payload["team_boards"]] == list(
        export._in_catalogue_order(export._STATISTICS_TEAM_BOARDS, "team"))
    assert list(export._STATISTICS_PLAYER_BOARDS) != [b["metric_key"] for b in payload["player_boards"]], (
        "the tuple is not in catalogue order, so this test proves the sort")


def test_two_current_seasons_for_one_competition_fail_the_export(monkeypatch):
    team = {"metric_key": "goals", "rank_order": "desc", "rank": 1, "display_value": 4, "team_sk": 1,
            "team_name": "T", "team_slug": "t", "team_logo_url": "t.png"}
    _fake_client(monkeypatch,
                 player_rows=[_season("PL", _player_row("goals_player", 1, 6, 1, "A"))],
                 team_rows=[{**team, "league_code": "PL", "season_api_year": 2025}])
    try:
        export.fetch_statistics_payloads(object())
    except ValueError as e:
        assert "PL" in str(e)
    else:
        raise AssertionError("a league with two current seasons must fail the export")


def test_a_competition_whose_current_season_serves_no_board_has_no_payload(monkeypatch):
    _fake_client(monkeypatch)
    assert export.fetch_statistics_payloads(object()) == []


def test_the_reads_take_only_current_season_rows_of_the_dropdown_competitions_and_listed_boards(monkeypatch):
    seen: list[str] = []
    _fake_client(monkeypatch, seen=seen)
    export.fetch_statistics_payloads(object())
    reads = [s for s in seen if "mart_leaderboards" in s or "mart_team_leaderboards" in s]
    assert len(reads) == 2
    for sql in reads:
        assert "is_current_season" in sql and "league_code in ('" in sql
        assert "'PL'" in sql and "'WCQEU'" not in sql
    player_sql = next(s for s in reads if "mart_leaderboards" in s and "mart_team" not in s)
    assert "window_type = 'season_to_date'" in player_sql and "'goals_per90'" in player_sql
    assert "'passes_player'" not in player_sql


def test_the_sample_limit_keeps_the_first_competitions(monkeypatch):
    team = {"metric_key": "goals", "rank_order": "desc", "rank": 1, "display_value": 4, "team_sk": 1,
            "team_name": "T", "team_slug": "t", "team_logo_url": "t.png"}
    _fake_client(monkeypatch, team_rows=[_season("WC", team), _season("PL", team)])
    assert [p["league_code"] for p in export.fetch_statistics_payloads(object(), sample=1)] == ["PL"]
