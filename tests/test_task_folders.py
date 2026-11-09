"""Per-task artifact folders: each task's files live in `.claude/task/<issue>-<slug>/`.

Pins the cases the mechanism exists for: two tasks open side by side and merged in either
order, a code change with no task folder, a branch that touches another task's folder, and a
branch that merges main into itself through a conflict. The
exclusion patterns come from the REAL routing file, so a pattern that stops matching fails here.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOOKS = ROOT / ".claude" / "hooks"
CI_SCRIPT = ROOT / "scripts" / "check_task_artifacts.py"

REAL = json.loads((ROOT / ".claude" / "review_routing.json").read_text(encoding="utf-8"))
ROUTING = {
    "always": ["scope-auditor"],
    "paths": {},
    "artifact_only": REAL["artifact_only"],
    "artifact_only_never": REAL["artifact_only_never"],
    "hash_exclude_paths": REAL["hash_exclude_paths"],
    "review_exclude_paths": REAL["review_exclude_paths"],
}

CONTRACT = "\n".join([
    "objective: >", "  test", "scope_paths:", "  - {code}",
    "decisions_reserved:", "  - none: test", "done_when:", "  - test", "",
])

REVIEW = "\n".join([
    "diff_sha256: {sha}", "rounds: 1", "",
    "#" * 2 + " scope-auditor", "VERDICT: PASS", "risks_checked:",
    "  - the diff against the contract, no defect", "",
])


def git(repo, *args, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=check)


def env(repo, base: str | None = "main") -> dict:
    e = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    if base:
        e["GOVERNANCE_BASE"] = base
    else:
        e.pop("GOVERNANCE_BASE", None)
    return e


@pytest.fixture()
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-q")
    git(r, "config", "user.email", "t@t")
    git(r, "config", "user.name", "t")
    (r / ".claude").mkdir()
    (r / ".claude" / "review_routing.json").write_text(json.dumps(ROUTING), encoding="utf-8")
    (r / ".claude" / "task").mkdir()
    (r / ".claude" / "task" / "TEMPLATE.md").write_text("template\n", encoding="utf-8")
    (r / ".claude" / "task" / "contract.md").write_text("an old shared contract\n", encoding="utf-8")
    (r / "app.py").write_text("x = 1\n", encoding="utf-8")
    git(r, "add", "-A")
    git(r, "commit", "-qm", "base")
    git(r, "branch", "-M", "main")
    return r


def pr_hash(repo) -> str:
    """The CI recompute: the raw branch diff minus the routing's hash exclusions."""
    spec = ["--", "."] + [f":(exclude){p}" for p in ROUTING["hash_exclude_paths"]]
    raw = subprocess.run(
        ["git", "diff", "--raw", "--no-renames", "--no-abbrev", "main...HEAD", *spec],
        cwd=repo, capture_output=True, check=True).stdout
    return hashlib.sha256(raw).hexdigest()


def build_task(repo, branch: str, task_id: str, code: str) -> None:
    """A finished task on its own branch: code and contract, then the review bound to them."""
    git(repo, "checkout", "-q", "-b", branch, "main")
    folder = repo / ".claude" / "task" / task_id
    folder.mkdir(parents=True)
    (repo / code).write_text(f"x = '{task_id}'\n", encoding="utf-8")
    (folder / "contract.md").write_text(CONTRACT.format(code=code), encoding="utf-8")
    (folder / "review_input.patch").write_text("patch\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", f"{task_id} code")
    (folder / "review.md").write_text(REVIEW.format(sha=pr_hash(repo)), encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", f"{task_id} verdicts")


def ci(repo) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(CI_SCRIPT), "--base", "main"], cwd=repo,
                       capture_output=True, text=True, env=env(repo))
    return r.returncode, r.stdout + r.stderr


def edit(repo, rel: str, base: str | None = "main") -> str:
    event = {"hook_event_name": "PreToolUse", "tool_name": "Write",
             "tool_input": {"file_path": str(repo / rel)}}
    r = subprocess.run([sys.executable, str(HOOKS / "task_contract_gate.py")],
                       input=json.dumps(event), capture_output=True, text=True,
                       cwd=repo, env=env(repo, base))
    return r.stdout


def denied(out: str) -> bool:
    return '"permissionDecision": "deny"' in out


@pytest.fixture()
def hooks(monkeypatch):
    monkeypatch.syspath_prepend(str(HOOKS))
    monkeypatch.setenv("GOVERNANCE_BASE", "main")
    import git_discipline
    import task_contract_gate
    return task_contract_gate, git_discipline


def merges_cleanly(repo, first: str, second: str) -> bool:
    git(repo, "checkout", "-q", "-B", f"trial-{first}-{second}", "main")
    for branch in (first, second):
        if git(repo, "merge", "-q", "--no-ff", "-m", f"merge {branch}", branch,
               check=False).returncode != 0:
            git(repo, "merge", "--abort", check=False)
            return False
    return True


