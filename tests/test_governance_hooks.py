"""Offline tests that run the governance hook scripts against a throwaway git repo."""

from __future__ import annotations

import fnmatch
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

HOOKS = os.path.join(os.path.dirname(__file__), "..", ".claude", "hooks")
TASK_ID = "1-test"
TASK = ".claude/task/" + TASK_ID + "/"

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

# The default CONTRACT carries an impact_map so edits to structural paths are allowed.
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

# CONTRACT_OVERRIDE derives from CONTRACT, so only this variant tests the deny direction.
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


@pytest.fixture(scope="session")
def _repo_template(tmp_path_factory):
    """Built once per session; each `repo` copies it, since a git repo is path-independent."""
    base = tmp_path_factory.mktemp("repo_template")
    subprocess.run(["git", "init", "-q"], cwd=base, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=base, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=base, check=True)
    (base / ".claude" / "task" / TASK_ID).mkdir(parents=True)
    (base / "dbt_project" / "models").mkdir(parents=True)
    (base / "dbt_project" / "models" / "allowed.sql").write_text("select 1")
    subprocess.run(["git", "add", "-A"], cwd=base, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=base, check=True)
    return base


@pytest.fixture()
def repo(_repo_template, tmp_path):
    dst = tmp_path / "repo"
    shutil.copytree(_repo_template, dst)
    return dst


def write_contract(repo, text: str = CONTRACT) -> None:
    (repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(text)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "contract"], cwd=repo, check=True)


# --- task_contract_gate: file edits ---
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
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, TASK + "review.md"), repo)
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
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, TASK + "contract.md"), repo)
    assert denied(out) and "CLEAN" in out


def test_contract_amendment_allowed_on_clean_tree(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, TASK + "contract.md"), repo)
    assert out.strip() == ""


# --- task_contract_gate: impact-map gate ---
def test_structural_edit_denied_without_impact_map(repo):
    write_contract(repo, CONTRACT_NO_IMPACT)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "dbt_project/models/allowed.sql"), repo)
    assert denied(out) and "impact_map" in out


def test_structural_edit_allowed_with_impact_map(repo):
    write_contract(repo)
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
    "impact_map: {v}\n",
    "impact_map: >\n  {v}\n",
    "impact_map:\n  - {v}\n",
])
@pytest.mark.parametrize("value", [
    "none", "None", "N/A", "n/a", "TBD", "todo", "(none)",
])
def test_nullish_impact_map_does_not_satisfy(repo, value, spelling):
    write_contract(repo, CONTRACT_NO_IMPACT.replace(
        "decisions_taken:", spelling.format(v=value) + "decisions_taken:"))
    out, _ = run_hook("task_contract_gate.py",
                      edit_event(repo, "dbt_project/models/allowed.sql"), repo)
    assert denied(out) and "impact_map" in out


@pytest.mark.parametrize("header", [">-", "|-", ">+", "|+", "|2", "|2-"])
def test_block_scalar_header_impact_map_does_not_satisfy(repo, header):
    write_contract(repo, CONTRACT_NO_IMPACT.replace(
        "decisions_taken:", f"impact_map: {header}\n  none\ndecisions_taken:"))
    out, _ = run_hook("task_contract_gate.py",
                      edit_event(repo, "dbt_project/models/allowed.sql"), repo)
    assert denied(out) and "impact_map" in out


@pytest.mark.parametrize("header", [">-", "|-", ">+", "|2"])
def test_block_scalar_header_decisions_reserved_does_not_satisfy(repo, header):
    write_contract(repo, CONTRACT.replace(
        "decisions_reserved:\n  - none",
        f"decisions_reserved: {header}\n  none",
    ))
    out, _ = run_hook("task_contract_gate.py", artifact_event(), repo)
    assert denied(out) and "decisions_reserved" in out


@pytest.mark.parametrize("spelling", [
    "impact_map: writers: loader_x; blast_radius: none (leaf)\n",
    "impact_map: >\n  writers: loader_x; blast_radius: none (leaf)\n",
    "impact_map: >-\n  writers: loader_x; blast_radius: none (leaf)\n",
    "impact_map:\n  - writers: loader_x; blast_radius: none (leaf)\n",
])
def test_real_impact_map_is_allowed_in_every_spelling(repo, spelling):
    write_contract(repo, CONTRACT_NO_IMPACT.replace(
        "decisions_taken:", spelling + "decisions_taken:"))
    out, _ = run_hook("task_contract_gate.py",
                      edit_event(repo, "dbt_project/models/allowed.sql"), repo)
    assert not denied(out)


def test_placeholder_impact_map_does_not_satisfy(repo):
    write_contract(repo, CONTRACT_NO_IMPACT.replace(
        "decisions_taken:", "impact_map: <fill me in>\ndecisions_taken:"))
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "dbt_project/models/allowed.sql"), repo)
    assert denied(out) and "impact_map" in out


def test_out_of_scope_structural_edit_denied_for_scope_first(repo):
    write_contract(repo, CONTRACT_NO_IMPACT)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "dbt_project/models/other.sql"), repo)
    assert denied(out) and "OUTSIDE" in out


# --- task_contract_gate: shell coverage ---
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


# --- stop_gate ---
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


# --- parked work in the stash ---
def _stash(repo, label: str) -> None:
    """Park one tracked change under `label`, leaving the tree clean."""
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 2")
    subprocess.run(["git", "stash", "push", "-m", label, "--", "dbt_project/models/allowed.sql"],
                   cwd=repo, check=True, capture_output=True)


def test_stop_blocked_by_a_parked_stash_even_on_a_clean_tree(repo):
    """The FAST_GATES check short-circuits on a clean tree, so the stash check must run before it."""
    write_contract(repo)
    _stash(repo, "parked: some real work")
    assert subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True,
                          text=True).stdout.strip() == "", "precondition: tree must be clean"
    out, _ = run_hook("stop_gate.py", {"hook_event_name": "Stop"}, repo)
    assert '"decision": "block"' in out and "parked work" in out and "some real work" in out
    assert "parked/" in out, "the message must tell the agent where parked work belongs"


def test_stop_blocks_a_temp_stash_too(repo):
    """No stash label is exempt, because a `TEMP-` stash seen at turn end is a forgotten one."""
    write_contract(repo)
    _stash(repo, "TEMP-contract-amend")
    out, _ = run_hook("stop_gate.py", {"hook_event_name": "Stop"}, repo)
    assert '"decision": "block"' in out and "TEMP-contract-amend" in out


def test_stop_passes_on_an_empty_stash(repo):
    write_contract(repo)
    assert subprocess.run(["git", "stash", "list"], cwd=repo, capture_output=True,
                          text=True).stdout.strip() == "", "precondition: empty stack"
    out, _ = run_hook("stop_gate.py", {"hook_event_name": "Stop"}, repo)
    assert out.strip() == ""


def test_stop_stash_check_precedes_the_dirty_tree_short_circuit():
    """The parked-stash check must run before the `_dirty_outside_task_dir` short-circuit in `main()`."""
    src = pathlib.Path(HOOKS, "stop_gate.py").read_text(encoding="utf-8")
    body = src[src.index("def main("):]
    assert body.index("_parked_stashes(root)") < body.index("_dirty_outside_task_dir(root)"), (
        "the stash check must run before the dirty-tree check, or a clean tree with a forgotten "
        "stash passes silently"
    )


# --- git_discipline: flag denies ---
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


# --- the real routing file: these tests load it and enumerate the real tree ---
REAL_ROUTING_PATH = os.path.join(
    os.path.dirname(__file__), "..", ".claude", "review_routing.json")


def real_routing() -> dict:
    with open(REAL_ROUTING_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def required_reviewers(routing: dict, path: str) -> set:
    """Calls the hook's own matcher, so the test cannot be more permissive than the gate."""
    return _gd()._required_reviewers([path], routing)


def _gd():
    """The hook module; its `main()` is `__main__`-guarded, so importing has no side effects."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".claude", "hooks"))
    import git_discipline
    return git_discipline


def tracked(prefix: str) -> list[str]:
    """NUL-separated, because without `-z` paths with spaces or non-ASCII characters drop out."""
    r = subprocess.run(["git", "ls-files", "-z", prefix], capture_output=True, text=True,
                       cwd=os.path.join(os.path.dirname(__file__), ".."))
    assert r.returncode == 0, f"git ls-files failed: {r.stderr}"
    return [p for p in r.stdout.split("\0") if p]


def test_every_reviewer_brief_carries_the_identical_delta_section():
    """A drifted copy of the delta-re-review rule would make a reviewer apply a different rule."""
    import glob
    agents_dir = os.path.join(os.path.dirname(__file__), "..", ".claude", "agents")
    briefs = sorted(glob.glob(os.path.join(agents_dir, "*.md")))
    reviewers = [b for b in briefs if os.path.basename(b) != "README.md"]
    assert len(reviewers) >= 6, f"expected >=6 reviewer briefs, found {len(reviewers)}"
    sections = {}
    for b in reviewers:
        text = open(b, encoding="utf-8").read()
        assert "## Delta re-review" in text, f"{os.path.basename(b)} lost its delta section"
        sections[b] = text.split("## Delta re-review", 1)[1]
    uniq = set(sections.values())
    assert len(uniq) == 1, (
        "delta sections have drifted across briefs: "
        + ", ".join(os.path.basename(b) for b in sections))


def test_ci_backstop_requires_rounds(ci_repo):
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code+contract"], cwd=ci_repo, check=True)
    real_hash = branch_hash(ci_repo)
    (ci_repo / ".claude" / "task" / TASK_ID / "review.md").write_text(
        "# Review\ndiff_sha256: " + real_hash + "\n\n" + GOOD_BODY)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "review"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "rounds:" in out


def test_ci_backstop_reuses_the_canonical_hook_logic():
    """The CI backstop must call the hooks' own round and nullish logic, not a hand copy."""
    import importlib
    gd = _gd()
    sys.path.insert(0, SCRIPTS)
    ci = importlib.import_module("check_task_artifacts")
    tcg = importlib.import_module("task_contract_gate")
    assert ci._rounds_error.__doc__ is not None
    assert ci._rounds_error("rounds: 1\n") is None
    assert ci._rounds_error("rounds: 4\nrounds_cap_override: tbd\n") is not None
    assert ci._rounds_error("rounds: 4\nrounds_cap_override: real reason\n") is None
    assert set(gd._NULLISH_WORDS) == set(tcg._NULLISH), (
        "git_discipline._NULLISH_WORDS has drifted from task_contract_gate._NULLISH")


def test_empty_cap_override_does_not_absorb_the_next_line(repo):
    """An empty `rounds_cap_override:` must not capture the following `## header` as its reason."""
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY,
                 rounds="rounds: 4\nrounds_cap_override:\n")
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "cap" in out


@pytest.mark.parametrize("word", ["tbd", "none", "(none)", "n/a", "todo", "-"])
def test_word_placeholder_cap_override_rejected(repo, word):
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY,
                 rounds=f"rounds: 4\nrounds_cap_override: {word}\n")
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "cap" in out


def test_real_routing_parses_and_has_the_required_keys():
    r = real_routing()
    for key in ("always", "paths", "artifact_only", "artifact_only_never",
                "hash_exclude_paths"):
        assert key in r, f"review_routing.json lost its `{key}` key"
    assert "scope-auditor" in r["always"]


def test_every_tracked_frontend_source_file_gets_the_display_reviewer():
    """A frontend file that can render a field must not escape the display reviewer."""
    r = real_routing()
    files = [f for f in tracked("site_v2") if f.startswith("site_v2/src/")]
    assert files, "no tracked files under site_v2/src — has the tree moved?"
    missing = [f for f in files
               if "bi-analyst-reviewer" not in required_reviewers(r, f)]
    assert not missing, f"frontend source escaping the display reviewer: {missing}"


def test_every_tracked_frontend_non_source_file_gets_platform_review():
    """Routing names build files individually, so a new root-level build file must not route to nobody."""
    r = real_routing()
    outside = [f for f in tracked("site_v2") if not f.startswith("site_v2/src/")]
    assert outside, "no tracked files outside site_v2/src — has the tree moved?"
    missing = [f for f in outside
               if "platform-reviewer" not in required_reviewers(r, f)]
    assert not missing, (
        f"site_v2 build/hosting files with NO platform review: {missing}. Add each "
        "to review_routing.json by NAME (never a glob that could reach src/).")


def test_frontend_build_config_does_not_get_the_display_reviewer():
    """A dependency bump or build-config edit must not demand a display review."""
    r = real_routing()
    outside = [f for f in tracked("site_v2") if not f.startswith("site_v2/src/")]
    assert outside, "no tracked files outside site_v2/src — has the tree moved?"
    stray = [f for f in outside
             if "bi-analyst-reviewer" in required_reviewers(r, f)]
    assert not stray, f"non-source file demanding a display review: {stray}"


# One representative path per routing pattern, with the reviewer that pattern confers.
PINNED_CASES = [
    ("dbt_project/models/5_marts/shared/mart_team_profile.sql", "analytics-engineer-reviewer"),
    ("dbt_project/seeds/metric_catalogue.csv", "football-analytics-expert-reviewer"),
    ("ingestion/api_football/main.py", "data-engineer-reviewer"),
    ("docs/competition_registry.yml", "data-engineer-reviewer"),
    ("docs/data_contract.md", "data-engineer-reviewer"),
    ("scripts/export_site_data.py", "analytics-engineer-reviewer"),
    ("scripts/sync_dbt_vars.py", "platform-reviewer"),
    ("tests/test_governance_hooks.py", "platform-reviewer"),
    ("requirements.txt", "cto-reviewer"),
    # fnmatch full-string-matches, so the pattern needs the leading `*`.
    ("ingestion/api_football/requirements.txt", "platform-reviewer"),
    (".claude/hooks/task_contract_gate.py", "cto-reviewer"),
    (".claude/hooks/git_discipline.py", "platform-reviewer"),
    (".claude/agents/bi-analyst-reviewer.md", "cto-reviewer"),
    (".claude/commands/anything.md", "cto-reviewer"),
    (".claude/settings.json", "cto-reviewer"),
    (".claude/review_routing.json", "cto-reviewer"),
    (".mcp.json", "cto-reviewer"),
    (".cursor/mcp.json", "cto-reviewer"),
    (".github/workflows/ci-data-build.yml", "cto-reviewer"),
    (".github/workflows/ci-validate.yml", "platform-reviewer"),
    # An exact-match pattern needs one case per reviewer it confers.
    (".gitlab-ci.yml", "cto-reviewer"),
    (".gitlab-ci.yml", "platform-reviewer"),
    ("scripts/check_design_inventory.py", "cto-reviewer"),
    ("scripts/check_page_css.py", "cto-reviewer"),
    ("scripts/design_inventory.py", "cto-reviewer"),
    ("tests/test_design_inventory.py", "cto-reviewer"),
    ("docs/design/components.yml", "cto-reviewer"),
    ("docs/wireframes/02_team_profile.md", "bi-analyst-reviewer"),
    ("site/i18n/de.json", "bi-analyst-reviewer"),
    ("site_v2/src/lib/metricRows.ts", "bi-analyst-reviewer"),
    # The build surface is named file by file because fnmatch's `*` crosses `/`.
    ("site_v2/package.json", "cto-reviewer"),
    ("site_v2/package-lock.json", "platform-reviewer"),
    ("site_v2/astro.config.mjs", "platform-reviewer"),
    ("site_v2/tsconfig.json", "platform-reviewer"),
    ("site_v2/firebase.json", "platform-reviewer"),
    ("site_v2/.gitignore", "platform-reviewer"),
    ("site_v2/integrations/seo-audit.mjs", "platform-reviewer"),
    ("site_v2/scripts/audit-seo.mjs", "platform-reviewer"),
    ("dbt_project/seeds/competition_registry.csv", "data-engineer-reviewer"),
]


