"""Offline tests for the governance hooks (G2): task_contract_gate, stop_gate,
git_discipline flag denies. Each test drives the hook script as Claude Code does
— event JSON on stdin, CLAUDE_PROJECT_DIR env — against a throwaway git repo.
No BigQuery, no network.
"""

from __future__ import annotations

import fnmatch
import json
import os
import shutil
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


@pytest.fixture(scope="session")
def _repo_template(tmp_path_factory):
    """The throwaway repo, built ONCE per session. Every `repo` below copies this
    instead of running `git init` + 2 configs + add + commit per test — six
    subprocess spawns each, over ~200 tests, which is what made the suite take
    ~11 minutes. A git repo is path-independent, so a copied `.git` keeps the
    initial commit and each copy mutates in isolation (review-economics trim,
    2026-07-22)."""
    base = tmp_path_factory.mktemp("repo_template")
    subprocess.run(["git", "init", "-q"], cwd=base, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=base, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=base, check=True)
    (base / ".claude" / "task").mkdir(parents=True)
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
# The REAL routing file. Everything below this block uses a synthetic fixture,
# which is correct for testing the gate's mechanics — but it meant nothing ever
# tested the routing DATA. On 2026-07-22 a routing change shipped that missed six
# tracked files, including `site_v2/src/lib/metricRows.ts` (the CPO-locked 16-row
# display contract), because it was "verified" by a one-off manual evaluation
# against two paths that did not exist. These tests load the real file and
# enumerate the real tree, so that class of miss fails the build instead.
# --------------------------------------------------------------------------- #
REAL_ROUTING_PATH = os.path.join(
    os.path.dirname(__file__), "..", ".claude", "review_routing.json")


