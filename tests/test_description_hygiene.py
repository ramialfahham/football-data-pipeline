"""Tests for `scripts/check_description_hygiene.py`; each rule is driven red by an offender."""
from __future__ import annotations

import os
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import check_description_hygiene as gate  # noqa: E402


CLEAN = """
version: 2
models:
  - name: some_model
    description: >
      One row per team per season, from the generic staging model. Grain:
      (team_sk, season_api_year). NULL where the provider sent no row.
    columns:
      - name: team_sk
        description: "Team identity key, globally unique in the provider's data."
"""


def _write(tmp_path, body: str):
    """A minimal dbt project directory holding one schema file."""
    models = tmp_path / "models"
    models.mkdir(parents=True, exist_ok=True)
    (models / "schema.yml").write_text(body, encoding="utf-8")
    return tmp_path


def _write_blocks(tmp_path, text: str, where="models/docs/shared_columns.md"):
    """dbt's `docs-paths` defaults to `models/`, so a block anywhere else cannot be resolved."""
    path = tmp_path / where
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return tmp_path


SHARED_TEAM_SK = "{% docs team_sk %}\nTeam identity key.\n{% enddocs %}\n"

# One model, one column named after a shared block. The description is the variable.
SHARED_NAME = """
version: 2
models:
  - name: some_model
    description: >
      One row per team per season. Grain: (team_sk, season_api_year).
    columns:
      - name: team_sk
%s
"""


def _shared(tmp_path, monkeypatch, description_line: str, blocks=SHARED_TEAM_SK,
            where="models/docs/shared_columns.md"):
    _write(tmp_path, SHARED_NAME % description_line)
    _write_blocks(tmp_path, blocks, where)
    monkeypatch.setattr(gate, "DBT_DIR", tmp_path)


def test_the_two_docs_block_regexes_agree():
    """`DOC_BLOCK_RE` is copied into the gate and the generator, so parity is pinned here."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "declare_missing_columns",
        os.path.join(os.path.dirname(__file__), "..", "scripts",
                     "declare_missing_columns.py"),
    )
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    cases = [
        "{% docs a %}A.{% enddocs %}",
        "prose {% docs stray %} more\n\n{% docs real %}R.{% enddocs %}",
        "{% docs a %}A.{% enddocs %}\n{% docs b %}B.{% enddocs %}",
        "{% docs unclosed %}nothing after it",
        "no blocks here at all",
    ]
    for text in cases:
        # The gate captures (name, body); the generator captures name only.
        gate_names = [m[0] if isinstance(m, tuple) else m
                      for m in gate.DOC_BLOCK_RE.findall(text)]
        gen_names = [m[0] if isinstance(m, tuple) else m
                     for m in gen.DOC_BLOCK_RE.findall(text)]
        assert gate_names == gen_names, f"the two regexes disagree on {text!r}"

    # Pins the behaviour itself, so agreement cannot mean both are wrong.
    assert [m[0] for m in gate.DOC_BLOCK_RE.findall(cases[1])] == ["real"]


AMBIGUOUS_BLOCKS = (SHARED_TEAM_SK
                    + "\n{% docs team_sk_other %}\nA different meaning.\n{% enddocs %}\n")

AMBIGUOUS_NAME = """
version: 2
models:
  - name: identity_model
    description: "One row per team."
    columns:
      - name: team_sk
        description: "{{ doc('team_sk') }}"
  - name: other_model
    description: "Where the same name means something else."
    columns:
      - name: team_sk
        description: "{{ doc('team_sk_other') }}"
  - name: prose_model
    description: "Inline text on a name that means two things."
    columns:
      - name: team_sk
        description: "Here it is the club side of the pairing."
