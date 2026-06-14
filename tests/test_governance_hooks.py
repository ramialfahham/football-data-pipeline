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


# --------------------------------------------------------------------------- #
# git_discipline — the review/commit gate (G3)
# --------------------------------------------------------------------------- #
ROUTING = {
    "always": ["scope-auditor"],
    "paths": {"dbt_project/**": ["analytics-engineer-reviewer"]},
    "artifact_only": [".claude/task/**", ".claude/active_work.md"],
    "artifact_only_never": [".claude/task/contract.md"],
    "hash_exclude_paths": [
        ".claude/task/review.md",
        ".claude/task/review_input.patch",
        ".claude/task/escalations.log",
        ".claude/active_work.md",
    ],
}


def setup_review_repo(repo, stage_path="dbt_project/models/allowed.sql"):
    (repo / ".claude" / "review_routing.json").write_text(json.dumps(ROUTING))
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "routing"], cwd=repo, check=True)
    target = repo / stage_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("select 99")
    subprocess.run(["git", "add", str(target)], cwd=repo, check=True)


def staged_hash(repo) -> str:
    # Compute via the hook's own --staged-hash so the test's expected value always
    # equals what the commit gate computes (F11: excludes bookkeeping, --no-renames).
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "git_discipline.py"), "--staged-hash"],
        cwd=str(repo), capture_output=True, text=True, env=env, timeout=60,
    )
    return r.stdout.strip()


def write_review(repo, hash_hex, body):
    (repo / ".claude" / "task" / "review.md").write_text(
        f"# Review\ndiff_sha256: {hash_hex}\n\n{body}\n"
    )


GOOD_BODY = """## scope-auditor
VERDICT: PASS
risks_checked:
- risk one checked
- risk two checked

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- risk one checked
- risk two checked
"""

COMMIT_CMD = 'git commit -m "feat: x"'


def test_commit_denied_without_review_artifact(repo):
    setup_review_repo(repo)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "no review artifact" in out


def test_commit_denied_on_hash_mismatch(repo):
    setup_review_repo(repo)
    write_review(repo, "0" * 64, GOOD_BODY)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "hash mismatch" in out


def test_commit_denied_on_fail_verdict(repo):
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY.replace(
        "## analytics-engineer-reviewer\nVERDICT: PASS",
        "## analytics-engineer-reviewer\nVERDICT: FAIL"))
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "FAIL" in out


def test_commit_denied_on_unanswered_escalation(repo):
    setup_review_repo(repo)
    body = GOOD_BODY + "\n## escalations\n- question: x?\nVERDICT: ESCALATE\n"
    write_review(repo, staged_hash(repo), body)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "CPO ANSWER" in out


def test_commit_denied_when_required_reviewer_missing(repo):
    setup_review_repo(repo)
    body = GOOD_BODY.split("## analytics-engineer-reviewer")[0]
    write_review(repo, staged_hash(repo), body)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "analytics-engineer-reviewer" in out


def test_commit_denied_on_pass_without_two_risks(repo):
    setup_review_repo(repo)
    body = GOOD_BODY.replace("- risk two checked\n\n## analytics", "\n## analytics", 1)
    write_review(repo, staged_hash(repo), body)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "two named risks" in out


def test_bullets_before_risks_marker_do_not_satisfy_quota(repo):
    """Risks count anchors to the risks_checked: marker (CTO, round 3) —
    stray bullets above it must not pass for checked risks."""
    setup_review_repo(repo)
    body = GOOD_BODY.replace(
        "VERDICT: PASS\nrisks_checked:\n- risk one checked\n- risk two checked\n\n## analytics",
        "- stray bullet\n- another stray\nVERDICT: PASS\nrisks_checked:\n\n## analytics", 1)
    write_review(repo, staged_hash(repo), body)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "two named risks" in out


def test_commit_allowed_with_complete_review(repo):
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert not denied(out)


def test_artifact_only_commit_exempt_from_review(repo):
    setup_review_repo(repo)
    subprocess.run(["git", "reset"], cwd=repo, check=True, capture_output=True)
    (repo / ".claude" / "task" / "notes.md").write_text("bookkeeping")
    subprocess.run(["git", "add", ".claude/task/notes.md"], cwd=repo, check=True)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert not denied(out)


def test_contract_commit_not_artifact_exempt(repo):
    """F10/#409: a commit touching contract.md is NEVER artifact-exempt — it
    authorizes scope, so it must go through review (here: denied for lack of one)."""
    setup_review_repo(repo)
    subprocess.run(["git", "reset"], cwd=repo, check=True, capture_output=True)
    (repo / ".claude" / "task" / "contract.md").write_text("# contract\nscope_paths:\n  - x\n")
    subprocess.run(["git", "add", ".claude/task/contract.md"], cwd=repo, check=True)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "no review artifact" in out