def real_routing() -> dict:
    with open(REAL_ROUTING_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def required_reviewers(routing: dict, path: str) -> set:
    """Calls the REAL matcher, imported from the hook. Not a reimplementation.

    An earlier version mirrored it by hand and added `pat.endswith("/**") and
    path.startswith(...)`, a clause the hook and the CI backstop do not have —
    so the test was strictly MORE PERMISSIVE than the two things it certifies,
    and would go green on a route the gate does not enforce. They agree today
    only because no `/**` pattern has an fnmatch metacharacter in its prefix,
    and this tree's own directories are `[lang]`, `[competition]`, `[fixture]`,
    so that is luck rather than design. Testing a model of the system instead of
    the system is the exact root cause this whole change exists to fix
    (cto-reviewer, 2026-07-22)."""
    return _gd()._required_reviewers([path], routing)


def _gd():
    """The hook module. Its `main()` is `__main__`-guarded, so importing is
    side-effect free."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".claude", "hooks"))
    import git_discipline
    return git_discipline


def tracked(prefix: str) -> list[str]:
    """NUL-separated, like `git_discipline.py` and `check_task_artifacts.py`.

    Without `-z`, a tracked path containing a space splits into fragments and a
    non-ASCII one comes back quote-escaped (`"site_v2/src/caf\\303\\251.astro"`),
    so it fails the prefix filter and silently leaves the coverage set — the
    under-enumeration bug this repo already fixed twice in the hooks themselves.
    A test whose one promise is "every tracked file is covered" must not
    under-enumerate (cto-reviewer, 2026-07-22)."""
    r = subprocess.run(["git", "ls-files", "-z", prefix], capture_output=True, text=True,
                       cwd=os.path.join(os.path.dirname(__file__), ".."))
    assert r.returncode == 0, f"git ls-files failed: {r.stderr}"
    return [p for p in r.stdout.split("\0") if p]


def test_every_reviewer_brief_carries_the_identical_delta_section():
    """The delta-re-review rule must read the same in all six briefs; a reviewer
    that received a drifted copy would apply a different rule. Enumerated from the
    real agents directory, not a hand list (review-economics, 2026-07-22)."""
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
    (ci_repo / ".claude" / "task" / "contract.md").write_text(CONTRACT)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code+contract"], cwd=ci_repo, check=True)
    real_hash = branch_hash(ci_repo)
    # a complete review EXCEPT the rounds line
    (ci_repo / ".claude" / "task" / "review.md").write_text(
        "# Review\ndiff_sha256: " + real_hash + "\n\n" + GOOD_BODY)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "review"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "rounds:" in out


def test_ci_backstop_reuses_the_canonical_hook_logic():
    """The CI backstop must not re-implement the round cap or the nullish/
    structural logic — it diverged once (the override placeholder set, the
    `(none)` spelling, the export regex) and nothing caught it. Assert CI calls
    the hooks' own functions, and that the two nullish sets are identical, so a
    future hand-copy is impossible to land green (cto-reviewer, 2026-07-22)."""
    import importlib
    gd = _gd()                                  # inserts .claude/hooks on the path
    sys.path.insert(0, SCRIPTS)
    ci = importlib.import_module("check_task_artifacts")
    tcg = importlib.import_module("task_contract_gate")
    # CI's round check IS the hook's, not a copy
    assert ci._rounds_error.__doc__ is not None
    assert ci._rounds_error("rounds: 1\n") is None
    assert ci._rounds_error("rounds: 4\nrounds_cap_override: tbd\n") is not None
    assert ci._rounds_error("rounds: 4\nrounds_cap_override: real reason\n") is None
    # the two nullish sets agree, exactly
    assert set(gd._NULLISH_WORDS) == set(tcg._NULLISH), (
        "git_discipline._NULLISH_WORDS has drifted from task_contract_gate._NULLISH")


def test_empty_cap_override_does_not_absorb_the_next_line(repo):
    """`rounds_cap_override:` with no inline value must NOT capture the following
    `## header` as its reason (cto-reviewer, 2026-07-22)."""
    setup_review_repo(repo)
    write_review(repo, staged_hash(repo), GOOD_BODY,
                 rounds="rounds: 4\nrounds_cap_override:\n")
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "cap" in out


@pytest.mark.parametrize("word", ["tbd", "none", "(none)", "n/a", "todo", "-"])
def test_word_placeholder_cap_override_rejected(repo, word):
    """The word-placeholders, not just `<...>`, must be rejected — the CI copy
    used to accept them (cto-reviewer, 2026-07-22)."""
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
    """The binding rule (00_overview.md, "the whole point") says a block may
    reference only fields that exist in the export. bi-analyst-reviewer enforces
    it. If ANY file that can render a field escapes that reviewer, a fabricated
    metric ships unseen — which is exactly what was planned on 2026-07-22.

    Enumerated from `git ls-files`, not from a hand-written list, because the
    hand-written list is what was wrong."""
    r = real_routing()
    files = [f for f in tracked("site_v2") if f.startswith("site_v2/src/")]
    assert files, "no tracked files under site_v2/src — has the tree moved?"
    missing = [f for f in files
               if "bi-analyst-reviewer" not in required_reviewers(r, f)]
    assert not missing, f"frontend source escaping the display reviewer: {missing}"


def test_every_tracked_frontend_non_source_file_gets_platform_review():
    """The POSITIVE mirror, and the coverage that `site_v2/**` used to guarantee
    for free. The CTO split replaced that glob with six file names and two
    directory globs, because fnmatch's `*` crosses `/` and `site_v2/*.json` would
    also match `site_v2/src/data/*.json`. Enumeration is exact but not
    self-extending: without this test the next root-level build file
    (`vitest.config.ts`, `.npmrc`, a postcss config) routes to NOBODY and the suite
    stays green.

    Both cto-reviewer and platform-reviewer raised this independently at opus on
    2026-07-31, citing this file's own docstrings three times over: a hand-written
    list is what was wrong the last three times. `site_v2/.gitignore` is included
    deliberately — a path covered today does not lose coverage in a split."""
    r = real_routing()
    outside = [f for f in tracked("site_v2") if not f.startswith("site_v2/src/")]
    assert outside, "no tracked files outside site_v2/src — has the tree moved?"
    missing = [f for f in outside
               if "platform-reviewer" not in required_reviewers(r, f)]
    assert not missing, (
        f"site_v2 build/hosting files with NO platform review: {missing}. Add each "
        "to review_routing.json by NAME (never a glob that could reach src/).")


def test_frontend_build_config_does_not_get_the_display_reviewer():
    """The other direction. A guard that cries wolf gets ignored, so a dependency
    bump or a build-config edit must NOT demand a display review.

    Enumerated from `git ls-files`, like the direction above. This was a
    three-item hand list — `astro.config.mjs`, `package.json`, `tsconfig.json` —
    which already missed the two other tracked non-source files
    (`package-lock.json`, `.gitignore`) and would miss whatever lands outside
    `src` next. Writing one direction from the real tree and the other from a
    literal is the same defect at half scale, in the file whose whole thesis is
    "enumerate the real tree" (cto-reviewer, 2026-07-22)."""
    r = real_routing()
    outside = [f for f in tracked("site_v2") if not f.startswith("site_v2/src/")]
    assert outside, "no tracked files outside site_v2/src — has the tree moved?"
    stray = [f for f in outside
             if "bi-analyst-reviewer" in required_reviewers(r, f)]
    assert not stray, f"non-source file demanding a display review: {stray}"


# One representative path per routing pattern, each asserting the reviewer THAT
# pattern is responsible for. A module constant rather than an inline literal
# because the coverage test below derives from it — see its docstring.
PINNED_CASES = [
    ("dbt_project/models/5_marts/shared/mart_team_profile.sql", "analytics-engineer-reviewer"),
    ("dbt_project/seeds/metric_catalogue.csv", "football-analytics-expert-reviewer"),
    ("ingestion/api_football/main.py", "data-engineer-reviewer"),
    ("docs/competition_registry.yml", "data-engineer-reviewer"),
    ("docs/data_contract.md", "data-engineer-reviewer"),
    ("scripts/export_site_data.py", "analytics-engineer-reviewer"),
    # The CTO split (#868, 2026-07-31): the territory moved to platform-reviewer,
    # so these four pins moved with it. The CTO is no longer routed to scripts/,
    # tests/ or site_v2/ at all — it is woken by a PROPERTY of the change.
    ("scripts/sync_dbt_vars.py", "platform-reviewer"),
    ("tests/test_governance_hooks.py", "platform-reviewer"),
    ("requirements.txt", "cto-reviewer"),
    # Pins the `*requirements*.txt` correction: fnmatch full-string-matches, so
    # the old `requirements*.txt` anchored at the start of the path and this file
    # never reached the dependency threshold at all.
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
    ("docs/wireframes/02_team_profile.md", "bi-analyst-reviewer"),
    ("site/i18n/de.json", "bi-analyst-reviewer"),
    ("site_v2/src/lib/metricRows.ts", "bi-analyst-reviewer"),
    # site_v2/** is gone and the build surface is enumerated by NAME, because
    # fnmatch's `*` crosses `/` and `site_v2/*.json` would also match
    # site_v2/src/data/*.json, re-creating the 48-file overlap the split removed.
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
    """A routing edit must be additive: widening one route cannot silently
    narrow another. Every pattern in the table is pinned — enforced, not
    claimed, by the test below."""
    assert expected in required_reviewers(real_routing(), path)


def test_every_routing_pattern_is_pinned_by_the_test_above():
    """Guards the guard: if a new route is added and nobody pins it, fail here
    rather than let the pin test quietly cover a shrinking share of the table.

    DERIVED from `PINNED_CASES`, never a second hand-written list. It was such a
    list, and it had already drifted: `site_v2/**` and
    `dbt_project/seeds/competition_registry.csv` sat in it with no case pinning
    them, so deleting either route left the whole suite green — frontend build
    config would have lost platform review silently. A hand-typed copy of a list
    is a list that desynchronises (cto-reviewer, 2026-07-22).

    A pattern counts as pinned only when some case both MATCHES it and asserts a
    reviewer that pattern actually confers. Matching alone is not enough:
    `site_v2/src/lib/metricRows.ts` matches `site_v2/**` too, but it asserts
    `bi-analyst-reviewer`, which says nothing about whether `site_v2/**` still
    routes to the CTO."""
    routing = real_routing()
    unpinned = [
        pattern for pattern, reviewers in routing["paths"].items()
        if not any(fnmatch.fnmatch(path, pattern) and expected in reviewers
                   for path, expected in PINNED_CASES)
    ]
    assert not unpinned, f"unpinned routing patterns: {sorted(unpinned)}"


def test_copy_gate_parses_the_real_strings_file():
    """Pins the fragile part of `scripts/check_copy_gate.py`: the regex that pulls
    dictionary entries out of `strings.ts`. If it silently matches nothing, the
    gate reports a clean pass over zero strings, which is worse than no gate.

    strings.ts's own header explains why every value is double-quoted: the build
    gate `check-page-specs.mjs` extracts keys on the double quote, so rewriting an
    entry as a backtick template drops it from the checked set. The same fragility
    applies here, so it is pinned here (CPO ruling 2026-07-31, #868)."""
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
    """The dead-role flag is the whole reason `activation()` was rewritten, and it
    was unreachable in the first version: a `Counter` only holds keys it was
    incremented for, so it could never yield a zero and the branch never ran —
    while a dead role existed in the repo. Seeding from the agent briefs UNION the
    routed names fixed it.

    HERMETIC, and that is load-bearing rather than tidiness. The first version
    called `activation(n=6)` against real history and asserted `total` was non-zero.
    `python-ci.yml` runs `pytest tests/` behind `actions/checkout@v4` with the
    default `fetch-depth: 1`, so on a `pull_request` HEAD is `refs/pull/N/merge`
    with no parents fetched: `git log -n 6` yields one sha and `diff-tree` prints
    nothing for a merge without `-m`, so `total == 0` and the assertion would have
    reddened **every PR in the repo, including this branch's own**. The irony was
    that `report_process_health.py` documents exactly that shape and handles it,
    while the test asserted it could not happen. Caught by platform-reviewer at
    opus, round 4. Faking `_git` also removes seven subprocess spawns and lets one
    test pin the counting as well as the roster."""
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
    """The branch that closed the `ZeroDivisionError` was the one thing nothing
    exercised — platform-reviewer's own words in round 4, and it was right. An empty
    range is the realistic CI shape (see the test above), so `main()` must report
    and exit 0 rather than divide by zero."""
    health = _health()
    monkeypatch.setattr(health, "_git", _fake_git({}))
    assert health.main() == 0
    assert "no file-bearing commits in range" in capsys.readouterr().out


def test_copy_gate_floor_is_in_the_gate_not_only_in_this_test(tmp_path, monkeypatch):
    """Pins `check_copy_gate.MIN_KEYS`, the floor INSIDE the gate.

    The test above asserts >= 20 against the real `strings.ts`, which proves the
    regex works today but says nothing about the gate: set `MIN_KEYS = 0`, or delete
    the `thin` block, and the suite stayed green while `main()` would print
    "COPY GATE ok: 0 strings" and return 0 over a broken regex. That is the exact
    failure the floor exists to prevent, and it was the floor's own coverage gap.
    Caught by platform-reviewer at opus, round 3 — the same finding class it had
    already raised twice, which is why it is pinned by driving `main()` rather than
    by inspecting a constant.

    A dictionary whose values are backtick templates matches `_DICT_RE` but yields
    ZERO entries from `_ENTRY_RE` — the fragility `strings.ts`'s own header warns
    about, since `check-page-specs.mjs` extracts keys on the double quote too."""
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


def test_routing_has_no_duplicate_keys():
    """`paths` is a JSON OBJECT, so two identical pattern keys are not a merge —
    `json.load` keeps the LAST one and the other reviewer requirement vanishes
    with no signal. Neither consumer detects it and no other test would either,
    because the parsed dict looks perfectly well-formed.

    Live risk as of the CTO split (#868): five patterns are deliberately shared
    between `cto-reviewer` and `platform-reviewer`, and the natural way to write
    that change is one key per role. `object_pairs_hook` sees the raw pairs
    BEFORE the dict collapses them, so this is exact rather than a regex guess.

    Found by the pre-CPO plan challenge on 2026-07-31, not in review."""
    def reject_dupes(pairs):
        seen = set()
        for key, _ in pairs:
            assert key not in seen, f"duplicate JSON key silently collapsed: {key!r}"
            seen.add(key)
        return dict(pairs)

    with open(REAL_ROUTING_PATH, encoding="utf-8") as fh:
        json.loads(fh.read(), object_pairs_hook=reject_dupes)


def test_frontend_source_gets_no_authority_or_platform_review():
    """The regression guard for what motivated the CTO split (#868). Before it,
    `site_v2/**` routed to `cto-reviewer` while `site_v2/src/**` routed to
    `bi-analyst-reviewer`, so 48 distinct tracked files demanded BOTH and a CTO
    reviewed Astro markup — the wrong altitude, and it spent the one role with
    architectural authority on line review.

    Enumerated from `git ls-files`, like its two siblings above, because a
    hand-written list is what was wrong the last three times."""
    r = real_routing()
    files = [f for f in tracked("site_v2") if f.startswith("site_v2/src/")]
    assert files, "no tracked files under site_v2/src — has the tree moved?"
    stray = {f: sorted(required_reviewers(r, f) & {"cto-reviewer", "platform-reviewer"})
             for f in files
             if required_reviewers(r, f) & {"cto-reviewer", "platform-reviewer"}}
    assert not stray, f"frontend source pulling in authority/platform review: {stray}"


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
        ".claude/task/acceptance_evidence.md",
        ".claude/task/rendered_page_evidence.md",
    ],
    # Mirrors the REAL review_exclude_paths. escalations.log is deliberately ABSENT:
    # it is authority, not a note, so reviewers must receive it (cto-reviewer, round 1).
    "review_exclude_paths": [
        ".claude/task/review.md",
        ".claude/task/review_input.patch",
        ".claude/task/acceptance_evidence.md",
        ".claude/task/rendered_page_evidence.md",
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


def write_review(repo, hash_hex, body, rounds="rounds: 1\n"):
    (repo / ".claude" / "task" / "review.md").write_text(
        f"# Review\ndiff_sha256: {hash_hex}\n{rounds}\n{body}\n"
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


def test_commit_allowed_on_pass_with_one_thing_examined(repo):
    """A PASS may find nothing (CPO 2026-08-01). One entry under risks_checked:
    is enough — the floor dropped from 2 to 1, because requiring two on correct
    code obliged the reviewer to invent, and what it invented was findings about
    the builder's own paperwork (#370 rounds 6-12)."""
    setup_review_repo(repo)
    body = GOOD_BODY.replace("- risk two checked\n\n## analytics", "\n## analytics", 1)
    write_review(repo, staged_hash(repo), body)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert not denied(out), out


def test_commit_denied_on_pass_with_nothing_examined(repo):
    """The floor is 1, not 0. A bare PASS with nothing under risks_checked: is
    still denied — that is the rubber stamp the original two-risk rule existed
    to prevent, and it survives the 2026-08-01 relaxation."""
    setup_review_repo(repo)
    body = GOOD_BODY.replace(
        "risks_checked:\n- risk one checked\n- risk two checked\n\n## analytics",
        "risks_checked:\n\n## analytics", 1)
    write_review(repo, staged_hash(repo), body)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "state what was examined" in out


def test_bullets_before_risks_marker_do_not_satisfy_quota(repo):
    """Risks count anchors to the risks_checked: marker (CTO, round 3) —
    stray bullets above it must not pass for checked risks."""
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
    (repo / ".claude" / "task" / "notes.md").write_text("bookkeeping")
    subprocess.run(["git", "add", ".claude/task/notes.md"], cwd=repo, check=True)
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert not denied(out)


# --------------------------------------------------------------------------- #
# Acceptance gate (Quality Assurance, CPO ruling 2026-07-31, #868)
#
# Every reviewer reads the diff and asks whether the code is right; none asked
# whether the finished thing does what the ticket asked. The player Overview
# built, passed BOTH its reviewers, and still opened on the wrong season. These
# tests pin the gate that would have caught it, in both directions — it must fire
# on the user-facing surface and must NOT fire anywhere else, because a guard that
# cries wolf gets ignored (review_routing.json's own _doc).
# --------------------------------------------------------------------------- #
FRONTEND_PATH = "site_v2/src/pages/x.astro"


def _stage_frontend(repo, contract: str | None, evidence: str | None = None):
    """Stage a user-facing change, optionally with a contract and evidence file."""
    setup_review_repo(repo, stage_path=FRONTEND_PATH)
    if contract is not None:
        (repo / ".claude" / "task" / "contract.md").write_text(contract, encoding="utf-8")
    if evidence is not None:
        (repo / ".claude" / "task" / "acceptance_evidence.md").write_text(
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
    """Two declared, one shown. An undemonstrated criterion is an unverified
    claim, which is exactly how the Overview passed."""
    _stage_frontend(repo, contract=CRITERIA_CONTRACT, evidence=(
        "criteria_demonstrated:\n"
        "  - read from dist/en/players/x/index.html: opens on 2025/26 Bundesliga\n"
    ))
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "2 acceptance criteria declared, 1 demonstrated" in out


def test_acceptance_gate_rejects_placeholder_evidence(repo):
    """A `<placeholder>` and a bare `none` must not satisfy the quota — the same
    rule the contract gate applies to impact_map, reused rather than re-invented."""
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
    """The narrow trigger. A warehouse or tooling change has no page to
    demonstrate, so demanding evidence there would be the cry-wolf failure.

    The staged content must DIFFER from HEAD. The first version of this test wrote
    `select 1`, byte-identical to what `_repo_template` already committed, so
    `git diff --staged --name-only` was EMPTY, `_commit_gate` returned at its
    `if not paths` guard, and the gate under test was never reached — the test
    would have passed with `ACCEPTANCE_TRIGGER = ""`, i.e. firing on everything.
    Caught by platform-reviewer at opus, 2026-07-31, round 1."""
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
    """The contract gate owns the missing-contract case, so this one returns None
    rather than inventing a second deny for it.

    Calls `_acceptance_gate` DIRECTLY. The first version drove the whole hook and
    asserted only `not denied(out)`, which proved nothing: delete the guard and
    `open()` raises FileNotFoundError, `main()` swallows it in the fail-open
    wrapper, and the commit is still not denied — so the test passed either way and
    its own coverage claim was false. Caught by platform-reviewer at opus, round 3.
    Reaching into the hook is the same move `required_reviewers` already makes for
    the routing matcher."""
    gd = _gd()
    frontend = ["site_v2/src/pages/x.astro"]
    assert gd._acceptance_gate(str(tmp_path), frontend) is None, (
        "with no contract.md the gate must DELEGATE (return None), never deny")
    # The mirror, so the assertion above cannot be satisfied by a gate that returns
    # None unconditionally: with a contract present but no criteria, it MUST deny.
    task = tmp_path / ".claude" / "task"
    task.mkdir(parents=True)
    (task / "contract.md").write_text("objective: >\n  a page\n", encoding="utf-8")
    assert gd._acceptance_gate(str(tmp_path), frontend) is not None


def test_acceptance_gate_rejects_evidence_too_short_to_be_a_reading(repo):
    """Pins `_MIN_EVIDENCE_CHARS`. Without this, deleting the length filter or
    setting the constant to 0 broke NO test: the placeholder test never reaches the
    filter (`_bullets` drops `<...>` and `none` first) and the distinctness test
    uses lines that clear the floor. So the branch added to answer round 1 was
    itself unpinned gate behaviour — round 1's own finding class, on round 1's fix.
    Named by platform-reviewer at opus, round 2.

    `- ok` and `- fine` are non-placeholder, distinct, and four characters: proof
    of nothing."""
    _stage_frontend(repo, contract=CRITERIA_CONTRACT, evidence=(
        "criteria_demonstrated:\n  - ok\n  - fine\n"))
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "0 demonstrated" in out
    assert "too short" in out, "the deny must say WHY a line did not count"


def test_acceptance_gate_rejects_repeated_identical_evidence(repo):
    """A count alone is satisfied by two bullets both reading "checked". The quota
    is a floor, not proof, so identical and too-short lines are rejected
    (cto-reviewer round 1: "the proof is written by the builder and read by a
    bullet counter")."""
    _stage_frontend(repo, contract=CRITERIA_CONTRACT, evidence=(
        "criteria_demonstrated:\n  - checked and it works fine\n"
        "  - checked and it works fine\n"))
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    assert denied(out) and "identical" in out.lower()


# --------------------------------------------------------------------------- #
# Round cap (review-economics, 2026-07-22) — the commit gate bounds the loop.
# --------------------------------------------------------------------------- #
def test_commit_denied_without_a_rounds_line(repo):
    setup_review_repo(repo)
    # write_review injects rounds by default; pass an empty string to omit it
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
        "# Review\ndiff_sha256: " + real_hash + "\nrounds: 1\n\n" + GOOD_BODY
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


def blocked(out: str) -> bool:
    return '"decision": "block"' in out


# --------------------------------------------------------------------------- #
# Fail-open: a hook bug must never wedge a session.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("script", [
    "task_contract_gate.py", "handover_in.py",
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


# ---------------------------------------------------------------------------
# Reviewers stop reviewing the review's own paperwork (CPO 2026-08-01).
# Three changes, three invariants. #370 ran twelve rounds because the paperwork
# was inside both the reviewed patch AND the hash, and a PASS required two
# findings — so a typo fix voided every verdict and bought another round.
# ---------------------------------------------------------------------------

def test_editing_an_evidence_artifact_does_not_change_the_staged_hash(repo):
    """CHANGE 2. Correcting a note must not restart the review. The two evidence
    artifacts are in hash_exclude_paths, so a PASS survives an edit to them.
    Fails on revert: put either file back in the hash and the digests differ."""
    setup_review_repo(repo)
    before = staged_hash(repo)
    for name in ("acceptance_evidence.md", "rendered_page_evidence.md"):
        (repo / ".claude" / "task" / name).write_text("evidence, rewritten\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    assert staged_hash(repo) == before, (
        "editing an evidence artifact changed the review hash, which voids every "
        "reviewer's PASS and forces a fresh round"
    )


def test_editing_the_contract_DOES_change_the_staged_hash(repo):
    """The guard that must survive change 2 (F10/F11, #409). contract.md carries
    scope_paths and acceptance_criteria, so widening scope after the reviewers
    passed has to break the hash. If this ever goes green, the exclusion list has
    been widened too far."""
    setup_review_repo(repo)
    before = staged_hash(repo)
    (repo / ".claude" / "task" / "contract.md").write_text(
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
    """CHANGE 1. Reviewers see code and contract.md, never the notes about the
    work. Measured on #370 before this: 839 lines of code inside a 38,932-line
    reviewed diff."""
    setup_review_repo(repo)
    # Create EVERY file that should be hidden, so all the assertions below bite.
    # Three of the four used to assert nothing because the files did not exist
    # (platform-reviewer, round 3).
    hidden = ("acceptance_evidence.md", "rendered_page_evidence.md",
              "review.md", "review_input.patch")
    for i, name in enumerate(hidden):
        (repo / ".claude" / "task" / name).write_text(f"HIDDEN_MARKER_{i}\n")
    (repo / ".claude" / "active_work.md").write_text("HANDOVER_MARKER\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    patch = _review_patch(repo)
    for i, name in enumerate(hidden):
        assert f"HIDDEN_MARKER_{i}" not in patch, f"{name}'s content reached the patch"
        # Match the DIFF HEADER, not the bare filename: review_routing.json is itself
        # in the patch and lists these paths as data, so a substring check on the name
        # false-positives on correct output.
        assert f"diff --git a/.claude/task/{name}" not in patch, f"{name} is in the diff"
    assert "HANDOVER_MARKER" not in patch


def test_review_patch_DOES_deliver_the_rulings_log(repo):
    """The other authority file. `escalations.log` is the durable record of CPO
    rulings that `protected_override` cites, so a reviewer that cannot see it cannot
    check whether a claimed ruling exists — a check that has fired. It was wrongly
    excluded for one round; this pins the mechanism, not just the routing data."""
    setup_review_repo(repo)
    (repo / ".claude" / "task" / "escalations.log").write_text("LOG_MARKER\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    assert "LOG_MARKER" in _review_patch(repo), (
        "escalations.log did not reach the reviewers — they cannot verify a cited ruling"
    )


def test_review_patch_is_cumulative_not_just_the_last_increment(repo):
    """Every brief promises "the cumulative branch diff vs main", because two
    individually clean commits can cumulatively drift. `git diff --staged` alone is
    index-vs-HEAD, so on a branch that already has a commit the reviewers would get
    only the newest slice. Fails on revert to a bare `--staged` (cto-reviewer)."""
    setup_review_repo(repo)
    subprocess.run(["git", "branch", "-f", "main", "HEAD"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", "feat/two-commits"], cwd=repo, check=True)
    # The two changes MUST be in different files. Putting both markers on one line
    # makes the test vacuous: a staged-only diff shows the whole changed line, so the
    # earlier marker appears in it as well and the assertion passes on the bug.
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
    """The other direction, so change 1 cannot be satisfied by excluding
    everything: the reviewers must still receive the code diff, and contract.md
    because that is what scope-auditor and cto-reviewer check authority against."""
    setup_review_repo(repo)
    (repo / "dbt_project" / "models" / "allowed.sql").write_text("select 1 as CODE_MARKER\n")
    (repo / ".claude" / "task" / "contract.md").write_text("objective: CONTRACT_MARKER\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    patch = _review_patch(repo)
    assert "CODE_MARKER" in patch
    assert "CONTRACT_MARKER" in patch, (
        "contract.md must reach the reviewers — it carries the scope and the "
        "authority they are asked to check"
    )


def test_every_task_artifact_is_classified(repo):
    """Stops `review_exclude_paths` from decaying as artifacts are added.

    Every tracked file in `.claude/task/` must be either excluded from what the
    reviewers read, or contract.md, which they MUST read. A new artifact that is
    neither fails here, so it gets classified deliberately instead of silently
    becoming reviewable surface — which is how #370's paperwork ended up inside
    its own review.

    This reads the REAL routing file, not the fixture: the fixture cannot catch a
    file that exists only in the repo."""
    excluded = set(real_routing().get("review_exclude_paths") or [])
    files = tracked(".claude/task/")
    assert files, "no tracked files under .claude/task/ — has the tree moved?"
    # The two files there that carry AUTHORITY and must reach the reviewers.
    authority = {".claude/task/contract.md", ".claude/task/escalations.log"}
    unclassified = [p for p in files if p not in excluded and p not in authority]
    assert not unclassified, (
        "these .claude/task/ files are neither hidden from reviewers nor one of the "
        f"two authority files, so reviewers will review their own paperwork: {unclassified}"
    )
    # And the other direction: an authority file must never be hidden. cto-reviewer
    # caught escalations.log excluded here — protected_override cites it as the
    # locatable record, so a reviewer that cannot see it cannot check whether a
    # claimed CPO ruling exists.
    hidden_authority = sorted(authority & excluded)
    assert not hidden_authority, (
        f"authority files hidden from reviewers: {hidden_authority}"
    )


def test_real_routing_hides_the_evidence_artifacts_from_the_hash(repo):
    """Pins the REAL routing data for change 2, not the synthetic fixture.

    `platform-reviewer` caught that every test of the hash exclusion used the
    fixture, so deleting the two evidence artifacts from the real
    `hash_exclude_paths` left the whole suite green — the change was demonstrated
    once by hand and then unprotected. The same gap shipped a routing change that
    missed six tracked files, which is why `real_routing()` exists at all."""
    excl = set(real_routing().get("hash_exclude_paths") or [])
    for p in (".claude/task/acceptance_evidence.md",
              ".claude/task/rendered_page_evidence.md"):
        assert p in excl, (
            f"{p} is back inside diff_sha256 — editing it now voids every "
            "reviewer's PASS and buys a fresh round"
        )
    assert ".claude/task/contract.md" not in excl, (
        "contract.md left the review hash — scope and acceptance_criteria could be "
        "widened after every reviewer passed (F10/F11, #409)"
    )


def _ci_repo_with_review(ci_repo, body: str):
    """Commit code + contract, then a review.md carrying the recomputed PR hash and
    `body`. Mirrors test_ci_check_passes_with_complete_artifacts."""
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    (ci_repo / ".claude" / "task" / "contract.md").write_text(CONTRACT)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code+contract"], cwd=ci_repo, check=True)
    (ci_repo / ".claude" / "task" / "review.md").write_text(
        "# Review\ndiff_sha256: " + branch_hash(ci_repo) + "\nrounds: 1\n\n" + body
    )
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "review"], cwd=ci_repo, check=True)
    return run_ci_check(ci_repo)


def test_ci_twin_accepts_a_pass_with_one_thing_examined(ci_repo):
    """The CI twin's floor must equal the local hook's, and nothing pinned it.

    The floor lives in TWO places — `git_discipline._commit_gate` and
    `check_task_artifacts.py` — and for one review round they disagreed: the hook
    allowed one entry while fail-closed CI still demanded two, so a reviewer taking
    the CPO's 2026-08-01 permission committed locally and then reddened the PR. Every
    existing CI-path test used a two-entry body, so all 248 stayed green through that
    divergence. Fails on revert of the CI floor to 2."""
    body = GOOD_BODY.replace("- risk two checked\n", "", 1)
    code, out = _ci_repo_with_review(ci_repo, body)
    assert code == 0, out


def test_ci_twin_denies_a_pass_with_nothing_examined(ci_repo):
    """The other direction, so the floor cannot be satisfied by deleting it: zero
    entries is still a rubber stamp and still fails CI. Pins the message text too,
    so the two copies cannot drift in what they tell the builder."""
    body = GOOD_BODY.replace("- risk one checked\n- risk two checked\n", "", 1)
    code, out = _ci_repo_with_review(ci_repo, body)
    assert code == 1, out
    assert "state what was examined" in out


def test_review_patch_fails_LOUD_when_git_fails(tmp_path):
    """The most dangerous behaviour of the new path, and nothing pinned it.

    `--review-patch`'s documented usage redirects stdout into review_input.patch, and
    a redirect truncates its target BEFORE the process runs. So a git failure that
    returned empty bytes and exit 0 would leave a zero-byte patch that reads to a
    reviewer as "nothing changed" — and nothing downstream can detect it, because
    review_input.patch is in both exclusion lists. Reverting the `raise` leaves the
    rest of the suite green (platform-reviewer, round 3).

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
    """`main` exists but has no common ancestor with HEAD. The old code fell back to
    a bare `--staged` here, silently handing reviewers the last increment only. It
    must refuse instead — loud or large, never narrower."""
    dst = tmp_path / "unrelated"
    shutil.copytree(_repo_template, dst)
    setup_review_repo(dst)
    subprocess.run(["git", "commit", "-qm", "one"], cwd=dst, check=True)
    start = subprocess.run(["git", "branch", "--show-current"], cwd=dst,
                           capture_output=True, text=True, check=True).stdout.strip()
    # An orphan branch named main: no shared history with the current HEAD.
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
