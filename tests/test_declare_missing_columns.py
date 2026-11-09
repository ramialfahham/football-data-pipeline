"""Tests for `scripts/declare_missing_columns.py`, driving `main()` against synthetic projects."""
from __future__ import annotations

import difflib
import json
import os
import pathlib
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import declare_missing_columns as gen  # noqa: E402


CORE_YML = """version: 2

models:
  - name: dim_thing
    description: >
      One row per thing.
    columns:
      - name: thing_sk
        description: "Identity key."
        tests: [not_null]
      - name: league_code
"""


def _project(tmp_path, ymls: dict[str, str], models: dict[str, str] | None = None):
    """`models` maps a model name to its layer directory; default: every yml model, in 3_core."""
    dbt = tmp_path / "dbt_project"
    if models is None:
        models = {}
        for body in ymls.values():
            doc = yaml.safe_load(body) or {}
            for model in doc.get("models") or []:
                models[model["name"]] = "3_core"
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
            "metadata": {"schema": "core", "name": model},
            "columns": {c: {"name": c, "index": i} for i, c in enumerate(cols)},
        }
        for model, cols in columns.items()
    }
    path = tmp_path / name
    path.write_text(json.dumps({"nodes": nodes, "sources": {}}), encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def _point_at_tmp(monkeypatch, tmp_path):
    """The discovery floor is lowered to 1 so tiny projects do not trip it."""
    monkeypatch.setattr(gen, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(gen, "DBT_DIR", tmp_path / "dbt_project")
    monkeypatch.setattr(gen, "MODELS_DIR", tmp_path / "dbt_project" / "models")
    monkeypatch.setattr(gen, "MIN_IN_SCOPE_MODELS", 1)


def _run(monkeypatch, catalog, *extra):
    monkeypatch.setattr(sys, "argv", ["declare_missing_columns.py",
                                      "--catalog", str(catalog), *extra])
    return gen.main()


def _assert_append_only(before: str, after: str):
    """Uses difflib directly because a check that validates itself proves nothing."""
    ops = difflib.SequenceMatcher(
        None, before.split("\n"), after.split("\n"), autojunk=False
    ).get_opcodes()
    assert [op[0] for op in ops if op[0] not in ("equal", "insert")] == []


def test_appends_names_to_an_existing_column_list(monkeypatch, tmp_path):
    dbt = _project(tmp_path, {"3_core/core.yml": CORE_YML})
    cat = _catalog(tmp_path, {"dim_thing": ["thing_sk", "league_code", "thing_name", "tier"]})
    before = (dbt / "models" / "3_core" / "core.yml").read_text(encoding="utf-8")

    assert _run(monkeypatch, cat) == 0

    after = (dbt / "models" / "3_core" / "core.yml").read_text(encoding="utf-8")
    _assert_append_only(before, after)
    doc = yaml.safe_load(after)
    assert [c["name"] for c in doc["models"][0]["columns"]] == [
        "thing_sk", "league_code", "thing_name", "tier",
    ]
    assert doc["models"][0]["columns"][0]["description"] == "Identity key."
    assert doc["models"][0]["columns"][0]["tests"] == ["not_null"]
    assert doc["models"][0]["columns"][2] == {"name": "thing_name"}
    assert doc["models"][0]["columns"][3] == {"name": "tier"}


def test_new_names_follow_the_warehouse_column_order(monkeypatch, tmp_path):
    dbt = _project(tmp_path, {"3_core/core.yml": CORE_YML})
    cat = _catalog(tmp_path, {"dim_thing": ["thing_sk", "league_code", "zzz", "aaa", "mmm"]})

    assert _run(monkeypatch, cat) == 0

    doc = yaml.safe_load((dbt / "models" / "3_core" / "core.yml").read_text(encoding="utf-8"))
    assert [c["name"] for c in doc["models"][0]["columns"][2:]] == ["zzz", "aaa", "mmm"]


def test_creates_a_columns_block_when_the_model_has_none(monkeypatch, tmp_path):
    body = "version: 2\n\nmodels:\n  - name: lonely\n    description: \"No columns yet.\"\n"
    dbt = _project(tmp_path, {"3_core/core.yml": body})
    cat = _catalog(tmp_path, {"lonely": ["a", "b"]})
    before = (dbt / "models" / "3_core" / "core.yml").read_text(encoding="utf-8")

    assert _run(monkeypatch, cat) == 0

    after = (dbt / "models" / "3_core" / "core.yml").read_text(encoding="utf-8")
    _assert_append_only(before, after)
    doc = yaml.safe_load(after)
    assert doc["models"][0]["columns"] == [{"name": "a"}, {"name": "b"}]
    assert doc["models"][0]["description"] == "No columns yet."


def test_a_model_whose_columns_are_all_declared_is_not_touched(monkeypatch, tmp_path):
    two = CORE_YML + """  - name: dim_other
    description: "Fully declared."
    columns:
      - name: other_sk
"""
    dbt = _project(tmp_path, {"3_core/core.yml": two})
    cat = _catalog(tmp_path, {
        "dim_thing": ["thing_sk", "league_code", "extra"],
        "dim_other": ["other_sk"],
    })

    assert _run(monkeypatch, cat) == 0

    doc = yaml.safe_load((dbt / "models" / "3_core" / "core.yml").read_text(encoding="utf-8"))
    other = [m for m in doc["models"] if m["name"] == "dim_other"][0]
    assert [c["name"] for c in other["columns"]] == ["other_sk"]


def test_a_declared_name_differing_only_in_case_is_not_redeclared(monkeypatch, tmp_path):
    body = "version: 2\n\nmodels:\n  - name: m\n    description: \"d\"\n    columns:\n      - name: Team_SK\n"
    dbt = _project(tmp_path, {"3_core/core.yml": body})
    cat = _catalog(tmp_path, {"m": ["team_sk", "new_one"]})

    assert _run(monkeypatch, cat) == 0

    doc = yaml.safe_load((dbt / "models" / "3_core" / "core.yml").read_text(encoding="utf-8"))
    assert [c["name"] for c in doc["models"][0]["columns"]] == ["Team_SK", "new_one"]


def test_nothing_to_add_exits_non_zero(monkeypatch, tmp_path, capsys):
    """Reporting success while matching nothing would hide a script that stopped matching."""
    _project(tmp_path, {"3_core/core.yml": CORE_YML})
    cat = _catalog(tmp_path, {"dim_thing": ["thing_sk", "league_code"]})

    assert _run(monkeypatch, cat) == 1
    assert "nothing to add" in capsys.readouterr().err


def test_refuses_a_catalogue_that_does_not_cover_every_in_scope_model(monkeypatch, tmp_path, capsys):
    """A stale dev catalog.json in dbt_project/target/ would declare almost nothing."""
    _project(tmp_path, {"3_core/core.yml": CORE_YML})
    cat = _catalog(tmp_path, {"some_other_model": ["a"]})

    assert _run(monkeypatch, cat) == 1
    err = capsys.readouterr().err
    assert "does not describe this warehouse" in err
    assert "dim_thing" in err


def test_refuses_a_model_that_is_declared_in_no_yml(monkeypatch, tmp_path, capsys):
    dbt = _project(tmp_path, {"3_core/core.yml": CORE_YML})
    (dbt / "models" / "3_core" / "orphan.sql").write_text("select 1\n", encoding="utf-8")
    cat = _catalog(tmp_path, {"dim_thing": ["thing_sk", "league_code"], "orphan": ["a"]})

    assert _run(monkeypatch, cat) == 1
    assert "in no yml at all" in capsys.readouterr().err


def test_refuses_a_columns_key_that_is_not_a_bare_key(monkeypatch, tmp_path, capsys):
    """An inline list gives no line to append after, so the script must refuse."""
    body = "version: 2\n\nmodels:\n  - name: m\n    description: \"d\"\n    columns: []\n"
    _project(tmp_path, {"3_core/core.yml": body})
    cat = _catalog(tmp_path, {"m": ["a"]})

    assert _run(monkeypatch, cat) == 1
    assert "not a bare key" in capsys.readouterr().err


def test_refuses_a_model_declared_in_two_ymls(monkeypatch, tmp_path, capsys):
    other = "version: 2\n\nmodels:\n  - name: dim_thing\n    description: \"dupe\"\n"
    _project(tmp_path, {"3_core/core.yml": CORE_YML, "3_core/dupe.yml": other})
    cat = _catalog(tmp_path, {"dim_thing": ["thing_sk", "league_code", "new"]})

    assert _run(monkeypatch, cat) == 1
    assert "declared twice" in capsys.readouterr().err


def test_the_discovery_floor_fires_on_a_broken_walk(monkeypatch, tmp_path, capsys):
    """The floor keeps its real value only here; a broken walk makes "nothing missing" trivially true."""
    monkeypatch.setattr(gen, "MIN_IN_SCOPE_MODELS", 40)
    _project(tmp_path, {"3_core/core.yml": CORE_YML})
    cat = _catalog(tmp_path, {"dim_thing": ["thing_sk", "league_code", "new"]})

    assert _run(monkeypatch, cat) == 1
    assert "Refusing to run against a broken walk" in capsys.readouterr().err


def test_dry_run_writes_nothing(monkeypatch, tmp_path):
    dbt = _project(tmp_path, {"3_core/core.yml": CORE_YML})
    cat = _catalog(tmp_path, {"dim_thing": ["thing_sk", "league_code", "new"]})
    before = (dbt / "models" / "3_core" / "core.yml").read_text(encoding="utf-8")

    assert _run(monkeypatch, cat, "--dry-run") == 0

    assert (dbt / "models" / "3_core" / "core.yml").read_text(encoding="utf-8") == before


def test_a_second_run_finds_nothing_and_says_so(monkeypatch, tmp_path, capsys):
    """'nothing to add' on the second run is the signal that the first run already worked."""
    _project(tmp_path, {"3_core/core.yml": CORE_YML})
    cat = _catalog(tmp_path, {"dim_thing": ["thing_sk", "league_code", "new"]})

    assert _run(monkeypatch, cat) == 0
    capsys.readouterr()
    assert _run(monkeypatch, cat) == 1
    assert "nothing to add" in capsys.readouterr().err


@pytest.mark.parametrize("newline", ["\r\n", "\n"])
def test_the_files_existing_line_endings_are_preserved(monkeypatch, tmp_path, newline):
    """Converting line terminators reformats every line while `git diff` hides it."""
    body = CORE_YML.replace("\n", newline)
    dbt = tmp_path / "dbt_project"
    d = dbt / "models" / "3_core"
    d.mkdir(parents=True)
    (d / "dim_thing.sql").write_text("select 1\n", encoding="utf-8")
    # newline="" stops the fixture's terminators being translated to os.linesep.
    (d / "core.yml").write_text(body, encoding="utf-8", newline="")
    cat = _catalog(tmp_path, {"dim_thing": ["thing_sk", "league_code", "brand_new"]})

    assert _run(monkeypatch, cat) == 0

    raw = (d / "core.yml").read_bytes()
    crlf = raw.count(b"\r\n")
    bare_lf = raw.count(b"\n") - crlf
    if newline == "\r\n":
        assert bare_lf == 0, f"CRLF file gained {bare_lf} bare LF terminators"
        assert crlf > 0
    else:
        assert crlf == 0, f"LF file gained {crlf} CRLF terminators"
    assert b"brand_new" in raw


def test_refuses_a_file_with_mixed_line_endings(monkeypatch, tmp_path, capsys):
    """Mixed endings leave no existing terminator to preserve, so the script must refuse."""
    body = CORE_YML.replace("\n", "\r\n").replace("    columns:\r\n", "    columns:\n")
    dbt = tmp_path / "dbt_project"
    d = dbt / "models" / "3_core"
    d.mkdir(parents=True)
    (d / "dim_thing.sql").write_text("select 1\n", encoding="utf-8")
    (d / "core.yml").write_text(body, encoding="utf-8", newline="")
    cat = _catalog(tmp_path, {"dim_thing": ["thing_sk", "league_code", "brand_new"]})

    assert _run(monkeypatch, cat) == 1
    assert "mixed line endings" in capsys.readouterr().err


def test_a_failure_at_the_commit_point_leaves_the_original_intact(monkeypatch, tmp_path, capsys):
    """Atomicity is asserted via the rename commit: if it fails, the original is byte-identical."""
    dbt = _project(tmp_path, {"3_core/core.yml": CORE_YML})
    target = dbt / "models" / "3_core" / "core.yml"
    before = target.read_bytes()
    cat = _catalog(tmp_path, {"dim_thing": ["thing_sk", "league_code", "brand_new"]})

    def boom(src, dst):
        raise OSError("simulated failure at the commit point")

    monkeypatch.setattr(gen.os, "replace", boom)

    assert _run(monkeypatch, cat) == 1
    assert target.read_bytes() == before, "the original was modified despite the failure"
    assert "the original is untouched" in capsys.readouterr().err
    assert list(target.parent.glob("*.tmp")) == [], "a temp file was left behind"


def test_a_successful_run_leaves_no_temp_files(monkeypatch, tmp_path):
    dbt = _project(tmp_path, {"3_core/core.yml": CORE_YML})
    cat = _catalog(tmp_path, {"dim_thing": ["thing_sk", "league_code", "brand_new"]})

    assert _run(monkeypatch, cat) == 0

    assert list((dbt / "models" / "3_core").glob("*.tmp")) == []
    # A surviving temp file must not parse as a schema file, or it would redeclare every model.
    assert not pathlib.Path("core.yml.tmp").match("*.yml")


# ---------------------------------------------------------------- --wire-shared-docs

WIRE_YML = """version: 2

models:
  - name: m
    description: "A model."
    columns:
      - name: team_sk
      - name: league_code
        description: "{{ doc('league_code_ingest_provenance') }}"
      - name: own_text
        description: "Not a shared name."
      - name: season_sk
        tests: [not_null]
"""


def _blocks_md(dbt, names, where="models/docs/shared_columns.md"):
    path = dbt / where
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n\n".join("{%% docs %s %%}\nText for %s.\n{%% enddocs %%}" % (n, n) for n in names)
    path.write_text(body + "\n", encoding="utf-8")
    return path


def _run_wire(monkeypatch, *extra):
    monkeypatch.setattr(sys, "argv",
                        ["declare_missing_columns.py", "--wire-shared-docs", *extra])
    return gen.main()


def test_wire_points_a_blank_shared_name_column_at_its_block(monkeypatch, tmp_path):
    dbt = _project(tmp_path, {"3_core/core.yml": WIRE_YML}, models={"m": "3_core"})
    _blocks_md(dbt, ["team_sk", "league_code", "league_code_ingest_provenance", "season_sk"])
    target = dbt / "models" / "3_core" / "core.yml"
    before = target.read_text(encoding="utf-8")

    assert _run_wire(monkeypatch) == 0

    after = target.read_text(encoding="utf-8")
    _assert_append_only(before, after)
    cols = {c["name"]: c for c in yaml.safe_load(after)["models"][0]["columns"]}
    assert cols["team_sk"]["description"] == "{{ doc('team_sk') }}"
    assert cols["season_sk"]["description"] == "{{ doc('season_sk') }}"
    assert cols["season_sk"]["tests"] == ["not_null"]


def test_wire_never_touches_a_column_that_already_has_text(monkeypatch, tmp_path):
    """A column pointing at a different block must not be dragged back to its own name's block."""
    dbt = _project(tmp_path, {"3_core/core.yml": WIRE_YML}, models={"m": "3_core"})
    _blocks_md(dbt, ["team_sk", "league_code", "league_code_ingest_provenance", "season_sk"])
    target = dbt / "models" / "3_core" / "core.yml"

    assert _run_wire(monkeypatch) == 0

    cols = {c["name"]: c for c in yaml.safe_load(target.read_text(encoding="utf-8"))["models"][0]["columns"]}
    assert cols["league_code"]["description"] == "{{ doc('league_code_ingest_provenance') }}"
    assert cols["own_text"]["description"] == "Not a shared name."


def test_wire_indent_follows_the_file_rather_than_a_constant(monkeypatch, tmp_path):
    body = ("version: 2\n\nmodels:\n  - name: m\n    description: \"d\"\n"
            "    columns:\n        - name: team_sk\n")
    dbt = _project(tmp_path, {"3_core/core.yml": body}, models={"m": "3_core"})
    _blocks_md(dbt, ["team_sk"])

    assert _run_wire(monkeypatch) == 0

    text = (dbt / "models" / "3_core" / "core.yml").read_text(encoding="utf-8")
    assert "          description: \"{{ doc('team_sk') }}\"" in text
    assert yaml.safe_load(text)["models"][0]["columns"][0]["description"] == "{{ doc('team_sk') }}"


def test_wire_ignores_a_block_outside_models(monkeypatch, tmp_path, capsys):
    """dbt's `docs-paths` defaults to `models/`, so a block elsewhere renders as literal text."""
    dbt = _project(tmp_path, {"3_core/core.yml": WIRE_YML}, models={"m": "3_core"})
    _blocks_md(dbt, ["season_sk"])
    _blocks_md(dbt, ["team_sk"], where="docs/engineering_standards.md")

    assert _run_wire(monkeypatch) == 0

    cols = {c["name"]: c for c in yaml.safe_load(
        (dbt / "models" / "3_core" / "core.yml").read_text(encoding="utf-8"))["models"][0]["columns"]}
    assert cols["season_sk"]["description"] == "{{ doc('season_sk') }}"
    assert "description" not in cols["team_sk"], "wired to a block dbt cannot resolve"


def test_wire_ignores_docs_text_with_no_enddocs(monkeypatch, tmp_path, capsys):
    """Without a closing tag a `{% docs name %}` in a sentence is prose, not a block."""
    dbt = _project(tmp_path, {"3_core/core.yml": WIRE_YML}, models={"m": "3_core"})
    md = dbt / "models" / "docs" / "shared_columns.md"
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(
        "Long text belongs in a docs block, {% docs team_sk %} in a .md file.\n\n"
        "{% docs season_sk %}\nReal one.\n{% enddocs %}\n", encoding="utf-8")

    assert _run_wire(monkeypatch) == 0

    cols = {c["name"]: c for c in yaml.safe_load(
        (dbt / "models" / "3_core" / "core.yml").read_text(encoding="utf-8"))["models"][0]["columns"]}
    assert cols["season_sk"]["description"] == "{{ doc('season_sk') }}"
    assert "description" not in cols["team_sk"], "prose read as a real block"


AMBIGUOUS_YML = """version: 2

models:
  - name: identity_model
    description: "The competition a row belongs to."
    columns:
      - name: league_code
        description: "{{ doc('league_code') }}"
  - name: provenance_model
    description: "league_code here is ingest provenance, not identity."
    columns:
      - name: league_code
        description: "{{ doc('league_code_ingest_provenance') }}"
  - name: blank_model
    description: "Has a blank one."
    columns:
      - name: league_code
      - name: team_sk
"""


def test_wire_withholds_a_name_that_already_means_two_things(monkeypatch, tmp_path, capsys):
    """Wiring matches a name to a block, so a name with two blocks is withheld, not guessed."""
    dbt = _project(tmp_path, {"3_core/core.yml": AMBIGUOUS_YML},
                   models={"identity_model": "3_core", "provenance_model": "3_core",
                           "blank_model": "3_core"})
    _blocks_md(dbt, ["league_code", "league_code_ingest_provenance", "team_sk"])
    target = dbt / "models" / "3_core" / "core.yml"

    assert _run_wire(monkeypatch) == 0

    out = capsys.readouterr().out
    assert "WITHHELD" in out
    assert "league_code already means 2 different things" in out

    models = {m["name"]: {c["name"]: c for c in m["columns"]}
              for m in yaml.safe_load(target.read_text(encoding="utf-8"))["models"]}
    assert "description" not in models["blank_model"]["league_code"], \
        "guessed at a name that already carries two meanings"
    assert models["blank_model"]["team_sk"]["description"] == "{{ doc('team_sk') }}"


def test_wire_refuses_when_no_blocks_exist_at_all(monkeypatch, tmp_path, capsys):
    """With an empty block set, "nothing to wire" would be trivially true."""
    _project(tmp_path, {"3_core/core.yml": WIRE_YML}, models={"m": "3_core"})

    assert _run_wire(monkeypatch) == 1
    assert "refusing to run against an empty block set" in capsys.readouterr().err


def test_wire_nothing_to_do_exits_non_zero(monkeypatch, tmp_path, capsys):
    dbt = _project(tmp_path, {"3_core/core.yml": WIRE_YML}, models={"m": "3_core"})
    _blocks_md(dbt, ["team_sk", "league_code", "league_code_ingest_provenance", "season_sk"])

    assert _run_wire(monkeypatch) == 0
    capsys.readouterr()
    assert _run_wire(monkeypatch) == 1
    assert "nothing to wire" in capsys.readouterr().err


def test_wire_dry_run_writes_nothing(monkeypatch, tmp_path):
    dbt = _project(tmp_path, {"3_core/core.yml": WIRE_YML}, models={"m": "3_core"})
    _blocks_md(dbt, ["team_sk", "season_sk"])
    target = dbt / "models" / "3_core" / "core.yml"
    before = target.read_text(encoding="utf-8")

    assert _run_wire(monkeypatch, "--dry-run") == 0

    assert target.read_text(encoding="utf-8") == before


def test_other_models_in_the_same_file_are_untouched(monkeypatch, tmp_path):
    """Insertion is bottom-up so one model's new lines cannot shift another's anchor."""
    two = CORE_YML + """  - name: dim_other
    description: "Second in the file."
    columns:
      - name: other_sk
        tests: [not_null]
"""
    dbt = _project(tmp_path, {"3_core/core.yml": two})
    cat = _catalog(tmp_path, {
        "dim_thing": ["thing_sk", "league_code", "t_new"],
        "dim_other": ["other_sk", "o_new"],
    })
    before = (dbt / "models" / "3_core" / "core.yml").read_text(encoding="utf-8")

    assert _run(monkeypatch, cat) == 0

    after = (dbt / "models" / "3_core" / "core.yml").read_text(encoding="utf-8")
    _assert_append_only(before, after)
    doc = yaml.safe_load(after)
    got = {m["name"]: [c["name"] for c in m["columns"]] for m in doc["models"]}
    assert got == {
        "dim_thing": ["thing_sk", "league_code", "t_new"],
        "dim_other": ["other_sk", "o_new"],
    }


# ------------------------------------------------- --wire-metric-docs
#
# A derived column name has no bare block, only `__team` and/or `__player`; choosing between
# them is what this mode does, and a wrong choice is invisible because the block still resolves.

METRIC_YML = """version: 2

models:
  - name: mart_team_profile
    columns:
      - name: goals_against_this_season
      - name: assists_this_season
"""


def _run_metric_wire(monkeypatch, *extra):
    monkeypatch.setattr(sys, "argv",
                        ["declare_missing_columns.py", "--wire-metric-docs", *extra])
    return gen.main()


def test_metric_wire_picks_the_block_for_the_MODELS_entity(monkeypatch, tmp_path):
    """Both entities' blocks exist for the name, so only consulting MODEL_ENTITY can pass."""
    dbt = _project(tmp_path, {"5_marts/shared/shared.yml": METRIC_YML},
                   models={"mart_team_profile": "5_marts/shared"})
    _blocks_md(dbt, ["goals_against_this_season__team", "goals_against_this_season__player",
                     "assists_this_season__team"])
    target = dbt / "models" / "5_marts" / "shared" / "shared.yml"
    before = target.read_text(encoding="utf-8")

    assert _run_metric_wire(monkeypatch) == 0

    after = target.read_text(encoding="utf-8")
    _assert_append_only(before, after)
    cols = {c["name"]: c for c in yaml.safe_load(after)["models"][0]["columns"]}
    assert cols["goals_against_this_season"]["description"] == \
        "{{ doc('goals_against_this_season__team') }}"


def test_metric_wire_refuses_a_model_it_has_no_entity_for(monkeypatch, tmp_path, capsys):
    """Defaulting would attach the wrong definition, so an unknown model stops the run."""
    yml = METRIC_YML.replace("mart_team_profile", "mart_something_new")
    dbt = _project(tmp_path, {"5_marts/shared/shared.yml": yml},
                   models={"mart_something_new": "5_marts/shared"})
    _blocks_md(dbt, ["goals_against_this_season__team", "assists_this_season__player"])

    assert _run_metric_wire(monkeypatch) == 1
    err = capsys.readouterr().err
    assert "MODEL_ENTITY" in err and "mart_something_new" in err


def test_metric_wire_REPORTS_a_column_with_no_block_for_its_entity(
        monkeypatch, tmp_path, capsys):
    """The catalogue never defined the metric for that entity, so the column stays blank."""
    dbt = _project(tmp_path, {"5_marts/shared/shared.yml": METRIC_YML},
                   models={"mart_team_profile": "5_marts/shared"})
    _blocks_md(dbt, ["goals_against_this_season__player", "assists_this_season__team"])
    target = dbt / "models" / "5_marts" / "shared" / "shared.yml"

    assert _run_metric_wire(monkeypatch) == 0

    out = capsys.readouterr().out
    assert "LEFT BLANK" in out and "goals_against_this_season__team" in out
    cols = {c["name"]: c for c in
            yaml.safe_load(target.read_text(encoding="utf-8"))["models"][0]["columns"]}
    assert "description" not in cols["goals_against_this_season"]
    assert cols["assists_this_season"]["description"] == \
        "{{ doc('assists_this_season__team') }}"


def test_metric_wire_leaves_a_column_that_already_has_text(monkeypatch, tmp_path):
    yml = METRIC_YML.replace(
        "      - name: assists_this_season\n",
        "      - name: assists_this_season\n        description: \"Its own sentence.\"\n")
    dbt = _project(tmp_path, {"5_marts/shared/shared.yml": yml},
                   models={"mart_team_profile": "5_marts/shared"})
    _blocks_md(dbt, ["goals_against_this_season__team", "assists_this_season__team"])
    target = dbt / "models" / "5_marts" / "shared" / "shared.yml"

    assert _run_metric_wire(monkeypatch) == 0

    cols = {c["name"]: c for c in
            yaml.safe_load(target.read_text(encoding="utf-8"))["models"][0]["columns"]}
    assert cols["assists_this_season"]["description"] == "Its own sentence."


def test_the_two_wire_modes_together_are_refused(monkeypatch, tmp_path, capsys):
    """Two passes over the same files in one run makes the diff unattributable."""
    monkeypatch.setattr(sys, "argv", ["declare_missing_columns.py",
                                      "--wire-shared-docs", "--wire-metric-docs"])
    assert gen.main() == 1
    assert "one at a time" in capsys.readouterr().err


# ---------------------------------------------- --promote-shared-docs
#
# The only mode that edits an existing line; it claims the block's text equals the column's text.

PROMOTE_YML = """version: 2

models:
  - name: dim_thing
    columns:
      - name: shared_col
        description: "The shared sentence."
      - name: other_col
        description: "Something else entirely."
"""


def _run_promote(monkeypatch, *extra):
    monkeypatch.setattr(sys, "argv",
                        ["declare_missing_columns.py", "--promote-shared-docs", *extra])
    return gen.main()


def _blocks_text(dbt, bodies, where="models/docs/shared_columns.md"):
    path = dbt / where
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n\n".join("{%% docs %s %%}\n%s\n{%% enddocs %%}" % (n, b)
                    for n, b in bodies.items()) + "\n",
        encoding="utf-8")
    return path


