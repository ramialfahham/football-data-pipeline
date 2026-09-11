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
    # The new ones carry a name and nothing else. "No thin filler" is enforced here
    # rather than trusted: a description invented by a generator
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
    """`open(path, "w")` truncates at open time, so a crash between the truncate
    and the last write leaves a TRACKED yml
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
    """A .md holding one real `{% docs %}` block per name given."""
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
    # tests: survives alongside the new description
    assert cols["season_sk"]["tests"] == ["not_null"]


def test_wire_never_touches_a_column_that_already_has_text(monkeypatch, tmp_path):
    """Including one deliberately pointing at a DIFFERENT block. Dragging
    `league_code_ingest_provenance` back to `league_code` would silently change
    what the column claims to mean."""
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
    """dbt's `docs-paths` defaults to `models/` and this project does not set it,
    so a block under `dbt_project/docs/` is invisible to dbt. Wiring a column to
    one would render as literal `{{ doc(...) }}` text in the warehouse."""
    dbt = _project(tmp_path, {"3_core/core.yml": WIRE_YML}, models={"m": "3_core"})
    _blocks_md(dbt, ["season_sk"])
    _blocks_md(dbt, ["team_sk"], where="docs/engineering_standards.md")

    assert _run_wire(monkeypatch) == 0

    cols = {c["name"]: c for c in yaml.safe_load(
        (dbt / "models" / "3_core" / "core.yml").read_text(encoding="utf-8"))["models"][0]["columns"]}
    assert cols["season_sk"]["description"] == "{{ doc('season_sk') }}"
    assert "description" not in cols["team_sk"], "wired to a block dbt cannot resolve"


def test_wire_ignores_docs_text_with_no_enddocs(monkeypatch, tmp_path, capsys):
    """`engineering_standards.md` contains the literal `{% docs name %}` inside a
    sentence explaining the syntax. Without a closing tag it is prose, not a block."""
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
    """THE GUARD THAT WAS MISSING, and it cost a real defect. Wiring matches a
    NAME to a block, which assumes one name means one thing. `league_code` does
    not: it is the competition almost everywhere and INGEST PROVENANCE on the
    global player events. The first version wired three staging columns to the
    identity block while the model's own description two lines above said
    "ingest provenance, not identity".

    The project already held the evidence, in that two blocks existed for the one
    name. So the script refuses to guess rather than trying to classify."""
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
    # The unambiguous name in the same model is still wired, so the guard withholds
    # a NAME rather than giving up on the file.
    assert models["blank_model"]["team_sk"]["description"] == "{{ doc('team_sk') }}"


def test_wire_refuses_when_no_blocks_exist_at_all(monkeypatch, tmp_path, capsys):
    """A floor: with an empty block set, "nothing to wire" is trivially true."""
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


# ------------------------------------------------- --wire-metric-docs (#82 MR4b)
#
# A derived column name has no bare block, only `__team` and/or `__player`, because
# a stem with one catalogue row says nothing about which entity the columns carrying
# its derived name belong to. (The worked example was `goals_against`, defined for a
# PLAYER while the columns of that name sat on TEAM models; step 4 of the naming
# programme renamed it to `goals_against_player`, so the example is historical — the
# fixtures below still exercise the mechanism, which is not.) Choosing between them
# is what this mode does, and choosing WRONG is invisible: the block resolves, the
# length is fine, dbt parses.

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
    """Both entities' blocks exist for one name here, so picking by name alone is
    impossible and the test can only pass by consulting MODEL_ENTITY."""
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
    """Defaulting is how the wrong definition gets attached, so an unknown model
    stops the run rather than being guessed at or quietly skipped."""
    yml = METRIC_YML.replace("mart_team_profile", "mart_something_new")
    dbt = _project(tmp_path, {"5_marts/shared/shared.yml": yml},
                   models={"mart_something_new": "5_marts/shared"})
    _blocks_md(dbt, ["goals_against_this_season__team", "assists_this_season__player"])

    assert _run_metric_wire(monkeypatch) == 1
    err = capsys.readouterr().err
    assert "MODEL_ENTITY" in err and "mart_something_new" in err


def test_metric_wire_REPORTS_a_column_with_no_block_for_its_entity(
        monkeypatch, tmp_path, capsys):
    """The catalogue never defined the metric for that entity, so the column stays
    blank — which is right, and saying so is what makes it a decision rather than a
    hole somebody finds later. 48 real columns are in this position."""
    dbt = _project(tmp_path, {"5_marts/shared/shared.yml": METRIC_YML},
                   models={"mart_team_profile": "5_marts/shared"})
    # only the PLAYER block exists for goals_against; the team column cannot wire.
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
    """Same rule as the shared-docs mode: this tool appends, it never rewrites."""
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


# ---------------------------------------------- --promote-shared-docs (#82 MR4b-2)
#
# This mode is the ONLY one that edits a line already in the file, in a script
# whose contract is append-only. Its single reviewable claim is that nothing is
# rewritten: the text the block resolves to is the text the column already had.
# Every test below exists to make that claim falsifiable.

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
    """A .md whose blocks carry the exact bodies given."""
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
    """The guard the whole mode rests on. If the block says something else, swapping
    the reference in REWRITES the column — which is the opposite of promoting it,
    and would be invisible afterwards because the reference resolves fine."""
    dbt = _project(tmp_path, {"3_core/core.yml": PROMOTE_YML}, models={"dim_thing": "3_core"})
    _blocks_text(dbt, {"shared_col": "A DIFFERENT sentence with the same name."})
    target = dbt / "models" / "3_core" / "core.yml"
    before = target.read_text(encoding="utf-8")

    assert _run_promote(monkeypatch) == 1          # nothing left to do, and loud
    out = capsys.readouterr()
    assert "NOT the block's text" in out.out
    assert target.read_text(encoding="utf-8") == before


def test_promote_REFUSES_a_folded_description(monkeypatch, tmp_path, capsys):
    """A folded scalar spans several lines and this script edits by LINE. Rewriting
    one is how a file gets mangled, so it is reported for a human. Two real sites
    are in exactly this shape."""
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
    """The same sentence appears under five models in the real `shared.yml`, so a
    whole-file search finds five candidates and can name none of them. Searching
    the file instead of the model made this mode skip five sites it should have
    promoted; only the model-scoped search gets them."""
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
    """`- name:` / `tests:` / `description:` is legal YAML and this repo already
    uses that ordering. An earlier version of the writer assumed the description
    was always the line immediately after the name and aborted the whole FILE for
    anything else — an assumption mutation testing showed had no test, and then
    showed was wrong."""
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
    assert col["tests"] == ["not_null"]          # survives untouched


def test_promote_refuses_when_the_planned_line_is_no_longer_there(monkeypatch, tmp_path):
    """The file changed between planning and writing. Overwriting an unexamined
    line is exactly what this script exists not to do."""
    lines = ['      - name: shared_col', '        description: "Something else."']
    with pytest.raises(gen.Abort) as exc:
        gen._replace_description(
            ["models:", "  - name: dim_thing", "    columns:", *lines],
            "dim_thing",
            {"shared_col": ("shared_col", '        description: "The planned line."')})
    assert "found 0" in str(exc.value)


def test_verify_still_refuses_a_replace_the_run_did_not_plan():
    """The append-only guard is NARROWED, not loosened. A replace on a line outside
    the planned set — a reformat, a reorder, an off-by-one swap — is still refused,
    and an empty planned set restores the original rule exactly."""
    before = 'a: 1\nb: 2\nc: 3\n'
    after = 'a: 1\nb: CHANGED\nc: 3\n'
    expected = yaml.safe_load(after)

    with pytest.raises(gen.Abort) as exc:
        gen._verify(before, after, expected, "f.yml", "\n", frozenset())
    assert "not append-only" in str(exc.value)

    # The same edit, with that exact line planned, is allowed.
    gen._verify(before, after, expected, "f.yml", "\n", frozenset({"b: 2"}))

    # A DIFFERENT line planned does not license this one.
    with pytest.raises(gen.Abort):
        gen._verify(before, after, expected, "f.yml", "\n", frozenset({"c: 3"}))


def test_an_unplanned_line_cannot_ride_along_inside_a_planned_replace():
    """⚠ THE CASE EVERY OTHER TEST MISSES, found by reading rather than running.
    The guard requires EVERY old line inside a `replace` opcode
    to have been planned. Weaken that to "at least one" and an unplanned line merged
    into the same opcode as a legitimate swap slips through — and `_verify`'s second,
    structural check cannot catch it either, because that one compares parsed YAML
    and is blind to a reformat.

    Every other test replaces ONE isolated line, where "all" and "any" are
    identical, so the mutation had nowhere to show. This makes two ADJACENT lines
    change together so difflib emits a single multi-line `replace`."""
    before = "a: 1\nb: 2\nc: 3\nd: 4\n"
    after = "a: 1\nb: CHANGED\nc: ALSO CHANGED\nd: 4\n"
    expected = yaml.safe_load(after)

    # Both lines planned: allowed, and this is what proves the test is not simply
    # asserting that multi-line replaces are always refused.
    gen._verify(before, after, expected, "f.yml", "\n", frozenset({"b: 2", "c: 3"}))

    # Only ONE of the two planned: the other rode along, and that must be refused.
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
    """A stale entry is a silent no-op that hides a model nobody classified. Run
    against the REAL repo, with no monkeypatching."""
    import importlib

    fresh = importlib.reload(gen)
    on_disk = {p.stem for p in (fresh.MODELS_DIR).rglob("*.sql")}
    missing = sorted(set(fresh.MODEL_ENTITY) - on_disk)
    assert not missing, (
        "MODEL_ENTITY names models that do not exist: " + ", ".join(missing))
    assert set(fresh.MODEL_ENTITY.values()) == {"team", "player"}
