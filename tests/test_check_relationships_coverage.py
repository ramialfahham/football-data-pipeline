"""Tests for `scripts/check_relationships_coverage.py`.

Each rule is driven through `main()` against a synthetic models tree and shown RED on the
defect it exists for, and the same tree without the defect is shown green — a gate that fires
on everything is as useless as one that fires on nothing. The last test runs the gate on the
real tree inside `test:python`, so a foreign key added without `relationships` or a declared
soft link fails every merge request from here on — the same shape as
`test_materialisation_policy.py` and `test_persist_docs_policy.py`.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import check_relationships_coverage as gate  # noqa: E402

CORE = """
version: 2
models:
  - name: dim_team
    columns:
      - name: team_sk
        tests: [not_null, unique]
  - name: fct_fixture
    columns:
      - name: fixture_sk
        tests: [not_null, unique]
      - name: home_team_sk
        tests:
          - relationships:
              to: ref('dim_team')
              field: team_sk
"""

MART = """
version: 2
models:
  - name: mart_x
    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns: [team_sk, season_api_year]
    columns:
      - name: team_sk
        tests:
          - not_null
          - relationships:
              to: ref('dim_team')
              field: team_sk
      - name: opponent_team_sk
%(opponent)s
      - name: team_season_sk
        tests: [unique]
"""

COVERED = """        tests:
          - relationships:
              to: ref('dim_team')
              field: team_sk"""
SOFT = """        meta:
          soft_link: "dim_team - opponents outside the tracked competitions have no row\""""
BARE = "        description: \"An opponent.\""


def _tree(tmp_path, mart_body: str, core_body: str = CORE):
    models = tmp_path / "models"
    (models / "3_core").mkdir(parents=True)
    (models / "5_marts").mkdir(parents=True)
    (models / "3_core" / "core.yml").write_text(core_body, encoding="utf-8")
    (models / "5_marts" / "marts.yml").write_text(mart_body, encoding="utf-8")
    return models


def _lower_floors(monkeypatch):
    """The synthetic tree is tiny by design; the floors are tested on their own below."""
    monkeypatch.setattr(gate, "MIN_MODELS", 0)
    monkeypatch.setattr(gate, "MIN_CORE_KEYS", 0)
    monkeypatch.setattr(gate, "MIN_FOREIGN_KEYS", 0)


def test_a_foreign_key_without_relationships_is_red(tmp_path, monkeypatch, capsys):
    _lower_floors(monkeypatch)
    assert gate.main(_tree(tmp_path, MART % {"opponent": BARE})) == 1
    out = capsys.readouterr().out
    assert "mart_x.opponent_team_sk" in out
    assert "ref('dim_team'), field: team_sk" in out


def test_the_same_key_with_relationships_is_green(tmp_path, monkeypatch, capsys):
    _lower_floors(monkeypatch)
    assert gate.main(_tree(tmp_path, MART % {"opponent": COVERED})) == 0
    assert "3 foreign keys, 3 with relationships, 0 declared soft links" in capsys.readouterr().out


def test_a_declared_soft_link_is_green_and_printed(tmp_path, monkeypatch, capsys):
    _lower_floors(monkeypatch)
    assert gate.main(_tree(tmp_path, MART % {"opponent": SOFT})) == 0
    out = capsys.readouterr().out
    assert "1 declared soft links" in out
    assert "soft link: mart_x.opponent_team_sk -> dim_team.team_sk: dim_team - opponents" in out


def test_an_empty_soft_link_does_not_count(tmp_path, monkeypatch):
    _lower_floors(monkeypatch)
    body = MART % {"opponent": '        meta:\n          soft_link: "  "'}
    assert gate.main(_tree(tmp_path, body)) == 1


