"""Offline unit tests for the landing-page export helpers, run on fabricated rows."""

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
    "BSA": {"name": "Brasileirão Série A", "slug": "brasileirao-serie-a",
            "crest": "https://x/bsa.png"},
    "MLS": {"name": "Major League Soccer", "slug": "mls", "crest": None},
    "BL1": {"name": "Bundesliga", "slug": "bundesliga", "crest": "https://x/bl1.png"},
}


def _fixture(sk, league_code, kickoff, season=2026, rnd="Regular Season - 20", order=1,
             away_crest=None, slug=None, matters=False):
    """One mart_competition_fixtures row of a next matchday, as the hero's query returns it."""
    return {
        "fixture_sk": sk, "league_code": league_code, "season_api_year": season,
        "round_name": rnd, "round_order": 20, "round_sequence": 20, "fixture_order": order,
        "kickoff_datetime": kickoff, "status_short": "NS", "is_played": False,
        "goals_home": None, "goals_away": None,
        "home_team_sk": 1, "home_team_name": "Palmeiras", "home_team_slug": "palmeiras",
        "home_team_logo_url": "https://x/1.png",
        "away_team_sk": 2, "away_team_name": "Flamengo", "away_team_slug": "flamengo",
        "away_team_logo_url": away_crest,
        "fixture_slug": slug, "is_next_round": True, "is_match_that_matters": matters,
    }


# --------------------------------------------------------------------------- #
# Fixtures hero
# --------------------------------------------------------------------------- #
def test_group_upcoming_fixtures_keeps_the_served_order():
    fixtures = [
        _fixture(11, "BSA", "2026-08-04T23:00:00Z"),
        _fixture(10, "MLS", "2026-08-04T01:00:00Z", order=1),
        _fixture(12, "MLS", "2026-08-05T01:00:00Z", order=2),
    ]
    groups = group_upcoming_fixtures(fixtures, _META)

    assert [g["league_code"] for g in groups] == ["BSA", "MLS"]
    assert [f["fixture_id"] for f in groups[1]["fixtures"]] == [10, 12]
    assert groups[1]["league_name"] == "Major League Soccer"
    assert groups[1]["competition_slug"] == "mls"


def test_group_upcoming_fixtures_carries_the_shared_match_row_shape():
    row = _fixture(10, "BSA", "2026-08-04T23:00:00Z", matters=True)
    fx = group_upcoming_fixtures([row], _META)[0]["fixtures"][0]
    assert fx == export_site_data._competition_fixture(row)
    assert fx["status"] == "NS"
    assert fx["is_match_that_matters"] is True


def test_group_upcoming_fixtures_carries_the_served_competition_crest():
    groups = group_upcoming_fixtures(
        [_fixture(10, "BSA", "2026-08-04T23:00:00Z"), _fixture(11, "MLS", "2026-08-05T01:00:00Z")],
        _META,
    )
    assert {g["league_code"]: g["crest"] for g in groups} == {
        "BSA": "https://x/bsa.png", "MLS": None,
    }


def test_group_upcoming_fixtures_caps_nothing():
    fixtures = [_fixture(i, "BSA", f"2026-08-0{i}T20:00:00Z", order=i) for i in range(1, 6)]
    groups = group_upcoming_fixtures(fixtures, _META)
    assert sum(len(g["fixtures"]) for g in groups) == 5, "every fixture handed in is grouped"


def test_group_upcoming_fixtures_carries_the_served_fixture_slug():
    """A row without a served slug links nowhere rather than somewhere wrong."""
    row = _fixture(10, "BSA", "2026-08-04T23:00:00Z", slug="2026-08-04-palmeiras-vs-flamengo")
    groups = group_upcoming_fixtures([row], _META)
    assert groups[0]["fixtures"][0]["slug"] == "2026-08-04-palmeiras-vs-flamengo"
    bare = group_upcoming_fixtures([_fixture(11, "BSA", "2026-08-04T23:00:00Z")], _META)
    assert bare[0]["fixtures"][0]["slug"] is None


