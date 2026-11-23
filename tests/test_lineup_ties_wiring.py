"""A line-up the provider stored twice at one ingest time: identical collapses, differing is withheld.

The macro newest_fetch_ties finds the tied sheets of a team and says whether they differ. The team is
the team after fixture_team_id_overrides, which base_apif__lineup_fetches holds. The model
base_apif__lineup_fetch_ties holds the answer, base_apif__lineup_sheets and base_apif__fixture_players
leave a team with differing sheets out, the research list carries its match as
lineup_duplicate_withheld, and tests at error check the rule: a proof derived from the fetches model
and a hand-written answer key. Each pin fails when its wiring is undone.
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
    text = _sql(DBT / "macros" / "newest_fetch_ties.sql")
    return text.split("macro newest_fetch_ties", 1)[1].split("endmacro", 1)[0]


KEYS = "{{ key_columns | join(', ') }}"
TIES_JOIN = (
    "left join {{ ref('base_apif__lineup_fetch_ties') }} as ties on sheet.league_code = ties.league_code "
    "and sheet.fixture_id = ties.fixture_id and sheet.team_id = ties.team_id"
)
NOT_DIFFERING = "where not coalesce(ties.rows_differ, false)"


def test_the_macro_counts_the_newest_rows_of_each_key_and_compares_their_fingerprints():
    body = _macro()
    assert body.lstrip().startswith("(relation, key_columns, ignore_columns=[]) -%}")
    assert f"select {KEYS}, raw_ingested_at, count(*) as tied_rows, min(row_hash) != max(row_hash) as rows_differ" in body
    assert (
        "farm_fingerprint(to_json_string( {%- if ignore_columns %} (select as struct source_row.* except "
        "({{ ignore_columns | join(', ') }})) {%- else %} source_row {%- endif %} )) as row_hash"
    ) in body
    assert f"raw_ingested_at = max(raw_ingested_at) over (partition by {KEYS}) as in_newest_fetch" in body
    assert "from {{ relation }} as source_row ) where in_newest_fetch" in body
    assert f"group by {KEYS}, raw_ingested_at" in body
    assert "order by" not in body


def test_the_fetches_model_holds_every_sheet_under_the_team_after_the_correction():
    text = _sql(BASE / "base_apif__lineup_fetches.sql")
    assert (
        "with src as ( select league_code, fixture_id, team_id as provider_team_id, formation, start_xi_json, "
        "substitutes_json, raw_ingested_at from {{ ref('stg_apif__lineups') }} where fixture_id is not null "
        "and team_id is not null )"
    ) in text
    assert (
        "coalesce( fixture_override.correct_team_api_id, alias_override.correct_team_api_id, "
        "reattribute_override.correct_team_api_id, src.provider_team_id ) as team_id"
    ) in text
    assert (
        "src.provider_team_id = fixture_override.wrong_team_api_id and src.fixture_id = fixture_override.fixture_id "
        "and fixture_override.mode = 'reattribute_in_fixture'"
    ) in text
    assert "src.provider_team_id = alias_override.wrong_team_api_id and alias_override.mode = 'alias'" in text
    assert (
        "src.provider_team_id = reattribute_override.wrong_team_api_id "
        "and reattribute_override.mode = 'reattribute_if_cohabiting' "
        "and reattribute_override.correct_team_api_id in ( fixture_participants.home_team_id, "
        "fixture_participants.away_team_id ) and reattribute_override.wrong_team_api_id not in ( "
        "fixture_participants.home_team_id, fixture_participants.away_team_id )"
    ) in text
    assert "from {{ ref('fixture_team_id_overrides') }}" in text
    assert "from {{ ref('base_apif__fixtures_next') }} where home_team_id is not null and away_team_id is not null" in text


def test_the_ties_model_compares_the_sheets_of_a_team_after_the_correction_and_ignores_our_own_columns():
    text = _sql(BASE / "base_apif__lineup_fetch_ties.sql")
    assert (
        "{{ newest_fetch_ties( ref('base_apif__lineup_fetches'), ['league_code', 'fixture_id', 'team_id'], "
        "['raw_ingested_at', 'provider_team_id'] ) }}"
    ) in text
    for column in ("league_code", "fixture_id", "team_id", "raw_ingested_at", "tied_rows", "rows_differ"):
        assert column in text.split("from (")[0], column


def test_a_team_with_differing_sheets_has_no_sheet_and_identical_sheets_collapse():
    text = _sql(BASE / "base_apif__lineup_sheets.sql")
    src = text.split("with src as (", 1)[1].split("), fetches as (", 1)[0]
    assert "from {{ ref('base_apif__lineup_fetches') }} as sheet " + TIES_JOIN in src
    assert NOT_DIFFERING in src
    assert "stg_apif__lineups" not in text
    assert "overrides" not in text.split("), fetches as (", 1)[0]
    latest = text.split("latest as (", 1)[1].split("), named", 1)[0]
    assert (
        "qualify row_number() over ( partition by league_code, fixture_id, team_id order by raw_ingested_at desc ) = 1"
    ) in latest


def test_the_grid_lender_lends_only_when_the_candidates_of_its_ingest_time_agree():
    latest = _sql(BASE / "base_apif__lineup_sheets.sql").split("latest as (", 1)[1].split("), named", 1)[0]
    assert (
        "farm_fingerprint(to_json_string(struct(h.fetch_formation, h.fetch_start_xi_json))) as content_hash"
    ) in latest
    assert (
        "qualify candidate.fetched_at = max(candidate.fetched_at) over () "
        "and min(candidate.content_hash) over (partition by candidate.fetched_at) "
        "= max(candidate.content_hash) over (partition by candidate.fetched_at) "
        "order by candidate.fetched_at desc limit 1"
    ) in latest
    assert "order by h.fetched_at desc" not in latest


def test_the_player_lines_read_from_line_ups_leave_a_differing_team_out():
    text = _sql(BASE / "base_apif__fixture_players.sql")
    sheets = text.split("latest_sheets as (", 1)[1].split("), sheet_players", 1)[0]
    assert (
        "select sheet.fixture_id, sheet.provider_team_id as team_id, sheet.start_xi_json, sheet.substitutes_json "
        "from {{ ref('base_apif__lineup_fetches') }} as sheet " + TIES_JOIN
    ) in sheets
    assert NOT_DIFFERING in sheets
    assert (
        "qualify row_number() over ( partition by sheet.fixture_id, sheet.provider_team_id "
        "order by sheet.raw_ingested_at desc ) = 1"
    ) in sheets
    assert "stg_apif__lineups" not in text


def test_the_research_list_carries_a_differing_line_up_as_its_own_row_kind():
    text = _sql(MART / "mart_competition_research_list.sql")
    assert (
        "select distinct 'lineup_duplicate_withheld' as check_name, 'none' as seed, fixture_id as fixture_sk, "
        "cast(null as int64) as team_sk, cast(null as string) as correction "
        "from {{ ref('base_apif__lineup_fetch_ties') }} where rows_differ union all select distinct '"
    ) in text
    shared = (MART / "shared.yml").read_text(encoding="utf-8")
    assert shared.count('"lineup_duplicate_withheld", "null_key_line_withheld", "correction_no_longer_needed"]') == 1
    assert shared.count('"fixture_lineup_corrections", "none"]') == 1


def test_the_staging_test_is_gone_and_the_base_proof_stays_at_error():
    staging = (DBT / "models" / "1_staging" / "api_football" / "stg_apif__generic.yml").read_text(encoding="utf-8")
    assert "stg_apif__lineups_order_keys_unique" not in staging
    block = staging.split("- name: stg_apif__lineups", 1)[1].split("\n  - name: ", 1)[0]
    assert "\n    tests:" not in block
    assert "\n    data_tests:" not in block
    base = (BASE / "base.yml").read_text(encoding="utf-8")
    sheets = base.split("- name: base_apif__lineup_sheets", 1)[1].split("\n  - name: ", 1)[0]
    assert "combination_of_columns: [league_code, fixture_id, team_id, is_starter, sheet_index]" in sheets
    assert "severity" not in sheets
    assert "where:" not in sheets
    ties = base.split("- name: base_apif__lineup_fetch_ties", 1)[1].split("\n  - name: ", 1)[0]
    assert "combination_of_columns: [league_code, fixture_id, team_id]" in ties
    assert "severity" not in ties
    assert "where:" not in ties


def test_the_proof_derives_the_differing_teams_from_the_fetches_and_stays_at_error():
    text = _sql(DBT / "tests" / "assert_lineup_fetches_never_tie.sql")
    assert "severity = 'error'" in text
    assert "from {{ ref('base_apif__lineup_fetches') }} ) as sheet" in text
    assert "base_apif__lineup_fetch_ties" not in text
    assert "newest_fetch_ties(" not in text
    assert (
        "* except (raw_ingested_at, provider_team_id), raw_ingested_at = max(raw_ingested_at) "
        "over (partition by league_code, fixture_id, team_id)"
    ) in text
    assert "group by league_code, fixture_id, team_id having count(distinct sheet_json) > 1" in text
    for model, alias in (("base_apif__lineup_sheets", "sheets"), ("base_apif__lineups", "lineups")):
        assert (
            f"from {{{{ ref('{model}') }}}} as {alias} inner join differing_teams on "
            f"{alias}.league_code = differing_teams.league_code and {alias}.fixture_id = differing_teams.fixture_id "
            f"and {alias}.team_id = differing_teams.team_id"
        ) in text, model
    assert "where lineups.lineup_state != 'researched'" in text


def test_the_grid_test_picks_the_lender_the_way_base_does():
    text = _sql(DBT / "tests" / "assert_lineup_fetch_keeps_grid_only_for_same_eleven.sql")
    candidates = text.split("lender_candidates as (", 1)[1].split("), lender as (", 1)[0]
    assert "farm_fingerprint(to_json_string(struct(f.formation, f.start_xi_json))) as content_hash" in candidates
    assert "where not n.has_grid and f.has_grid and f.starting_eleven = n.starting_eleven" in candidates
    lender = text.split("), lender as (", 1)[1].split("), lent_places", 1)[0]
    assert "from lender_candidates as f" in lender
    assert (
        "qualify f.raw_ingested_at = max(f.raw_ingested_at) over (partition by f.league_code, f.fixture_id, f.team_id) "
        "and min(content_hash) over (partition by f.league_code, f.fixture_id, f.team_id, f.raw_ingested_at) "
        "= max(content_hash) over (partition by f.league_code, f.fixture_id, f.team_id, f.raw_ingested_at) "
        "and row_number() over (partition by f.league_code, f.fixture_id, f.team_id order by f.raw_ingested_at desc) = 1"
    ) in lender


def test_the_answer_key_runs_the_macro_on_its_own_rows():
    text = _sql(DBT / "tests" / "assert_newest_fetch_ties_answer_key.sql")
    assert "severity = 'error'" in text
    assert (
        "{{ newest_fetch_ties('sheet_rows', ['fixture_id', 'team_id'], ['load_offset', 'provider_team_id']) }}"
    ) in text
    assert (
        "struct( 1 as fixture_id, 10 as team_id, 2 as raw_ingested_at, 'a' as sheet, 1 as load_offset, "
        "10 as provider_team_id ),"
    ) in text
    for row in (
        "struct(2, 10, 2, 'b', 1, 10),",
        "struct(3, 10, 2, 'a', 1, 10),",
        "struct(4, 10, 1, 'a', 1, 10),",
        "struct(4, 10, 1, 'b', 1, 10),",
        "struct(4, 10, 2, 'a', 1, 10),",
        "struct(5, 10, 1, 'a', 1, 10),",
        "struct(5, 10, 2, 'b', 1, 10),",
        "struct(6, 11, 2, 'a', 1, 11),",
        "struct(6, 11, 2, 'b', 1, 11),",
        "struct(8, 10, 3, 'a', 1, 10),",
        "struct(8, 11, 2, 'a', 1, 11),",
        "struct(8, 11, 2, 'b', 1, 11),",
        "struct(9, 10, 2, 'a', 1, 10),",
        "struct(9, 10, 2, 'a', 2, 10),",
        "struct(10, 10, 2, 'a', 1, 10),",
        "struct(10, 10, 2, 'b', 2, 10),",
        "struct(11, 10, 2, 'a', 1, 100),",
        "struct(11, 10, 2, 'a', 1, 101),",
        "struct(12, 10, 2, 'a', 1, 100),",
        "struct(12, 10, 2, 'b', 1, 101) ])",
    ):
        assert text.count(row) == 1, row
    assert text.count("struct(7, 10, 2, 'a', 1, 10)") == 3
    assert text.count("struct(1, 10, 2, 'a', 1, 10),") == 1
    assert text.count("struct(2, 10, 2, 'a', 1, 10),") == 1
    assert text.count("struct(6, 10, 2, 'a', 1, 10),") == 2
    assert (
        "struct(1 as fixture_id, 10 as team_id, 2 as tied_rows, false as rows_differ), "
        "struct(2, 10, 2, true), struct(3, 10, 1, false), struct(4, 10, 1, false), "
        "struct(5, 10, 2, true), struct(6, 10, 2, false), struct(6, 11, 2, true), "
        "struct(7, 10, 3, false), struct(8, 10, 1, false), struct(8, 11, 2, true), "
        "struct(9, 10, 2, false), struct(10, 10, 2, true), struct(11, 10, 2, false), "
        "struct(12, 10, 2, true) ])"
    ) in text
    assert (
        "from expected as e full outer join actual as a on e.fixture_id = a.fixture_id and e.team_id = a.team_id "
        "where e.fixture_id is null or a.fixture_id is null or e.tied_rows != a.tied_rows "
        "or e.rows_differ != a.rows_differ"
    ) in text


def test_the_cleaning_rule_names_the_withheld_line_up():
    text = (DBT / "models" / "docs" / "cleaning_rules.md").read_text(encoding="utf-8")
    assert (
        "  - A team whose line-up the provider stored twice at the newest ingest time with different content "
        "has no sheet, and the match is listed; identical copies count once."
    ) in text


def test_the_research_skill_does_not_research_the_row_kind():
    text = (ROOT / ".claude" / "skills" / "research-provider-errors" / "SKILL.md").read_text(encoding="utf-8")
    assert "`lineup_duplicate_withheld` row is not researched" in text
