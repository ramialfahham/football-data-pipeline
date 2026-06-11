"""Offline tests for the governance hooks (G2): task_contract_gate, stop_gate,
git_discipline flag denies. Each test drives the hook script as Claude Code does
— event JSON on stdin, CLAUDE_PROJECT_DIR env — against a throwaway git repo.
No BigQuery, no network.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

HOOKS = os.path.join(os.path.dirname(__file__), "..", ".claude", "hooks")

CONTRACT = """# Task contract — test
objective: >
  test
refs: test

scope_paths:
  - dbt_project/models/allowed.sql
  - docs/allowed_dir/

decisions_taken: >
  test
decisions_reserved:
  - none
done_when:
  - test
amendments: (none)
"""

CONTRACT_OVERRIDE = CONTRACT.replace(
    "decisions_taken:",
    'protected_override: >\n  CPO approval test\ndecisions_taken:',
).replace(
    "scope_paths:\n", "scope_paths:\n  - .claude/hooks/some_hook.py\n"
)


def run_hook(script: str, event: dict, repo: str) -> tuple[str, str]:
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, script)],
        input=json.dumps(event), capture_output=True, text=True, env=env,
        cwd=str(repo), timeout=60,
    )
    return r.stdout, r.stderr


def edit_event(repo: str, rel: str, tool: str = "Edit") -> dict:
    return {"hook_event_name": "PreToolUse", "tool_name": tool,
            "tool_input": {"file_path": os.path.join(str(repo), rel)}}


def bash_event(cmd: str, hook_event: str = "PreToolUse") -> dict:
    return {"hook_event_name": hook_event, "tool_name": "Bash",
            "tool_input": {"command": cmd}}


def denied(out: str) -> bool:
    return '"permissionDecision": "deny"' in out


@pytest.fixture()
def repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / ".claude" / "task").mkdir(parents=True)
    (tmp_path / "dbt_project" / "models").mkdir(parents=True)
    (tmp_path / "dbt_project" / "models" / "allowed.sql").write_text("select 1")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=tmp_path, check=True)
    return tmp_path


def write_contract(repo, text: str = CONTRACT) -> None:
    (repo / ".claude" / "task" / "contract.md").write_text(text)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "contract"], cwd=repo, check=True)


# --------------------------------------------------------------------------- #
# task_contract_gate — file edits
# --------------------------------------------------------------------------- #
def test_no_contract_denies_repo_edit(repo):
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "dbt_project/models/allowed.sql"), repo)
    assert denied(out) and "no task contract" in out


def test_in_scope_edit_allowed(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "dbt_project/models/allowed.sql"), repo)
    assert out.strip() == ""


def test_scope_dir_glob_allows_children(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "docs/allowed_dir/page.md"), repo)
    assert out.strip() == ""


def test_out_of_scope_edit_denied(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "dbt_project/models/other.sql", "Write"), repo)
    assert denied(out) and "OUTSIDE the contract" in out


def test_outside_repo_path_ungoverned(repo):
    write_contract(repo)
    ev = {"hook_event_name": "PreToolUse", "tool_name": "Edit",
          "tool_input": {"file_path": os.path.join(str(repo), "..", "elsewhere.md")}}
    out, _ = run_hook("task_contract_gate.py", ev, repo)
    assert out.strip() == ""


def test_task_dir_always_allowed(repo):
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, ".claude/task/review.md"), repo)
    assert out.strip() == ""


def test_protected_path_denied_without_override(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, ".claude/hooks/some_hook.py"), repo)
    assert denied(out) and "PROTECTED" in out


def test_protected_path_allowed_with_override(repo):
    write_contract(repo, CONTRACT_OVERRIDE)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, ".claude/hooks/some_hook.py"), repo)
    assert not denied(out) and "protected_override" in out


def test_contract_amendment_denied_on_dirty_tree(repo):
    write_contract(repo)
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 2")
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, ".claude/task/contract.md"), repo)
    assert denied(out) and "CLEAN" in out


def test_contract_amendment_allowed_on_clean_tree(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, ".claude/task/contract.md"), repo)
    assert out.strip() == ""


# --------------------------------------------------------------------------- #
# task_contract_gate — shell coverage
# --------------------------------------------------------------------------- #
def test_shell_redirect_to_repo_file_denied(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", bash_event("echo x > dbt_project/models/other.sql"), repo)
    assert denied(out)


def test_shell_redirect_in_scope_allowed(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", bash_event("echo x >> dbt_project/models/allowed.sql"), repo)
    assert out.strip() == ""


def test_quoted_gt_is_not_a_redirect(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py",
                      bash_event('bq query --format=csv "select countif(x > 0.001) from t"'), repo)
    assert out.strip() == ""


def test_script_heredoc_denied(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", bash_event("python - <<'EOF'\nprint(1)\nEOF"), repo)
    assert denied(out) and "heredoc" in out


def test_sed_inplace_out_of_scope_denied(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", bash_event("sed -i 's/a/b/' dbt_project/models/other.sql"), repo)
    assert denied(out)


def test_redirect_outside_repo_allowed(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", bash_event("ls > /tmp/listing.txt"), repo)
    assert out.strip() == ""


def test_post_bash_flags_out_of_scope_changes(repo):
    write_contract(repo)
    (repo / "stray.md").write_text("drift")
    out, _ = run_hook("task_contract_gate.py", bash_event("echo done", "PostToolUse"), repo)
    assert "CONTRACT GATE VIOLATION" in out and "stray.md" in out


def test_post_bash_quiet_when_clean(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", bash_event("echo done", "PostToolUse"), repo)
    assert out.strip() == ""


# --------------------------------------------------------------------------- #
# stop_gate
# --------------------------------------------------------------------------- #
def test_stop_blocked_on_out_of_scope_changes(repo):
    write_contract(repo)
    (repo / "stray.md").write_text("drift")
    out, _ = run_hook("stop_gate.py", {"hook_event_name": "Stop"}, repo)
    assert '"decision": "block"' in out and "stray.md" in out


def test_stop_allowed_when_clean(repo):
    write_contract(repo)
    out, _ = run_hook("stop_gate.py", {"hook_event_name": "Stop"}, repo)
    assert out.strip() == ""


def test_stop_never_loops(repo):
    write_contract(repo)
    (repo / "stray.md").write_text("drift")
    out, _ = run_hook("stop_gate.py", {"hook_event_name": "Stop", "stop_hook_active": True}, repo)
    assert out.strip() == ""


# --------------------------------------------------------------------------- #
# git_discipline — flag denies
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("cmd", [
    "git commit --amend",
    "git commit --no-verify -m x",
    "git commit -n -m x",
    "git config core.hooksPath /tmp/x",
])
def test_forbidden_git_commands_denied(repo, cmd):
    out, _ = run_hook("git_discipline.py", bash_event(cmd), repo)
    assert denied(out)


def test_commit_message_mentioning_flags_not_denied(repo):
    cmd = 'git commit -m "docs: explain why --amend and --no-verify are blocked"'
    out, _ = run_hook("git_discipline.py", bash_event(cmd), repo)
    assert not denied(out)


def test_normal_commit_not_denied(repo):
    out, _ = run_hook("git_discipline.py", bash_event('git commit -m "feat: x"'), repo)
    assert not denied(out)