def test_group_upcoming_fixtures_keeps_a_null_crest_null():
    """A missing crest is a real absence the page renders as a monogram, never a fake URL."""
    groups = group_upcoming_fixtures([_fixture(10, "BSA", "2026-08-04T23:00:00Z")], _META)
    assert groups[0]["fixtures"][0]["away"]["crest"] is None


def test_group_upcoming_fixtures_omits_a_competition_with_no_fixture_in_the_window():
    fixtures = [_fixture(10, "MLS", "2026-08-04T01:00:00Z")]
    groups = group_upcoming_fixtures(fixtures, _META)
    assert [g["league_code"] for g in groups] == ["MLS"], "BSA is in _META but has no fixture"
    assert all(g["fixtures"] for g in groups), "no group may be emitted empty"


def test_group_upcoming_fixtures_handles_an_empty_calendar():
    assert group_upcoming_fixtures([], _META) == []


def test_the_hero_reads_the_next_matchday_mart_whole_in_the_served_order(monkeypatch):
    """The hero SQL reads mart_next_matchday whole, ordered by served columns, with no selection."""
    captured: list[str] = []

    def fake_query(client, sql):
        captured.append(sql)
        if "mart_next_matchday" in sql:
            return [
                _fixture(11, "BL1", "2026-09-18T18:30:00Z", rnd="Regular Season - 4", order=1),
                _fixture(12, "BL1", "2026-09-20T15:30:00Z", rnd="Regular Season - 4", order=2),
                _fixture(13, "MLS", "2026-09-19T23:00:00Z", rnd="Regular Season - 26"),
            ]
        return []

    monkeypatch.setattr(export_site_data, "_query", fake_query)
    monkeypatch.setattr(export_site_data, "_warehouse_competition_meta", lambda client: {})
    monkeypatch.setattr(export_site_data, "_competition_page_meta",
                        lambda client: {"BL1": {"logo_url": "https://x/bl1.png"}})

    payload = export_site_data.fetch_landing_payload(object())

    hero_sql = next(s for s in captured if "mart_next_matchday" in s)
    assert "core.fct_fixture" not in hero_sql, "the hero reads the mart, not the fact"
    lowered = " ".join(hero_sql.lower().split())
    for token in ("where", "min(fixture_date)", "row_number", "qualify", "current_date"):
        assert token not in lowered, f"selection vocabulary in the export: {token!r}"
    assert "order by n.competition_order, c.fixture_order" in lowered
    assert not any("core.dim_team" in s for s in captured), "the match rows carry the teams"

    assert [g["league_code"] for g in payload["upcoming"]] == ["BL1", "MLS"]
    groups = {g["league_code"]: g for g in payload["upcoming"]}
    assert groups["BL1"]["crest"] == "https://x/bl1.png", "the crest is mart_competition_index's"
    assert groups["MLS"]["crest"] is None, "a competition the mart gives no crest has none"
    assert [f["fixture_id"] for f in groups["BL1"]["fixtures"]] == [11, 12], (
        "every served fixture of the round is carried; the page folds, the export does not cut"
    )
    assert {f["round"] for f in groups["BL1"]["fixtures"]} == {"Regular Season - 4"}
    assert [f["fixture_id"] for f in groups["MLS"]["fixtures"]] == [13]


# --------------------------------------------------------------------------- #
# Payload assembly
# --------------------------------------------------------------------------- #
def test_shape_landing_payload_carries_only_the_built_modules():
    """The key set is exact, so a re-added block fails whether populated or an empty shell."""
    payload = shape_landing_payload(
        upcoming=[{"league_code": "BSA"}],
        top_players=[{"metric_key": "goals_player", "rows": [{"name": "X"}]}],
        top_teams=[{"metric_key": "goals_per_match", "rows": [{"name": "Y"}]}],
    )
    assert payload["type"] == "landing"
    assert set(payload) == {"type", "upcoming", "top_players", "top_teams"}


def test_shape_landing_payload_omits_top_players_when_no_board_survived():
    """An empty result is absent from the payload, not an empty list the page must guard."""
    for empty in ([], None):
        payload = shape_landing_payload(
            upcoming=[{"league_code": "BSA"}], top_players=empty, top_teams=empty,
        )
        assert "top_players" not in payload, f"empty {empty!r} must not reach the payload"
        assert "top_teams" not in payload, f"empty {empty!r} must not reach the payload"
        assert set(payload) == {"type", "upcoming"}


