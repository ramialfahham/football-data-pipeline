"""scripts/wait_for_nightly.py — the main prod build waits while a nightly run is in progress."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from unittest.mock import MagicMock

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("wait_for_nightly", REPO_ROOT / "scripts" / "wait_for_nightly.py")
wait_for_nightly = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wait_for_nightly)

PREFIX = "projects/football-data-pipeline-gcp/locations/europe-west1/jobs/fdp-nightly/executions/"


def _execution(name: str, completed: bool) -> dict:
    e = {"name": PREFIX + name, "createTime": "2026-10-07T04:00:31Z"}
    if completed:
        e["completionTime"] = "2026-10-07T05:20:00Z"
    return e


def test_an_execution_without_completion_time_is_in_progress():
    executions = [_execution("fdp-nightly-new", False), _execution("fdp-nightly-old", True)]
    assert wait_for_nightly.runs_in_progress(executions) == ["fdp-nightly-new"]


def test_finished_executions_failed_ones_included_are_not_in_progress():
    executions = [_execution("fdp-nightly-failed", True), _execution("fdp-nightly-ok", True)]
    assert wait_for_nightly.runs_in_progress(executions) == []


def test_no_executions_means_nothing_in_progress():
    assert wait_for_nightly.runs_in_progress([]) == []


def _session(*payloads):
    session = MagicMock()
    responses = []
    for payload in payloads:
        response = MagicMock()
        response.json.return_value = payload
        responses.append(response)
    session.get.side_effect = responses
    return session


def test_main_waits_until_the_run_completes(monkeypatch):
    session = _session(
        {"executions": [_execution("fdp-nightly-new", False)]},
        {"executions": [_execution("fdp-nightly-new", True)]},
    )
    sleeps = []
    monkeypatch.setattr(wait_for_nightly.google.auth, "default", lambda scopes: (MagicMock(), "p"))
    monkeypatch.setattr(wait_for_nightly, "AuthorizedSession", lambda credentials: session)
    monkeypatch.setattr(wait_for_nightly.time, "sleep", sleeps.append)
    assert wait_for_nightly.main() == 0
    assert session.get.call_count == 2
    assert sleeps == [wait_for_nightly.POLL_SECONDS]


def test_main_returns_at_once_when_nothing_runs(monkeypatch):
    session = _session({"executions": [_execution("fdp-nightly-old", True)]})
    monkeypatch.setattr(wait_for_nightly.google.auth, "default", lambda scopes: (MagicMock(), "p"))
    monkeypatch.setattr(wait_for_nightly, "AuthorizedSession", lambda credentials: session)
    monkeypatch.setattr(wait_for_nightly.time, "sleep", lambda s: (_ for _ in ()).throw(AssertionError("slept")))
    assert wait_for_nightly.main() == 0


def test_a_run_outlasting_the_deadline_fails_before_any_write(monkeypatch):
    session = MagicMock()
    session.get.return_value.json.return_value = {"executions": [_execution("fdp-nightly-long", False)]}
    sleeps = []
    monkeypatch.setattr(wait_for_nightly, "MAX_WAIT_SECONDS", 3 * wait_for_nightly.POLL_SECONDS)
    monkeypatch.setattr(wait_for_nightly.google.auth, "default", lambda scopes: (MagicMock(), "p"))
    monkeypatch.setattr(wait_for_nightly, "AuthorizedSession", lambda credentials: session)
    monkeypatch.setattr(wait_for_nightly.time, "sleep", sleeps.append)
    assert wait_for_nightly.main() == 1
    assert len(sleeps) == 3


def _seconds(timeout: str) -> int:
    units = {"h": 3600, "m": 60}
    return sum(int(n) * units[u] for n, u in re.findall(r"(\d+)\s*([hm])", timeout))


def test_the_main_build_waits_after_auth_and_before_its_first_prod_write():
    job = yaml.safe_load((REPO_ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8"))["data:build:main"]
    script = job["script"]
    auth = next(i for i, step in enumerate(script) if "GOOGLE_APPLICATION_CREDENTIALS" in step)
    wait = script.index("python scripts/wait_for_nightly.py")
    first_prod_write = next(i for i, step in enumerate(script) if "--target prod" in step)
    assert auth < wait < first_prod_write
    assert wait_for_nightly.MAX_WAIT_SECONDS <= _seconds(job["timeout"]) - 30 * 60


def test_an_api_error_fails_instead_of_continuing(monkeypatch):
    session = MagicMock()
    session.get.return_value.raise_for_status.side_effect = RuntimeError("403")
    monkeypatch.setattr(wait_for_nightly.google.auth, "default", lambda scopes: (MagicMock(), "p"))
    monkeypatch.setattr(wait_for_nightly, "AuthorizedSession", lambda credentials: session)
    try:
        wait_for_nightly.main()
    except RuntimeError:
        return
    raise AssertionError("an API error must fail the job")
