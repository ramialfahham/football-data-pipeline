"""Every surface shows its metrics in the catalogue's order and only filters.

The catalogue's `metric_order` is a metric's place in its group; `metric_group_order` places the
group. The export's board lists say which boards a surface shows, and `_in_catalogue_order` puts
them in the catalogue's order. These tests fail when a shown metric has no place, or when a payload
leaves the catalogue's order.
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CATALOGUE = REPO / "dbt_project" / "seeds" / "metric_catalogue.csv"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import export_site_data as export  # noqa: E402

SURFACES = {
    "Rankings team": (export._COMPETITION_TEAM_BOARDS, "team"),
    "Rankings player": (export._COMPETITION_PLAYER_BOARDS, "player"),
    "Home team": (export._HOME_TEAM_BOARDS, "team"),
    "Home player": (export._HOME_PLAYER_BOARDS, "player"),
}


def _catalogue(entity: str) -> dict[str, dict[str, str]]:
    with CATALOGUE.open(newline="", encoding="utf-8") as f:
        return {r["metric_id"]: r for r in csv.DictReader(f) if r["entity"] == entity}


def _place(row: dict[str, str]) -> tuple[int, int]:
    return int(row["metric_group_order"]), int(row["metric_order"])


def test_every_metric_a_surface_shows_has_a_place_in_its_group():
    missing = {name: [m for m in boards if not _catalogue(entity)[m]["metric_order"]]
               for name, (boards, entity) in SURFACES.items()}
    assert {k: v for k, v in missing.items() if v} == {}
    form = [r["metric_id"] for r in export.fetch_metric_rows()["rows"]]
    team = _catalogue("team")
    assert all(team[m]["metric_order"] for m in form), "a Form comparison row without a place"


def test_each_surface_is_served_in_the_catalogue_order():
    for name, (boards, entity) in SURFACES.items():
        cat = _catalogue(entity)
        served = export._in_catalogue_order(boards, entity)
        assert sorted(served) == sorted(boards), f"{name}: the order filters nothing out or in"
        assert [_place(cat[m]) for m in served] == sorted(_place(cat[m]) for m in served), name


def test_the_passing_player_boards_read_passes_pass_accuracy_key_passes():
    served = export._in_catalogue_order(export._COMPETITION_PLAYER_BOARDS, "player")
    passing = [m for m in served if _catalogue("player")[m]["metric_group"] == "passing"]
    assert passing == ["passes_player", "passes_accuracy_player_pct", "passes_key_player"]


def test_the_rankings_payload_keeps_the_order_it_is_given():
    order = export._in_catalogue_order(export._COMPETITION_PLAYER_BOARDS, "player")
    catalogue = export._board_catalogue(export._COMPETITION_PLAYER_BOARDS, "player")
    rows = [{"metric_key": m, "league_leader_order": 1} for m in reversed(order)]
    boards = export.shape_competition_boards(rows, order, catalogue, "player")
    assert [b["metric_key"] for b in boards] == list(order)


def _board_row(key: str, entity: str) -> dict:
    row = {"league_code": "BL1", "season_api_year": 2026, "metric_key": key, "rank": 1,
           "rank_order": "desc", "sort_value": 1.0, "team_sk": 1, "team_name": "T1",
           "team_slug": "t1", "team_logo_url": "c1"}
    if entity == "player":
        row.update({"player_sk": 9, "player_name": "P9"})
    return row


def _fixture_row() -> dict:
    return {"fixture_sk": 7, "league_code": "BL1", "season_api_year": 2026, "round_name": "Regular Season - 1",
            "round_order": 1, "round_sequence": 1, "fixture_order": 1, "kickoff_datetime": "2026-08-28T18:30:00Z",
            "status_short": "NS", "is_played": False, "goals_home": None, "goals_away": None,
            "home_team_sk": 1, "home_team_name": "T1", "home_team_slug": "t1", "home_team_logo_url": "c1",
            "away_team_sk": 2, "away_team_name": "T2", "away_team_slug": "t2", "away_team_logo_url": "c2",
            "fixture_slug": "slug-7", "is_next_round": True, "is_match_that_matters": False}


def test_the_fetched_rankings_and_leaderboards_follow_the_catalogue(monkeypatch):
    """The warehouse serves the boards in the board lists' own order; the payloads carry the
    catalogue's."""
    def fake_query(client, sql):
        if "mart_team_leaderboards" in sql:
            return [_board_row(k, "team") for k in export._COMPETITION_TEAM_BOARDS]
        if "mart_leaderboards" in sql:
            return [_board_row(k, "player") for k in export._COMPETITION_PLAYER_BOARDS]
        if "mart_competition_fixtures" in sql:
            return [_fixture_row()]
        return []

    monkeypatch.setattr(export, "_query", fake_query)
    monkeypatch.setattr(export, "_warehouse_competition_meta", lambda client: {})
    monkeypatch.setattr(export, "_competition_page_meta", lambda client: {})
    (payload,) = export.fetch_competition_payloads(object())
    for key, (boards, entity) in (("team_boards", SURFACES["Rankings team"]),
                                  ("player_boards", SURFACES["Rankings player"])):
        assert [b["metric_key"] for b in payload[key]] == list(export._in_catalogue_order(boards, entity)), key
    (lb,) = export.fetch_leaderboard_payloads(object())
    assert list(lb["boards"]) == list(export._in_catalogue_order(export._LEADERBOARD_METRICS, "player"))


def test_a_board_without_a_place_fails_the_export():
    try:
        export._in_catalogue_order(("goals_penalty_player",), "player")
    except KeyError as e:
        assert "goals_penalty_player" in str(e)
    else:
        raise AssertionError("a shown board without a catalogue order must fail")
