import io
import json
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HOOKS = os.path.join(ROOT, ".claude", "hooks")
sys.path.insert(0, HOOKS)

import git_discipline as gd  # noqa: E402
import task_contract_gate as gate  # noqa: E402

SHA = "a" * 40
OTHER = "b" * 40
GOOD_MR = {"state": "opened", "target_branch": "main", "source_branch": "research-fix/2026-11-20",
           "head_pipeline": {"status": "success", "source": "merge_request_event"}, "sha": SHA}
MERGE = f"glab mr merge 7 --sha {SHA}"
ROUTING = json.load(open(os.path.join(ROOT, ".claude", "review_routing.json"), encoding="utf-8"))
def z(*paths):
    return "".join(f"{p}\0" for p in paths)


SAFE_DIFF = z("dbt_project/seeds/fixture_card_corrections.csv", ".claude/task/262-x/contract.md")


class Fake:
    """Stands in for subprocess.run: one reply per command kind, and a record of what ran."""

    def __init__(self, mr=None, routing=None, diff=SAFE_DIFF, diff_rc=0, **codes):
        self.mr = mr if mr is not None else GOOD_MR
        self.codes = {"glab": 0, "fetch": 0, "show": 0, "diff": diff_rc, "worktree": 0, "cleanup": 0,
                      "ready": 0, **codes}
        self.diff = diff
        self.routing = json.dumps(ROUTING) if routing is None else routing
        self.ran, self.cmds, self.timeouts = [], [], []

    def __call__(self, cmd, **kwargs):
        out = ""
        if cmd[0] == "glab":
            kind, out = "glab", json.dumps(self.mr)
        elif cmd[0] == "git":
            kind = {"fetch": "fetch", "show": "show", "diff": "diff"}.get(cmd[1])
            if cmd[1] == "worktree":
                kind = "worktree" if cmd[2] == "add" else "cleanup"
            out = {"show": self.routing, "diff": self.diff}.get(kind, "")
        else:
            kind, out = "ready", "NOT READY"
        self.ran.append(kind)
        self.cmds.append(cmd)
        self.timeouts.append(kwargs.get("timeout"))
        return subprocess.CompletedProcess(cmd, self.codes[kind], stdout=out, stderr="")


def denial(monkeypatch, sha=SHA, **kw):
    fake = Fake(**kw)
    monkeypatch.setattr(subprocess, "run", fake)
    return gd._agent_merge_denial("7", sha, "."), fake


def test_all_conditions_met_allows(monkeypatch):
    why, fake = denial(monkeypatch)
    assert why is None
    assert fake.ran == ["glab", "fetch", "show", "diff", "worktree", "ready", "cleanup"]


def test_the_list_and_the_judge_come_from_the_target_branch_not_the_mr(monkeypatch):
    _, fake = denial(monkeypatch)
    assert fake.cmds[fake.ran.index("show")][-1] == "gitlab/main:.claude/review_routing.json"
    diff = fake.cmds[fake.ran.index("diff")]
    assert diff[-1] == f"gitlab/main...{SHA}" and "-z" in diff
    add = fake.cmds[fake.ran.index("worktree")]
    assert add[-1] == "gitlab/main"
    ready = fake.cmds[fake.ran.index("ready")]
    assert ready[1] == os.path.join(add[-2], "scripts", "merge_ready.py") and ready[2] == "7"


