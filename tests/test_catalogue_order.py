"""Every surface shows its metrics in the catalogue's `metric_group_order` then `metric_order`."""
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
    "Match leaders": (export._MATCH_PLAYER_BOARDS, "player"),
    "Players to watch": (export._MATCH_WATCH_BOARDS, "player"),
    "Statistics team": (export._STATISTICS_TEAM_BOARDS, "team"),
    "Statistics player": (export._STATISTICS_PLAYER_BOARDS, "player"),
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
    """The warehouse serves boards in the board lists' order; the payloads must use the catalogue's."""
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


def test_a_board_without_a_place_fails_the_export():
    try:
        export._in_catalogue_order(("goals_open_play_player",), "player")
    except KeyError as e:
        assert "goals_open_play_player" in str(e)
    else:
        raise AssertionError("a shown board without a catalogue order must fail")


PINNED_ORDER = {
    "player": {
        "goals": ["goals_player", "goals_per90", "assists_player", "assists_per90",
                  "scorer_points_player", "scorer_points_per90", "goals_penalty_player",
                  "contribution_player_pct"],
        "shooting": ["shots_player", "shots_per90", "shots_on_goal_player", "shots_on_goal_per90",
                     "shots_on_goal_player_pct", "finishing_efficiency_player_pct"],
        "passing": ["passes_player", "passes_per90", "passes_accurate_player", "passes_accurate_per90",
                    "passes_accuracy_player_pct", "passes_key_player", "passes_key_per90",
                    "ball_actions_player", "ball_actions_per90"],
        "one_on_one": ["dribbles_attempts_player", "dribbles_attempts_per90", "dribbles_success_player",
                       "dribbles_success_per90", "dribbles_success_player_pct", "duels_player", "duels_per90",
                       "duels_won_player", "duels_won_per90", "duels_won_player_pct"],
        "defending": ["defensive_actions_player", "defensive_actions_per90", "tackles_player", "tackles_per90",
                      "interceptions_player", "interceptions_per90", "blocks_player", "blocks_per90",
                      "dribbles_past_player", "dribbles_past_per90"],
        "goalkeeping": ["saves_player", "saves_per90", "saves_player_pct", "goals_against_player",
                        "goals_against_per90", "shots_on_goal_against_player"],
        "discipline": ["cards_yellow_player", "cards_red_player", "fouls_player", "fouls_per90",
                       "penalty_committed_player", "offsides_player", "offsides_per90"],
        "playing_time": ["appearances", "minutes_per_appearance"],
    },
    "team": {
        "goals": ["goals", "goals_per_match", "goals_against", "goals_against_per_match", "clean_sheets",
                  "clean_sheets_pct", "goals_open_play", "goals_penalty", "goals_own"],
        "shooting": ["shots_per_match", "shots_on_goal_per_match", "shots_on_goal_against_per_match",
                     "shots_on_goal_difference_per_match", "shots_inside_box", "shots_inside_box_per_match",
                     "shots_inside_box_pct", "shots_on_goal_pct", "finishing_efficiency_pct", "shots_share_pct",
                     "shots_off_target_per_match", "shots_blocked_per_match"],
        "passing": ["passes_per_match", "passes_accurate_per_match", "passes_accuracy_pct",
                    "passes_key_per_match", "passes_share_pct"],
        "one_on_one": ["dribbles_attempts_per_match", "dribbles_success_per_match", "dribbles_success_pct",
                       "duels_per_match", "duels_won_per_match", "duels_won_pct"],
        "defending": ["defensive_actions_per_match", "tackles_per_match", "interceptions_per_match",
                      "blocks_per_match"],
        "goalkeeping": ["saves", "saves_per_match", "saves_pct"],
        "set_pieces": ["corners", "corners_per_match", "corners_against_per_match", "free_kicks_per_match"],
        "discipline": ["cards_yellow", "cards_red", "fouls_per_match", "offsides_per_match"],
    },
}
PINNED_GROUP_ORDER = {
    "player": ["goals", "shooting", "passing", "one_on_one", "defending", "goalkeeping", "discipline",
               "playing_time"],
    "team": ["goals", "shooting", "passing", "one_on_one", "defending", "goalkeeping", "set_pieces",
             "discipline"],
}


def _ordered(entity: str) -> dict[str, list[str]]:
    placed = [r for r in _catalogue(entity).values() if r["metric_order"]]
    placed.sort(key=_place)
    groups: dict[str, list[str]] = {}
    for r in placed:
        groups.setdefault(r["metric_group"], []).append(r["metric_id"])
    return groups


def test_the_catalogue_order_is_pinned_per_group_for_players_and_teams():
    for entity in ("player", "team"):
        groups = _ordered(entity)
        assert list(groups) == PINNED_GROUP_ORDER[entity], f"{entity}: the group order changed"
        assert groups == PINNED_ORDER[entity], f"{entity}: a metric_order changed; update the pin with the catalogue"


def test_the_combined_player_cards_metric_has_no_place_so_players_and_teams_show_yellow_and_red():
    assert not _catalogue("player")["cards_player"]["metric_order"]
    assert _ordered("player")["discipline"][:2] == ["cards_yellow_player", "cards_red_player"]
    assert _ordered("team")["discipline"][:2] == ["cards_yellow", "cards_red"]


def _stem(metric_id: str) -> str:
    return metric_id.replace("_player", "").replace("_per90", "_per").replace("_per_match", "_per")


def test_a_metric_that_exists_for_players_and_teams_sits_in_the_same_relative_order():
    player, team = _ordered("player"), _ordered("team")
    for group in sorted(set(player) & set(team)):
        p = [_stem(m) for m in player[group]]
        t = [_stem(m) for m in team[group]]
        shared = [s for s in p if s in t]
        assert shared == [s for s in t if s in p], f"{group}: players read {shared}, teams read {[s for s in t if s in p]}"
        assert len(shared) == len(set(shared)), f"{group}: two metrics share a stem"
    shared_groups = [g for g in PINNED_GROUP_ORDER["player"] if g in PINNED_GROUP_ORDER["team"]]
    assert shared_groups == [g for g in PINNED_GROUP_ORDER["team"] if g in PINNED_GROUP_ORDER["player"]]
