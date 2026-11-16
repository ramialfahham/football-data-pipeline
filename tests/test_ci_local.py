"""scripts/ci_local.py runs jobs of .gitlab-ci.yml locally and keeps no copy of a step."""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "ci_local.py"

spec = importlib.util.spec_from_file_location("ci_local", SCRIPT)
cl = importlib.util.module_from_spec(spec)
sys.modules["ci_local"] = cl
spec.loader.exec_module(cl)

MR_ENV = {"CI_PIPELINE_SOURCE": "merge_request_event", "CI_DEFAULT_BRANCH": "main"}


@pytest.fixture(scope="module")
def doc():
    return cl.load_ci()


def ci(tmp_path, body: str) -> dict:
    f = tmp_path / ".gitlab-ci.yml"
    f.write_text(textwrap.dedent(body), encoding="utf-8")
    return cl.load_ci(f)


def test_anchors_and_merge_keys_are_resolved(tmp_path):
    d = ci(tmp_path, """
        .base: &base
          image: python:3.11
          before_script: [pip install x]
        job:
          <<: *base
          script: [echo hi]
    """)
    job = cl.resolve_job(d, "job")
    assert job["image"] == "python:3.11" and job["before_script"] == ["pip install x"]


def test_extends_merges_hashes_deeply_and_replaces_lists(tmp_path):
    d = ci(tmp_path, """
        .a:
          variables: {X: "1", Y: "2"}
          script: [one, two]
        .b:
          extends: .a
          variables: {Y: "3"}
        job:
          extends: [.b]
          variables: {Z: "4"}
          script: [three]
    """)
    job = cl.resolve_job(d, "job")
    assert job["variables"] == {"X": "1", "Y": "3", "Z": "4"}
    assert job["script"] == ["three"]
    assert "extends" not in job


def test_an_extends_loop_is_refused(tmp_path):
    d = ci(tmp_path, """
        a: {extends: b, script: [x]}
        b: {extends: a, script: [x]}
    """)
    with pytest.raises(SystemExit):
        cl.resolve_job(d, "a")


def test_hidden_templates_and_global_keys_are_not_jobs(tmp_path):
    d = ci(tmp_path, """
        stages: [test]
        variables: {A: "1"}
        workflow: {rules: [{if: '$X'}]}
        .hidden: {script: [x]}
        real: {script: [x]}
    """)
    assert cl.job_names(d) == ["real"]


def test_unknown_tags_such_as_reference_do_not_break_loading(tmp_path):
    d = ci(tmp_path, """
        job:
          script:
            - !reference [.x, script]
            - echo ok
    """)
    assert "job" in d


@pytest.mark.parametrize("pattern,path,hit", [
    ("dbt_project/models/**/*", "dbt_project/models/a.sql", True),
    ("dbt_project/models/**/*", "dbt_project/models/1_staging/x/a.sql", True),
    ("dbt_project/models/**/*", "dbt_project/macros/a.sql", False),
    ("scripts/check_*.py", "scripts/check_copy_gate.py", True),
    ("scripts/check_*.py", "scripts/sub/check_copy_gate.py", False),
    ("dbt_project/*.yml", "dbt_project/dbt_project.yml", True),
    ("dbt_project/*.yml", "dbt_project/models/x.yml", False),
    (".githooks/**", ".githooks/pre-commit", True),
    (".githooks/**", ".githooks/sub/pre-commit", True),
    ("requirements*.txt", "requirements-ui.txt", True),
    ("requirements*.txt", "docs/requirements.txt", False),
    ("site/**/*", "site/i18n/en.json", True),
    ("**/*.md", "README.md", True),
    ("**/*.md", "docs/a/b.md", True),
    ("docs/{a,b}.md", "docs/b.md", True),
    ("docs/{a,b}.md", "docs/c.md", False),
    (".gitlab-ci.yml", ".gitlab-ci.yml", True),
    (".gitlab-ci.yml", "xgitlab-ci.yml", False),
])
def test_changes_globs_follow_gitlab(pattern, path, hit):
    assert cl.changes_match([pattern], [path]) is hit