@pytest.mark.parametrize("path", [
    "site_v2/src/pages/index.astro", "site_v2/src/i18n/strings.ts", "dbt_project/seeds/metric_catalogue.csv",
    "docs/working_agreement.md", ".claude/hooks/git_discipline.py", ".claude/settings.json",
    ".claude/review_routing.json", ".gitlab-ci.yml", "scripts/check_layer_contract.py",
    "scripts/merge_ready.py", "docs/competition_registry.yml", "deploy/nightly/entrypoint.sh",
    "dbt_project/seeds/team_name_overrides.csv", "dbt_project/seeds/round_names.csv",
    "dbt_project/seeds/competition_registry.csv", "docs/wireframes/metrics_display.md",
    ".claude/skills/research-provider-errors/SKILL.md", ".gitleaksignore", "brand_new_file.txt",
    "tests/test_governance_hooks.py", "tests/fixtures/design_inventory/baseline.json",
    "dbt_project/macros/generate_schema_name.sql", "dbt_project/tests/assert_x.sql",
    "dbt_project/models/5_marts/shared.yml", "dbt_project/seeds/confederations.csv",
    ".claude/task/REVIEW_TEMPLATE.md", ".claude/task/TEMPLATE.md",
])
def test_an_mr_touching_an_unlisted_or_excluded_path_waits_for_the_cpo(monkeypatch, path):
    why, fake = denial(monkeypatch, diff=SAFE_DIFF + z(path))
    assert path in why and "worktree" not in fake.ran


def test_a_non_ascii_path_is_read_as_it_is_and_is_not_listed(monkeypatch):
    path = "site_v2/src/content/münchen – spielplan.md"
    why, fake = denial(monkeypatch, diff=z(path))
    assert path in why and "worktree" not in fake.ran


def test_a_non_ascii_path_under_a_listed_directory_is_cleared(monkeypatch):
    why, _ = denial(monkeypatch, diff=z(".claude/task/262-x/münchen.md"))
    assert why is None


def test_a_model_is_not_a_listed_path(monkeypatch):
    why, fake = denial(monkeypatch, diff=SAFE_DIFF + z("dbt_project/models/5_marts/mart_x.sql"))
    assert "mart_x.sql" in why and "worktree" not in fake.ran


def test_correction_seeds_are_merged_only_from_a_research_fix_branch(monkeypatch):
    why, _ = denial(monkeypatch)
    assert why is None
    for branch in ("claude/anything", "xresearch-fix/1"):
        why, fake = denial(monkeypatch, mr={**GOOD_MR, "source_branch": branch})
        assert "correction seeds" in why and "worktree" not in fake.ran
    why, _ = denial(monkeypatch, diff=z(".claude/task/262-x/contract.md"),
                    mr={**GOOD_MR, "source_branch": "claude/anything"})
    assert why is None


def test_an_excluded_path_is_outside_the_allowlist_even_when_it_is_listed():
    assert gd._outside_allowlist(["a/x.csv", "a/y.csv"], ["a/*"], ["a/y.csv"]) == ["a/y.csv"]
    assert gd._outside_allowlist(["a/x.csv"], ["a/*"], []) == []


def test_a_path_on_the_except_list_of_main_waits_for_the_cpo(monkeypatch):
    routing = json.dumps({**ROUTING, "agent_merge_except": ["dbt_project/seeds/fixture_card_corrections.csv"]})
    why, fake = denial(monkeypatch, routing=routing)
    assert "fixture_card_corrections.csv" in why and "worktree" not in fake.ran


def test_the_diff_is_read_so_that_a_rename_shows_both_paths(tmp_path, monkeypatch):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, capture_output=True, text=True, check=True).stdout

    git("init", "-q", "-b", "main")
    git("config", "user.email", "t@t")
    git("config", "user.name", "t")
    (tmp_path / ".claude" / "hooks").mkdir(parents=True)
    guard = tmp_path / ".claude" / "hooks" / "guard.py"
    guard.write_text("x = 1\n" * 20)
    git("add", "-A")
    git("commit", "-qm", "base")
    git("checkout", "-qb", "mr")
    target = tmp_path / "dbt_project" / "seeds" / "fixture_card_corrections.csv"
    target.parent.mkdir(parents=True)
    guard.rename(target)
    git("add", "-A")
    git("commit", "-qm", "rename")
    _, fake = denial(monkeypatch, diff="")
    monkeypatch.undo()
    flags = fake.cmds[fake.ran.index("diff")][:-1]
    paths = [p for p in git("-c", "diff.renames=true", *flags[1:], "main...mr").split("\0") if p]
    assert ".claude/hooks/guard.py" in paths and "dbt_project/seeds/fixture_card_corrections.csv" in paths
    assert gd._outside_allowlist(paths, ROUTING["agent_merge_paths"], ROUTING["agent_merge_except"]) == [
        ".claude/hooks/guard.py"]


