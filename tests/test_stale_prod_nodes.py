"""scripts/stale_prod_nodes.py — the prod models a cut-short prod build left older than their inputs."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("stale_prod_nodes", REPO_ROOT / "scripts" / "stale_prod_nodes.py")
stale_prod_nodes = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stale_prod_nodes)

PROJECT = "proj"


def _model(name: str, schema: str, parents: list[str], materialized: str = "table") -> dict:
    return {
        "resource_type": "model",
        "name": name,
        "schema": schema,
        "database": PROJECT,
        "config": {"materialized": materialized},
        "depends_on": {"nodes": parents},
    }


def _manifest() -> dict:
    return {
        "nodes": {
            "seed.s": {"resource_type": "seed", "name": "s", "depends_on": {"nodes": []}},
            "model.a": _model("a", "staging", ["seed.s", "source.raw"]),
            "model.v": _model("v", "staging", ["model.a"], materialized="view"),
            "model.b": _model("b", "core", ["model.v"]),
            "model.c": _model("c", "marts", ["model.b"]),
            "model.d": _model("d", "marts", ["seed.s"]),
        }
    }


def _times(a: int, b: int, c: int, d: int = 10) -> dict:
    return {("staging", "a"): a, ("staging", "v"): 1, ("core", "b"): b, ("marts", "c"): c, ("marts", "d"): d}


def test_a_whole_build_has_no_stale_model():
    assert stale_prod_nodes.stale_models(_manifest(), _times(a=100, b=110, c=120)) == []


def test_models_skipped_after_an_upstream_rebuild_are_stale():
    assert stale_prod_nodes.stale_models(_manifest(), _times(a=200, b=110, c=120)) == ["b"]
    assert stale_prod_nodes.stale_models(_manifest(), _times(a=200, b=110, c=105)) == ["b", "c"]


def test_a_view_is_looked_through_to_its_table_parents():
    times = _times(a=100, b=110, c=120)
    times[("staging", "v")] = 999
    assert stale_prod_nodes.stale_models(_manifest(), times) == []


def test_a_seed_never_makes_a_model_stale():
    times = _times(a=100, b=110, c=120)
    times[("staging", "s")] = 999
    assert stale_prod_nodes.stale_models(_manifest(), times) == []


def test_a_model_missing_from_the_warehouse_is_stale():
    times = _times(a=100, b=110, c=120)
    del times[("core", "b")]
    assert stale_prod_nodes.stale_models(_manifest(), times) == ["b"]


def test_a_view_is_never_itself_listed():
    times = _times(a=100, b=110, c=120)
    del times[("staging", "v")]
    assert stale_prod_nodes.stale_models(_manifest(), times) == []


def test_an_alias_names_the_relation():
    manifest = _manifest()
    manifest["nodes"]["model.b"]["alias"] = "b_table"
    times = _times(a=100, b=0, c=120)
    times[("core", "b_table")] = 110
    assert stale_prod_nodes.stale_models(manifest, times) == []


def _client(rows):
    client = SimpleNamespace()
    client.query = lambda sql: SimpleNamespace(result=lambda: rows, sql=sql)
    return client


def test_last_modified_reads_the_metadata_of_each_dataset_once():
    seen = []
    rows = [SimpleNamespace(dataset="core", table_id="b", last_modified_time="110")]

    def query(sql):
        seen.append(sql)
        return SimpleNamespace(result=lambda: rows)

    client = SimpleNamespace(query=query)
    assert stale_prod_nodes.last_modified(client, _manifest()) == {("core", "b"): 110}
    assert len(seen) == 1
    for dataset in ("staging", "core", "marts"):
        assert f"`proj.{dataset}.__TABLES__`" in seen[0]


def test_a_schema_that_is_not_an_identifier_is_refused():
    manifest = _manifest()
    manifest["nodes"]["model.b"]["schema"] = "core`; drop"
    with pytest.raises(ValueError):
        stale_prod_nodes.last_modified(_client([]), manifest)


def test_main_prints_one_selection_line(tmp_path, monkeypatch, capsys):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(_manifest()), encoding="utf-8")
    monkeypatch.setattr(stale_prod_nodes, "last_modified", lambda client, manifest: _times(a=200, b=110, c=105))
    monkeypatch.setattr(stale_prod_nodes.bigquery, "Client", lambda project: object())
    assert stale_prod_nodes.main(["stale_prod_nodes.py", str(path)]) == 0
    out = capsys.readouterr()
    assert out.out == "b+ c+\n"
    assert "2 stale prod model(s): b, c" in out.err


def test_main_prints_an_empty_selection_when_nothing_is_stale(tmp_path, monkeypatch, capsys):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(_manifest()), encoding="utf-8")
    monkeypatch.setattr(stale_prod_nodes, "last_modified", lambda client, manifest: _times(a=100, b=110, c=120))
    monkeypatch.setattr(stale_prod_nodes.bigquery, "Client", lambda project: object())
    assert stale_prod_nodes.main(["stale_prod_nodes.py", str(path)]) == 0
    assert capsys.readouterr().out == "\n"
