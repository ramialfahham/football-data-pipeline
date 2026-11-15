"""MR pipelines test the branch merged with the latest target branch; pinned on the parsed CI file.

The merged-result step itself is also run in a throwaway repository, so the pin covers what the
shell does, not only where the step sits.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
CI = yaml.safe_load((ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8"))
MERGED = CI[".merged_result"]
PROFILE = CI[".dbt_profile"]

MERGED_JOBS = ("test:python", "build:site-v2", "validate:ui", "data:build:mr")


def _steps(job: str) -> list[str]:
    return list(CI[job].get("before_script") or []) + list(CI[job].get("script") or [])


def test_the_step_fetches_the_target_and_merges_it_on_merge_requests_only():
    assert MERGED.startswith('if [ "$CI_PIPELINE_SOURCE" = "merge_request_event" ]; then')
    assert 'fetch --no-tags origin "$CI_MERGE_REQUEST_TARGET_BRANCH_NAME"' in MERGED
    assert "config --global" not in MERGED, "the step must not write git config outside the job"
    assert 'merge --no-edit "$MR_TARGET_SHA"' in MERGED
    assert "export MR_TARGET_SHA=" in MERGED and "export MR_TARGET_SHORT_SHA=" in MERGED


@pytest.mark.parametrize("job", MERGED_JOBS)
def test_each_merged_job_merges_before_it_installs_or_builds_anything(job):
    steps = _steps(job)
    assert steps[0] == MERGED, f"{job} must run the merged-result step first; its first step is {steps[0]!r}"
    assert str(CI[job]["variables"]["GIT_DEPTH"]) == "0", f"{job} needs the full history to merge"


def test_governance_tests_the_branch_because_the_review_hash_is_computed_on_it():
    assert MERGED not in _steps("validate:governance")


def test_validate_ui_merges_the_target_commit_build_site_v2_built():
    build = CI["build:site-v2"]
    assert build["artifacts"]["reports"]["dotenv"] == "merged_result.env"
    writes = [s for s in build["script"] if "merged_result.env" in s]
    assert writes and "MR_TARGET_SHA=$MR_TARGET_SHA" in writes[0]
    assert CI["validate:ui"]["needs"] == ["build:site-v2"]
    assert 'MR_TARGET_SHA="${MR_TARGET_SHA:-' in MERGED


def test_the_mr_data_build_compares_against_the_commit_it_merged():
    raw = _steps("data:build:mr")
    assert raw.index(MERGED) < raw.index(PROFILE)
    steps = [" ".join(s.split()) for s in raw]
    assert not [s for s in steps if s.startswith("git fetch")], (
        "a second fetch can return a newer target than the one merged in"
    )
    assert "git worktree add --detach /tmp/main-src \"$MR_TARGET_SHA\"" in steps
    seed_diff = next(s for s in steps if s.startswith("SEED_DIFF="))
    assert '"${MR_TARGET_SHA:?}" HEAD' in seed_diff
    assert "CI_MERGE_REQUEST_DIFF_BASE_SHA" not in seed_diff


def test_scratch_datasets_are_named_per_merge_request_and_target_commit():
    line = next(ln.strip() for ln in PROFILE.splitlines() if "DBT_CI_TARGET=" in ln)
    assert "CI_MERGE_REQUEST_IID" in line and "MR_TARGET_SHORT_SHA" in line


def _bash() -> str | None:
    return shutil.which("bash")


def _target_name(env: dict[str, str]) -> str:
    line = next(ln.strip() for ln in PROFILE.splitlines() if "DBT_CI_TARGET=" in ln)
    out = subprocess.run(
        [_bash(), "-c", f'{line}\nprintf %s "$DBT_CI_TARGET"'],
        env={"PATH": os.environ["PATH"], **env}, capture_output=True, text=True, check=True,
    )
    return out.stdout


@pytest.mark.skipif(_bash() is None, reason="needs bash")
def test_the_scratch_name_expands_per_pipeline_kind():
    assert _target_name({"CI_MERGE_REQUEST_IID": "445", "MR_TARGET_SHORT_SHA": "1a2b3c4d"}) == "ci_mr445_1a2b3c4d"
    assert _target_name({}) == "ci_mrshared"


def test_the_mr_data_build_stops_when_the_merge_step_did_not_run():
    guard = CI["data:build:mr"]["script"][0]
    assert 'test -n "$MR_TARGET_SHA"' in guard and "exit 1" in guard


def test_two_merge_requests_build_at_once_and_one_merge_request_queues():
    assert CI["data:build:mr"]["resource_group"] == "ci-data-build-mr$CI_MERGE_REQUEST_IID"


def test_the_mr_data_build_starts_only_once_no_prod_build_holds_the_warehouse():
    gate = CI["data:wait-prod-build"]
    assert gate["resource_group"] == CI["data:build:main"]["resource_group"] == "prod-warehouse-write"
    assert gate["variables"]["GIT_STRATEGY"] == "none"
    assert gate["needs"] == []
    assert CI["data:build:mr"]["needs"] == ["data:wait-prod-build"]
    assert gate["rules"] == CI["data:build:mr"]["rules"], "GitLab refuses a needs: target its rules excluded"
    assert "id_tokens" not in gate and not any("GOOGLE" in s for s in gate["script"])


def test_the_mr_data_build_waits_for_the_nightly_before_its_first_bigquery_read():
    steps = _steps("data:build:mr")
    auth = next(i for i, s in enumerate(steps) if "GOOGLE_APPLICATION_CREDENTIALS" in s)
    wait = steps.index("python scripts/wait_for_nightly.py")
    first_read = next(i for i, s in enumerate(steps) if "dbt deps" in s or s.startswith("sqlfluff"))
    assert auth < wait < first_read


def test_mains_design_sweep_has_one_resource_group():
    group = CI["validate:ui"]["resource_group"]
    assert group.replace("$CI_COMMIT_REF_SLUG", "main") == "validate-ui-main"
    assert "interruptible" not in CI["validate:ui"]


def _git(cwd: pathlib.Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=cwd, capture_output=True, text=True, check=True,
    ).stdout.strip()


def _repo_with_a_stale_branch(tmp_path: pathlib.Path) -> tuple[pathlib.Path, str, str]:
    origin = tmp_path / "origin.git"
    work = tmp_path / "work"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(origin)], check=True, capture_output=True)
    subprocess.run(["git", "clone", str(origin), str(work)], check=True, capture_output=True)
    (work / "base.txt").write_text("base\n")
    _git(work, "add", "base.txt")
    _git(work, "commit", "-m", "base")
    _git(work, "push", "origin", "HEAD:main")
    _git(work, "checkout", "-b", "feature")
    (work / "feature.txt").write_text("feature\n")
    _git(work, "add", "feature.txt")
    _git(work, "commit", "-m", "feature")
    branch_sha = _git(work, "rev-parse", "HEAD")
    _git(work, "checkout", "main")
    (work / "dependency.txt").write_text("merged to main after the branch was cut\n")
    _git(work, "add", "dependency.txt")
    _git(work, "commit", "-m", "dependency")
    _git(work, "push", "origin", "main")
    target_sha = _git(work, "rev-parse", "HEAD")
    _git(work, "checkout", "--detach", branch_sha)
    return work, branch_sha, target_sha


def _clean_env() -> dict[str, str]:
    """os.environ without what the CI job's own merged-result step exported into pytest."""
    return {k: v for k, v in os.environ.items() if not k.startswith("MR_TARGET_")}


