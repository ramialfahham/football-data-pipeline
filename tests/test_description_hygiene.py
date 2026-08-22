"""Tests for `scripts/check_description_hygiene.py`.

The point of these is NOT that the gate passes on today's repo — it does, and a
test asserting that would go green forever while the gate quietly stopped
matching anything. The point is that it goes RED, once per banned class, on text
that is deliberately wrong. That is the repo's dominant failure mode (#904): a
claim asserted rather than run.

So every rule below is driven through `main()` against a synthetic offender and
asserted to exit 1, AND the same fixture without the offending phrase is asserted
to exit 0 — a rule that fires on everything is as useless as one that fires on
nothing.
"""
from __future__ import annotations

import os
import sys

import pytest

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


@pytest.fixture(autouse=True)
def _point_gate_at_tmp(monkeypatch):
    """Each test supplies its own tiny project, so the extraction floor would
    otherwise trip on every one of them and mask what is being tested. The floor
    gets its own test below, which is the only place it stays at its real value.

    MIN_MODELS and MIN_SOURCE_TABLES are lowered for the same reason and no other:
    a tmp fixture holds a schema file and usually no .sql at all, so the coverage
    discovery floor would fire on every test and hide what each one is checking.
    Both keep their real values in `test_the_coverage_floor_fires_...` below, and
    the gate runs them at full strength against the real project."""
    monkeypatch.setattr(gate, "MIN_DESCRIPTIONS", 1)
    monkeypatch.setattr(gate, "MIN_MODELS", 0)
    monkeypatch.setattr(gate, "MIN_SOURCE_TABLES", 0)


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
    ("feeds-a-column claim", "Cumulative opponent shots; feeds shot_share downstream."),
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
    """A rule that fires on everything is as useless as one that fires on nothing."""
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, CLEAN))
    assert gate.main() == 0