def test_hash_excludes_bookkeeping_but_binds_contract(repo):
    """F11/#409: the review hash covers code + contract.md, not bookkeeping artifacts."""
    setup_review_repo(repo)  # stages dbt_project/models/allowed.sql
    h_code = staged_hash(repo)
    assert h_code  # non-empty
    # adding a bookkeeping artifact does NOT change the hash (excluded)
    (repo / ".claude" / "task" / "escalations.log").write_text("log entry")
    subprocess.run(["git", "add", ".claude/task/escalations.log"], cwd=repo, check=True)
    assert staged_hash(repo) == h_code
    # adding contract.md DOES change the hash (it is bound to the review)
    (repo / ".claude" / "task" / "contract.md").write_text("# contract\n")
    subprocess.run(["git", "add", ".claude/task/contract.md"], cwd=repo, check=True)
    assert staged_hash(repo) != h_code


def test_escalation_with_answer_allows_commit(repo):
    setup_review_repo(repo)
    body = GOOD_BODY + (
        "\n## escalations\nVERDICT: ESCALATE\n- question: x?\n  CPO ANSWER: do y\n"
    )
    write_review(repo, staged_hash(repo), body)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert not denied(out)


def test_answer_elsewhere_does_not_mask_unanswered_escalation(repo):
    setup_review_repo(repo)
    body = GOOD_BODY + (
        "\n## escalations\nVERDICT: ESCALATE\n- question: x?\n"
        "\n## notes\nCPO ANSWER: for something else entirely\n"
    )
    write_review(repo, staged_hash(repo), body)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "escalations" in out


def test_preamble_escalation_not_masked(repo):
    """An ESCALATE before the first ## header belongs to the _preamble
    pseudo-section and must pair there (CTO finding, round 4)."""
    setup_review_repo(repo)
    body = (
        "VERDICT: ESCALATE\n- question: x?\n\n" + GOOD_BODY +
        "\n## notes\nCPO ANSWER: for something else entirely\n"
    )
    write_review(repo, staged_hash(repo), body)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "_preamble" in out


@pytest.mark.parametrize("cmd", [
    'git add extra.txt && git commit -m "sneak"',
    'echo x; git commit -m "sneak"',
    'git commit -m "ok" && git push origin main',
])
def test_commit_chained_with_sibling_commands_denied(repo, cmd):
    """The hash is verified at PreToolUse time; sibling commands in the same
    call could restage content before the commit runs (CTO finding, round 4).
    `git commit` must be the sole command in the Bash call."""
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY)
    out, _ = run_hook("git_discipline.py", bash_event(cmd), repo)
    assert denied(out) and "SOLE" in out


@pytest.mark.parametrize("cmd", [
    'git commit -am "sneak"',
    'git commit -a -m "sneak"',
    'git commit --all -m "sneak"',
    'git commit -i extra.txt -m "sneak"',
    'git commit --only thing.sql -m "sneak"',
    'git commit dbt_project/models/allowed.sql -m "sneak"',
    'git commit -m "msg" -- some/path.sql',
])
def test_selfstaging_commit_forms_denied(repo, cmd):
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY)
    out, _ = run_hook("git_discipline.py", bash_event(cmd), repo)
    assert denied(out) and "COMMIT FORM BLOCKED" in out


def test_plain_commit_with_quoted_message_not_form_blocked(repo):
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY)
    out, _ = run_hook(
        "git_discipline.py",
        bash_event('git commit -m "feat: mentions -a and files.sql in text"'), repo)
    assert not denied(out)


@pytest.mark.parametrize("cmd", [
    'git commit -qam "sneak"',                       # POSIX short-option bundle
    'git commit -sam "sneak"',
    'git commit --inc -m "sneak"',                   # long-option prefix abbreviation
    'git commit -p -m "sneak"',                      # commit-time staging via patch
    'git commit --interactive',
    'git -C . commit -a -m "sneak"',                 # git global options before commit
    'git -c user.name=x commit --all -m "sneak"',
    'git --no-pager commit -am "sneak"',
    'git -p commit -am "sneak"',                     # valueless short global flag
    'git -P commit -am "sneak"',
    'git --git-dir .git commit -am "sneak"',         # space-separated global value
    'git --work-tree . commit -a -m "sneak"',
    'git commit -m "sneak" "dbt_project/models/allowed file.sql"',  # QUOTED pathspec
    'git commit -m "unclosed',                       # unparseable quoting: fail-closed
])
def test_bundled_abbreviated_and_global_option_forms_denied(repo, cmd):
    """Allowlist inversion (CTO findings, rounds 2-3): spellings a denylist
    regex misses must still be form-blocked — only exactly `git commit`
    enters the gate's allowed path."""
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY)
    out, _ = run_hook("git_discipline.py", bash_event(cmd), repo)
    assert denied(out) and "COMMIT FORM BLOCKED" in out


