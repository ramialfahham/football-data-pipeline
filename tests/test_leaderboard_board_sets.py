"""The leaderboard marts' board sets are written in several places, and they must agree.

A board is named in the mart's Jinja lists and the yml's `accepted_values` on `metric_key`; the
export's tuples choose the boards a page shows from it. A key missing from the yml is a build that
fails; an export board the mart does not rank is a board the page lacks.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from scripts.export_site_data import (
    _COMPETITION_PLAYER_BOARDS,
    _COMPETITION_TEAM_BOARDS,
    _HOME_PLAYER_BOARDS,
    _HOME_TEAM_BOARDS,
    _MATCH_PLAYER_BOARDS,
    _in_catalogue_order,
)

REPO = Path(__file__).resolve().parent.parent
MARTS = REPO / "dbt_project" / "models" / "5_marts" / "shared"
TEAM_SQL = MARTS / "mart_team_leaderboards.sql"
PLAYER_SQL = MARTS / "mart_leaderboards.sql"
SHARED_YML = MARTS / "shared.yml"

_KEY = re.compile(r"'([a-z0-9_]+)'")


def _jinja_list(text: str, name: str) -> list[str]:
    """The string keys of `{% set <name> = [ ... ] %}` in a model, in order."""
    m = re.search(r"\{%\s*set\s+" + name + r"\s*=\s*\[(.*?)\]\s*%\}", text, re.S)
    assert m, f"no `set {name}` list found"
    return _KEY.findall(m.group(1))


def _dict_keys(text: str, name: str) -> list[str]:
    """The `key` of each dict in `{% set <name> = [ {...}, ... ] %}`."""
    m = re.search(r"\{%\s*set\s+" + name + r"\s*=\s*\[(.*?)\]\s*%\}", text, re.S)
    assert m, f"no `set {name}` list found"
    return re.findall(r"'key':\s*'([a-z0-9_]+)'", m.group(1))


def _player_season_boards(text: str) -> list[str]:
    """Every season board, in the order the model unions them."""
    return (_jinja_list(text, "count_boards") + _jinja_list(text, "per90_boards")
            + _dict_keys(text, "scoped_per90_boards") + _dict_keys(text, "rate_boards"))


def _accepted_values(model: str) -> list[str]:
    doc = yaml.safe_load(SHARED_YML.read_text(encoding="utf-8"))
    for m in doc["models"]:
        if m["name"] != model:
            continue
        for col in m.get("columns", []):
            if col["name"] != "metric_key":
                continue
            for t in col.get("tests", []):
                if isinstance(t, dict) and "accepted_values" in t:
                    return list(t["accepted_values"]["values"])
    raise AssertionError(f"{model}.metric_key has no accepted_values")


def _check(mart: list[str], accepted: list[str], exported: tuple[str, ...], label: str) -> list[str]:
    problems = []
    if not set(exported) <= set(mart):
        problems.append(f"{label}: the export shows {sorted(set(exported) - set(mart))}, which the mart does not rank")
    if set(mart) != set(accepted):
        problems.append(f"{label}: accepted_values differ from the mart on {sorted(set(mart) ^ set(accepted))}")
    if len(set(mart)) != len(mart):
        problems.append(f"{label}: the mart names a board twice")
    if len(set(exported)) != len(exported):
        problems.append(f"{label}: the export names a board twice")
    return problems


def test_team_boards_agree_in_the_mart_the_yml_and_the_export():
    mart = _jinja_list(TEAM_SQL.read_text(encoding="utf-8"), "boards")
    assert len(mart) == 38, "the Statistics and Rankings tab team boards (GitLab #139, #129)"
    accepted = _accepted_values("mart_team_leaderboards")
    assert _check(mart, accepted, _COMPETITION_TEAM_BOARDS, "team") == []
    assert _check(mart, accepted, _HOME_TEAM_BOARDS, "team home") == []


def test_player_boards_agree_in_the_mart_the_yml_and_the_export():
    text = PLAYER_SQL.read_text(encoding="utf-8")
    season = _player_season_boards(text)
    assert len(season) == 44, "the Statistics and Rankings tab player boards (GitLab #139, #129)"
    match_boards = _jinja_list(text, "match_boards")
    assert len(match_boards) == 8, "the Match leaders boards of the played match page"
    accepted = _accepted_values("mart_leaderboards")
    assert set(accepted) == set(season) | set(match_boards), "accepted_values cover the season and match boards"
    season_accepted = sorted(set(accepted) - (set(match_boards) - set(season)))
    assert _check(season, season_accepted, _COMPETITION_PLAYER_BOARDS, "player") == []
    assert _check(season, season_accepted, _HOME_PLAYER_BOARDS, "player home") == []


def test_the_export_match_boards_are_ranked_by_the_mart():
    match_boards = _jinja_list(PLAYER_SQL.read_text(encoding="utf-8"), "match_boards")
    assert set(_MATCH_PLAYER_BOARDS) <= set(match_boards), "the Match leaders boards the export carries"
    assert len(set(_MATCH_PLAYER_BOARDS)) == len(_MATCH_PLAYER_BOARDS)
    assert _in_catalogue_order(_MATCH_PLAYER_BOARDS, "player") == (
        "shots_player", "passes_player", "passes_key_player", "dribbles_attempts_player",
        "duels_won_player", "defensive_actions_player", "fouls_player",
    ), "the ruled order of the Match leaders boards"


def test_the_export_lists_the_ruled_order():
    """The page keeps the export's order within a group, so the tuple carries the ordering."""
    assert _COMPETITION_TEAM_BOARDS[:2] == ("goals_per_match", "goals_against_per_match")
    assert _COMPETITION_TEAM_BOARDS[-2:] == ("cards_yellow", "cards_red")
    assert _COMPETITION_PLAYER_BOARDS[:2] == ("goals_player", "assists_player")
    assert _COMPETITION_PLAYER_BOARDS[-1] == "saves_player"


def test_the_most_first_overrides_are_exactly_the_discipline_boards():
    """Only the discipline boards override the catalogue's direction; another key would mis-rank."""
    assert _jinja_list(TEAM_SQL.read_text(encoding="utf-8"), "most_first_by_ruling") == [
        "cards_yellow", "cards_red", "fouls_per_match", "offsides_per_match",
    ]
    assert _jinja_list(PLAYER_SQL.read_text(encoding="utf-8"), "most_first_by_ruling") == [
        "cards_yellow_player", "cards_red_player", "penalty_committed_player", "fouls_per90", "offsides_per90",
    ]


# --- the guard seen red -------------------------------------------------------------------- #

def test_an_export_board_the_mart_does_not_rank_is_red():
    mart = _jinja_list(TEAM_SQL.read_text(encoding="utf-8"), "boards")
    accepted = _accepted_values("mart_team_leaderboards")
    assert _check(mart[1:], accepted[1:], ("goals",) + _COMPETITION_TEAM_BOARDS, "team")


def test_a_board_missing_from_the_yml_is_red():
    mart = _jinja_list(TEAM_SQL.read_text(encoding="utf-8"), "boards")
    assert _check(mart, _accepted_values("mart_team_leaderboards")[:-1], _COMPETITION_TEAM_BOARDS, "team")


def test_a_board_missing_from_the_mart_is_red():
    season = _player_season_boards(PLAYER_SQL.read_text(encoding="utf-8"))
    accepted = _accepted_values("mart_leaderboards")
    assert _check(season[1:], accepted, _COMPETITION_PLAYER_BOARDS, "player")