@pytest.mark.parametrize("path,expected", PINNED_CASES)
def test_real_routing_still_covers_every_pre_existing_surface(path, expected):
    """Widening one route must not silently narrow another."""
    assert expected in required_reviewers(real_routing(), path)


def test_every_routing_pattern_is_pinned_by_the_test_above():
    """A pattern is pinned only when a case both matches it and asserts a reviewer it confers."""
    routing = real_routing()
    unpinned = [
        pattern for pattern, reviewers in routing["paths"].items()
        if not any(fnmatch.fnmatch(path, pattern) and expected in reviewers
                   for path, expected in PINNED_CASES)
    ]
    assert not unpinned, f"unpinned routing patterns: {sorted(unpinned)}"


def test_copy_gate_parses_the_real_strings_file():
    """If the entry regex silently matches nothing, the gate passes over zero strings."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
    try:
        import check_copy_gate as gate
    finally:
        sys.path.pop(0)
    text = gate.STRINGS.read_text(encoding="utf-8")
    dicts = gate._dicts(text)
    for loc in gate.LOCALES:
        assert loc in dicts, f"copy gate found no `{loc}` dictionary in strings.ts"
        assert len(dicts[loc]) >= 20, (
            f"copy gate extracted only {len(dicts[loc])} {loc} strings — the entry "
            "regex has stopped matching. A gate over zero strings always passes.")
    assert len(dicts["en"]) == len(dicts["de"]) == len(dicts["fi"]), (
        "locale dictionaries differ in size; the gate's completeness check must "
        "be the thing that reports that, not this test")


def _health():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
    try:
        import report_process_health as health
    finally:
        sys.path.pop(0)
    return health


def _fake_git(files_by_sha: dict[str, list[str]]):
    """Stand in for `report_process_health._git`, dispatching on the subcommand."""
    def run(*args: str) -> str:
        if args[0] == "log":
            return "\n".join(files_by_sha) + "\n"
        if args[0] == "diff-tree":
            return "\n".join(files_by_sha.get(args[-1], [])) + "\n"
        return ""
    return run


def test_health_report_surfaces_a_dead_reviewer(monkeypatch):
    """Hermetic: a shallow CI clone has no usable history, so `_git` is faked."""
    health = _health()
    monkeypatch.setattr(health, "_git", _fake_git({
        "sha1": ["dbt_project/models/x.sql"],
        "sha2": [".claude/hooks/git_discipline.py"],
    }))
    total, hits = health.activation(n=2)

    assert total == 2
    briefs = {p.stem for p in (health.REPO_ROOT / ".claude" / "agents").glob("*.md")
              if p.stem != "README"}
    assert briefs <= set(hits), (
        f"reviewers with a brief but absent from the roster: {briefs - set(hits)}. "
        "A role missing from the roster can never be seen to be dead.")
    assert hits["seo-expert-reviewer"] == 0, (
        "a brief with no routing row must appear at zero, not be absent — that is "
        "the whole point of seeding the counter")
    assert hits["scope-auditor"] == 2, "the always-on reviewer fires on every commit"
    assert hits["analytics-engineer-reviewer"] == 1 and hits["cto-reviewer"] == 1, (
        "the counting itself is now pinned, not only the roster")


def test_health_report_survives_a_shallow_clone(monkeypatch, capsys):
    """An empty commit range is the realistic CI shape, so `main()` must report and exit 0."""
    health = _health()
    monkeypatch.setattr(health, "_git", _fake_git({}))
    assert health.main() == 0
    assert "no file-bearing commits in range" in capsys.readouterr().out


def test_copy_gate_floor_is_in_the_gate_not_only_in_this_test(tmp_path, monkeypatch):
    """Backtick-template values match `_DICT_RE` but yield zero entries, so the gate's own floor must fail."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
    try:
        import check_copy_gate as gate
    finally:
        sys.path.pop(0)

    broken = tmp_path / "strings.ts"
    broken.write_text(
        "\n".join(
            f"const {loc}: Dict = {{\n" + "".join(
                f"  key{i}: `value {i}`,\n" for i in range(40)) + "};\n"
            for loc in ("EN", "DE", "FI")
        ), encoding="utf-8")
    monkeypatch.setattr(gate, "STRINGS", broken)

    assert gate._dicts(broken.read_text(encoding="utf-8")).keys() >= {"en", "de", "fi"}, (
        "the fixture must reproduce the real failure: dictionaries FOUND but EMPTY")
    assert gate.main() == 1, (
        "the gate must FAIL on a file it extracted no strings from; a clean pass "
        "over zero strings is worse than no gate at all")


def _copy_gate():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
    try:
        import check_copy_gate as gate
    finally:
        sys.path.pop(0)
    return gate


def _strings_fixture(chrome_values='"v{i}"', metric_values='"m{i}"', metric_n=18,
                     metric_locales=("EN", "DE", "FI")):
    """A synthetic strings.ts: three healthy chrome dicts plus METRIC_LABELS blocks for `metric_locales`."""
    out = []
    for loc in ("EN", "DE", "FI"):
        body = "".join(f"  key{i}: {chrome_values.format(i=i)},\n" for i in range(40))
        out.append(f"const {loc}: Dict = {{\n{body}}};\n")
    for loc in metric_locales:
        body = "".join(
            f'  "metrics.m{i}.label": {metric_values.format(i=i)},\n'
            for i in range(metric_n))
        out.append(f"const METRIC_LABELS_{loc}: MetricLabels = {{\n{body}}};\n")
    return "\n".join(out)


def test_copy_gate_metric_floor_is_in_the_gate_not_only_in_a_test(tmp_path, monkeypatch):
    """Keeps the chrome dicts healthy so only the metric floor can fire; backtick values yield zero entries."""
    gate = _copy_gate()
    broken = tmp_path / "strings.ts"
    broken.write_text(_strings_fixture(metric_values="`m{i}`"), encoding="utf-8")
    monkeypatch.setattr(gate, "STRINGS", broken)

    text = broken.read_text(encoding="utf-8")
    assert len(gate._dicts(text)["en"]) >= gate.MIN_KEYS, (
        "the fixture must clear the CHROME floor, or this test passes for the wrong reason")
    assert gate._metric_labels(text).keys() >= {"en", "de", "fi"}, (
        "the fixture must reproduce the real failure: metric blocks FOUND but EMPTY")
    assert all(v == {} for v in gate._metric_labels(text).values())
    assert gate.main() == 1, (
        "the gate must FAIL when it extracted no metric labels; otherwise 54 "
        "user-visible strings skip the em dash and completeness checks silently")


def test_copy_gate_fails_when_a_metric_labels_block_is_absent(tmp_path, monkeypatch):
    """A locale losing its whole METRIC_LABELS block must fail rather than go unchecked."""
    gate = _copy_gate()
    partial = tmp_path / "strings.ts"
    text = _strings_fixture(metric_locales=("EN", "DE"))
    partial.write_text(text, encoding="utf-8")
    monkeypatch.setattr(gate, "STRINGS", partial)

    assert "fi" not in gate._metric_labels(text), "fixture must actually drop the FI block"
    assert gate.main() == 1, "a locale with no METRIC_LABELS block must fail the gate"


def test_copy_gate_metric_parser_agrees_with_the_real_consumers():
    """The Python parser must see every `metrics.X.label` key the page asks for, as the JS parsers do."""
    import pathlib
    import re as _re

    gate = _copy_gate()
    root = pathlib.Path(__file__).resolve().parents[1]
    parsed = gate._metric_labels(gate.STRINGS.read_text(encoding="utf-8"))
    assert set(parsed) == {"en", "de", "fi"}

    pattern = _re.compile(r'"(metrics\.[A-Za-z0-9_]+\.label)"')
    asked = set()
    for rel in ("site_v2/src/data/metric_rows.json",
                "site_v2/src/components/team/TeamDeserved.astro"):
        asked |= set(pattern.findall((root / rel).read_text(encoding="utf-8")))
    assert len(asked) >= 18, f"only {len(asked)} keys found in the consumers"

    for loc in ("en", "de", "fi"):
        missing = sorted(asked - set(parsed[loc]))
        assert not missing, (
            f"the Python parser does not see {missing} for {loc}, but a component asks for it — "
            "either the regex drifted or a label is genuinely absent")


def test_copy_gate_sees_the_player_metric_namespace_too():
    """`_METRIC_ENTRY_RE` must see `playerMetrics.*`, not only `metrics.*.label`; board labels come from the catalogue."""
    import csv
    import pathlib
    import re as _re

    gate = _copy_gate()
    root = pathlib.Path(__file__).resolve().parents[1]

    block = _re.search(
        r"_HOME_PLAYER_BOARDS\s*=\s*\(([^)]*)\)",
        (root / "scripts" / "export_site_data.py").read_text(encoding="utf-8"))
    assert block, "could not find _HOME_PLAYER_BOARDS in scripts/export_site_data.py"
    board_ids = _re.findall(r'"([a-z0-9_]+)"', block.group(1))
    assert len(board_ids) >= 4, f"parsed only {len(board_ids)} board ids — the tuple regex broke"

    with open(root / "dbt_project" / "seeds" / "metric_catalogue.csv", encoding="utf-8") as f:
        catalogue = [r for r in csv.DictReader(f) if r.get("entity") == "player"]
    by_id = {r["metric_id"]: r.get("label_i18n_key") for r in catalogue}
    asked = []
    for metric_id in board_ids:
        key = by_id.get(metric_id)
        assert key, f"no player catalogue row with a label_i18n_key for board {metric_id}"
        asked.append(key)
    assert any(not k.startswith("metrics.") for k in asked), (
        "this test proves nothing unless at least one board label sits OUTSIDE the metrics.* "
        "namespace — that is the case the widening exists for")

    parsed = gate._metric_labels(gate.STRINGS.read_text(encoding="utf-8"))
    for loc in ("en", "de", "fi"):
        missing = sorted(set(asked) - set(parsed[loc]))
        assert not missing, (
            f"the gate does not see {missing} for {loc}, but the Home page titles a board with it — "
            "either _METRIC_ENTRY_RE narrowed again or the label is genuinely absent")


def test_copy_gate_sees_metric_labels_as_ordinary_copy(tmp_path, monkeypatch):
    """Metric labels are merged into `dicts`, so an em dash in a metric name is reported like any other."""
    gate = _copy_gate()
    f = tmp_path / "strings.ts"
    text = _strings_fixture().replace('"metrics.m3.label": "m3"', '"metrics.m3.label": "a — b"')
    f.write_text(text, encoding="utf-8")
    monkeypatch.setattr(gate, "STRINGS", f)
    assert gate.main() == 1, "an em dash inside a metric label must be reported like any other"


def _seed_fixture(tmp_path, keys):
    """A one-file seed carrying `label_i18n_key` values."""
    p = tmp_path / "competition_types.csv"
    p.write_text("competition_type,label_i18n_key,label_en\n"
                 + "".join(f"t{i},{k},Label {i}\n" for i, k in enumerate(keys)),
                 encoding="utf-8")
    return p


def test_copy_gate_fails_on_a_seed_key_no_locale_carries(tmp_path, monkeypatch):
    """A seed key present in no locale is invisible to the locale-comparison checks, so the gate reads the seed."""
    gate = _copy_gate()
    f = tmp_path / "strings.ts"
    f.write_text(_strings_fixture(), encoding="utf-8")
    monkeypatch.setattr(gate, "STRINGS", f)
    monkeypatch.setattr(gate, "SEED_LABEL_FILES", (_seed_fixture(tmp_path, ["key1", "compTypeGhost"]),))

    text = f.read_text(encoding="utf-8")
    dicts = gate._dicts(text)
    assert all("compTypeGhost" not in dicts[loc] for loc in ("en", "de", "fi")), (
        "the fixture must reproduce the blind spot: the key is in NO locale, so check 2 is silent")
    assert gate.main() == 1, "a seed-published key absent from every locale must fail the gate"


def test_copy_gate_passes_when_every_seed_key_resolves(tmp_path, monkeypatch):
    """A blank `label_i18n_key` cell is left to the seed's own not_null test."""
    gate = _copy_gate()
    f = tmp_path / "strings.ts"
    f.write_text(_strings_fixture(), encoding="utf-8")
    monkeypatch.setattr(gate, "STRINGS", f)
    monkeypatch.setattr(gate, "SEED_LABEL_FILES", (_seed_fixture(tmp_path, ["key1", "key7", ""]),))
    assert gate._seed_label_keys() == {"competition_types.csv": ["key1", "key7"]}
    assert gate.main() == 0


def test_copy_gate_fails_closed_on_a_seed_without_the_key_column(tmp_path, monkeypatch):
    """A gate over zero keys always passes, so a missing column or file must end in the gate's FAIL line."""
    gate = _copy_gate()
    f = tmp_path / "strings.ts"
    f.write_text(_strings_fixture(), encoding="utf-8")
    monkeypatch.setattr(gate, "STRINGS", f)

    renamed = tmp_path / "competition_types.csv"
    renamed.write_text("competition_type,i18n_key,label_en\nt0,key1,Label 0\n", encoding="utf-8")
    monkeypatch.setattr(gate, "SEED_LABEL_FILES", (renamed,))
    with pytest.raises(KeyError):
        gate._seed_label_keys()
    assert gate.main() == 1, "a seed without the key column must fail the gate, not pass over zero keys"

    monkeypatch.setattr(gate, "SEED_LABEL_FILES", (tmp_path / "does_not_exist.csv",))
    assert gate.main() == 1, "an absent seed file must fail the gate with its own message"

    # A decode error is a ValueError, not an OSError, and must land on the same FAIL line.
    latin = tmp_path / "competition_types.csv"
    latin.write_bytes("competition_type,label_i18n_key,label_en\nt0,key1,Nationale Superpokale \xe4\n".encode("cp1252"))
    monkeypatch.setattr(gate, "SEED_LABEL_FILES", (latin,))
    assert gate.main() == 1, "a non-UTF-8 seed must fail the gate, not raise through it"


