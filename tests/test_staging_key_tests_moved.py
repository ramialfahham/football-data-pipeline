"""A provider key that base drops when NULL is tested in base, not in staging.

The staging not_null tests on provider keys stopped the nightly on a provider payload. Base drops
the NULL-key rows and its own not_null tests prove it. This test pins the move: no removed staging
test is back, each has its base proof in yml at error without a filter, every read of a moved
staging model carries its key filter, and the staging uniqueness tests stay at error.
"""

import pathlib
import re

import pytest
import yaml

DBT = pathlib.Path(__file__).resolve().parents[1] / "dbt_project"
STAGING = DBT / "models" / "1_staging" / "api_football" / "stg_apif__generic.yml"
BASE = DBT / "models" / "2_base" / "api_football" / "base.yml"
BASE_SQL = DBT / "models" / "2_base" / "api_football"

# (staging model, staging column, base model, base column)
NULL_KEYS = [
    ("stg_apif__fixtures_next", "fixture_id", "base_apif__fixtures_next", "fixture_id"),
    ("stg_apif__fixture_events", "fixture_id", "base_apif__fixture_events", "fixture_id"),
    ("stg_apif__fixture_statistics", "fixture_id", "base_apif__fixture_statistics", "fixture_id"),
    ("stg_apif__fixture_statistics", "team_id", "base_apif__fixture_statistics", "team_id"),
    ("stg_apif__lineups", "fixture_id", "base_apif__lineup_fetches", "fixture_id"),
    ("stg_apif__lineups", "team_id", "base_apif__lineup_fetches", "team_id"),
    ("stg_apif__teams", "team_id", "base_apif__teams", "team_api_id"),
    ("stg_apif__leagues", "league_api_id", "base_apif__leagues", "league_api_id"),
    ("stg_apif__leagues", "season_api_year", "base_apif__leagues", "season_api_year"),
    ("stg_apif__players", "player_id", "base_apif__players", "player_api_id"),
    ("stg_apif__players", "team_id", "base_apif__player_team_season", "team_id"),
    ("stg_apif__player_profiles", "player_id", "base_apif__player_profiles", "player_api_id"),
    ("stg_apif__squads", "team_id", "base_apif__squads", "team_api_id"),
    ("stg_apif__squads", "player_id", "base_apif__squads", "player_api_id"),
    ("stg_apif__standings", "season", "base_apif__standings", "season"),
    ("stg_apif__coaches", "coach_id", "base_apif__coaches", "coach_api_id"),
    ("stg_apif__coach_career", "coach_id", "base_apif__coach_career", "coach_api_id"),
]

# staging models whose uniqueness test stays: (model, the model-level test name, or "fixture_id" for
# the column-level unique test of stg_apif__fixtures_next)
UNIQUE_STAYS = [
    ("stg_apif__fixtures_next", "fixture_id"),
    ("stg_apif__fixture_events", "stg_apif__fixture_events_order_keys_unique"),
    ("stg_apif__teams", "stg_apif__teams_order_keys_unique"),
    ("stg_apif__leagues", "stg_apif__leagues_order_keys_unique"),
    ("stg_apif__standings", "stg_apif__standings_order_keys_unique"),
]

# Reads of a moved staging model whose key filters sit between the ref and the end of its CTE or its
# union branch: (base file, staging model, filters). The i-th row of a file and model pins the i-th
# read of that model in that file.
BASE_READERS = [
    ("base_apif__fixtures_next.sql", "stg_apif__fixtures_next", ["fixture_id is not null"]),
    ("base_apif__fixture_events.sql", "stg_apif__fixture_events", ["fixture_id is not null"]),
    (
        "base_apif__fixture_statistics.sql",
        "stg_apif__fixture_statistics",
        ["fixture_id is not null", "team_id is not null"],
    ),
    ("base_apif__lineup_fetches.sql", "stg_apif__lineups", ["fixture_id is not null", "team_id is not null"]),
    ("base_apif__squads.sql", "stg_apif__squads", ["team_id is not null"]),
    ("base_apif__squads.sql", "stg_apif__squads", ["team_id is not null", "player_id is not null"]),
    ("base_apif__standings.sql", "stg_apif__standings", ["team_id is not null", "season is not null"]),
    ("base_apif__coaches.sql", "stg_apif__coaches", ["stg.coach_id is not null"]),
    ("base_apif__coach_career.sql", "stg_apif__coach_career", ["coach_id is not null", "team_id is not null"]),
    ("base_apif__player_profiles.sql", "stg_apif__player_profiles", ["player_id is not null"]),
    ("base_apif__teams.sql", "stg_apif__teams", ["team_id is not null"]),
    ("base_apif__teams.sql", "stg_apif__standings", ["team_id is not null", "season is not null"]),
    ("base_apif__teams.sql", "stg_apif__fixtures_next", ["fixture_id is not null"]),
    ("base_apif__teams.sql", "stg_apif__fixture_statistics", ["team_id is not null", "fixture_id is not null"]),
    ("base_apif__teams.sql", "stg_apif__fixture_events", ["team_id is not null", "fixture_id is not null"]),
    ("base_apif__players.sql", "stg_apif__players", ["player_id is not null"]),
]