@pytest.mark.parametrize("routing", [
    "", "not json", "{}", json.dumps({"agent_merge_paths": ["tests/**"]}),
    json.dumps({"agent_merge_except": []}), json.dumps({"agent_merge_paths": [], "agent_merge_except": []}),
    json.dumps({"agent_merge_paths": "x", "agent_merge_except": []}),
    json.dumps({"agent_merge_paths": [""], "agent_merge_except": []}),
    json.dumps({"agent_merge_paths": [1], "agent_merge_except": []}),
    json.dumps({"agent_merge_paths": ["tests/**"], "agent_merge_except": [None]}),
])
def test_no_usable_list_on_main_denies(monkeypatch, routing):
    why, fake = denial(monkeypatch, routing=routing)
    assert why and "ready" not in fake.ran


def test_a_list_on_main_that_cannot_be_read_denies(monkeypatch):
    why, fake = denial(monkeypatch, show=128)
    assert "could not be read" in why and "diff" not in fake.ran


def test_an_empty_diff_denies(monkeypatch):
    why, _ = denial(monkeypatch, diff="")
    assert "changes nothing" in why


def test_a_diff_that_cannot_be_read_denies(monkeypatch):
    why, fake = denial(monkeypatch, diff_rc=1)
    assert "could not be read" in why and "ready" not in fake.ran


@pytest.mark.parametrize("change", [
    {"state": "merged"},
    {"target_branch": "release"},
    {"head_pipeline": {"status": "running"}},
    {"head_pipeline": None},
    {"head_pipeline": {"status": "success", "source": "web"}},
    {"head_pipeline": {"status": "success"}},
    {"sha": ""},
    {"sha": OTHER},
])
def test_each_mr_fact_that_fails_denies(monkeypatch, change):
    why, fake = denial(monkeypatch, mr={**GOOD_MR, **change})
    assert why
    assert "show" not in fake.ran and "ready" not in fake.ran


def test_sha_that_is_not_the_head_denies(monkeypatch):
    why, fake = denial(monkeypatch, sha=OTHER)
    assert "--sha is not the head" in why and "show" not in fake.ran


def test_a_main_checkout_that_fails_denies_and_runs_nothing_from_the_tree(monkeypatch):
    why, fake = denial(monkeypatch, worktree=128)
    assert "could not be checked out" in why and "ready" not in fake.ran and "cleanup" in fake.ran


def test_not_ready_denies_and_removes_the_main_checkout(monkeypatch):
    why, fake = denial(monkeypatch, ready=1)
    assert "not ready to merge" in why and fake.ran[-1] == "cleanup"
    remove = fake.cmds[-1]
    assert remove[:4] == ["git", "worktree", "remove", "--force"]


def test_unreadable_mr_denies(monkeypatch):
    why, _ = denial(monkeypatch, glab=1)
    assert "could not be read" in why


def test_failed_fetch_denies(monkeypatch):
    why, _ = denial(monkeypatch, fetch=1)
    assert "could not be fetched" in why


def test_an_exception_denies(monkeypatch):
    def boom(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, 1)

    monkeypatch.setattr(subprocess, "run", boom)
    assert "could not be checked" in gd._agent_merge_denial("7", SHA, ".")


def test_the_steps_share_one_deadline_below_the_harness_timeout(monkeypatch):
    import time

    assert gd.MERGE_DEADLINE_SECONDS < 600
    clock = iter([0.0] + [gd.MERGE_DEADLINE_SECONDS - 5.0] * 50)
    monkeypatch.setattr(time, "monotonic", lambda: next(clock))
    why, fake = denial(monkeypatch)
    assert why is None
    steps = [t for kind, t in zip(fake.ran, fake.timeouts) if kind != "cleanup"]
    assert max(steps) <= 5.0 + 1e-9