def test_changes_accepts_the_paths_form():
    assert cl.changes_match({"paths": ["a/*.py"], "compare_to": "main"}, ["a/x.py"])
    assert not cl.changes_match({"paths": ["a/*.py"]}, ["b/x.py"])


@pytest.mark.parametrize("expr,expected", [
    ('$CI_PIPELINE_SOURCE == "merge_request_event"', True),
    ('$CI_PIPELINE_SOURCE == "push"', False),
    ('$CI_PIPELINE_SOURCE != "push"', True),
    ('$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH', False),
    ('$CI_COMMIT_BRANCH == null', True),
    ('$CI_COMMIT_BRANCH', False),
    ('$CI_DEFAULT_BRANCH', True),
    ('$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH && $CI_PIPELINE_SOURCE == "push"', False),
    ('$CI_PIPELINE_SOURCE == "push" || $CI_PIPELINE_SOURCE == "merge_request_event"', True),
    ('($CI_PIPELINE_SOURCE == "push" || $CI_DEFAULT_BRANCH) && $CI_PIPELINE_SOURCE =~ /^merge/', True),
    ('$CI_PIPELINE_SOURCE =~ /^PUSH$/i', False),
    ('$CI_PIPELINE_SOURCE !~ /^push$/', True),
    ("$CI_DEFAULT_BRANCH == 'main'", True),
])
def test_rules_if_expressions(expr, expected):
    assert cl.eval_if(expr, MR_ENV) is expected


def test_an_unreadable_if_is_an_error_not_a_silent_false():
    with pytest.raises(ValueError):
        cl.eval_if("$A ~~ 1", MR_ENV)


def test_first_matching_rule_decides_and_changes_must_hit(tmp_path):
    d = ci(tmp_path, """
        job:
          script: [x]
          rules:
            - if: $CI_PIPELINE_SOURCE == "schedule"
              when: never
            - if: $CI_PIPELINE_SOURCE == "merge_request_event"
              changes: [src/**/*]
            - if: $CI_PIPELINE_SOURCE == "web"
              when: manual
    """)
    job = cl.resolve_job(d, "job")
    assert cl.rule_when(job, MR_ENV, ["src/a/b.py"]) == "on_success"
    assert cl.rule_when(job, MR_ENV, ["docs/a.md"]) is None
    assert cl.rule_when(job, dict(MR_ENV, CI_PIPELINE_SOURCE="schedule"), ["src/a"]) == "never"
    assert cl.rule_when(job, dict(MR_ENV, CI_PIPELINE_SOURCE="web"), []) == "manual"


def test_a_job_without_rules_runs_in_every_pipeline():
    assert cl.rule_when({"script": ["x"]}, MR_ENV, []) == "on_success"


def test_variables_expand_in_order_and_unknown_ones_are_empty():
    env = cl.job_env({"variables": {"A": "$CI_PROJECT_DIR/.cache"}}, {"variables": {"B": "${A}/x", "C": "$$HOME $NOPE"}},
                     {"CI_PROJECT_DIR": "/work"})
    assert env["A"] == "/work/.cache" and env["B"] == "/work/.cache/x" and env["C"] == "$HOME "


def test_needs_artifacts_exclude_jobs_that_say_artifacts_false():
    job = {"needs": ["a", {"job": "b"}, {"job": "c", "artifacts": False}]}
    assert cl.artifact_needs(job) == ["a", "b"]
    assert cl.artifact_needs({"needs": []}) == []
    assert cl.artifact_needs({}) == []


def test_only_the_named_needs_reach_a_job(tmp_path):
    runs = tmp_path
    for job, name in (("build-site-v2", "dist.txt"), ("other-job", "leak.txt")):
        (runs / job / "out" / "artifacts" / "site_v2").mkdir(parents=True)
        (runs / job / "out" / "artifacts" / "site_v2" / name).write_text("x")
    (runs / "build-site-v2" / "out" / "dotenv.env").write_text("MR_TARGET_SHA=abc\n# c\n")
    plans = {"build:site-v2": {"name": "build:site-v2"}, "other-job": {"name": "other-job"},
             "validate:ui": {"name": "validate:ui", "needs": ["build:site-v2"]}}
    folder, env = cl.collect_needs(plans, plans["validate:ui"], runs)
    assert (folder / "site_v2" / "dist.txt").exists()
    assert not (folder / "site_v2" / "leak.txt").exists()
    assert env == {"MR_TARGET_SHA": "abc"}
    assert cl.collect_needs(plans, {"name": "x", "needs": []}, runs) == (None, {})