# Reads whose filter sits outside the CTE that holds the staging ref: (base file, staging model, the
# normalised SQL that carries the filter)
FETCHES = "from fetches where fixture_id is not null group by fixture_id"
LISTING_CALL = (
    "{{ lines_without_key( ref('stg_apif__fixture_statistics'), ref('stg_apif__lineups'), "
    "ref('base_apif__lineup_sheets'), 'participants', 'overrides' ) }}"
)
FILE_PINS = [
    ("base_apif__fixture_fetches.sql", "stg_apif__lineups", FETCHES),
    ("base_apif__fixture_fetches.sql", "stg_apif__fixture_events", FETCHES),
    ("base_apif__fixture_fetches.sql", "stg_apif__fixture_statistics", FETCHES),
    (
        "base_apif__player_team_season.sql",
        "stg_apif__players",
        "from src where player_id is not null and team_id is not null and season_year is not null",
    ),
    (
        "base_apif__leagues.sql",
        "stg_apif__leagues",
        "where leagues.league_api_id is not null and leagues.season_api_year is not null )",
    ),
    ("base_apif__fixture_lines_without_key.sql", "stg_apif__fixture_statistics", LISTING_CALL),
    ("base_apif__fixture_lines_without_key.sql", "stg_apif__lineups", LISTING_CALL),
]

REF = re.compile(r"ref\(\s*['\"](stg_apif__\w+)['\"]\s*\)")
FORBIDDEN_IN_A_PROOF = {"where", "warn_if", "error_if", "limit", "store_failures", "enabled", "fail_calc"}


def _models(path):
    return {model["name"]: model for model in yaml.safe_load(path.read_text(encoding="utf-8"))["models"]}


def _sql(path):
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"\{#.*?#\}", " ", text, flags=re.DOTALL)
    text = re.sub(r"--[^\n]*", " ", text)
    return re.sub(r"\s+", " ", text)


def _tests(tests):
    found = []
    for test in tests or []:
        if isinstance(test, str):
            found.append((test, {}))
        else:
            (name, body), = test.items()
            found.append((name, body or {}))
    return found


def _column_tests(model, column):
    (found,) = [c for c in model["columns"] if c["name"] == column]
    return _tests(found.get("tests") or found.get("data_tests"))


def _model_tests(model):
    return _tests(model.get("tests") or model.get("data_tests"))


def _stays_at_error(body):
    config = body.get("config") or {}
    return (
        not (FORBIDDEN_IN_A_PROOF & set(body))
        and not (FORBIDDEN_IN_A_PROOF & set(config))
        and config.get("severity", "error") == "error"
        and body.get("severity", "error") == "error"
    )


@pytest.fixture(scope="module")
def staging():
    return _models(STAGING)


@pytest.fixture(scope="module")
def base():
    return _models(BASE)


@pytest.mark.parametrize("stg, column, base_model, base_column", NULL_KEYS)
def test_a_null_provider_key_is_proven_dropped_by_base_not_tested_in_staging(
    staging, base, stg, column, base_model, base_column
):
    assert "not_null" not in [name for name, _ in _column_tests(staging[stg], column)]
    proofs = [body for name, body in _column_tests(base[base_model], base_column) if name == "not_null"]
    assert len(proofs) == 1
    assert _stays_at_error(proofs[0]), (base_model, base_column, proofs[0])


@pytest.mark.parametrize("stg, test", UNIQUE_STAYS)
def test_the_uniqueness_test_of_staging_stays_at_error(staging, stg, test):
    model = staging[stg]
    if test == "fixture_id":
        kept = [body for name, body in _column_tests(model, "fixture_id") if name == "unique"]
    else:
        kept = [body for _, body in _model_tests(model) if body.get("name") == test]
    assert len(kept) == 1, (stg, test)
    assert _stays_at_error(kept[0]), (stg, test, kept[0])


def test_a_proof_that_is_filtered_or_lowered_is_not_a_proof():
    assert _stays_at_error({})
    assert not _stays_at_error({"config": {"severity": "warn"}})
    assert not _stays_at_error({"severity": "warn"})
    assert not _stays_at_error({"where": "x is not null"})
    assert not _stays_at_error({"config": {"where": "x is not null"}})
    assert not _stays_at_error({"warn_if": ">1"})
    assert not _stays_at_error({"config": {"enabled": False}})
    assert not _stays_at_error({"config": {"fail_calc": "0"}})


