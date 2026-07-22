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

CONTRACT_NO_IMPACT = """# Task contract — test
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

# The default CONTRACT carries an impact_map so structural-path tests (which edit
# dbt_project/models/allowed.sql) are allowed; the missing-map deny is exercised
# with CONTRACT_NO_IMPACT. (#518 / Appendix A6 — the impact-map gate.)
_IMPACT_BLOCK = (
    "impact_map: >\n"
    "  writers: loader_x. downstream (dbt ls --select allowed+): none (leaf).\n"
    "  layer_rules: staging partitions by league_code only.\n"
    "  deploy_order: rebuilds on next CI; no shared-warehouse break.\n"
    "  blast_radius: none (leaf mart).\n\n"
)
CONTRACT = CONTRACT_NO_IMPACT.replace(
    "decisions_taken:", _IMPACT_BLOCK + "decisions_taken:")

CONTRACT_OVERRIDE = CONTRACT.replace(
    "decisions_taken:",
    'protected_override: >\n  CPO approval test\ndecisions_taken:',
).replace(
    "scope_paths:\n", "scope_paths:\n  - .claude/hooks/some_hook.py\n"
)

# An override WITHOUT an impact_map. This fixture did not exist until 2026-07-22,
# and its absence is why the suite covered only the ALLOW direction of the
# protected-path gate: CONTRACT_OVERRIDE derives from CONTRACT, which already
# carries _IMPACT_BLOCK, so `test_protected_path_allowed_with_override` would
# have passed identically whether or not the map was ever checked. A one-sided
# test passes while broken (cto-reviewer, 2026-07-22).
CONTRACT_OVERRIDE_NO_IMPACT = CONTRACT_NO_IMPACT.replace(
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
# task_contract_gate — impact-map gate (structural surface, #518 / Appendix A6)
# --------------------------------------------------------------------------- #
def test_structural_edit_denied_without_impact_map(repo):
    write_contract(repo, CONTRACT_NO_IMPACT)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "dbt_project/models/allowed.sql"), repo)
    assert denied(out) and "impact_map" in out


def test_structural_edit_allowed_with_impact_map(repo):
    write_contract(repo)  # default CONTRACT carries an impact_map
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "dbt_project/models/allowed.sql"), repo)
    assert out.strip() == ""


def test_nonstructural_edit_allowed_without_impact_map(repo):
    write_contract(repo, CONTRACT_NO_IMPACT)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "docs/allowed_dir/page.md"), repo)
    assert out.strip() == ""


def test_ingestion_edit_denied_without_impact_map(repo):
    write_contract(repo, CONTRACT_NO_IMPACT.replace(
        "  - docs/allowed_dir/\n", "  - docs/allowed_dir/\n  - ingestion/\n"))
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "ingestion/loader.py", "Write"), repo)
    assert denied(out) and "impact_map" in out


@pytest.mark.parametrize("spelling", [
    "impact_map: {v}\n",              # inline
    "impact_map: >\n  {v}\n",         # block scalar
    "impact_map:\n  - {v}\n",         # dash list — the spelling the first fix missed,
])                                    # and the one every other key in the real contract uses
@pytest.mark.parametrize("value", [
    "none", "None", "N/A", "n/a", "TBD", "todo", "(none)",
])
def test_nullish_impact_map_does_not_satisfy(repo, value, spelling):
    """`impact_map: none` used to satisfy the requirement. The nullish set
    rejected `(none)` but not `none`, `n/a` or `TBD`, and did not case-fold — the
    same hole class fixed in the sibling helper a round earlier, left standing in
    the function this task makes load-bearing on every guard edit in the repo
    (cto-reviewer, 2026-07-22)."""
    write_contract(repo, CONTRACT_NO_IMPACT.replace(
        "decisions_taken:", spelling.format(v=value) + "decisions_taken:"))
    out, _ = run_hook("task_contract_gate.py",
                      edit_event(repo, "dbt_project/models/allowed.sql"), repo)
    assert denied(out) and "impact_map" in out


@pytest.mark.parametrize("header", [">-", "|-", ">+", "|+", "|2", "|2-"])
def test_block_scalar_header_impact_map_does_not_satisfy(repo, header):
    """A YAML chomping or indentation suffix used to walk straight through the
    nullish word list, which had `>` and `|` but not `>-`. Not contrived: this
    repo's own workflow files write `>-`. Matched by pattern now, because
    enumerating literals loses by one variant every round (cto-reviewer)."""
    write_contract(repo, CONTRACT_NO_IMPACT.replace(
        "decisions_taken:", f"impact_map: {header}\n  none\ndecisions_taken:"))
    out, _ = run_hook("task_contract_gate.py",
                      edit_event(repo, "dbt_project/models/allowed.sql"), repo)
    assert denied(out) and "impact_map" in out


@pytest.mark.parametrize("header", [">-", "|-", ">+", "|2"])
def test_block_scalar_header_decisions_reserved_does_not_satisfy(repo, header):
    """The same bypass on the artifact gate's half."""
    write_contract(repo, CONTRACT.replace(
        "decisions_reserved:\n  - none",
        f"decisions_reserved: {header}\n  none",
    ))
    out, _ = run_hook("task_contract_gate.py", artifact_event(), repo)
    assert denied(out) and "decisions_reserved" in out