@pytest.mark.parametrize("cmd", [
    'git commit -m "feat: x" -q',
    'git commit --message="feat: x" -S',
    'git commit -v -m "feat: x"',
    'git commit -F notes.txt -q',
])
def test_allowed_commit_flag_set_not_form_blocked(repo, cmd):
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY)
    out, _ = run_hook("git_discipline.py", bash_event(cmd), repo)
    assert not denied(out)


def test_non_ascii_staged_path_still_requires_reviewer(repo):
    """quotePath-escaped paths must not drop a required reviewer (CTO,
    round 5): the -z enumeration keeps the path matchable by routing."""
    setup_review_repo(repo, stage_path="dbt_project/models/täst.sql")
    body = GOOD_BODY.split("## analytics-engineer-reviewer")[0]
    write_review(repo, staged_hash(repo), body)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "analytics-engineer-reviewer" in out


# --------------------------------------------------------------------------- #
# task_contract_gate — G3 additions
# --------------------------------------------------------------------------- #
def test_routing_file_is_protected(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, ".claude/review_routing.json"), repo)
    assert denied(out) and "PROTECTED" in out


def test_agents_dir_is_protected(repo):
    """Per the CPO's recorded G3 escalation answer (2026-06-12): reviewer
    definitions are governance artifacts — protected like the routing file."""
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, ".claude/agents/scope-auditor.md"), repo)
    assert denied(out) and "PROTECTED" in out


def test_commands_dir_is_protected(repo):
    """Per the CPO ruling 2026-06-14: custom slash commands can embed shell, so a
    command file is protected like a hook/agent definition."""
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, ".claude/commands/status.md"), repo)
    assert denied(out) and "PROTECTED" in out


def test_untracked_dir_files_in_scope_not_flagged(repo):
    """-uall: files inside an untracked directory are matched individually."""
    write_contract(repo, CONTRACT.replace(
        "scope_paths:\n", "scope_paths:\n  - newdir/\n"))
    (repo / "newdir").mkdir()
    (repo / "newdir" / "inside.md").write_text("in scope")
    out, _ = run_hook("task_contract_gate.py", bash_event("echo done", "PostToolUse"), repo)
    assert "VIOLATION" not in out


def test_untracked_dir_files_out_of_scope_flagged_by_file(repo):
    write_contract(repo)
    (repo / "newdir").mkdir()
    (repo / "newdir" / "stray.md").write_text("drift")
    out, _ = run_hook("task_contract_gate.py", bash_event("echo done", "PostToolUse"), repo)
    assert "VIOLATION" in out and "newdir/stray.md" in out


# --------------------------------------------------------------------------- #
# check_task_artifacts.py — the CI backstop (fail-closed)
# --------------------------------------------------------------------------- #
SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")


def run_ci_check(repo) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "check_task_artifacts.py"), "--base", "main"],
        capture_output=True, text=True, cwd=str(repo), timeout=60,
    )
    return r.returncode, r.stdout + r.stderr


def branch_hash(repo, base="main") -> str:
    """The F11 hash CI recomputes: sha256 of `git diff base...HEAD` excluding the
    bookkeeping artifacts (--no-renames), mirroring check_task_artifacts.py."""
    import hashlib
    excludes = ROUTING["hash_exclude_paths"]
    pathspec = ["--", "."] + [f":(exclude){p}" for p in excludes]
    diff = subprocess.run(
        ["git", "diff", "--no-renames", "--no-abbrev", f"{base}...HEAD"] + pathspec,
        cwd=repo, capture_output=True,
    ).stdout
    return hashlib.sha256(diff).hexdigest()


@pytest.fixture()
def ci_repo(repo):
    subprocess.run(["git", "branch", "-m", "main"], cwd=repo, check=True)
    (repo / ".claude" / "review_routing.json").write_text(json.dumps(ROUTING))
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", "feature"], cwd=repo, check=True)
    return repo


def test_ci_check_fails_without_review(ci_repo):
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "review.md" in out


def test_ci_check_passes_artifact_only_pr(ci_repo):
    (ci_repo / ".claude" / "task" / "notes.md").write_text("bookkeeping")
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "artifacts"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 0 and "artifact-only" in out


def test_ci_check_passes_with_complete_artifacts(ci_repo):
    # F11: review.md must carry the hash of the actual PR diff (code + contract,
    # bookkeeping excluded). Commit code+contract first, then write review.md with the
    # recomputed hash, then commit it — CI recomputes the same and passes.
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    (ci_repo / ".claude" / "task" / "contract.md").write_text(CONTRACT)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code+contract"], cwd=ci_repo, check=True)
    real_hash = branch_hash(ci_repo)
    (ci_repo / ".claude" / "task" / "review.md").write_text(
        "# Review\ndiff_sha256: " + real_hash + "\n\n" + GOOD_BODY
    )
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "review"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 0, out


