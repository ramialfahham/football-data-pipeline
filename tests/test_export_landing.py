"""Unit tests for the landing-page export helpers (#367).

No BigQuery — fabricated rows only, so python-ci validates the logic offline.

The load-bearing test here is `test_shape_landing_payload_carries_only_the_built_modules`. Two
blocks were cut from this page — the stats teasers and trending — and BOTH had put business
logic in the export: eligibility judgement and competition ranking in the first case, storyline
ranking in the second (which is why `mart_landing_trending` was written at all). A third, browse,
was dropped ("drop the browse section") — registry-driven, not a layering violation, but removed
for the same reason the key set is asserted exactly: the payload shape is the cheapest place to
catch any of the three coming back.
"""

import csv

from scripts import export_site_data
from scripts.export_site_data import (
    _HOME_TEAM_BOARDS,
    CATALOGUE_SEED_PATH,
    _board_catalogue,
    _competitions_index,
    _warehouse_competition_meta,
    group_upcoming_fixtures,
    shape_home_top_players,
    shape_home_top_teams,
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


def test_group_upcoming_fixtures_caps_nothing():
    """⚠ INVERTED. This test asserted the opposite — that the helper capped at a `limit` —
    and that cap is retired ("we will show what we have, more matches will come, because we
    ingest more competitions"). The `limit` parameter is gone, so the old assertion
    could not merely be relaxed; keeping the case and flipping its expectation is what pins the
    new behaviour at the same spot the old one guarded.

    WHICH day is shown is no longer decided here either — it is a WHERE clause in
    `fetch_landing_payload`'s query (GAP-32 records the layer dispute about that placement).
    """
    fixtures = [_fixture(i, "BSA", f"2026-08-0{i}T20:00:00Z") for i in range(1, 6)]
    groups = group_upcoming_fixtures(fixtures, _TEAMS, _META)
    assert sum(len(g["fixtures"]) for g in groups) == 5, "every fixture handed in is grouped"


def test_group_upcoming_fixtures_carries_the_served_fixture_slug():
    """The slug is mart_competition_fixtures' column, joined into the read; nothing here spells
    a URL from names, so a row without a served slug links nowhere rather than somewhere wrong."""
    row = _fixture(10, "BSA", "2026-08-04T23:00:00Z")
    row["fixture_slug"] = "2026-08-04-palmeiras-vs-flamengo"
    groups = group_upcoming_fixtures([row], _TEAMS, _META)
    assert groups[0]["fixtures"][0]["slug"] == "2026-08-04-palmeiras-vs-flamengo"
    bare = group_upcoming_fixtures([_fixture(11, "BSA", "2026-08-04T23:00:00Z")], _TEAMS, _META)
    assert bare[0]["fixtures"][0]["slug"] is None


def test_group_upcoming_fixtures_keeps_a_null_crest_null():
    """A missing crest is a real absence the page renders as a monogram, never a fake URL."""
    groups = group_upcoming_fixtures(
        [_fixture(10, "BSA", "2026-08-04T23:00:00Z")], _TEAMS, _META
    )
    assert groups[0]["fixtures"][0]["away"]["crest"] is None


def test_group_upcoming_fixtures_omits_a_competition_with_no_fixture_in_the_window():
    """Acceptance criterion 1: a competition with nothing coming up does not appear at all.

    ⚠ REWORKED. This used `limit=1` to manufacture the "outside the window" case, and
    that parameter is gone with the retired cap. The property under test is unchanged and still
    worth pinning — a competition contributing NO fixture must not produce an empty group — so the
    window is now expressed by simply not handing the helper any BSA fixture, which is what the
    query's matchday WHERE clause does upstream.
    """
    fixtures = [_fixture(10, "MLS", "2026-08-04T01:00:00Z")]
    groups = group_upcoming_fixtures(fixtures, _TEAMS, _META)
    assert [g["league_code"] for g in groups] == ["MLS"], "BSA is in _META but has no fixture"
    assert all(g["fixtures"] for g in groups), "no group may be emitted empty"


def test_group_upcoming_fixtures_handles_an_empty_calendar():
    assert group_upcoming_fixtures([], _TEAMS, _META) == []


def test_the_hero_reads_the_next_matchday_mart_whole(monkeypatch):
    """The window is EACH COMPETITION'S NEXT MATCHDAY, and the WAREHOUSE decides it:
    mart_next_matchday holds every upcoming fixture of each competition's next round, and the
    export reads that table whole - no WHERE, no window, no ranking, no second pass in Python.

    Offline, so the SQL text is what can be pinned: the read is FROM the mart, and none of the
    selection vocabulary that used to live here (min(fixture_date), row_number, qualify,
    current_date, a where) is in it. The rows the fake returns are then carried through
    unfiltered and grouped by competition.
    """
    captured: list[str] = []

    def fake_query(client, sql):
        captured.append(sql)
        if "mart_next_matchday" in sql:
            return [
                _fixture(11, "BL1", "2026-09-18T18:30:00Z", rnd="Regular Season - 4"),
                _fixture(12, "BL1", "2026-09-20T15:30:00Z", rnd="Regular Season - 4"),
                _fixture(13, "MLS", "2026-09-19T23:00:00Z", home=3, away=1,
                         rnd="Regular Season - 26"),
            ]
        if "core.dim_team" in sql:
            return list(_TEAMS.values())
        return []

    monkeypatch.setattr(export_site_data, "_query", fake_query)
    monkeypatch.setattr(export_site_data, "_warehouse_competition_meta", lambda client: {})

    payload = export_site_data.fetch_landing_payload(object())

    hero_sql = next(s for s in captured if "mart_next_matchday" in s)
    assert "core.fct_fixture" not in hero_sql, "the hero reads the mart, not the fact"
    lowered = " ".join(hero_sql.lower().split())
    for token in ("where", "min(fixture_date)", "row_number", "qualify", "current_date"):
        assert token not in lowered, f"selection vocabulary in the export: {token!r}"

    groups = {g["league_code"]: g for g in payload["upcoming"]}
    assert [f["fixture_id"] for f in groups["BL1"]["fixtures"]] == [11, 12], (
        "every served fixture of the round is carried; the page folds, the export does not cut"
    )
    assert {f["round"] for f in groups["BL1"]["fixtures"]} == {"Regular Season - 4"}
    assert [f["fixture_id"] for f in groups["MLS"]["fixtures"]] == [13]


# --------------------------------------------------------------------------- #
# Payload assembly
#
# Three blocks' worth of tests stood here and went with their blocks.
#
# The stats teasers took ten with them — six on `eligible_stats_competitions`,
# four on `pick_stats_competition`. Trending took seven, led by one that asserted
# the export followed the mart's `trending_rank` instead of re-sorting by run
# length. Browse's own tests were never written in the export (it called
# `build_nav`, tested elsewhere) — only its key in the payload-shape assertions
# below, updated in place. All seventeen removed were good tests of code that
# should never have been in the export: they pinned eligibility judgement and
# business ranking, which `layering.md` puts in dbt.
#
# They are deleted rather than migrated because none of the three blocks
# survives. The stats teasers were ruled useless and are replaced by the
# mart-backed Top players / Top teams; trending was cut alongside and was stale
# against the last streak ruling anyway; browse was DROPPED ("drop the browse
# section") once its only remaining justification — reachability into the
# long-tail team/player pages — turned out to apply to exactly the two entity
# types already blocked on data-quality work.
#
# What those tests knew is not lost. The three defects the stats tests pinned (a
# season that has not kicked off, a group competition's within-group ranks, a
# competition with no player stats) are recorded in `docs/wireframes/10_home.md`
# §0 so the replacement marts inherit them instead of rediscovering them.
# --------------------------------------------------------------------------- #
def test_shape_landing_payload_carries_only_the_built_modules():
    """TWO modules now, of the three in the composition: next matches and Top players. The key set
    is asserted EXACTLY, so a re-added block fails here whether it arrives populated or as an empty
    shell.

    ⚠ THE KEY SET IS NOW COMPLETE. All three modules of the composition are built, so a new key
    appearing here is a re-added block, not a pending one. That is a deliberate edit of this line
    rather than a silent widening.
    """
    payload = shape_landing_payload(
        upcoming=[{"league_code": "BSA"}],
        top_players=[{"metric_key": "goals_player", "rows": [{"name": "X"}]}],
        top_teams=[{"metric_key": "goals_per_match", "rows": [{"name": "Y"}]}],
    )
    assert payload["type"] == "landing"
    assert set(payload) == {"type", "upcoming", "top_players", "top_teams"}


def test_shape_landing_payload_omits_top_players_when_no_board_survived():
    """#40: a board with no data is not rendered, and if NO board has data the block itself does
    not render. So an empty result must be ABSENT, not an empty list — otherwise the page has to
    guard against a key that means "nothing", which is the empty-state that is ruled out.
    """
    for empty in ([], None):
        payload = shape_landing_payload(
            upcoming=[{"league_code": "BSA"}], top_players=empty, top_teams=empty,
        )
        assert "top_players" not in payload, f"empty {empty!r} must not reach the payload"
        assert "top_teams" not in payload, f"empty {empty!r} must not reach the payload"
        assert set(payload) == {"type", "upcoming"}


def test_shape_landing_payload_carries_none_of_the_removed_blocks():
    """Named individually as well as by the key-set assertion above, so a failure says WHICH block
    came back rather than only that the shape moved."""
    payload = shape_landing_payload([])
    assert "stats" not in payload
    assert "trending" not in payload
    assert "browse" not in payload


# --------------------------------------------------------------------------- #
# Top players (#40)
#
# The mart already ranks within (league_code, season_api_year), so the shaper only ever filters and
# orders. These fabricate mart rows directly — no BigQuery — and the WHERE that picks elite /
# current-season / rank-1 lives in the query, not here, so the rows below are what that query
# would have returned.
# --------------------------------------------------------------------------- #
_LEAGUE_META = {
    "PL": {"name": "Premier League"},
    "PD": {"name": "La Liga"},
    "BL1": {"name": "Bundesliga"},
}

# Read from the real catalogue seed, not fabricated: a board's NAME is a governed value, and a
# fabricated key here would let the label mechanism drift from the catalogue unnoticed.
_LABEL_KEYS = _board_catalogue()
_TEAM_CATALOGUE = _board_catalogue(_HOME_TEAM_BOARDS, "team")


def _tlb(metric_key, league_code, name, value, team_sk=1):
    """One mart_team_leaderboards row, as the export's query returns it."""
    return {
        "metric_key": metric_key, "league_code": league_code, "sort_value": value,
        "team_sk": team_sk, "team_name": name, "team_logo_url": "https://x/1.png",
        "team_slug": f"{name.lower().replace(' ', '-')}-fc",
    }


def _lb(metric_key, league_code, name, value, player_sk=1):
    """One mart_leaderboards row, as the export's query returns it."""
    return {
        "metric_key": metric_key, "league_code": league_code, "sort_value": value,
        "player_sk": player_sk, "player_name": name,
        "team_name": f"{name} FC", "team_slug": "club", "team_logo_url": "https://x/1.png",
    }


def test_top_players_renders_the_order_the_warehouse_served():
    """The shaper does NOT sort. It groups the rows into boards, keeps their order and cuts at 7.

    ⚠ THIS TEST ASSERTED THE OPPOSITE AND THE OPPOSITE WAS WRONG. It used to hand the shaper
    unordered rows and require it to sort them by value, which is ranking in the consumption layer;
    the ruling is "all ranking and ordering lives in the warehouse. The page renders the order it
    is served."
    So the rows below arrive in the order the query's ORDER BY produced, and the assertion is that
    the shaper left them alone. Flipping the expectation in the same test, rather than deleting it,
    is what pins the new behaviour where the old one was guarded.
    """
    boards = shape_home_top_players([
        _lb("goals_player", "PL", "Haaland", 25.0, 12),
        _lb("goals_player", "PD", "Mbappe", 21.0, 10),
        _lb("goals_player", "BL1", "Kane", 20.0, 11),
    ], _LEAGUE_META, _LABEL_KEYS)
    assert len(boards) == 1
    assert boards[0]["metric_key"] == "goals_player"
    assert [r["name"] for r in boards[0]["rows"]] == ["Haaland", "Mbappe", "Kane"]
    assert [r["league_name"] for r in boards[0]["rows"]] == ["Premier League", "La Liga", "Bundesliga"]
    # Every row carries its club as well as its player (#40) and a slug to link to.
    assert boards[0]["rows"][0]["club"] == "Haaland FC"
    assert boards[0]["rows"][0]["slug"] == "haaland-12"


def test_top_players_does_not_reorder_what_it_is_given():
    """The sharper form of the test above, and the one that would catch a sort creeping back in:
    rows handed over in an order NO sort would produce must come out exactly as they went in.

    A shaper that re-sorted by value would reorder these; one that preserves order cannot.
    """
    rows = [
        _lb("goals_player", "BL1", "Lowest", 2.0, 11),
        _lb("goals_player", "PL", "Highest", 30.0, 12),
        _lb("goals_player", "PD", "Middle", 9.0, 13),
    ]
    boards = shape_home_top_players(rows, _LEAGUE_META, _LABEL_KEYS)
    assert [r["name"] for r in boards[0]["rows"]] == ["Lowest", "Highest", "Middle"]


def test_top_players_keeps_board_order_and_caps_each_at_seven():
    """The four boards render in a FIXED order — Goals, Assists, Passes, Key passes — regardless of
    the order the mart returned them, and each is cut at 7 (raised from 5).

    NINE DISTINCT LEAGUES, and that stays deliberate even though the shaper no longer dedupes. The
    query now returns one row per league (`league_leader_order = 1`), so nine rows means nine
    leagues in the data this function is ever handed. Feeding nine rows from ONE league would test
    the cap against input the export cannot produce.
    """
    nine = ("PL", "PD", "BL1", "ED", "L1", "LP", "SA", "PPL", "TSL")
    rows = []
    for key in ("passes_key_player", "goals_player", "passes_player", "assists_player"):
        for i, league in enumerate(nine):
            rows.append(_lb(key, league, f"{key}-{i}", 100 - i, player_sk=i))
    boards = shape_home_top_players(rows, _LEAGUE_META, _LABEL_KEYS)
    assert [b["metric_key"] for b in boards] == [
        "goals_player", "assists_player", "passes_player", "passes_key_player",
    ]
    assert all(len(b["rows"]) == 7 for b in boards)


# --------------------------------------------------------------------------- #
# TWO TESTS STOOD HERE AND WENT TO THE WAREHOUSE WITH THE BEHAVIOUR THEY GUARDED.
# They are deleted rather than relaxed, and this note exists so the next reader does not think the
# invariants were dropped — only that they are no longer THIS file's to assert.
#
#   · `test_top_players_shows_one_row_per_league_when_the_leaders_are_tied` pinned a Python dedupe
#     that picked between joint rank-1 players. That pick is now `league_leader_order` in
#     `mart_leaderboards`, and it is asserted by
#     `dbt_project/tests/assert_mart_leaderboards_one_leader_per_league.sql`, which checks BOTH that
#     exactly one row per league-board carries 1 AND that it is the row the rule picks. That test is
#     mutation-proven: with the ruled order it returns 0 rows, with the `minutes` leg dropped it
#     returns 443 over the whole mart.
#   · `test_top_players_is_deterministic_when_values_tie` pinned a total order in a Python sort.
#     The sort is gone; the order is the query's ORDER BY over served columns, and determinism is a
#     property of the warehouse column plus that clause.
#
# Keeping either as a unit test would mean re-implementing the rule in the test to check it, which
# is a tautology. What replaces them at THIS level is
# `test_top_players_does_not_reorder_what_it_is_given` above: the shaper's own contract is now
# "group, preserve, cap", and that is what a unit test can honestly hold it to.
# --------------------------------------------------------------------------- #


def test_top_players_omits_an_empty_board_and_survivors_keep_their_order():
    """#40: a board with no data is NOT rendered — no placeholder, no empty state — and the
    surviving boards keep their order and do not reflow to fill the gap."""
    boards = shape_home_top_players([
        _lb("goals_player", "PL", "A", 5.0),
        _lb("passes_key_player", "PL", "B", 3.0),
    ], _LEAGUE_META, _LABEL_KEYS)
    # assists and passes had no rows at all: they are absent, not empty.
    assert [b["metric_key"] for b in boards] == ["goals_player", "passes_key_player"]


def test_top_players_carries_the_catalogue_label_key_not_a_hand_written_name():
    """The board's NAME comes from the metric catalogue (#327: the seed is the single source of
    metric definitions), so the payload ships the label KEY and the frontend resolves it per
    locale. Nothing hand-types a board name in the export or the component.

    Asserted against the seed rather than a literal, so renaming a key in the catalogue fails here
    instead of silently shipping a board with the old name.
    """
    boards = shape_home_top_players(
        [_lb("goals_player", "PL", "A", 5.0)], _LEAGUE_META, _LABEL_KEYS
    )
    assert boards[0]["label_i18n_key"] == _LABEL_KEYS["goals_player"]["label_i18n_key"]
    assert boards[0]["label_i18n_key"], "a board must never ship without a label key"


def test_board_label_keys_are_the_player_rows_not_the_team_ones():
    """The board label must come from the catalogue's PLAYER row for the id.

    ⚠ THE ORIGINAL CLAIM HERE WAS FALSE AND IS REPLACED, NOT SOFTENED. It said "two of the four ids
    also carry a TEAM row". Measured against the seed, two-sided: **0 of 86** metric_ids are defined
    for more than one entity, and none of these four carries anything but a player row — so the
    collision it described does not exist today and this test was passing for a reason that was not
    true.

    What it does pin is still worth pinning, and the entity filter in `_board_label_keys` is still
    right. `assert_metric_catalogue_unique_by_entity` enforces uniqueness per (metric_id, entity),
    NOT globally, so a team row sharing one of these ids is permitted by the catalogue's own guards
    and would make an unfiltered lookup take whichever row `csv.DictReader` reached first — the bug
    export_metric_definitions_json.py once had. This keeps that door shut and pins the key to
    the seed rather than to a literal, so renaming it in the catalogue fails here instead of
    silently shipping a board with the old name.
    """
    import csv

    with open("dbt_project/seeds/metric_catalogue.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for metric_id, entry in _LABEL_KEYS.items():
        player = [r for r in rows if r["metric_id"] == metric_id and r["entity"] == "player"]
        assert player, f"{metric_id} has no player row"
        assert entry["label_i18n_key"] == player[0]["label_i18n_key"]

    # The same for the TEAM boards, and this is where the entity filter stops being theoretical:
    # the two board sets use different metric_ids, so a lookup that ignored entity would still have
    # to pick a row, and the seed is the only thing that says which.
    for metric_id, entry in _TEAM_CATALOGUE.items():
        team = [r for r in rows if r["metric_id"] == metric_id and r["entity"] == "team"]
        assert team, f"{metric_id} has no team row"
        assert entry["label_i18n_key"] == team[0]["label_i18n_key"]
        assert entry["format"] == team[0]["format"]


def test_top_teams_renders_the_order_the_warehouse_served():
    """The team shaper does not sort either. Same contract as the player one: group, preserve, cap.

    The rows below arrive in the order the query's `order by board_leader_order` produced, and the
    assertion is that the shaper left them alone.
    """
    boards = shape_home_top_teams([
        _tlb("goals_per_match", "PL", "Alpha", 2.4, 10),
        _tlb("goals_per_match", "PD", "Beta", 2.1, 11),
        _tlb("goals_per_match", "BL1", "Gamma", 1.9, 12),
    ], _LEAGUE_META, _TEAM_CATALOGUE)
    assert len(boards) == 1
    assert boards[0]["metric_key"] == "goals_per_match"
    assert [r["name"] for r in boards[0]["rows"]] == ["Alpha", "Beta", "Gamma"]
    assert [r["league_name"] for r in boards[0]["rows"]] == [
        "Premier League", "La Liga", "Bundesliga",
    ]


def test_top_teams_does_not_reorder_what_it_is_given():
    """The sharper form, and the one that catches a sort creeping back in: rows handed over in an
    order NO sort would produce must come out exactly as they went in."""
    rows = [
        _tlb("goals_per_match", "BL1", "Lowest", 0.9, 11),
        _tlb("goals_per_match", "PL", "Highest", 3.3, 12),
        _tlb("goals_per_match", "PD", "Middle", 2.0, 13),
    ]
    boards = shape_home_top_teams(rows, _LEAGUE_META, _TEAM_CATALOGUE)
    assert [r["name"] for r in boards[0]["rows"]] == ["Lowest", "Highest", "Middle"]


def test_top_teams_carries_the_catalogue_format_per_board():
    """⛔ THE ONE THING THAT DIFFERS FROM THE PLAYER BLOCK. Its four boards are all integers; these
    four are NOT one format — goals and shots on goal are `decimal_1`, passes and duels are
    `decimal_0`. A component that picked a formatter would render one pair wrong, so the format
    travels per board from the catalogue and this pins that it is the catalogue's, not a literal.
    """
    rows = [_tlb(key, "PL", f"T-{key}", 1.5) for key in _HOME_TEAM_BOARDS]
    boards = shape_home_top_teams(rows, _LEAGUE_META, _TEAM_CATALOGUE)
    by_key = {b["metric_key"]: b["format"] for b in boards}
    assert by_key["goals_per_match"] == "decimal_1"
    assert by_key["shots_on_goal_per_match"] == "decimal_1"
    assert by_key["passes_per_match"] == "decimal_0"
    assert by_key["duels_per_match"] == "decimal_0"
    assert len(set(by_key.values())) == 2, "the boards must not collapse to one shared format"


def test_top_teams_rows_carry_the_served_slug():
    """⚠ INVERTED. This asserted rows carry NO slug, because an earlier version shipped them
    unlinked to dodge the committed-team-sample problem. #41 says the opposite outright — "Every row
    links out. That is why the block exists" — so the fix was to commit the payloads the rows link
    to, not to drop the link. Keeping the case and flipping its expectation pins the new behaviour
    where the old one was guarded.

    The slug is `dim_team.team_slug`, SERVED (#852). This file generates no identity.
    """
    boards = shape_home_top_teams(
        [_tlb("goals_per_match", "PL", "Alpha", 2.4)], _LEAGUE_META, _TEAM_CATALOGUE,
    )
    row = boards[0]["rows"][0]
    assert row["slug"] == "alpha-fc"
    assert set(row) == {"team_id", "slug", "name", "crest", "league_code", "league_name", "value"}


def test_top_teams_keeps_board_order_and_caps_each_at_seven():
    """The four boards render in their fixed order regardless of what the mart returned, and
    each is cut at 7. Nine DISTINCT leagues, because the query returns one team per league."""
    nine = ("PL", "PD", "BL1", "ED", "L1", "LP", "SA", "PPL", "TSL")
    rows = []
    for key in ("duels_per_match", "goals_per_match", "passes_per_match", "shots_on_goal_per_match"):
        for i, league in enumerate(nine):
            rows.append(_tlb(key, league, f"{key}-{i}", 9.0 - i, team_sk=i))
    boards = shape_home_top_teams(rows, _LEAGUE_META, _TEAM_CATALOGUE)
    assert [b["metric_key"] for b in boards] == list(_HOME_TEAM_BOARDS)
    assert all(len(b["rows"]) == 7 for b in boards)


def test_top_teams_omits_an_empty_board_and_returns_nothing_when_all_are_empty():
    """Same rule as the player block: a board with no data is absent rather than empty, and if none
    survives the shaper returns an empty list, which shape_landing_payload then omits."""
    boards = shape_home_top_teams([
        _tlb("goals_per_match", "PL", "Alpha", 2.4),
        _tlb("duels_per_match", "PL", "Beta", 48.0),
    ], _LEAGUE_META, _TEAM_CATALOGUE)
    assert [b["metric_key"] for b in boards] == ["goals_per_match", "duels_per_match"]
    assert shape_home_top_teams([], _LEAGUE_META, _TEAM_CATALOGUE) == []


def test_top_players_returns_nothing_when_no_board_has_data():
    """If no board has data the block does not render at all — the shaper says so by returning an
    empty list, which shape_landing_payload then omits entirely."""
    assert shape_home_top_players([], _LEAGUE_META, _LABEL_KEYS) == []
    # A metric the home block does not show must not create a board either.
    assert shape_home_top_players([_lb("cards_player", "PL", "A", 9.0)], _LEAGUE_META, _LABEL_KEYS) == []


def test_the_team_board_set_is_all_per_match_rates():
    """⛔ THIS IS THE PREMISE THE BOARD HEADING RESTS ON, AND IT USED TO BE INFERRED FROM A NAME.

    `boardTitle()` turns the served label `Ø Goals` into the heading `Goals per match` (#41). An
    earlier version guarded that by reading `metric_id.endsWith("_per_match")` in TypeScript, and
    that was wrong: classifying a metric is a taxonomy judgement, which
    `layering.md` §Consumption layer keeps out of the frontend. It was also simply UNSAFE — an id's
    spelling is not a fact about the metric, and this catalogue proves it, since
    `shots_on_goal_per_match` carries the label key `metrics.shots_on_target_per_match.label`
    (`metrics_display.md` records that mismatch causing a defect in #370).

    The catalogue states the distinction in DATA: a per-match rate divides by `count(*)`, a per-90
    divides by `sum(minutes_played)`. So the premise is asserted here, against the seed, once —
    and a future board that is not a per-match rate turns this RED before its heading can lie.
    """
    with open(CATALOGUE_SEED_PATH, encoding="utf-8") as fh:
        rows = {(r["metric_id"], r["entity"]): r for r in csv.DictReader(fh)}

    for metric_id in _HOME_TEAM_BOARDS:
        row = rows.get((metric_id, "team"))
        assert row is not None, f"{metric_id} is not a team metric in the catalogue"
        assert row["denominator_expr"] == "count(*)", (
            f"{metric_id} is denominated by {row['denominator_expr']!r}, not by matches — the "
            f"Top teams heading would call it a per-match rate and be wrong"
        )

    # Two-sided: the catalogue really does distinguish the two, so the assertion above is not
    # vacuously true of every rate in the seed.
    per90 = [r for r in rows.values() if r["denominator_expr"] == "sum(minutes_played)"]
    assert per90, "no per-90 metric in the catalogue; this guard would then discriminate nothing"


# --------------------------------------------------------------------------- #
# The competition display name — registry is INPUT, the warehouse DISPLAYS
# --------------------------------------------------------------------------- #
class _FakeClient:
    """`_query` only needs `client.query(sql).result()` to yield rows with `.items()`, and a plain
    dict has that — so no BigQuery and no row stub."""

    def __init__(self, rows):
        self._rows = rows
        self.sql = None

    def query(self, sql):
        self.sql = sql
        return self

    def result(self):
        return self._rows


def test_the_competition_display_name_comes_from_the_warehouse_not_the_registry():
    """⛔ THE DEFECT THIS PINS SHIPPED. `docs/competition_registry.yml` names BL1
    `1. Fußball-Bundesliga`; `mart_competition_index` names it `Bundesliga`. The export read the
    registry, so the Home intro rendered "... Eredivisie, 1. Fußball-Bundesliga, Premier League"
    and every BL1 team page header said the same. 37 of the 48 names are identical in both sources,
    which is exactly why it hid — so this asserts on one of the 11 that differ.

    The slug is asserted separately, in
    `test_the_overlay_never_takes_the_slug_even_if_the_warehouse_offers_one` — putting it here made
    it vacuous, see that test's note."""
    client = _FakeClient([
        {"league_code": "BL1", "competition_name": "Bundesliga", "region_rank": 1},
    ])
    index = _competitions_index(client)
    assert index["BL1"]["name"] == "Bundesliga"
    # Every registry competition is still present — the overlay narrows nothing.
    assert len(index) > 40


def test_the_overlay_never_takes_the_slug_even_if_the_warehouse_offers_one(monkeypatch):
    """The slug is an ASSIGNED IDENTIFIER, not a display string: it is the URL, so taking it from
    the warehouse would move URL identity out of the registry.

    ⚠ WRITTEN THIS WAY BECAUSE THE OBVIOUS VERSION WAS VACUOUS. Asserting the slug next to the name
    above passed against a deliberately broken `_competitions_index` that DID prefer a served slug
    — `_warehouse_competition_meta` selects only `league_code, competition_name, region_rank`, so
    no slug ever reached the overlay and the assertion could not fail. The helper is patched here
    to hand one over, which is the only way the assertion means anything."""
    monkeypatch.setattr(
        export_site_data, "_warehouse_competition_meta",
        lambda client: {"BL1": {"name": "Bundesliga", "slug": "warehouse-must-not-win-this"}},
    )
    index = _competitions_index(object())
    assert index["BL1"]["name"] == "Bundesliga"
    assert index["BL1"]["slug"] == "bundesliga"


def test_a_competition_the_warehouse_does_not_name_keeps_the_registry_name():
    """The overlay is a correction, not a replacement of the registry as the enumeration. A league
    the mart returns no row for — or returns a NULL name for — keeps the registry's name rather
    than rendering a blank heading."""
    client = _FakeClient([{"league_code": "BL1", "competition_name": None, "region_rank": 1}])
    index = _competitions_index(client)
    assert index["BL1"]["name"] == "1. Fußball-Bundesliga"
    assert index["PL"]["name"] == "Premier League"


def test_the_warehouse_meta_carries_the_name_and_the_region_rank_together():
    """One helper serves both consumers — `fetch_landing_payload`'s `meta` (the fixtures hero's
    group headings and both board blocks) and `_competitions_index` (`competitions.json`, which
    TeamHeader renders). The rule living at two call sites is what let one of them drift."""
    client = _FakeClient([
        {"league_code": "BL1", "competition_name": "Bundesliga", "region_rank": 1},
        {"league_code": "MLS", "competition_name": None, "region_rank": 3},
    ])
    served = _warehouse_competition_meta(client)
    assert served["BL1"] == {"region_rank": 1, "name": "Bundesliga"}
    assert served["MLS"] == {"region_rank": 3}
    assert "mart_competition_index" in client.sql