def test_promote_replaces_a_restatement_with_a_reference(monkeypatch, tmp_path):
    dbt = _project(tmp_path, {"3_core/core.yml": PROMOTE_YML}, models={"dim_thing": "3_core"})
    _blocks_text(dbt, {"shared_col": "The shared sentence."})
    target = dbt / "models" / "3_core" / "core.yml"

    assert _run_promote(monkeypatch) == 0

    cols = {c["name"]: c for c in
            yaml.safe_load(target.read_text(encoding="utf-8"))["models"][0]["columns"]}
    assert cols["shared_col"]["description"] == "{{ doc('shared_col') }}"
    assert cols["other_col"]["description"] == "Something else entirely."


def test_promote_REFUSES_a_site_whose_text_is_not_the_blocks_text(
        monkeypatch, tmp_path, capsys):
    """If the block says something else, swapping in the reference would rewrite the column."""
    dbt = _project(tmp_path, {"3_core/core.yml": PROMOTE_YML}, models={"dim_thing": "3_core"})
    _blocks_text(dbt, {"shared_col": "A DIFFERENT sentence with the same name."})
    target = dbt / "models" / "3_core" / "core.yml"
    before = target.read_text(encoding="utf-8")

    assert _run_promote(monkeypatch) == 1          # nothing left to do, and loud
    out = capsys.readouterr()
    assert "NOT the block's text" in out.out
    assert target.read_text(encoding="utf-8") == before


