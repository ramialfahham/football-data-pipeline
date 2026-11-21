"""The venue's clock: the seeds name only zones that exist, every country has a row, and the export
carries the two served columns on every match row it shapes."""
import csv
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import export_site_data as export  # noqa: E402

SEEDS = ROOT / "dbt_project" / "seeds"


def _rows(name: str) -> list[dict]:
    with open(SEEDS / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_every_zone_a_seed_names_is_in_time_zones():
    known = {r["time_zone"] for r in _rows("time_zones.csv")}
    named = {r["time_zone"] for r in _rows("country_time_zones.csv") if r["time_zone"]}
    named |= {r["time_zone"] for r in _rows("venue_time_zones.csv")}
    assert named - known == set()


def test_every_zone_in_time_zones_is_an_iana_zone():
    zoneinfo = pytest.importorskip("zoneinfo")
    try:
        zoneinfo.ZoneInfo("Europe/Berlin")
    except zoneinfo.ZoneInfoNotFoundError:
        pytest.skip("no tz database on this machine")
    bad = []
    for r in _rows("time_zones.csv"):
        try:
            zoneinfo.ZoneInfo(r["time_zone"])
        except zoneinfo.ZoneInfoNotFoundError:
            bad.append(r["time_zone"])
    assert bad == []


def test_every_country_has_a_row_in_country_time_zones():
    countries = {r["country_key"] for r in _rows("countries.csv")}
    zoned = [r["country_key"] for r in _rows("country_time_zones.csv")]
    assert len(zoned) == len(set(zoned))
    assert countries == set(zoned)


def test_a_country_without_a_default_zone_is_one_that_spans_zones():
    without = {r["country_key"] for r in _rows("country_time_zones.csv") if not r["time_zone"]}
    assert without == {
        "australia", "brazil", "canada", "indonesia", "mexico", "russia", "united-states-of-america",
    }


def test_a_venue_has_one_row_in_venue_time_zones():
    ids = [r["venue_api_id"] for r in _rows("venue_time_zones.csv")]
    assert len(ids) == len(set(ids))


def test_a_zone_that_has_a_daylight_label_has_a_standard_label():
    bad = [r["time_zone"] for r in _rows("time_zones.csv") if r["label_daylight"] and not r["label_standard"]]
    assert bad == []


def test_the_competition_fixture_columns_carry_the_clock():
    columns = {c.strip() for c in export._COMPETITION_FIXTURE_COLUMNS.split(",")}
    assert {"kickoff_local", "kickoff_zone_label"} <= columns


def _mart_row(**extra) -> dict:
    return {
        "fixture_sk": 7, "fixture_slug": "a-b", "kickoff_datetime": "2026-11-21 19:30:00+00:00",
        "kickoff_local": "2026-11-21 20:30:00", "kickoff_zone_label": "CET", "round_name": "R",
        "fixture_order": 1, "status_short": "NS", "is_played": False, "home_team_sk": 1,
        "away_team_sk": 2, **extra,
    }


def test_a_match_row_carries_the_served_local_kickoff_and_label_unchanged():
    row = export._competition_fixture(_mart_row())
    assert row["kickoff"] == "2026-11-21 19:30:00+00:00"
    assert row["kickoff_local"] == "2026-11-21 20:30:00"
    assert row["kickoff_zone_label"] == "CET"


def test_a_next_match_and_a_landing_group_carry_the_clock():
    nxt = export.shape_next_match({**_mart_row(), "league_code": "BL1"}, fixture_id=99)
    assert (nxt["kickoff_local"], nxt["kickoff_zone_label"]) == ("2026-11-21 20:30:00", "CET")
    groups = export.group_upcoming_fixtures([{**_mart_row(), "league_code": "BL1"}], {"BL1": {"name": "Bundesliga"}})
    fixture = groups[0]["fixtures"][0]
    assert (fixture["kickoff_local"], fixture["kickoff_zone_label"]) == ("2026-11-21 20:30:00", "CET")


def test_a_team_schedule_row_carries_the_clock():
    shaped = export._shape_team_fixture({
        "kickoff_datetime": "2026-11-21 19:30:00+00:00", "kickoff_local": "2026-11-21 20:30:00",
        "kickoff_zone_label": "CET",
    })
    assert (shaped["kickoff_local"], shaped["kickoff_zone_label"]) == ("2026-11-21 20:30:00", "CET")
