"""The crest phase: what it fetches, what it stores, and what it never does."""

from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone

import pytest
from PIL import Image

from ingestion.api_football.loads import crests
from ingestion.api_football.loads.context import PipelineContext

NOW = datetime(2026, 11, 22, 4, 0, tzinfo=timezone.utc)
ENSURED: list[str] = []


def png(width: int = 150, height: int = 150, colour=(200, 30, 30, 255)) -> bytes:
    out = io.BytesIO()
    Image.new("RGBA", (width, height), colour).save(out, format="PNG")
    return out.getvalue()


class FakeStore:
    def __init__(self, exists: bool = True):
        self._exists = exists
        self.objects: dict[str, bytes] = {}

    def exists(self) -> bool:
        return self._exists

    def put(self, object_name: str, data: bytes) -> None:
        self.objects[object_name] = data


class Provider:
    """The image host and the account endpoint, with a counter that images may or may not move."""

    def __init__(self, bodies: dict[str, bytes], statuses: dict[str, int] | None = None, images_count: bool = False):
        self.bodies = bodies
        self.statuses = statuses or {}
        self.images_count = images_count
        self.requests_today = 100
        self.fetched: list[str] = []

    def fetch(self, url: str) -> crests.Fetched:
        self.fetched.append(url)
        if self.images_count:
            self.requests_today += 1
        status = self.statuses.get(url, 200)
        return crests.Fetched(status, self.bodies.get(url, b"") if status == 200 else b"")

    def status_numbers(self, headers: dict) -> tuple[int, int]:
        return self.requests_today, 7500


@pytest.fixture
def written(monkeypatch):
    rows: list[dict] = []
    monkeypatch.setattr(crests, "ensure_raw_table_partitioned", lambda client, table: ENSURED.append(table))
    monkeypatch.setattr(crests, "load_json_to_bq", lambda client, table, payload, **kw: rows.append({"table": table, **kw, "payload": payload}))
    return rows


def run(ctx_state, store, provider, discovered, monkeypatch, now=NOW):
    monkeypatch.setattr(crests, "read_latest_payload_json", lambda client, table: ctx_state)
    ctx = PipelineContext(client=object(), headers={})
    return crests.run(
        ctx, store=store, discovered=discovered, fetch=provider.fetch,
        status_numbers=provider.status_numbers, now=now, sleep=lambda s: None,
    )


URL_1 = "https://media.api-sports.io/football/teams/1.png"
URL_2 = "https://media.api-sports.io/football/teams/2.png"
LEAGUE = "https://media.api-sports.io/football/leagues/9.png"


