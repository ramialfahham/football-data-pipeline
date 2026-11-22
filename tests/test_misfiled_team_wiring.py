"""The models that withhold a line filed under a team that did not play the match call the rule where the line leaves them.

dbt 1.7 has no unit tests and prod holds no such line, so a call site that is reverted leaves every
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


def _flag(team: str, home: str, away: str) -> str:
    team, home, away = (re.escape(part) for part in (team, home, away))
    return (
        rf"coalesce\( {team} is not null and {home} is not null and {away} is not null "
        rf"and {team} not in \({home}, {away}\), false \) as team_needs_research"
    )


PARTICIPANTS = r"select fixture_id, cast\(home_team_id as int64\) as home_team_id, cast\(away_team_id as int64\) as away_team_id from `base_apif__fixtures_next`"
PARTICIPANTS_RENAMED = (
    r"select fixture_id as participant_fixture_id, cast\(home_team_id as int64\) as home_team, "
    r"cast\(away_team_id as int64\) as away_team from `base_apif__fixtures_next`"
)


def test_an_event_is_flagged_when_its_team_is_not_one_of_the_match_teams():
    sql = render_model("base_apif__fixture_events_checked")
    assert re.fullmatch(PARTICIPANTS, _cte(sql, "participants").strip())
    assert re.search(_flag("events.team_id", "participants.home_team_id", "participants.away_team_id"), sql)
    assert re.search(r"from events left join checked on .*? left join participants on events\.fixture_id = participants\.fixture_id$", sql)


def test_a_player_line_is_flagged_and_the_flag_reaches_the_output():
    sql = render_model("base_apif__fixture_players_checked")
    assert re.fullmatch(PARTICIPANTS, _cte(sql, "participants").strip())
    assert re.search(
        r"checked_players as \( select players\.\*, "
        + _flag("players.team_id", "participants.home_team_id", "participants.away_team_id"),
        sql,
    )
    assert re.search(r"left join participants on players\.fixture_id = participants\.fixture_id \)", sql)
    assert sql.endswith("stat_corrections, team_needs_research from checked_players")


def test_a_line_up_player_is_flagged_and_the_flag_reaches_the_output():
    sql = render_model("base_apif__fixture_players_from_lineups")
    assert re.fullmatch(PARTICIPANTS_RENAMED, _cte(sql, "participants").strip())
    flagged = _cte(sql, "flagged")
    assert re.fullmatch(
        r"select c\.\*, " + _flag("c.team_id", "p.home_team", "p.away_team")
        + r" from cleaned as c left join participants as p on c\.fixture_id = p\.participant_fixture_id",
        flagged.strip(),
    )
    assert sql.endswith("raw_ingested_at, team_needs_research, goals_need_research from flagged")


def test_a_match_with_a_misfiled_event_proves_no_cards_of_its_line_up_players():
    sql = render_model("base_apif__fixture_players_from_lineups")
    assert re.search(r"has_full_events, team_needs_research, assist_player_name is not null or assist_needs_research as is_assisted from `base_apif__fixture_events_checked`", sql)
    assert _cte(sql, "match_events").endswith(
        "logical_or(has_full_events) and not logical_or(team_needs_research) as has_full_events from events group by fixture_id"
    )
    assert "coalesce(m.has_full_events, false)" in sql


def test_a_statistics_line_is_flagged_and_the_flag_reaches_the_output():
    sql = render_model("base_apif__fixture_statistics")
    assert re.fullmatch(PARTICIPANTS_RENAMED, _cte(sql, "participants").strip())
    flagged = _cte(sql, "flagged")
    assert re.fullmatch(
        r"select c\.\*, " + _flag("c.team_id", "p.home_team", "p.away_team")
        + r" from cleaned as c left join participants as p on c\.fixture_id = p\.participant_fixture_id",
        flagged.strip(),
    )
    assert re.search(r"raw_ingested_at, team_needs_research, array\(", sql)
    assert sql.endswith("as stat_corrections from flagged")


@pytest.mark.parametrize("fact", ["fct_fixture_event", "fct_fixture_player_stats"])
def test_a_fact_leaves_out_the_lines_that_are_flagged(fact):
    assert render_model(fact).endswith("from src where not team_needs_research")


def test_the_research_list_holds_every_flagged_line_under_the_team_the_provider_filed_it_under():
    sql = render_model("mart_competition_research_list")
    lines = _cte(sql, "misfiled_lines")
    for model in (
        "base_apif__fixture_events_checked",
        "base_apif__fixture_players_checked",
        "base_apif__fixture_players_from_lineups",
        "base_apif__fixture_statistics",
    ):
        assert re.search(rf"select fixture_id, team_id from `{model}` where team_needs_research", lines), model
    assert re.search(
        r"from `base_apif__fixture_players_from_lineups` where goals_need_research and not team_needs_research\b",
        _cte(sql, "items"),
    )
    assert lines.startswith("select distinct cast(fixture_id as int64) as fixture_sk, cast(team_id as int64) as provider_team_id ")


def test_the_research_list_keeps_a_team_key_only_where_the_team_is_in_dim_team():
    sql = render_model("mart_competition_research_list")
    items = _cte(sql, "misfiled_items")
    assert "'fixture_team_id_overrides' as seed" in items
    assert "t.team_sk, cast(null as string) as correction, m.provider_team_id" in items
    assert items.endswith("from misfiled_lines as m left join `dim_team` as t on m.provider_team_id = t.team_sk")
    assert re.search(
        r"select m\.check_name, m\.seed, m\.fixture_sk, m\.team_sk, m\.correction, m\.provider_team_id, "
        r"f\.league_code, f\.season_api_year from misfiled_items as m inner join fixtures as f on m\.fixture_sk = f\.fixture_sk",
        sql,
    )
    assert "cast(coalesce(a.provider_team_id, a.team_sk) as string)" in sql
