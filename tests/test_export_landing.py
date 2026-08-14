"""Unit tests for the landing-page export helpers (#367).

No BigQuery — fabricated rows only, so python-ci validates the logic offline.

The load-bearing test here is `test_shape_landing_payload_carries_only_the_built_modules`. Two
blocks were cut from this page on 2026-08-08 — the stats teasers and trending — and BOTH had put
business logic in the export: eligibility judgement and competition ranking in the first case,
storyline ranking in the second (which is why `mart_landing_trending` was written at all). The
payload key set is the cheapest place to catch either coming back, so it is asserted exactly.
"""

from scripts.export_site_data import (
    group_upcoming_fixtures,
    shape_landing_payload,
)

_META = {
    "BSA": {"name": "Brasileirão Série A", "slug": "brasileirao-serie-a", "sort_order": 30},
    "MLS": {"name": "Major League Soccer", "slug": "mls", "sort_order": 20},
    "BL1": {"name": "Bundesliga", "slug": "bundesliga", "sort_order": 10},
}

_TEAMS = {
    1: {"team_sk": 1, "team_name": "Palmeiras", "team_slug": "palmeiras",
        "team_logo_url": "https://x/1.png"},
    2: {"team_sk": 2, "team_name": "Flamengo", "team_slug": "flamengo",
        "team_logo_url": None},
    3: {"team_sk": 3, "team_name": "Inter Miami", "team_slug": "inter-miami",
        "team_logo_url": "https://x/3.png"},
}


def _fixture(sk, league_code, kickoff, home=1, away=2, season=2026, rnd="Regular Season - 20"):
    return {
        "fixture_sk": sk, "league_code": league_code, "season_api_year": season,
        "kickoff_datetime": kickoff, "round_name": rnd,
        "home_team_sk": home, "away_team_sk": away,
    }


# --------------------------------------------------------------------------- #
# Fixtures hero
# --------------------------------------------------------------------------- #
def test_group_upcoming_fixtures_groups_by_competition_in_kickoff_order():
    fixtures = [
        _fixture(10, "MLS", "2026-08-04T01:00:00Z", home=3, away=1),
        _fixture(11, "BSA", "2026-08-04T23:00:00Z"),
        _fixture(12, "MLS", "2026-08-05T01:00:00Z", home=1, away=3),
    ]
    groups = group_upcoming_fixtures(fixtures, _TEAMS, _META)

    # group order follows the EARLIEST kickoff, which is first-appearance order
    assert [g["league_code"] for g in groups] == ["MLS", "BSA"]
    assert [f["fixture_id"] for f in groups[0]["fixtures"]] == [10, 12]
    assert groups[0]["league_name"] == "Major League Soccer"
    assert groups[0]["competition_slug"] == "mls"


def test_group_upcoming_fixtures_caps_at_the_display_limit():
    fixtures = [_fixture(i, "BSA", f"2026-08-0{i}T20:00:00Z") for i in range(1, 6)]
    groups = group_upcoming_fixtures(fixtures, _TEAMS, _META, limit=3)
    assert sum(len(g["fixtures"]) for g in groups) == 3


def test_group_upcoming_fixtures_builds_the_fixture_slug_from_names():
    groups = group_upcoming_fixtures(
        [_fixture(10, "BSA", "2026-08-04T23:00:00Z")], _TEAMS, _META
    )
    assert groups[0]["fixtures"][0]["slug"] == "2026-08-04-palmeiras-vs-flamengo"


def test_group_upcoming_fixtures_keeps_a_null_crest_null():
    """A missing crest is a real absence the page renders as a monogram, never a fake URL."""
    groups = group_upcoming_fixtures(
        [_fixture(10, "BSA", "2026-08-04T23:00:00Z")], _TEAMS, _META
    )
    assert groups[0]["fixtures"][0]["away"]["crest"] is None


def test_group_upcoming_fixtures_omits_a_competition_with_no_fixture_in_the_window():
    """Acceptance criterion 1: a competition with nothing coming up does not appear at all."""
    fixtures = [
        _fixture(10, "MLS", "2026-08-04T01:00:00Z"),
        _fixture(11, "BSA", "2026-08-09T23:00:00Z"),
    ]
    groups = group_upcoming_fixtures(fixtures, _TEAMS, _META, limit=1)
    assert [g["league_code"] for g in groups] == ["MLS"]
    assert all(g["fixtures"] for g in groups)


def test_group_upcoming_fixtures_handles_an_empty_calendar():
    assert group_upcoming_fixtures([], _TEAMS, _META) == []


# --------------------------------------------------------------------------- #
# Payload assembly
#
# Two blocks' worth of tests stood here and went with their blocks on 2026-08-08.
#
# The stats teasers took ten with them — six on `eligible_stats_competitions`,
# four on `pick_stats_competition`. Trending took seven, led by one that asserted
# the export followed the mart's `trending_rank` instead of re-sorting by run
# length. All seventeen were good tests of code that should never have been in the
# export: they pinned eligibility judgement and business ranking, which
# `layering.md` puts in dbt.
#
# They are deleted rather than migrated because neither block survives. The stats
# teasers were ruled useless (CPO 2026-08-08) and are replaced by the mart-backed
# Top players / Top teams; trending is not in the composition the CPO set that day
# (next matches -> Top players -> Top teams -> browse), and the built version was
# stale against the 2026-08-04 ruling anyway.
#
# What those tests knew is not lost. The three defects the stats tests pinned (a
# season that has not kicked off, a group competition's within-group ranks, a
# competition with no player stats) are recorded in `docs/wireframes/10_home.md`
# §0 so the replacement marts inherit them instead of rediscovering them.
# --------------------------------------------------------------------------- #
def test_shape_landing_payload_carries_only_the_built_modules():
    """TWO modules today, of the four in the composition. The key set is asserted EXACTLY, so a
    re-added block fails here whether it arrives populated or as an empty shell.

    Top players and Top teams will each add a key when they are built; that is a deliberate edit of
    this line, not a silent widening.
    """
    payload = shape_landing_payload(
        upcoming=[{"league_code": "BSA"}],
        browse={"groups": [], "countries": []},
    )
    assert payload["type"] == "landing"
    assert set(payload) == {"type", "upcoming", "browse"}


def test_shape_landing_payload_carries_neither_removed_block():
    """Named individually as well as by the key-set assertion above, so a failure says WHICH block
    came back rather than only that the shape moved."""
    payload = shape_landing_payload([], {"groups": [], "countries": []})
    assert "stats" not in payload
    assert "trending" not in payload