def test_shrink_keeps_aspect_transparency_and_both_sizes():
    wide = png(300, 150, (10, 20, 30, 0))
    for size in crests.SIZES:
        image = Image.open(io.BytesIO(crests.shrink(wide, size)))
        assert image.format == "WEBP"
        assert image.size == (size, size // 2)
        assert image.convert("RGBA").getpixel((0, 0))[3] == 0


def test_object_names_carry_kind_id_and_size():
    assert crests.object_name("teams", 689, 104) == "teams/689-104.webp"
    assert crests.object_name("leagues", 9, 48) == "leagues/9-48.webp"


def test_plan_takes_new_ids_first_then_the_longest_unchecked_past_the_window():
    found = {("teams", 1): URL_1, ("teams", 2): URL_2, ("leagues", 9): LEAGUE, ("teams", 3): "u3"}
    old = (NOW - timedelta(days=30)).isoformat()
    older = (NOW - timedelta(days=60)).isoformat()
    fresh = (NOW - timedelta(days=1)).isoformat()
    state = {("teams", 1): {"checked_at": old}, ("teams", 2): {"checked_at": fresh}, ("teams", 3): {"checked_at": older}}
    assert crests.plan(found, state, NOW, 10) == [("leagues", 9, LEAGUE), ("teams", 3, "u3"), ("teams", 1, URL_1)]
    assert crests.plan(found, state, NOW, 1) == [("leagues", 9, LEAGUE)]
    assert crests.plan(found, state, NOW, 0) == []


def test_a_missing_bucket_writes_nothing_and_fetches_nothing_but_the_state_table_exists(monkeypatch, written):
    ENSURED.clear()
    provider = Provider({URL_1: png()})
    summary = run(None, FakeStore(exists=False), provider, {("teams", 1): URL_1}, monkeypatch)
    assert summary["skipped"] == "the crest bucket does not exist"
    assert provider.fetched == [] and written == []
    assert ENSURED == ["RAW_APIF_CREST_OBJECTS"]


def test_the_first_fill_stores_both_sizes_and_records_the_preflight(monkeypatch, written):
    bodies = {f"https://x/{i}.png": png() for i in range(12)} | {LEAGUE: png()}
    provider = Provider(bodies)
    store = FakeStore()
    found = {("teams", i): f"https://x/{i}.png" for i in range(12)} | {("leagues", 9): LEAGUE}
    summary = run(None, store, provider, found, monkeypatch)
    assert summary["stored"] == 13
    assert {"leagues/9-104.webp", "leagues/9-48.webp", "teams/0-104.webp", "teams/11-48.webp"} <= set(store.objects)
    assert len(store.objects) == 26
    (row,) = written
    assert row["table"] == "RAW_APIF_CREST_OBJECTS" and row["append"] is True and row["as_json_payload"] is True
    assert row["payload"]["preflight"]["images_count_quota"] is False
    assert len(row["payload"]["objects"]) == 13 and all(o["status"] == "ok" for o in row["payload"]["objects"])


def test_the_preflight_sees_images_count_against_the_quota_and_caps_the_run(monkeypatch, written):
    bodies = {f"https://x/{i}.png": png() for i in range(40)}
    provider = Provider(bodies, images_count=True)
    provider.requests_today = 7500 - crests.API_RESERVE - 5 - crests.PREFLIGHT_SAMPLE
    found = {("teams", i): f"https://x/{i}.png" for i in range(40)}
    summary = run(None, FakeStore(), provider, found, monkeypatch)
    (row,) = written
    assert row["payload"]["preflight"]["images_count_quota"] is True
    assert summary["stored"] == crests.PREFLIGHT_SAMPLE + 5


def test_the_preflight_runs_once_and_later_runs_keep_its_result(monkeypatch, written):
    state = {"version": 1, "preflight": {"images_count_quota": False}, "objects": []}
    provider = Provider({URL_1: png()})
    calls = []
    provider.status_numbers = lambda headers: calls.append(1) or (0, 7500)
    run(state, FakeStore(), provider, {("teams", 1): URL_1}, monkeypatch)
    assert calls == []


def test_an_unchanged_image_updates_its_check_and_stores_nothing(monkeypatch, written):
    body = png()
    first = Provider({URL_1: body})
    store = FakeStore()
    run(None, store, first, {("teams", 1): URL_1}, monkeypatch)
    state = written[0]["payload"]
    written.clear()
    store.objects.clear()
    later = NOW + timedelta(days=8)
    summary = run(state, store, Provider({URL_1: body}), {("teams", 1): URL_1}, monkeypatch, now=later)
    assert summary["unchanged"] == 1 and summary["stored"] == 0 and store.objects == {}
    assert written[0]["payload"]["objects"][0]["checked_at"] == later.isoformat()


def test_a_changed_badge_is_stored_again(monkeypatch, written):
    store = FakeStore()
    run(None, store, Provider({URL_1: png()}), {("teams", 1): URL_1}, monkeypatch)
    state = written[0]["payload"]
    written.clear()
    new_badge = png(colour=(0, 0, 255, 255))
    summary = run(state, store, Provider({URL_1: new_badge}), {("teams", 1): URL_1}, monkeypatch, now=NOW + timedelta(days=8))
    assert summary["stored"] == 1
    assert written[0]["payload"]["objects"][0]["fetched_at"] == (NOW + timedelta(days=8)).isoformat()


def test_nothing_due_writes_no_row(monkeypatch, written):
    state = {
        "version": 1, "preflight": {"images_count_quota": False},
        "objects": [{"kind": "teams", "id": 1, "status": "ok", "sha256": "x", "checked_at": NOW.isoformat()}],
    }
    provider = Provider({})
    summary = run(state, FakeStore(), provider, {("teams", 1): URL_1}, monkeypatch)
    assert provider.fetched == [] and written == [] and summary["stored"] == 0


def test_a_404_is_recorded_as_missing_and_no_object_is_written(monkeypatch, written):
    store = FakeStore()
    summary = run({"preflight": {"images_count_quota": False}, "objects": []}, store, Provider({}, {URL_1: 404}), {("teams", 1): URL_1}, monkeypatch)
    assert summary["missing"] == 1 and store.objects == {}
    assert written[0]["payload"]["objects"][0]["status"] == "missing"


def test_a_429_or_403_stops_the_phase_and_keeps_what_was_stored(monkeypatch, written):
    state = {"preflight": {"images_count_quota": False}, "objects": []}
    provider = Provider({URL_1: png(), URL_2: png(), LEAGUE: png()}, {URL_2: 429})
    store = FakeStore()
    summary = run(state, store, provider, {("teams", 1): URL_1, ("teams", 2): URL_2, ("leagues", 9): LEAGUE}, monkeypatch)
    assert provider.fetched == [LEAGUE, URL_1, URL_2]
    assert summary["stopped"] == f"429 on {URL_2}"
    assert summary["stored"] == 2
    assert [(o["kind"], o["id"]) for o in written[0]["payload"]["objects"]] == [("leagues", 9), ("teams", 1)]


def test_a_server_error_leaves_the_state_alone(monkeypatch, written):
    state = {"preflight": {"images_count_quota": False}, "objects": []}
    summary = run(state, FakeStore(), Provider({}, {URL_1: 503}), {("teams", 1): URL_1}, monkeypatch)
    assert summary["failed"] == 1 and written == []


def test_a_stop_in_the_preflight_sample_leaves_the_preflight_unmeasured(monkeypatch, written):
    provider = Provider({URL_1: png()}, {URL_1: 403})
    summary = run(None, FakeStore(), provider, {("teams", 1): URL_1}, monkeypatch)
    assert summary["stopped"] == f"403 on {URL_1}"
    assert written == []


def test_an_unreadable_account_counter_means_no_fetch_and_no_recorded_preflight(monkeypatch, written):
    provider = Provider({URL_1: png()})
    provider.status_numbers = lambda headers: (0, 0)
    summary = run(None, FakeStore(), provider, {("teams", 1): URL_1}, monkeypatch)
    assert provider.fetched == [] and written == []
    assert "unreadable" in summary["skipped"]


def test_a_sample_the_host_did_not_answer_leaves_the_preflight_unmeasured_and_the_fill_for_later(monkeypatch, written):
    bodies = {f"https://x/{i}.png": png() for i in range(30)}
    statuses = {url: 503 for url in bodies}
    provider = Provider(bodies, statuses)
    found = {("teams", i): f"https://x/{i}.png" for i in range(30)}
    summary = run(None, FakeStore(), provider, found, monkeypatch)
    assert summary["failed"] == crests.PREFLIGHT_SAMPLE and summary["stored"] == 0
    assert "not measured yet" in summary["skipped"]
    assert len(provider.fetched) == crests.PREFLIGHT_SAMPLE and written == []


def test_the_phase_skips_itself_when_the_daily_api_quota_is_used_up(monkeypatch, written):
    monkeypatch.setattr(crests.errors_quota, "_http_quota_exhausted", True)
    provider = Provider({URL_1: png()})
    summary = run(None, FakeStore(), provider, {("teams", 1): URL_1}, monkeypatch)
    assert "used up" in summary["skipped"] and provider.fetched == [] and written == []


def test_one_bad_image_costs_nothing_else_and_the_others_are_kept(monkeypatch, written):
    state = {"preflight": {"images_count_quota": False}, "objects": []}
    provider = Provider({URL_1: b"<html>not an image</html>", URL_2: png(), LEAGUE: png()})
    store = FakeStore()
    summary = run(state, store, provider, {("teams", 1): URL_1, ("teams", 2): URL_2, ("leagues", 9): LEAGUE}, monkeypatch)
    assert summary["failed"] == 1 and summary["stored"] == 2
    assert [(o["kind"], o["id"]) for o in written[0]["payload"]["objects"]] == [("leagues", 9), ("teams", 2)]


def test_a_raising_fetch_is_a_failure_and_the_run_goes_on(monkeypatch, written):
    state = {"preflight": {"images_count_quota": False}, "objects": []}
    provider = Provider({URL_2: png()})
    real = provider.fetch

    def fetch(url):
        if url == URL_1:
            raise TimeoutError("read timed out")
        return real(url)

    provider.fetch = fetch
    summary = run(state, FakeStore(), provider, {("teams", 1): URL_1, ("teams", 2): URL_2}, monkeypatch)
    assert summary["failed"] == 1 and summary["stored"] == 1


def test_a_store_error_is_a_failure_and_never_loses_the_state_of_what_was_stored(monkeypatch, written):
    state = {"preflight": {"images_count_quota": False}, "objects": []}

    class FlakyStore(FakeStore):
        def put(self, object_name, data):
            if object_name.startswith("teams/2-"):
                raise OSError("gcs unavailable")
            super().put(object_name, data)

    provider = Provider({URL_1: png(), URL_2: png()})
    summary = run(state, FlakyStore(), provider, {("teams", 1): URL_1, ("teams", 2): URL_2}, monkeypatch)
    assert summary["failed"] == 1 and summary["stored"] == 1
    assert [(o["kind"], o["id"]) for o in written[0]["payload"]["objects"]] == [("teams", 1)]


def test_a_failed_write_of_a_changed_badge_keeps_the_old_entry_so_the_next_run_checks_again(monkeypatch, written):
    store = FakeStore()
    run(None, store, Provider({URL_1: png()}), {("teams", 1): URL_1}, monkeypatch)
    first = written[0]["payload"]
    written.clear()

    class FailingStore(FakeStore):
        def put(self, object_name, data):
            raise OSError("gcs unavailable")

    later = NOW + timedelta(days=8)
    summary = run(first, FailingStore(), Provider({URL_1: png(colour=(0, 0, 255, 255))}), {("teams", 1): URL_1}, monkeypatch, now=later)
    assert summary["failed"] == 1 and written == []
    assert first["objects"][0]["checked_at"] == NOW.isoformat()


def test_an_unreadable_counter_after_images_count_skips_the_night_with_a_reason(monkeypatch, written):
    state = {"preflight": {"images_count_quota": True}, "objects": []}
    provider = Provider({URL_1: png()})
    provider.status_numbers = lambda headers: (0, 0)
    summary = run(state, FakeStore(), provider, {("teams", 1): URL_1}, monkeypatch)
    assert "unreadable" in summary["skipped"] and provider.fetched == []


def test_an_exception_outside_the_loop_still_writes_the_state_gathered_so_far(monkeypatch, written):
    state = {"preflight": {"images_count_quota": False}, "objects": []}
    provider = Provider({URL_1: png(), URL_2: png()})
    calls = []

    def sleep(seconds):
        calls.append(seconds)
        if len(calls) == 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(crests, "read_latest_payload_json", lambda client, table: state)
    ctx = PipelineContext(client=object(), headers={})
    with pytest.raises(KeyboardInterrupt):
        crests.run(ctx, store=FakeStore(), discovered={("teams", 1): URL_1, ("teams", 2): URL_2},
                   fetch=provider.fetch, status_numbers=provider.status_numbers, now=NOW, sleep=sleep)
    assert [(o["kind"], o["id"]) for o in written[0]["payload"]["objects"]] == [("teams", 1)]


def test_a_host_that_fails_every_request_stops_the_phase_after_a_run_of_failures(monkeypatch, written):
    state = {"preflight": {"images_count_quota": False}, "objects": []}
    urls = {f"https://x/{i}.png": 503 for i in range(60)}
    provider = Provider({}, urls)
    found = {("teams", i): url for i, url in enumerate(urls)}
    summary = run(state, FakeStore(), provider, found, monkeypatch)
    assert summary["stopped"] == f"{crests.MAX_FAILURES_IN_A_ROW} failures in a row"
    assert len(provider.fetched) == crests.MAX_FAILURES_IN_A_ROW


def test_the_bucket_class_turns_a_missing_bucket_into_false_and_sets_the_cache_header():
    from google.api_core.exceptions import NotFound

    class Blob:
        def __init__(self):
            self.cache_control = None
            self.uploaded = None

        def upload_from_string(self, data, content_type):
            self.uploaded = (data, content_type)

    blobs = {}

    class Bucket:
        def blob(self, name):
            return blobs.setdefault(name, Blob())

    class Client:
        def __init__(self, missing):
            self.missing = missing

        def bucket(self, name):
            return Bucket()

        def list_blobs(self, bucket, max_results=None):
            if self.missing:
                raise NotFound("no such bucket")
            return iter([])

    assert crests.GcsStore("b", client=Client(missing=True)).exists() is False
    present = crests.GcsStore("b", client=Client(missing=False))
    assert present.exists() is True
    present.put("teams/1-48.webp", b"data")
    blob = blobs["teams/1-48.webp"]
    assert blob.cache_control == "public, max-age=604800"
    assert blob.uploaded == (b"data", "image/webp")


def test_the_discovery_query_reads_the_latest_row_per_league_of_both_raw_tables():
    seen: list[str] = []

    class Result:
        def __init__(self, rows):
            self.rows = rows

        def result(self):
            return self.rows

    class Client:
        def query(self, sql):
            seen.append(sql)
            if "RAW_APIF_TEAMS" in sql:
                return Result([{"provider_id": "1", "source_url": URL_1}, {"provider_id": "x", "source_url": "bad"}])
            return Result([{"provider_id": "9", "source_url": LEAGUE}])

    found = crests.discover(Client())
    assert found == {("teams", 1): URL_1, ("leagues", 9): LEAGUE}
    assert all("partition by league_code order by ingested_at desc" in sql for sql in seen)
    assert "$.team.logo" in seen[0] and "$.league.logo" in seen[1]


def test_only_the_two_dimensions_read_the_models_that_carry_the_provider_logo_address():
    """A mart that read a base or staging team or league model would publish the provider's host."""
    import re
    from pathlib import Path

    models = Path(__file__).resolve().parents[1] / "dbt_project" / "models"
    carriers = re.compile(r"ref\(\s*'(base_apif__(teams|teams_global|leagues|league_entity)|stg_apif__(teams|leagues))'\s*\)")
    readers = {
        path.name
        for folder in ("3_core", "4_intermediate", "5_marts")
        for path in (models / folder).rglob("*.sql")
        if carriers.search(path.read_text(encoding="utf-8"))
    }
    assert readers <= {"dim_team.sql", "dim_league.sql", "dim_team_competition_season_mapping.sql"}, readers


def test_the_two_dimensions_publish_the_crest_path_only_where_an_object_is_stored():
    from pathlib import Path

    models = Path(__file__).resolve().parents[1] / "dbt_project" / "models" / "3_core"
    team = (models / "dim_team.sql").read_text(encoding="utf-8")
    league = (models / "dim_league.sql").read_text(encoding="utf-8")
    assert "'/crests/teams/', cast(teams.team_api_id as string), '-104.webp'" in team
    assert "'/crests/leagues/', cast(leagues.league_api_id as string), '-104.webp'" in league
    assert "when crests.provider_id is not null" in team and "when crests.provider_id is not null" in league


def test_the_phase_runs_after_the_player_loads_and_never_fails_the_ingest():
    from pathlib import Path

    text = (Path(crests.__file__).parents[1] / "orchestrator.py").read_text(encoding="utf-8")
    assert text.index("load_player_teams_global(ctx, universe=shared_universe)") < text.index("crests.run(ctx)")
    assert "phase failed, ingest continues" in text