@pytest.mark.parametrize("spelling", [
    "impact_map: writers: loader_x; blast_radius: none (leaf)\n",   # inline
    "impact_map: >\n  writers: loader_x; blast_radius: none (leaf)\n",   # block
    "impact_map: >-\n  writers: loader_x; blast_radius: none (leaf)\n",  # chomped block
    "impact_map:\n  - writers: loader_x; blast_radius: none (leaf)\n",   # dash list
])
def test_real_impact_map_is_allowed_in_every_spelling(repo, spelling):
    """The ALLOW half. The nullish tests covered three spellings of DENY while
    the only ALLOW fixture was the plain block scalar, so a fix that rejected too
    much would have passed — the one-sided coverage this contract's own done_when
    names, found for the third time (cto-reviewer, 2026-07-22)."""
    write_contract(repo, CONTRACT_NO_IMPACT.replace(
        "decisions_taken:", spelling + "decisions_taken:"))
    out, _ = run_hook("task_contract_gate.py",
                      edit_event(repo, "dbt_project/models/allowed.sql"), repo)
    assert not denied(out)


def test_placeholder_impact_map_does_not_satisfy(repo):
    """A literally-copied `<placeholder>` is not a real map — still denied."""
    write_contract(repo, CONTRACT_NO_IMPACT.replace(
        "decisions_taken:", "impact_map: <fill me in>\ndecisions_taken:"))
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "dbt_project/models/allowed.sql"), repo)
    assert denied(out) and "impact_map" in out


def test_out_of_scope_structural_edit_denied_for_scope_first(repo):
    """An out-of-scope structural path fails the scope check before the map check."""
    write_contract(repo, CONTRACT_NO_IMPACT)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "dbt_project/models/other.sql"), repo)
    assert denied(out) and "OUTSIDE" in out


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


# --------------------------------------------------------------------------- #
# Protected paths are STRUCTURAL — authority and understanding are two gates
# (2026-07-22). Every one of these runs both directions on purpose.
# --------------------------------------------------------------------------- #

def test_protected_path_denied_with_override_but_no_impact_map(repo):
    """THE missing direction. `protected_override` answers "may you"; the
    impact_map answers "do you know what breaks". A guard's blast radius is
    every future task in the repo, wider than most models."""
    write_contract(repo, CONTRACT_OVERRIDE_NO_IMPACT)
    out, _ = run_hook("task_contract_gate.py",
                      edit_event(repo, ".claude/hooks/some_hook.py"), repo)
    assert denied(out) and "impact_map" in out


def test_protected_path_allowed_with_override_and_impact_map(repo):
    """The paired ALLOW, stated explicitly rather than inherited from a fixture
    that happened to carry a map."""
    write_contract(repo, CONTRACT_OVERRIDE)
    out, _ = run_hook("task_contract_gate.py",
                      edit_event(repo, ".claude/hooks/some_hook.py"), repo)
    assert not denied(out)


