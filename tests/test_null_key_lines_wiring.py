"""A match where base loses a value to its team-id filter is listed by match.

The macro lines_without_key says which matches those are, from base's own selection: a statistics
line with no team id is lost where a stat it carries has no value for a team of the match from a
line with a team id in any fetch, and a line-up with no team id is lost where a team of the match
has no sheet in base_apif__lineup_sheets. The model base_apif__fixture_lines_without_key calls it,
the research list carries the matches as null_key_line_withheld, and two tests at error check the
rule: one derives the matches from staging, one runs hand-written lines through the macro. Each pin
fails when its wiring is undone.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DBT = ROOT / "dbt_project"
BASE = DBT / "models" / "2_base" / "api_football"
MART = DBT / "models" / "5_marts" / "shared"


def _sql(path):
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"\{#.*?#\}", " ", text, flags=re.DOTALL)
    text = re.sub(r"--[^\n]*", " ", text)
    return re.sub(r"\s+", " ", text)


def _macro():
    text = _sql(DBT / "macros" / "lines_without_key.sql")
    return text.split("macro lines_without_key", 1)[1].split("endmacro", 1)[0]


def _stat_types(text):
    return set(re.findall(r"'([A-Z][A-Za-z ]+)'", text))


def test_the_macro_takes_five_relations_and_calls_no_other_macro():
    text = _macro()
    assert text.lstrip().startswith("(statistics_lines, lineups, served_sheets, participants, overrides) -%}")
    assert "{{ fixture_player_id" not in text
    assert "raw_ingested_at" not in text


def test_the_macro_reads_the_stats_base_reads_and_no_others():
    base = _sql(BASE / "base_apif__fixture_statistics.sql")
    base_types = set(re.findall(r"stat_type = '([^']+)'", base))
    assert len(base_types) == 16
    block = _macro().split("case when stat_type = 'Ball Possession'", 1)[1].split("end as stat_value", 1)[0]
    assert "then safe_cast(regexp_replace(stat_value_raw, r'%', '') as int64)" in block
    listed = set(re.findall(r"'([^']+)'", block.split("stat_type in (", 1)[1].split(")", 1)[0]))
    assert listed | {"Ball Possession"} == base_types
    assert "then safe_cast(stat_value_raw as int64)" in block


def test_the_macro_judges_a_statistics_line_with_no_team_by_the_teams_that_have_the_stat_in_any_fetch():
    text = _macro()
    assert "from {{ statistics_lines }} where fixture_id is not null )" in text
    assert "where provider_team_id is null and stat_value is not null" in text
    assert "where provider_team_id is not null and stat_value is not null" in text
    assert "inner join {{ participants }} as match_teams on unnamed.fixture_id = match_teams.fixture_id" in text
    assert (
        "and unnamed.stat_type = named.stat_type and named.team_id in "
        "(match_teams.home_team_id, match_teams.away_team_id) group by"
    ) in text
    assert "group by unnamed.fixture_id, unnamed.stat_type having count(distinct named.team_id) < 2" in text


def test_the_macro_maps_a_team_the_way_base_does():
    text = _macro()
    base = _sql(BASE / "base_apif__fixture_statistics.sql")
    for mode in ("reattribute_in_fixture", "alias", "reattribute_if_cohabiting"):
        assert f"mode = '{mode}'" in text, mode
        assert f"mode = '{mode}'" in base, mode
    assert (
        "left join {{ overrides }} as fixture_override on line.provider_team_id = fixture_override.wrong_team_api_id "
        "and line.fixture_id = fixture_override.fixture_id and fixture_override.mode = 'reattribute_in_fixture'"
    ) in text
    assert (
        "left join {{ overrides }} as alias_override on line.provider_team_id = alias_override.wrong_team_api_id "
        "and alias_override.mode = 'alias'"
    ) in text
    assert "left join {{ participants }} as line_match on line.fixture_id = line_match.fixture_id" in text
    assert (
        "left join {{ overrides }} as reattribute_override on "
        "line.provider_team_id = reattribute_override.wrong_team_api_id "
        "and reattribute_override.mode = 'reattribute_if_cohabiting'"
    ) in text
    assert (
        "coalesce( fixture_override.correct_team_api_id, alias_override.correct_team_api_id, "
        "reattribute_override.correct_team_api_id, line.provider_team_id ) as team_id"
    ) in text
    assert "reattribute_override.correct_team_api_id in (line_match.home_team_id, line_match.away_team_id)" in text
    assert (
        "reattribute_override.wrong_team_api_id not in (line_match.home_team_id, line_match.away_team_id)"
    ) in text


def test_the_macro_judges_a_line_up_with_no_team_by_the_sheets_base_serves():
    text = _macro()
    assert "where fixture_id is not null and team_id is null" in text
    assert "from {{ lineups }} where" in text
    assert "left join {{ served_sheets }} as sheet on unnamed.fixture_id = sheet.fixture_id" in text
    assert "and sheet.team_id in (match_teams.home_team_id, match_teams.away_team_id) group by" in text
    assert "group by unnamed.fixture_id having count(distinct sheet.team_id) < 2" in text
    assert "'stg_apif__lineups' as line_table, 'team_id' as missing_key from lineups_lost" in text
    assert "'stg_apif__fixture_statistics' as line_table, 'team_id' as missing_key from statistics_lost" in text


def test_the_listing_model_calls_the_macro_with_staging_the_served_sheets_and_the_teams_of_the_match():
    text = _sql(BASE / "base_apif__fixture_lines_without_key.sql")
    assert "select distinct cast(fixture_id as int64) as fixture_id, line_table, missing_key from (" in text
    assert (
        "{{ lines_without_key( ref('stg_apif__fixture_statistics'), ref('stg_apif__lineups'), "
        "ref('base_apif__lineup_sheets'), 'participants', 'overrides' ) }}"
    ) in text
    assert (
        "participants as ( select fixture_id, cast(home_team_id as int64) as home_team_id, "
        "cast(away_team_id as int64) as away_team_id from {{ ref('base_apif__fixtures_next') }} "
        "where home_team_id is not null and away_team_id is not null )"
    ) in text
    assert "from {{ ref('fixture_team_id_overrides') }} )" in text
    assert "stg_apif__fixture_players" not in text
    assert "seed" not in text


def test_the_research_list_carries_the_matches_as_their_own_row_kind_with_no_seed():
    text = _sql(MART / "mart_competition_research_list.sql")
    assert (
        "select distinct 'null_key_line_withheld' as check_name, 'none' as seed, fixture_id as fixture_sk, "
        "cast(null as int64) as team_sk, cast(null as string) as correction "
        "from {{ ref('base_apif__fixture_lines_without_key') }} )"
    ) in text
    shared = (MART / "shared.yml").read_text(encoding="utf-8")
    assert shared.count('"lineup_duplicate_withheld", "null_key_line_withheld", "correction_no_longer_needed"]') == 1
    assert "player_id_overrides" not in shared


def test_the_listing_model_has_its_own_tests_at_error():
    text = (BASE / "base.yml").read_text(encoding="utf-8")
    block = text.split("- name: base_apif__fixture_lines_without_key", 1)[1].split("\n  - name: ", 1)[0]
    assert "combination_of_columns: [fixture_id, line_table, missing_key]" in block
    assert 'values: ["stg_apif__fixture_statistics", "stg_apif__lineups"]' in block
    assert 'values: ["team_id"]' in block
    assert "seed" not in block
    assert "severity" not in block
    assert "where:" not in block


def test_the_listing_test_derives_the_matches_from_staging_and_stays_at_error():
    text = _sql(DBT / "tests" / "assert_null_key_lines_listed.sql")
    assert "severity = 'error'" in text
    for model in ("stg_apif__fixture_statistics", "stg_apif__lineups"):
        assert f"ref('{model}')" in text, model
    assert "base_apif__fixture_lines_without_key" not in text
    assert "lines_without_key(" not in text
    assert "base_apif__lineup_sheets" not in text
    assert "check_name = 'null_key_line_withheld'" in text
    assert "'not_listed' as problem" in text
    assert "'listed_without_line' as problem" in text
    base_types = set(re.findall(r"stat_type = '([^']+)'", _sql(BASE / "base_apif__fixture_statistics.sql")))
    assert _stat_types(text.split("stat_type in (", 1)[1].split(")", 1)[0]) == base_types
    assert "having logical_or(statistic_lines.team_id is null and statistic_lines.has_value) and count(distinct if(" in text
    assert "statistic_lines.team_id in (participants.home_team_id, participants.away_team_id), statistic_lines.team_id, null )) < 2" in text
    assert "qualify row_number() over ( partition by league_code, fixture_id, team_id order by raw_ingested_at desc ) = 1" in text
    assert "and latest_sheets.has_players and latest_sheets.team_id in (participants.home_team_id" in text
    assert "having count(distinct latest_sheets.team_id) < 2" in text
    assert (
        "from {{ ref('base_apif__lineup_fetch_ties') }} as ties "
        "where ties.rows_differ and ties.fixture_id is not null"
    ) in text
    assert text.count("inner join rewritten_teams on lines.team_id = rewritten_teams.team_id") == 2
    assert "select distinct cast(wrong_team_api_id as int64) as team_id from {{ ref('fixture_team_id_overrides') }}" in text
    assert "inner join {{ ref('fct_fixture') }} as fixtures on expected.fixture_id = fixtures.fixture_sk" in text
    assert "left join left_out on expected.fixture_id = left_out.fixture_id where left_out.fixture_id is null" in text
    assert "research.check_name = 'null_key_line_withheld' and left_out.fixture_id is null" in text
    assert (
        "left join listed on expected_in_fixtures.fixture_id = listed.fixture_id "
        "where listed.fixture_id is null"
    ) in text
    assert (
        "left join expected_in_fixtures on listed.fixture_id = expected_in_fixtures.fixture_id "
        "where expected_in_fixtures.fixture_id is null"
    ) in text


def test_the_answer_key_runs_the_macro_on_its_own_lines_in_both_directions():
    text = _sql(DBT / "tests" / "assert_lines_without_key_answer_key.sql")
    assert "severity = 'error'" in text
    assert (
        "{{ lines_without_key('statistics_rows', 'lineup_rows', 'served_sheets', 'participants', 'overrides') }}"
    ) in text
    assert "'not_listed' as problem" in text
    assert "'listed_for_nothing' as problem" in text
    for row in (
        "struct(990000001 as fixture_id, cast(null as int64) as team_id, 'Fouls' as stat_type, '10' as stat_value_raw),",
        "struct(990000001, 5, 'Fouls', '12'),",
        "struct(990000001, 6, 'Corner Kicks', '3'),",
        "struct(990000002, cast(null as int64), 'Fouls', '10'),",
        "struct(990000002, 5, 'Fouls', '12'),",
        "struct(990000002, 6, 'Fouls', '9'),",
        "struct(990000003, cast(null as int64), 'Fouls', cast(null as string)),",
        "struct(990000003, cast(null as int64), 'Corner Kicks', 'n/a'),",
        "struct(990000004, cast(null as int64), 'Expected Goals', '1.2'),",
        "struct(990000005, cast(null as int64), 'Fouls', '10'),",
        "struct(990000005, 5, 'Fouls', '12'),",
        "struct(990000005, 7, 'Fouls', '11'),",
        "struct(990000006, cast(null as int64), 'Ball Possession', '45%'),",
        "struct(990000006, 5, 'Ball Possession', '55%'),",
        "struct(990000007, cast(null as int64), 'Fouls', '10'),",
        "struct(990000007, 99, 'Fouls', '11'),",
        "struct(990000008, cast(null as int64), 'Fouls', '10'),",
        "struct(990000014, cast(null as int64), 'Fouls', '10'),",
        "struct(990000014, 5, 'Fouls', '12'),",
        "struct(990000014, 8, 'Fouls', '11'),",
        "struct(990000015, cast(null as int64), 'Fouls', '10'),",
        "struct(990000015, 5, 'Fouls', '12'),",
        "struct(990000015, 8, 'Fouls', '11'),",
        "struct(990000016, cast(null as int64), 'Fouls', '10'),",
        "struct(990000016, 5, 'Fouls', '12'),",
        "struct(990000016, 9, 'Fouls', '11'),",
        "struct(990000017, cast(null as int64), 'Fouls', '10'),",
        "struct(990000017, 6, 'Fouls', '12'),",
        "struct(990000017, 9, 'Fouls', '11'),",
        "struct(990000014, 5, 6), struct(990000015, 5, 6), struct(990000016, 5, 6), struct(990000017, 6, 9),",
        "struct(8, 6, 'reattribute_in_fixture', 990000014), struct(9, 6, 'reattribute_if_cohabiting', cast(null as int64)) ])",
        "struct(cast(null as int64), cast(null as int64), 'Fouls', '10') ])",
        "struct(990000010 as fixture_id, cast(null as int64) as team_id),",
        "struct(990000010, 5),",
        "struct(990000011, cast(null as int64)),",
        "struct(990000011, 6),",
        "struct(990000012, cast(null as int64)),",
        "struct(990000013, 5),",
        "struct(cast(null as int64), cast(null as int64)) ])",
        "struct(990000010 as fixture_id, 5 as team_id),",
        "struct(990000011, 5),",
        "struct(990000012, 99),",
        "struct(990000013, 5) ])",
        "struct(7 as wrong_team_api_id, 5 as correct_team_api_id, 'alias' as mode, cast(null as int64) as fixture_id),",
    ):
        assert row in text, row
    assert "struct(990000008, 5, 6)," not in text
    assert (
        "struct(990000001 as fixture_id, 'stg_apif__fixture_statistics' as line_table, 'team_id' as missing_key), "
        "struct(990000005, 'stg_apif__fixture_statistics', 'team_id'), "
        "struct(990000006, 'stg_apif__fixture_statistics', 'team_id'), "
        "struct(990000007, 'stg_apif__fixture_statistics', 'team_id'), "
        "struct(990000015, 'stg_apif__fixture_statistics', 'team_id'), "
        "struct(990000010, 'stg_apif__lineups', 'team_id'), "
        "struct(990000012, 'stg_apif__lineups', 'team_id') ])"
    ) in text
    assert (
        "from expected as e left join actual as a on e.fixture_id = a.fixture_id and e.line_table = a.line_table "
        "and e.missing_key = a.missing_key where a.fixture_id is null"
    ) in text
    assert (
        "from actual as a left join expected as e on a.fixture_id = e.fixture_id and a.line_table = e.line_table "
        "and a.missing_key = e.missing_key where e.fixture_id is null"
    ) in text


def test_the_research_skill_does_not_research_the_row_kind():
    text = (ROOT / ".claude" / "skills" / "research-provider-errors" / "SKILL.md").read_text(encoding="utf-8")
    line = text.split("`null_key_line_withheld` row", 1)[1].split("\n", 1)[0]
    assert "is not researched" in line
    assert "no seed (`none`)" in line