def test_copy_gate_reads_the_real_seeds():
    """An absent seed file must raise, not pass over zero keys."""
    gate = _copy_gate()
    keys = gate._seed_label_keys()
    assert set(keys) == {"competition_types.csv", "confederations.csv", "round_names.csv"}
    assert len(keys["competition_types.csv"]) >= 14 and len(keys["confederations.csv"]) >= 7
    assert len(keys["round_names.csv"]) >= 60
    dicts = gate._dicts(gate.STRINGS.read_text(encoding="utf-8"))
    for name, ks in keys.items():
        for k in ks:
            for loc in ("en", "de", "fi"):
                assert k in dicts[loc], f"{name}: {k} missing from {loc}"


def test_routing_has_no_duplicate_keys():
    """`json.load` keeps the last of two identical keys, silently dropping the other reviewer requirement."""
    def reject_dupes(pairs):
        seen = set()
        for key, _ in pairs:
            assert key not in seen, f"duplicate JSON key silently collapsed: {key!r}"
            seen.add(key)
        return dict(pairs)

    with open(REAL_ROUTING_PATH, encoding="utf-8") as fh:
        json.loads(fh.read(), object_pairs_hook=reject_dupes)


def test_frontend_source_gets_no_authority_or_platform_review():
    """Frontend source goes to the display reviewer only, not to the authority or platform reviewers."""
    r = real_routing()
    files = [f for f in tracked("site_v2") if f.startswith("site_v2/src/")]
    assert files, "no tracked files under site_v2/src — has the tree moved?"
    stray = {f: sorted(required_reviewers(r, f) & {"cto-reviewer", "platform-reviewer"})
             for f in files
             if required_reviewers(r, f) & {"cto-reviewer", "platform-reviewer"}}
    assert not stray, f"frontend source pulling in authority/platform review: {stray}"


# --- git_discipline: the review/commit gate ---
ROUTING = {
    "always": ["scope-auditor"],
    "paths": {"dbt_project/**": ["analytics-engineer-reviewer"]},
    "artifact_only": [".claude/task/**", ".claude/active_work.md"],
    "artifact_only_never": [".claude/task/*/contract.md"],
    "hash_exclude_paths": [
        ".claude/task/*/review.md",
        ".claude/task/*/review_input.patch",
        ".claude/task/*/escalations.log",
        ".claude/active_work.md",
        ".claude/task/*/acceptance_evidence.md",
        ".claude/task/*/rendered_page_evidence.md",
    ],
    # escalations.log is absent on purpose: reviewers must receive it.
    "review_exclude_paths": [
        ".claude/task/*/review.md",
        ".claude/task/*/review_input.patch",
        ".claude/task/*/acceptance_evidence.md",
        ".claude/task/*/rendered_page_evidence.md",
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
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "git_discipline.py"), "--staged-hash"],
        cwd=str(repo), capture_output=True, text=True, env=env, timeout=60,
    )
    return r.stdout.strip()


def write_review(repo, hash_hex, body, rounds="rounds: 1\n"):
    (repo / ".claude" / "task" / TASK_ID / "review.md").write_text(
        f"# Review\ndiff_sha256: {hash_hex}\n{rounds}\n{body}\n"
    )


GOOD_BODY = (
    "## scope-auditor\nVERDICT: PASS\nrisks_checked:\n- risk one checked\n- risk two checked\n\n"
    "## analytics-engineer-reviewer\nVERDICT: PASS\nrisks_checked:\n- risk one checked\n"
    "- risk two checked\n"
)

COMMIT_CMD = 'git commit -m "feat: x"'


def test_commit_denied_without_review_artifact(repo):
    (repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
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


def test_commit_allowed_on_pass_with_one_thing_examined(repo):
    """One entry under risks_checked: is enough for a PASS."""
    setup_review_repo(repo)
    body = GOOD_BODY.replace("- risk two checked\n\n## analytics", "\n## analytics", 1)
    write_review(repo, staged_hash(repo), body)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert not denied(out), out


def test_commit_denied_on_pass_with_nothing_examined(repo):
    """A bare PASS with nothing under risks_checked: is a rubber stamp."""
    setup_review_repo(repo)
    body = GOOD_BODY.replace(
        "risks_checked:\n- risk one checked\n- risk two checked\n\n## analytics",
        "risks_checked:\n\n## analytics", 1)
    write_review(repo, staged_hash(repo), body)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "state what was examined" in out


def test_bullets_before_risks_marker_do_not_satisfy_quota(repo):
    """Risks are counted from the risks_checked: marker, so stray bullets above it do not count."""
    setup_review_repo(repo)
    body = GOOD_BODY.replace(
        "VERDICT: PASS\nrisks_checked:\n- risk one checked\n- risk two checked\n\n## analytics",
        "- stray bullet\n- another stray\nVERDICT: PASS\nrisks_checked:\n\n## analytics", 1)
    write_review(repo, staged_hash(repo), body)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "state what was examined" in out


def test_commit_allowed_with_complete_review(repo):
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert not denied(out)


def test_artifact_only_commit_exempt_from_review(repo):
    setup_review_repo(repo)
    subprocess.run(["git", "reset"], cwd=repo, check=True, capture_output=True)
    (repo / ".claude" / "task" / TASK_ID / "notes.md").write_text("bookkeeping")
    subprocess.run(["git", "add", TASK + "notes.md"], cwd=repo, check=True)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert not denied(out)


# --- acceptance gate: fires on the user-facing surface and nowhere else ---
FRONTEND_PATH = "site_v2/src/pages/x.astro"


def _stage_frontend(repo, contract: str | None, evidence: str | None = None):
    """Stage a user-facing change, optionally with a contract and evidence file."""
    setup_review_repo(repo, stage_path=FRONTEND_PATH)
    if contract is not None:
        (repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(contract, encoding="utf-8")
    if evidence is not None:
        (repo / ".claude" / "task" / TASK_ID / "acceptance_evidence.md").write_text(
            evidence, encoding="utf-8")
    write_review(repo, staged_hash(repo), GOOD_BODY)


CRITERIA_CONTRACT = """objective: >
  a page
acceptance_criteria:
  - the page opens on the most recent CLUB season, not a national one
  - the title is unique across the generated set
scope_paths:
  - site_v2/src/**
"""


def test_acceptance_gate_denies_frontend_change_with_no_criteria(repo):
    _stage_frontend(repo, contract="objective: >\n  a page\nscope_paths:\n  - x\n")
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "acceptance_criteria" in out


def test_acceptance_gate_denies_when_evidence_file_is_missing(repo):
    _stage_frontend(repo, contract=CRITERIA_CONTRACT)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "acceptance_evidence.md" in out


def test_acceptance_gate_denies_when_a_criterion_is_undemonstrated(repo):
    _stage_frontend(repo, contract=CRITERIA_CONTRACT, evidence=(
        "criteria_demonstrated:\n"
        "  - read from dist/en/players/x/index.html: opens on 2025/26 Bundesliga\n"
    ))
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "2 acceptance criteria declared, 1 demonstrated" in out


def test_acceptance_gate_rejects_placeholder_evidence(repo):
    _stage_frontend(repo, contract=CRITERIA_CONTRACT, evidence=(
        "criteria_demonstrated:\n  - <what it showed>\n  - none\n"))
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "0 demonstrated" in out


def test_acceptance_gate_passes_when_every_criterion_is_demonstrated(repo):
    _stage_frontend(repo, contract=CRITERIA_CONTRACT, evidence=(
        "criteria_demonstrated:\n"
        "  - read from dist/en/players/x/index.html: opens on 2025/26 Bundesliga\n"
        "  - all 3 locale titles distinct, read from dist/{de,en,fi}\n"))
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert not denied(out)


def test_acceptance_gate_does_not_fire_off_the_user_facing_surface(repo):
    """The staged content must differ from HEAD, or `_commit_gate` returns before reaching the gate."""
    _stage_frontend(repo, contract="objective: >\n  a model\nscope_paths:\n  - x\n")
    subprocess.run(["git", "reset"], cwd=repo, check=True, capture_output=True)
    target = repo / "dbt_project" / "models" / "warehouse_only.sql"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("select 42 as definitely_not_head")
    subprocess.run(["git", "add", str(target)], cwd=repo, check=True)
    staged = subprocess.run(["git", "diff", "--staged", "--name-only"], cwd=repo,
                            capture_output=True, text=True, check=True).stdout.split()
    assert staged == ["dbt_project/models/warehouse_only.sql"], (
        f"the gate under test is only reached with a non-empty staged diff; got {staged}")
    write_review(repo, staged_hash(repo), GOOD_BODY)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert not denied(out)


def test_acceptance_gate_delegates_when_there_is_no_contract(tmp_path):
    """Calls `_acceptance_gate` directly, since `main()` swallows errors in its fail-open wrapper."""
    gd = _gd()
    frontend = ["site_v2/src/pages/x.astro"]
    assert gd._acceptance_gate(str(tmp_path), frontend, TASK) is None, (
        "with no contract.md the gate must DELEGATE (return None), never deny")
    task = tmp_path / ".claude" / "task" / TASK_ID
    task.mkdir(parents=True)
    (task / "contract.md").write_text("objective: >\n  a page\n", encoding="utf-8")
    assert gd._acceptance_gate(str(tmp_path), frontend, TASK) is not None


def test_acceptance_gate_rejects_evidence_too_short_to_be_a_reading(repo):
    """`- ok` and `- fine` are non-placeholder and distinct, so only `_MIN_EVIDENCE_CHARS` rejects them."""
    _stage_frontend(repo, contract=CRITERIA_CONTRACT, evidence=(
        "criteria_demonstrated:\n  - ok\n  - fine\n"))
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "0 demonstrated" in out
    assert "too short" in out, "the deny must say WHY a line did not count"


def test_acceptance_gate_rejects_repeated_identical_evidence(repo):
    """A bare count would accept two identical bullets, so identical lines are rejected."""
    _stage_frontend(repo, contract=CRITERIA_CONTRACT, evidence=(
        "criteria_demonstrated:\n  - checked and it works fine\n"
        "  - checked and it works fine\n"))
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "identical" in out.lower()


# --- round cap ---
def test_commit_denied_without_a_rounds_line(repo):
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY, rounds="")
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "rounds:" in out


def test_commit_allowed_at_the_cap(repo):
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY, rounds="rounds: 3\n")
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert not denied(out)


def test_commit_denied_over_the_cap_without_override(repo):
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY, rounds="rounds: 4\n")
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "cap" in out


def test_commit_allowed_over_the_cap_with_a_real_override(repo):
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY,
                 rounds="rounds: 5\nrounds_cap_override: CPO said keep going, 2026-07-22\n")
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert not denied(out)


@pytest.mark.parametrize("bad", ["rounds: 0\n", "rounds: many\n", "rounds: -1\n"])
def test_commit_denied_on_a_non_positive_rounds(repo, bad):
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY, rounds=bad)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out)


def test_placeholder_cap_override_does_not_satisfy(repo):
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY,
                 rounds="rounds: 4\nrounds_cap_override: <reason>\n")
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "cap" in out


def test_contract_commit_not_artifact_exempt(repo):
    """A commit touching contract.md authorizes scope, so it is never artifact-exempt."""
    setup_review_repo(repo)
    subprocess.run(["git", "reset"], cwd=repo, check=True, capture_output=True)
    (repo / ".claude" / "task" / TASK_ID / "contract.md").write_text("# contract\nscope_paths:\n  - x\n")
    subprocess.run(["git", "add", TASK + "contract.md"], cwd=repo, check=True)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "no review artifact" in out


def test_hash_excludes_bookkeeping_but_binds_contract(repo):
    setup_review_repo(repo)
    h_code = staged_hash(repo)
    assert h_code
    (repo / ".claude" / "task" / TASK_ID / "escalations.log").write_text("log entry")
    subprocess.run(["git", "add", TASK + "escalations.log"], cwd=repo, check=True)
    assert staged_hash(repo) == h_code
    (repo / ".claude" / "task" / TASK_ID / "contract.md").write_text("# contract\n")
    subprocess.run(["git", "add", TASK + "contract.md"], cwd=repo, check=True)
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
    """The hash is verified at PreToolUse time, so a sibling command could restage content before the commit."""
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
    'git commit -qam "sneak"',
    'git commit -sam "sneak"',
    'git commit --inc -m "sneak"',
    'git commit -p -m "sneak"',
    'git commit --interactive',
    'git -C . commit -a -m "sneak"',
    'git -c user.name=x commit --all -m "sneak"',
    'git --no-pager commit -am "sneak"',
    'git -p commit -am "sneak"',
    'git -P commit -am "sneak"',
    'git --git-dir .git commit -am "sneak"',
    'git --work-tree . commit -a -m "sneak"',
    'git commit -m "sneak" "dbt_project/models/allowed file.sql"',
    'git commit -m "unclosed',
])
def test_bundled_abbreviated_and_global_option_forms_denied(repo, cmd):
    """Only exactly `git commit` enters the allowed path, so spellings a denylist regex misses are blocked."""
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
    setup_review_repo(repo, stage_path="dbt_project/models/täst.sql")
    body = GOOD_BODY.split("## analytics-engineer-reviewer")[0]
    write_review(repo, staged_hash(repo), body)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "analytics-engineer-reviewer" in out


# --- task_contract_gate: protected paths and untracked files ---
def test_routing_file_is_protected(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, ".claude/review_routing.json"), repo)
    assert denied(out) and "PROTECTED" in out


def test_agents_dir_is_protected(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, ".claude/agents/scope-auditor.md"), repo)
    assert denied(out) and "PROTECTED" in out


@pytest.mark.parametrize("rel", [
    "scripts/check_design_inventory.py", "scripts/check_page_css.py",
    "scripts/design_inventory.py", "tests/test_design_inventory.py",
])
def test_design_checks_are_protected_even_in_scope(repo, rel):
    write_contract(repo, CONTRACT.replace("scope_paths:\n", f"scope_paths:\n  - {rel}\n"))
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, rel), repo)
    assert denied(out) and "PROTECTED" in out


def test_commands_dir_is_protected(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, ".claude/commands/status.md"), repo)
    assert denied(out) and "PROTECTED" in out


def test_untracked_dir_files_in_scope_not_flagged(repo):
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


# --- check_task_artifacts.py: the CI backstop ---
SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")


def _ci_module():
    import importlib

    sys.path.insert(0, SCRIPTS)
    return importlib.import_module("check_task_artifacts")


# --- default_base(): which remote the bare command diffs against ---
def _add_remote(repo, name: str) -> None:
    subprocess.run(["git", "remote", "add", name, f"https://example.invalid/{name}.git"],
                   cwd=repo, check=True)


def test_default_base_prefers_the_live_remote_over_the_mirror_origin(repo, monkeypatch):
    ci = _ci_module()
    monkeypatch.chdir(repo)
    monkeypatch.delenv("GOVERNANCE_BASE", raising=False)

    _add_remote(repo, "origin")
    assert ci.default_base() == "origin/main", (
        "with no `gitlab` remote the historical default must be unchanged — this is "
        "the GitHub-primary case, which is not retired and may return")

    _add_remote(repo, "gitlab")
    assert ci.default_base() == "gitlab/main", (
        "with a `gitlab` remote present the bare command must diff against it, not "
        "against `origin`, the GitHub mirror that lags it")


