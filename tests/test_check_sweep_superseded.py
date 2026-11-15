"""scripts/check_sweep_superseded.py — an older main design sweep stops when a newer one covers it."""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("check_sweep_superseded", ROOT / "scripts" / "check_sweep_superseded.py")
sweep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sweep)
CI = yaml.safe_load((ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8"))


def test_the_patterns_are_the_jobs_own_main_rule():
    rule = next(r for r in CI["validate:ui"]["rules"] if "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH" in str(r.get("if")))
    assert sweep.main_changes(CI) == rule["changes"]
    assert "site_v2/**/*" in sweep.main_changes(CI)


def test_globs_match_like_gitlab_changes():
    patterns = ["site_v2/**/*", "tests/fixtures/design_inventory/*", "requirements-ui.txt"]
    assert sweep.matches("site_v2/src/pages/index.astro", patterns)
    assert sweep.matches("site_v2/package.json", patterns)
    assert sweep.matches("tests/fixtures/design_inventory/baseline.json", patterns)
    assert sweep.matches("requirements-ui.txt", patterns)
    assert not sweep.matches("tests/fixtures/design_inventory/sub/x.json", patterns)
    assert not sweep.matches("dbt_project/models/marts/mart_x.sql", patterns)
    assert not sweep.matches("requirements-ui.txt.bak", patterns)
    assert not sweep.matches("xsite_v2/a", patterns)


def test_only_a_newer_push_touching_the_list_supersedes():
    pushes = [("c3", ["dbt_project/models/a.sql"]), ("c2", ["site_v2/src/x.astro"])]
    assert sweep.superseding_push(pushes, ["site_v2/**/*"]) == "c2"
    assert sweep.superseding_push(pushes[:1], ["site_v2/**/*"]) is None
    assert sweep.superseding_push([], ["site_v2/**/*"]) is None


def _git(cwd: pathlib.Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=cwd, capture_output=True, text=True, check=True,
    ).stdout


def _merge(repo: pathlib.Path, branch: str, path: str) -> str:
    _git(repo, "checkout", "-q", "-b", branch, "main")
    (repo / path).parent.mkdir(parents=True, exist_ok=True)
    (repo / path).write_text(branch)
    _git(repo, "add", path)
    _git(repo, "commit", "-q", "-m", branch)
    _git(repo, "checkout", "-q", "main")
    _git(repo, "merge", "-q", "--no-ff", "--no-edit", branch)
    return _git(repo, "rev-parse", "HEAD").strip()


def test_each_newer_merge_reports_only_its_own_files(tmp_path):
    repo = tmp_path / "r"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    (repo / "README").write_text("x")
    _git(repo, "add", "README")
    _git(repo, "commit", "-q", "-m", "base")
    this = _merge(repo, "a", "site_v2/a.astro")
    data = _merge(repo, "b", "dbt_project/models/b.sql")
    site = _merge(repo, "c", "site_v2/c.astro")
    pushes = sweep.newer_pushes(lambda *a: _git(repo, *a), this, site)
    assert pushes == [(site, ["site_v2/c.astro"]), (data, ["dbt_project/models/b.sql"])]
    assert sweep.superseding_push(pushes, ["site_v2/**/*"]) == site
    assert sweep.newer_pushes(lambda *a: _git(repo, *a), site, site) == []


def _pushed_main(tmp_path: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    origin = tmp_path / "origin.git"
    repo = tmp_path / "clone"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    subprocess.run(["git", "clone", "-q", str(origin), str(repo)], check=True, capture_output=True)
    (repo / ".gitlab-ci.yml").write_text((ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8"), encoding="utf-8")
    _git(repo, "add", ".gitlab-ci.yml")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "push", "-q", "origin", "HEAD:main")
    return origin, repo


def _main(monkeypatch, repo: pathlib.Path, this_sha: str) -> int:
    monkeypatch.setattr(sweep, "REPO", repo)
    monkeypatch.setenv("CI_COMMIT_SHA", this_sha)
    monkeypatch.setenv("CI_DEFAULT_BRANCH", "main")
    return sweep.main()


def test_main_stops_the_sweep_when_a_newer_push_has_its_own(tmp_path, monkeypatch, capsys):
    _, repo = _pushed_main(tmp_path)
    this = _merge(repo, "a", "site_v2/a.astro")
    newer = _merge(repo, "b", "site_v2/b.astro")
    _git(repo, "push", "-q", "origin", "main")
    _git(repo, "checkout", "-q", "--detach", this)
    assert _main(monkeypatch, repo, this) == 0
    assert newer in capsys.readouterr().out


def test_main_runs_the_sweep_when_no_newer_push_touches_the_list(tmp_path, monkeypatch):
    _, repo = _pushed_main(tmp_path)
    this = _merge(repo, "a", "site_v2/a.astro")
    _merge(repo, "b", "dbt_project/models/b.sql")
    _git(repo, "push", "-q", "origin", "main")
    assert _main(monkeypatch, repo, this) == 1


def test_main_runs_the_sweep_on_the_newest_commit(tmp_path, monkeypatch):
    _, repo = _pushed_main(tmp_path)
    this = _merge(repo, "a", "site_v2/a.astro")
    _git(repo, "push", "-q", "origin", "main")
    assert _main(monkeypatch, repo, this) == 1


def test_a_failed_fetch_never_reads_as_superseded(tmp_path, monkeypatch):
    _, repo = _pushed_main(tmp_path)
    this = _merge(repo, "a", "site_v2/a.astro")
    _git(repo, "remote", "set-url", "origin", str(tmp_path / "missing.git"))
    try:
        code = _main(monkeypatch, repo, this)
    except subprocess.CalledProcessError:
        return
    assert code != 0


def test_the_script_exits_non_zero_on_any_error(tmp_path):
    env = {k: v for k, v in os.environ.items() if k not in ("CI_COMMIT_SHA", "CI_DEFAULT_BRANCH")}
    run = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_sweep_superseded.py")],
                         env=env, capture_output=True, text=True)
    assert run.returncode != 0


def test_only_a_push_to_main_may_stop_its_sweep_and_only_before_any_check():
    first = CI["validate:ui"]["script"][0]
    assert "python scripts/check_sweep_superseded.py" in first and "exit 0" in first
    assert '"$CI_PIPELINE_SOURCE" = "push"' in first
    assert '"$CI_COMMIT_BRANCH" = "$CI_DEFAULT_BRANCH"' in first
    rest = "\n".join(CI["validate:ui"]["script"][1:])
    assert "check_sweep_superseded" not in rest
