"""The models that withhold a provider error call the withholding macros where the value leaves them.

dbt 1.7 has no unit tests and prod holds no input that triggers a withhold, so a call site that is
reverted leaves every data test green. These tests render the real model text, with the real
macros, and check the rendered SQL at the column that carries the value.
"""

import pathlib
import re

import jinja2
import pytest

DBT = pathlib.Path(__file__).resolve().parents[1] / "dbt_project"
MACROS = DBT / "macros"
BASE = DBT / "models" / "2_base" / "api_football"


def _environment() -> jinja2.Environment:
    environment = jinja2.Environment()
    environment.globals.update(
        ref=lambda name: f"`{name}`",
        source=lambda source, name: f"`{source}.{name}`",
        config=lambda **kwargs: "",
        var=lambda name, default=None: default,
    )
    text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(MACROS.glob("*.sql")))
    module = environment.from_string(text).module
    environment.globals.update({name: getattr(module, name) for name in dir(module) if not name.startswith("_")})
    return environment


def render_model(file_name: str) -> str:
    """The model's SQL with every dbt macro and ref expanded, whitespace collapsed."""
    environment = _environment()
    template = environment.from_string((BASE / file_name).read_text(encoding="utf-8"))
    return " ".join(template.render().split())


@pytest.fixture(scope="module")
def players_sql():
    return render_model("base_apif__players.sql")


def _withhold(field: str) -> str:
    return (
        rf"if\(\(latest\.has_conflicting_{field}\) and not \({field}_fix\.player_api_id is not null\), "
        r"null, "
    )


def test_a_birth_date_is_blank_while_its_records_conflict_and_no_correction_settles_it(players_sql):
    assert re.search(r"safe_cast\( " + _withhold("birth_date") + r".*? as date \) as player_birth_date\b", players_sql)


def test_a_nationality_is_blank_while_its_records_conflict_and_no_correction_settles_it(players_sql):
    assert re.search(
        r"nullif\( trim\( " + _withhold("nationality") + r".*?\) \), '' \) as player_nationality\b", players_sql
    )


@pytest.mark.parametrize("field", ["birth_date", "nationality"])
def test_the_flag_is_true_exactly_where_the_value_is_withheld(players_sql, field):
    flag = (
        rf"latest\.has_conflicting_{field} and {field}_fix\.player_api_id is null "
        rf"as {field}_needs_research"
    )
    assert re.search(flag, players_sql)


def test_the_flags_reach_the_model_output(players_sql):
    output = players_sql.rsplit(" select player_api_id,", 1)[1]
    assert "birth_date_needs_research, nationality_needs_research," in output
