"""Tests for the metric map that `scripts/sync_metric_docs_blocks.py` generates.

The map says where each catalogue metric can be read in the marts. The synthetic tests drive the
generator against a small catalogue and mart tree and assert one property or one refusal each; the
real-repo tests hold the committed seed to the generator and to the 20 fan questions of #190.
"""
from __future__ import annotations

import csv
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import sync_metric_docs_blocks as gen  # noqa: E402

REAL_MAP = gen.MAP_OUT
SEED_FIELDS = ["metric_id", "entity", "description", "denominator_expr"]


def _model(name, columns):
    """A model entry; a column is (name, description) or (name, description, accepted values)."""
    lines = [f"  - name: {name}", "    columns:"]
    for column in columns:
        lines += [f"      - name: {column[0]}", f"        description: \"{column[1]}\""]
        if len(column) > 2:
            lines += ["        tests:", "          - accepted_values:",
                      f"              values: {column[2]!r}"]
    return "\n".join(lines) + "\n"


@pytest.fixture
def repo(monkeypatch, tmp_path):
    """Points the generator at a catalogue of team metrics and at model files the test writes."""
    monkeypatch.setattr(gen, "MIN_METRICS", 1)
    monkeypatch.setattr(gen, "MIN_DERIVED", 0)
    monkeypatch.setattr(gen, "MODELS", tmp_path / "models")
    monkeypatch.setattr(gen, "OUT", tmp_path / "out" / "metric_columns.md")
    monkeypatch.setattr(gen, "MAP_OUT", tmp_path / "out" / "metric_map.csv")

    def build(metric_ids, marts, others=None):
        seed = tmp_path / "metric_catalogue.csv"
        with open(seed, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=SEED_FIELDS)
            writer.writeheader()
            writer.writerows({"metric_id": m, "entity": "team", "description": "A definition.",
                              "denominator_expr": ""} for m in metric_ids)
        monkeypatch.setattr(gen, "SEED", seed)
        for layer, yml in {gen.MARTS_DIR: marts, **(others or {})}.items():
            folder = tmp_path / "models" / layer
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "schema.yml").write_text("version: 2\nmodels:\n" + yml, encoding="utf-8")

    return build


def _map():
    text = gen._render_map(gen._read_rows(), gen._column_names()).decode("utf-8")
    return list(csv.DictReader(io.StringIO(text)))


def _run(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["sync_metric_docs_blocks.py", *args])
    return gen.main()


# ---------------------------------------------------------------- what is a row

def test_a_mart_column_pointing_at_a_metric_block_is_a_row(repo):
    repo(["goals"], _model("mart_x", [("goals_for", "{{ doc('goals') }}")]))

    assert _map() == [{"table_name": "mart_x", "column_name": "goals_for", "metric_id": "goals",
                       "variant": "", "window_column": "", "metric_key_column": ""}]


def test_a_column_pointing_at_no_metric_block_is_not_a_row(repo):
    """Only a generated metric block says a column holds a metric; a hand-written block or a
    sentence says nothing the generator can rely on."""
    repo(["goals"], _model("mart_x", [("goals_for", "{{ doc('goals') }}"),
                                      ("fouls", "{{ doc('fouls') }}"),
                                      ("goals_text", "Goals the team scored.")]))

    assert [r["column_name"] for r in _map()] == ["goals_for"]


def test_a_column_outside_the_marts_is_not_a_row(repo):
    repo(["goals"], _model("mart_x", [("goals_for", "{{ doc('goals') }}")]),
         {"4_intermediate": _model("int_x", [("goals", "{{ doc('goals') }}")])})

    assert {r["table_name"] for r in _map()} == {"mart_x"}


def test_a_derived_block_maps_to_its_metric(repo):
    repo(["goals"], _model("mart_x", [("goals_this_season",
                                       "{{ doc('goals_this_season__team') }}")]))

    (row,) = _map()
    assert (row["metric_id"], row["variant"]) == ("goals", "this_season")


@pytest.mark.parametrize("column, variant", [
    ("goals_for", ""),
    ("goals_player_prev_season_full", "prev_season_full"),
    ("goals_player_prev_season", "prev_season"),
    ("points_delta_yoy", "delta_yoy"),
    ("goals_for_sum_season", "sum_season"),
    ("home_goals_per_match_recent", "home_form"),
    ("away_points_won_sum_form", "away_form"),
    ("goals_away", "away"),
    ("opponent_corner_kicks_sum_season", "opponent_sum_season"),
    ("last_meeting_goals_for", "last_meeting"),
    ("recent_meetings.goals_for", "recent_meetings"),
])
def test_the_variant_is_read_from_the_column_name(column, variant):
    assert gen._variant(column) == variant


