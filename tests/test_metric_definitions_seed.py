"""metric_definitions seed: one row per canonical metric_id."""

from __future__ import annotations

import csv
from pathlib import Path

SEED = Path(__file__).resolve().parents[1] / "dbt_project" / "seeds" / "metric_definitions.csv"


def _rows() -> list[dict[str, str]]:
    with SEED.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_metric_id_unique() -> None:
    ids = [r["metric_id"].strip() for r in _rows()]
    assert len(ids) == len(set(ids))


def test_paired_metrics_have_home_and_away_columns() -> None:
    for row in _rows():
        home = (row.get("home_column") or "").strip()
        away = (row.get("away_column") or "").strip()
        single = (row.get("single_column") or "").strip()
        if single:
            assert not home and not away, row["metric_id"]
        elif row["context"] == "match_preview":
            assert home and away, row["metric_id"]
