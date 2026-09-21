"""Tests for `scripts/check_yml_vs_projection.py`.

Each test drives the gate against a synthetic project and a synthetic catalogue and asserts one
thing it must refuse, or one thing it must accept. The real-tree test at the end runs only when a
COMPLETE catalogue is on disk — on a dev machine `dbt_project/target/catalog.json` is whatever the
last local `dbt docs generate` wrote, and the gate's own partial-catalogue abort would fire on it,
which would be the abort working, not the tree failing.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import check_yml_vs_projection as gate  # noqa: E402


YML = """version: 2

models:
  - name: mart_thing
    description: One row per thing.
    columns:
      - name: thing_sk
        description: Identity key.
      - name: league_code
        description: The competition.
"""


def _project(tmp_path, ymls: dict[str, str], models: dict[str, str] | None = None):
    """A minimal dbt project: one .sql per model, plus the schema files given."""
    dbt = tmp_path / "dbt_project"
    if models is None:
        models = {}
        for body in ymls.values():
            doc = yaml.safe_load(body) or {}
            for model in doc.get("models") or []:
                models[model["name"]] = "5_marts"
    for name, layer in models.items():
        d = dbt / "models" / layer
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{name}.sql").write_text("select 1\n", encoding="utf-8")
    for rel, body in ymls.items():
        path = dbt / "models" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return dbt


def _catalog(tmp_path, columns: dict[str, list[str]], name: str = "catalog.json"):
    nodes = {
        f"model.proj.{model}": {
            "metadata": {"schema": "marts", "name": model},
            "columns": {c: {"name": c, "index": i} for i, c in enumerate(cols)},
        }
        for model, cols in columns.items()
    }
    path = tmp_path / name
    path.write_text(json.dumps({"nodes": nodes, "sources": {}}), encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def _point_at_tmp(monkeypatch, tmp_path):
    """Every test supplies a one-or-two model project, so both floors would fire on all of them
    and mask what is being tested. They keep their real values in the two floor tests."""
    monkeypatch.setattr(gate, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(gate, "DBT_DIR", tmp_path / "dbt_project")
    monkeypatch.setattr(gate, "MODELS_DIR", tmp_path / "dbt_project" / "models")
    monkeypatch.setattr(gate, "MIN_MODELS", 1)
    monkeypatch.setattr(gate, "MIN_LISTED_COLUMNS", 1)


def test_a_listed_column_missing_from_the_projection_is_red(tmp_path, capsys):
    _project(tmp_path, {"marts.yml": YML})
    cat = _catalog(tmp_path, {"mart_thing": ["thing_sk"]})
    assert gate.main(cat) == 1
    out = capsys.readouterr().out
    assert out.startswith("PROJECTION:")
    assert "mart_thing.league_code is listed but not in the model's projection" in out
    assert "marts.yml" in out


def test_every_listed_column_present_is_green(tmp_path, capsys):
    _project(tmp_path, {"marts.yml": YML})
    cat = _catalog(tmp_path, {"mart_thing": ["thing_sk", "league_code", "unlisted_extra"]})
    assert gate.main(cat) == 0
    assert capsys.readouterr().out.startswith("OK: 1 models, 2 listed columns, 0 absent")


STRUCT_YML = YML + "      - name: recent_meetings\n        description: A struct.\n" \
                   "      - name: recent_meetings.goals_for\n        description: A field.\n"

# What dbt-bigquery's catalogue holds for a STRUCT column: the parent and every leaf path
# (`INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`), which is how the dotted entries in the repo's
# own ymls came to be written by `declare_missing_columns.py` in the first place.
STRUCT_COLUMNS = ["thing_sk", "league_code", "recent_meetings", "recent_meetings.goals_for",
                  "recent_meetings.result"]


def test_a_struct_field_listed_and_present_is_green(tmp_path):
    _project(tmp_path, {"marts.yml": STRUCT_YML})
    cat = _catalog(tmp_path, {"mart_thing": STRUCT_COLUMNS})
    assert gate.main(cat) == 0


def test_a_struct_field_absent_from_the_catalogue_is_red_even_with_its_parent_present(tmp_path, capsys):
    """A mistyped or removed field must not pass on its parent's back."""
    yml = STRUCT_YML + "      - name: recent_meetings.goals_fro\n        description: Typo.\n"
    _project(tmp_path, {"marts.yml": yml})
    cat = _catalog(tmp_path, {"mart_thing": STRUCT_COLUMNS})
    assert gate.main(cat) == 1
    out = capsys.readouterr().out
    assert "mart_thing.recent_meetings.goals_fro is listed" in out
    assert "goals_for is listed" not in out


def test_a_yml_block_for_a_model_with_no_sql_on_disk_is_red(tmp_path, capsys):
    """`dbt parse` only warns on an orphan block; its descriptions reach nothing."""
    orphan = YML.replace("mart_thing", "mart_gone")
    _project(tmp_path, {"marts.yml": YML, "gone.yml": orphan}, models={"mart_thing": "5_marts"})
    cat = _catalog(tmp_path, {"mart_thing": ["thing_sk", "league_code"]})
    assert gate.main(cat) == 1
    out = capsys.readouterr().out
    assert "gone.yml: mart_gone is declared but has no model file on disk" in out


