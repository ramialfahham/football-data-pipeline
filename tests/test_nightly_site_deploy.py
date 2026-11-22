"""The guards of the nightly site deploy: the warehouse nightly, the count floor, the folder swap."""

from __future__ import annotations

import json
import math
import os
import sys
import urllib.error
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import nightly_site_deploy as nsd  # noqa: E402

TODAY = datetime(2026, 11, 22, 6, 30, tzinfo=timezone.utc)


def execution(created="2026-11-22T04:00:03.123456789Z", completed="2026-11-22T05:30:00Z", state="CONDITION_SUCCEEDED"):
    out = {"name": "projects/p/locations/r/jobs/fdp-nightly/executions/fdp-nightly-abc", "createTime": created}
    if completed:
        out["completionTime"] = completed
        out["conditions"] = [{"type": "Completed", "state": state}]
    return out


def test_a_nightly_that_succeeded_today_passes():
    assert nsd.nightly_state([execution()], TODAY)[0] == "ok"


def test_no_execution_refuses():
    assert nsd.nightly_state([], TODAY)[0] == "refuse"


def test_a_nightly_of_yesterday_refuses():
    state, why = nsd.nightly_state([execution(created="2026-11-21T04:00:00Z")], TODAY)
    assert state == "refuse" and "not today" in why


def test_a_failed_nightly_refuses():
    assert nsd.nightly_state([execution(state="CONDITION_FAILED")], TODAY)[0] == "refuse"


def test_a_running_nightly_waits():
    assert nsd.nightly_state([execution(completed=None)], TODAY)[0] == "wait"


def test_counts_without_conditions_use_the_task_counts():
    ok = dict(execution(), succeededCount=1)
    ok.pop("conditions", None)
    ok["completionTime"] = "2026-11-22T05:30:00Z"
    assert nsd.nightly_state([ok], TODAY)[0] == "ok"
    bad = dict(ok, failedCount=1)
    assert nsd.nightly_state([bad], TODAY)[0] == "refuse"


class FakeSession:
    def __init__(self, bodies):
        self.bodies = list(bodies)
        self.calls = 0

    def get(self, url, params=None, timeout=None):
        self.calls += 1
        body = self.bodies.pop(0)

        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return body

        return Response()


def test_wait_returns_once_the_nightly_has_finished():
    session = FakeSession([{"executions": [execution(completed=None)]}, {"executions": [execution()]}])
    slept = []
    nsd.wait_for_nightly(session, now=lambda: TODAY, sleep=slept.append)
    assert session.calls == 2 and slept == [nsd.POLL_SECONDS]


def test_wait_gives_up_after_the_limit_and_refuses():
    session = FakeSession([{"executions": [execution(completed=None)]}] * 100)
    with pytest.raises(SystemExit, match="still running"):
        nsd.wait_for_nightly(session, now=lambda: TODAY, sleep=lambda s: None)
    assert session.calls == nsd.MAX_WAIT_SECONDS // nsd.POLL_SECONDS + 1


def test_wait_refuses_at_once_on_a_failed_nightly():
    session = FakeSession([{"executions": [execution(state="CONDITION_FAILED")]}])
    with pytest.raises(SystemExit, match="did not succeed"):
        nsd.wait_for_nightly(session, now=lambda: TODAY, sleep=lambda s: None)
    assert session.calls == 1


LIVE = {"counts": {"team": 3346, "fixture": 64952, "competition": 254, "player": 18526, "player_peers": 547, "match_day": 69}}


def test_the_first_deploy_has_nothing_to_fall_below():
    assert nsd.count_regressions(None, {"counts": {}}) == []


def test_counts_at_the_floor_pass_and_below_it_fail():
    at_floor = {"counts": {**LIVE["counts"], "player": math.ceil(18526 * 0.9)}}
    assert nsd.count_regressions(LIVE, at_floor) == []
    below = {"counts": {**LIVE["counts"], "player": math.ceil(18526 * 0.9) - 1}}
    issues = nsd.count_regressions(LIVE, below)
    assert len(issues) == 1 and issues[0].startswith("player:")


def test_a_missing_key_is_a_fall():
    now = {"counts": {k: v for k, v in LIVE["counts"].items() if k != "team"}}
    assert [i.split(":")[0] for i in nsd.count_regressions(LIVE, now)] == ["team"]