def test_governance_base_env_still_overrides_everything(repo, monkeypatch):
    ci = _ci_module()
    monkeypatch.chdir(repo)
    _add_remote(repo, "gitlab")
    monkeypatch.setenv("GOVERNANCE_BASE", "upstream/release")
    assert ci.default_base() == "upstream/release"


def test_default_base_falls_back_when_git_cannot_be_queried(repo, monkeypatch):
    """An unreadable remote list returns the default rather than raising inside a CI gate."""
    ci = _ci_module()
    monkeypatch.chdir(repo)
    monkeypatch.delenv("GOVERNANCE_BASE", raising=False)

    def _boom(*a, **k):
        raise OSError("git unavailable")

    monkeypatch.setattr(ci.subprocess, "run", _boom)
    assert ci.default_base() == "origin/main"


def run_ci_check(repo) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "check_task_artifacts.py"), "--base", "main"],
        capture_output=True, text=True, cwd=str(repo), timeout=60,
    )
    return r.returncode, r.stdout + r.stderr


def branch_hash(repo, base="main") -> str:
    """sha256 of `git diff --raw base...HEAD` minus bookkeeping artifacts, mirroring check_task_artifacts.py."""
    import hashlib
    excludes = ROUTING["hash_exclude_paths"]
    pathspec = ["--", "."] + [f":(exclude){p}" for p in excludes]
    diff = subprocess.run(
        ["git", "diff", "--raw", "--no-renames", "--no-abbrev", f"{base}...HEAD"] + pathspec,
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
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "review.md" in out


def test_ci_check_passes_artifact_only_pr(ci_repo):
    (ci_repo / ".claude" / "task" / TASK_ID / "notes.md").write_text("bookkeeping")
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "artifacts"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 0 and "artifact-only" in out


def test_ci_check_passes_with_complete_artifacts(ci_repo):
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code+contract"], cwd=ci_repo, check=True)
    real_hash = branch_hash(ci_repo)
    (ci_repo / ".claude" / "task" / TASK_ID / "review.md").write_text(
        "# Review\ndiff_sha256: " + real_hash + "\nrounds: 1\n\n" + GOOD_BODY
    )
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "review"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 0, out


def test_ci_check_contract_only_pr_not_artifact_exempt(ci_repo):
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "contract only"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "review.md" in out


def test_ci_check_fails_on_stale_review_hash(ci_repo):
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    (ci_repo / ".claude" / "task" / TASK_ID / "review.md").write_text(
        "# Review\ndiff_sha256: " + "b" * 64 + "\n\n" + GOOD_BODY
    )
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "stale review"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "not bound to this PR" in out


def test_local_staged_hash_equals_ci_recompute(ci_repo):
    """The local pre-commit hash must equal the CI post-commit recompute over a modified, a new and an excluded file."""
    (ci_repo / "dbt_project" / "models" / "allowed.sql").write_text("select 7\n")
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    (ci_repo / ".claude" / "task" / TASK_ID / "escalations.log").write_text("noise\n")
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    local = staged_hash(ci_repo)
    subprocess.run(["git", "commit", "-qm", "code+contract"], cwd=ci_repo, check=True)
    ci = branch_hash(ci_repo)
    assert local == ci, f"local {local} != ci {ci}"


def test_review_hash_is_invariant_to_diff_rendering_settings(ci_repo):
    """The hash must not move when a diff rendering setting such as `diff.context` moves."""
    # The changed line must sit between unchanged ones, or there is no context for the setting to alter.
    model = ci_repo / "dbt_project" / "models" / "allowed.sql"
    model.write_text("".join("select %d\n" % i for i in range(1, 11)))
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "ten lines"], cwd=ci_repo, check=True)

    lines = model.read_text().splitlines(keepends=True)
    lines[4] = "select 99\n"
    model.write_text("".join(lines))
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)

    subprocess.run(["git", "config", "diff.context", "0"], cwd=ci_repo, check=True)
    tight = staged_hash(ci_repo)
    subprocess.run(["git", "config", "diff.context", "3"], cwd=ci_repo, check=True)
    loose = staged_hash(ci_repo)

    assert tight and loose, "the hook produced no hash at all"
    assert tight == loose, (
        "the review hash changed when only a DIFF RENDERING setting changed "
        f"(context=0 -> {tight[:16]}, context=3 -> {loose[:16]}); it is hashing a presentation "
        "format, so two machines can disagree about identical content (#63)")


def test_staged_hash_refuses_to_emit_a_hash_it_could_not_compute(tmp_path):
    """An uncomputable hash must stop the workflow, not resolve to the digest of empty input."""
    import hashlib
    empty = hashlib.sha256(b"").hexdigest()
    # `_repo_root()` prefers CLAUDE_PROJECT_DIR over the cwd, so it must be removed to leave the hook with no repository.
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "git_discipline.py"), "--staged-hash"],
        cwd=str(tmp_path), capture_output=True, text=True, timeout=60, env=env,
    )
    assert r.returncode != 0, "exited 0 without computing a hash"
    assert empty not in r.stdout, (
        "printed sha256 of EMPTY as if it were a real hash — review.md would bind to nothing "
        "and the gate would match it against itself")
    assert not re.search(r"\b[0-9a-f]{64}\b", r.stdout), \
        f"emitted a 64-hex hash it could not have computed: {r.stdout!r}"


def test_commit_gate_denies_when_the_hash_cannot_be_computed(monkeypatch, ci_repo):
    """Uses `ci_repo` because without `review_routing.json` the gate returns before computing the hash."""
    repo = ci_repo
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 1\n")
    (repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    write_review(repo, "a" * 64, GOOD_BODY)

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gd_under_test", os.path.join(HOOKS, "git_discipline.py"))
    gd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gd)
    monkeypatch.setattr(gd, "_cumulative_diff",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("base unresolvable")))

    reason = gd._commit_gate(str(repo))
    assert reason, "the gate allowed a commit whose hash could not be computed"
    assert "could not be computed" in reason, \
        f"denied for the wrong reason (a mismatch, not the real cause): {reason!r}"


def test_base_resolution_prefers_the_remote_tracking_ref_over_a_stale_local_main(ci_repo):
    """A local `main` goes stale, so the remote-tracking ref must win; `ci_repo` has no remotes, so one is added."""
    stale = subprocess.run(["git", "rev-parse", "main"], cwd=ci_repo,
                           capture_output=True, text=True, check=True).stdout.strip()

    for n in (1, 2):
        (ci_repo / "dbt_project" / "models" / f"upstream{n}.sql").write_text(f"select {n}\n")
        subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
        subprocess.run(["git", "commit", "-qm", f"upstream {n}"], cwd=ci_repo, check=True)
    ahead = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ci_repo,
                           capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(["git", "update-ref", "refs/remotes/gitlab/main", ahead], cwd=ci_repo, check=True)
    subprocess.run(["git", "update-ref", "refs/heads/main", stale], cwd=ci_repo, check=True)
    assert stale != ahead, "fixture did not actually create a stale local main"

    (ci_repo / "dbt_project" / "models" / "mine.sql").write_text("select 42\n")
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)

    import hashlib
    excludes = ROUTING["hash_exclude_paths"]
    pathspec = ["--", "."] + [f":(exclude){p}" for p in excludes]

    def hash_from(base):
        d = subprocess.run(
            ["git", "diff", "--staged", "--no-renames", "--no-abbrev", "--raw", base] + pathspec,
            cwd=ci_repo, capture_output=True).stdout
        return hashlib.sha256(d).hexdigest()

    got = staged_hash(ci_repo)
    assert got == hash_from(ahead), (
        "the hook resolved a base that is not the remote-tracking ref")
    assert got != hash_from(stale), (
        "the hook used the STALE local `main` — the reviewers' patch and the hash would both "
        "cover commits that are already merged upstream")


def test_governance_base_env_var_overrides_the_base(ci_repo):
    """The override ref must have diverged from HEAD, or tip and merge-base coincide and the test cannot tell them apart."""
    (ci_repo / "dbt_project" / "models" / "allowed.sql").write_text("select 1\n")
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "branch work"], cwd=ci_repo, check=True)

    subprocess.run(["git", "checkout", "-q", "-b", "upstream", "main"], cwd=ci_repo, check=True)
    (ci_repo / "dbt_project" / "models" / "upstream_only.sql").write_text("select 99\n")
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "upstream moved"], cwd=ci_repo, check=True)
    tip = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ci_repo,
                         capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(["git", "checkout", "-q", "feature"], cwd=ci_repo, check=True)

    ancestor = subprocess.run(["git", "merge-base", "HEAD", tip], cwd=ci_repo,
                              capture_output=True, text=True, check=True).stdout.strip()
    assert ancestor != tip, "fixture did not create a genuinely diverged ref"

    (ci_repo / "dbt_project" / "models" / "second.sql").write_text("select 2\n")
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)

    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(ci_repo), GOVERNANCE_BASE="upstream")
    overridden = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "git_discipline.py"), "--staged-hash"],
        cwd=str(ci_repo), capture_output=True, text=True, env=env, timeout=60)
    assert overridden.returncode == 0, overridden.stderr

    import hashlib
    pathspec = ["--", "."] + [f":(exclude){p}" for p in ROUTING["hash_exclude_paths"]]

    def hash_from(base):
        d = subprocess.run(
            ["git", "diff", "--staged", "--no-renames", "--no-abbrev", "--raw", base] + pathspec,
            cwd=ci_repo, capture_output=True).stdout
        return hashlib.sha256(d).hexdigest()

    assert overridden.stdout.strip() == hash_from(ancestor), (
        "the override did not resolve through merge-base")
    assert overridden.stdout.strip() != hash_from(tip), (
        "the override resolved to the branch TIP. CI diffs `base...HEAD` (merge-base), so the two "
        "halves would hash different bytes and the local diff would carry a reverse delta for "
        "everything merged upstream since this branch was cut — the very defect #63 removes")


def test_an_empty_cumulative_diff_is_not_reported_as_a_failure_to_compute(ci_repo):
    """`None` (could not compute) and `b""` (nothing changed) are different states; a staged revert is net-zero."""
    model = ci_repo / "dbt_project" / "models" / "allowed.sql"
    original = model.read_text()
    model.write_text("select 999\n")
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "change it"], cwd=ci_repo, check=True)
    model.write_text(original)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)

    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "git_discipline.py"), "--staged-hash"],
        cwd=str(ci_repo), capture_output=True, text=True,
        env=dict(os.environ, CLAUDE_PROJECT_DIR=str(ci_repo)), timeout=60)
    assert r.returncode == 0, (
        "a net-zero branch was treated as a failure to compute the hash: " + r.stderr)
    import hashlib
    assert r.stdout.strip() == hashlib.sha256(b"").hexdigest(), \
        "an empty cumulative diff should hash to the empty digest, not be refused"


def test_local_staged_hash_equals_ci_recompute_on_a_multi_commit_branch(ci_repo):
    """After a second commit the index equals HEAD, so the local hash must still cover the whole branch."""
    (ci_repo / "dbt_project" / "models" / "allowed.sql").write_text("select 7\n")
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "first"], cwd=ci_repo, check=True)

    (ci_repo / "dbt_project" / "models" / "second.sql").write_text("select 8\n")
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "second"], cwd=ci_repo, check=True)

    local = staged_hash(ci_repo)
    ci = branch_hash(ci_repo)
    assert local == ci, (
        f"local {local[:16]} != ci {ci[:16]} on a two-commit branch — the local gate is hashing "
        "only the last increment, so a locally-passing commit is rejected by CI (#63)")


def test_ci_check_fails_on_missing_required_reviewer(ci_repo):
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    body = GOOD_BODY.split("## analytics-engineer-reviewer")[0]
    (ci_repo / ".claude" / "task" / TASK_ID / "review.md").write_text(
        "# Review\ndiff_sha256: " + "a" * 64 + "\n\n" + body
    )
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code+partial"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "analytics-engineer-reviewer" in out


def test_ci_check_requires_reviewer_for_non_ascii_path(ci_repo):
    (ci_repo / "dbt_project" / "models" / "täst.sql").write_text(
        "select 1", encoding="utf-8")
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    body = GOOD_BODY.split("## analytics-engineer-reviewer")[0]
    (ci_repo / ".claude" / "task" / TASK_ID / "review.md").write_text(
        "# Review\ndiff_sha256: " + "a" * 64 + "\n\n" + body
    )
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "analytics-engineer-reviewer" in out


def test_ci_check_fails_on_preamble_escalation(ci_repo):
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    body = (
        "VERDICT: ESCALATE\n- question: x?\n\n" + GOOD_BODY +
        "\n## notes\nCPO ANSWER: for something else entirely\n"
    )
    (ci_repo / ".claude" / "task" / TASK_ID / "review.md").write_text(
        "# Review\ndiff_sha256: " + "a" * 64 + "\n\n" + body
    )
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code+artifacts"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "_preamble" in out


def test_ci_check_fails_on_per_section_unanswered_escalation(ci_repo):
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    body = GOOD_BODY + (
        "\n## escalations\nVERDICT: ESCALATE\n- question: x?\n"
        "\n## notes\nCPO ANSWER: for something else entirely\n"
    )
    (ci_repo / ".claude" / "task" / TASK_ID / "review.md").write_text(
        "# Review\ndiff_sha256: " + "a" * 64 + "\n\n" + body
    )
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code+artifacts"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "escalations" in out


# --- protected paths also need an impact_map ---

def test_protected_path_denied_with_override_but_no_impact_map(repo):
    write_contract(repo, CONTRACT_OVERRIDE_NO_IMPACT)
    out, _ = run_hook("task_contract_gate.py",
                      edit_event(repo, ".claude/hooks/some_hook.py"), repo)
    assert denied(out) and "impact_map" in out


def test_protected_path_allowed_with_override_and_impact_map(repo):
    write_contract(repo, CONTRACT_OVERRIDE)
    out, _ = run_hook("task_contract_gate.py",
                      edit_event(repo, ".claude/hooks/some_hook.py"), repo)
    assert not denied(out)


@pytest.mark.parametrize("rel", [
    ".claude/hooks/h.py", ".claude/agents/a.md",
    ".claude/commands/c.md", ".github/workflows/w.yml",
    ".claude/settings.json", ".claude/review_routing.json",
    ".mcp.json", ".cursor/mcp.json", ".gitlab-ci.yml",
    "scripts/check_design_inventory.py", "scripts/check_page_css.py",
    "scripts/design_inventory.py", "tests/test_design_inventory.py",
    "docs/design/components.yml",
])
def test_every_protected_path_needs_an_impact_map(repo, rel):
    scoped = CONTRACT_OVERRIDE_NO_IMPACT.replace(
        "  - .claude/hooks/some_hook.py\n", f"  - {rel}\n")
    write_contract(repo, scoped)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, rel), repo)
    assert denied(out) and "impact_map" in out


