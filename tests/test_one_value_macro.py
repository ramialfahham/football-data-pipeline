"""one_value(column) renders min(column) behind a guard that calls error() when a group holds two
values. BigQuery's error() fails the query, so a group with two values fails the build."""

import pathlib
import re

import jinja2

MACRO = pathlib.Path(__file__).resolve().parents[1] / "dbt_project" / "macros" / "one_value.sql"


def _render(column: str) -> str:
    env = jinja2.Environment()
    module = env.from_string(MACRO.read_text(encoding="utf-8")).module
    return " ".join(str(module.one_value(column)).split())


def test_two_values_reach_error_and_one_value_reaches_min():
    sql = _render("team_id")
    match = re.fullmatch(r"if\( count\(distinct team_id\) > 1, error\('(.+)'\), min\(team_id\) \)", sql)
    assert match, sql
    assert "team_id" in match.group(1)


def test_a_quoted_column_expression_keeps_the_error_message_a_valid_string():
    sql = _render("if(kind in ('a', 'b'), x, y)")
    message = re.search(r"error\('([^']*)'\)", sql)
    assert message and "'" not in message.group(1), sql
    assert sql.endswith("min(if(kind in ('a', 'b'), x, y)) )")