def test_ordinary_prose_is_not_mistaken_for_decision_language(tmp_path, monkeypatch):
    """MEASURED, not hypothetical. On the cleaned MR3/MR4 text a case-insensitive
    `CORRECTED` matches six legitimate sentences, and a bare `feeds` matches
    ordinary prose. A gate that fires on correct text gets weakened, not obeyed."""
    body = CLEAN.replace(
        "NULL where the provider sent no row.",
        "It applies the country corrections from the override seed, so the value is "
        "already the corrected name. It feeds into the season rollup.",
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 0, "the gate fired on ordinary prose, not on a decision log"


def test_football_prose_using_ruled_is_not_decision_language(tmp_path, monkeypatch):
    """`ruled` and `ruling` are ordinary words in a football repo. An earlier draft
    of the gate matched them bare, which would have fired on "goal ruled out for
    offside" — a false positive in the one domain this repo is about, and a breach
    of the gate's own stated design rule (annotation forms, not ordinary verbs).
    `\\bCPO\\b` catches the real instances, because a logged ruling is attributed."""
    body = CLEAN.replace(
        "NULL where the provider sent no row.",
        "Excludes any goal ruled out for offside, and any match ruled void.",
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 0, "the gate read ordinary football prose as a decision log"


def test_an_attributed_ruling_is_still_caught(tmp_path, monkeypatch):
    """The other half of the pair above: dropping bare `ruled` must not create a
    hole. A real decision-log line names who ruled."""
    body = CLEAN.replace(
        "NULL where the provider sent no row.",
        "The CPO ruled this column stays as-is.",
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 1


def test_a_non_utf8_file_fails_closed_and_names_the_file(tmp_path, monkeypatch, capsys):
    """`read_text` raises UnicodeDecodeError, not YAMLError. Uncaught it escapes as
    a raw traceback: still a non-zero exit, but blaming nothing and naming no file."""
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
    """1,024 is BigQuery's own column-description maximum; past it the DDL is
    rejected and persist_docs fails the build."""
    body = CLEAN.replace(
        '"Team identity key, globally unique in the provider\'s data."',
        '"' + ("word " * 250) + '"',          # ~1,250 chars
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 1


def test_a_model_description_may_exceed_the_column_limit(tmp_path, monkeypatch):
    """The limits differ because BigQuery's do: 1,024 for a column, 16,384 for a
    table. A model description of 1,250 chars is long, but it is not a build
    failure, and this gate only guards build failures — brevity is a human's job."""
    body = CLEAN.replace("NULL where the provider sent no row.", "word " * 250)
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 0


def test_a_model_over_bigquerys_table_limit_turns_the_gate_red(tmp_path, monkeypatch):
    body = CLEAN.replace("NULL where the provider sent no row.", "word " * 4000)
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 1


def _write_block(tmp_path, name: str, body: str):
    """A `{% docs %}` block, in a .md file the way dbt requires."""
    docs = tmp_path / "models" / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / f"{name}.md").write_text(
        "{%% docs %s %%}\n%s\n{%% enddocs %%}\n" % (name, body), encoding="utf-8"
    )


def test_a_short_docs_block_reference_is_green(tmp_path, monkeypatch):
    """Reuse must not be punished: a shared block plus a short qualifier is exactly
    what the standard asks for, and it stays under the limit once rendered."""
    _write_block(tmp_path, "team_sk", "Team identity key, globally unique.")
    body = CLEAN.replace(
        '"Team identity key, globally unique in the provider\'s data."',
        '"{{ doc(\'team_sk\') }} Here it is the home side."',
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 0


def test_length_is_measured_after_the_docs_block_is_expanded(tmp_path, monkeypatch, capsys):
    """THE HOLE THIS CLOSES. An earlier version waived the length rule for any
    description containing a doc() reference, reasoning that the block was checked
    on its own. It was not — blocks live in .md files, not in `description:` keys,
    so the walk never saw them. Meanwhile persist_docs renders the block INTO the
    stored description, so the string BigQuery receives is block + qualifier.

    Here the qualifier alone is under the limit and the block alone is under it;
    only the rendered total is over. The old waiver passed this.
    """
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
    """A block may reference another. One substitution pass would leave the inner
    tag literal — understating the stored length and never checking the nested
    block's own text. No nesting exists today; this keeps it from being a hole if
    it ever does."""
    _write_block(tmp_path, "outer", "{{ doc('inner') }}")
    _write_block(tmp_path, "inner", "block " * 250)          # ~1,500 chars
    body = CLEAN.replace(
        '"Team identity key, globally unique in the provider\'s data."',
        '"{{ doc(\'outer\') }}"',
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 1, "the nested block was never expanded, so its length went unseen"


def test_a_circular_docs_block_does_not_hang(tmp_path, monkeypatch, capsys):
    """Two blocks referencing each other must terminate and be reported, not spin."""
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
    """dbt cannot compile a doc() reference with no block, and the stored length
    cannot be known — so shrugging at it measures the wrong string."""
    body = CLEAN.replace(
        '"Team identity key, globally unique in the provider\'s data."',
        '"{{ doc(\'no_such_block\') }}"',
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 1
    assert "unresolved docs block" in capsys.readouterr().out


def test_a_banned_phrase_inside_a_shared_block_is_caught(tmp_path, monkeypatch):
    """A block reaches every call site. A banned phrase hiding in one would
    otherwise be invisible to a gate that only reads the YAML."""
    _write_block(tmp_path, "team_sk", "Team key. Its only reader is dim_team.")
    body = CLEAN.replace(
        '"Team identity key, globally unique in the provider\'s data."',
        '"{{ doc(\'team_sk\') }}"',
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 1


def test_the_floor_fires_from_inside_the_gate(tmp_path, monkeypatch, capsys):
    """The floor is what stops a broken walk reporting a clean sweep over zero
    descriptions. It has to live in the gate, not only here: this test would not
    exist in CI's failure path."""
    monkeypatch.setattr(gate, "MIN_DESCRIPTIONS", 400)
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, CLEAN))

    assert gate.main() == 1
    out = capsys.readouterr().out
    assert "floor" in out, "the floor fired without explaining that the walk broke"


def test_an_unparseable_file_fails_closed(tmp_path, monkeypatch, capsys):
    """An unreadable schema.yml is a description surface the gate is silently not
    covering, which is worse than a finding.

    Asserts the FILE IS NAMED and that the count is not what gets blamed. An
    unparseable file contributes zero descriptions, so it drags the census under
    the floor; the first version of the gate hit the floor check first and told the
    operator the walk had broken, sending them after the wrong thing entirely.
    """
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
    """Ships green on day one — the `check_copy_gate.py` precedent, where wiring a
    gate that was red on main would have reddened CI on text only the CPO could
    fix. This one asserts the state the wiring depends on."""
    assert gate.main() == 0


# ---------------------------------------------------------------------------
# COVERAGE: the object has no description at all.
#
# The content rules above never see such an object, which is how the coverage
# half of engineering_standards.md section 2 stayed unenforced for the life of
# the project: 11 of 11 source tables had no description when this was written.
# ---------------------------------------------------------------------------

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
    """THE CASE THAT MOTIVATED WALKING FILES INSTEAD OF YAML ENTRIES.

    `int_team__market_value_latest` had no description because it appeared in no
    yml whatsoever. A check that read yml entries would have found nothing to
    complain about and passed it green, which is precisely the blind spot the
    coverage rule exists to close.
    """
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
    """A rule that fires on everything is as useless as one that fires on nothing."""
    monkeypatch.setattr(gate, "DBT_DIR", _project(tmp_path, schema=DESCRIBED))
    assert gate.main() == 0


def test_a_source_table_with_no_description_turns_the_gate_red(tmp_path, monkeypatch, capsys):
    """11 of 11 source tables were in this state. A raw table nobody has described
    is where the whole pipeline starts."""
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
    """The floor at its REAL value, which the autouse fixture lowers everywhere else.

    Without it, a moved directory or a changed suffix makes "every model is
    described" true by finding no models — the same vacuous-pass shape
    MIN_DESCRIPTIONS guards against for the content half.
    """
    monkeypatch.setattr(gate, "MIN_MODELS", 50)
    monkeypatch.setattr(gate, "MIN_SOURCE_TABLES", 5)
    monkeypatch.setattr(gate, "DBT_DIR", _project(tmp_path, model_sql=None, schema=DESCRIBED))

    assert gate.main() == 1, "the gate passed with the model discovery finding nothing"
    out = capsys.readouterr().out
    assert "discovery looks broken" in out, (
        "the gate failed without reporting that discovery, not content, was the problem"
    )