# Each `if:` condition mapped to the pipeline contexts in which it holds. Contexts:
#   schedule  — a scheduled pipeline (runs on main)
#   web       — a manual dispatch from the UI (runs on main)
#   mr        — a merge-request pipeline (CI_COMMIT_BRANCH is unset)
#   push_main — an ordinary push to main
# `changes:` is ignored because GitLab evaluates it as true on any pipeline that is not a push or an MR.
_CONDITION_TRUTH = {
    '$CI_PIPELINE_SOURCE == "schedule"': {"schedule"},
    '$CI_PIPELINE_SOURCE == "web"': {"web"},
    '$CI_PIPELINE_SOURCE == "merge_request_event"': {"mr"},
    "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH": {"schedule", "web", "push_main"},
    '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH && $CI_PIPELINE_SOURCE == "push"':
        {"push_main"},
}


def _ci_cond(rule: dict) -> str | None:
    """Normalise a rule's `if:` for quote style and whitespace only."""
    cond = rule.get("if")
    if cond is None:
        return None
    return " ".join(cond.replace("'", '"').split())


def _matches(cond: str | None, context: str) -> bool:
    """An unrecognised condition raises, because assuming it is false would let a guard test stop guarding."""
    if cond is None:
        return True
    if cond in _CONDITION_TRUTH:
        return context in _CONDITION_TRUTH[cond]
    raise AssertionError(
        f"unrecognised CI rule condition {cond!r}. These tests reason about pipeline "
        f"reachability by classifying conditions, and an unknown one must not be "
        f"assumed harmless. Add it to _CONDITION_TRUTH in this file, deciding "
        f"deliberately which of schedule/web/mr/push_main it holds in.")


def _when_in(job: dict, context: str) -> str:
    """The effective `when:` for `job` in `context`; the first matching rule wins, else never."""
    for rule in (job.get("rules") or [{}]):
        if _matches(_ci_cond(rule), context):
            return rule.get("when", "on_success")
    return "never"


def test_a_web_dispatch_never_auto_starts_a_warehouse_build():
    """A web dispatch may offer expensive warehouse work as a button but must not start it."""
    import pathlib

    import yaml

    root = pathlib.Path(__file__).resolve().parents[1]
    ci = yaml.safe_load((root / ".gitlab-ci.yml").read_text(encoding="utf-8"))

    # Warehouse jobs are identified by what they run. The regex matches a dbt command in command
    # position, not prose in an echo; `deps`, `parse` and `compile` are absent because they touch no data.
    import re as _re
    _dbt_cmd = _re.compile(
        r"(?m)(?:^|&&|;|\|)\s*\(?\s*(?:cd \S+\s*&&\s*)*"
        r"dbt\s+(build|test|seed|run|snapshot)\b")

    def spends_warehouse_money(job: dict) -> bool:
        return any(_dbt_cmd.search(step) for step in (job.get("script") or []))

    checked = 0
    for name, job in ci.items():
        if name.startswith(".") or not isinstance(job, dict) or "script" not in job:
            continue
        if not spends_warehouse_money(job):
            continue
        checked += 1
        assert _when_in(job, "web") in ("manual", "never"), (
            f"job {name!r} AUTO-STARTS on a web dispatch and spends warehouse money "
            f"(when={_when_in(job, 'web')!r}). A manual pipeline must not begin an "
            f"expensive build the user did not ask for — make it `when: manual`. "
            f"rules={job.get('rules')!r}")

    assert checked >= 3, (
        f"only {checked} warehouse-spending jobs recognised — this test has probably "
        f"stopped seeing them, which makes it pass vacuously")

    assert _when_in(ci["data:build:main"], "push_main") == "on_success", (
        "data:build:main no longer runs automatically on a push to main. The fix was "
        "meant to narrow WEB dispatches only — prod must still rebuild on merge, or it "
        "silently goes stale and every MR's state:modified+ baseline drifts.")


def test_the_firebase_deploy_is_reachable_only_by_deliberate_dispatch():
    """`when: manual` alone excludes nothing by source, so a deploy job must be unreachable except by web dispatch.

    The two nightly-image jobs are excluded by name, since a property-based exclusion could be met by accident."""
    import pathlib

    import yaml

    root = pathlib.Path(__file__).resolve().parents[1]
    ci = yaml.safe_load((root / ".gitlab-ci.yml").read_text(encoding="utf-8"))

    everyday = ("mr", "push_main", "schedule")

    auto_deploy_jobs = {"build:nightly-image", "deploy:nightly-image"}

    deploy_jobs = [k for k, v in ci.items()
                   if not k.startswith(".") and isinstance(v, dict)
                   and v.get("stage") == "deploy" and k not in auto_deploy_jobs]
    assert deploy_jobs, "no deploy-stage jobs found — this test has gone stale"
    assert auto_deploy_jobs <= ci.keys(), (
        f"{auto_deploy_jobs - ci.keys()} named as the deliberate exception no longer "
        f"exist — remove them from auto_deploy_jobs or this exclusion is dead code")

    for name in deploy_jobs:
        rules = ci[name].get("rules") or []
        assert rules, f"deploy job {name!r} has no rules, so every pipeline carries it"
        for context in everyday:
            assert _when_in(ci[name], context) == "never", (
                f"deploy job {name!r} is reachable on a {context} pipeline. A Firebase "
                f"deploy would appear as a play button on ordinary merge requests / "
                f"pushes. Scope it to `if: $CI_PIPELINE_SOURCE == \"web\"` with a "
                f"`when: never` fallback. rules={rules!r}")


def test_the_nightly_image_jobs_are_reachable_only_on_a_push_to_main():
    """The nightly-image jobs run automatically on a push to main and are unreachable from MR, schedule or web."""
    import pathlib

    import yaml

    root = pathlib.Path(__file__).resolve().parents[1]
    ci = yaml.safe_load((root / ".gitlab-ci.yml").read_text(encoding="utf-8"))

    for name in ("build:nightly-image", "deploy:nightly-image"):
        assert name in ci, f"{name} is missing — GitLab #74's fix has been removed"
        job = ci[name]

        for context in ("mr", "schedule", "web"):
            assert _when_in(job, context) == "never", (
                f"{name} is reachable on a {context!r} pipeline "
                f"(when={_when_in(job, context)!r}). It must only ever run "
                f"automatically on a push to main.")
        assert _when_in(job, "push_main") == "on_success", (
            f"{name} no longer runs automatically on a push to main "
            f"(when={_when_in(job, 'push_main')!r}) — the #74 defect (image never "
            f"tracks main) is back, just with a green pipeline instead of a red one.")

    # GitLab refuses to build a pipeline where a `needs:` target's own `rules:` excluded it.
    assert ci["build:nightly-image"]["rules"] == ci["deploy:nightly-image"]["rules"], (
        "build:nightly-image and deploy:nightly-image have DIFFERENT rules: — "
        "deploy:nightly-image needs: [build:nightly-image], so if a pipeline ever "
        "creates one without the other, GitLab refuses to construct it at all.")

    # Without `needs:` the deploy could pin a tag the build has not pushed yet; without the shared
    # resource_group two concurrent builds race on the same Artifact Registry tag.
    assert ci["deploy:nightly-image"].get("needs") == ["build:nightly-image"], (
        "deploy:nightly-image must `needs: [\"build:nightly-image\"]` — without it, "
        f"the two jobs can run concurrently. needs={ci['deploy:nightly-image'].get('needs')!r}")
    build_rg = ci["build:nightly-image"].get("resource_group")
    deploy_rg = ci["deploy:nightly-image"].get("resource_group")
    assert build_rg and build_rg == deploy_rg, (
        "build:nightly-image and deploy:nightly-image must share ONE resource_group — "
        f"got build={build_rg!r}, deploy={deploy_rg!r}. Without it, concurrent pipelines "
        "can build/deploy this image at the same time.")

    # A job scheduled off `needs:` starts as soon as its own edges finish, regardless of stage, so
    # every gate must be an edge or a failing push could still be built into the image.
    required_gates = {"validate:governance", "test:python", "validate:secrets", "lint:python"}
    build_needs = set(ci["build:nightly-image"].get("needs") or [])
    missing = required_gates - build_needs
    assert not missing, (
        f"build:nightly-image's needs: is missing {sorted(missing)} — a push to main that "
        f"fails one of these can still have its content built into the prod image and pushed "
        f"before the failure is visible. needs={ci['build:nightly-image'].get('needs')!r}")


def test_data_paths_image_covers_what_the_nightly_image_actually_runs():
    """A path missing from `.data_paths_image` fails silently, since the image just does not rebuild."""
    import pathlib
    import re
    import fnmatch

    import yaml

    root = pathlib.Path(__file__).resolve().parents[1]
    ci = yaml.safe_load((root / ".gitlab-ci.yml").read_text(encoding="utf-8"))
    image_paths = ci.get(".data_paths_image")
    assert isinstance(image_paths, list) and image_paths, (
        ".data_paths_image is missing or not a list")

    entrypoint = (root / "deploy" / "nightly" / "entrypoint.sh").read_text(encoding="utf-8")
    invoked_scripts = sorted(set(re.findall(r"python\s+(scripts/\S+\.py)", entrypoint)))
    assert invoked_scripts, (
        "no `python scripts/*.py` invocation found in entrypoint.sh — this test has probably "
        "stopped recognising them, which makes it pass vacuously")

    for script in invoked_scripts:
        assert any(fnmatch.fnmatch(script, pat) for pat in image_paths), (
            f"entrypoint.sh runs {script!r}, but no pattern in .data_paths_image matches it — "
            f"a change there would not rebuild the image. patterns={image_paths!r}")

    # Non-script inputs: the image build itself and the two deploy/nightly files the container needs at runtime.
    for fixed in ("Dockerfile", ".dockerignore",
                  "deploy/nightly/entrypoint.sh", "deploy/nightly/profiles.yml"):
        assert fixed in image_paths, (
            f"{fixed!r} is an image input (Dockerfile COPY / kaniko build-context / "
            f"entrypoint dependency) but is missing from .data_paths_image. "
            f"patterns={image_paths!r}")
    assert ".gcloudignore" not in image_paths, (
        ".gcloudignore has no effect on what kaniko builds and must not trigger a rebuild — "
        "see the anchor's own comment in .gitlab-ci.yml for why.")


def test_every_job_using_gcp_auth_declares_id_tokens():
    """GitLab sets `$GITLAB_OIDC_TOKEN` only for a job that declares `id_tokens:` itself, and Google rejects a wrong `aud`."""
    import pathlib

    import yaml

    root = pathlib.Path(__file__).resolve().parents[1]
    ci = yaml.safe_load((root / ".gitlab-ci.yml").read_text(encoding="utf-8"))

    expected_aud = "https://gitlab.com"
    checked = 0
    for name, job in ci.items():
        if name.startswith(".") or not isinstance(job, dict) or "script" not in job:
            continue
        # The anchor expands inline, so its body identifies a consumer, not its name.
        if not any("GITLAB_OIDC_TOKEN" in step for step in (job.get("script") or [])):
            continue
        checked += 1
        aud = (job.get("id_tokens") or {}).get("GITLAB_OIDC_TOKEN", {}).get("aud")
        assert aud, (
            f"job {name!r} expands *gcp_auth but declares no id_tokens block, so "
            f"$GITLAB_OIDC_TOKEN will be empty and the job dies at the auth guard. "
            f"Merge the shared anchor: `<<: [*python, *gcp_job]`.")
        assert aud == expected_aud, (
            f"job {name!r} requests an id_token with aud={aud!r}, but the GCP provider "
            f"allows {expected_aud!r}. Google rejects the token exchange on a mismatch.")

    assert checked >= 3, (
        f"only {checked} jobs found using *gcp_auth — this test has probably stopped "
        f"recognising them, which makes it pass vacuously")


def test_every_job_except_the_nightly_is_guarded_against_schedules():
    """A scheduled pipeline runs on main, so any job matching the default branch would silently double the build."""
    import pathlib

    import yaml

    root = pathlib.Path(__file__).resolve().parents[1]
    ci = yaml.safe_load((root / ".gitlab-ci.yml").read_text(encoding="utf-8"))

    nightly = "data:nightly"
    jobs = {k: v for k, v in ci.items()
            if not k.startswith(".") and isinstance(v, dict) and "script" in v}
    assert nightly in jobs, f"{nightly} is missing — the schedule has nothing to run"

    def runs_on_a_schedule(job: dict) -> bool:
        """Evaluate `rules:` as GitLab would for a scheduled pipeline on main, whatever the rule order."""
        return _when_in(job, "schedule") != "never"

    for name, job in jobs.items():
        if name == nightly:
            continue
        assert not runs_on_a_schedule(job), (
            f"job {name!r} WILL RUN on a scheduled pipeline. Rules are first-match-wins "
            f"and a schedule is on main, so `$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH` "
            f"matches and `changes:` does not filter it. For data:build:main that means "
            f"a SECOND full prod warehouse build every night, silently. Put "
            f"`*not_on_schedule` first, or scope the job to an explicit source. "
            f"rules={job.get('rules')!r}")

    assert runs_on_a_schedule(jobs[nightly]), (
        f"{nightly} does not run on a schedule — the nightly build would never fire")


def test_ci_writes_the_dbt_profile_where_sqlfluff_looks_for_it():
    """dbt honours `DBT_PROFILES_DIR` but sqlfluff reads `profiles_dir` from `dbt_project/.sqlfluff`, so the two must agree.

    The comparison is textual so it runs offline."""
    import configparser
    import pathlib
    import re as _re

    import yaml

    root = pathlib.Path(__file__).resolve().parents[1]
    ci = yaml.safe_load((root / ".gitlab-ci.yml").read_text(encoding="utf-8"))

    assert "DBT_PROFILES_DIR" not in (ci.get("variables") or {}), (
        "DBT_PROFILES_DIR is set again in .gitlab-ci.yml `variables:`. It moves dbt "
        "WITHOUT moving sqlfluff, whose profiles_dir is pinned in dbt_project/.sqlfluff. "
        "Write the profile to the default ~/.dbt instead.")

    written = _re.search(r"cat\s*>\s*(\S+)/profiles\.yml", ci[".dbt_profile"])
    assert written, ".dbt_profile no longer writes a profiles.yml — this test is stale"
    ci_dir = written.group(1).rstrip("/")

    # Read as config, not grepped, so a moved key or changed section fails instead of passing silently.
    cfg = configparser.ConfigParser()
    cfg.read(root / "dbt_project" / ".sqlfluff", encoding="utf-8")
    lint_dir = cfg["sqlfluff:templater:dbt"]["profiles_dir"].strip().rstrip("/")

    assert ci_dir == lint_dir, (
        f"CI writes the dbt profile to {ci_dir!r} but dbt_project/.sqlfluff tells "
        f"sqlfluff to read it from {lint_dir!r}. `dbt deps` will pass and `sqlfluff "
        f"lint` will fail. Change the CI path, NOT .sqlfluff — local development reads "
        f"that file too.")

    # GitLab runs `script:` items in list order, so the profile must be written before the first dbt/sqlfluff call.
    # `\(?` matters: `data:build:mr` invokes dbt inside a subshell.
    marker = f"cat > {ci_dir}/profiles.yml"
    runs_tool = _re.compile(r"(?m)^\s*\(?\s*(cd \S+ && )?(dbt|sqlfluff)\s")
    for name, job in ci.items():
        if name.startswith(".") or not isinstance(job, dict):
            continue
        script = job.get("script") or []
        tool_at = next((i for i, s in enumerate(script) if runs_tool.search(s)), None)
        if tool_at is None:
            continue
        profile_at = next((i for i, s in enumerate(script) if marker in s), None)
        assert profile_at is not None, (
            f"job {name!r} runs dbt/sqlfluff but never writes the profile — it is "
            f"missing the *dbt_profile anchor")
        assert profile_at < tool_at, (
            f"job {name!r} writes the dbt profile at script step {profile_at} but "
            f"already invokes dbt/sqlfluff at step {tool_at}. GitLab runs script items "
            f"in order, so the profile must be written first or the run fails with "
            f"\"Could not find profile named 'football_data_pipeline'\".")