def test_no_reader_row_is_listed_twice():
    assert len(BASE_READERS) == len({(file, stg, tuple(filters)) for file, stg, filters in BASE_READERS})
    assert len(FILE_PINS) == len(set(FILE_PINS))


def _read_bodies(text, stg):
    bodies = []
    for match in re.finditer(r"ref\(\s*['\"]" + stg + r"['\"]\s*\)", text):
        after = text[match.end():]
        ends = [after.find(mark) for mark in ("union all", "), ", ") select")]
        bodies.append(after[: min(end for end in ends if end >= 0)])
    return bodies


@pytest.mark.parametrize("base_file, stg, filters", BASE_READERS)
def test_a_base_model_reading_staging_drops_the_null_key_rows(base_file, stg, filters):
    index = [row[:2] for row in BASE_READERS[: BASE_READERS.index((base_file, stg, filters))]].count(
        (base_file, stg)
    )
    bodies = _read_bodies(_sql(BASE_SQL / base_file), stg)
    assert index < len(bodies), (base_file, stg, index)
    for condition in filters:
        assert condition in bodies[index], (base_file, stg, condition)


@pytest.mark.parametrize("base_file, stg, snippet", FILE_PINS)
def test_a_base_read_filtered_outside_its_own_cte_drops_the_null_key_rows(base_file, stg, snippet):
    assert snippet in _sql(BASE_SQL / base_file), (base_file, stg)


def test_every_base_read_of_a_moved_staging_model_is_pinned():
    moved = {stg for stg, _, _, _ in NULL_KEYS}
    reads = {}
    for path in sorted(BASE_SQL.glob("*.sql")):
        for stg in REF.findall(_sql(path)):
            if stg in moved:
                reads[(path.name, stg)] = reads.get((path.name, stg), 0) + 1
    pinned = {}
    for base_file, stg, _ in BASE_READERS:
        pinned[(base_file, stg)] = pinned.get((base_file, stg), 0) + 1
    for base_file, stg, _ in FILE_PINS:
        pinned[(base_file, stg)] = pinned.get((base_file, stg), 0) + 1
    unpinned = {pair: count for pair, count in reads.items() if pinned.get(pair, 0) < count}
    assert not unpinned


# Singular tests that recompute a rule of base from a moved staging model carry the filter base
# applies: (test file, the normalised SQL that carries the filter)
TEST_PINS = [
    (
        "assert_team_id_aliases_merged.sql",
        "from {{ ref('stg_apif__fixtures_next') }} where fixture_id is not null and fixture_id not in",
    ),
    ("assert_team_id_aliases_merged.sql", "where fixtures.fixture_id is not null"),
    ("assert_team_id_aliases_merged.sql", "where standings.season is not null"),
    (
        "assert_league_name_overrides_are_corrections.sql",
        "from {{ ref('stg_apif__leagues') }} where league_api_id is not null and season_api_year is not null",
    ),
    ("assert_base_team_stats_cleaned.sql", "where s.fixture_id is not null and s.team_id is not null"),
    ("assert_coach_bio_from_every_fetch.sql", "from {{ ref('stg_apif__coaches') }} where coach_id is not null"),
    ("assert_coach_fetches_agree_on_bio.sql", "from {{ ref('stg_apif__coaches') }} where coach_id is not null"),
    ("assert_fixture_statistics_from_every_fetch.sql", "where fixture_id is not null and team_id is not null and"),
    ("assert_identity_fields_never_blanked.sql", "from {{ ref('stg_apif__players') }} where player_id is not null"),
    ("assert_identity_names_stable.sql", "from {{ ref('stg_apif__players') }} where player_id is not null"),
    (
        "assert_lineup_fetch_keeps_grid_only_for_same_eleven.sql",
        "from {{ ref('stg_apif__lineups') }} where fixture_id is not null and team_id is not null",
    ),
    (
        "assert_lineup_two_people_one_id_not_held.sql",
        "from {{ ref('stg_apif__lineups') }} where fixture_id is not null and team_id is not null",
    ),
]

# Singular tests that read a moved staging model and need no key filter, because a NULL-key row
# changes none of their results: they compare strings, count rows or join on the key.
TEST_EXEMPT = {
    "assert_country_name_overrides_still_needed.sql",
    "assert_fixture_events_only_from_latest_fetch.sql",
    "assert_goal_added_minute_from_newest_fetch.sql",
    "assert_sheet_and_stats_player_join_on_shirt.sql",
    "test_stg_fixture_statistics_non_empty.sql",
    "assert_null_key_lines_listed.sql",
    "assert_squads_read_per_team.sql",
}