def test_promote_REFUSES_a_folded_description(monkeypatch, tmp_path, capsys):
    """A folded scalar spans several lines and the script edits by line, so a human handles it."""
    yml = PROMOTE_YML.replace(
        '      - name: shared_col\n        description: "The shared sentence."\n',
        "      - name: shared_col\n        description: >\n          The shared\n"
        "          sentence.\n")
    dbt = _project(tmp_path, {"3_core/core.yml": yml}, models={"dim_thing": "3_core"})
    _blocks_text(dbt, {"shared_col": "The shared sentence."})
    target = dbt / "models" / "3_core" / "core.yml"
    before = target.read_text(encoding="utf-8")

    assert _run_promote(monkeypatch) == 1
    assert "folded scalar is for a human" in capsys.readouterr().out
    assert target.read_text(encoding="utf-8") == before


def test_promote_finds_the_line_inside_ITS_OWN_model(monkeypatch, tmp_path):
    """The same sentence under several models is ambiguous in a file-wide search."""
    yml = PROMOTE_YML + """
  - name: dim_other
    columns:
      - name: shared_col
        description: "The shared sentence."
"""
    dbt = _project(tmp_path, {"3_core/core.yml": yml},
                   models={"dim_thing": "3_core", "dim_other": "3_core"})
    _blocks_text(dbt, {"shared_col": "The shared sentence."})
    target = dbt / "models" / "3_core" / "core.yml"

    assert _run_promote(monkeypatch) == 0

    doc = yaml.safe_load(target.read_text(encoding="utf-8"))
    got = {m["name"]: {c["name"]: c.get("description") for c in m["columns"]}
           for m in doc["models"]}
    assert got["dim_thing"]["shared_col"] == "{{ doc('shared_col') }}"
    assert got["dim_other"]["shared_col"] == "{{ doc('shared_col') }}"


