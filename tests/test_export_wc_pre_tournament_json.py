"""Unit tests for WC pre-tournament JSON export payload shape."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "export_wc_pre_tournament_json.py"
    spec = importlib.util.spec_from_file_location("export_wc_pre_tournament_json", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_payload_top_level_keys():
    mod = _load_module()
    payload = {
        "league_code": mod.LEAGUE_CODE,
        "season_api_year": 2026,
        "exported_at": "2026-05-18T12:00:00+00:00",
        "teams": [{"team_sk": "x", "team_name": "Testland"}],
    }
    assert payload["league_code"] == "WC"
    assert isinstance(payload["teams"], list)
    assert payload["season_api_year"] == 2026
