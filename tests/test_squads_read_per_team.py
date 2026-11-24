"""A squad is read per team: no fetch row stands for its league, so no team is dropped with it.

RAW_APIF_SQUADS holds one row per fetch covering only the teams that fetch reached. These pins keep
staging reading every row, base taking the newest block of each team, and the readers of base
joining on the team.
"""

import pathlib
import re

DBT = pathlib.Path(__file__).resolve().parents[1] / "dbt_project"
STAGING = DBT / "models" / "1_staging" / "api_football" / "stg_apif__squads.sql"
BASE = DBT / "models" / "2_base" / "api_football" / "base_apif__squads.sql"
PAGE_PROFILE = DBT / "models" / "4_intermediate" / "shared" / "int_player__page_profile.sql"
PAGE_TEST = DBT / "tests" / "assert_player_page_choices_follow_the_rule.sql"
READ_PER_TEAM = DBT / "tests" / "assert_squads_read_per_team.sql"


def _sql(path):
    text = re.sub(r"\{#.*?#\}", " ", path.read_text(encoding="utf-8"), flags=re.DOTALL)
    text = re.sub(r"--[^\n]*", " ", text)
    return re.sub(r"\s+", " ", text).lower()


def test_staging_reads_every_row_and_no_league_snapshot():
    sql = _sql(STAGING)
    assert "qualify" not in sql and "partition by" not in sql


def test_staging_keeps_a_team_block_whose_list_is_empty():
    sql = _sql(STAGING)
    assert "left join unnest(json_query_array(json_query(team_blocks.team_block, '$.squad_payload'), '$')) as squad_el" in sql
    assert "left join unnest(json_query_array(json_query(squad_el, '$.players'), '$')) as player_el" in sql


def test_base_takes_each_teams_newest_block_after_the_team_id_override():
    sql = _sql(BASE)
    assert "max(raw_ingested_at) as raw_ingested_at from fetched group by team_id" in sql
    assert "src.raw_ingested_at = newest.raw_ingested_at" in sql
    assert "group by src.team_id, src.player_id, src.raw_ingested_at" in sql
    assert "team_id_override('team_id')" in sql


def test_a_reader_of_base_squads_does_not_join_on_the_league():
    for path in (PAGE_PROFILE, PAGE_TEST):
        sql = _sql(path)
        assert "from {{ ref('base_apif__squads') }} as sq" in sql
        body = sql.split("from {{ ref('base_apif__squads') }} as sq", 1)[1]
        body = body.split("),", 1)[0]
        assert "sq.league_code" not in body, path.name


def test_the_per_team_error_test_checks_raw_staging_and_base():
    sql = _sql(READ_PER_TEAM)
    assert "source('api_football', 'raw_apif_squads')" in sql
    assert "ref('stg_apif__squads')" in sql and "ref('base_apif__squads')" in sql
    assert "severity = 'error'" in sql