def test_shell_redirect_to_protected_path_needs_an_impact_map(repo):
    """Neither the post-command check nor the stop gate flags a protected file afterwards, so the redirect is gated."""
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
    scoped = CONTRACT_NO_IMPACT.replace(
        "scope_paths:\n", "scope_paths:\n  - docs/plain.md\n")
    write_contract(repo, scoped)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "docs/plain.md"), repo)
    assert not denied(out)


# --- the Artifact gate ---

def artifact_event(path="/tmp/mock.html", hook_event="PreToolUse") -> dict:
    return {"hook_event_name": hook_event, "tool_name": "Artifact",
            "tool_input": {"file_path": path}}


# A contract whose decisions_reserved is a real reservation, not the template's bare `- none`.
CONTRACT_RESERVED = CONTRACT.replace(
    "decisions_reserved:\n  - none",
    "decisions_reserved:\n  - what the Overview shows for a goalkeeper",
)


def test_artifact_denied_without_contract(repo):
    out, _ = run_hook("task_contract_gate.py", artifact_event(), repo)
    assert denied(out) and "needs a task contract" in out


def test_artifact_denied_when_nothing_is_reserved(repo):
    write_contract(repo)
    out, _ = run_hook("task_contract_gate.py", artifact_event(), repo)
    assert denied(out) and "decisions_reserved" in out


def test_artifact_allowed_with_a_real_reservation(repo):
    write_contract(repo, CONTRACT_RESERVED)
    out, _ = run_hook("task_contract_gate.py", artifact_event(), repo)
    assert not denied(out)


def test_artifact_allowed_when_nothing_open_is_stated_as_a_sentence(repo):
    write_contract(repo, CONTRACT.replace(
        "decisions_reserved:\n  - none",
        "decisions_reserved:\n  - none: the design is CPO-approved as mock "
        "f6348775 and this publishes it unchanged",
    ))
    out, _ = run_hook("task_contract_gate.py", artifact_event(), repo)
    assert not denied(out)


@pytest.mark.parametrize("reserved", [
    "decisions_reserved: >\n  none",
    "decisions_reserved: |\n  none",
    # The template's own two-line placeholder ends in `;`, not `>`.
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
    """An entry opening with `<` must not hide the real reservations after it."""
    write_contract(repo, CONTRACT.replace(
        "decisions_reserved:\n  - none",
        "decisions_reserved:\n  - <2s page load is a product call\n"
        "  - what the Overview shows for a goalkeeper",
    ))
    out, _ = run_hook("task_contract_gate.py", artifact_event(), repo)
    assert not denied(out)


def test_artifact_allowed_when_a_block_scalar_carries_real_content(repo):
    write_contract(repo, CONTRACT.replace(
        "decisions_reserved:\n  - none",
        "decisions_reserved: >\n  what the Overview shows for a goalkeeper",
    ))
    out, _ = run_hook("task_contract_gate.py", artifact_event(), repo)
    assert not denied(out)


# --- key ordering: `decisions_reserved:` must close the preceding block like every other top-level key ---

def test_reserved_block_cannot_forge_an_impact_map(repo):
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
    """An in-repo path outside scope_paths, so an implementation reusing `_gate_file_edit` would deny it."""
    write_contract(repo, CONTRACT_RESERVED)
    out, _ = run_hook("task_contract_gate.py",
                      artifact_event(str(repo / "dbt_project" / "models" / "other.sql")), repo)
    assert not denied(out)


def test_artifact_post_tool_use_does_not_emit_a_pretooluse_deny(repo):
    out, _ = run_hook("task_contract_gate.py",
                      artifact_event(hook_event="PostToolUse"), repo)
    assert not denied(out)


def blocked(out: str) -> bool:
    return '"decision": "block"' in out


# --- fail-open: a hook bug must never wedge a session ---

@pytest.mark.parametrize("script", [
    "task_contract_gate.py", "handover_in.py",
])
@pytest.mark.parametrize("junk", ["", "not json", "null", "[]", '{"tool_name": 5}'])
def test_hooks_fail_open_on_malformed_input(repo, script, junk, tmp_path):
    # A failing fake `glab` keeps the handover hook off the network on every machine.
    base = _fake_glab(tmp_path, fail=True) if script == "handover_in.py" else os.environ
    env = dict(base, CLAUDE_PROJECT_DIR=str(repo))
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, script)],
        input=junk, capture_output=True, text=True, env=env, cwd=str(repo), timeout=60,
    )
    assert r.returncode == 0
    assert not denied(r.stdout) and not blocked(r.stdout)


# --- handover_in: these tests put a fake `glab` first on PATH ---

def _fake_glab(tmp_path, body=None, fail=False, sleep=0):
    """A `glab` that answers `body` as the issue description or exits 1, and records its arguments."""
    bindir = tmp_path / "fakebin"
    bindir.mkdir()
    impl = bindir / "glab_fake.py"
    impl.write_text(
        "import json, sys, time\n"
        "open(%r, 'w', encoding='utf-8').write(' '.join(sys.argv[1:]))\n"
        "time.sleep(%r)\n"
        "if %r:\n    sys.exit(1)\n"
        "sys.stdout.buffer.write(json.dumps({'description': %r}).encode('utf-8'))\n"
        % (str(tmp_path / "glab_args.txt"), sleep, fail, body),
        encoding="utf-8")
    if os.name == "nt":
        (bindir / "glab.cmd").write_text('@"%s" "%s" %%*\n' % (sys.executable, impl))
    else:
        launcher = bindir / "glab"
        launcher.write_text('#!/bin/sh\nexec "%s" "%s" "$@"\n' % (sys.executable, impl))
        launcher.chmod(0o755)
    return dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ.get("PATH", ""))


def _handover(repo, env, event=None, cwd=None) -> str:
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "handover_in.py")],
        input=json.dumps({"cwd": str(repo)} if event is None else event),
        capture_output=True, text=True, cwd=str(cwd or repo),
        env=dict(env, CLAUDE_PROJECT_DIR=str(repo)), timeout=60,
    )
    return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]


CACHE = (".claude", "handover.cache.md")


def test_handover_injected_from_the_issue_and_saved(repo, tmp_path):
    body = "# Active work\nTHE GOAL: ship the site."
    ctx = _handover(repo, _fake_glab(tmp_path, body))
    assert "THE GOAL: ship the site." in ctx and "BEGIN HANDOVER" in ctx and "#157" in ctx
    assert (tmp_path / "glab_args.txt").read_text(encoding="utf-8") == "api projects/85168767/issues/157"
    assert repo.joinpath(*CACHE).read_text(encoding="utf-8") == body


def test_handover_cache_lands_at_the_project_root_from_a_subdirectory(repo, tmp_path):
    """A session started below the repo root must save and find the same copy."""
    sub = repo / "dbt_project" / "models"
    ctx = _handover(repo, _fake_glab(tmp_path, "THE GOAL: ship the site."), event={}, cwd=sub)
    assert "THE GOAL: ship the site." in ctx
    assert repo.joinpath(*CACHE).is_file() and not sub.joinpath(*CACHE).exists()


def test_handover_falls_back_to_the_saved_copy_when_gitlab_is_down(repo, tmp_path):
    repo.joinpath(*CACHE).write_text("SAVED COPY: ship the site.", encoding="utf-8")
    ctx = _handover(repo, _fake_glab(tmp_path, fail=True))
    assert "SAVED COPY: ship the site." in ctx
    assert "could not be reached" in ctx and "UTC" in ctx
    assert repo.joinpath(*CACHE).read_text(encoding="utf-8") == "SAVED COPY: ship the site.", (
        "a failed read must never overwrite the saved copy")


def test_handover_says_so_when_neither_exists(repo, tmp_path):
    ctx = _handover(repo, _fake_glab(tmp_path, fail=True))
    assert "No handover could be read" in ctx and "BEGIN HANDOVER" not in ctx


def test_an_empty_saved_copy_counts_as_none(repo, tmp_path):
    repo.joinpath(*CACHE).write_text("  \n", encoding="utf-8")
    ctx = _handover(repo, _fake_glab(tmp_path, fail=True))
    assert "No handover could be read" in ctx and "BEGIN HANDOVER" not in ctx


def test_the_handover_check_refuses_a_host_address_or_an_oversize_draft(tmp_path):
    """The address is assembled at run time because a literal one in this file is forbidden."""
    tool = os.path.join(os.path.dirname(__file__), "..", "design-mocks", "check_handover.py")
    drafts = {
        "clean": "# Active work\nNothing open. The runner is ci-runner-01.\n",
        "address": "# Active work\nThe runner answers on %s.\n" % ".".join(str(o) for o in (8, 8, 4, 4)),
        "oversize": "y" * 16001,
    }
    codes = {}
    for name, text in drafts.items():
        path = tmp_path / ("%s.md" % name)
        path.write_text(text, encoding="utf-8")
        codes[name] = subprocess.run([sys.executable, tool, str(path)], capture_output=True, text=True,
                                     env=dict(os.environ, PYTHONIOENCODING="utf-8"), timeout=60).returncode
    assert codes == {"clean": 0, "address": 1, "oversize": 1}, codes


def test_a_hanging_gitlab_read_times_out(tmp_path, monkeypatch):
    """Without the timeout a hanging GitLab holds the hook until the harness kills it, so no saved copy is used."""
    spec = importlib.util.spec_from_file_location("handover_in_under_test", os.path.join(HOOKS, "handover_in.py"))
    hook = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hook)
    monkeypatch.setattr(hook, "FETCH_TIMEOUT_S", 1)
    env = _fake_glab(tmp_path, "LATE ANSWER", sleep=5)
    monkeypatch.setenv("PATH", env["PATH"])
    assert hook.fetch() is None


def test_handover_announces_truncation(repo, tmp_path):
    ctx = _handover(repo, _fake_glab(tmp_path, "y" * 20000))
    assert "TRUNCATED" in ctx


def test_handover_under_the_cap_is_not_called_truncated_when_multibyte(repo, tmp_path):
    """The cap counts characters; a multibyte text under it but over the byte count must not be truncated."""
    text = "⭐" * 15900
    assert len(text) < 16000 < len(text.encode("utf-8"))
    ctx = _handover(repo, _fake_glab(tmp_path, text))
    assert "TRUNCATED" not in ctx
    assert text in ctx


# --- the review's own paperwork is outside the reviewed patch and the hash ---

def test_editing_an_evidence_artifact_does_not_change_the_staged_hash(repo):
    """The evidence artifacts are in hash_exclude_paths, so editing them must not void a PASS."""
    setup_review_repo(repo)
    before = staged_hash(repo)
    for name in ("acceptance_evidence.md", "rendered_page_evidence.md"):
        (repo / ".claude" / "task" / TASK_ID / name).write_text("evidence, rewritten\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    assert staged_hash(repo) == before, (
        "editing an evidence artifact changed the review hash, which voids every "
        "reviewer's PASS and forces a fresh round"
    )


