"""Unit tests for pages export manifest shape (WC block)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock


def _load_export_pages_data():
    path = Path(__file__).resolve().parents[1] / "scripts" / "export_pages_data.py"
    spec = importlib.util.spec_from_file_location("export_pages_data", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_manifest_includes_wc_block_with_matchday_counts(tmp_path, monkeypatch):
    mod = _load_export_pages_data()
    artifacts = tmp_path / "artifacts"

    class _Row:
        def __init__(self, items):
            self._items = items

        def items(self):
            return self._items

    def _query_result(rows):
        result = MagicMock()
        result.result.return_value = [_Row(r) for r in rows]
        return result

    client = MagicMock()
    fixture_row = {
        "fixture_sk": 1,
        "league_code": "WC",
        "home_team_name": "A",
        "away_team_name": "B",
    }
    client.query.side_effect = [
        _query_result([fixture_row]),  # BL1 matchday
        _query_result([]),  # BL1 team season
        _query_result([fixture_row]),  # WC matchday
    ]

    monkeypatch.setattr(mod, "domestic_league_codes", lambda: ["BL1"])

    import google.cloud.bigquery as bq

    monkeypatch.setattr(bq, "Client", lambda project: client)

    manifest = mod.export_all(artifacts_root=artifacts)

    assert "wc" in manifest
    assert manifest["wc"]["league_code"] == "WC"
    assert manifest["wc"]["matchday_row_count"] == 1
    assert manifest["wc"]["matchday_source_mart"] == "mart_matchday_insights_wc"
    assert manifest["wc"]["matchday_path"] == "data/wc/matchday_insights.json"

    wc_json = artifacts / "data" / "wc" / "matchday_insights.json"
    assert wc_json.is_file()
    payload = json.loads(wc_json.read_text(encoding="utf-8"))
    assert len(payload["show"]) == 1
