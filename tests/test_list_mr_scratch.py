"""scripts/list_mr_scratch.py — which merge-request scratch datasets nothing reads any more."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("list_mr_scratch", REPO_ROOT / "scripts" / "list_mr_scratch.py")
list_mr_scratch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(list_mr_scratch)


def _never(names):
    raise AssertionError(f"creation time read for {names}")


def test_names_parse_into_merge_request_and_target_commit():
    assert list_mr_scratch.parse("ci_mr445_1a2b3c4d") == (445, "1a2b3c4d")
    assert list_mr_scratch.parse("ci_mr445_1a2b3c4d_marts") == (445, "1a2b3c4d")
    assert list_mr_scratch.parse("ci_mr445_1a2b3c4d_dbt_test__audit") == (445, "1a2b3c4d")
    assert list_mr_scratch.parse("ci_mr114") == (114, None)
    assert list_mr_scratch.parse("ci_mr114_marts") == (114, None)


def test_other_datasets_are_never_scratch():
    for name in ("marts", "dbt_analytics", "raw", "dev_scratch", "dev_marts", "ci_mrshared", "ci_marts"):
        assert list_mr_scratch.parse(name) is None


def test_prod_and_dev_datasets_are_never_listed():
    datasets = ["marts", "core", "dbt_analytics", "raw", "dev_scratch", "ci_mrshared"]
    assert list_mr_scratch.classify(datasets, set(), _never) == []


def test_every_dataset_of_a_closed_merge_request_is_listed():
    datasets = ["ci_mr10_aaaaaaaa", "ci_mr10_aaaaaaaa_marts", "ci_mr10_bbbbbbbb_core"]
    listed = list_mr_scratch.classify(datasets, set(), _never)
    assert [n for n, _ in listed] == sorted(datasets)
    assert all("not open" in reason for _, reason in listed)


def test_an_open_merge_request_keeps_its_newest_set_only():
    datasets = [
        "ci_mr20_aaaaaaaa", "ci_mr20_aaaaaaaa_marts",
        "ci_mr20_bbbbbbbb", "ci_mr20_bbbbbbbb_marts",
    ]
    created = {
        "aaaaaaaa": datetime(2026, 11, 14, tzinfo=timezone.utc),
        "bbbbbbbb": datetime(2026, 11, 15, tzinfo=timezone.utc),
    }
    listed = list_mr_scratch.classify(datasets, {20}, lambda names: created[names[0].split("_")[2]])
    assert [n for n, _ in listed] == ["ci_mr20_aaaaaaaa", "ci_mr20_aaaaaaaa_marts"]
    assert all("superseded by its bbbbbbbb set" in reason for _, reason in listed)


def test_an_open_merge_request_with_one_set_keeps_it_without_reading_metadata():
    assert list_mr_scratch.classify(["ci_mr30_aaaaaaaa", "ci_mr30_aaaaaaaa_core"], {30}, _never) == []


def test_a_name_without_a_target_commit_is_listed_even_when_its_merge_request_is_open():
    listed = list_mr_scratch.classify(["ci_mr40", "ci_mr40_marts", "ci_mr40_cccccccc"], {40}, _never)
    assert [n for n, _ in listed] == ["ci_mr40", "ci_mr40_marts"]


def test_the_script_has_no_delete_call():
    source = (REPO_ROOT / "scripts" / "list_mr_scratch.py").read_text(encoding="utf-8")
    for call in ("delete_dataset", "delete_table", "bq rm", "DROP "):
        assert call not in source