@pytest.mark.parametrize("rel", [
    # PROTECTED_PREFIXES …
    ".claude/hooks/h.py", ".claude/agents/a.md",
    ".claude/commands/c.md", ".github/workflows/w.yml",
    # … and PROTECTED_FILES, which the first version of this test omitted while
    # calling itself exhaustive. The change went into `_is_protected`, which
    # covers both tuples, and `.claude/settings.json` is edited by this very
    # diff (cto-reviewer, 2026-07-22).
    ".claude/settings.json", ".claude/review_routing.json",
    ".mcp.json", ".cursor/mcp.json",
])
def test_every_protected_path_needs_an_impact_map(repo, rel):
    scoped = CONTRACT_OVERRIDE_NO_IMPACT.replace(
        "  - .claude/hooks/some_hook.py\n", f"  - {rel}\n")
    write_contract(repo, scoped)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, rel), repo)
    assert denied(out) and "impact_map" in out


def test_shell_redirect_to_protected_path_needs_an_impact_map(repo):
    """The gate was enforced on the Edit path only, so a redirect reached a
    protected file with no trace, and neither the post-command check nor the
    stop gate flags a protected+override file afterwards."""
    write_contract(repo, CONTRACT_OVERRIDE_NO_IMPACT)
    out, _ = run_hook("task_contract_gate.py",
                      bash_event("echo x >> .claude/hooks/some_hook.py"), repo)
    assert denied(out) and "impact_map" in out


def test_shell_redirect_to_protected_path_allowed_with_impact_map(repo):
    write_contract(repo, CONTRACT_OVERRIDE)
    out, _ = run_hook("task_contract_gate.py",
                      bash_event("echo x >> .claude/hooks/some_hook.py"), repo)
    assert not denied(out)


def test_ordinary_doc_still_needs_no_impact_map(repo):
    """The widened surface must not swallow ordinary files."""
    scoped = CONTRACT_NO_IMPACT.replace(
        "scope_paths:\n", "scope_paths:\n  - docs/plain.md\n")
    write_contract(repo, scoped)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "docs/plain.md"), repo)
    assert not denied(out)


# --------------------------------------------------------------------------- #
# The Artifact gate — design was the only surface with no gate at all, which is
# why three mocks were produced and rejected in one day (2026-07-22).
# --------------------------------------------------------------------------- #

def artifact_event(path="/tmp/mock.html", hook_event="PreToolUse") -> dict:
    return {"hook_event_name": hook_event, "tool_name": "Artifact",
            "tool_input": {"file_path": path}}


# A contract whose decisions_reserved is a real reservation, not the template's
# bare `- none`. The gate requires this: a contract exists in nearly every
# session, so contract-existence alone would make the gate fire almost never.
CONTRACT_RESERVED = CONTRACT.replace(
    "decisions_reserved:\n  - none",
    "decisions_reserved:\n  - what the Overview shows for a goalkeeper",
)


def test_artifact_denied_without_contract(repo):
    out, _ = run_hook("task_contract_gate.py", artifact_event(), repo)
    assert denied(out) and "needs a task contract" in out


def test_artifact_denied_when_nothing_is_reserved(repo):
    """The default contract's `- none` is the template speaking, not an author."""
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", artifact_event(), repo)
    assert denied(out) and "decisions_reserved" in out


def test_artifact_allowed_with_a_real_reservation(repo):
    write_contract(repo, CONTRACT_RESERVED)
    out, _ = run_hook("task_contract_gate.py", artifact_event(), repo)
    assert not denied(out)


def test_artifact_allowed_when_nothing_open_is_stated_as_a_sentence(repo):
    """"Nothing is open" stays legitimate — it just has to be checkable."""
    write_contract(repo, CONTRACT.replace(
        "decisions_reserved:\n  - none",
        "decisions_reserved:\n  - none: the design is CPO-approved as mock "
        "f6348775 and this publishes it unchanged",
    ))
    out, _ = run_hook("task_contract_gate.py", artifact_event(), repo)
    assert not denied(out)