def test_promote_handles_a_description_that_is_not_the_first_line_of_its_column(
        monkeypatch, tmp_path):
    """`name`, `tests`, `description` is legal YAML; the description need not follow the name."""
    yml = """version: 2

models:
  - name: dim_thing
    columns:
      - name: shared_col
        tests: [not_null]
        description: "The shared sentence."
"""
    dbt = _project(tmp_path, {"3_core/core.yml": yml}, models={"dim_thing": "3_core"})
    _blocks_text(dbt, {"shared_col": "The shared sentence."})
    target = dbt / "models" / "3_core" / "core.yml"

    assert _run_promote(monkeypatch) == 0

    col = yaml.safe_load(target.read_text(encoding="utf-8"))["models"][0]["columns"][0]
    assert col["description"] == "{{ doc('shared_col') }}"
    assert col["tests"] == ["not_null"]


def test_promote_refuses_when_the_planned_line_is_no_longer_there(monkeypatch, tmp_path):
    """If the file changed after planning, an unexamined line must not be overwritten."""
    lines = ['      - name: shared_col', '        description: "Something else."']
    with pytest.raises(gen.Abort) as exc:
        gen._replace_description(
            ["models:", "  - name: dim_thing", "    columns:", *lines],
            "dim_thing",
            {"shared_col": ("shared_col", '        description: "The planned line."')})
    assert "found 0" in str(exc.value)