def test_shape_landing_payload_carries_none_of_the_removed_blocks():
    """Named per block so a failure says which block came back."""
    payload = shape_landing_payload([])
    assert "stats" not in payload
    assert "trending" not in payload
    assert "browse" not in payload


# --------------------------------------------------------------------------- #
# Top players
# --------------------------------------------------------------------------- #
_LEAGUE_META = {
    "PL": {"name": "Premier League"},
    "PD": {"name": "La Liga"},
    "BL1": {"name": "Bundesliga"},
}

# Read from the real catalogue seed so the label mechanism cannot drift from it.
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
    """The shaper does not sort: it groups rows into boards, keeps their order and cuts at 7."""
    boards = shape_home_top_players([
        _lb("goals_player", "PL", "Haaland", 25.0, 12),
        _lb("goals_player", "PD", "Mbappe", 21.0, 10),
        _lb("goals_player", "BL1", "Kane", 20.0, 11),
    ], _LEAGUE_META, _LABEL_KEYS)
    assert len(boards) == 1
    assert boards[0]["metric_key"] == "goals_player"
    assert [r["name"] for r in boards[0]["rows"]] == ["Haaland", "Mbappe", "Kane"]
    assert [r["league_name"] for r in boards[0]["rows"]] == ["Premier League", "La Liga", "Bundesliga"]
    assert boards[0]["rows"][0]["club"] == "Haaland FC"
    assert boards[0]["rows"][0]["slug"] == "haaland-12"


def test_top_players_does_not_reorder_what_it_is_given():
    """Rows in an order no sort would produce must come out exactly as they went in."""
    rows = [
        _lb("goals_player", "BL1", "Lowest", 2.0, 11),
        _lb("goals_player", "PL", "Highest", 30.0, 12),
        _lb("goals_player", "PD", "Middle", 9.0, 13),
    ]
    boards = shape_home_top_players(rows, _LEAGUE_META, _LABEL_KEYS)
    assert [r["name"] for r in boards[0]["rows"]] == ["Lowest", "Highest", "Middle"]


def test_top_players_keeps_board_order_and_caps_each_at_seven():
    """Boards keep a fixed order and cap at 7; nine leagues as the query returns one row each."""
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


def test_top_players_omits_an_empty_board_and_survivors_keep_their_order():
    """An empty board is absent, with no placeholder, and the survivors keep their order."""
    boards = shape_home_top_players([
        _lb("goals_player", "PL", "A", 5.0),
        _lb("passes_key_player", "PL", "B", 3.0),
    ], _LEAGUE_META, _LABEL_KEYS)
    assert [b["metric_key"] for b in boards] == ["goals_player", "passes_key_player"]


def test_top_players_carries_the_catalogue_label_key_not_a_hand_written_name():
    """The board ships the catalogue's label key, asserted against the seed, not a literal."""
    boards = shape_home_top_players(
        [_lb("goals_player", "PL", "A", 5.0)], _LEAGUE_META, _LABEL_KEYS
    )
    assert boards[0]["label_i18n_key"] == _LABEL_KEYS["goals_player"]["label_i18n_key"]
    assert boards[0]["label_i18n_key"], "a board must never ship without a label key"


