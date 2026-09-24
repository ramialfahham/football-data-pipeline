"""Pin what `scripts/bootstrap.py` decides: skip what is done, never overwrite, never print the key."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import bootstrap  # noqa: E402

FAKE_KEY = "k3y-that-must-never-be-printed-0123456789"


def test_copy_if_missing_creates_the_file(tmp_path: Path):
    source, target = tmp_path / "a.example", tmp_path / "a"
    source.write_text("template", encoding="utf-8")

    assert bootstrap.copy_if_missing(source, target) is True
    assert target.read_text(encoding="utf-8") == "template"


def test_copy_if_missing_never_overwrites(tmp_path: Path):
    source, target = tmp_path / "a.example", tmp_path / "a"
    source.write_text("template", encoding="utf-8")
    target.write_text("mine", encoding="utf-8")

    assert bootstrap.copy_if_missing(source, target) is False
    assert target.read_text(encoding="utf-8") == "mine"


@pytest.mark.parametrize(
    ("root", "is_windows", "long_paths", "expected"),
    [
        ("C:\\" + "x" * 90, True, False, True),
        ("C:\\" + "x" * 90, True, True, False),
        ("C:\\" + "x" * 90, False, False, False),
        ("C:\\01_Projects\\football-data-pipeline", True, False, False),
    ],
)
def test_path_too_long_only_when_windows_limits_apply(root, is_windows, long_paths, expected):
    assert bootstrap.path_too_long(Path(root), is_windows, long_paths) is expected


@pytest.mark.parametrize(
    ("remotes", "expected"),
    [
        ({"origin": "https://gitlab.com/group/repo.git"}, True),
        ({"origin": "https://github.com/owner/repo.git"}, False),
        ({"gitlab": "https://gitlab.com/group/repo.git"}, False),
        ({"origin": "https://gitlab.com/a.git", "gitlab": "https://gitlab.com/b.git"}, False),
        ({}, False),
    ],
)
def test_remote_is_renamed_only_for_a_gitlab_origin_without_a_gitlab_remote(remotes, expected):
    assert bootstrap.remote_rename_needed(remotes) is expected


def test_npm_install_skipped_when_node_modules_is_newer_than_the_lock(tmp_path: Path):
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    assert bootstrap.npm_install_needed(tmp_path) is True

    installed = tmp_path / "node_modules" / ".package-lock.json"
    installed.parent.mkdir()
    installed.write_text("{}", encoding="utf-8")
    later = time.time() + 10
    os.utime(installed, (later, later))
    assert bootstrap.npm_install_needed(tmp_path) is False


def test_write_api_key_fills_the_empty_line_and_keeps_the_rest(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("# comment\nAPI_FOOTBALL_API_KEY=\n# API_FOOTBALL_INGEST_PROFILE=default\n", encoding="utf-8")

    bootstrap.write_api_key(env, FAKE_KEY)

    assert env.read_text(encoding="utf-8") == (
        f"# comment\nAPI_FOOTBALL_API_KEY={FAKE_KEY}\n# API_FOOTBALL_INGEST_PROFILE=default\n"
    )


def test_write_api_key_never_overwrites_a_key(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("API_FOOTBALL_API_KEY=existing\n", encoding="utf-8")

    with pytest.raises(bootstrap.SetupError):
        bootstrap.write_api_key(env, FAKE_KEY)
    assert env.read_text(encoding="utf-8") == "API_FOOTBALL_API_KEY=existing\n"


def test_fetch_key_writes_the_key_and_never_prints_it(tmp_path: Path, monkeypatch, capsys):
    (tmp_path / ".env.example").write_text("API_FOOTBALL_API_KEY=\n", encoding="utf-8")
    calls = []

    class Result:
        returncode = 0
        stdout = FAKE_KEY + "\n"
        stderr = ""

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return Result()

    monkeypatch.setattr(bootstrap, "ROOT", tmp_path)
    monkeypatch.setattr(bootstrap, "tool", lambda name: name)
    monkeypatch.setattr(bootstrap.subprocess, "run", fake_run)

    bootstrap.fetch_key()

    assert calls == [[
        "gcloud", "secrets", "versions", "access", "latest",
        "--secret=api-football-key", "--project=football-data-pipeline-gcp",
    ]]
    assert (tmp_path / ".env").read_text(encoding="utf-8") == f"API_FOOTBALL_API_KEY={FAKE_KEY}\n"
    output = capsys.readouterr()
    assert FAKE_KEY not in output.out and FAKE_KEY not in output.err


def test_pre_commit_installs_the_push_and_open_mr_hook():
    """The setup's `pre-commit install` is the only thing that puts the auto-push hook into a clone.

    Dropping `post-commit` from the install types, or the hook itself, leaves every test and the
    setup job green while new clones silently stop pushing and opening a merge request.
    """
    config = yaml.safe_load((Path(bootstrap.ROOT) / ".pre-commit-config.yaml").read_text(encoding="utf-8"))

    assert "post-commit" in config.get("default_install_hook_types", []), (
        "`pre-commit install` no longer installs a post-commit hook, so no clone pushes or opens an MR"
    )
    hooks = [
        hook
        for repo in config["repos"]
        for hook in repo["hooks"]
        if hook.get("entry") == ".githooks/post-commit"
    ]
    assert len(hooks) == 1, f"expected one hook running .githooks/post-commit, found {len(hooks)}"
    hook = hooks[0]
    assert hook.get("stages") == ["post-commit"], "the push hook must run after a commit, never before"
    assert hook.get("always_run") is True and hook.get("pass_filenames") is False, (
        "the push hook must run on every commit and take no file arguments"
    )