@pytest.mark.parametrize("reserved", [
    # The YAML block indicators. `decisions_reserved: >` used to satisfy the gate
    # ON THE KEY LINE, so the body was never read. Five of seven keys in this
    # repo's own contract are written `key: >`.
    "decisions_reserved: >\n  none",
    "decisions_reserved: |\n  none",
    # The TEMPLATE's own two-line placeholder. It ends in `;`, not `>`, so the
    # anchored `^<.*>$` placeholder pattern missed it entirely: a contract copied
    # from the template and never filled in satisfied the gate.
    "decisions_reserved:\n  - <every known ambiguity / CPO-class question (§10)"
    " that may surface;\n     escalate each blinded (§11) — never decide>",
    "decisions_reserved:\n  - (none)",
    "decisions_reserved:\n  - TBD",
])
def test_artifact_denied_on_every_empty_spelling(repo, reserved):
    write_contract(repo, CONTRACT.replace("decisions_reserved:\n  - none", reserved))
    out, _ = run_hook("task_contract_gate.py", artifact_event(), repo)
    assert denied(out) and "decisions_reserved" in out


def test_unclosed_bracket_does_not_swallow_a_later_real_reservation(repo):
    """An entry legitimately opening with `<` used to latch an "inside a
    placeholder" flag that nothing cleared, hiding every real reservation after
    it and then reporting the block as still holding the template's bare
    `- none`, which was neither true nor actionable (cto-reviewer, 2026-07-22)."""
    write_contract(repo, CONTRACT.replace(
        "decisions_reserved:\n  - none",
        "decisions_reserved:\n  - <2s page load is a product call\n"
        "  - what the Overview shows for a goalkeeper",
    ))
    out, _ = run_hook("task_contract_gate.py", artifact_event(), repo)
    assert not denied(out)


def test_artifact_allowed_when_a_block_scalar_carries_real_content(repo):
    """The `key: >` form must still WORK when it has a body — the fix rejects the
    bare indicator, not the spelling."""
    write_contract(repo, CONTRACT.replace(
        "decisions_reserved:\n  - none",
        "decisions_reserved: >\n  what the Overview shows for a goalkeeper",
    ))
    out, _ = run_hook("task_contract_gate.py", artifact_event(), repo)
    assert not denied(out)


# --------------------------------------------------------------------------- #
# Key ordering. `decisions_reserved:` must CLOSE the preceding block like every
# other top-level key. Every pre-existing fixture happens to carry
# `decisions_taken:` in between, which is exactly why nothing caught this.
# --------------------------------------------------------------------------- #

def test_reserved_block_cannot_forge_an_impact_map(repo):
    """`impact_map: <placeholder>` immediately followed by `decisions_reserved:`
    left the impact block open, so the first reservation was scored as impact-map
    content and satisfied the requirement that is this task's headline change."""
    contract = CONTRACT_NO_IMPACT.replace(
        "decisions_taken: >\n  test\n",
        "impact_map: <fill me in>\ndecisions_reserved:\n  - a real open question\n"
        "decisions_taken: >\n  test\n",
    ).replace("decisions_reserved:\n  - none\n", "")
    write_contract(repo, contract)
    out, _ = run_hook("task_contract_gate.py",
                      edit_event(repo, "dbt_project/models/allowed.sql"), repo)
    assert denied(out) and "impact_map" in out


def test_scope_paths_closes_an_open_impact_block(repo):
    """The third forgeable key ordering. `scope_paths:` did not close an impact
    block opened above it, so any indented non-item line inside the scope list
    was scored as impact-map content and forged the map — the requirement this
    whole task makes load-bearing (cto-reviewer, 2026-07-22, round 7)."""
    contract = (
        "# Task contract — test\n"
        "objective: >\n  test\n"
        "impact_map: <fill me in>\n"
        "scope_paths:\n"
        "  - dbt_project/models/allowed.sql\n"
        "  a stray indented line that is not a list item\n"
        "decisions_taken: >\n  test\n"
        "decisions_reserved:\n  - none\n"
        "done_when:\n  - test\n"
        "amendments: (none)\n"
    )
    write_contract(repo, contract)
    out, _ = run_hook("task_contract_gate.py",
                      edit_event(repo, "dbt_project/models/allowed.sql"), repo)
    assert denied(out) and "impact_map" in out