# --------------------------------------------------------------------------- #
# Two tasks side by side
# --------------------------------------------------------------------------- #

def test_two_tasks_each_resolve_their_own_folder_and_pass_ci(repo, hooks):
    tcg, _ = hooks
    build_task(repo, "task-a", "10-alpha", "a.py")
    build_task(repo, "task-b", "20-beta", "b.py")
    for branch, task_id in (("task-a", "10-alpha"), ("task-b", "20-beta")):
        git(repo, "checkout", "-q", branch)
        assert tcg.task_folder(str(repo), "main") == {
            "folder": f".claude/task/{task_id}/", "errors": []}
        code, out = ci(repo)
        assert code == 0, out


def test_two_tasks_merge_in_either_order_without_conflict(repo):
    build_task(repo, "task-a", "10-alpha", "a.py")
    build_task(repo, "task-b", "20-beta", "b.py")
    assert merges_cleanly(repo, "task-a", "task-b")
    assert merges_cleanly(repo, "task-b", "task-a")


def test_second_task_still_passes_after_the_first_merges(repo, hooks):
    tcg, _ = hooks
    build_task(repo, "task-a", "10-alpha", "a.py")
    build_task(repo, "task-b", "20-beta", "b.py")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--no-ff", "-m", "merge a", "task-a")
    git(repo, "checkout", "-q", "task-b")
    assert tcg.task_folder(str(repo), "main")["folder"] == ".claude/task/20-beta/"
    code, out = ci(repo)
    assert code == 0, out


# --------------------------------------------------------------------------- #
# A missing folder
# --------------------------------------------------------------------------- #

def test_code_change_without_a_task_folder_is_refused(repo, hooks):
    _, gd = hooks
    git(repo, "checkout", "-q", "-b", "no-task", "main")
    assert denied(edit(repo, "app.py"))
    (repo / "app.py").write_text("x = 2\n", encoding="utf-8")
    git(repo, "add", "-A")
    reason = gd._commit_gate(str(repo))
    assert reason and "no task folder" in reason
    git(repo, "commit", "-qm", "code")
    code, out = ci(repo)
    assert code == 1 and "touches no task folder" in out


def test_the_first_file_of_a_new_task_folder_is_allowed(repo):
    git(repo, "checkout", "-q", "-b", "new-task", "main")
    assert edit(repo, ".claude/task/30-gamma/contract.md").strip() == ""


# --------------------------------------------------------------------------- #
# Another task's folder
# --------------------------------------------------------------------------- #

