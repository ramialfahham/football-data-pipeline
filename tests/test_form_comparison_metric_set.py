"""The rows of two approved comparisons are pinned as sets.

The match page's Form comparison and the Player page's comparisons show every metric their mart
serves that has a `metric_order` in the catalogue. A place given to a metric for another page would
therefore add a row to these approved pages without anyone deciding it. The order of the rows
follows the catalogue; the set changes only with its page's design.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import export_site_data as export  # noqa: E402

FORM_COMPARISON = {
    "goals_per_match", "goals_against_per_match", "clean_sheets",
    "shots_per_match", "shots_on_goal_per_match", "shots_on_goal_against_per_match",
    "shots_inside_box_per_match", "shots_inside_box_pct", "shots_on_goal_pct", "finishing_efficiency_pct",
    "passes_per_match", "passes_accurate_per_match", "passes_accuracy_pct", "passes_key_per_match",
    "passes_share_pct",
    "dribbles_attempts_per_match", "dribbles_success_per_match", "dribbles_success_pct",
    "duels_per_match", "duels_won_per_match", "duels_won_pct",
    "defensive_actions_per_match", "tackles_per_match", "interceptions_per_match", "blocks_per_match",
    "saves_per_match", "saves_pct",
    "corners_per_match", "corners_against_per_match", "free_kicks_per_match",
    "fouls_per_match", "offsides_per_match", "cards_yellow", "cards_red",
}

PLAYER_COMPARISON = {
    "goals_per90", "assists_per90", "scorer_points_per90",
    "shots_per90", "shots_on_goal_per90", "shots_on_goal_player_pct", "finishing_efficiency_player_pct",
    "passes_per90", "passes_accuracy_player_pct", "passes_key_per90", "ball_actions_per90",
    "dribbles_success_per90", "dribbles_success_player_pct", "duels_won_per90", "duels_won_player_pct",
    "defensive_actions_per90", "tackles_per90", "interceptions_per90", "blocks_per90",
    "saves_per90", "saves_player_pct", "goals_against_per90",
    "fouls_per90", "offsides_per90",
}


def test_the_form_comparison_shows_its_approved_metrics():
    served = {r["metric_id"] for r in export.fetch_metric_rows()["rows"]}
    assert served == FORM_COMPARISON, (
        f"added {sorted(served - FORM_COMPARISON)}, dropped {sorted(FORM_COMPARISON - served)}"
    )


def test_the_player_comparison_shows_its_approved_metrics():
    served = {r["metric_id"] for r in export.fetch_player_metric_rows()["rows"]}
    assert served == PLAYER_COMPARISON, (
        f"added {sorted(served - PLAYER_COMPARISON)}, dropped {sorted(PLAYER_COMPARISON - served)}"
    )
