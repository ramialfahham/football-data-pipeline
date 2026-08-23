"""Tests for `scripts/declare_missing_columns.py`.

The point is not that the script runs on today's repo. It does, and a test
asserting that would stay green while the script quietly stopped matching
anything, which is the failure this repo keeps hitting (#904) and the exact
failure this script's own "nothing to add" guard exists to prevent.

So each test drives `main()` against a synthetic project and asserts one thing
the script MUST refuse, or one property of what it writes. The append-only
property is asserted independently with `difflib` rather than by calling the
script's own `_verify`, because a check that validates itself proves nothing.
"""
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
    """A minimal dbt project: one .sql per model, plus the schema files given.

    `models` maps a model name to the layer directory it lives in; it defaults to
    every model named in the ymls, in 3_core.
    """
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
    """A catalog.json holding exactly the models and column orders given."""
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
    """Every test supplies a two-or-three model project, so the discovery floor
    would fire on all of them and mask what is being tested. It keeps its real
    value in `test_the_discovery_floor_fires_on_a_broken_walk`, which is the only
    place it is asserted, and the script runs it at full strength for real."""
    monkeypatch.setattr(gen, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(gen, "DBT_DIR", tmp_path / "dbt_project")
    monkeypatch.setattr(gen, "MODELS_DIR", tmp_path / "dbt_project" / "models")
    monkeypatch.setattr(gen, "MIN_IN_SCOPE_MODELS", 1)


def _run(monkeypatch, catalog, *extra):
    monkeypatch.setattr(sys, "argv", ["declare_missing_columns.py",
                                      "--catalog", str(catalog), *extra])
    return gen.main()


def _assert_append_only(before: str, after: str):
    """No line was deleted, changed or moved. Asserted with difflib directly, not
    with the script's own verifier."""
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
    # The names that were already there keep their description and tests.
    assert doc["models"][0]["columns"][0]["description"] == "Identity key."
    assert doc["models"][0]["columns"][0]["tests"] == ["not_null"]
    # The new ones carry a name and nothing else. "No thin filler" (CPO 2026-08-21)
    # is enforced here rather than trusted: a description invented by a generator
    # is the worst kind.
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
    """A bulk-edit script that reports success while matching nothing is the
    handover's trap 2 and #904's dominant shape. Silence here would be the bug."""
    _project(tmp_path, {"3_core/core.yml": CORE_YML})
    cat = _catalog(tmp_path, {"dim_thing": ["thing_sk", "league_code"]})

    assert _run(monkeypatch, cat) == 1
    assert "nothing to add" in capsys.readouterr().err


def test_refuses_a_catalogue_that_does_not_cover_every_in_scope_model(monkeypatch, tmp_path, capsys):
    """The stale dev catalog.json sitting in dbt_project/target/ describes 10
    relations in dev schemas. Running against it would declare almost nothing."""
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
    """An inline list gives no line to append after, so the script must refuse
    rather than guess where the list ends."""
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
    """The floor keeps its REAL value here and nowhere else. A renamed layer
    directory leaves the walk matching nothing, and "no missing columns" then
    becomes trivially true."""
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
    """Idempotence, and the shape of it. The second run must not be silently
    green: 'nothing to add' is the signal that the first run already worked."""
    _project(tmp_path, {"3_core/core.yml": CORE_YML})
    cat = _catalog(tmp_path, {"dim_thing": ["thing_sk", "league_code", "new"]})

    assert _run(monkeypatch, cat) == 0
    capsys.readouterr()
    assert _run(monkeypatch, cat) == 1
    assert "nothing to add" in capsys.readouterr().err


@pytest.mark.parametrize("newline", ["\r\n", "\n"])
def test_the_files_existing_line_endings_are_preserved(monkeypatch, tmp_path, newline):
    """Converting every line terminator IS reformatting every line, even though
    `git diff` hides it: `core.autocrlf=true` here and `.gitattributes` pins only
    `*.sh` and `Dockerfile`, so these ymls are CRLF in the working tree and LF in
    the object store. The diff therefore shows zero deletions either way, and the
    rewrite is invisible in exactly the place you would look for it.

    That is not hypothetical in this repo. `.gitattributes` exists because a
    CRLF working copy shipped `\\r` into a container shebang under #39 and died at
    04:00 in production, having passed every test and built a clean image.

    This test caught the real thing: the first version of the script read with
    universal newlines and wrote LF, silently converting all 14 files."""
    body = CORE_YML.replace("\n", newline)
    dbt = tmp_path / "dbt_project"
    d = dbt / "models" / "3_core"
    d.mkdir(parents=True)
    (d / "dim_thing.sql").write_text("select 1\n", encoding="utf-8")
    # newline="" so the fixture's terminators survive being written, rather than
    # being translated to os.linesep on the way to disk.
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
    """Nothing here has mixed endings today. If one ever does, there is no
    "existing terminator" to preserve, so the script must refuse rather than pick
    one and rewrite half the file."""
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
    """platform-reviewer's round-1 FAIL. `open(path, "w")` truncates at open time,
    so a crash between the truncate and the last write leaves a TRACKED yml
    half-written. `_verify` cannot catch that: it compares two in-memory strings
    and has already returned before any byte moves.

    Atomicity is untestable by actually killing the process, so this asserts the
    property that makes it atomic: the file is committed by a rename, and if that
    rename fails the original is still byte-identical."""
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
    # The temp name must not be parseable as a schema file even if one survives a
    # crash, or the next run would read it as a second declaration of every model.
    assert not pathlib.Path("core.yml.tmp").match("*.yml")


def test_other_models_in_the_same_file_are_untouched(monkeypatch, tmp_path):
    """Insertion is bottom-up so one model's new lines cannot shift another's
    anchor. Two models in one file, both gaining columns, is the case that breaks
    if that ordering is wrong."""
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