def test_touching_a_merged_tasks_folder_is_refused(repo):
    build_task(repo, "task-a", "10-alpha", "a.py")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--no-ff", "-m", "merge a", "task-a")
    git(repo, "checkout", "-q", "-b", "task-c", "main")
    assert denied(edit(repo, ".claude/task/10-alpha/review.md"))
    (repo / ".claude" / "task" / "10-alpha" / "review.md").write_text("rebound\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "touch a merged task")
    code, out = ci(repo)
    assert code == 1 and "merged task's folder" in out


def test_a_second_task_folder_on_one_branch_is_refused(repo):
    build_task(repo, "task-a", "10-alpha", "a.py")
    assert denied(edit(repo, ".claude/task/40-delta/notes.md"))
    (repo / ".claude" / "task" / "40-delta").mkdir()
    (repo / ".claude" / "task" / "40-delta" / "notes.md").write_text("x\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "second folder")
    code, out = ci(repo)
    assert code == 1 and "exactly one task folder" in out


def test_a_folder_name_without_an_issue_number_is_refused(repo):
    git(repo, "checkout", "-q", "-b", "bad-name", "main")
    assert denied(edit(repo, ".claude/task/notes/contract.md"))


def test_the_old_shared_files_may_be_deleted_but_not_written(repo, hooks):
    tcg, _ = hooks
    git(repo, "checkout", "-q", "-b", "legacy", "main")
    assert denied(edit(repo, ".claude/task/contract.md"))
    assert edit(repo, ".claude/task/TEMPLATE.md").strip() == ""
    build_task(repo, "task-e", "50-epsilon", "e.py")
    git(repo, "rm", "-q", ".claude/task/contract.md")
    git(repo, "commit", "-qm", "drop the old shared contract")
    assert tcg.task_folder(str(repo), "main") == {
        "folder": ".claude/task/50-epsilon/", "errors": []}
    (repo / ".claude" / "task" / "contract.md").write_text("back\n", encoding="utf-8")
    assert any("old shared layout" in e for e in tcg.task_folder(str(repo), "main")["errors"])


def shell(repo, cmd: str) -> str:
    event = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
             "tool_input": {"command": cmd}, "cwd": str(repo)}
    r = subprocess.run([sys.executable, str(HOOKS / "task_contract_gate.py")],
                       input=json.dumps(event), capture_output=True, text=True,
                       cwd=repo, env=env(repo))
    return r.stdout


def test_a_shell_write_into_the_own_folder_is_allowed_and_elsewhere_refused(repo):
    build_task(repo, "task-a", "10-alpha", "a.py")
    assert shell(repo, "echo x > .claude/task/10-alpha/review_input.patch").strip() == ""
    assert denied(shell(repo, "echo x > .claude/task/40-delta/notes.md"))
    assert denied(shell(repo, "echo x > .claude/task/review.md"))


def _merged_folder_staged(repo):
    build_task(repo, "task-a", "10-alpha", "a.py")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--no-ff", "-m", "merge a", "task-a")
    git(repo, "checkout", "-q", "-b", "task-c", "main")
    (repo / ".claude" / "task" / "10-alpha" / "review.md").write_text("rebound\n", encoding="utf-8")


def _second_folder_staged(repo):
    build_task(repo, "task-a", "10-alpha", "a.py")
    (repo / ".claude" / "task" / "40-delta").mkdir()
    (repo / ".claude" / "task" / "40-delta" / "notes.md").write_text("x\n", encoding="utf-8")


def _old_file_staged(repo):
    git(repo, "checkout", "-q", "-b", "legacy", "main")
    (repo / ".claude" / "task" / "contract.md").write_text("rewritten\n", encoding="utf-8")


@pytest.mark.parametrize("arrange, reason", [
    (_merged_folder_staged, "merged task's folder"),
    (_second_folder_staged, "exactly one task folder"),
    (_old_file_staged, "old shared layout"),
])
def test_the_commit_gate_refuses_a_bookkeeping_commit_that_breaks_the_rule(
        repo, hooks, arrange, reason):
    _, gd = hooks
    arrange(repo)
    git(repo, "add", "-A")
    denial = gd._commit_gate(str(repo))
    assert denial and denial.startswith("TASK FOLDER GATE") and reason in denial


def test_a_per_folder_pattern_excludes_exactly_what_the_literal_path_did(repo):
    build_task(repo, "task-a", "10-alpha", "a.py")
    literal = [p.replace(".claude/task/*/", ".claude/task/10-alpha/")
               for p in ROUTING["hash_exclude_paths"]]

    def raw(excludes):
        spec = ["--", "."] + [f":(exclude){p}" for p in excludes]
        return subprocess.run(["git", "diff", "--raw", "--no-renames", "--no-abbrev",
                               "main...HEAD", *spec], cwd=repo, capture_output=True,
                              check=True).stdout

    assert raw(ROUTING["hash_exclude_paths"]) == raw(literal)
    assert b"10-alpha/review.md" not in raw(ROUTING["hash_exclude_paths"])
    assert b"10-alpha/contract.md" in raw(ROUTING["hash_exclude_paths"])


# --------------------------------------------------------------------------- #
# Main merged into a branch
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("linked", [False, True], ids=["governance-base", "linked-worktree"])
def test_a_branch_that_merges_main_through_a_conflict_passes_the_gate(
        repo, hooks, monkeypatch, linked):
    tcg, gd = hooks
    build_task(repo, "task-b", "20-beta", "app.py")
    build_task(repo, "task-a", "10-alpha", "app.py")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--no-ff", "-m", "merge a", "task-a")
    (repo / "other.py").write_text("y = 1\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "other work on main")
    base = "main"
    if linked:
        git(repo, "update-ref", "refs/remotes/origin/main", "main")
        git(repo, "checkout", "-q", "--detach")
        work = repo.parent / "wt"
        git(repo, "worktree", "add", "-q", str(work), "task-b")
        monkeypatch.delenv("GOVERNANCE_BASE")
        base = None
    else:
        work = repo
        git(repo, "checkout", "-q", "task-b")
    assert git(work, "merge", "main", check=False).returncode != 0
    own = {"folder": ".claude/task/20-beta/", "errors": []}
    assert tcg.task_folder(str(work)) == own
    assert tcg.task_folder(str(work), "main") == own
    unresolved = tcg.task_folder(str(work), "no-such-ref")
    assert unresolved["folder"] is None and "merge is in progress" in unresolved["errors"][0]
    assert tcg._dirty_outside_task_dir(str(work)) == ["app.py"]
    assert not denied(edit(work, "app.py", base))
    (work / "app.py").write_text("x = '20-beta'\n", encoding="utf-8")
    git(work, "add", "app.py")
    sha = hashlib.sha256(gd._staged_diff_bytes(str(work))).hexdigest()
    (work / ".claude" / "task" / "20-beta" / "review.md").write_text(
        REVIEW.format(sha=sha), encoding="utf-8")
    git(work, "add", "-A")
    assert gd._staged_paths(str(work)) == [".claude/task/20-beta/contract.md",
                                           ".claude/task/20-beta/review.md",
                                           ".claude/task/20-beta/review_input.patch", "app.py"]
    assert gd._commit_gate(str(work)) is None
    git(work, "commit", "-q", "--no-edit")
    assert pr_hash(work) == sha
    code, out = ci(work)
    assert code == 0, out
