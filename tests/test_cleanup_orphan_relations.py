"""Pin the safety guarantees of scripts/cleanup_orphan_relations.py (#84).

WHY THIS EXISTS
---------------
This is the only script in the repo that can delete production relations in bulk, and it decides
what to delete by SUBTRACTION: everything the manifest does not claim. That shape has one
catastrophic failure mode. If the manifest is empty, truncated, or read from the wrong path, the
expected set collapses, every relation in production looks orphaned, and a `--confirm` run drops
the warehouse. `MANIFEST_FLOOR` exists for exactly that, so it is tested by driving it, not by
reading it (#904).

The other guarantees are the ones a reviewer would otherwise have to take on trust: dry-run really
is the default, a live model can never be selected, and the dataset allowlist really is a fence
rather than a comment.

Every test runs against a fake BigQuery client. Nothing here touches the real warehouse.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_script():
    """Import `scripts/cleanup_orphan_relations.py` as a module."""
    spec = importlib.util.spec_from_file_location(
        "cleanup_orphan_relations", ROOT / "scripts" / "cleanup_orphan_relations.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cleanup = _load_script()


# --------------------------------------------------------------------------------------------
# fakes
# --------------------------------------------------------------------------------------------


class _FakeItem:
    def __init__(self, table_id: str, table_type: str) -> None:
        self.table_id = table_id
        self.table_type = table_type


class _FakeTable:
    def __init__(self, view_query: str) -> None:
        self.view_query = view_query


class _FakeClient:
    """Just enough BigQuery client to exercise the script, and it records what was asked of it."""

    def __init__(self, relations: dict[tuple[str, str], str], view_sql=None, routines=None) -> None:
        self.relations = dict(relations)
        self.view_sql = dict(view_sql or {})
        self.routines = set(routines or ())
        self.deleted: list[tuple[str, str]] = []
        self.listed: list[str] = []

    def list_routines(self, path: str):
        dataset = path.split(".")[-1]

        class _R:
            def __init__(self, rid):
                self.routine_id = rid

        return [_R(name) for ds, name in self.routines if ds == dataset]

    def list_tables(self, path: str):
        dataset = path.split(".")[-1]
        self.listed.append(dataset)
        return [
            _FakeItem(name, kind)
            for (ds, name), kind in self.relations.items()
            if ds == dataset
        ]

    def get_table(self, full_id: str):
        _, dataset, name = full_id.split(".")
        return _FakeTable(self.view_sql.get((dataset, name), ""))

    def delete_table(self, full_id: str) -> None:
        _, dataset, name = full_id.split(".")
        self.deleted.append((dataset, name))
        self.relations.pop((dataset, name), None)


def _write_manifest(tmp_path: pathlib.Path, nodes=None, sources=None, filler: int = 60):
    """A manifest with enough real nodes to clear MANIFEST_FLOOR, plus any caller-supplied ones."""
    payload: dict = {"nodes": {}, "sources": {}}
    for i in range(filler):
        payload["nodes"][f"model.fdp.filler_{i}"] = {
            "resource_type": "model",
            "name": f"filler_{i}",
            "alias": f"filler_{i}",
            "config": {"schema": "marts", "materialized": "table"},
        }
    for name, node in (nodes or {}).items():
        payload["nodes"][f"model.fdp.{name}"] = node
    for name, source in (sources or {}).items():
        payload["sources"][f"source.fdp.{name}"] = source

    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _model(name: str, schema: str | None = "staging", materialized: str = "table"):
    return {
        "resource_type": "model",
        "name": name,
        "alias": name,
        "config": {"schema": schema, "materialized": materialized},
    }


# --------------------------------------------------------------------------------------------
# the manifest floor — the failure that would drop the warehouse
# --------------------------------------------------------------------------------------------


def test_empty_manifest_aborts_instead_of_orphaning_everything(tmp_path):
    """An empty manifest must abort, not mark all of production orphaned."""
    manifest = _write_manifest(tmp_path, filler=0)
    client = _FakeClient({("staging", "stg_apif__teams"): "TABLE"})

    code = cleanup.main("all", confirm=True, manifest_path=manifest, client=client)

    assert code == 2
    assert client.deleted == [], "an empty manifest must never reach a delete"


def test_manifest_just_below_the_floor_aborts(tmp_path):
    manifest = _write_manifest(tmp_path, filler=cleanup.MANIFEST_FLOOR - 1)
    client = _FakeClient({("staging", "orphan_view"): "VIEW"})

    code = cleanup.main("all", confirm=True, manifest_path=manifest, client=client)

    assert code == 2
    assert client.deleted == []


def test_manifest_at_the_floor_is_accepted(tmp_path):
    """The floor is a floor, not a moat: exactly MANIFEST_FLOOR must pass."""
    manifest = _write_manifest(tmp_path, filler=cleanup.MANIFEST_FLOOR)
    assert len(cleanup.load_expected(manifest)) == cleanup.MANIFEST_FLOOR


def test_missing_manifest_aborts(tmp_path):
    client = _FakeClient({("staging", "orphan_view"): "VIEW"})

    code = cleanup.main("all", confirm=True, manifest_path=tmp_path / "nope.json", client=client)

    assert code == 2
    assert client.deleted == []


def test_unreadable_manifest_aborts(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(cleanup.ManifestError):
        cleanup.load_expected(path)


# --------------------------------------------------------------------------------------------
# what the manifest owns is never selectable
# --------------------------------------------------------------------------------------------


def test_a_model_in_the_manifest_is_never_an_orphan(tmp_path):
    manifest = _write_manifest(tmp_path, nodes={"stg_apif__teams": _model("stg_apif__teams")})
    expected = cleanup.load_expected(manifest)
    warehouse = {("staging", "stg_apif__teams"): "TABLE", ("staging", "stg_apif__bl1_teams"): "VIEW"}

    orphans = cleanup.find_orphans(warehouse, expected)

    assert ("staging", "stg_apif__teams") not in orphans
    assert orphans == [("staging", "stg_apif__bl1_teams")]


def test_a_node_with_no_custom_schema_maps_to_dbt_analytics(tmp_path):
    """Base models and seeds ride target.schema, which is dbt_analytics in prod."""
    manifest = _write_manifest(
        tmp_path, nodes={"base_apif__teams": _model("base_apif__teams", schema=None)}
    )
    expected = cleanup.load_expected(manifest)

    assert (cleanup.DEFAULT_DATASET, "base_apif__teams") in expected
    assert ("staging", "base_apif__teams") not in expected


def test_declared_sources_protect_raw_tables(tmp_path):
    manifest = _write_manifest(
        tmp_path,
        sources={"raw_apif_teams": {"identifier": "RAW_APIF_TEAMS", "name": "raw_apif_teams"}},
    )
    expected = cleanup.load_expected(manifest)
    warehouse = {
        ("raw", "RAW_APIF_TEAMS"): "TABLE",
        ("raw", "RAW_WC26_APIF_TEAMS"): "TABLE",
    }

    orphans = cleanup.find_orphans(warehouse, expected)

    assert orphans == [("raw", "RAW_WC26_APIF_TEAMS")]


def test_a_snapshot_is_keyed_on_target_schema_not_schema(tmp_path):
    """Snapshots declare their dataset with `target_schema`; `schema` is absent on them.

    `dbt_project.yml` sets `snapshots: +target_schema: snapshots` and says in the comment above it
    that the value is applied verbatim, never through `generate_schema_name.sql`. Reading
    `config.schema` here returns None and files every snapshot under DEFAULT_DATASET instead. That
    is inert today (no snapshots exist, and `snapshots` is not in ALLOWED_DATASETS) but a snapshot
    is an SCD2 history table, so the mapping must be right before the first one lands.
    """
    manifest = _write_manifest(
        tmp_path,
        nodes={
            "snap_thing": {
                "resource_type": "snapshot",
                "name": "snap_thing",
                "alias": "snap_thing",
                "config": {"target_schema": "snapshots", "materialized": "snapshot"},
            }
        },
    )
    expected = cleanup.load_expected(manifest)

    assert ("snapshots", "snap_thing") in expected
    assert (cleanup.DEFAULT_DATASET, "snap_thing") not in expected


def test_a_snapshot_relation_is_never_orphaned_by_a_wrong_dataset(tmp_path):
    """The consequence the mapping protects against: a live snapshot read as an orphan table."""
    manifest = _write_manifest(
        tmp_path,
        nodes={
            "snap_thing": {
                "resource_type": "snapshot",
                "name": "snap_thing",
                "alias": "snap_thing",
                "config": {"target_schema": "snapshots", "materialized": "snapshot"},
            }
        },
    )
    expected = cleanup.load_expected(manifest)

    assert cleanup.find_orphans({("snapshots", "snap_thing"): "TABLE"}, expected) == []


def test_ephemeral_models_are_not_expected_to_exist(tmp_path):
    """An ephemeral model is inlined into its consumers and builds no relation."""
    manifest = _write_manifest(
        tmp_path, nodes={"int_thing": _model("int_thing", "intermediate", "ephemeral")}
    )
    assert ("intermediate", "int_thing") not in cleanup.load_expected(manifest)


# --------------------------------------------------------------------------------------------
# the other exclusions
# --------------------------------------------------------------------------------------------


def test_dbt_tmp_relations_are_never_selected(tmp_path):
    """They are incremental-merge artifacts with a dbt-set 12-hour expiration."""
    manifest = _write_manifest(tmp_path)
    expected = cleanup.load_expected(manifest)
    warehouse = {("core", "fct_fixture_event__dbt_tmp"): "TABLE"}

    assert cleanup.find_orphans(warehouse, expected) == []


def test_raw_operational_tables_are_never_selected(tmp_path):
    manifest = _write_manifest(tmp_path)
    expected = cleanup.load_expected(manifest)
    warehouse = {(cleanup.RAW_DATASET, name): "TABLE" for name in cleanup.RAW_OPERATIONAL}

    assert cleanup.find_orphans(warehouse, expected) == []


def test_only_allowed_datasets_are_ever_listed():
    """The allowlist is a fence: raw_archive, dbt_scratch and the ci_/dev_ datasets are unreachable."""
    client = _FakeClient({})

    cleanup.list_warehouse(client)

    assert set(client.listed) == set(cleanup.ALLOWED_DATASETS)
    for forbidden in ("raw_archive", "dbt_scratch", "dev_scratch", "ci_marts", "snapshots"):
        assert forbidden not in client.listed


# --------------------------------------------------------------------------------------------
# broken vs live, and the phases
# --------------------------------------------------------------------------------------------


def _ref(dataset: str, name: str) -> str:
    return f"select * from `{cleanup.PROJECT}`.`{dataset}`.`{name}`"


def test_view_over_a_dropped_table_is_broken():
    warehouse = {("staging", "stg_apif__bl1_teams"): "VIEW"}
    queries = {("staging", "stg_apif__bl1_teams"): _ref("raw", "RAW_APIF_BL1_TEAMS")}

    assert not cleanup.resolves(("staging", "stg_apif__bl1_teams"), warehouse, queries)


def test_view_over_a_live_table_resolves():
    warehouse = {("marts", "mart_top_scorers"): "VIEW", ("marts", "mart_player_season"): "TABLE"}
    queries = {("marts", "mart_top_scorers"): _ref("marts", "mart_player_season")}

    assert cleanup.resolves(("marts", "mart_top_scorers"), warehouse, queries)


def test_brokenness_is_transitive():
    """The real case: base_apif__bl1_teams names only relations that exist, but one of them is a
    view over a dropped raw table, so a query against it errors. A one-level check calls this live
    and would put it in the phase advertised as risk-free."""
    warehouse = {
        ("dbt_analytics", "base_apif__bl1_teams"): "VIEW",
        ("staging", "stg_apif__bl1_teams"): "VIEW",
    }
    queries = {
        ("dbt_analytics", "base_apif__bl1_teams"): _ref("staging", "stg_apif__bl1_teams"),
        ("staging", "stg_apif__bl1_teams"): _ref("raw", "RAW_APIF_BL1_TEAMS"),
    }

    assert not cleanup.resolves(("dbt_analytics", "base_apif__bl1_teams"), warehouse, queries)


def test_unknown_reference_is_assumed_live_not_broken():
    """Unprovable must fall on the cautious side, never into the risk-free phase."""
    warehouse = {("marts", "mart_thing"): "VIEW"}
    queries = {("marts", "mart_thing"): _ref("some_other_dataset", "whatever")}

    assert cleanup.resolves(("marts", "mart_thing"), warehouse, queries)


def test_a_view_calling_a_udf_is_live_not_broken():
    """The real defect: `marts.mart_fixture_index` calls `dbt_analytics.url_fixture_slug`.

    A UDF call is written exactly like a table reference, and neither `bq ls` nor
    `Client.list_tables` returns routines, so the reference used to look like a missing table and
    flip `resolves()` to False. That put a view which validates and returns 1.5 MB into the phase
    advertised as risk-free. Reproduced here in the same shape: live tables plus a UDF call.
    """
    warehouse = {
        ("marts", "mart_fixture_index"): "VIEW",
        ("core", "fct_fixture"): "TABLE",
    }
    queries = {
        ("marts", "mart_fixture_index"): (
            _ref("core", "fct_fixture")
            + f", `{cleanup.PROJECT}.dbt_analytics.url_fixture_slug`(a, b, c) as fixture_slug"
        )
    }
    routines = {("dbt_analytics", "url_fixture_slug")}

    assert not cleanup.resolves(("marts", "mart_fixture_index"), warehouse, queries, set()), (
        "without the routine set this is the old, wrong answer - the test would be vacuous if "
        "this line passed"
    )
    assert cleanup.resolves(("marts", "mart_fixture_index"), warehouse, queries, routines)


def test_a_udf_reference_does_not_rescue_a_genuinely_broken_view():
    """Recognising routines must not become a blanket 'everything resolves'."""
    warehouse = {("marts", "mart_thing"): "VIEW"}
    queries = {
        ("marts", "mart_thing"): (
            _ref("raw", "GONE")
            + f", `{cleanup.PROJECT}.dbt_analytics.url_kebab`(x) as slug"
        )
    }
    routines = {("dbt_analytics", "url_kebab")}

    assert not cleanup.resolves(("marts", "mart_thing"), warehouse, queries, routines)


def test_a_routine_is_never_returned_as_an_orphan(tmp_path):
    """Routines must never enter the droppable set.

    `find_orphans()` iterates the warehouse map, so if routines were folded in there to make
    `resolves()` work, every UDF would read as an orphan relation and be selected for deletion -
    worse than the bug being fixed. They are held in a separate set for exactly this reason.
    """
    manifest = _write_manifest(tmp_path)
    expected = cleanup.load_expected(manifest)
    warehouse = {("marts", "some_orphan_view"): "VIEW"}

    orphans = cleanup.find_orphans(warehouse, expected)

    assert orphans == [("marts", "some_orphan_view")]
    assert all("url_" not in name for _, name in orphans)


def test_classify_passes_routines_through():
    """A regression guard on the wiring, not just on `resolves()` in isolation."""
    warehouse = {
        ("marts", "calls_a_udf"): "VIEW",
        ("core", "fct_fixture"): "TABLE",
    }
    queries = {
        ("marts", "calls_a_udf"): (
            _ref("core", "fct_fixture")
            + f", `{cleanup.PROJECT}.dbt_analytics.url_entity_slug`(a) as slug"
        )
    }
    orphans = [("marts", "calls_a_udf")]

    without = cleanup.classify(orphans, warehouse, queries, set())
    with_routines = cleanup.classify(
        orphans, warehouse, queries, {("dbt_analytics", "url_entity_slug")}
    )

    assert without["broken"] == orphans, "guard against a vacuous comparison"
    assert with_routines["live-views"] == orphans
    assert with_routines["broken"] == []


def test_list_routines_reads_every_allowed_dataset_and_nothing_else():
    class _R:
        def __init__(self, rid):
            self.routine_id = rid

    class _C(_FakeClient):
        def __init__(self):
            super().__init__({})
            self.routine_datasets = []

        def list_routines(self, path):
            dataset = path.split(".")[-1]
            self.routine_datasets.append(dataset)
            return [_R("url_kebab")] if dataset == "dbt_analytics" else []

    client = _C()
    found = cleanup.list_routines(client)

    assert found == {("dbt_analytics", "url_kebab")}
    assert set(client.routine_datasets) == set(cleanup.ALLOWED_DATASETS)
    for forbidden in ("raw_archive", "dbt_scratch", "ci_marts"):
        assert forbidden not in client.routine_datasets


def test_phases_are_disjoint_and_cover_every_orphan():
    warehouse = {
        ("staging", "broken_view"): "VIEW",
        ("marts", "live_view"): "VIEW",
        ("marts", "backing_table"): "TABLE",
        ("core", "orphan_table"): "TABLE",
    }
    queries = {
        ("staging", "broken_view"): _ref("raw", "GONE"),
        ("marts", "live_view"): _ref("marts", "backing_table"),
    }
    orphans = sorted(warehouse)

    phases = cleanup.classify(orphans, warehouse, queries)

    assert phases["broken"] == [("staging", "broken_view")]
    assert phases["live-views"] == [("marts", "live_view")]
    assert sorted(phases["tables"]) == [("core", "orphan_table"), ("marts", "backing_table")]

    flat = [key for group in phases.values() for key in group]
    assert sorted(flat) == orphans, "phases must cover every orphan"
    assert len(flat) == len(set(flat)), "phases must be disjoint"
    assert sorted(cleanup.select(phases, "all")) == orphans


# --------------------------------------------------------------------------------------------
# dry-run is the default, and --confirm drops only the selected phase
# --------------------------------------------------------------------------------------------


def _two_phase_fixture(tmp_path):
    manifest = _write_manifest(tmp_path)
    relations = {
        ("staging", "broken_view"): "VIEW",
        ("marts", "live_view"): "VIEW",
        ("marts", "backing_table"): "TABLE",
    }
    view_sql = {
        ("staging", "broken_view"): _ref("raw", "GONE"),
        ("marts", "live_view"): _ref("marts", "backing_table"),
    }
    return manifest, _FakeClient(relations, view_sql)


def test_dry_run_is_the_default_and_deletes_nothing(tmp_path):
    manifest, client = _two_phase_fixture(tmp_path)

    code = cleanup.main("all", confirm=False, manifest_path=manifest, client=client)

    assert code == 0
    assert client.deleted == [], "no --confirm must mean no delete_table call, ever"


def test_confirm_drops_only_the_selected_phase(tmp_path):
    manifest, client = _two_phase_fixture(tmp_path)

    code = cleanup.main("broken", confirm=True, manifest_path=manifest, client=client)

    assert code == 0
    assert client.deleted == [("staging", "broken_view")]
    assert ("marts", "live_view") in client.relations, "another phase must be untouched"
    assert ("marts", "backing_table") in client.relations


def test_confirm_all_drops_every_orphan(tmp_path):
    manifest, client = _two_phase_fixture(tmp_path)

    code = cleanup.main("all", confirm=True, manifest_path=manifest, client=client)

    assert code == 0
    assert sorted(client.deleted) == [
        ("marts", "backing_table"),
        ("marts", "live_view"),
        ("staging", "broken_view"),
    ]


def test_main_does_not_drop_a_udf_calling_view_in_phase_broken(tmp_path):
    """END-TO-END through main(), which is the only thing that pins the WIRING.

    `classify()` and `list_routines()` are each tested in isolation above, and both pass even if
    `main()` never fetches routines or never threads them into `classify()`. Measured: reverting
    exactly those two lines in `main()` leaves every other test in this file GREEN. That is how
    the production defect reached the operator in the first place — the misclassification happened
    in the script people run, not in a unit under test.

    So this asserts the consequence that actually matters: `--phase broken --confirm` must not
    delete a view that only looked broken because it calls a UDF, while still deleting one that is
    genuinely broken.
    """
    manifest = _write_manifest(
        tmp_path, nodes={"fct_fixture": _model("fct_fixture", schema="core")}
    )
    relations = {
        ("core", "fct_fixture"): "TABLE",             # live, owned by the manifest
        ("marts", "mart_fixture_index"): "VIEW",      # orphan, but resolves via a UDF
        ("staging", "really_broken"): "VIEW",         # orphan, genuinely broken
    }
    view_sql = {
        ("marts", "mart_fixture_index"): (
            _ref("core", "fct_fixture")
            + f", `{cleanup.PROJECT}.dbt_analytics.url_fixture_slug`(a, b) as fixture_slug"
        ),
        ("staging", "really_broken"): _ref("raw", "RAW_APIF_BL1_TEAMS"),
    }
    client = _FakeClient(
        relations, view_sql, routines={("dbt_analytics", "url_fixture_slug")}
    )

    code = cleanup.main("broken", confirm=True, manifest_path=manifest, client=client)

    assert code == 0
    assert client.deleted == [("staging", "really_broken")], (
        "phase broken must drop the genuinely broken view and nothing else"
    )
    assert ("marts", "mart_fixture_index") in client.relations, (
        "a view that resolves through a UDF must survive phase broken"
    )
    assert ("core", "fct_fixture") in client.relations


def test_nothing_to_do_when_the_warehouse_matches_the_manifest(tmp_path):
    manifest = _write_manifest(tmp_path, nodes={"stg_apif__teams": _model("stg_apif__teams")})
    expected = cleanup.load_expected(manifest)
    client = _FakeClient({key: "TABLE" for key in expected})

    code = cleanup.main("all", confirm=True, manifest_path=manifest, client=client)

    assert code == 0
    assert client.deleted == []