def test_growth_and_uncompared_keys_pass():
    now = {"counts": {**{k: v * 2 for k, v in LIVE["counts"].items() if k != "match_day"}, "match_day": 1}}
    assert nsd.count_regressions(LIVE, now) == []


def test_a_small_baseline_is_ignored():
    assert nsd.count_regressions({"counts": {"team": 19}}, {"counts": {"team": 0}}) == []


def _opener(error=None, body=b"{}"):
    def opener(url, timeout=None):
        if error is not None:
            raise error
        return _Ctx(body)

    return opener


class _Ctx:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self.body


def _http(code):
    return urllib.error.HTTPError("u", code, "x", {}, None)


def test_a_404_is_the_first_deploy():
    assert nsd.fetch_live_manifest("u", opener=_opener(error=_http(404))) is None


def test_any_other_error_refuses_rather_than_pass_as_a_first_deploy():
    with pytest.raises(urllib.error.HTTPError):
        nsd.fetch_live_manifest("u", opener=_opener(error=_http(503)))
    with pytest.raises(urllib.error.URLError):
        nsd.fetch_live_manifest("u", opener=_opener(error=urllib.error.URLError("down")))


def test_a_served_manifest_is_read():
    assert nsd.fetch_live_manifest("u", opener=_opener(body=json.dumps(LIVE).encode())) == LIVE


def test_the_published_manifest_carries_counts_only():
    manifest = {"generated_at": "t", "counts": {"team": 1}, "source_counts": {"fixtures_played": 2}, "entries": [{"sha256": "x"}]}
    assert set(nsd.published_manifest(manifest)) == {"generated_at", "counts", "source_counts"}


def test_the_sample_is_replaced_by_the_export_and_the_readme_stays(tmp_path):
    site, export = tmp_path / "site", tmp_path / "export"
    data = site / "src" / "data"
    (data / "teams").mkdir(parents=True)
    (data / "teams" / "old.json").write_text("{}")
    (data / "landing.json").write_text("{}")
    (data / "README.md").write_text("keep")
    (export / "teams").mkdir(parents=True)
    (export / "teams" / "new.json").write_text("{}")
    (export / "manifest.json").write_text("{}")

    nsd.replace_sample_with_export(site, export)

    assert sorted(p.relative_to(data).as_posix() for p in data.rglob("*") if p.is_file()) == [
        "README.md",
        "manifest.json",
        "teams/new.json",
    ]
    assert list(export.iterdir()) == [], "the export is moved, so no second copy stays on the memory disk"


def test_the_crests_are_copied_into_the_public_folder_after_the_export_and_before_the_build():
    from pathlib import Path

    assert nsd.CRESTS_DIR == nsd.SITE_DIR / "public" / "crests"
    text = Path(nsd.__file__).read_text(encoding="utf-8")
    sample = text.index("replace_sample_with_export(SITE_DIR, EXPORT_DIR)")
    crests = text.index('step("crests"')
    build = text.index('"build and gates"')
    assert sample < crests < build
    assert "scripts/sync_crests.py" in text


def test_firebase_serves_the_crests_with_a_seven_day_cache_and_the_copy_is_not_committed():
    import json
    from pathlib import Path

    site = Path(nsd.SITE_DIR)
    headers = json.loads((site / "firebase.json").read_text(encoding="utf-8"))["hosting"]["headers"]
    crest = next(h for h in headers if h["source"] == "/crests/**")
    assert crest["headers"] == [{"key": "Cache-Control", "value": "public, max-age=604800"}]
    assert "public/crests/" in (site / ".gitignore").read_text(encoding="utf-8").splitlines()


def test_a_live_site_without_a_counts_file_refuses_unless_the_run_is_flagged_first():
    assert nsd.floor_issues(None, {"counts": {}}, allow_first=False)
    assert nsd.floor_issues(None, {"counts": {}}, allow_first=True) == []


def test_a_served_counts_file_is_compared_whatever_the_flag():
    low = {"counts": {**LIVE["counts"], "team": 1}}
    assert nsd.floor_issues(LIVE, low, allow_first=True)
    assert nsd.floor_issues(LIVE, LIVE, allow_first=False) == []