def test_editing_the_contract_DOES_change_the_staged_hash(repo):
    """contract.md carries scope_paths and acceptance_criteria, so widening scope after review must break the hash."""
    setup_review_repo(repo)
    before = staged_hash(repo)
    (repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(
        "objective: something else entirely\nscope_paths:\n  - anywhere/**\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    assert staged_hash(repo) != before, (
        "contract.md left the review hash — scope could now be widened after "
        "every reviewer passed, with no gate noticing"
    )


def _review_patch(repo) -> str:
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "git_discipline.py"), "--review-patch"],
        cwd=str(repo), capture_output=True, text=True, env=env, timeout=60,
    )
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_review_patch_excludes_the_tasks_own_paperwork(repo):
    """Reviewers see code and contract.md, never the notes about the work."""
    setup_review_repo(repo)
    hidden = ("acceptance_evidence.md", "rendered_page_evidence.md",
              "review.md", "review_input.patch")
    for i, name in enumerate(hidden):
        (repo / ".claude" / "task" / TASK_ID / name).write_text(f"HIDDEN_MARKER_{i}\n")
    (repo / ".claude" / "active_work.md").write_text("HANDOVER_MARKER\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    patch = _review_patch(repo)
    for i, name in enumerate(hidden):
        assert f"HIDDEN_MARKER_{i}" not in patch, f"{name}'s content reached the patch"
        # Match the diff header, because review_routing.json lists these names as data.
        assert f"diff --git a/{TASK}{name}" not in patch, f"{name} is in the diff"
    assert "HANDOVER_MARKER" not in patch


def test_review_patch_DOES_deliver_the_rulings_log(repo):
    """A `protected_override` may cite `escalations.log`, so reviewers must be able to see it."""
    setup_review_repo(repo)
    (repo / ".claude" / "task" / TASK_ID / "escalations.log").write_text("LOG_MARKER\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    assert "LOG_MARKER" in _review_patch(repo), (
        "escalations.log did not reach the reviewers — they cannot verify a cited ruling"
    )


def test_review_patch_is_cumulative_not_just_the_last_increment(repo):
    """`git diff --staged` alone is index-vs-HEAD, which would give reviewers only the newest slice."""
    setup_review_repo(repo)
    subprocess.run(["git", "branch", "-f", "main", "HEAD"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", "feat/two-commits"], cwd=repo, check=True)
    # The two changes must be in different files, or a staged-only diff would show both markers.
    first = repo / "dbt_project" / "models" / "committed.sql"
    first.write_text("select 1 as FIRST_COMMIT_MARKER\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "first"], cwd=repo, check=True)
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 2 as STAGED_MARKER\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    patch = _review_patch(repo)
    assert "STAGED_MARKER" in patch
    assert "FIRST_COMMIT_MARKER" in patch, (
        "the reviewers received only the staged increment, not the whole branch"
    )


def test_review_patch_still_contains_the_code_and_the_contract(repo):
    """Reviewers must still receive the code diff and contract.md, which they check authority against."""
    setup_review_repo(repo)
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 1 as CODE_MARKER\n")
    (repo / ".claude" / "task" / TASK_ID / "contract.md").write_text("objective: CONTRACT_MARKER\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    patch = _review_patch(repo)
    assert "CODE_MARKER" in patch
    assert "CONTRACT_MARKER" in patch, (
        "contract.md must reach the reviewers — it carries the scope and the "
        "authority they are asked to check"
    )


def test_every_task_artifact_is_classified(repo):
    """Every tracked `.claude/task/` file is either excluded from review or an authority file reviewers must read."""
    excluded = real_routing().get("review_exclude_paths") or []
    files = tracked(".claude/task/")
    assert files, "no tracked files under .claude/task/ — has the tree moved?"

    def hidden(p):
        return any(fnmatch.fnmatch(p, pat) for pat in excluded)

    authority = (".claude/task/*/contract.md", ".claude/task/escalations.log")
    unclassified = [p for p in files
                    if not hidden(p) and not any(fnmatch.fnmatch(p, a) for a in authority)]
    assert not unclassified, (
        "these .claude/task/ files are neither hidden from reviewers nor one of the "
        f"two authority files, so reviewers will review their own paperwork: {unclassified}"
    )
    hidden_authority = sorted(
        p for p in (TASK + "contract.md", ".claude/task/escalations.log") if hidden(p))
    assert not hidden_authority, (
        f"authority files hidden from reviewers: {hidden_authority}"
    )


def test_real_routing_hides_the_evidence_artifacts_from_the_hash(repo):
    """Reads the real routing data, since the synthetic fixture cannot catch a deleted exclusion."""
    excl = real_routing().get("hash_exclude_paths") or []
    for p in (TASK + "acceptance_evidence.md",
              TASK + "rendered_page_evidence.md"):
        assert any(fnmatch.fnmatch(p, pat) for pat in excl), (
            f"{p} is back inside diff_sha256 — editing it now voids every "
            "reviewer's PASS and buys a fresh round"
        )
    assert not any(fnmatch.fnmatch(TASK + "contract.md", pat) for pat in excl), (
        "contract.md left the review hash — scope and acceptance_criteria could be "
        "widened after every reviewer passed (F10/F11, #409)"
    )


def _ci_repo_with_review(ci_repo, body: str):
    """Commit code and contract, then a review.md carrying the recomputed PR hash and `body`."""
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code+contract"], cwd=ci_repo, check=True)
    (ci_repo / ".claude" / "task" / TASK_ID / "review.md").write_text(
        "# Review\ndiff_sha256: " + branch_hash(ci_repo) + "\nrounds: 1\n\n" + body
    )
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "review"], cwd=ci_repo, check=True)
    return run_ci_check(ci_repo)


def test_ci_twin_accepts_a_pass_with_one_thing_examined(ci_repo):
    """The floor lives in both `git_discipline._commit_gate` and `check_task_artifacts.py` and must be equal."""
    body = GOOD_BODY.replace("- risk two checked\n", "", 1)
    code, out = _ci_repo_with_review(ci_repo, body)
    assert code == 0, out


def test_ci_twin_denies_a_pass_with_nothing_examined(ci_repo):
    """Zero entries is a rubber stamp, and the message text must match the hook's."""
    body = GOOD_BODY.replace("- risk one checked\n- risk two checked\n", "", 1)
    code, out = _ci_repo_with_review(ci_repo, body)
    assert code == 1, out
    assert "state what was examined" in out


def test_review_patch_fails_LOUD_when_git_fails(tmp_path):
    """A redirect truncates review_input.patch before the run, so a silent git failure would read as no changes.

    A directory with a routing file but no `.git` makes every git call fail."""
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "review_routing.json").write_text(json.dumps(ROUTING))
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(tmp_path))
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "git_discipline.py"), "--review-patch"],
        cwd=str(tmp_path), capture_output=True, text=True, env=env, timeout=60,
    )
    assert r.returncode != 0, "a git failure produced a successful exit"
    assert r.stdout == "", "a failed run still emitted patch bytes"
    assert "cumulative" in r.stderr or "patch" in r.stderr, r.stderr


def test_review_patch_refuses_a_base_that_shares_no_history(tmp_path, _repo_template):
    """A `main` with no common ancestor must be refused, never narrowed to the last increment."""
    dst = tmp_path / "unrelated"
    shutil.copytree(_repo_template, dst)
    setup_review_repo(dst)
    subprocess.run(["git", "commit", "-qm", "one"], cwd=dst, check=True)
    start = subprocess.run(["git", "branch", "--show-current"], cwd=dst,
                           capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(["git", "checkout", "-q", "--orphan", "main"], cwd=dst, check=True)
    (dst / "unrelated.txt").write_text("x\n")
    subprocess.run(["git", "add", "-A"], cwd=dst, check=True)
    subprocess.run(["git", "commit", "-qm", "orphan"], cwd=dst, check=True)
    subprocess.run(["git", "checkout", "-q", start], cwd=dst, check=True)
    (dst / "dbt_project" / "models" / "allowed.sql").write_text("select 99\n")
    subprocess.run(["git", "add", "-A"], cwd=dst, check=True)
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(dst))
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "git_discipline.py"), "--review-patch"],
        cwd=str(dst), capture_output=True, text=True, env=env, timeout=60,
    )
    assert r.returncode != 0, "unrelated histories produced a patch instead of refusing"
    assert "common ancestor" in r.stderr, r.stderr


def _routing_with(**extra) -> dict:
    r = json.loads(json.dumps(ROUTING))
    r.update(extra)
    return r


def test_unparseable_routing_announces_itself_instead_of_silently_disabling_review(repo):
    """`_load_routing` returns None on a parse error, which `_commit_gate` reads as gate not active."""
    # Something must be staged: `_commit_gate` returns before reading routing when the index is empty.
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 1\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    (repo / ".claude" / "review_routing.json").write_text('{"always": ["x",]}')
    out, _ = run_hook("git_discipline.py", bash_event('git commit -m "x"'), repo)
    assert "REVIEW ROUTING UNREADABLE" in out, out
    assert "DISABLED" in out
    assert not denied(out), "the canary must not turn a parse error into a hard block"


def test_routing_canary_never_pollutes_cli_stdout(repo):
    """As a hook, stdout carries the JSON protocol; as a CLI it is the product, so the canary goes to stderr."""
    setup_review_repo(repo)
    (repo / ".claude" / "review_routing.json").write_text('{"always": ["x",]}')
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    for flag, must_start in (("--review-patch", "diff --git"), ("--staged-hash", "")):
        r = subprocess.run(
            [sys.executable, os.path.join(HOOKS, "git_discipline.py"), flag],
            cwd=str(repo), capture_output=True, text=True, env=env, timeout=60,
        )
        assert "hookSpecificOutput" not in r.stdout, (
            f"{flag} emitted hook JSON into its product: {r.stdout[:200]}")
        assert "REVIEW ROUTING UNREADABLE" not in r.stdout, r.stdout[:200]
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "git_discipline.py"), "--review-patch"],
        cwd=str(repo), capture_output=True, text=True, env=env, timeout=60,
    )
    assert "did not parse" in r.stderr, r.stderr


def test_manifest_failure_is_loud_not_silent(repo):
    """Summarised paths leave the body on the promise of a manifest, so a manifest error must raise."""
    setup_review_repo(repo)
    sys.path.insert(0, HOOKS)
    import git_discipline  # noqa: E402
    # Malformed pathspec magic makes `git diff --stat` exit non-zero.
    with pytest.raises(Exception) as exc:
        git_discipline._summary_manifest(str(repo), [":(attr:!!bad)x"])
    assert "manifest" in str(exc.value).lower(), (
        f"raised, but not with the manifest explanation: {exc.value}")


def test_fast_gates_and_validate_local_agree(repo):
    """The FAST_GATES list and the validate-local skill describe the same turn-end set."""
    root = os.path.join(os.path.dirname(__file__), "..")
    sys.path.insert(0, HOOKS)
    import stop_gate  # noqa: E402
    skill = open(os.path.join(root, ".claude", "skills", "validate-local", "SKILL.md"),
                 encoding="utf-8").read()

    # Set equality over the marked region: each name appears several times elsewhere in SKILL.md.
    block = re.search(r"<!-- FAST_GATES:START -->(.*?)<!-- FAST_GATES:END -->",
                      skill, re.S)
    assert block, (
        "the FAST_GATES markers are gone from validate-local's SKILL.md; without them "
        "nothing states which gates run at turn end and this test cannot check anything"
    )
    documented = set(re.findall(r"`([A-Za-z0-9_]+)`", block.group(1)))
    actual = {os.path.basename(g)[: -len(".py")] for g in stop_gate.FAST_GATES}
    assert documented == actual, (
        f"validate-local documents {sorted(documented)} as the turn-end set but "
        f"FAST_GATES is {sorted(actual)}"
    )

    for rel in stop_gate.FAST_GATES:
        assert os.path.isfile(os.path.join(root, rel)), f"{rel} does not exist"

    assert not any("check_task_artifacts" in g for g in stop_gate.FAST_GATES), (
        "check_task_artifacts needs a fetched origin/main and a current review.md; in "
        "FAST_GATES it would block every turn end during the build phase"
    )


def test_missing_routing_file_stays_silent(repo):
    """A missing routing file is a legitimate state; only one that exists and will not parse is a defect."""
    path = repo / ".claude" / "review_routing.json"
    if path.exists():
        path.unlink()
    out, _ = run_hook("git_discipline.py", bash_event('git commit -m "x"'), repo)
    assert "REVIEW ROUTING UNREADABLE" not in out, out


def test_review_patch_excludes_summarise_paths_from_the_body(repo):
    """`review_summarise_paths` keeps generated data out of the pasted diff."""
    (repo / ".claude" / "review_routing.json").write_text(
        json.dumps(_routing_with(review_summarise_paths=["data/**"])))
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "routing"], cwd=repo, check=True)
    (repo / "data").mkdir(exist_ok=True)
    (repo / "data" / "sample.json").write_text('{"UNIQUE_MARKER_IN_BODY": 1}\n')
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 42\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "git_discipline.py"), "--review-patch"],
        cwd=str(repo), capture_output=True, text=True, env=env, timeout=60,
    )
    assert r.returncode == 0, r.stderr
    assert "UNIQUE_MARKER_IN_BODY" not in r.stdout, "sample data was pasted into the body"
    assert "select 42" in r.stdout, "excluding sample data must not drop real code"


def test_summarised_paths_are_announced_not_hidden(repo):
    """Excluding the body must not hide that the files changed, unlike `review_exclude_paths`."""
    (repo / ".claude" / "review_routing.json").write_text(
        json.dumps(_routing_with(review_summarise_paths=["data/**"])))
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "routing"], cwd=repo, check=True)
    (repo / "data").mkdir(exist_ok=True)
    (repo / "data" / "sample.json").write_text('{"a": 1}\n')
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "git_discipline.py"), "--review-patch"],
        cwd=str(repo), capture_output=True, text=True, env=env, timeout=60,
    )
    assert r.returncode == 0, r.stderr
    assert "NOT PASTED ABOVE" in r.stdout, "changed sample data was hidden with no manifest"
    assert "data/sample.json" in r.stdout, "the manifest must name the changed files"


def test_no_manifest_when_no_summarised_path_changed(repo):
    (repo / ".claude" / "review_routing.json").write_text(
        json.dumps(_routing_with(review_summarise_paths=["data/**"])))
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "routing"], cwd=repo, check=True)
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 7\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    r = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "git_discipline.py"), "--review-patch"],
        cwd=str(repo), capture_output=True, text=True, env=env, timeout=60,
    )
    assert "NOT PASTED ABOVE" not in r.stdout, r.stdout


def test_summarised_paths_still_bind_the_review_hash(repo):
    """`review_summarise_paths` sets what is read and `hash_exclude_paths` what binds the verdict; they must not merge."""
    (repo / ".claude" / "review_routing.json").write_text(
        json.dumps(_routing_with(review_summarise_paths=["data/**"])))
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "routing"], cwd=repo, check=True)
    (repo / "data").mkdir(exist_ok=True)
    (repo / "data" / "sample.json").write_text('{"a": 1}\n')
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    before = staged_hash(repo)
    (repo / "data" / "sample.json").write_text('{"a": 2}\n')
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    after = staged_hash(repo)
    assert before and after and before != after, (
        "changing a summarised file left the review hash unchanged — it would pass "
        "review verification without any reviewer having seen the new content"
    )


# --- review_exclude_paths: excluded files are hidden but announced in a trailer ---
def _stage_excluded_edit(repo, body: str = "handover body\n") -> None:
    """Stage a change to a `review_exclude_paths` member, plus real code alongside it."""
    (repo / ".claude" / "active_work.md").write_text(body)
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 42\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)


def _commit_routing(repo) -> None:
    (repo / ".claude" / "review_routing.json").write_text(json.dumps(ROUTING))
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "routing"], cwd=repo, check=True)


def test_excluded_paths_that_changed_are_named(repo):
    """A reviewer must be able to tell a file hidden on purpose from one never touched."""
    _commit_routing(repo)
    _stage_excluded_edit(repo)
    patch = _review_patch(repo)

    assert "NOT SHOWN (review_exclude_paths)" in patch, (
        "an edited excluded file was removed from the patch with nothing said, which is the "
        "inference that cost three review rounds"
    )
    assert ".claude/active_work.md" in patch, "the trailer must name the file"
    assert "select 42" in patch, "announcing excluded files must not drop real code"


def test_the_trailer_names_files_without_pasting_them(repo):
    """The trailer carries names and counts and no content."""
    _commit_routing(repo)
    _stage_excluded_edit(repo, "UNIQUE_MARKER_INSIDE_EXCLUDED_FILE\n")
    patch = _review_patch(repo)

    assert "NOT SHOWN (review_exclude_paths)" in patch, patch
    assert "UNIQUE_MARKER_INSIDE_EXCLUDED_FILE" not in patch, (
        "the trailer pasted the excluded file's CONTENT — it may name files, never quote them"
    )


def test_no_trailer_when_no_excluded_path_changed(repo):
    _commit_routing(repo)
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 7\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)

    assert "NOT SHOWN (review_exclude_paths)" not in _review_patch(repo)


def test_the_trailer_does_not_reach_the_review_hash(repo):
    """`--review-patch` and `--staged-hash` resolve different lists, so the trailer must not feed the hash."""
    _commit_routing(repo)
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 42\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    without_trailer = staged_hash(repo)

    _stage_excluded_edit(repo)
    with_trailer = staged_hash(repo)

    assert "NOT SHOWN (review_exclude_paths)" in _review_patch(repo), (
        "precondition: this test is meaningless unless a trailer is actually emitted"
    )
    assert without_trailer and with_trailer
    assert without_trailer == with_trailer, (
        "the trailer changed the review hash. It annotates what reviewers READ; the hash "
        "answers what BINDS a verdict, and conflating them is what made a typo cost a round"
    )


