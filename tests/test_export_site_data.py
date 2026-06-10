"""Unit tests for the per-entity site export pure helpers (#365).

No BigQuery — exercises slugify, payload shaping and manifest building with
fabricated rows so python-ci validates the logic offline.
"""

from scripts.export_site_data import (
    build_manifest,
    shape_player_payload,
    shape_team_payload,
    slugify,
)


def test_slugify_folds_accents_and_appends_id():
    assert slugify("Bayern München", 157) == "bayern-munchen-157"


def test_slugify_collapses_punctuation_and_spaces():
    assert slugify("Brighton & Hove Albion", 51) == "brighton-hove-albion-51"


def test_slugify_falls_back_to_id_when_name_empty():
    assert slugify("", 99) == "99"
    assert slugify(None, 99) == "99"


def test_shape_team_payload_identity_from_latest_and_seasons_desc():
    rows = [
        {"team_sk": 157, "season_api_year": 2024, "league_code": "BL1",
         "team_name": "Bayern", "team_country": "Germany",
         "team_logo_url": "u", "points": 78},
        {"team_sk": 157, "season_api_year": 2025, "league_code": "BL1",
         "team_name": "Bayern München", "team_country": "Germany",
         "team_logo_url": "u2", "points": 82},
    ]
    p = shape_team_payload(rows)
    assert p["team_id"] == 157
    assert p["slug"] == "bayern-munchen-157"          # from the 2025 (latest) row
    assert p["name"] == "Bayern München"
    assert [s["season_api_year"] for s in p["seasons"]] == [2025, 2024]  # desc
    # identity columns are stripped from per-season rows
    assert "team_name" not in p["seasons"][0]
    assert p["seasons"][0]["points"] == 82


def test_shape_player_payload_orders_match_log_desc():
    profiles = [
        {"player_sk": 1090, "season_api_year": 2025, "league_code": "BL1",
         "player_name": "Jamal Musiala", "player_photo_url": "ph",
         "player_nationality": "Germany", "position_code": "M", "goals": 12},
    ]
    matches = [
        {"player_sk": 1090, "kickoff_datetime": "2025-09-01T18:30:00",
         "opponent_name": "A", "goals_total": 1},
        {"player_sk": 1090, "kickoff_datetime": "2025-10-01T18:30:00",
         "opponent_name": "B", "goals_total": 0},
    ]
    p = shape_player_payload(profiles, matches)
    assert p["player_id"] == 1090
    assert p["slug"] == "jamal-musiala-1090"
    assert p["position"] == "M"
    assert [m["opponent_name"] for m in p["match_log"]] == ["B", "A"]  # latest first


def test_build_manifest_counts_by_type():
    entries = [
        {"type": "team", "id": 1, "slug": "a-1", "path": "teams/1.json", "sha256": "x"},
        {"type": "team", "id": 2, "slug": "b-2", "path": "teams/2.json", "sha256": "y"},
        {"type": "player", "id": 3, "slug": "c-3", "path": "players/3.json", "sha256": "z"},
    ]
    m = build_manifest(entries)
    assert m["counts"] == {"team": 2, "player": 1}
    assert len(m["entries"]) == 3
    assert "generated_at" in m