def test_an_exhausted_deadline_denies(monkeypatch):
    import time

    clock = iter([0.0] + [gd.MERGE_DEADLINE_SECONDS + 1.0] * 50)
    monkeypatch.setattr(time, "monotonic", lambda: next(clock))
    why, fake = denial(monkeypatch)
    assert "could not be checked" in why and fake.ran == []


@pytest.mark.parametrize("cmd", [
    f"glab mr merge 7 --sha {SHA}",
    f"glab mr merge 7 --sha={SHA} --yes",
    f"glab mr accept 7 --yes --sha {SHA}",
    f"glab mr merge 12 --sha {SHA} -d -y",
    f"  glab mr merge 7 --sha {SHA}  ",
])
def test_allowed_forms(cmd):
    iid, sha = gd._agent_merge_form(cmd)
    assert iid in ("7", "12") and sha == SHA


@pytest.mark.parametrize("cmd", [
    "glab mr merge",
    "glab mr merge 7",
    "glab mr merge 7 --yes",
    f"glab mr merge 7 --sha {SHA} --auto-merge",
    f"glab mr merge 7 --sha {SHA} --squash",
    f"glab mr merge 7 --sha {SHA} -s",
    f"glab mr merge 7 --sha {SHA} --when-pipeline-succeeds",
    f"glab mr merge 7 --sha {SHA} --sha {OTHER}",
    "glab mr merge 7 --sha abc",
    f"glab mr merge 7 --sha {SHA.upper()}",
    f"glab mr merge $(echo 7) --sha {SHA}",
    f"glab mr merge feature-branch --sha {SHA}",
    f"glab mr merge 7 --sha {SHA} -R other/repo",
    f"glab mr merge 7 --sha {SHA} > out.txt",
    f"glab mr merge 7 --sha {SHA} &",
    f"glab -R other/repo mr merge 7 --sha {SHA}",
    f"FOO=1 glab mr merge 7 --sha {SHA}",
    f"GIT_DIR=../other/.git glab mr merge 7 --sha {SHA}",
    f"env glab mr merge 7 --sha {SHA}",
    f"sudo glab mr merge 7 --sha {SHA}",
    f"command glab mr merge 7 --sha {SHA}",
    f"glab mr merge '7 --sha {SHA}",
])
def test_other_forms_are_not_the_merge_form(cmd):
    assert gd._agent_merge_form(cmd) is None


def run_main(monkeypatch, capsys, command):
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(
        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}})))
    monkeypatch.setattr(sys, "argv", ["git_discipline.py"])
    assert gd.main() == 0
    return capsys.readouterr().out


def denied(out):
    return '"permissionDecision": "deny"' in out


def test_main_allows_a_passing_merge(monkeypatch, capsys):
    monkeypatch.setattr(subprocess, "run", Fake())
    assert not denied(run_main(monkeypatch, capsys, MERGE + " --yes"))


def test_main_denies_a_failing_merge_and_says_why(monkeypatch, capsys):
    monkeypatch.setattr(subprocess, "run", Fake(ready=1))
    out = run_main(monkeypatch, capsys, MERGE + " --yes")
    assert denied(out) and "not ready to merge" in out


def test_main_denies_an_mr_that_touches_an_unlisted_path(monkeypatch, capsys):
    monkeypatch.setattr(subprocess, "run", Fake(diff=z("site_v2/src/pages/index.astro")))
    out = run_main(monkeypatch, capsys, MERGE)
    assert denied(out) and "CPO merges it" in out


@pytest.mark.parametrize("command", [
    f"glab mr merge 7 --sha {SHA} --auto-merge",
    "glab mr merge",
    "glab mr merge 7 --yes",
    f"{MERGE} && echo done",
    f"echo hi; {MERGE}",
    f"FOO=1 {MERGE}",
    f"glab mr accept 7 --sha {SHA} --when-pipeline-succeeds",
])
def test_main_blocks_every_other_merge_without_asking_gitlab(monkeypatch, capsys, command):
    def no_calls(cmd, **kwargs):
        raise AssertionError(f"ran {cmd}")

    monkeypatch.setattr(subprocess, "run", no_calls)
    assert denied(run_main(monkeypatch, capsys, command))


