"""The models that withhold a score that stopped at 90 minutes read the checked score where they use it.

dbt 1.7 has no unit tests and prod holds no such match, so a reader that goes back to the unchecked
score leaves every data test green. These tests render the real model text, with the real macros,
and check the rendered SQL where the score enters each model.
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


def test_the_checked_model_counts_the_goal_events_with_a_scorer_of_a_match_decided_after_extra_time():
    goal_counts = _cte(render_model("base_apif__fixtures_checked"), "goal_counts")
    assert "from fixtures inner join `base_apif__fixture_events` as events on fixtures.fixture_id = events.fixture_id" in goal_counts
    assert "where fixtures.status_short in ('AET', 'PEN') and events.is_goal and coalesce(safe_cast(events.player_id as int64), 0) != 0" in goal_counts
    assert "countif(events.team_id = cast(fixtures.home_team_id as int64) and events.minute_elapsed <= 90) as home_goals_in_90" in goal_counts
    assert "countif(events.team_id = cast(fixtures.away_team_id as int64) and events.minute_elapsed <= 90) as away_goals_in_90" in goal_counts
    assert "countif(events.minute_elapsed > 90 and events.event_detail in ('Normal Goal', 'Own Goal')) as open_play_goals_after_90" in goal_counts
    assert "countif(events.minute_elapsed is null) as goals_without_minute" in goal_counts


def test_the_checked_model_flags_a_stopped_score_with_the_rule():
    checked = _cte(render_model("base_apif__fixtures_checked"), "checked")
    assert re.fullmatch(
        r"select fixtures\.\*, coalesce\( goal_counts\.goals_without_minute = 0 and goal_counts\.open_play_goals_after_90 > 0 "
        r"and goal_counts\.home_goals_in_90 = fixtures\.goals_home and goal_counts\.away_goals_in_90 = fixtures\.goals_away, "
        r"false \) as score_stops_at_90 from fixtures left join goal_counts on fixtures\.fixture_id = goal_counts\.fixture_id",
        checked,
    )


def test_the_checked_model_withholds_the_result_of_a_stopped_score():
    sql = render_model("base_apif__fixtures_checked")
    assert sql.endswith(
        "select * except (goals_home, goals_away, shootout_home, shootout_away, winner_team_id, result_needs_research), "
        "result_needs_research or score_stops_at_90 as result_needs_research, "
        "if(score_stops_at_90, null, goals_home) as goals_home, "
        "if(score_stops_at_90, null, goals_away) as goals_away, "
        "if(score_stops_at_90, null, shootout_home) as shootout_home, "
        "if(score_stops_at_90, null, shootout_away) as shootout_away, "
        "if(score_stops_at_90, null, winner_team_id) as winner_team_id from checked"
    )


def test_every_reader_of_the_score_downstream_of_the_events_reads_the_checked_model():
    for name, cte in (
        ("base_apif__fixture_players", "fixtures"),
        ("base_apif__fixture_players_from_lineups", "fixtures"),
        ("base_apif__fixture_statistics", "fixtures"),
        ("fct_fixture", "import_base_apif__fixtures_next"),
    ):
        body = _cte(render_model(name), cte)
        assert "from `base_apif__fixtures_checked`" in body, name
        assert "base_apif__fixtures_next`" not in body, name


def test_the_events_keep_reading_the_unchecked_score_so_the_models_do_not_form_a_cycle():
    sql = render_model("base_apif__fixture_events")
    assert "base_apif__fixtures_next" in sql
    assert "base_apif__fixtures_checked" not in sql