def test_a_soft_link_is_printed_even_when_another_column_fails(tmp_path, monkeypatch, capsys):
    """The docstring promises a soft link is never silent; a red run must print it too."""
    _lower_floors(monkeypatch)
    body = (MART % {"opponent": SOFT}).replace(
        "      - name: team_season_sk\n        tests: [unique]",
        "      - name: mystery_sk\n        description: \"Nobody knows.\"")
    assert gate.main(_tree(tmp_path, body)) == 1
    out = capsys.readouterr().out
    assert "soft link: mart_x.opponent_team_sk -> dim_team.team_sk" in out
    assert "mart_x.mystery_sk" in out


def test_an_undeclared_sk_that_is_not_the_models_own_key_is_red(tmp_path, monkeypatch, capsys):
    _lower_floors(monkeypatch)
    body = (MART % {"opponent": COVERED}).replace(
        "      - name: team_season_sk\n        tests: [unique]",
        "      - name: mystery_sk\n        description: \"Nobody knows.\"")
    assert gate.main(_tree(tmp_path, body)) == 1
    out = capsys.readouterr().out
    assert "mart_x.mystery_sk" in out
    assert "UNDECLARED KEY" in out


def test_an_own_key_needs_no_parent(tmp_path, monkeypatch, capsys):
    """`team_season_sk` is unique in mart_x and names no core key: an own key, not a finding.
    The entity prefix rule is what keeps it from resolving to `season_sk`."""
    _lower_floors(monkeypatch)
    core = CORE + (
        "  - name: dim_competition_season\n"
        "    columns:\n"
        "      - name: season_sk\n"
        "        tests: [unique]\n"
    )
    assert gate.main(_tree(tmp_path, MART % {"opponent": COVERED}, core)) == 0
    assert "3 foreign keys, 3 with relationships, 0 declared soft links, 4 own keys" in capsys.readouterr().out


def test_resolve_role_prefix_vs_entity_prefix():
    keys = {"team_sk": "dim_team", "season_sk": "dim_competition_season",
            "fixture_sk": "fct_fixture", "player_sk": "dim_player"}
    assert gate.resolve("team_sk", keys) == "team_sk"
    assert gate.resolve("opponent_team_sk", keys) == "team_sk"
    assert gate.resolve("biggest_margin_home_team_sk", keys) == "team_sk"
    assert gate.resolve("upcoming_fixture_sk", keys) == "fixture_sk"
    assert gate.resolve("team_in_sk", keys) == "team_sk"
    assert gate.resolve("team_season_sk", keys) is None
    assert gate.resolve("player_club_season_sk", keys) is None
    assert gate.resolve("standing_sk", keys) is None


def test_a_core_key_in_its_own_model_is_not_a_foreign_key(tmp_path, monkeypatch, capsys):
    _lower_floors(monkeypatch)
    assert gate.main(_tree(tmp_path, MART % {"opponent": COVERED})) == 0
    assert "3 own keys, 2 core keys" in capsys.readouterr().out


def test_below_the_floor_is_red(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(gate, "MIN_MODELS", 0)
    monkeypatch.setattr(gate, "MIN_CORE_KEYS", 0)
    monkeypatch.setattr(gate, "MIN_FOREIGN_KEYS", 10)
    assert gate.main(_tree(tmp_path, MART % {"opponent": COVERED})) == 1
    assert "discovery looks broken" in capsys.readouterr().out


def test_an_unparseable_file_fails_closed_and_names_it(tmp_path, monkeypatch, capsys):
    _lower_floors(monkeypatch)
    models = _tree(tmp_path, MART % {"opponent": COVERED})
    (models / "5_marts" / "broken.yml").write_text("models: [\n", encoding="utf-8")
    assert gate.main(models) == 1
    assert "broken.yml" in capsys.readouterr().out


def test_the_real_tree_is_covered(capsys):
    """The gate on the repo itself: this is what enforces the rule on every merge request until
    the script has its own `validate:governance` line."""
    assert gate.main() == 0
    out = capsys.readouterr().out
    assert out.startswith("OK:")
    assert "4 declared soft links" in out