def test_blocked_merge_over_the_real_hook_process():
    event = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
             "tool_input": {"command": "glab mr merge 7 --auto-merge"}}
    r = subprocess.run([sys.executable, os.path.join(HOOKS, "git_discipline.py")], input=json.dumps(event),
                       capture_output=True, text=True, cwd=ROOT, timeout=60)
    assert denied(r.stdout) and "MERGE BLOCKED" in r.stdout


ALLOWED, EXCEPT = ROUTING["agent_merge_paths"], ROUTING["agent_merge_except"]


def agent_may_merge(path):
    return not gd._outside_allowlist([path], ALLOWED, EXCEPT)


def _as_sample(entry):
    return entry + "x/y.py" if entry.endswith("/") else entry


def test_no_guard_path_of_the_contract_gate_is_agent_mergeable():
    for entry in (*gate.PROTECTED_PREFIXES, *gate.PROTECTED_FILES):
        assert not agent_may_merge(_as_sample(entry)), f"{entry} is a guard path and the agent may merge it"


def test_no_core_document_is_agent_mergeable():
    text = open(os.path.join(ROOT, "docs", "working_agreement.md"), encoding="utf-8").read()
    row = next(ln for ln in text.splitlines() if ln.startswith("| Core document text"))
    docs = re.findall(r"`([a-z_]+\.md)`", row)
    assert len(docs) >= 8
    for name in docs:
        assert not agent_may_merge(f"docs/{name}"), f"docs/{name} is a core document"


@pytest.mark.parametrize("path", [
    "site_v2/src/pages/en/index.astro", "site_v2/src/i18n/strings.ts", "site_v2/package.json",
    "dbt_project/seeds/metric_catalogue.csv", "dbt_project/seeds/competition_registry.csv",
    "dbt_project/seeds/team_name_overrides.csv", "dbt_project/seeds/league_name_overrides.csv",
    "dbt_project/seeds/country_name_overrides.csv", "dbt_project/seeds/round_names.csv",
    "docs/competition_registry.yml", "docs/data_contract.md", "docs/wireframes/metrics_display.md",
    "deploy/nightly/README.md", "ingestion/api_football/settings.py", "ingestion/api_football/main.py",
    "scripts/check_registry_var_sync.py", "scripts/merge_ready.py", "scripts/ci_local.py",
    "scripts/design_inventory.py", "scripts/security/check_no_secrets.py", "scripts/export_site_data.py",
    ".claude/settings.json", ".claude/settings.local.json", ".claude/hooks/x.py", ".claude/agents/x.md",
    ".claude/skills/other-skill/SKILL.md", ".claude/review_routing.json", ".claude/active_work.md",
    ".gitlab-ci.yml", ".gitleaks.toml", ".gitleaksignore", ".pre-commit-config.yaml", ".ruff-ci.toml",
    ".github/workflows/x.yml", ".mcp.json", "CLAUDE.md", "requirements.txt", "a_new_top_level_file.txt",
    "tests/fixtures/design_inventory/baseline.json", "tests/conftest.py", "tests/test_check_layer_contract.py",
    "tests/test_check_chart_components.py", "tests/test_x.py", "dbt_project/tests/assert_x.sql",
    "dbt_project/macros/generate_schema_name.sql", "dbt_project/macros/x.sql", "dbt_project/models/x/y.yml",
    "dbt_project/models/5_marts/mart_x.sql", "dbt_project/models/2_base/api_football/base_x.sql",
    "dbt_project/seeds/confederations.csv", "dbt_project/seeds/competition_types.csv",
    "dbt_project/seeds/standings_corrections.csv", "dbt_project/seeds/fixture_card_answer_key.csv",
    ".claude/task/TEMPLATE.md", ".claude/task/REVIEW_TEMPLATE.md", ".claude/task/escalations.log",
])
def test_the_agent_may_not_merge_these(path):
    assert not agent_may_merge(path)


