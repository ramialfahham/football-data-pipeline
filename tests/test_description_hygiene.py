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
    gets its own test below, which is the only place it stays at its real value."""
    monkeypatch.setattr(gate, "MIN_DESCRIPTIONS", 1)


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


def test_over_length_turns_the_gate_red(tmp_path, monkeypatch):
    body = CLEAN.replace("NULL where the provider sent no row.", "word " * 200)
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 1


def test_a_docs_block_reference_is_exempt_from_the_length_rule(tmp_path, monkeypatch):
    """The block is a description in its own right and is checked there; charging
    its length to every call site would punish exactly the reuse the standard asks
    for."""
    long_tail = "word " * 200
    body = CLEAN.replace(
        '"Team identity key, globally unique in the provider\'s data."',
        f'"{{{{ doc(\'team_sk\') }}}} {long_tail}"',
    )
    monkeypatch.setattr(gate, "DBT_DIR", _write(tmp_path, body))
    assert gate.main() == 0


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
