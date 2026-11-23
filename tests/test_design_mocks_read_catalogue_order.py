"""The mock generators and the committed site data show metrics in the catalogue's order."""
from __future__ import annotations

import csv
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.insert(0, str(REPO / "design-mocks"))
import export_site_data as export  # noqa: E402
import gen_competition_teams as rankings  # noqa: E402
import gen_match_page as match_page  # noqa: E402
import gen_top_players as top_players  # noqa: E402
import gen_top_teams as top_teams  # noqa: E402
from catalogue_order import place  # noqa: E402


def _catalogue(entity: str) -> dict[str, dict[str, str]]:
    path = REPO / "dbt_project" / "seeds" / "metric_catalogue.csv"
    with path.open(newline="", encoding="utf-8") as f:
        return {r["metric_id"]: r for r in csv.DictReader(f) if r["entity"] == entity}


def _is_in_catalogue_order(metric_ids: list[str], entity: str) -> bool:
    return [place(m, entity) for m in metric_ids] == sorted(place(m, entity) for m in metric_ids)


def test_the_home_mocks_list_their_boards_in_the_catalogue_order():
    assert _is_in_catalogue_order([b["rank_metric"] for b in top_teams.BOARDS], "team")
    assert _is_in_catalogue_order([b["rank_metric"] for b in top_players.BOARDS], "player")


def test_the_rankings_mock_groups_and_lists_its_boards_in_the_catalogue_order():
    for groups, entity in ((rankings.GROUPS, "team"), (rankings.PLAYER_GROUPS, "player")):
        flat = [m for _label, ids in groups for m in ids]
        assert _is_in_catalogue_order(flat, entity), entity
        cat = _catalogue(entity)
        assert [label for label, _ids in groups] == [
            f"metricGroups.{g}.label" for g in dict.fromkeys(cat[m]["metric_group"] for m in flat)
        ], f"{entity}: the group sequence is not the catalogue's"


def test_the_played_match_mock_lists_its_stats_in_the_catalogue_order():
    stats = [(label, col) for _group, rows in match_page.PLAYED_STATS for label, col, _d, _u in rows]
    assert {col for _label, col in stats} == set(match_page.PLAYED_METRIC), "a stat without a catalogue metric"
    fx = {"home": {"name": "H"}, "away": {"name": "A"},
          "team": {col: (1, 2) for _label, col in stats}}
    drawn: list[str] = []
    real = match_page.stat_row
    match_page.stat_row = lambda label, *rest: drawn.append(label) or ""
    try:
        html_out = match_page.stats_block(fx)
    finally:
        match_page.stat_row = real
    expected = [label for label, col in sorted(stats, key=lambda s: place(match_page.PLAYED_METRIC[s[1]], "team"))]
    assert drawn == expected
    groups = re.findall(r'class="mgroup">([^<]+)<', html_out)
    assert groups == ["Shooting", "Passing", "One-on-one", "Defending", "Goalkeeping", "Set pieces", "Discipline"]


def test_the_match_leaders_boards_follow_the_catalogue_order_and_keep_their_set():
    for state_fx in (match_page.PLAYED, match_page.PLAYED_PEN):
        names = [name for _group, boards in state_fx["leaders"] for name, _rows in boards]
        assert set(names) <= set(match_page.LEADER_METRIC), "a board without a catalogue metric"
        shuffled = dict(state_fx, leaders=[(g, list(reversed(b))) for g, b in reversed(state_fx["leaders"])])
        drawn = [re.sub(r"<[^>]*>", "", n) for n in re.findall(
            r'class="bt"><span class="nm">([^<]+)</span>', match_page.leaders_block(shuffled))]
        expected = sorted(names, key=lambda n: place(match_page.LEADER_METRIC[n], "player"))
        assert drawn == expected, "the Match leaders boards must read the catalogue's order"


def test_the_rankings_mock_shows_the_boards_the_rankings_tab_shows():
    team = {m for _label, ids in rankings.GROUPS for m in ids}
    player = {m for _label, ids in rankings.PLAYER_GROUPS for m in ids}
    assert team == set(export._COMPETITION_TEAM_BOARDS)
    assert player == set(export._COMPETITION_PLAYER_BOARDS)


def test_the_committed_player_metric_rows_are_a_fresh_regeneration_from_the_seed():
    committed = (REPO / "site_v2" / "src" / "data" / "player_metric_rows.json").read_text(encoding="utf-8")
    assert committed == export._payload_bytes(export.fetch_player_metric_rows()).decode("utf-8"), (
        "site_v2/src/data/player_metric_rows.json differs from the seed; regenerate it with the export"
    )


def test_a_metric_without_a_place_fails_a_mock():
    try:
        place("cards_player", "player")
    except SystemExit as e:
        assert "cards_player" in str(e)
    else:
        raise AssertionError("a metric without a catalogue order must fail the generator")