"""


def test_a_name_that_means_two_things_is_not_demanded(tmp_path, monkeypatch, capsys):
    """A name with two meanings is not demanded a shared block, but a blank one still fails."""
    _write(tmp_path, AMBIGUOUS_NAME)
    _write_blocks(tmp_path, AMBIGUOUS_BLOCKS)
    monkeypatch.setattr(gate, "DBT_DIR", tmp_path)
    assert gate.main() == 0, "the gate demanded a guess on a name that means two things"

    _write(tmp_path, AMBIGUOUS_NAME.replace(
        '        description: "Here it is the club side of the pairing."\n', ""))
    assert gate.main() == 1, "a blank column passed because its name means two things"
    out = capsys.readouterr().out
    assert "COLUMN COVERAGE" in out and "prose_model.team_sk" in out
    assert "SHARED DEFINITIONS" not in out


def test_an_unpoliced_name_is_reported_not_silently_skipped(tmp_path, monkeypatch, capsys):
    """A name exempted from the shared-definition rule is reported in every run."""
    _write(tmp_path, AMBIGUOUS_NAME)
    _write_blocks(tmp_path, AMBIGUOUS_BLOCKS)
    monkeypatch.setattr(gate, "DBT_DIR", tmp_path)

    assert gate.main() == 0
    out = capsys.readouterr().out
    assert "NOT POLICED" in out
    assert "team_sk: team_sk, team_sk_other" in out


def test_the_two_ambiguity_rules_agree(tmp_path):
    """The gate and the generator must agree on which names are ambiguous; pinned by behaviour."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "declare_missing_columns",
        os.path.join(os.path.dirname(__file__), "..", "scripts",
                     "declare_missing_columns.py"),
    )
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    doc = yaml.safe_load(AMBIGUOUS_NAME)
    gate_view = gate._ambiguous_names([("schema.yml", tmp_path / "schema.yml", doc)])
    gen_view = gen._ambiguous_names([(tmp_path / "schema.yml", doc)])

    assert gate_view == gen_view == {"team_sk": {"team_sk", "team_sk_other"}}

    clean = yaml.safe_load(CLEAN)
    assert gate._ambiguous_names([("c.yml", tmp_path / "c.yml", clean)]) == {}
    assert gen._ambiguous_names([(tmp_path / "c.yml", clean)]) == {}


def test_a_blank_column_whose_name_has_a_shared_definition_is_red(tmp_path, monkeypatch, capsys):
    _shared(tmp_path, monkeypatch, "")

    assert gate.main() == 1
    out = capsys.readouterr().out
    assert "SHARED DEFINITIONS" in out
    assert "blank, but a shared definition for 'team_sk' exists" in out


def test_a_column_restating_a_shared_definition_is_red(tmp_path, monkeypatch, capsys):
    _shared(tmp_path, monkeypatch,
            '        description: "Team identity key, globally unique in the provider data."')

    assert gate.main() == 1
    assert "restates a shared definition instead of referencing it" in capsys.readouterr().out


def test_a_column_referencing_its_own_block_is_green(tmp_path, monkeypatch):
    _shared(tmp_path, monkeypatch, '        description: "{{ doc(\'team_sk\') }}"')
    assert gate.main() == 0


def test_referencing_a_DIFFERENT_block_is_green(tmp_path, monkeypatch):
    """The rule does not police which block is referenced; that would need an exemption list."""
    blocks = (SHARED_TEAM_SK
              + "\n{% docs team_sk_other_meaning %}\nSomething else.\n{% enddocs %}\n")
    _shared(tmp_path, monkeypatch,
            '        description: "{{ doc(\'team_sk_other_meaning\') }}"', blocks=blocks)
    assert gate.main() == 0


def test_a_block_outside_models_is_not_a_block(tmp_path, monkeypatch):
    """dbt's `docs-paths` defaults to `models/`, so a block elsewhere is invisible to the gate."""
    _shared(tmp_path, monkeypatch, '        description: "Team identity key."',
            where="docs/engineering_standards.md")
    assert gate.main() == 0, "a block dbt cannot resolve was treated as real"


def test_docs_prose_with_no_enddocs_neither_invents_nor_swallows_a_block(
        tmp_path, monkeypatch, capsys):
    """A literal `{% docs name %}` in prose must not invent a block or swallow the next real one."""
    blocks = ("Long text belongs in a docs block, {% docs name %} in a .md file.\n\n"
              + SHARED_TEAM_SK)
    _shared(tmp_path, monkeypatch, '        description: "{{ doc(\'team_sk\') }}"',
            blocks=blocks)

    assert gate.main() == 0, "the real team_sk block was swallowed by the stray opener"
    assert "unresolved docs block" not in capsys.readouterr().out


@pytest.fixture(autouse=True)
def _point_gate_at_tmp(monkeypatch):
    """Each test builds a tiny project, so the discovery floors are lowered."""
    monkeypatch.setattr(gate, "MIN_DESCRIPTIONS", 1)
    monkeypatch.setattr(gate, "MIN_MODELS", 0)
    monkeypatch.setattr(gate, "MIN_SOURCE_TABLES", 0)
    monkeypatch.setattr(gate, "MIN_LISTED_COLUMNS", 0)