@pytest.mark.parametrize("given, expected", [
    ("C:\\x\\y", "\\\\?\\C:\\x\\y"),
    ("\\\\?\\C:\\x", "\\\\?\\C:\\x"),
    ("\\\\server\\share\\x", "\\\\?\\UNC\\server\\share\\x"),
])
def test_the_extended_length_form_of_a_windows_path(given, expected):
    assert cl.extended(given) == expected


@pytest.mark.skipif(os.name != "nt", reason="the 260-character limit is Windows-only")
def test_artifacts_deeper_than_260_characters_are_handed_over_and_removed(tmp_path):
    runs = tmp_path
    deep = Path(*["segment-of-some-length"] * 12, "page.txt")
    src = runs / "build-site-v2" / "out" / "artifacts" / "site_v2" / deep
    assert len(str(src)) > 300
    os.makedirs(cl.long_path(src.parent))
    Path(cl.long_path(src)).write_text("x")
    plans = {"build:site-v2": {"name": "build:site-v2"},
             "validate:ui": {"name": "validate:ui", "needs": ["build:site-v2"]}}
    folder, _ = cl.collect_needs(plans, plans["validate:ui"], runs)
    assert Path(cl.long_path(folder / "site_v2" / deep)).read_text() == "x"
    cl.rm_tree(runs / "build-site-v2")
    assert not Path(cl.long_path(src)).exists()


def test_a_need_runs_before_its_dependant(doc):
    order = cl.order_jobs(doc, ["validate:ui"])
    assert order.index("build:site-v2") < order.index("validate:ui")
    both = cl.order_jobs(doc, ["validate:ui", "build:site-v2"])
    assert both == order


def changed_run(doc, changed):
    return cl.select_mr_jobs(doc, MR_ENV, changed)


def test_a_script_only_change_runs_the_always_on_jobs_and_nothing_else(doc):
    run, skipped = changed_run(doc, ["scripts/ci_local.py", "tests/test_ci_local.py"])
    assert set(run) == {"validate:governance", "validate:secrets", "lint:python", "test:python"}
    assert skipped == {}


def test_a_site_change_adds_the_build_and_the_design_check(doc):
    run, _ = changed_run(doc, ["site_v2/src/pages/index.astro"])
    assert {"build:site-v2", "validate:ui"} <= set(run)
    assert "data:build:mr" not in run


def test_a_model_change_runs_the_data_job_and_skips_the_warehouse_gate(doc):
    run, skipped = changed_run(doc, ["dbt_project/models/5_marts/x.sql"])
    assert "data:build:mr" in run
    assert "data:wait-prod-build" in skipped


def test_a_ci_file_change_runs_every_path_filtered_job(doc):
    run, _ = changed_run(doc, [".gitlab-ci.yml"])
    assert {"data:build:mr", "build:site-v2", "validate:ui", "setup:clean-clone"} <= set(run)


def test_an_mr_never_selects_a_main_only_manual_or_deploy_job(doc):
    for changed in (["dbt_project/models/a.sql"], ["site_v2/src/a.astro"], [".gitlab-ci.yml"]):
        run, skipped = changed_run(doc, changed)
        picked = set(run) | set(skipped)
        for name in ("data:build:main", "data:nightly", "deploy:export", "deploy:site-v2",
                     "build:nightly-image", "deploy:nightly-image"):
            assert name not in picked, name


def test_a_schedule_pipeline_selects_no_job_but_the_nightly(doc):
    env = dict(MR_ENV, CI_PIPELINE_SOURCE="schedule", CI_COMMIT_BRANCH="main")
    run, _ = cl.select_mr_jobs(doc, env, ["dbt_project/models/a.sql"])
    assert set(run) <= {"data:nightly"}


def test_every_job_in_the_file_is_planned_or_named_as_skipped(doc):
    for name in cl.job_names(doc):
        job = cl.resolve_job(doc, name)
        assert cl.skip_reason(job) or cl.plan_job(doc, name)["image"] != "None", name