class _Recorder:
    """Stands in for `step`: records each step, writes the export's manifest, and can fail one step."""

    def __init__(self, export_dir, fail=None, counts=None):
        self.export_dir, self.fail, self.counts = export_dir, fail, counts or LIVE["counts"]
        self.names = []

    def __call__(self, name, command, cwd=None, env=None):
        self.names.append(name)
        if name == "export":
            (self.export_dir / "teams").mkdir(parents=True, exist_ok=True)
            (self.export_dir / "teams" / "1.json").write_text("{}")
            manifest = {"generated_at": "t", "counts": self.counts, "source_counts": {}}
            (self.export_dir / "manifest.json").write_text(json.dumps(manifest))
        if name == "build and gates":
            (nsd.SITE_DIR / "dist").mkdir(parents=True, exist_ok=True)
            (nsd.SITE_DIR / "dist" / "index.html").write_text("x")
        if name == self.fail:
            raise SystemExit(f"{name} failed")


@pytest.fixture
def job(tmp_path, monkeypatch):
    site = tmp_path / "site_v2"
    (site / "src" / "data").mkdir(parents=True)
    monkeypatch.setattr(nsd, "SITE_DIR", site)
    monkeypatch.setattr(nsd, "EXPORT_DIR", tmp_path / "export")
    monkeypatch.setattr(nsd, "wait_for_nightly", lambda session: None)
    monkeypatch.setattr(nsd, "fetch_live_manifest", lambda: LIVE)
    monkeypatch.delenv(nsd.FIRST_DEPLOY_FLAG, raising=False)
    return tmp_path


def test_the_steps_run_in_order_and_the_counts_file_goes_into_dist_before_the_deploy(job, monkeypatch):
    recorder = _Recorder(job / "export")
    monkeypatch.setattr(nsd, "step", recorder)

    assert nsd.deploy(object()) == 0

    assert recorder.names == ["export", "crests", "build and gates", "deploy"]
    assert json.loads((nsd.SITE_DIR / "dist" / nsd.PUBLISHED_MANIFEST).read_text())["counts"] == LIVE["counts"]


@pytest.mark.parametrize("failing", ["export", "build and gates"])
def test_a_failed_step_stops_the_job_before_the_firebase_deploy(job, monkeypatch, failing):
    recorder = _Recorder(job / "export", fail=failing)
    monkeypatch.setattr(nsd, "step", recorder)

    with pytest.raises(SystemExit):
        nsd.deploy(object())

    assert "deploy" not in recorder.names


def test_a_fall_below_the_live_counts_stops_the_job_before_the_build(job, monkeypatch):
    recorder = _Recorder(job / "export", counts={**LIVE["counts"], "team": 1})
    monkeypatch.setattr(nsd, "step", recorder)

    with pytest.raises(SystemExit, match="team"):
        nsd.deploy(object())

    assert recorder.names == ["export"]


def test_a_missing_counts_file_stops_the_job_before_the_build_unless_flagged(job, monkeypatch):
    monkeypatch.setattr(nsd, "fetch_live_manifest", lambda: None)
    recorder = _Recorder(job / "export")
    monkeypatch.setattr(nsd, "step", recorder)
    with pytest.raises(SystemExit, match=nsd.FIRST_DEPLOY_FLAG):
        nsd.deploy(object())
    assert recorder.names == ["export"]

    monkeypatch.setenv(nsd.FIRST_DEPLOY_FLAG, "1")
    recorder = _Recorder(job / "export")
    monkeypatch.setattr(nsd, "step", recorder)
    assert nsd.deploy(object()) == 0
    assert recorder.names == ["export", "crests", "build and gates", "deploy"]


def test_step_raises_on_a_failing_command():
    import subprocess

    with pytest.raises(subprocess.CalledProcessError):
        nsd.step("fails", [sys.executable, "-c", "raise SystemExit(3)"])


def test_the_site_build_script_runs_both_gates_after_the_build():
    package = json.loads((nsd.SITE_DIR / "package.json").read_text(encoding="utf-8"))
    build = package["scripts"]["build"]
    order = [build.index(part) for part in ("astro build", "audit-seo", "check-built-pages")]
    assert order == sorted(order), build