def _run_step(work: pathlib.Path, **env: str) -> subprocess.CompletedProcess:
    script = f"set -e\n{MERGED}\nprintf 'SHA=%s SHORT=%s\\n' \"$MR_TARGET_SHA\" \"$MR_TARGET_SHORT_SHA\""
    return subprocess.run(
        [_bash(), "-c", script], cwd=work, capture_output=True, text=True,
        env={**_clean_env(), "CI_MERGE_REQUEST_TARGET_BRANCH_NAME": "main", **env},
    )


def test_the_shell_tests_ignore_the_jobs_own_merged_target(monkeypatch):
    monkeypatch.setenv("MR_TARGET_SHA", "0" * 40)
    monkeypatch.setenv("MR_TARGET_SHORT_SHA", "00000000")
    assert not any(k.startswith("MR_TARGET_") for k in _clean_env())


@pytest.mark.skipif(_bash() is None, reason="needs bash")
def test_the_step_tests_a_stale_branch_with_the_dependency_merged_in(tmp_path):
    work, branch_sha, target_sha = _repo_with_a_stale_branch(tmp_path)
    run = _run_step(work, CI_PIPELINE_SOURCE="merge_request_event", CI_COMMIT_SHA=branch_sha)
    assert run.returncode == 0, run.stderr
    assert (work / "feature.txt").exists() and (work / "dependency.txt").exists()
    assert f"SHA={target_sha} SHORT={target_sha[:8]}" in run.stdout
    parents = _git(work, "rev-list", "--parents", "-n", "1", "HEAD").split()[1:]
    assert parents == [branch_sha, target_sha]


@pytest.mark.skipif(_bash() is None, reason="needs bash")
def test_the_step_merges_the_commit_it_was_handed(tmp_path):
    work, branch_sha, _ = _repo_with_a_stale_branch(tmp_path)
    base_sha = _git(work, "rev-parse", "HEAD~1")
    run = _run_step(work, CI_PIPELINE_SOURCE="merge_request_event", MR_TARGET_SHA=base_sha)
    assert run.returncode == 0, run.stderr
    assert not (work / "dependency.txt").exists()
    assert _git(work, "rev-parse", "HEAD") == branch_sha


@pytest.mark.skipif(_bash() is None, reason="needs bash")
def test_a_conflict_with_the_target_fails_the_step(tmp_path):
    work, branch_sha, _ = _repo_with_a_stale_branch(tmp_path)
    _git(work, "checkout", "main")
    (work / "feature.txt").write_text("main wrote this file too\n")
    _git(work, "add", "feature.txt")
    _git(work, "commit", "-m", "conflict")
    _git(work, "push", "origin", "main")
    _git(work, "checkout", "--detach", branch_sha)
    run = _run_step(work, CI_PIPELINE_SOURCE="merge_request_event")
    assert run.returncode != 0


@pytest.mark.skipif(_bash() is None, reason="needs bash")
def test_off_a_merge_request_the_step_changes_nothing(tmp_path):
    work, branch_sha, _ = _repo_with_a_stale_branch(tmp_path)
    run = _run_step(work, CI_PIPELINE_SOURCE="push")
    assert run.returncode == 0, run.stderr
    assert _git(work, "rev-parse", "HEAD") == branch_sha
    assert "SHA= SHORT=" in run.stdout