def test_column_names_match_case_insensitively(tmp_path):
    _project(tmp_path, {"marts.yml": YML})
    cat = _catalog(tmp_path, {"mart_thing": ["THING_SK", "League_Code"]})
    assert gate.main(cat) == 0


def test_a_partial_catalogue_aborts_and_names_the_model(tmp_path, capsys):
    """An on-disk model the catalogue does not hold means the catalogue is not this
    warehouse's; judging the rest against it would be a smaller answer presented as the answer."""
    _project(tmp_path, {"marts.yml": YML}, models={"mart_thing": "5_marts", "mart_other": "5_marts"})
    cat = _catalog(tmp_path, {"mart_thing": ["thing_sk", "league_code"]})
    assert gate.main(cat) == 1
    out = capsys.readouterr().out
    assert out.startswith("ABORT:")
    assert "missing 1 of 2 models on disk" in out
    assert "mart_other" in out


def test_a_missing_catalogue_file_aborts(tmp_path, capsys):
    _project(tmp_path, {"marts.yml": YML})
    assert gate.main(tmp_path / "absent.json") == 1
    out = capsys.readouterr().out
    assert out.startswith("ABORT:")
    assert "cannot read" in out


def test_an_invalid_catalogue_file_aborts(tmp_path, capsys):
    _project(tmp_path, {"marts.yml": YML})
    bad = tmp_path / "catalog.json"
    bad.write_text("{not json", encoding="utf-8")
    assert gate.main(bad) == 1
    assert "cannot read (JSONDecodeError)" in capsys.readouterr().out


def test_an_unparseable_yml_aborts_and_names_it(tmp_path, capsys):
    _project(tmp_path, {"marts.yml": YML, "broken.yml": "models:\n  - name: [\n"},
             models={"mart_thing": "5_marts"})
    cat = _catalog(tmp_path, {"mart_thing": ["thing_sk", "league_code"]})
    assert gate.main(cat) == 1
    out = capsys.readouterr().out
    assert out.startswith("ABORT:")
    assert "broken.yml: cannot parse" in out


def test_a_model_declared_in_two_ymls_aborts(tmp_path, capsys):
    _project(tmp_path, {"a.yml": YML, "b.yml": YML})
    cat = _catalog(tmp_path, {"mart_thing": ["thing_sk", "league_code"]})
    assert gate.main(cat) == 1
    assert "declared twice" in capsys.readouterr().out


def test_a_yml_whose_models_key_is_not_a_list_is_skipped(tmp_path):
    """`dbt_project.yml` has a `models:` DICT (the config tree); it declares nothing."""
    _project(tmp_path, {"marts.yml": YML})
    (tmp_path / "dbt_project" / "dbt_project.yml").write_text(
        "name: proj\nmodels:\n  proj:\n    +materialized: table\n", encoding="utf-8"
    )
    cat = _catalog(tmp_path, {"mart_thing": ["thing_sk", "league_code"]})
    assert gate.main(cat) == 0


def test_below_the_models_floor_is_red(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(gate, "MIN_MODELS", 50)
    _project(tmp_path, {"marts.yml": YML})
    cat = _catalog(tmp_path, {"mart_thing": ["thing_sk", "league_code"]})
    assert gate.main(cat) == 1
    assert "found only 1 models" in capsys.readouterr().out


def test_below_the_listed_columns_floor_is_red(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(gate, "MIN_LISTED_COLUMNS", 800)
    _project(tmp_path, {"marts.yml": YML})
    cat = _catalog(tmp_path, {"mart_thing": ["thing_sk", "league_code"]})
    assert gate.main(cat) == 1
    assert "found only 2 listed columns" in capsys.readouterr().out


def test_the_cli_takes_the_catalogue_path(tmp_path, capsys):
    _project(tmp_path, {"marts.yml": YML})
    cat = _catalog(tmp_path, {"mart_thing": ["thing_sk"]})
    assert gate._cli(["--catalog", str(cat)]) == 1
    assert "league_code" in capsys.readouterr().out


def test_the_real_tree_against_a_complete_catalogue(monkeypatch, capsys):
    """Green on the repo when a whole catalogue is on disk; skipped, never faked, otherwise."""
    repo = pathlib.Path(__file__).resolve().parents[1]
    monkeypatch.setattr(gate, "REPO_ROOT", repo)
    monkeypatch.setattr(gate, "DBT_DIR", repo / "dbt_project")
    monkeypatch.setattr(gate, "MODELS_DIR", repo / "dbt_project" / "models")
    monkeypatch.setattr(gate, "MIN_MODELS", 50)
    monkeypatch.setattr(gate, "MIN_LISTED_COLUMNS", 800)
    catalog = repo / "dbt_project" / "target" / "catalog.json"
    if not catalog.exists():
        pytest.skip("no catalog.json on disk")
    try:
        held = gate.catalog_columns(catalog).keys()
    except gate.Abort as exc:
        pytest.skip(f"catalog.json unreadable: {exc}")
    if gate.models_on_disk() - held:
        pytest.skip("catalog.json on disk is partial (a dev-target run), not the warehouse")
    assert gate.main(catalog) == 0
    assert capsys.readouterr().out.startswith("OK:")
