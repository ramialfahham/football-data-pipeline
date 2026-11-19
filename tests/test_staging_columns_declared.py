import pathlib
import re

import pytest
import yaml
from sqlfluff.core import FluffConfig, Linter

ROOT = pathlib.Path(__file__).resolve().parents[1]
STAGING = ROOT / "dbt_project" / "models" / "1_staging" / "api_football"
GENERIC_YML = STAGING / "stg_apif__generic.yml"

_LINTER = Linter(config=FluffConfig(overrides={"dialect": "bigquery", "templater": "raw"}))


def _strip_jinja(sql):
    sql = re.sub(r"\{#.*?#\}", "", sql, flags=re.DOTALL)
    sql = re.sub(r"\{%.*?%\}", "", sql, flags=re.DOTALL)
    return re.sub(r"\{\{.*?\}\}", "__jinja__", sql, flags=re.DOTALL)


def output_columns(sql):
    tree = _LINTER.parse_string(_strip_jinja(sql)).tree
    unparsable = [s.raw for s in tree.recursive_crawl("unparsable")]
    if unparsable:
        raise ValueError(f"sqlfluff could not parse: {unparsable[0]!r}")
    statement = tree.get_child("statement")
    top = statement.segments[0]
    final = top.get_children("select_statement")[-1] if top.is_type("with_compound_statement") else top
    names = []
    for element in final.get_child("select_clause").get_children("select_clause_element"):
        alias = element.get_child("alias_expression")
        if alias is not None:
            identifier = list(alias.recursive_crawl("naked_identifier", "quoted_identifier"))[-1]
        elif element.get_child("column_reference") is not None:
            identifier = list(
                element.get_child("column_reference").recursive_crawl(
                    "naked_identifier", "quoted_identifier"
                )
            )[-1]
        else:
            raise ValueError(f"cannot name output column: {element.raw!r}")
        names.append(identifier.raw.strip("`"))
    return names


def undeclared_columns(sql, declared):
    return [c for c in output_columns(sql) if c not in declared]


def _declared_by_model():
    models = yaml.safe_load(GENERIC_YML.read_text(encoding="utf-8"))["models"]
    return {m["name"]: {c["name"] for c in m.get("columns", [])} for m in models}


_DECLARED = _declared_by_model()
_MODELS = sorted(p.stem for p in STAGING.glob("stg_apif__*.sql"))


def test_every_staging_model_has_a_yml_entry():
    assert _MODELS
    assert set(_MODELS) <= set(_DECLARED)


@pytest.mark.parametrize("model", _MODELS)
def test_every_output_column_is_declared_in_the_yml(model):
    sql = (STAGING / f"{model}.sql").read_text(encoding="utf-8")
    assert output_columns(sql)
    assert undeclared_columns(sql, _DECLARED[model]) == []


def test_an_undeclared_column_is_reported():
    sql = "with src as (select 1 as a)\nselect\n    a,\n    {{ macro('x') }} as b,\n    c\nfrom src"
    assert output_columns(sql) == ["a", "b", "c"]
    assert undeclared_columns(sql, {"a", "b"}) == ["c"]
    assert undeclared_columns(sql, {"a", "b", "c"}) == []


def test_a_select_without_a_cte_and_quoted_names_are_read():
    assert output_columns("select t.a, `b` as `c` from t") == ["a", "c"]


def test_a_wildcard_or_unparsable_final_select_fails_loudly():
    with pytest.raises(ValueError):
        output_columns("select * from t")
    with pytest.raises(ValueError):
        output_columns("select a b c d from from t")