def test_a_table_holding_several_windows_names_its_window_column(repo):
    repo(["goals"], _model("mart_x", [("window_type", "Which window."),
                                      ("goals", "{{ doc('goals') }}")]))

    (row,) = _map()
    assert row["window_column"] == "window_type"


# ---------------------------------------------------------------- long-format marts

def test_a_long_format_mart_enters_with_one_row_per_metric(repo):
    repo(["goals", "corners"], _model("mart_board", [
        ("metric_key", "The metric.", ["goals", "corners"]), ("metric_value", "The value.")]))

    assert [(r["column_name"], r["metric_id"], r["metric_key_column"]) for r in _map()] == [
        ("metric_value", "corners", "metric_key"), ("metric_value", "goals", "metric_key")]


def test_a_ranking_reads_its_value_from_sort_value(repo):
    repo(["goals"], _model("mart_board", [("metric_key", "The board.", ["goals"]),
                                          ("sort_value", "The value.")]))

    assert [r["column_name"] for r in _map()] == ["sort_value"]


@pytest.mark.parametrize("columns, refusal", [
    ([("metric_key", "The metric."), ("metric_value", "The value.")],
     "pins no accepted_values"),
    ([("metric_key", "The metric.", ["goals", "nonsense"]), ("metric_value", "The value.")],
     "does not define: nonsense"),
    ([("metric_key", "The metric.", ["goals"]), ("rank", "The rank.")],
     "to hold its value"),
])
def test_a_long_format_mart_it_cannot_read_is_refused(repo, monkeypatch, capsys, columns,
                                                      refusal):
    repo(["goals"], _model("mart_board", columns))

    assert _run(monkeypatch, "--check") == 1
    assert refusal in capsys.readouterr().err


# ---------------------------------------------------------------- coverage and drift

def test_a_metric_no_mart_column_holds_is_refused(repo, monkeypatch, capsys):
    repo(["goals", "orphan"], _model("mart_x", [("goals_for", "{{ doc('goals') }}")]))

    assert _run(monkeypatch) == 1
    err = capsys.readouterr().err
    assert "no mart column" in err and "orphan" in err
    assert not gen.MAP_OUT.exists()


def test_check_names_a_row_the_file_lacks(repo, monkeypatch, capsys):
    repo(["goals", "corners"], _model("mart_x", [("goals_for", "{{ doc('goals') }}"),
                                                 ("corner_kicks", "{{ doc('corners') }}")]))
    assert _run(monkeypatch) == 0
    capsys.readouterr()

    repo(["goals", "corners"], _model("mart_x", [("goals_for", "{{ doc('goals') }}"),
                                                 ("corner_kicks", "{{ doc('corners') }}"),
                                                 ("away_corners", "{{ doc('corners') }}")]))
    assert _run(monkeypatch, "--check") == 1
    assert "missing row: mart_x,away_corners,corners,away,," in capsys.readouterr().out


def test_check_names_a_row_no_longer_generated(repo, monkeypatch, capsys):
    repo(["goals", "corners"], _model("mart_x", [("goals_for", "{{ doc('goals') }}"),
                                                 ("corner_kicks", "{{ doc('corners') }}"),
                                                 ("away_corners", "{{ doc('corners') }}")]))
    assert _run(monkeypatch) == 0
    capsys.readouterr()

    repo(["goals", "corners"], _model("mart_x", [("goals_for", "{{ doc('goals') }}"),
                                                 ("corner_kicks", "{{ doc('corners') }}")]))
    assert _run(monkeypatch, "--check") == 1
    assert ("row no longer generated: mart_x,away_corners,corners,away,,"
            in capsys.readouterr().out)


def test_check_reports_drift_that_changes_no_row(repo, monkeypatch, capsys):
    """Same rows, different bytes: without this message the failure would name nothing."""
    repo(["goals"], _model("mart_x", [("goals_for", "{{ doc('goals') }}")]))
    assert _run(monkeypatch) == 0
    capsys.readouterr()

    gen.MAP_OUT.write_bytes(gen.MAP_OUT.read_bytes().replace(b"mart_x,", b'"mart_x",'))
    assert _run(monkeypatch, "--check") == 1
    assert "the rows all match but the bytes do not" in capsys.readouterr().out


# ---------------------------------------------------------------- the real repo

