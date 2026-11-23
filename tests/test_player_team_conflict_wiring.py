"""The models that withhold a player whose stat line and events name different teams call the rule where the line leaves them.

dbt 1.7 has no unit tests and prod holds no such player, so a call site that is reverted leaves every
data test green. These tests render the real model text, with the real macros, and check the
rendered SQL at the expression that carries the withholding.
"""

import pathlib
import re
import types

import jinja2
import pytest

DBT = pathlib.Path(__file__).resolve().parents[1] / "dbt_project"
MACROS = DBT / "macros"
MODELS = DBT / "models"

RULE_BODY = (
    r"select distinct r\.fixture_id, r\.player_id from {player_rows} as r inner join {events} as e "
    r"on r\.fixture_id = e\.fixture_id and r\.player_id = e\.player_id "
    r"inner join {participants} as p on r\.fixture_id = p\.fixture_id "
    r"where e\.team_id != r\.team_id and r\.team_id in \(p\.home_team_id, p\.away_team_id\) "
    r"and e\.team_id in \(p\.home_team_id, p\.away_team_id\) "
    r"and not \(e\.event_type = 'Goal' and e\.event_detail = 'Own Goal'\) "
    r"and e\.goal_correction_source is null and e\.card_correction_source is null"
)


def _environment() -> jinja2.Environment:
    environment = jinja2.Environment()
    environment.globals.update(
        ref=lambda name: f"`{name}`",
        source=lambda source, name: f"`{source}.{name}`",
        config=lambda **kwargs: "",
        var=lambda name, default=None: default,
        dbt_utils=types.SimpleNamespace(generate_surrogate_key=lambda columns: "surrogate_key"),
    )
    text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(MACROS.glob("*.sql")))
    module = environment.from_string(text).module
    environment.globals.update({name: getattr(module, name) for name in dir(module) if not name.startswith("_")})
    return environment


def render_model(name: str) -> str:
    """The model's SQL with every dbt macro and ref expanded, comments removed, whitespace collapsed."""
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
            return sql[start.end():position].strip()
    raise AssertionError(f"CTE {name} is not closed")


def _rule(player_rows: str, events: str, participants: str) -> str:
    return RULE_BODY.format(
        player_rows=re.escape(player_rows), events=re.escape(events), participants=re.escape(participants)
    )


def test_an_event_is_flagged_for_a_player_whose_events_and_stat_line_name_different_teams():
    sql = render_model("base_apif__fixture_events_checked")
    assert re.fullmatch(_rule("`base_apif__fixture_players`", "events", "participants"), _cte(sql, "disputed_players"))
    assert re.search(r"disputed_players\.fixture_id is not null as player_team_needs_research from events", sql)
    assert sql.endswith(
        "left join disputed_players on events.fixture_id = disputed_players.fixture_id "
        "and events.player_id = disputed_players.player_id"
    )


def test_a_player_line_is_flagged_and_the_flag_reaches_the_output():
    sql = render_model("base_apif__fixture_players_checked")
    assert re.fullmatch(
        _rule("`base_apif__fixture_players`", "`base_apif__fixture_events`", "participants"),
        _cte(sql, "disputed_players"),
    )
    assert re.search(
        r"as team_needs_research, disputed_players\.fixture_id is not null as player_team_needs_research, ", sql
    )
    assert re.search(
        r"left join disputed_players on players\.fixture_id = disputed_players\.fixture_id "
        r"and players\.player_id = disputed_players\.player_id \)",
        sql,
    )
    assert sql.endswith("stat_corrections, team_needs_research, player_team_needs_research from checked_players")


def test_a_line_up_player_is_flagged_and_the_flag_reaches_the_output():
    sql = render_model("base_apif__fixture_players_from_lineups")
    participants = (
        "(select participant_fixture_id as fixture_id, home_team as home_team_id, "
        "away_team as away_team_id from participants)"
    )
    assert re.fullmatch(
        _rule("`base_apif__fixture_players`", "`base_apif__fixture_events`", participants),
        _cte(sql, "disputed_players"),
    )
    assert re.search(
        r"as team_needs_research, d\.fixture_id is not null as player_team_needs_research "
        r"from cleaned as c left join participants as p on c\.fixture_id = p\.participant_fixture_id "
        r"left join disputed_players as d on c\.fixture_id = d\.fixture_id and c\.player_id = d\.player_id",
        _cte(sql, "flagged"),
    )
    assert sql.endswith("team_needs_research, player_team_needs_research, goals_need_research from flagged")


@pytest.mark.parametrize("fact", ["fct_fixture_event", "fct_fixture_player_stats"])
def test_a_fact_leaves_out_the_lines_of_a_disputed_player(fact):
    assert render_model(fact).endswith("from src where not team_needs_research and not player_team_needs_research")


def test_the_research_list_holds_the_match_of_a_disputed_player():
    items = _cte(render_model("mart_competition_research_list"), "items")
    assert items.endswith(
        "select distinct 'player_team_withheld' as check_name, 'fixture_lineup_corrections' as seed, "
        "cast(fixture_id as int64) as fixture_sk, cast(null as int64) as team_sk, cast(null as string) as correction "
        "from `base_apif__fixture_events_checked` where player_team_needs_research"
    )
