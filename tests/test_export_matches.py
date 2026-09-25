"""Unit tests for the Matches page's export: one payload per day from `mart_match_days` (#160).

No BigQuery: fabricated rows only. What is pinned is what the consumption-layer contract allows
the export to do and nothing more. It groups rows by day and competition and carries the mart's
day facts (neighbours, opening day) and the match rows unchanged. It never decides which match is
in reach, which day opens or which competition comes first: the mart decides the first two and
the page the third.
"""

from scripts import export_site_data
from scripts.export_site_data import _competition_fixture, shape_match_day_payloads


def _row(sk, lc, day, order, *, opening=False, prev=None, nxt=None, played=False):
    return {
        "match_day": day, "day_row_order": order, "is_opening_day": opening,
        "previous_day": prev, "next_day": nxt,
        "fixture_sk": sk, "league_code": lc, "season_api_year": 2026, "round_name": "Regular Season - 5",
        "round_order": 5, "round_sequence": 5, "fixture_order": sk, "kickoff_datetime": f"{day} 18:30:00+00:00",
        "status_short": "FT" if played else "NS", "is_played": played,
        "goals_home": 2 if played else None, "goals_away": 1 if played else None,
        "home_team_sk": sk * 10, "home_team_name": f"H{sk}", "home_team_slug": f"h{sk}", "home_team_logo_url": None,
        "away_team_sk": sk * 10 + 1, "away_team_name": f"A{sk}", "away_team_slug": f"a{sk}", "away_team_logo_url": None,
        "fixture_slug": f"{day}-h{sk}-vs-a{sk}", "is_next_round": not played, "is_match_that_matters": False,
    }


_COMPS = {
    "BL1": {"name": "Bundesliga", "slug": "bundesliga", "crest": "https://x/bl1.png",
            "entity_type": "club", "confederation": "UEFA", "region_rank": 1},
    "MLS": {"name": "MLS", "slug": "mls", "crest": None,
            "entity_type": "club", "confederation": "CONCACAF", "region_rank": 4},
}


def test_one_payload_per_day_with_the_marts_day_facts():
    rows = [
        _row(1, "BL1", "2026-09-20", 1, prev=None, nxt="2026-09-26", played=True),
        _row(2, "MLS", "2026-09-26", 1, opening=True, prev="2026-09-20", nxt=None),
    ]
    days = shape_match_day_payloads(rows, _COMPS)
    assert [d["day"] for d in days] == ["2026-09-20", "2026-09-26"]
    first, second = days
    assert (first["is_opening_day"], first["previous_day"], first["next_day"]) == (False, None, "2026-09-26")
    assert (second["is_opening_day"], second["previous_day"], second["next_day"]) == (True, "2026-09-20", None)
    assert first["type"] == "match_day" and first["slug"] == "2026-09-20"


def test_rows_keep_the_served_day_row_order_and_the_match_row_shape():
    """Rows arrive shuffled; the payload keeps day_row_order, the mart's order, and each row is the
    competition payload's match row, unchanged, so the site's one match row renders it."""
    rows = [
        _row(3, "BL1", "2026-09-26", 3, opening=True),
        _row(1, "BL1", "2026-09-26", 1, opening=True),
        _row(2, "BL1", "2026-09-26", 2, opening=True),
    ]
    (day,) = shape_match_day_payloads(rows, _COMPS)
    (bl1,) = day["competitions"]
    assert [f["fixture_id"] for f in bl1["fixtures"]] == [1, 2, 3]
    assert bl1["fixtures"][0] == _competition_fixture(rows[1])


def test_a_competition_carries_its_facts_and_no_order_is_invented():
    rows = [_row(2, "MLS", "2026-09-26", 1, opening=True), _row(1, "BL1", "2026-09-26", 1, opening=True)]
    (day,) = shape_match_day_payloads(rows, _COMPS)
    assert [c["league_code"] for c in day["competitions"]] == ["BL1", "MLS"]
    bl1 = day["competitions"][0]
    assert {k: bl1[k] for k in _COMPS["BL1"]} == _COMPS["BL1"]
    assert set(bl1) == {"league_code", *_COMPS["BL1"], "fixtures"}


def test_a_played_row_carries_its_score():
    (day,) = shape_match_day_payloads([_row(1, "BL1", "2026-09-20", 1, played=True)], _COMPS)
    row = day["competitions"][0]["fixtures"][0]
    assert (row["is_played"], row["goals_home"], row["goals_away"]) == (True, 2, 1)


def test_the_fetch_reads_the_mart_whole_and_selects_nothing(monkeypatch):
    """The reach, the neighbours and the opening day are the mart's: the query joins the day rows to
    their match rows and filters, ranks and windows nothing."""
    captured = []

    def fake_query(client, sql):
        captured.append(sql)
        if "mart_match_days" in sql:
            return [_row(1, "BL1", "2026-09-26", 1, opening=True)]
        return []

    monkeypatch.setattr(export_site_data, "_query", fake_query)
    monkeypatch.setattr(export_site_data, "_warehouse_competition_meta",
                        lambda client: {"BL1": {"name": "Bundesliga", "region_rank": 1}})
    monkeypatch.setattr(export_site_data, "_competition_page_meta",
                        lambda client: {"BL1": {"logo_url": "https://x/bl1.png", "entity_type": "club"}})
    (day,) = export_site_data.fetch_match_day_payloads(object())
    sql = next(s for s in captured if "mart_match_days" in s).lower()
    for word in ("where", "row_number", "qualify", "current_date", "order by", "limit"):
        assert word not in sql, word
    bl1 = day["competitions"][0]
    assert (bl1["name"], bl1["slug"], bl1["crest"], bl1["entity_type"], bl1["region_rank"]) == (
        "Bundesliga", "bundesliga", "https://x/bl1.png", "club", 1)
    assert bl1["confederation"] == "UEFA"
