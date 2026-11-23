"""The statistics model leaves a card count blank in a match with an event filed under a team that did not play it.

dbt 1.7 has no unit tests and prod holds no such event, so a guard that is removed leaves every data
test green. These tests render the real model text, with the real macros, and check the rendered
SQL where the guard is set and read.
"""

import pathlib
import re
import types

import jinja2

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


def test_a_match_with_an_event_under_a_team_that_did_not_play_it_is_marked():
    match_events = _cte(render_model("base_apif__fixture_statistics"), "match_events")
    assert re.fullmatch(
        r"select events\.fixture_id, logical_or\(events\.has_full_events\) as events_delivered, "
        r"coalesce\( logical_or\(coalesce\( events\.team_id is not null and fixtures\.home_team_id is not null "
        r"and fixtures\.away_team_id is not null and events\.team_id not in \(fixtures\.home_team_id, "
        r"fixtures\.away_team_id\), false \)\), false \) as has_misfiled_event, "
        r"max\(events\.raw_ingested_at\) as events_ingested_at from events "
        r"left join fixtures on events\.fixture_id = fixtures\.fixture_id group by events\.fixture_id",
        match_events,
    )


def test_the_events_of_such_a_match_bound_no_card_count():
    matches = _cte(render_model("base_apif__fixture_statistics"), "matches_with_events")
    assert re.fullmatch(
        r"select events\.fixture_id from `base_apif__fixture_events` as events "
        r"left join fixture_participants as participants on events\.fixture_id = participants\.fixture_id "
        r"group by events\.fixture_id having logical_or\(events\.has_full_events\) "
        r"and not coalesce\( logical_or\(coalesce\( events\.team_id is not null and participants\.home_team_id is not null "
        r"and participants\.away_team_id is not null and events\.team_id not in "
        r"\(participants\.home_team_id, participants\.away_team_id\), false \)\), false \)",
        matches,
    )
    assert re.search(r"left join matches_with_events as m on n\.fixture_id = m\.fixture_id", render_model("base_apif__fixture_statistics"))


def test_the_mark_reaches_the_fill_of_a_card_count():
    sql = render_model("base_apif__fixture_statistics")
    assert "coalesce(me.has_misfiled_event, false) as has_misfiled_event" in _cte(sql, "in_context")
    assert re.search(
        r"coalesce\( cards_yellow, if\( opponent_cards_yellow is not null "
        r"or \(events_delivered and not has_misfiled_event and events_against_no_yellow = 0\), 0, null \) "
        r"\) as cards_yellow_filled",
        sql,
    )
    assert re.search(
        r"coalesce\( cards_red, if\( opponent_cards_red is not null "
        r"or \(events_delivered and not has_misfiled_event and events_against_no_red = 0\), 0, null \) "
        r"\) as cards_red_filled",
        sql,
    )
