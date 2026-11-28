"""The pre-match social image (`design-mocks/social/prematch.py`): what it draws and what it refuses."""

from __future__ import annotations

import copy
import importlib.util
import pathlib
import sys

import pytest

SOCIAL = pathlib.Path(__file__).resolve().parents[1] / "design-mocks" / "social"
_spec = importlib.util.spec_from_file_location("social_prematch", SOCIAL / "prematch.py")
prematch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prematch)

PNG_END = b"IEND\xaeB`\x82"


def sample():
    metrics = {m[0]: (0.5 if m[2] == "pct" else 1.5) for m in prematch.METRICS}
    window = {"window_type": "last_5", "games_in_window": 5, "games_with_team_stats": 5, **metrics}
    standing = {"is_knockout": False, "league_rank": 3, "standing_points": 20, "standing_goals_diff": -4}
    return {
        "fixture": {
            "fixture_sk": 1, "fixture_slug": "2031-03-02-a-vs-b", "league_code": "LG", "status_short": "NS",
            "round_label_i18n_key": "compFactMatchday", "round_number": 7,
            "kickoff_local": "2031-03-02 18:30:00", "kickoff_zone_label": "CET", "venue_name": "Ground & Park",
            "home_team_sk": 10, "home_team_name": "Home Town FC",
            "away_team_sk": 20, "away_team_name": "Awayside",
            "is_home_team_next_match": True, "is_away_team_next_match": True,
        },
        "window": [
            {"team_sk": 10, "contributing_competitions": ["CUP", "LG"], **window},
            {"team_sk": 20, "contributing_competitions": ["LG", "EUR"], **window},
        ],
        "standing": [{"team_sk": 10, **standing}, {"team_sk": 20, **standing}],
        "competitions": [
            {"league_code": "LG", "competition_name": "Zeta League"},
            {"league_code": "CUP", "competition_name": "Beta Cup"},
            {"league_code": "EUR", "competition_name": "Alpha Trophy"},
        ],
    }


def test_every_stated_value_comes_from_the_data():
    markup = prematch.page(prematch.model(sample()))
    for text in (
        "Spielvorschau · Zeta League", "<span>7. Spieltag</span>", "<span>So., 2. März 2031</span>",
        "<span>18:30 CET</span>", "<span>Ground &amp; Park</span>",
        "Letzte 5 Pflichtspiele · Zeta League, Alpha Trophy und Beta Cup",
        'Home Town <span class="nb">FC</span>', '<span class="nb">Awayside</span>',
        "#<b>3</b>", "<b>20</b> Punkte", "Diff. <b>−4</b>", 'src="crests/10-104.webp"',
    ):
        assert text in markup


def test_labels_and_order_are_the_approved_ones():
    markup = prematch.page(prematch.model(sample()))
    labels = ["Tore", "Gegentore", "Schüsse aufs Tor", "Schüsse aufs Tor gegen",
              "Schüsse aus dem Strafraum", "Abschlussquote", "Ballbesitz"]
    assert [chunk.split("<")[0] for chunk in markup.split('class="chart-name">')[1:]] == labels
    assert markup.count("pro Spiel") == 4


@pytest.mark.parametrize("home, away, better, winner", [
    (2.0, 1.0, "high", "home"), (2.0, 1.0, "low", "away"), (1.04, 0.96, "high", None),
])
def test_green_marks_the_better_shown_value(home, away, better, winner):
    row = prematch.metric_row({"metrics": {"x": home}}, {"metrics": {"x": away}}, "x", "X", "avg", better)
    assert ("cmp-home chart-better" in row) == (winner == "home")
    assert ("cmp-away chart-better" in row) == (winner == "away")


@pytest.mark.parametrize("value, kind, shown", [
    (0.125, "pct", "13%"), (0.625, "pct", "63%"), (23 / 40, "pct", "57%"),
    (0.25, "avg", "0,3"), (2.25, "avg", "2,3"), (1.0, "avg", "1,0"),
])
def test_an_exact_half_rounds_up_as_on_the_match_page(value, kind, shown):
    assert prematch.fmt(value, kind) == shown