def test_reserved_block_cannot_append_to_scope_paths(repo):
    """`scope_paths:` immediately followed by `decisions_reserved:` left the scope
    block open, so reservations matched the list-item pattern and were appended to
    the allowlist."""
    contract = CONTRACT.replace(
        "decisions_taken: >\n  test\n", ""
    ).replace(
        "  - docs/allowed_dir/\n",
        "  - docs/allowed_dir/\ndecisions_reserved:\n  - dbt_project/models/other.sql\n",
    )
    write_contract(repo, contract)
    out, _ = run_hook("task_contract_gate.py",
                      edit_event(repo, "dbt_project/models/other.sql", "Write"), repo)
    assert denied(out) and "OUTSIDE the contract" in out


def test_artifact_gate_does_not_apply_scope_to_the_artifact_path(repo):
    """Non-vacuous version: an IN-REPO path that is OUTSIDE scope_paths. An
    implementation that reused `_gate_file_edit` would deny this. The earlier
    version used an out-of-repo path, which `_rel_in_repo` returns None for, so
    it passed under either implementation (cto-reviewer, 2026-07-22)."""
    write_contract(repo, CONTRACT_RESERVED)
    out, _ = run_hook("task_contract_gate.py",
                      artifact_event(str(repo / "dbt_project" / "models" / "other.sql")), repo)
    assert not denied(out)


def test_artifact_post_tool_use_does_not_emit_a_pretooluse_deny(repo):
    out, _ = run_hook("task_contract_gate.py",
                      artifact_event(hook_event="PostToolUse"), repo)
    assert not denied(out)


# --------------------------------------------------------------------------- #
# plain_language_gate — enforced, because as a habit it failed inside the very
# retrospective that asked for it (2026-07-22).
# --------------------------------------------------------------------------- #

def stop_event(repo, text: str) -> dict:
    tp = repo / "transcript.jsonl"
    tp.write_text(json.dumps({
        "type": "assistant",
        "message": {"content": [{"type": "text", "text": text}]},
    }) + "\n", encoding="utf-8")
    return {"hook_event_name": "Stop", "transcript_path": str(tp), "cwd": str(repo)}


def blocked(out: str) -> bool:
    return '"decision": "block"' in out


@pytest.mark.parametrize("text,marker", [
    ("A sentence — with an em dash.", "EM DASH"),
    ("See §10 for the rule.", "SECTION"),
    ("Look at dbt_project/models/x.sql for this.", "FILE PATH"),
    ("word " * 700, "TOO LONG"),
])
def test_plain_language_blocks(repo, text, marker):
    out, _ = run_hook("plain_language_gate.py", stop_event(repo, text), repo)
    assert blocked(out) and marker in out


@pytest.mark.parametrize("text", [
    "The team page is approved and unbuilt. I will build it next.",
    "Look at `dbt_project/models/x.sql` for this.",              # inline code
    "Here:\n```\ndbt_project/models/x.sql\n```\ndone.",          # fenced
    "See [the model](dbt_project/models/x.sql) here.",           # link target
    "The terms are at api-sports.io/docs/v3.json and allow it.",  # a URL, not a path
    "We shipped v2 and 3 of 5 pages are done.",                  # no false positive
])
def test_plain_language_allows(repo, text):
    out, _ = run_hook("plain_language_gate.py", stop_event(repo, text), repo)
    assert not blocked(out)


def test_length_counts_prose_not_code(repo):
    """A code block the CPO asked for is scannable, not a wall of text."""
    text = "Short answer.\n\n```\n" + ("x" * 4000) + "\n```\n"
    out, _ = run_hook("plain_language_gate.py", stop_event(repo, text), repo)
    assert not blocked(out)