def test_board_label_keys_are_the_player_rows_not_the_team_ones():
    """Labels come from the catalogue row of the board's entity; metric_id alone is not unique."""
    import csv

    with open("dbt_project/seeds/metric_catalogue.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for metric_id, entry in _LABEL_KEYS.items():
        player = [r for r in rows if r["metric_id"] == metric_id and r["entity"] == "player"]
        assert player, f"{metric_id} has no player row"
        assert entry["label_i18n_key"] == player[0]["label_i18n_key"]

    for metric_id, entry in _TEAM_CATALOGUE.items():
        team = [r for r in rows if r["metric_id"] == metric_id and r["entity"] == "team"]
        assert team, f"{metric_id} has no team row"
        assert entry["label_i18n_key"] == team[0]["label_i18n_key"]
        assert entry["format"] == team[0]["format"]


def test_top_teams_renders_the_order_the_warehouse_served():
    """Same contract as the player shaper: group, preserve, cap, never sort."""
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
    """Rows in an order no sort would produce must come out exactly as they went in."""
    rows = [
        _tlb("goals_per_match", "BL1", "Lowest", 0.9, 11),
        _tlb("goals_per_match", "PL", "Highest", 3.3, 12),
        _tlb("goals_per_match", "PD", "Middle", 2.0, 13),
    ]
    boards = shape_home_top_teams(rows, _LEAGUE_META, _TEAM_CATALOGUE)
    assert [r["name"] for r in boards[0]["rows"]] == ["Lowest", "Highest", "Middle"]


def test_top_teams_carries_the_catalogue_format_per_board():
    """The format travels per board from the catalogue because the boards share no one format."""
    rows = [_tlb(key, "PL", f"T-{key}", 1.5) for key in _HOME_TEAM_BOARDS]
    boards = shape_home_top_teams(rows, _LEAGUE_META, _TEAM_CATALOGUE)
    by_key = {b["metric_key"]: b["format"] for b in boards}
    assert by_key["goals_per_match"] == "decimal_1"
    assert by_key["shots_on_goal_per_match"] == "decimal_1"
    assert by_key["passes_per_match"] == "decimal_0"
    assert by_key["duels_per_match"] == "decimal_0"
    assert len(set(by_key.values())) == 2, "the boards must not collapse to one shared format"


def test_home_boards_carry_the_catalogue_format_and_per_match():
    """Every Home board carries the catalogue's format and per_match, read from the seed."""
    players = shape_home_top_players(
        [_lb(key, "PL", f"P-{key}", 3.0) for key in _LABEL_KEYS], _LEAGUE_META, _LABEL_KEYS,
    )
    teams = shape_home_top_teams(
        [_tlb(key, "PL", f"T-{key}", 1.5) for key in _HOME_TEAM_BOARDS], _LEAGUE_META,
        _TEAM_CATALOGUE,
    )
    for board in players:
        assert board["format"] == _LABEL_KEYS[board["metric_key"]]["format"]
        assert board["per_match"] is False
    for board in teams:
        assert board["per_match"] is True, f"{board['metric_key']} is a per-match rate"


def test_top_teams_rows_carry_the_served_slug():
    """Rows carry the served `dim_team.team_slug`; the export generates no identity."""
    boards = shape_home_top_teams(
        [_tlb("goals_per_match", "PL", "Alpha", 2.4)], _LEAGUE_META, _TEAM_CATALOGUE,
    )
    row = boards[0]["rows"][0]
    assert row["slug"] == "alpha-fc"
    assert set(row) == {"team_id", "slug", "name", "crest", "league_code", "league_name", "value"}


def test_top_teams_keeps_board_order_and_caps_each_at_seven():
    """Boards keep a fixed order and cap at 7; nine leagues as the query returns one team each."""
    nine = ("PL", "PD", "BL1", "ED", "L1", "LP", "SA", "PPL", "TSL")
    rows = []
    for key in ("duels_per_match", "goals_per_match", "passes_per_match", "shots_on_goal_per_match"):
        for i, league in enumerate(nine):
            rows.append(_tlb(key, league, f"{key}-{i}", 9.0 - i, team_sk=i))
    boards = shape_home_top_teams(rows, _LEAGUE_META, _TEAM_CATALOGUE)
    assert [b["metric_key"] for b in boards] == list(_HOME_TEAM_BOARDS)
    assert all(len(b["rows"]) == 7 for b in boards)


def test_top_teams_omits_an_empty_board_and_returns_nothing_when_all_are_empty():
    """An empty board is absent, and the shaper returns an empty list when none survives."""
    boards = shape_home_top_teams([
        _tlb("goals_per_match", "PL", "Alpha", 2.4),
        _tlb("duels_per_match", "PL", "Beta", 48.0),
    ], _LEAGUE_META, _TEAM_CATALOGUE)
    assert [b["metric_key"] for b in boards] == ["goals_per_match", "duels_per_match"]
    assert shape_home_top_teams([], _LEAGUE_META, _TEAM_CATALOGUE) == []


def test_top_players_returns_nothing_when_no_board_has_data():
    """When no board has data the shaper returns an empty list."""
    assert shape_home_top_players([], _LEAGUE_META, _LABEL_KEYS) == []
    # A metric the home block does not show must not create a board either.
    assert shape_home_top_players([_lb("cards_player", "PL", "A", 9.0)], _LEAGUE_META, _LABEL_KEYS) == []


def test_the_team_board_set_is_all_per_match_rates():
    """Every team board divides by matches in the catalogue, so its per-match heading cannot lie."""
    with open(CATALOGUE_SEED_PATH, encoding="utf-8") as fh:
        rows = {(r["metric_id"], r["entity"]): r for r in csv.DictReader(fh)}

    for metric_id in _HOME_TEAM_BOARDS:
        row = rows.get((metric_id, "team"))
        assert row is not None, f"{metric_id} is not a team metric in the catalogue"
        assert row["denominator_expr"] == "count(*)", (
            f"{metric_id} is denominated by {row['denominator_expr']!r}, not by matches — the "
            f"Top teams heading would call it a per-match rate and be wrong"
        )

    # Two-sided: guards the assertion above against being vacuously true of every rate.
    per90 = [r for r in rows.values() if r["denominator_expr"] == "sum(minutes)"]
    assert per90, "no per-90 metric in the catalogue; this guard would then discriminate nothing"


# --------------------------------------------------------------------------- #
# The competition display name: the registry is input, the warehouse displays
# --------------------------------------------------------------------------- #
class _FakeClient:
    """Stands in for BigQuery: `_query` only needs `.query(sql).result()` to yield dict rows."""

    def __init__(self, rows):
        self._rows = rows
        self.sql = None

    def query(self, sql):
        self.sql = sql
        return self

    def result(self):
        return self._rows


def test_the_competition_display_name_comes_from_the_warehouse_not_the_registry():
    """The name is mart_competition_index's, not the registry's, which names BL1 differently."""
    client = _FakeClient([
        {"league_code": "BL1", "competition_name": "Bundesliga", "region_rank": 1},
    ])
    index = _competitions_index(client)
    assert index["BL1"]["name"] == "Bundesliga"
    # Every registry competition is still present — the overlay narrows nothing.
    assert len(index) > 40


def test_the_overlay_never_takes_the_slug_even_if_the_warehouse_offers_one(monkeypatch):
    """The slug is the URL, so the overlay never takes it from the warehouse even when offered."""
    # The helper is patched to offer a slug; otherwise none reaches the overlay.
    monkeypatch.setattr(
        export_site_data, "_warehouse_competition_meta",
        lambda client: {"BL1": {"name": "Bundesliga", "slug": "warehouse-must-not-win-this"}},
    )
    index = _competitions_index(object())
    assert index["BL1"]["name"] == "Bundesliga"
    assert index["BL1"]["slug"] == "bundesliga"


def test_a_competition_the_warehouse_does_not_name_keeps_the_registry_name():
    """A league with no served row or a NULL name keeps the registry's name, never a blank."""
    client = _FakeClient([{"league_code": "BL1", "competition_name": None, "region_rank": 1}])
    index = _competitions_index(client)
    assert index["BL1"]["name"] == "1. Fußball-Bundesliga"
    assert index["PL"]["name"] == "Premier League"


def test_the_warehouse_meta_carries_the_name_and_the_region_rank_together():
    """One helper serves both `fetch_landing_payload`'s meta and `_competitions_index`."""
    client = _FakeClient([
        {"league_code": "BL1", "competition_name": "Bundesliga", "region_rank": 1},
        {"league_code": "MLS", "competition_name": None, "region_rank": 3},
    ])
    served = _warehouse_competition_meta(client)
    assert served["BL1"] == {"region_rank": 1, "name": "Bundesliga"}
    assert served["MLS"] == {"region_rank": 3}
    assert "mart_competition_index" in client.sql
