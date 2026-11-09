"""The governance hooks judge the worktree an action targets, not CLAUDE_PROJECT_DIR.

A main checkout and a real `git worktree add` under `.claude/worktrees/` carry different
contracts. CLAUDE_PROJECT_DIR always names the main checkout, the way it does for a session
opened there that works in a worktree.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

HOOKS = os.path.join(os.path.dirname(__file__), "..", ".claude", "hooks")

ROUTING = {
    "always": ["scope-auditor"],
    "paths": {},
    "artifact_only": [".claude/task/**"],
    "artifact_only_never": [".claude/task/*/contract.md"],
    "hash_exclude_paths": [".claude/task/*/review.md", ".claude/task/*/review_input.patch"],
    "review_exclude_paths": [".claude/task/*/review.md", ".claude/task/*/review_input.patch"],
}


def _contract(scoped: str) -> str:
    return (
        "# Task contract — test\nobjective: >\n  test\nrefs: test\n\n"
        f"scope_paths:\n  - {scoped}\n\n"
        "decisions_taken: >\n  test\ndecisions_reserved:\n  - none\n"
        "done_when:\n  - test\namendments: (none)\n"
    )


def _git(cwd, *args) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True)


def _commit_all(cwd, msg: str) -> None:
    _git(cwd, "add", "-A")
    _git(cwd, "commit", "-qm", msg)


@pytest.fixture()
def trees(tmp_path):
    main = tmp_path / "main"
    (main / ".claude" / "task" / "1-main").mkdir(parents=True)
    (main / "notes").mkdir()
    _git(main, "init", "-q", "-b", "main")
    _git(main, "config", "user.email", "t@t")
    _git(main, "config", "user.name", "t")
    (main / ".gitignore").write_text(".claude/worktrees/\n.venv/\n")
    (main / ".claude" / "review_routing.json").write_text(json.dumps(ROUTING))
    (main / "notes" / "a.txt").write_text("a")
    (main / "notes" / "b.txt").write_text("b")
    _commit_all(main, "init")
    wt = main / ".claude" / "worktrees" / "w"
    _git(main, "worktree", "add", "-q", "-b", "feature", str(wt))
    (wt / ".claude" / "task" / "2-wt").mkdir(parents=True)
    (wt / ".claude" / "task" / "2-wt" / "contract.md").write_text(_contract("notes/b.txt"))
    _commit_all(wt, "worktree contract")
    (main / ".claude" / "task" / "1-main" / "contract.md").write_text(_contract("notes/a.txt"))
    return main, wt


def run_hook(script: str, event: dict, project_dir, env_extra: dict | None = None):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project_dir), **(env_extra or {}))
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, script)],
        input=json.dumps(event), capture_output=True, text=True, env=env,
        cwd=str(project_dir), timeout=60,
    )
    return r.stdout


def edit(path) -> dict:
    return {"hook_event_name": "PreToolUse", "tool_name": "Edit",
            "tool_input": {"file_path": str(path)}}


def bash(cmd: str, cwd=None, hook_event: str = "PreToolUse") -> dict:
    event = {"hook_event_name": hook_event, "tool_name": "Bash", "tool_input": {"command": cmd}}
    if cwd is not None:
        event["cwd"] = str(cwd)
    return event


def denied(out: str) -> bool:
    return '"permissionDecision": "deny"' in out


def test_each_edit_is_judged_by_its_own_worktree_contract(trees):
    main, wt = trees
    assert not denied(run_hook("task_contract_gate.py", edit(wt / "notes" / "b.txt"), main))
    out = run_hook("task_contract_gate.py", edit(wt / "notes" / "a.txt"), main)
    assert denied(out) and "notes/a.txt" in out


def test_an_edit_inside_the_main_checkout_is_judged_as_before(trees):
    main, _ = trees
    assert not denied(run_hook("task_contract_gate.py", edit(main / "notes" / "a.txt"), main))
    out = run_hook("task_contract_gate.py", edit(main / "notes" / "b.txt"), main)
    assert denied(out) and "notes/b.txt" in out


def test_a_shell_write_is_judged_by_the_worktree_it_runs_in(trees):
    main, wt = trees
    assert not denied(run_hook("task_contract_gate.py", bash("echo x > notes/b.txt", wt), main))
    assert denied(run_hook("task_contract_gate.py", bash("echo x > notes/a.txt", wt), main))


def test_a_shell_write_into_the_main_checkout_from_a_worktree_is_judged_by_main(trees):
    main, wt = trees
    out = run_hook("task_contract_gate.py", bash(f"echo x > {(main / 'notes' / 'b.txt').as_posix()}", wt), main)
    assert denied(out) and "notes/b.txt" in out


def test_a_shell_write_into_the_main_git_dir_from_a_worktree_is_judged_by_main(trees):
    main, wt = trees
    out = run_hook("task_contract_gate.py", bash(f"echo x >> {(main / '.git' / 'config').as_posix()}", wt), main)
    assert denied(out) and ".git/config" in out


def test_without_a_cwd_the_shell_write_falls_back_to_the_project_dir(trees):
    main, _ = trees
    assert denied(run_hook("task_contract_gate.py", bash("echo x > notes/b.txt"), main))


def test_a_cwd_outside_any_repo_falls_back_to_the_project_dir(trees, tmp_path):
    main, _ = trees
    outside = tmp_path / "outside"
    outside.mkdir()
    assert denied(run_hook("task_contract_gate.py", bash("echo x > notes/b.txt", outside), main))


def test_a_file_outside_any_repo_is_not_judged(trees, tmp_path):
    main, _ = trees
    outside = tmp_path / "outside" / "note.md"
    outside.parent.mkdir()
    assert not denied(run_hook("task_contract_gate.py", edit(outside), main))


def test_a_file_in_an_unrelated_repo_is_not_judged(trees, tmp_path):
    main, _ = trees
    other = tmp_path / "other"
    other.mkdir()
    _git(other, "init", "-q")
    assert not denied(run_hook("task_contract_gate.py", edit(other / "x.txt"), main))


def test_a_nested_git_init_does_not_exempt_a_protected_folder(trees):
    main, _ = trees
    hooks = main / ".claude" / "hooks"
    hooks.mkdir()
    _git(hooks, "init", "-q")
    out = run_hook("task_contract_gate.py", edit(hooks / "task_contract_gate.py"), main)
    assert denied(out) and ".claude/hooks/task_contract_gate.py" in out


def test_where_git_cannot_answer_the_project_dir_still_judges(trees):
    main, _ = trees
    out = run_hook("task_contract_gate.py", edit(main / ".git" / "info" / "x.txt"), main)
    assert denied(out) and ".git/info/x.txt" in out


def test_the_commit_gate_reads_the_worktree_it_runs_in(trees):
    main, wt = trees
    (wt / "notes" / "b.txt").write_text("changed")
    _git(wt, "add", "notes/b.txt")
    out = run_hook("git_discipline.py", bash('git commit -m "x"', wt), main)
    assert denied(out) and "no review artifact" in out


def test_staged_hash_hashes_the_worktree_it_runs_in(trees):
    main, wt = trees
    (wt / "notes" / "b.txt").write_text("changed")
    _git(wt, "add", "notes/b.txt")

    def staged_hash(project_dir) -> str:
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project_dir), GOVERNANCE_BASE="main")
        r = subprocess.run(
            [sys.executable, os.path.join(HOOKS, "git_discipline.py"), "--staged-hash"],
            capture_output=True, text=True, env=env, cwd=str(wt), timeout=60,
        )
        assert r.returncode == 0, r.stderr
        return r.stdout.strip()

    assert staged_hash(main) == staged_hash(wt)


def test_the_stop_gate_judges_the_worktree_it_runs_in(trees):
    main, wt = trees
    (main / "stray.txt").write_text("drift")
    stop = {"hook_event_name": "Stop", "cwd": str(wt)}
    assert '"decision": "block"' not in run_hook("stop_gate.py", stop, main)
    (wt / "stray.txt").write_text("drift")
    out = run_hook("stop_gate.py", stop, main)
    assert '"decision": "block"' in out and "stray.txt" in out


def test_a_worktree_without_a_venv_runs_the_gates_with_the_main_checkouts(trees):
    import venv

    main, wt = trees
    venv.create(main / ".venv", with_pip=False)
    (wt / "scripts").mkdir()
    (wt / "scripts" / "check_layer_contract.py").write_text(
        "import os, sys\n"
        f"venv = os.path.realpath({str(main / '.venv')!r})\n"
        "if os.path.normcase(os.path.realpath(sys.prefix)) != os.path.normcase(venv):\n"
        "    print('- ran outside the main checkout .venv')\n"
        "    sys.exit(1)\n"
    )
    _commit_all(wt, "fast gate stub")
    (wt / "notes" / "b.txt").write_text("changed")
    out = run_hook("stop_gate.py", {"hook_event_name": "Stop", "cwd": str(wt)}, wt)
    assert out.strip() == "", out


def test_the_tracker_gate_judges_the_worktree_file(trees):
    main, wt = trees
    assert denied(run_hook("tracker_snapshot_gate.py", edit(wt / "docs" / "tracker" / "x.md"), main))


def write(path, content: str) -> dict:
    return {"hook_event_name": "PreToolUse", "tool_name": "Write",
            "tool_input": {"file_path": str(path), "content": content}}


def test_the_comment_history_gate_judges_the_worktree_file(trees):
    main, wt = trees
    line = "x = 1  " + chr(35) + " see " + "!" + "132\n"
    assert denied(run_hook("comment_history_gate.py", write(wt / "scripts" / "x.py", line), main))


@pytest.fixture()
def sibling(trees, tmp_path):
    main, _ = trees
    path = tmp_path / "sibling"
    _git(main, "worktree", "add", "-q", "-b", "sibling", str(path))
    return path


def test_the_sentence_length_gate_judges_a_sibling_worktree_file(trees, sibling):
    main, _ = trees
    sentence = " ".join(["word"] * 26) + ".\n"
    assert denied(run_hook("sentence_length_gate.py", write(sibling / "docs" / "a.md", sentence), main))


def test_the_host_fingerprint_gate_judges_a_sibling_worktree_file(trees, sibling):
    main, _ = trees
    address = ".".join(["203", "0", "113", "7"])
    out = run_hook("host_fingerprint_gate.py", write(sibling / "docs" / "a.md", f"at {address}\n"), main)
    assert denied(out) and "docs/a.md" in out
