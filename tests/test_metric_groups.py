"""The metric groups are defined once, in the catalogue, and the site reads a copy of that.

`site_v2/src/data/metric_groups.json` is a committed build input the export writes from
`metric_catalogue.csv` (key and order, one row per group). These tests lock the committed file to
a fresh regeneration from the seed — the `test_metric_bindings.py` pattern — so a group renamed or
reordered in the seed cannot ship while the site still lists the old set, and check the seed's
own group facts offline: every group has one order, and the orders are the positions 1..N. The
same rule runs in the warehouse as `assert_metric_group_order_is_one_per_group`; this copy is
what fails a merge request before a build.
"""
from __future__ import annotations

import csv
import io
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CATALOGUE = REPO / "dbt_project" / "seeds" / "metric_catalogue.csv"
COMMITTED_JSON = REPO / "site_v2" / "src" / "data" / "metric_groups.json"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import export_site_data as export  # noqa: E402


def _rows() -> list[dict[str, str]]:
    with CATALOGUE.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_the_committed_file_is_a_fresh_regeneration_from_the_seed():
    fresh = export._payload_bytes(export.fetch_metric_groups()).decode("utf-8")
    # `read_text` folds a CRLF checkout to LF, as `test_metric_bindings.py` does: the bytes
    # git hands a Windows working tree differ from the export's, the content must not
    assert COMMITTED_JSON.read_text(encoding="utf-8") == fresh, (
        "site_v2/src/data/metric_groups.json differs from the seed. Regenerate it: "
        "python scripts/export_site_data.py --entities metric_groups, then copy metric_groups.json."
    )


def _out_of_position(payload: dict, groups: set[str]) -> list[str]:
    """Why the payload is not one row per group at positions 1..N; empty when it is."""
    listed = [g["key"] for g in payload["groups"]]
    orders = [g["order"] for g in payload["groups"]]
    findings = []
    if sorted(listed) != sorted(groups):
        findings.append(f"keys {sorted(listed)} != seed groups {sorted(groups)}")
    if len(listed) != len(set(listed)):
        findings.append(f"a group listed twice: {listed}")
    if orders != list(range(1, len(groups) + 1)):
        findings.append(f"orders {orders} are not the positions 1..{len(groups)}")
    return findings


def test_every_catalogue_group_is_listed_once_in_order():
    rows = _rows()
    groups = {r["metric_group"] for r in rows}
    assert _out_of_position(export.fetch_metric_groups(), groups) == []


def test_a_group_has_exactly_one_order_in_the_seed():
    orders: dict[str, set[str]] = {}
    for r in _rows():
        orders.setdefault(r["metric_group"], set()).add(r["metric_group_order"])
    split = {g: sorted(o) for g, o in orders.items() if len(o) != 1}
    assert split == {}, f"groups with more than one order: {split}"


def test_the_seed_is_not_empty():
    """Anti-vacuous floor: 87 rows and 10 groups when written."""
    rows = _rows()
    assert len(rows) >= 60
    assert len({r["metric_group"] for r in rows}) >= 8


def _seed_with(tmp_path, edit) -> str:
    rows = _rows()
    for r in rows:
        edit(r)
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    bad = tmp_path / "metric_catalogue.csv"
    bad.write_text(out.getvalue(), encoding="utf-8")
    return str(bad)


def test_two_groups_on_one_order_is_red(tmp_path):
    def edit(r):
        if r["metric_group"] == "shooting":
            r["metric_group_order"] = "1"
    groups = {r["metric_group"] for r in _rows()}
    findings = _out_of_position(export.fetch_metric_groups(_seed_with(tmp_path, edit)), groups)
    assert findings and "positions" in findings[0]


def test_one_group_on_two_orders_is_red(tmp_path):
    def edit(r):
        if r["metric_id"] == "goals_per_match":
            r["metric_group_order"] = "11"
    groups = {r["metric_group"] for r in _rows()}
    findings = _out_of_position(export.fetch_metric_groups(_seed_with(tmp_path, edit)), groups)
    assert any("listed twice" in f for f in findings)
