"""Tests for `scripts/generate_metric_sql.py`.

The first test is the drift check: the SQL in the player models must be exactly what the
catalogue generates, so a hand edit inside a generated block, or a catalogue change the models did
not follow, fails `test:python`. The others drive the generator against a synthetic catalogue and
model and assert one thing it must do or refuse.
"""
from __future__ import annotations

import csv
import os
import pathlib
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import generate_metric_sql as gen  # noqa: E402

FIELDS = ["metric_id", "entity", "base_relation", "numerator_expr", "denominator_expr", "computation_kind"]


def _seed(tmp_path: pathlib.Path, rows: list[dict]) -> pathlib.Path:
    path = tmp_path / "metric_catalogue.csv"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({"entity": "player", "base_relation": gen.BASE_RELATION,
                             "denominator_expr": "", "computation_kind": "expression", **row})
    return path


def _model(tmp_path: pathlib.Path, relative: str, margin: str = "    ") -> pathlib.Path:
    path = tmp_path / "models" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "select\n    player_sk,\n" + margin + gen.BEGIN + "\n" + margin + gen.END + "\nfrom window_rows\n",
        encoding="utf-8",
    )
    return path


def test_models_match_the_catalogue():
    rendered = gen._render()
    drifted = [gen._rel(path) for path, text in rendered.items()
               if not gen._same(path.read_text(encoding="utf-8"), text)]
    assert drifted == [], (
        "generated metric SQL has drifted from the catalogue; run python scripts/generate_metric_sql.py: "
        + ", ".join(drifted)
    )


def test_every_surface_model_exists_and_carries_one_block():
    for surface in gen.SURFACES:
        text = (gen.MODELS / surface.model).read_text(encoding="utf-8")
        assert text.count(gen.BEGIN) == 1 and text.count(gen.END) == 1, surface.model


def test_a_hand_edit_inside_a_block_is_drift(tmp_path, monkeypatch):
    seed = _seed(tmp_path, [{"metric_id": f"m{i}_player", "numerator_expr": "sum(goals)"} for i in range(45)])
    model = _model(tmp_path, "a.sql")
    monkeypatch.setattr(gen, "SURFACES", (gen.Surface("a.sql", ("m0_player",)),))
    text = gen._render(tmp_path / "models", seed)[model]
    model.write_text(text.replace("sum(goals)", "sum(goals) + 1"), encoding="utf-8")
    assert not gen._same(model.read_text(encoding="utf-8"), gen._render(tmp_path / "models", seed)[model])


def test_every_aggregate_carries_the_eligibility_rule():
    lines = gen._metric_lines("x_pct", "sum(goals - goals_penalty)", "sum(shots_on_target)", False, "    ")
    sql = " ".join(line.strip() for line in lines)
    assert "logical_and(window_is_complete and (goals - goals_penalty) is not null)" in sql
    assert "logical_and(window_is_complete and shots_on_target is not null)" in sql
    assert sql.startswith("safe_divide(") and sql.endswith("as x_pct")


def test_a_windowed_surface_aggregates_over_the_window():
    lines = gen._metric_lines("goals_player", "sum(goals)", "", True, "    ")
    sql = " ".join(line.strip() for line in lines)
    assert "logical_and(window_is_complete and goals is not null) over w" in sql
    assert "sum(goals) over w" in sql


def test_countif_is_gated_like_sum():
    lines = gen._metric_lines("minutes_per_appearance", "sum(minutes)", "countif(minutes > 0)", False, "    ")
    assert "if(logical_and(window_is_complete and (minutes > 0) is not null), countif(minutes > 0), null)" in " ".join(
        line.strip() for line in lines)


def test_no_line_exceeds_the_lint_length():
    formulas = gen._read_formulas()
    for surface in gen.SURFACES:
        for line in gen._block(surface, formulas, "        "):
            assert len(line) <= gen.MAX_LINE, (surface.model, line)


def test_a_metric_the_catalogue_lacks_aborts(tmp_path, monkeypatch):
    seed = _seed(tmp_path, [{"metric_id": f"m{i}_player", "numerator_expr": "sum(goals)"} for i in range(45)])
    _model(tmp_path, "a.sql")
    monkeypatch.setattr(gen, "SURFACES", (gen.Surface("a.sql", ("not_in_catalogue",)),))
    with pytest.raises(gen.Abort, match="not_in_catalogue"):
        gen._render(tmp_path / "models", seed)


def test_a_model_without_markers_aborts(tmp_path, monkeypatch):
    seed = _seed(tmp_path, [{"metric_id": f"m{i}_player", "numerator_expr": "sum(goals)"} for i in range(45)])
    path = tmp_path / "models" / "a.sql"
    path.parent.mkdir(parents=True)
    path.write_text("select 1\n", encoding="utf-8")
    monkeypatch.setattr(gen, "SURFACES", (gen.Surface("a.sql", ("m0_player",)),))
    with pytest.raises(gen.Abort, match="markers"):
        gen._render(tmp_path / "models", seed)


def test_a_thin_catalogue_read_aborts(tmp_path):
    seed = _seed(tmp_path, [{"metric_id": "goals_player", "numerator_expr": "sum(goals)"}])
    with pytest.raises(gen.Abort, match="floor"):
        gen._read_formulas(seed)


def test_a_team_row_is_never_read_as_a_player_formula(tmp_path):
    rows = [{"metric_id": f"m{i}_player", "numerator_expr": "sum(goals)"} for i in range(45)]
    rows.append({"metric_id": "goals_per_match", "entity": "team", "numerator_expr": "sum(goals_for)"})
    formulas = gen._read_formulas(_seed(tmp_path, rows))
    assert "goals_per_match" not in formulas


def test_the_block_follows_the_marker_indentation(tmp_path, monkeypatch):
    seed = _seed(tmp_path, [{"metric_id": f"m{i}_player", "numerator_expr": "sum(goals)"} for i in range(45)])
    model = _model(tmp_path, "a.sql", margin="        ")
    monkeypatch.setattr(gen, "SURFACES", (gen.Surface("a.sql", ("m0_player", "m1_player")),))
    text = gen._render(tmp_path / "models", seed)[model]
    block = [line for line in text.split("\n") if "sum(goals)" in line]
    assert block and all(line.startswith("        if(") for line in block)
    assert block[0].endswith(",") and not block[-1].endswith(",")