def _real_rows():
    with open(REAL_MAP, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _accepted(table, column):
    for path in sorted((gen.MODELS / gen.MARTS_DIR).rglob("*.yml")):
        for model, columns in gen._models_in(path):
            for col in columns if model == table else []:
                if col["name"] == column:
                    for test in col.get("tests") or []:
                        if isinstance(test, dict) and "accepted_values" in test:
                            return test["accepted_values"]["values"]
    return []


def test_the_real_map_matches_the_generator():
    """Fails when the catalogue or a mart's YAML changes and the map is not regenerated."""
    try:
        expected = gen._render_map(gen._read_rows(), gen._column_names())
    except gen.Abort as exc:                                    # pragma: no cover
        pytest.fail(f"the real repo does not render a map: {exc}")

    assert gen._same(REAL_MAP.read_bytes(), expected), (
        "dbt_project/seeds/metric_map.csv has drifted. Run: python scripts/sync_metric_docs_blocks.py")


# (question, table, column, metric, the filters the answer needs)
QUESTIONS = (
    ("How many goals per match has Arsenal scored in its last five matches?",
     "mart_team_momentum", "goals_per_match", "goals_per_match", {"window_type": "last_5"}),
    ("How many more or fewer points does Bayern Munich have than at the same point last season?",
     "mart_team_profile", "points_delta_yoy", "points_won", {}),
    ("How many goals per match was Leverkusen conceding at this point last season?",
     "mart_team_profile", "goals_against_per_match_prev_season", "goals_against_per_match", {}),
    ("Has Napoli won more points this season than its chances deserved?",
     "mart_team_profile", "deserved_points_gap", "deserved_points_gap", {}),
    ("Does Liverpool get more shots on target per match than the typical Premier League team?",
     "mart_team_competition_benchmarks", "metric_value", "shots_on_goal_per_match",
     {"metric_key": "shots_on_goal_per_match"}),
    ("Which Premier League teams get the most yellow cards this season?",
     "mart_team_leaderboards", "sort_value", "cards_yellow", {"metric_key": "cards_yellow"}),
    ("How many goals did Barcelona score the last time they played Real Madrid?",
     "mart_head_to_head", "last_meeting_goals_for", "goals", {}),
    ("How many corners did Dortmund win in their last match?",
     "mart_team_fixture_stats", "corner_kicks", "corners", {}),
    ("How many goals per match did Argentina score at the 2026 World Cup?",
     "mart_team_profile", "goals_per_match", "goals_per_match", {"league_code": "WC"}),
    ("Going into Saturday's game, how many points has the home side taken from its recent "
     "matches?",
     "mart_matchday_insights", "home_points_won_sum_form", "points_won", {}),
    ("How many goals has Harry Kane scored this season?",
     "mart_player_profile", "goals_player", "goals_player", {}),
    ("Who are the top scorers in La Liga this season?",
     "mart_leaderboards", "sort_value", "goals_player", {"metric_key": "goals_player"}),
    ("How many goals per 90 minutes does Haaland score, compared with other forwards in his "
     "league?",
     "mart_player_competition_benchmarks", "metric_value", "goals_per90",
     {"metric_key": "goals_per90", "position_group": "ATT"}),
    ("What share of the shots on target he faces does Courtois save?",
     "mart_player_profile", "saves_player_pct", "saves_player_pct", {}),
    ("How many assists has Musiala made in his team's last five matches?",
     "mart_player_momentum", "goals_assists", "assists_player", {"window_type": "last_5"}),
    ("Has Salah scored more or fewer goals than at the same point last season?",
     "mart_player_profile", "goals_player_delta_yoy", "goals_player", {}),
    ("How many goals did Wirtz score in the whole of last season?",
     "mart_player_profile", "goals_player_prev_season_full", "goals_player", {}),
    ("How many goals did Lewandowski score for Barcelona each season?",
     "mart_player_career", "goals_player", "goals_player", {}),
    ("How many tackles did Declan Rice make in his last match?",
     "mart_player_match_log", "tackles_total", "tackles_player", {}),
    ("What share of his team's goals has Mbappé scored or set up this season?",
     "mart_player_profile", "contribution_player_pct", "contribution_player_pct", {}),
)


def test_there_are_twenty_questions():
    assert len(QUESTIONS) == 20


@pytest.mark.parametrize("question, table, column, metric, filters", QUESTIONS,
                         ids=[f"q{n:02d}" for n in range(1, len(QUESTIONS) + 1)])
def test_the_map_answers_a_fan_question(question, table, column, metric, filters):
    """The map names the column, and every filter the answer needs is one the table accepts."""
    rows = {(r["table_name"], r["column_name"], r["metric_id"]): r for r in _real_rows()}
    row = rows.get((table, column, metric))

    assert row, f"the map has no row {table}.{column} for {metric}: {question}"
    if row["window_column"]:
        assert filters.get(row["window_column"]) in _accepted(table, row["window_column"]), question
    if row["metric_key_column"]:
        assert filters.get(row["metric_key_column"]) == metric, question