# (label, the phrase spliced into an otherwise-clean description)
OFFENDERS = [
    ("issue reference", "Superseded by #844."),
    ("GAP reference", "The gap is registered as GAP-19."),
    ("MR reference", "Landed in !27."),
    ("ISO date", "Corrected on 2026-07-23 after a review."),
    ("dated update stamp", "UPDATED after the migration."),
    ("decision language", "The CPO ruled this on review."),
    ("slated-for annotation", "SLATED FOR DELETION once the page ships."),
    ("only-reader claim", "Its only reader is build_nav()."),
    ("no-consumer claim", "This model has NO consumer today."),
    ("nothing-downstream claim", "Nothing downstream resolves its versions."),
    ("feeds-a-model claim", "Feeds fct_fixture and nothing else."),
    ("feeds-a-column claim", "Cumulative opponent shots; feeds shots_share_pct downstream."),
    ("read-by claim", "READ by mart_competition_index for the page."),
    ("severity emoji", "⚠ This is a trap for the unwary."),
]


@pytest.mark.parametrize("label,phrase", OFFENDERS, ids=[o[0] for o in OFFENDERS])
def test_each_banned_class_turns_the_gate_red(tmp_path, monkeypatch, capsys, label, phrase):
    body = CLEAN.replace("NULL where the provider sent no row.",
                         f"NULL where the provider sent no row. {phrase}")
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))

    assert gate.main() == 1, f"the gate passed text containing a {label}"
    out = capsys.readouterr().out
    assert "finding" in out, f"the gate failed on a {label} without saying why"


def test_the_same_fixture_without_the_offender_is_green(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, CLEAN))
    assert gate.main() == 0