@pytest.mark.parametrize("path", [
    "dbt_project/seeds/fixture_card_corrections.csv", "dbt_project/seeds/fixture_goal_corrections.csv",
    "dbt_project/seeds/fixture_result_corrections.csv", ".claude/task/1-x/contract.md",
    ".claude/task/1-x/review.md",
])
def test_the_agent_may_merge_these(path):
    assert agent_may_merge(path)


def test_the_allowlist_holds_no_tests_and_no_wildcard_seed_or_directory():
    for pattern in ALLOWED:
        assert not pattern.startswith("tests/") and "dbt_project/tests" not in pattern
        assert pattern not in ("dbt_project/seeds/**", "dbt_project/models/**", "dbt_project/macros/**")
        assert not pattern.endswith("/**"), f"{pattern} lists a whole directory"


def test_the_files_merge_ready_imports_are_not_agent_mergeable():
    src = open(os.path.join(ROOT, "scripts", "merge_ready.py"), encoding="utf-8").read()
    for module in re.findall(r"^\s*import (ci_local|check_design_inventory|design_inventory|task_contract_gate)\b",
                             src, re.M):
        rel = {"ci_local": "scripts/ci_local.py", "check_design_inventory": "scripts/check_design_inventory.py",
               "design_inventory": "scripts/design_inventory.py",
               "task_contract_gate": ".claude/hooks/task_contract_gate.py"}[module]
        assert not agent_may_merge(rel), rel


def _ci():
    import yaml

    return yaml.safe_load(open(os.path.join(ROOT, ".gitlab-ci.yml"), encoding="utf-8"))


def test_ci_runs_the_research_check_from_the_target_branch_copy():
    steps = _ci()["validate:governance"]["script"]
    line = next(s for s in steps if "check_research_fix_mr" in s)
    assert "research-fix/*" in line
    assert 'git show "origin/${CI_MERGE_REQUEST_TARGET_BRANCH_NAME:-main}:scripts/check_research_fix_mr.py"' in line
    assert "main.py || exit 1; python /tmp/check_research_fix_mr_main.py" in line
    assert "python scripts/check_research_fix_mr.py" not in line


def test_the_data_jobs_carry_no_research_fix_rule():
    ci = _ci()
    assert "data:build:research-fix" not in ci
    for name in ("data:build:mr", "data:wait-prod-build", "data:build:main"):
        assert not [r for r in ci[name]["rules"] if "research-fix" in json.dumps(r)], name


WATCHDOG_CHILD = """
import io, json, subprocess, sys, time
sys.path.insert(0, {hooks!r})
import git_discipline as gd
gd.MERGE_DEADLINE_SECONDS = 1
gd._WATCHDOG_GRACE_SECONDS = 1
subprocess.run = lambda *a, **k: time.sleep(60)
sys.stdin = io.StringIO(json.dumps({{"hook_event_name": "PreToolUse", "tool_name": "Bash",
    "tool_input": {{"command": {command!r}}}}}))
sys.argv = ["git_discipline.py"]
sys.exit(gd.main())
"""


def test_a_step_that_never_returns_is_denied_inside_the_deadline():
    import time

    code = WATCHDOG_CHILD.format(hooks=HOOKS, command=MERGE)
    started = time.monotonic()
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30)
    assert time.monotonic() - started < 20
    assert denied(r.stdout) and "deadline" in r.stdout


def test_the_harness_timeout_of_the_merge_hook_is_above_its_deadline_and_watchdog():
    settings = json.load(open(os.path.join(ROOT, ".claude", "settings.json"), encoding="utf-8"))
    entries = [h for m in settings["hooks"]["PreToolUse"] for h in m["hooks"] if "git_discipline.py" in h["command"]]
    assert len(entries) == 1
    assert entries[0].get("timeout", 0) > gd.MERGE_DEADLINE_SECONDS + gd._WATCHDOG_GRACE_SECONDS