def test_a_job_without_an_image_is_refused():
    with pytest.raises(SystemExit):
        cl.image_of({"script": ["x"]})


def test_the_jobs_that_deploy_or_hold_a_credential_are_skipped(doc):
    for name in ("deploy:export", "deploy:site-v2", "build:nightly-image", "deploy:nightly-image",
                 "data:wait-prod-build"):
        assert cl.skip_reason(cl.resolve_job(doc, name)), name
    for name in ("validate:governance", "validate:ui", "build:site-v2", "test:python", "lint:python",
                 "validate:secrets", "setup:clean-clone", "data:build:mr"):
        assert cl.skip_reason(cl.resolve_job(doc, name)) is None, name


def test_the_merged_result_step_is_made_by_the_command_not_run_in_the_job(doc):
    text = cl.merged_result_text(doc)
    assert "git" in text and "merge" in text
    for name, merged in (("test:python", True), ("build:site-v2", True), ("validate:ui", True),
                         ("data:build:mr", True), ("validate:governance", False), ("lint:python", False),
                         ("validate:secrets", False)):
        p = cl.plan_job(doc, name)
        assert p["merged"] is merged, name
        assert all(s.strip() != text for s in p["before"] + p["script"]), name


def test_validate_ui_receives_the_site_build_and_its_dotenv(doc):
    ui, build = cl.plan_job(doc, "validate:ui"), cl.plan_job(doc, "build:site-v2")
    assert ui["needs"] == ["build:site-v2"]
    assert "site_v2/dist" in build["artifact_paths"] and build["dotenv"] == "merged_result.env"
    assert cl.plan_job(doc, "test:python")["needs"] == []


def test_a_data_job_runs_parse_and_lint_and_never_a_write(doc):
    p = cl.plan_job(doc, "data:build:mr")
    text = "\n".join(p["before"] + p["script"])
    assert "dbt parse" in text and "sqlfluff lint" in text
    assert not cl.DBT_WRITES.search(text)
    for forbidden in ("wait_for_nightly", "bq ", "ingestion", "git worktree", "GOOGLE_APPLICATION",
                      str(doc[".gcp_auth"]).strip()):
        assert forbidden not in text, forbidden
    assert p["needs"] == []
    assert str(doc[".dbt_profile"]) in p["script"]


def test_the_data_lint_runs_the_committed_config_without_a_subset(doc):
    assert "--rules" not in cl.SQLFLUFF_OFFLINE and "--config" not in cl.SQLFLUFF_OFFLINE
    assert "--templater jinja" in cl.SQLFLUFF_OFFLINE


def test_every_script_item_becomes_one_step_verbatim_with_lf(doc, tmp_path):
    p = cl.plan_job(doc, "validate:governance")
    files = cl.write_steps(p, tmp_path, False)
    assert len(files) == len(p["script"]) > 8
    for f, step in zip(files, p["script"]):
        assert f.read_bytes() == (step.rstrip("\n") + "\n").encode("utf-8")
    for name in ("before.sh", "runner.sh", "artifacts.txt", "fullscope.txt"):
        assert b"\r" not in (tmp_path / name).read_bytes(), name


def test_the_steps_that_branch_on_the_pipeline_source_are_the_full_scope_pass(doc, tmp_path):
    p = cl.plan_job(doc, "validate:ui")
    cl.write_steps(p, tmp_path, True)
    scoped = (tmp_path / "fullscope.txt").read_text().split()
    assert scoped and all("CI_PIPELINE_SOURCE" in (tmp_path / n).read_text() for n in scoped)
    cl.write_steps(p, tmp_path, False)
    assert (tmp_path / "fullscope.txt").read_text() == ""


def test_stale_steps_of_an_earlier_job_are_removed(doc, tmp_path):
    cl.write_steps(cl.plan_job(doc, "validate:governance"), tmp_path, False)
    cl.write_steps(cl.plan_job(doc, "validate:secrets"), tmp_path, False)
    assert [f.name for f in tmp_path.glob("[0-9]*.sh")] == ["01.sh"]