def test_ordinary_prose_is_not_mistaken_for_decision_language(tmp_path, monkeypatch):
    """Ordinary prose using `corrected` or `feeds` must not match the decision-language rules."""
    body = CLEAN.replace(
        "NULL where the provider sent no row.",
        "It applies the country corrections from the override seed, so the value is "
        "already the corrected name. It feeds into the season rollup.",
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 0, "the gate fired on ordinary prose, not on a decision log"


def test_football_prose_using_ruled_is_not_decision_language(tmp_path, monkeypatch):
    """`ruled` is ordinary football prose; only an attributed ruling is decision language."""
    body = CLEAN.replace(
        "NULL where the provider sent no row.",
        "Excludes any goal ruled out for offside, and any match ruled void.",
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 0, "the gate read ordinary football prose as a decision log"


def test_an_attributed_ruling_is_still_caught(tmp_path, monkeypatch):
    """Not matching bare `ruled` must not hide a ruling attributed to a person."""
    body = CLEAN.replace(
        "NULL where the provider sent no row.",
        "The CPO ruled this column stays as-is.",
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 1


def test_a_non_utf8_file_fails_closed_and_names_the_file(tmp_path, monkeypatch, capsys):
    """`read_text` raises UnicodeDecodeError, not YAMLError, and the file must still be named."""
    models = tmp_path / "models"
    models.mkdir(parents=True, exist_ok=True)
    # cp1252 bytes that are not valid UTF-8
    (models / "schema.yml").write_bytes(b"description: caf\xe9 na\xefve\n")
    monkeypatch.setattr(gate, "DBT_DIR", tmp_path)

    assert gate.main() == 1
    out = capsys.readouterr().out
    assert "schema.yml" in out, "the gate failed without naming the file it could not read"
    assert "UnicodeDecodeError" in out, "the gate did not report why the file was unreadable"


def test_a_column_over_bigquerys_limit_turns_the_gate_red(tmp_path, monkeypatch):
    """1,024 is BigQuery's column-description maximum; past it persist_docs fails the build."""
    body = CLEAN.replace(
        '"Team identity key, globally unique in the provider\'s data."',
        '"' + ("word " * 250) + '"',          # ~1,250 chars
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 1


def test_a_model_description_may_exceed_the_column_limit(tmp_path, monkeypatch):
    """BigQuery allows 1,024 characters for a column but 16,384 for a table."""
    body = CLEAN.replace("NULL where the provider sent no row.", "word " * 250)
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 0


def test_a_model_over_bigquerys_table_limit_turns_the_gate_red(tmp_path, monkeypatch):
    body = CLEAN.replace("NULL where the provider sent no row.", "word " * 4000)
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 1


def _write_block(tmp_path, name: str, body: str):
    docs = tmp_path / "models" / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / f"{name}.md").write_text(
        "{%% docs %s %%}\n%s\n{%% enddocs %%}\n" % (name, body), encoding="utf-8"
    )


def test_a_short_docs_block_reference_is_green(tmp_path, monkeypatch):
    """A shared block plus a short qualifier stays under the limit once rendered."""
    _write_block(tmp_path, "team_sk", "Team identity key, globally unique.")
    body = CLEAN.replace(
        '"Team identity key, globally unique in the provider\'s data."',
        '"{{ doc(\'team_sk\') }} Here it is the home side."',
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 0


def test_length_is_measured_after_the_docs_block_is_expanded(tmp_path, monkeypatch, capsys):
    """persist_docs renders the block into the stored description, so the rendered total counts."""
    _write_block(tmp_path, "team_sk", "block " * 150)         # ~900 chars
    body = CLEAN.replace(
        '"Team identity key, globally unique in the provider\'s data."',
        '"{{ doc(\'team_sk\') }} ' + ("tail " * 60) + '"',      # ~300 chars
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))

    assert gate.main() == 1, "the rendered description exceeded the limit and passed"
    out = capsys.readouterr().out
    assert "after expanding its docs block" in out, (
        "the gate flagged the length without saying the block was what pushed it over"
    )


def test_a_nested_docs_block_is_expanded_too(tmp_path, monkeypatch):
    """A block may reference another, so expansion must recurse."""
    _write_block(tmp_path, "outer", "{{ doc('inner') }}")
    _write_block(tmp_path, "inner", "block " * 250)          # ~1,500 chars
    body = CLEAN.replace(
        '"Team identity key, globally unique in the provider\'s data."',
        '"{{ doc(\'outer\') }}"',
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 1, "the nested block was never expanded, so its length went unseen"


def test_a_circular_docs_block_does_not_hang(tmp_path, monkeypatch, capsys):
    _write_block(tmp_path, "a", "{{ doc('b') }}")
    _write_block(tmp_path, "b", "{{ doc('a') }}")
    body = CLEAN.replace(
        '"Team identity key, globally unique in the provider\'s data."',
        '"{{ doc(\'a\') }}"',
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 1
    assert "circular" in capsys.readouterr().out


def test_an_unresolved_docs_block_is_a_finding(tmp_path, monkeypatch, capsys):
    """With no block behind a doc() reference, the stored length cannot be known."""
    body = CLEAN.replace(
        '"Team identity key, globally unique in the provider\'s data."',
        '"{{ doc(\'no_such_block\') }}"',
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 1
    assert "unresolved docs block" in capsys.readouterr().out


def test_a_banned_phrase_inside_a_shared_block_is_caught(tmp_path, monkeypatch):
    """A block reaches every call site, so the banned phrases apply inside it."""
    _write_block(tmp_path, "team_sk", "Team key. Its only reader is dim_team.")
    body = CLEAN.replace(
        '"Team identity key, globally unique in the provider\'s data."',
        '"{{ doc(\'team_sk\') }}"',
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 1


def test_the_floor_fires_from_inside_the_gate(tmp_path, monkeypatch, capsys):
    """The floor stops a broken walk reporting a clean sweep over zero descriptions."""
    monkeypatch.setattr(gate, "MIN_DESCRIPTIONS", 400)
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, CLEAN))

    assert gate.main() == 1
    out = capsys.readouterr().out
    assert "floor" in out, "the floor fired without explaining that the walk broke"


def test_an_unparseable_file_fails_closed(tmp_path, monkeypatch, capsys):
    """The file must be named, and the floor must not be blamed for the descriptions it hides."""
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, "key: [unclosed\n"))
    assert gate.main() == 1

    out = capsys.readouterr().out
    assert "schema.yml" in out, "the gate failed without naming the file it could not read"
    assert "unchecked" in out, "the gate did not say those descriptions went unchecked"
    assert "floor" not in out, (
        "the gate blamed the extraction floor for a malformed file; the diagnosis "
        "has to name the real cause"
    )


def test_the_real_repo_is_green():
    assert gate.main() == 0


# --- coverage: the object has no description at all ---

def _project(tmp_path, *, model_sql: str | None = "int_x", schema: str = "") -> object:
    """A tmp project with a real .sql on disk, optionally with a schema file."""
    models = tmp_path / "models"
    models.mkdir(parents=True, exist_ok=True)
    if model_sql:
        (models / f"{model_sql}.sql").write_text("select 1", encoding="utf-8")
    if schema:
        (models / "schema.yml").write_text(schema, encoding="utf-8")
    return tmp_path


DESCRIBED = """version: 2
models:
  - name: int_x
    description: "One row per team per season, from the generic staging model."
"""


def test_a_model_declared_in_no_yml_turns_the_gate_red(tmp_path, monkeypatch, capsys):
    """The walk is over .sql files, so a model that appears in no yml is still found."""
    monkeypatch.setattr(gate, "DBT_DIR", _project(tmp_path))
    assert gate.main() == 1, "a model with no yml entry at all passed the gate"
    out = capsys.readouterr().out
    assert "int_x" in out and "declared in no yml" in out, (
        "the gate failed without naming the model or saying it was undeclared"
    )


def test_a_model_with_an_empty_description_turns_the_gate_red(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(gate, "DBT_DIR", _project(
        tmp_path, schema='version: 2\nmodels:\n  - name: int_x\n    description: ""\n'))
    assert gate.main() == 1, "a model with an empty description passed the gate"
    assert "NO DESCRIPTION" in capsys.readouterr().out


def test_a_described_model_is_green(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "DBT_DIR", _project(tmp_path, schema=DESCRIBED))
    assert gate.main() == 0


# --- column coverage: a column the yml lists has no description ---

def _listed(column_lines: str) -> str:
    return DESCRIBED + "    columns:\n      - name: team_sk\n" + column_lines


def test_a_listed_column_with_no_description_turns_the_gate_red(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(gate, "DBT_DIR", _project(tmp_path, schema=_listed("        tests: [not_null]\n")))
    assert gate.main() == 1, "a listed column with no description passed the gate"
    out = capsys.readouterr().out
    assert "COLUMN COVERAGE" in out and "int_x.team_sk" in out and "NO DESCRIPTION" in out


def test_a_listed_column_with_an_empty_description_turns_the_gate_red(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(gate, "DBT_DIR", _project(tmp_path, schema=_listed('        description: "  "\n')))
    assert gate.main() == 1
    assert "int_x.team_sk" in capsys.readouterr().out


def test_a_listed_column_with_text_is_green(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "DBT_DIR", _project(
        tmp_path, schema=_listed('        description: "Team identity key, globally unique in the provider\'s data."\n')))
    assert gate.main() == 0


def test_a_listed_column_referencing_a_block_is_green(tmp_path, monkeypatch):
    """A `{{ doc() }}` reference is a description; whether it resolves is the render rule's job."""
    _write_blocks(tmp_path, SHARED_TEAM_SK)
    monkeypatch.setattr(gate, "DBT_DIR", _project(
        tmp_path, schema=_listed('        description: "{{ doc(\'team_sk\') }}"\n')))
    assert gate.main() == 0


def test_the_listed_column_floor_fires_when_the_walk_finds_nothing(tmp_path, monkeypatch, capsys):
    """A walk that finds no listed columns must not read as every listed column being described."""
    monkeypatch.setattr(gate, "MIN_LISTED_COLUMNS", 800)
    monkeypatch.setattr(gate, "DBT_DIR", _project(tmp_path, schema=DESCRIBED))
    assert gate.main() == 1
    assert "discovery looks broken" in capsys.readouterr().out


def test_a_source_table_with_no_description_turns_the_gate_red(tmp_path, monkeypatch, capsys):
    schema = DESCRIBED + """
sources:
  - name: api_football
    tables:
      - name: raw_apif_thing
"""
    monkeypatch.setattr(gate, "DBT_DIR", _project(tmp_path, schema=schema))
    assert gate.main() == 1, "a source table with no description passed the gate"
    out = capsys.readouterr().out
    assert "raw_apif_thing" in out, "the gate failed without naming the source table"


def test_a_described_source_table_is_green(tmp_path, monkeypatch):
    schema = DESCRIBED + """
sources:
  - name: api_football
    tables:
      - name: raw_apif_thing
        description: "One row per FETCH of a whole league, as JSON. Append-only."
"""
    monkeypatch.setattr(gate, "DBT_DIR", _project(tmp_path, schema=schema))
    assert gate.main() == 0


def test_a_seed_with_no_description_turns_the_gate_red(tmp_path, monkeypatch, capsys):
    seeds = tmp_path / "seeds"
    seeds.mkdir(parents=True, exist_ok=True)
    (seeds / "some_seed.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    monkeypatch.setattr(gate, "DBT_DIR", _project(tmp_path, schema=DESCRIBED))
    assert gate.main() == 1, "a seed with no description passed the gate"
    assert "some_seed" in capsys.readouterr().out


def test_the_coverage_floor_fires_when_discovery_finds_nothing(tmp_path, monkeypatch, capsys):
    """At its real value, which the autouse fixture lowers elsewhere, finding no models fails."""
    monkeypatch.setattr(gate, "MIN_MODELS", 50)
    monkeypatch.setattr(gate, "MIN_SOURCE_TABLES", 5)
    monkeypatch.setattr(gate, "DBT_DIR", _project(tmp_path, model_sql=None, schema=DESCRIBED))

    assert gate.main() == 1, "the gate passed with the model discovery finding nothing"
    out = capsys.readouterr().out
    assert "discovery looks broken" in out, (
        "the gate failed without reporting that discovery, not content, was the problem"
    )