def test_plain_language_never_loops(repo):
    ev = stop_event(repo, "A sentence — with an em dash.")
    ev["stop_hook_active"] = True
    out, _ = run_hook("plain_language_gate.py", ev, repo)
    assert not blocked(out)


def test_plain_language_fails_open_without_a_transcript(repo):
    out, _ = run_hook("plain_language_gate.py",
                      {"hook_event_name": "Stop", "cwd": str(repo)}, repo)
    assert not blocked(out)


# --------------------------------------------------------------------------- #
# Fail-open: a hook bug must never wedge a session.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("script", [
    "task_contract_gate.py", "plain_language_gate.py", "handover_in.py",
])
@pytest.mark.parametrize("junk", ["", "not json", "null", "[]", '{"tool_name": 5}'])
def test_hooks_fail_open_on_malformed_input(repo, script, junk):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, script)],
        input=junk, capture_output=True, text=True, env=env, cwd=str(repo), timeout=60,
    )
    assert r.returncode == 0
    assert not denied(r.stdout) and not blocked(r.stdout)


# --------------------------------------------------------------------------- #
# handover_in — the delivery half. It was never wired at all until 2026-07-22,
# while the handover file claimed it was.
# --------------------------------------------------------------------------- #

def test_handover_injected(repo):
    (repo / ".claude" / "active_work.md").write_text(
        "# Active work\nTHE GOAL: ship the site.", encoding="utf-8")
    out, _ = run_hook("handover_in.py", {"cwd": str(repo)}, repo)
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "THE GOAL: ship the site." in ctx and "BEGIN HANDOVER" in ctx


def test_handover_found_from_a_subdirectory(repo):
    """The discriminating case for the root-resolution change. The hook used
    `cwd` alone, so a session started below the repo root reported the handover
    missing and invited writing a second one in the wrong place. Every other
    branch of the test harness sets cwd, CLAUDE_PROJECT_DIR and the event's cwd
    to the same directory, so all four existing handover tests passed identically
    against the old code (cto-reviewer, 2026-07-22)."""
    (repo / ".claude" / "active_work.md").write_text(
        "# Active work\nTHE GOAL: ship the site.", encoding="utf-8")
    sub = repo / "dbt_project" / "models"
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "handover_in.py")],
        input=json.dumps({}),                       # no cwd key at all
        capture_output=True, text=True, cwd=str(sub),
        env=dict(os.environ, CLAUDE_PROJECT_DIR=str(repo)), timeout=60,
    )
    ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "THE GOAL: ship the site." in ctx


def test_handover_says_so_when_missing(repo):
    out, _ = run_hook("handover_in.py", {"cwd": str(repo)}, repo)
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "No .claude/active_work.md found" in ctx


def test_handover_announces_truncation(repo):
    """Silent truncation is how a handover looks complete while its tail is
    missing — the failure that hid 86% of the file before it was cut down."""
    (repo / ".claude" / "active_work.md").write_text("y" * 20000, encoding="utf-8")
    out, _ = run_hook("handover_in.py", {"cwd": str(repo)}, repo)
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "TRUNCATED" in ctx


def test_handover_under_the_cap_is_not_called_truncated_when_multibyte(repo):
    """The cap is CHARACTERS. Reading characters while deciding truncation from
    the file's SIZE IN BYTES meant any handover under the character cap but over
    the byte cap was injected whole AND labelled truncated. A pure-ASCII fixture
    cannot catch that, because there the two units coincide — which is why the
    first version of the truncation test passed against the bug.

    '⭐' is 3 bytes and 1 character: 15,900 of them is comfortably under the
    16,000-character cap and comfortably over 16,000 bytes."""
    text = "⭐" * 15900
    (repo / ".claude" / "active_work.md").write_text(text, encoding="utf-8")
    assert len(text) < 16000 < len(text.encode("utf-8"))      # the fixture is the point
    out, _ = run_hook("handover_in.py", {"cwd": str(repo)}, repo)
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "TRUNCATED" not in ctx
    assert text in ctx                                        # and nothing was dropped
