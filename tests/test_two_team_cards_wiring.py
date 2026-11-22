"""The models that withhold a two-team player's cards call the rule where the cards leave them.

dbt 1.7 has no unit tests and prod holds no player whose card events name two teams, so a call site
that is reverted leaves every data test green. These tests render the real model text, with the real
macros, and check the rendered SQL at the expression that carries the withholding.
"""

import pathlib
import re

import jinja2
import pytest

DBT = pathlib.Path(__file__).resolve().parents[1] / "dbt_project"
MACROS = DBT / "macros"
MODELS = DBT / "models"


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


def render_model(name: str) -> str:
    """The model's SQL with every dbt macro and ref expanded, whitespace collapsed."""
    (path,) = MODELS.rglob(f"{name}.sql")
    template = _environment().from_string(path.read_text(encoding="utf-8"))
    return " ".join(re.sub(r"--[^\n]*", "", template.render()).split())


def _cte(sql: str, name: str) -> str:
    """The body of the CTE `name`, up to its closing parenthesis."""
    start = re.search(rf"\b{name} as \( ", sql)
    assert start, f"no CTE {name}"
    depth = 1
    for position in range(start.end(), len(sql)):
        depth += {"(": 1, ")": -1}.get(sql[position], 0)
        if depth == 0:
            return sql[start.end():position]
    raise AssertionError(f"CTE {name} is not closed")


@pytest.fixture(scope="module")
def players_sql():
    return render_model("base_apif__fixture_players")


@pytest.fixture(scope="module")
def lineups_sql():
    return render_model("base_apif__fixture_players_from_lineups")


@pytest.fixture(scope="module")
def lines_sql():
    return render_model("base_apif__fixture_player_lines")


@pytest.fixture(scope="module")
def list_sql():
    return render_model("mart_competition_research_list")


def test_the_player_line_withholds_the_cards_of_a_player_whose_card_events_name_two_teams(players_sql):
    assert re.search(
        r"cards_naming_two_teams as \( select fixture_id, player_id from events where event_type = 'Card' ", players_sql
    )
    assert re.search(
        r"left join cards_naming_two_teams as tt on d\.fixture_id = tt\.fixture_id and d\.player_id = tt\.player_id",
        players_sql,
    )
    assert re.search(
        r"rm\.fixture_id is null and \( dp\.fixture_id is not null or tt\.fixture_id is not null or \(.*?\) "
        r"\) as cards_need_research",
        players_sql,
    )


def test_the_line_up_row_does_not_prove_the_cards_of_a_two_team_player_in_an_unresearched_match(lineups_sql):
    assert re.search(
        r"cards_naming_two_teams as \( select fixture_id, player_id from events where event_type = 'Card' ", lineups_sql
    )
    assert re.search(
        r"left join cards_naming_two_teams as tt on s\.fixture_id = tt\.fixture_id and s\.player_id = tt\.player_id "
        r"left join researched_card_matches as rm on s\.fixture_id = rm\.fixture_id",
        lineups_sql,
    )
    assert re.search(r"and \(tt\.fixture_id is null or rm\.fixture_id is not null\) as cards_are_proven", lineups_sql)
    assert _cte(lineups_sql, "researched_card_matches") == "select distinct fixture_id from `fixture_card_corrections` "


@pytest.mark.parametrize("sql_fixture", ["players_sql", "lines_sql"])
def test_no_player_cards_query_raises_an_error_on_a_player_with_two_teams(request, sql_fixture):
    assert "error(" not in _cte(request.getfixturevalue(sql_fixture), "player_cards")


def test_a_card_with_no_player_on_the_match_is_checked_for_every_team_its_player_is_named_under(players_sql):
    assert _cte(players_sql, "player_card_teams").startswith("select distinct fixture_id, team_id, player_id from events ")
    assert re.search(
        r"from player_card_teams as c inner join team_stat_cards as s "
        r"on c\.fixture_id = s\.fixture_id and c\.team_id = s\.team_id "
        r"left join delivered as d on c\.fixture_id = d\.fixture_id and c\.player_id = d\.player_id",
        players_sql,
    )


def test_the_research_list_holds_the_match_of_a_two_team_player_unless_it_is_researched(list_sql):
    branch = list_sql.split("'cards_withheld' as check_name", 1)[1].split("'lineup_goals_withheld' as check_name", 1)[0]
    assert re.search(
        r"select two_team_players\.fixture_id from \(select fixture_id, player_id from `base_apif__fixture_events_checked` "
        r"where event_type = 'Card' .*? having count\(distinct team_id\) > 1\) as two_team_players "
        r"left join `fixture_card_corrections` as researched on two_team_players\.fixture_id = researched\.fixture_id "
        r"where researched\.fixture_id is null",
        branch,
    )