def test_the_container_gets_the_jobs_image_read_only_tree_and_no_credential(doc, tmp_path):
    p = cl.plan_job(doc, "data:build:mr")
    env = cl.job_env(doc, p["job"], cl.pipeline_env("a" * 40, "b" * 40, "br"))
    cmd = cl.docker_command(p, env, tmp_path, tmp_path, tmp_path, "name", None, False, False)
    assert p["image"] in cmd and cmd[cmd.index("--entrypoint") + 1] == "sh"
    assert any(a.endswith(",readonly") and "target=/src" in a for a in cmd)
    assert not any("target=/needs" in a for a in cmd)
    assert "CI_PIPELINE_SOURCE=merge_request_event" in cmd
    joined = " ".join(cmd)
    for forbidden in ("GOOGLE_APPLICATION_CREDENTIALS", "GITLAB_OIDC_TOKEN", ".config/gcloud"):
        assert forbidden not in joined


def test_needs_are_mounted_and_the_scope_flags_reach_the_container(doc, tmp_path):
    p = cl.plan_job(doc, "validate:ui")
    cmd = cl.docker_command(p, {}, tmp_path, tmp_path, tmp_path, "n", tmp_path, True, True)
    assert any("target=/needs,readonly" in a for a in cmd)
    assert "FAIL_FAST=1" in cmd and "FULL_SCOPE=1" in cmd


def test_the_script_keeps_no_second_copy_of_a_check():
    text = SCRIPT.read_text(encoding="utf-8")
    for name in ("check_layer_contract", "check_design_inventory", "check_chart_screenshots", "npm run build",
                 "pytest tests", "pre-commit run", "gitleaks"):
        assert name not in text, name


def test_the_script_and_its_runner_have_lf_endings():
    assert b"\r" not in SCRIPT.read_bytes()
    assert "\r" not in cl.RUNNER


def run_git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args], cwd=cwd, check=True,
                   capture_output=True)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    run_git(r, "init", "-q", "-b", "main")
    run_git(r, "config", "core.autocrlf", "true")
    (r / "a.sh").write_bytes(b"echo a\n")
    run_git(r, "add", "-A")
    run_git(r, "commit", "-q", "-m", "one")
    return r


def head(r):
    return cl.git(r, "rev-parse", "HEAD")


def test_a_clean_tree_is_tested_as_head(repo, tmp_path):
    assert cl.snapshot_commit(repo, tmp_path) == head(repo)


def test_uncommitted_changes_are_part_of_the_branch_and_the_index_is_untouched(repo, tmp_path):
    (repo / "a.sh").write_bytes(b"echo changed\r\n")
    (repo / "new.txt").write_text("new")
    before = cl.git(repo, "status", "--porcelain")
    snap = cl.snapshot_commit(repo, tmp_path)
    assert snap != head(repo)
    assert cl.git(repo, "show", "%s:new.txt" % snap) == "new"
    assert b"\r" not in subprocess.run(["git", "show", "%s:a.sh" % snap], cwd=repo, capture_output=True).stdout
    assert cl.git(repo, "status", "--porcelain") == before
    assert cl.git(repo, "rev-parse", "HEAD") == head(repo)


def make_trees(repo, tmp_path, target_sha, ref="refs/ci_local/t"):
    cl.git(repo, "update-ref", ref, head(repo))
    return cl.Trees(repo, tmp_path / "run", head(repo), target_sha, ref)


def test_the_branch_tree_is_checked_out_with_lf_whatever_the_machine_setting(repo, tmp_path):
    trees = make_trees(repo, tmp_path, head(repo))
    tree = trees.get(False)
    assert (tree / "a.sh").read_bytes() == b"echo a\n"
    assert cl.git(tree, "rev-parse", "origin/main") == head(repo)


def test_the_merged_tree_holds_the_branch_and_the_latest_target(repo, tmp_path):
    base = head(repo)
    run_git(repo, "checkout", "-q", "-b", "feature")
    (repo / "feature.txt").write_text("f")
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-q", "-m", "feature")
    run_git(repo, "checkout", "-q", "main")
    (repo / "main2.txt").write_text("m")
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-q", "-m", "main moved")
    target = head(repo)
    run_git(repo, "checkout", "-q", "feature")
    trees = make_trees(repo, tmp_path, target)
    merged = trees.get(True)
    assert (merged / "feature.txt").exists() and (merged / "main2.txt").exists()
    assert not (trees.get(False) / "main2.txt").exists()
    assert base != target