def test_ci_check_contract_only_pr_not_artifact_exempt(ci_repo):
    """F10/#409: a contract-only PR is no longer artifact-exempt at CI — it must carry
    a review (here it doesn't, so CI fails). Closes the #407 contract-only-merge hole."""
    (ci_repo / ".claude" / "task" / "contract.md").write_text(CONTRACT)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "contract only"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "review.md" in out


def test_ci_check_fails_on_stale_review_hash(ci_repo):
    """F11/#409: a review.md whose hash does not match this PR's diff (the #405
    false-green) is now rejected by CI."""
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    (ci_repo / ".claude" / "task" / "contract.md").write_text(CONTRACT)
    (ci_repo / ".claude" / "task" / "review.md").write_text(
        "# Review\ndiff_sha256: " + "b" * 64 + "\n\n" + GOOD_BODY
    )
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "stale review"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "not bound to this PR" in out


def test_local_staged_hash_equals_ci_recompute(ci_repo):
    """F11/#409 — the LOAD-BEARING invariant: the local commit gate's --staged-hash
    (computed on the staged tree, pre-commit) must equal the CI recompute
    (`git diff base...HEAD`, post-commit). If this ever diverges, a locally-passing
    commit would be falsely rejected by CI. Exercises ALL three diff shapes:
    a MODIFIED base-resident file (allowed.sql — its index line carries a non-zero OLD
    blob, the one vector where pre/post-commit could diverge), a NEW file (contract.md),
    and a bookkeeping artifact that must be excluded (escalations.log)."""
    (ci_repo / "dbt_project" / "models" / "allowed.sql").write_text("select 7\n")  # MODIFY base file
    (ci_repo / ".claude" / "task" / "contract.md").write_text(CONTRACT)  # add
    (ci_repo / ".claude" / "task" / "escalations.log").write_text("noise\n")  # excluded
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    local = staged_hash(ci_repo)            # what the local gate checks
    subprocess.run(["git", "commit", "-qm", "code+contract"], cwd=ci_repo, check=True)
    ci = branch_hash(ci_repo)               # what CI recomputes
    assert local == ci, f"local {local} != ci {ci}"


def test_ci_check_fails_on_missing_required_reviewer(ci_repo):
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    (ci_repo / ".claude" / "task" / "contract.md").write_text(CONTRACT)
    body = GOOD_BODY.split("## analytics-engineer-reviewer")[0]
    (ci_repo / ".claude" / "task" / "review.md").write_text(
        "# Review\ndiff_sha256: " + "a" * 64 + "\n\n" + body
    )
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code+partial"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "analytics-engineer-reviewer" in out


def test_ci_check_requires_reviewer_for_non_ascii_path(ci_repo):
    """CI mirror of the -z enumeration fix (CTO finding, round 5)."""
    (ci_repo / "dbt_project" / "models" / "täst.sql").write_text(
        "select 1", encoding="utf-8")
    (ci_repo / ".claude" / "task" / "contract.md").write_text(CONTRACT)
    body = GOOD_BODY.split("## analytics-engineer-reviewer")[0]
    (ci_repo / ".claude" / "task" / "review.md").write_text(
        "# Review\ndiff_sha256: " + "a" * 64 + "\n\n" + body
    )
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "analytics-engineer-reviewer" in out


def test_ci_check_fails_on_preamble_escalation(ci_repo):
    """CI mirror of the _preamble pseudo-section rule (CTO finding, round 4)."""
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    (ci_repo / ".claude" / "task" / "contract.md").write_text(CONTRACT)
    body = (
        "VERDICT: ESCALATE\n- question: x?\n\n" + GOOD_BODY +
        "\n## notes\nCPO ANSWER: for something else entirely\n"
    )
    (ci_repo / ".claude" / "task" / "review.md").write_text(
        "# Review\ndiff_sha256: " + "a" * 64 + "\n\n" + body
    )
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code+artifacts"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "_preamble" in out


def test_ci_check_fails_on_per_section_unanswered_escalation(ci_repo):
    """Per-section pairing (scope-auditor finding, round 2): an answer in one
    section must not mask another section's unanswered ESCALATE — the global
    count alone would pass this body."""
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    (ci_repo / ".claude" / "task" / "contract.md").write_text(CONTRACT)
    body = GOOD_BODY + (
        "\n## escalations\nVERDICT: ESCALATE\n- question: x?\n"
        "\n## notes\nCPO ANSWER: for something else entirely\n"
    )
    (ci_repo / ".claude" / "task" / "review.md").write_text(
        "# Review\ndiff_sha256: " + "a" * 64 + "\n\n" + body
    )
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code+artifacts"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "escalations" in out
