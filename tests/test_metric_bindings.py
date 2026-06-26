"""metric_bindings: the live match-preview wiring, plus the byte-identity guard for its JSON.

The live match-preview data file (site/match-preview/metric_definitions.json) is generated
from metric_bindings.csv (wiring) + metric_catalogue.csv (definition). These tests keep the
wiring well-formed and lock the generated file to a fresh regeneration, so future steps cannot
silently change what the live site renders.
"""

from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BINDINGS = REPO / "site" / "match-preview" / "metric_bindings.csv"
CATALOGUE = REPO / "dbt_project" / "seeds" / "metric_catalogue.csv"
COMMITTED_JSON = REPO / "site" / "match-preview" / "metric_definitions.json"
EXPORT = REPO / "scripts" / "export_metric_definitions_json.py"


def _binding_rows() -> list[dict[str, str]]:
    with BINDINGS.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _catalogue_ids() -> set[str]:
    with CATALOGUE.open(newline="", encoding="utf-8") as f:
        return {(r.get("metric_id") or "").strip() for r in csv.DictReader(f)}


def test_live_ids_unique() -> None:
    ids = [(r.get("live_id") or "").strip() for r in _binding_rows()]
    assert ids
    assert len(ids) == len(set(ids))


def test_every_binding_resolves_to_a_catalogue_metric() -> None:
    catalogue = _catalogue_ids()
    for row in _binding_rows():
        cat_id = (row.get("catalogue_metric_id") or "").strip()
        assert cat_id in catalogue, f"{row.get('live_id')} -> unknown catalogue metric '{cat_id}'"


def test_match_preview_bindings_are_paired() -> None:
    for row in _binding_rows():
        if (row.get("context") or "").strip() == "match_preview":
            assert (row.get("home_column") or "").strip(), row.get("live_id")
            assert (row.get("away_column") or "").strip(), row.get("live_id")


def test_regenerated_json_matches_committed() -> None:
    """Running the export (default sources) must reproduce the committed data file exactly."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "metric_definitions.json"
        subprocess.run(
            [sys.executable, str(EXPORT), "--out", str(out)],
            check=True,
            cwd=str(REPO),
        )
        assert out.read_text(encoding="utf-8") == COMMITTED_JSON.read_text(encoding="utf-8")