@pytest.mark.parametrize("points, goal_diff, shown", [
    (1, 0, ("<b>1</b> Punkt</span>", "Diff. <b>0</b>")),
    (0, 3, ("<b>0</b> Punkte</span>", "Diff. <b>+3</b>")),
    (2, -1, ("<b>2</b> Punkte</span>", "Diff. <b>−1</b>")),
])
def test_the_standing_reads_as_on_the_match_page(points, goal_diff, shown):
    markup = prematch.team_block({"sk": 1, "name": "A B", "rank": 18, "points": points, "goal_diff": goal_diff})
    for text in shown:
        assert text in markup


def test_a_zero_value_is_drawn():
    data = sample()
    data["window"][0]["goals_against_per_match"] = 0.0
    assert "0,0" in prematch.page(prematch.model(data))


def _set(path, value):
    def change(data):
        target = data
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
    return change


REFUSALS = [
    *[_set(("fixture", key), None) for key in (
        "status_short", "league_code", "round_label_i18n_key", "round_number", "kickoff_local",
        "kickoff_zone_label", "venue_name", "home_team_name", "away_team_name",
        "is_home_team_next_match", "is_away_team_next_match",
    )],
    *[_set(("window", 1, m[0]), None) for m in prematch.METRICS],
    _set(("window", 1, "goals_per_match"), float("nan")),
    *[_set(("standing", 0, key), None) for key in (
        "league_rank", "standing_points", "standing_goals_diff", "is_knockout",
    )],
    _set(("standing", 0, "is_knockout"), True),
    _set(("standing",), []),
    _set(("window",), []),
    _set(("window", 0, "window_type"), "qualifiers"),
    _set(("window", 0, "games_in_window"), 4),
    _set(("window", 0, "games_with_team_stats"), 4),
    _set(("window", 0, "contributing_competitions"), []),
    _set(("competitions", 1, "competition_name"), None),
    _set(("fixture", "status_short"), "TBD"),
    _set(("fixture", "round_label_i18n_key"), "roundOf16"),
    _set(("fixture", "is_away_team_next_match"), False),
]


@pytest.mark.parametrize("change", REFUSALS)
def test_a_missing_or_untrue_value_stops_the_run(change):
    data = copy.deepcopy(sample())
    change(data)
    with pytest.raises(prematch.Refused):
        prematch.model(data)


def test_two_rows_for_one_team_stop_the_run():
    data = sample()
    data["standing"].append(dict(data["standing"][0]))
    with pytest.raises(prematch.Refused):
        prematch.model(data)


def test_the_template_reads_only_its_own_assets():
    markup = prematch.page(prematch.model(sample()))
    assert markup.count('rel="stylesheet"') == 2
    css = (prematch.ASSETS / "site.css").read_text(encoding="utf-8")
    assert "url(InterVariable.woff2)" in css and "url(/" not in css and "@import" not in css
    for name in ("layout.css", "InterVariable.woff2", "OFL.txt", "mark.svg", "wordmark.svg"):
        assert (prematch.ASSETS / name).is_file(), name


def test_the_wait_ends_on_the_finished_file_when_the_process_stays_alive(tmp_path):
    target = tmp_path / "shot.png"
    code = f"import sys,time; open(sys.argv[1],'wb').write({PNG_END!r}); time.sleep(60)"
    prematch.run_until_written([sys.executable, "-c", code, str(target)], target, timeout=30)
    assert target.read_bytes() == PNG_END


@pytest.mark.parametrize("code, timeout", [("raise SystemExit(3)", 30), ("import time; time.sleep(60)", 1)])
def test_a_run_that_writes_no_file_stops(tmp_path, code, timeout):
    with pytest.raises(prematch.Refused):
        prematch.run_until_written([sys.executable, "-c", code], tmp_path / "shot.png", timeout=timeout)