def test_verify_still_refuses_a_replace_the_run_did_not_plan():
    """A replace outside the planned set is still refused; an empty set means append-only."""
    before = 'a: 1\nb: 2\nc: 3\n'
    after = 'a: 1\nb: CHANGED\nc: 3\n'
    expected = yaml.safe_load(after)

    with pytest.raises(gen.Abort) as exc:
        gen._verify(before, after, expected, "f.yml", "\n", frozenset())
    assert "not append-only" in str(exc.value)

    gen._verify(before, after, expected, "f.yml", "\n", frozenset({"b: 2"}))

    with pytest.raises(gen.Abort):
        gen._verify(before, after, expected, "f.yml", "\n", frozenset({"c: 3"}))


def test_an_unplanned_line_cannot_ride_along_inside_a_planned_replace():
    """Every old line inside one multi-line `replace` opcode must have been planned."""
    before = "a: 1\nb: 2\nc: 3\nd: 4\n"
    after = "a: 1\nb: CHANGED\nc: ALSO CHANGED\nd: 4\n"
    expected = yaml.safe_load(after)

    gen._verify(before, after, expected, "f.yml", "\n", frozenset({"b: 2", "c: 3"}))

    for planned in (frozenset({"b: 2"}), frozenset({"c: 3"})):
        with pytest.raises(gen.Abort) as exc:
            gen._verify(before, after, expected, "f.yml", "\n", planned)
        assert "unexpected edit" in str(exc.value)


def test_promote_refuses_to_run_alongside_another_mode(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["declare_missing_columns.py",
                                      "--promote-shared-docs", "--wire-shared-docs"])
    assert gen.main() == 1
    assert "one mode at a time" in capsys.readouterr().err


def test_every_MODEL_ENTITY_key_names_a_model_that_exists():
    """A stale entry is a silent no-op; runs against the real repo with no monkeypatching."""
    import importlib

    fresh = importlib.reload(gen)
    on_disk = {p.stem for p in (fresh.MODELS_DIR).rglob("*.sql")}
    missing = sorted(set(fresh.MODEL_ENTITY) - on_disk)
    assert not missing, (
        "MODEL_ENTITY names models that do not exist: " + ", ".join(missing))
    assert set(fresh.MODEL_ENTITY.values()) == {"team", "player"}