# How many reads of a moved staging model each of those tests and each macro makes. A read added
# to a pinned file is a read no pin has seen.
READS = {
    "assert_base_team_stats_cleaned.sql": 1,
    "assert_coach_bio_from_every_fetch.sql": 1,
    "assert_coach_fetches_agree_on_bio.sql": 1,
    "assert_fixture_statistics_from_every_fetch.sql": 2,
    "assert_identity_fields_never_blanked.sql": 1,
    "assert_identity_names_stable.sql": 1,
    "assert_league_name_overrides_are_corrections.sql": 1,
    "assert_lineup_fetch_keeps_grid_only_for_same_eleven.sql": 1,
    "assert_lineup_two_people_one_id_not_held.sql": 1,
    "assert_team_id_aliases_merged.sql": 3,
    "assert_country_name_overrides_still_needed.sql": 4,
    "assert_fixture_events_only_from_latest_fetch.sql": 1,
    "assert_goal_added_minute_from_newest_fetch.sql": 1,
    "assert_sheet_and_stats_player_join_on_shirt.sql": 1,
    "test_stg_fixture_statistics_non_empty.sql": 1,
    "assert_null_key_lines_listed.sql": 5,
    "assert_squads_read_per_team.sql": 3,
    "players_with_conflicting_bio.sql": 1,
}

# Macros that read a moved staging model and carry its key filter: (macro file, normalised SQL)
MACRO_PINS = [
    (
        "players_with_conflicting_bio.sql",
        "from {{ ref('stg_apif__players') }} as season_row where season_row.player_id is not null",
    ),
]


def _moved_reads(path):
    moved = {stg for stg, _, _, _ in NULL_KEYS}
    return [stg for stg in REF.findall(_sql(path)) if stg in moved]


@pytest.mark.parametrize("test_file, snippet", TEST_PINS)
def test_a_singular_test_recomputing_base_drops_the_null_key_rows(test_file, snippet):
    assert snippet in _sql(DBT / "tests" / test_file), test_file


@pytest.mark.parametrize("macro_file, snippet", MACRO_PINS)
def test_a_macro_reading_a_moved_staging_model_drops_the_null_key_rows(macro_file, snippet):
    assert snippet in _sql(DBT / "macros" / macro_file), macro_file


def test_every_singular_test_reading_a_moved_staging_model_is_pinned_or_exempt():
    reading = {path.name for path in sorted((DBT / "tests").glob("*.sql")) if _moved_reads(path)}
    assert reading == {file for file, _ in TEST_PINS} | TEST_EXEMPT


def test_every_macro_reading_a_moved_staging_model_is_pinned():
    reading = {path.name for path in sorted((DBT / "macros").glob("*.sql")) if _moved_reads(path)}
    assert reading == {file for file, _ in MACRO_PINS}


def test_no_singular_test_or_macro_has_a_read_no_pin_has_seen():
    counts = {}
    for folder in ("tests", "macros"):
        for path in sorted((DBT / folder).glob("*.sql")):
            if _moved_reads(path):
                counts[path.name] = len(_moved_reads(path))
    assert counts == READS


def test_the_policy_is_stated_where_the_rule_lives_and_names_the_one_model_it_excepts(staging):
    standards = " ".join((DBT / "docs" / "engineering_standards.md").read_text(encoding="utf-8").split())
    layering = " ".join((DBT / "docs" / "layering.md").read_text(encoding="utf-8").split())
    header = " ".join(STAGING.read_text(encoding="utf-8").split())
    assert (
        "A provider key that base drops when NULL is the exception. Its `not_null` lives in base. "
        "`stg_apif__fixture_players` keeps its own."
    ) in standards
    assert (
        "except a provider key that base drops when NULL (its `not_null` is in base; "
        "`stg_apif__fixture_players` keeps its own)"
    ) in layering
    assert "except in # stg_apif__fixture_players, which keeps its own tests." in header
    kept = [name for name, _ in _column_tests(staging["stg_apif__fixture_players"], "fixture_id")]
    assert "not_null" in kept


def test_the_read_guard_sees_a_multi_line_and_a_double_quoted_read():
    assert REF.findall(_sql_of("from {{ ref(\n 'stg_apif__teams'\n) }}")) == ["stg_apif__teams"]
    assert REF.findall(_sql_of('from {{ ref("stg_apif__teams") }}')) == ["stg_apif__teams"]
    assert len(_read_bodies("ref('stg_apif__teams') where a ), x as (ref('stg_apif__teams') where b ), ", "stg_apif__teams")) == 2


def _sql_of(text):
    return re.sub(r"\s+", " ", text)
