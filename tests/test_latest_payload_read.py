"""`read_latest_payload_json` must prune partitions, asserted on the SQL a fake client records.

Neither `ORDER BY ... LIMIT 1` nor a subquery predicate prunes, so the payload read needs an
equality predicate on a literal timestamp.
"""

from __future__ import annotations

import json

import pytest

from ingestion.api_football.bigquery import read_latest_payload_json


class _Field:
    def __init__(self, name: str, field_type: str = "STRING"):
        self.name = name
        self.field_type = field_type


class _Table:
    def __init__(self, fields):
        self.schema = fields


class _Result:
    """Stands in for a RowIterator: iterable, and convertible to arrow like the real one."""

    def __init__(self, rows):
        self._rows = rows

    def __iter__(self):
        return iter(self._rows)

    def to_arrow(self, create_bqstorage_client=False):  # noqa: ARG002 - signature parity
        payloads = [r[0] for r in self._rows]

        class _Col:
            def __init__(self, values):
                self._values = values

            def __getitem__(self, i):
                class _Cell:
                    def __init__(self, v):
                        self._v = v

                    def as_py(self):
                        return self._v

                return _Cell(self._values[i])

        class _Arrow:
            num_rows = len(payloads)

            def column(self, _name):
                return _Col(payloads)

        return _Arrow()


class _FakeClient:
    """Records every query issued and replays canned results in order."""

    def __init__(self, table, results):
        self._table = table
        self._results = list(results)
        self.queries: list[str] = []
        self.params: list[list] = []

    def get_table(self, _table_id):
        return self._table

    def query(self, sql, job_config=None):
        self.queries.append(" ".join(sql.split()))
        self.params.append(list(getattr(job_config, "query_parameters", []) or []))
        result = self._results.pop(0)

        class _Job:
            def result(self_inner):
                return result

        return _Job()


PAYLOAD = {"response": [{"id": 1}]}


def test_reads_in_two_steps_and_prunes_on_the_partition_column():
    """A wrong query shape would still return the right value, so the SQL itself is asserted."""
    table = _Table([_Field("payload"), _Field("league_code"),
                    _Field("ingested_at", "TIMESTAMP")])
    client = _FakeClient(table, [_Result([("2026-08-02T07:24:45",)]),
                                 _Result([(json.dumps(PAYLOAD),)])])

    assert read_latest_payload_json(client, "RAW_APIF_TRANSFERS", "BL1") == PAYLOAD

    assert len(client.queries) == 2, "expected a timestamp lookup then a pruned payload read"
    lookup, payload_q = client.queries

    assert "MAX(ingested_at)" in lookup
    assert "payload" not in lookup, "the cheap lookup must not touch the payload column"

    assert "ingested_at = @ts" in payload_q, (
        "the payload read must pin the partition column to a literal parameter — this is the "
        "predicate that prunes"
    )
    assert "ORDER BY" not in payload_q.upper(), (
        "ORDER BY cannot prune partitions; that is the defect #890 removed"
    )
    assert "SELECT MAX" not in payload_q.upper(), (
        "a subquery predicate does not prune either — measured at the same 6.634 GiB"
    )


def test_league_code_is_a_parameter_not_interpolated():
    table = _Table([_Field("payload"), _Field("league_code"),
                    _Field("ingested_at", "TIMESTAMP")])
    client = _FakeClient(table, [_Result([("2026-08-02T07:24:45",)]),
                                 _Result([(json.dumps(PAYLOAD),)])])

    read_latest_payload_json(client, "RAW_APIF_TRANSFERS", "BL1")

    assert all("'BL1'" not in q for q in client.queries)
    assert any(p.name == "league_code" and p.value == "BL1" for p in client.params[0])


def test_timestamp_parameter_type_follows_the_column_type():
    """A DATETIME column needs a DATETIME parameter; a mismatch is a query error."""
    table = _Table([_Field("payload"), _Field("league_code"),
                    _Field("ingested_datetime", "DATETIME")])
    client = _FakeClient(table, [_Result([("2026-08-02T07:24:45",)]),
                                 _Result([(json.dumps(PAYLOAD),)])])

    read_latest_payload_json(client, "RAW_APIF_SOMETHING", "BL1")

    assert "MAX(ingested_datetime)" in client.queries[0]
    ts_param = next(p for p in client.params[1] if p.name == "ts")
    assert ts_param.type_ == "DATETIME"


@pytest.mark.parametrize(
    "lookup_result",
    [
        pytest.param(_Result([(None,)]), id="one_null_row_what_bigquery_really_returns"),
        pytest.param(_Result([]), id="zero_rows_defensive"),
    ],
)
def test_no_rows_for_the_league_returns_none_without_a_second_query(lookup_result):
    """`MAX()` over no matching rows returns one NULL row; `_scalar` must also handle zero rows."""
    table = _Table([_Field("payload"), _Field("league_code"),
                    _Field("ingested_at", "TIMESTAMP")])
    client = _FakeClient(table, [lookup_result])

    assert read_latest_payload_json(client, "RAW_APIF_TRANSFERS", "ZZZ") is None
    assert len(client.queries) == 1, "the payload query must be skipped when there is no timestamp"


def test_table_without_an_ingest_time_column_keeps_the_single_query_path():
    """With no ingest-time column there is nothing to prune on."""
    table = _Table([_Field("payload"), _Field("league_code")])
    client = _FakeClient(table, [_Result([(json.dumps(PAYLOAD),)])])

    assert read_latest_payload_json(client, "RAW_APIF_ODD", "BL1") == PAYLOAD
    assert len(client.queries) == 1
    assert "MAX(" not in client.queries[0]


@pytest.mark.parametrize("value", [PAYLOAD, json.dumps(PAYLOAD)])
def test_payload_is_returned_as_a_dict_whether_stored_as_json_or_string(value):
    table = _Table([_Field("payload"), _Field("league_code"),
                    _Field("ingested_at", "TIMESTAMP")])
    client = _FakeClient(table, [_Result([("2026-08-02T07:24:45",)]), _Result([(value,)])])

    assert read_latest_payload_json(client, "RAW_APIF_TRANSFERS", "BL1") == PAYLOAD