def test_excluded_trailer_failure_is_loud_not_silent(repo):
    """A trailer that can silently not appear re-creates the ambiguity it exists to remove."""
    setup_review_repo(repo)
    sys.path.insert(0, HOOKS)
    import git_discipline  # noqa: E402
    # Malformed pathspec magic makes `git diff --stat` exit non-zero.
    with pytest.raises(Exception) as exc:
        git_discipline._excluded_trailer(str(repo), [":(attr:!!bad)x"])
    # The full phrase, because the trailer's reason string also contains the bare word "trailer".
    assert "review patch trailer" in str(exc.value).lower(), (
        f"raised, but not identified as the trailer section: {exc.value}")


def _install_fast_gate(repo, body: str) -> None:
    """Commit a stub fast gate, because an uncommitted one is out of scope and the scope check fires first."""
    scripts = repo / "scripts"
    scripts.mkdir(exist_ok=True)
    (scripts / "check_layer_contract.py").write_text(body)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "fast gate stub"], cwd=repo, check=True)
    write_contract(repo)


def test_stop_gate_blocks_on_a_failing_fast_gate(repo):
    _install_fast_gate(repo, "import sys\nprint('- deliberate failure for the test')\nsys.exit(1)\n")
    # Dirty an in-scope file: correctness is only reached once the scope check passes.
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 5\n")
    out, _ = run_hook("stop_gate.py", {"hook_event_name": "Stop"}, repo)
    assert '"decision": "block"' in out, out
    assert "correctness" in out
    assert "check_layer_contract.py" in out


def test_stop_gate_passes_when_fast_gates_pass(repo):
    _install_fast_gate(repo, "print('ok')\n")
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 6\n")
    out, _ = run_hook("stop_gate.py", {"hook_event_name": "Stop"}, repo)
    assert out.strip() == "", out


def test_stop_gate_skips_correctness_on_a_clean_tree(repo):
    """A clean tree cannot have broken a passing gate, so a conversational turn skips the cost."""
    _install_fast_gate(repo, "import sys\nprint('would fail')\nsys.exit(1)\n")
    out, _ = run_hook("stop_gate.py", {"hook_event_name": "Stop"}, repo)
    assert out.strip() == "", "correctness ran on a clean tree"


def test_stop_gate_ignores_absent_fast_gates(repo):
    """Missing checker scripts are legitimate on other branches and worktrees."""
    write_contract(repo)
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 8\n")
    out, _ = run_hook("stop_gate.py", {"hook_event_name": "Stop"}, repo)
    assert out.strip() == "", out


def test_stop_gate_reports_scope_violation_before_correctness(repo):
    """An out-of-scope tree is the more actionable failure, so it is reported alone and first."""
    _install_fast_gate(repo, "import sys\nsys.exit(1)\n")
    (repo / "stray.txt").write_text("out of scope\n")
    out, _ = run_hook("stop_gate.py", {"hook_event_name": "Stop"}, repo)
    assert '"decision": "block"' in out
    assert "does not match the task contract" in out
    assert "correctness" not in out


_GATE_PASSES_ONLY_IN_REPO_VENV = (
    "import os, sys\n"
    "venv = os.path.realpath(os.path.join(os.getcwd(), '.venv'))\n"
    "if os.path.normcase(os.path.realpath(sys.prefix)) != os.path.normcase(venv):\n"
    "    print('- ran outside the repo .venv')\n"
    "    sys.exit(1)\n"
)


def test_stop_gate_runs_gates_with_the_repo_venv(repo):
    """The hook starts under the system Python, which lacks the gates' packages, so gates must run in the repo `.venv`."""
    import venv

    (repo / ".gitignore").write_text(".venv/\n")
    _install_fast_gate(repo, _GATE_PASSES_ONLY_IN_REPO_VENV)
    venv.create(repo / ".venv", with_pip=False)
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 9\n")
    out, _ = run_hook("stop_gate.py", {"hook_event_name": "Stop"}, repo)
    assert out.strip() == "", out


def test_stop_gate_without_a_venv_runs_gates_with_its_own_python(repo):
    """With no `.venv` the gates run under the hook's own Python, and a failure still blocks."""
    _install_fast_gate(repo, _GATE_PASSES_ONLY_IN_REPO_VENV)
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 10\n")
    out, _ = run_hook("stop_gate.py", {"hook_event_name": "Stop"}, repo)
    assert '"decision": "block"' in out, out
    assert "ran outside the repo .venv" in out
    assert sys.executable in out.replace("\\\\", "\\")


# --- task_contract_gate: approved-design gate for the page surface ---
_PAGE_CONTRACT = CONTRACT.replace(
    "scope_paths:\n",
    "scope_paths:\n  - site_v2/src/pages/home.astro\n  - scripts/export_site_data.py\n",
)


def _with_design(block: str) -> str:
    return _PAGE_CONTRACT.replace("decisions_taken:", f"approved_design:\n{block}\ndecisions_taken:")


@pytest.mark.parametrize("rel", ["site_v2/src/pages/home.astro", "scripts/export_site_data.py"])
def test_page_surface_edit_denied_without_approved_design(repo, rel):
    write_contract(repo, _PAGE_CONTRACT)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, rel), repo)
    assert denied(out) and "approved_design" in out


def _approve_on_base(repo, monkeypatch, text: str = "home: 127\nmatch: 132\n") -> None:
    """Commit the approved-designs list on a base ref only, so the working branch has no copy."""
    root = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"], cwd=repo,
                          capture_output=True, text=True, check=True).stdout.split()[0]
    subprocess.run(["git", "checkout", "-q", "-b", "base_main", root], cwd=repo, check=True)
    path = repo / "docs" / "wireframes" / "approved_designs.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "approved"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-q", "-"], cwd=repo, check=True)
    monkeypatch.setenv("GOVERNANCE_BASE", "base_main")


@pytest.mark.parametrize("block", [
    "  - home: #127",
    "  - home: #127\n  - match: #132",
    "  - Home: #127",
    "  - none: no page output changes",
])
def test_page_surface_edit_allowed_with_a_design_on_main(repo, monkeypatch, block):
    _approve_on_base(repo, monkeypatch)
    write_contract(repo, _with_design(block))
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "site_v2/src/pages/home.astro"), repo)
    assert not denied(out), out


def test_a_none_line_needs_no_list(repo, monkeypatch):
    monkeypatch.setenv("GOVERNANCE_BASE", "no_such_ref")
    write_contract(repo, _with_design("  - none: no page output changes"))
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "site_v2/src/pages/home.astro"), repo)
    assert not denied(out), out


@pytest.mark.parametrize("block, named", [
    ("  - player: #136", "player: #136"),
    ("  - home: #128", "home: #128"),
    ("  - home: #127\n  - player: #136", "player: #136"),
    ("  - see #127", "#127"),
])
def test_page_surface_edit_denied_for_a_design_not_on_main(repo, monkeypatch, block, named):
    _approve_on_base(repo, monkeypatch)
    write_contract(repo, _with_design(block))
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "site_v2/src/pages/home.astro"), repo)
    assert denied(out) and named in out and "approved_designs.yml" in out


def test_the_branch_copy_of_the_list_does_not_count(repo, monkeypatch):
    _approve_on_base(repo, monkeypatch, "match: 132\n")
    path = repo / "docs" / "wireframes" / "approved_designs.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("home: 127\n")
    write_contract(repo, _with_design("  - home: #127"))
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "site_v2/src/pages/home.astro"), repo)
    assert denied(out) and "home: #127" in out


def test_an_unreadable_list_denies_the_edit(repo, monkeypatch):
    monkeypatch.setenv("GOVERNANCE_BASE", "no_such_ref")
    write_contract(repo, _with_design("  - home: #127"))
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "site_v2/src/pages/home.astro"), repo)
    assert denied(out) and "home: #127" in out and "no_such_ref" in out


def test_shell_write_to_the_page_surface_needs_a_design_on_main(repo, monkeypatch):
    _approve_on_base(repo, monkeypatch)
    write_contract(repo, _with_design("  - player: #136"))
    out, _ = run_hook("task_contract_gate.py", bash_event("echo x >> site_v2/src/pages/home.astro"), repo)
    assert denied(out) and "player: #136" in out


@pytest.mark.parametrize("block, named", [
    ("  - match: #132, player: #136", "player: #136"),
    ("  - match: #132 and #136", "#136"),
])
def test_every_design_on_a_contract_line_is_checked(repo, monkeypatch, block, named):
    _approve_on_base(repo, monkeypatch)
    write_contract(repo, _with_design(block))
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "site_v2/src/pages/home.astro"), repo)
    assert denied(out) and named in out


@pytest.mark.parametrize("named, allowed", [("match: #132", True), ("player: #136", False)])
def test_a_list_with_a_non_utf8_byte_still_gates(repo, monkeypatch, named, allowed):
    root = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"], cwd=repo,
                          capture_output=True, text=True, check=True).stdout.split()[0]
    subprocess.run(["git", "checkout", "-q", "-b", "base_main", root], cwd=repo, check=True)
    path = repo / "docs" / "wireframes" / "approved_designs.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"# caf\xe9 \x97 list\nmatch: 132\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "approved"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-q", "-"], cwd=repo, check=True)
    monkeypatch.setenv("GOVERNANCE_BASE", "base_main")
    write_contract(repo, _with_design(f"  - {named}"))
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "site_v2/src/pages/home.astro"), repo)
    assert denied(out) is not allowed, out


@pytest.mark.parametrize("text, expected", [
    ("home: 127\n", {("home", 127)}),
    ("home: #127\n", {("home", 127)}),
    ("home: 127  # the home page\n", {("home", 127)}),
    ("home: 127\r\nmatch: 132\r\n", {("home", 127), ("match", 132)}),
    ("  home: 127\n", {("home", 127)}),
    ("# home: 127\n", set()),
    ("Home: 127\n", set()),
    ("- home: 127\n", set()),
    ("home: soon\n", set()),
])
def test_the_approved_list_parser(text, expected):
    sys.path.insert(0, HOOKS)
    import task_contract_gate as tcg
    assert tcg.parse_approved(text) == expected


def test_every_entry_of_the_shipped_approved_list_parses():
    sys.path.insert(0, HOOKS)
    import task_contract_gate as tcg
    shipped = os.path.join(os.path.dirname(__file__), "..", tcg.APPROVED_DESIGNS)
    with open(shipped, encoding="utf-8") as f:
        text = f.read()
    entries = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    assert entries and len(tcg.parse_approved(text)) == len(entries)


@pytest.mark.parametrize("block", ["  - none", "  - none:", "  - <page>: #<issue>", "  >", "", "  # later"])
def test_empty_or_placeholder_approved_design_does_not_satisfy(repo, block):
    write_contract(repo, _with_design(block))
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "site_v2/src/pages/home.astro"), repo)
    assert denied(out) and "approved_design" in out


def test_shell_write_to_the_page_surface_needs_approved_design(repo):
    write_contract(repo, _PAGE_CONTRACT)
    out, _ = run_hook("task_contract_gate.py", bash_event("echo x >> site_v2/src/pages/home.astro"), repo)
    assert denied(out) and "approved_design" in out


@pytest.mark.parametrize("block", ["  - <page>: #<issue>", ""])
def test_a_page_issue_after_the_block_does_not_count(repo, block):
    """The block ends at the next top-level key: an issue number there is not a design approval."""
    contract = _with_design(block).replace("decisions_taken: >\n  test", "decisions_taken: >\n  see #127")
    write_contract(repo, contract)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "site_v2/src/pages/home.astro"), repo)
    assert denied(out) and "approved_design" in out


def test_approved_design_block_cannot_append_to_scope_paths(repo):
    write_contract(repo, _with_design("  - home: #127\n  - site_v2/src/pages/other.astro"))
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "site_v2/src/pages/other.astro"), repo)
    assert denied(out) and "OUTSIDE" in out


def test_off_the_page_surface_needs_no_approved_design(repo):
    write_contract(repo, CONTRACT_NO_IMPACT)
    out, _ = run_hook("task_contract_gate.py", edit_event(repo, "docs/allowed_dir/page.md"), repo)
    assert out.strip() == ""


def test_ci_design_check_passes_a_design_on_main_and_fails_the_rest(repo, monkeypatch):
    ci = _ci_module()
    _approve_on_base(repo, monkeypatch)
    write_contract(repo, _with_design("  - home: #127\n  - player: #136"))
    errors = ci.design_errors(["site_v2/src/pages/home.astro"], str(repo), "base_main", TASK)
    assert len(errors) == 1 and "`player: #136`" in errors[0] and "base_main" in errors[0]


def test_ci_design_check_fails_closed_when_the_list_cannot_be_read(repo):
    ci = _ci_module()
    write_contract(repo, _with_design("  - home: #127"))
    errors = ci.design_errors(["site_v2/src/pages/home.astro"], str(repo), "no_such_ref", TASK)
    assert len(errors) == 1 and "`home: #127`" in errors[0]


def test_ci_design_check_fails_a_page_diff_without_the_field(repo):
    ci = _ci_module()
    write_contract(repo, _PAGE_CONTRACT)
    errors = ci.design_errors(["scripts/export_site_data.py"], str(repo), "no_such_ref", TASK)
    assert len(errors) == 1 and "names no approved design" in errors[0]


def test_ci_design_check_ignores_a_diff_off_the_page_surface(repo):
    ci = _ci_module()
    write_contract(repo, CONTRACT)
    assert ci.design_errors(["docs/allowed_dir/page.md"], str(repo), "no_such_ref", TASK) == []


def test_ci_design_check_needs_no_list_for_a_none_line(repo):
    ci = _ci_module()
    write_contract(repo, _with_design("  - none: no page output changes"))
    assert ci.design_errors(["site_v2/src/pages/home.astro"], str(repo), "no_such_ref",
                            TASK) == []


def test_ci_check_runs_the_design_check_on_a_page_diff(ci_repo):
    """End to end through main(): a page diff whose design stands only in the branch's own list fails."""
    (ci_repo / "site_v2" / "src" / "pages").mkdir(parents=True, exist_ok=True)
    (ci_repo / "site_v2" / "src" / "pages" / "home.astro").write_text("<h1>x</h1>\n")
    (ci_repo / "docs" / "wireframes").mkdir(parents=True, exist_ok=True)
    (ci_repo / "docs" / "wireframes" / "approved_designs.yml").write_text("home: 127\n")
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(_with_design("  - home: #127"))
    (ci_repo / ".claude" / "task" / TASK_ID / "review.md").write_text("diff_sha256: " + "0" * 64 + "\nrounds: 1\n")
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "page"], cwd=ci_repo, check=True)
    r = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "check_task_artifacts.py"), "--base", "main"],
        capture_output=True, text=True, cwd=str(ci_repo), timeout=60,
    )
    assert r.returncode == 1 and "`home: #127`" in r.stdout