def test_a_branch_that_conflicts_with_the_target_fails_as_the_mr_would(repo, tmp_path):
    run_git(repo, "checkout", "-q", "-b", "feature")
    (repo / "a.sh").write_bytes(b"echo feature\n")
    run_git(repo, "commit", "-q", "-am", "f")
    run_git(repo, "checkout", "-q", "main")
    (repo / "a.sh").write_bytes(b"echo main\n")
    run_git(repo, "commit", "-q", "-am", "m")
    target = head(repo)
    run_git(repo, "checkout", "-q", "feature")
    with pytest.raises(SystemExit, match="does not merge"):
        make_trees(repo, tmp_path, target).get(True)


def test_the_throwaway_trees_can_be_removed_even_with_read_only_git_objects(repo, tmp_path):
    trees = make_trees(repo, tmp_path, head(repo))
    tree = trees.get(False)
    cl.rm_tree(tmp_path / "run")
    assert not tree.exists()


def test_a_rename_lists_the_old_and_the_new_path(repo):
    base = head(repo)
    run_git(repo, "checkout", "-q", "-b", "feature")
    (repo / "dir").mkdir()
    run_git(repo, "mv", "a.sh", "dir/a.sh")
    (repo / "dir" / "café.txt").write_text("x")
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-q", "-m", "rename")
    assert sorted(cl.changed_files(repo, base, head(repo))) == ["a.sh", "dir/a.sh", "dir/café.txt"]


def run_name(hours_ago: float) -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.localtime(time.time() - hours_ago * 3600)) + "-4242"


def test_only_a_run_older_than_a_day_counts_as_killed():
    assert cl.run_is_stale(run_name(25)) and not cl.run_is_stale(run_name(1)) and not cl.run_is_stale(run_name(0))
    assert not cl.run_is_stale("not-a-run-id")


def test_pruning_removes_a_killed_runs_leftovers_and_spares_every_live_run(repo, tmp_path, monkeypatch):
    monkeypatch.setattr(cl, "OUT", tmp_path / "out")
    old, live = run_name(30), run_name(0.5)
    for folder in ("trees", "runs"):
        for name in (old, live):
            (tmp_path / "out" / folder / name).mkdir(parents=True)
    mine = "refs/ci_local/%s/" % cl.WORKTREE
    other_worktree = "refs/ci_local/ffffff/" + old
    for ref in (mine + old, mine + live, other_worktree):
        cl.git(repo, "update-ref", ref, head(repo))
    cl.prune_stale(repo)
    for folder in ("trees", "runs"):
        assert not (tmp_path / "out" / folder / old).exists()
        assert (tmp_path / "out" / folder / live).exists()
    assert cl.git(repo, "for-each-ref", "--format=%(refname)", "refs/ci_local/").split() == sorted([other_worktree, mine + live])


def test_two_runs_in_one_worktree_never_share_a_container_name():
    assert cl.container_name(run_name(0), "test:python") != cl.container_name(run_name(1), "test:python")
    assert cl.container_name("r", "test:python") != cl.container_name("r", "lint:python")




def test_a_string_exit_becomes_exit_code_2(monkeypatch, capsys):
    monkeypatch.setattr(cl, "main", lambda: (_ for _ in ()).throw(SystemExit("boom")))
    assert cl.run() == 2
    assert "boom" in capsys.readouterr().err


def test_a_numeric_exit_passes_through(monkeypatch):
    monkeypatch.setattr(cl, "main", lambda: (_ for _ in ()).throw(SystemExit(0)))
    with pytest.raises(SystemExit):
        cl.run()


def test_a_tree_that_cannot_be_removed_is_reported_not_raised(tmp_path, monkeypatch, capsys):
    def refuse(*_a, **_k):
        raise PermissionError("locked")
    (tmp_path / "t").mkdir()
    monkeypatch.setattr(cl.shutil, "rmtree", refuse)
    cl.rm_tree(tmp_path / "t")
    assert "could not remove" in capsys.readouterr().err


