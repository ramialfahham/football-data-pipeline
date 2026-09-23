"""The Rankings tab's board sets are written in three places each, and they must be one set.

A board is named in the mart's Jinja list (what the warehouse ranks), in the yml's
`accepted_values` on `metric_key` (what a build accepts), and in the export's tuple (what the
page is served). GitLab #151: "each list, its seed's accepted values and its singular test move
together". A key present in one and missing from another is a board the page silently lacks or a
build that silently fails, so the three copies are read here and compared as sets and as order.
The check is seen red in the mutation tests below before it is trusted.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from scripts.export_site_data import _COMPETITION_PLAYER_BOARDS, _COMPETITION_TEAM_BOARDS

REPO = Path(__file__).resolve().parent.parent
MARTS = REPO / "dbt_project" / "models" / "5_marts" / "shared"
TEAM_SQL = MARTS / "mart_team_leaderboards.sql"
PLAYER_SQL = MARTS / "mart_leaderboards.sql"
SHARED_YML = MARTS / "shared.yml"

_KEY = re.compile(r"'([a-z_]+)'")


def _jinja_list(text: str, name: str) -> list[str]:
    """The string keys of `{% set <name> = [ ... ] %}` in a model, in order."""
    m = re.search(r"\{%\s*set\s+" + name + r"\s*=\s*\[(.*?)\]\s*%\}", text, re.S)
    assert m, f"no `set {name}` list found"
    return _KEY.findall(m.group(1))


def _player_boards_in_sql(text: str) -> list[str]:
    """count_boards, then the `key` of each rate board — the order the model unions them in."""
    counts = _jinja_list(text, "count_boards")
    m = re.search(r"\{%\s*set\s+rate_boards\s*=\s*\[(.*?)\]\s*%\}", text, re.S)
    assert m, "no `set rate_boards` list found"
    rates = re.findall(r"'key':\s*'([a-z_]+)'", m.group(1))
    return counts + rates


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
    if set(mart) != set(exported):
        problems.append(f"{label}: mart ranks {sorted(set(mart) ^ set(exported))} differently from the export")
    if set(mart) != set(accepted):
        problems.append(f"{label}: accepted_values differ from the mart on {sorted(set(mart) ^ set(accepted))}")
    if len(set(exported)) != len(exported):
        problems.append(f"{label}: the export names a board twice")
    return problems


def test_team_boards_are_one_set_in_the_mart_the_yml_and_the_export():
    mart = _jinja_list(TEAM_SQL.read_text(encoding="utf-8"), "boards")
    assert len(mart) == 12, "the ruled team board count (GitLab #129)"
    assert _check(mart, _accepted_values("mart_team_leaderboards"), _COMPETITION_TEAM_BOARDS, "team") == []


def test_player_boards_are_one_set_in_the_mart_the_yml_and_the_export():
    mart = _player_boards_in_sql(PLAYER_SQL.read_text(encoding="utf-8"))
    assert len(mart) == 13, "the ruled player board count (GitLab #129)"
    assert _check(mart, _accepted_values("mart_leaderboards"), _COMPETITION_PLAYER_BOARDS, "player") == []


def test_the_export_lists_the_ruled_order():
    """The page keeps the export's order within a group, so the tuple carries the ruling:
    groups in the catalogue's order, and inside a group the issue's order."""
    assert _COMPETITION_TEAM_BOARDS[:2] == ("goals_per_match", "goals_against_per_match")
    assert _COMPETITION_TEAM_BOARDS[-2:] == ("cards_yellow", "cards_red")
    assert _COMPETITION_PLAYER_BOARDS[:2] == ("goals_player", "assists_player")
    assert _COMPETITION_PLAYER_BOARDS[-1] == "saves_player"


def test_the_mart_most_first_override_is_exactly_the_two_card_boards():
    """The ruled exception to "direction from the catalogue" is the two card boards and nothing
    else; a third key here would rank a fewest-is-best figure most first without a ruling."""
    text = TEAM_SQL.read_text(encoding="utf-8")
    assert _jinja_list(text, "most_first_by_ruling") == ["cards_yellow", "cards_red"]


# --- the guard seen red -------------------------------------------------------------------- #

def test_a_board_missing_from_the_export_is_red():
    mart = _jinja_list(TEAM_SQL.read_text(encoding="utf-8"), "boards")
    assert _check(mart, _accepted_values("mart_team_leaderboards"), _COMPETITION_TEAM_BOARDS[1:], "team")


def test_a_board_missing_from_the_yml_is_red():
    mart = _jinja_list(TEAM_SQL.read_text(encoding="utf-8"), "boards")
    assert _check(mart, _accepted_values("mart_team_leaderboards")[:-1], _COMPETITION_TEAM_BOARDS, "team")


def test_a_board_missing_from_the_mart_is_red():
    mart = _player_boards_in_sql(PLAYER_SQL.read_text(encoding="utf-8"))
    assert _check(mart[1:], _accepted_values("mart_leaderboards"), _COMPETITION_PLAYER_BOARDS, "player")
