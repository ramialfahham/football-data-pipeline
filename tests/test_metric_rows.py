"""The match page's Form comparison rows are the catalogue's, and the site reads a copy of them.

`site_v2/src/data/metric_rows.json` is a committed build input the export writes from
`metric_catalogue.csv`: every team metric with a `metric_order`. These tests lock the committed
file to a fresh regeneration, hold the row set to the metrics `mart_team_momentum` serves (minus
the Results group, which the page shows elsewhere), and hold each group's order to the positions
1..N.
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CATALOGUE = REPO / "dbt_project" / "seeds" / "metric_catalogue.csv"
METRIC_MAP = REPO / "dbt_project" / "seeds" / "metric_map.csv"
COMMITTED_JSON = REPO / "site_v2" / "src" / "data" / "metric_rows.json"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import export_site_data as export  # noqa: E402


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_the_committed_file_is_a_fresh_regeneration_from_the_seed():
    fresh = export._payload_bytes(export.fetch_metric_rows()).decode("utf-8")
    assert COMMITTED_JSON.read_text(encoding="utf-8") == fresh, (
        "site_v2/src/data/metric_rows.json differs from the seed. Regenerate it: "
        "python scripts/export_site_data.py --entities metric_rows, then copy metric_rows.json."
    )


def test_the_rows_are_the_form_window_metrics_outside_results():
    team = {r["metric_id"]: r for r in _read(CATALOGUE) if r["entity"] == "team"}
    served = {r["metric_id"] for r in _read(METRIC_MAP) if r["table_name"] == "mart_team_momentum"}
    expected = {m for m in served if team[m]["metric_group"] != "outcomes"}
    rows = {r["metric_id"] for r in export.fetch_metric_rows()["rows"]}
    assert len(expected) >= 30
    assert rows == expected, (
        f"metric_order set but not in the form window: {sorted(rows - expected)}; "
        f"in the form window without a metric_order: {sorted(expected - rows)}"
    )


def test_each_group_is_ordered_one_to_n():
    by_group: dict[str, list[int]] = {}
    for r in export.fetch_metric_rows()["rows"]:
        by_group.setdefault(r["metric_group"], []).append(r["metric_order"])
    bad = {g: o for g, o in by_group.items() if o != list(range(1, len(o) + 1))}
    assert bad == {}, f"groups whose metric_order is not 1..N in file order: {bad}"


def test_the_rows_follow_the_group_order():
    order = {g["key"]: g["order"] for g in export.fetch_metric_groups()["groups"]}
    seq = [order[r["metric_group"]] for r in export.fetch_metric_rows()["rows"]]
    assert seq == sorted(seq)


def test_a_per_match_row_is_a_count_star_average_and_not_a_share():
    team = {r["metric_id"]: r for r in _read(CATALOGUE) if r["entity"] == "team"}
    for r in export.fetch_metric_rows()["rows"]:
        c = team[r["metric_id"]]
        assert r["per_match"] == (c["denominator_expr"] == "count(*)" and c["format"] != "percent"), r