def test_a_step_that_reads_stdin_cannot_eat_the_step_list(tmp_path):
    steps = {"01.sh": "cat > /dev/null\necho one >> trail.txt\n", "02.sh": "cat > /dev/null\necho two >> trail.txt\n",
             "fullscope.txt": "01.sh\n02.sh\n", "scoped": ""}
    res, root = run_runner(tmp_path, steps, {"FULL_SCOPE": "1"})
    assert res.returncode == 0, res.stdout + res.stderr
    assert (root / "work" / "trail.txt").read_text().split() == ["one", "two", "one", "two"]


def run_runner(tmp_path, steps: dict[str, str], env: dict[str, str] | None = None):
    """The runner script itself, with its container paths moved under tmp_path."""
    sh = shutil.which("sh")
    if sh is None:
        pytest.skip("no sh on this machine")
    root = tmp_path / "root"
    for d in ("src", "steps", "out", "work", "state", "cache"):
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / "src" / "file.txt").write_text("tree")
    for name, body in steps.items():
        (root / "steps" / name).write_text(body, encoding="utf-8", newline="\n")
    script = cl.RUNNER
    for d in ("src", "steps", "out", "work", "state", "cache", "needs"):
        script = script.replace("/" + d, (root / d).as_posix())
    (root / "runner.sh").write_text(script, encoding="utf-8", newline="\n")
    res = subprocess.run([sh, (root / "runner.sh").as_posix()], capture_output=True, text=True, encoding="utf-8",
                         env=dict(os.environ, **(env or {})), cwd=tmp_path)
    return res, root


def test_the_runner_carries_cwd_and_exports_between_steps(tmp_path):
    res, root = run_runner(tmp_path, {"01.sh": "mkdir sub && cd sub && export KEPT=yes\n",
                                      "02.sh": "test \"$(basename \"$PWD\")\" = sub && test \"$KEPT\" = yes\n"})
    assert res.returncode == 0, res.stdout + res.stderr
    assert "0 step(s) failed" in res.stdout
    assert (root / "work" / "file.txt").read_text() == "tree"


def test_the_runner_counts_a_failing_step_and_runs_the_rest(tmp_path):
    res, _ = run_runner(tmp_path, {"01.sh": "false\n", "02.sh": "echo second\n"})
    assert res.returncode != 0
    assert "FAIL" in res.stdout and "second" in res.stdout and "1 step(s) failed" in res.stdout


def test_fail_fast_stops_at_the_first_failing_step(tmp_path):
    res, _ = run_runner(tmp_path, {"01.sh": "false\n", "02.sh": "echo second\n"}, {"FAIL_FAST": "1"})
    assert res.returncode != 0 and "second" not in res.stdout


def test_a_failing_before_script_stops_the_job_with_exit_2(tmp_path):
    res, _ = run_runner(tmp_path, {"before.sh": "false\n", "01.sh": "echo never\n"})
    assert res.returncode == 2 and "never" not in res.stdout


def test_the_full_scope_pass_runs_the_listed_steps_as_a_push(tmp_path):
    steps = {"01.sh": "echo src=$CI_PIPELINE_SOURCE >> trail.txt\n", "fullscope.txt": "01.sh\n"}
    res, root = run_runner(tmp_path, steps, {"CI_PIPELINE_SOURCE": "merge_request_event", "FULL_SCOPE": "1"})
    assert res.returncode == 0, res.stdout + res.stderr
    assert (root / "work" / "trail.txt").read_text().split() == ["src=merge_request_event", "src=push"]


def test_the_runner_hands_over_only_the_listed_artifacts_and_the_dotenv(tmp_path):
    steps = {"01.sh": "mkdir -p dist && echo built > dist/index.html && echo junk > other.txt && echo A=1 > job.env\n",
             "artifacts.txt": "dist\n"}
    res, root = run_runner(tmp_path, steps, {"CI_LOCAL_DOTENV": "job.env"})
    assert res.returncode == 0, res.stdout + res.stderr
    assert (root / "out" / "artifacts" / "dist" / "index.html").read_text().strip() == "built"
    assert not (root / "out" / "artifacts" / "other.txt").exists()
    assert (root / "out" / "dotenv.env").read_text().strip() == "A=1"
