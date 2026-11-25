"""Review tiers: text needs no reviewer, a territory path its owner, a risk path the owner and one specialist."""
# ruff: noqa: F811  (the imported fixtures are requested by name as test parameters)

from __future__ import annotations

import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from test_governance_hooks import (  # noqa: F401  (fixtures are used by name)
    COMMIT_CMD,
    CONTRACT,
    ROUTING,
    SCRIPTS,
    TASK_ID,
    _gd,
    _repo_template,
    bash_event,
    branch_hash,
    ci_repo,
    denied,
    real_routing,
    repo,
    run_ci_check,
    run_hook,
    staged_hash,
    tracked,
    write_review,
)

AE, BI, CTO = "analytics-engineer-reviewer", "bi-analyst-reviewer", "cto-reviewer"
DE, FA, PL = "data-engineer-reviewer", "football-analytics-expert-reviewer", "platform-reviewer"

# One or more tracked files per row of the contract's tier map, with the reviewers each must get.
TIER_MAP = {
    # risk: the protected paths
    ".claude/hooks/git_discipline.py": {PL, CTO},
    ".claude/agents/scope-auditor.md": {PL, CTO},
    ".claude/commands/status.md": {PL, CTO},
    ".claude/settings.json": {PL, CTO},
    ".claude/review_routing.json": {PL, CTO},
    ".mcp.json": {PL, CTO},
    ".cursor/mcp.json": {PL, CTO},
    ".github/workflows/README.md": {PL, CTO},
    ".gitlab-ci.yml": {PL, CTO},
    "scripts/check_design_inventory.py": {PL, CTO},
    "scripts/check_page_css.py": {PL, CTO},
    "scripts/design_inventory.py": {PL, CTO},
    "tests/test_design_inventory.py": {PL, CTO},
    "docs/design/components.yml": {BI, CTO},
    # risk: dependencies
    "requirements.txt": {PL, CTO},
    "requirements-dev.txt": {PL, CTO},
    "ingestion/api_football/requirements.txt": {PL, CTO},
    "site_v2/package.json": {PL, CTO},
    "site_v2/package-lock.json": {PL, CTO},
    # risk: gates; `*` crosses `/`, so the nested secrets check needs its own row
    "scripts/check_layer_contract.py": {PL, CTO},
    "scripts/check_task_artifacts.py": {PL, CTO},
    "scripts/security/check_no_secrets.py": {PL, CTO},
    "scripts/merge_ready.py": {PL, CTO},
    "site_v2/scripts/check-built-pages.mjs": {PL, CTO},
    "site_v2/scripts/check-built-pages.test.mjs": {PL, CTO},
    ".claude/skills/research-provider-errors/SKILL.md": {AE, CTO},
    # risk: gate inputs found by test_every_file_a_gate_names_is_a_risk_path
    "scripts/sync_metric_docs_blocks.py": {PL, CTO},
    "scripts/sync_dbt_vars.py": {PL, CTO},
    "scripts/get_new_league_codes.py": {PL, CTO},
    "scripts/wait_for_nightly.py": {PL, CTO},
    "scripts/stale_prod_nodes.py": {PL, CTO},
    ".ruff-ci.toml": {PL, CTO},
    ".python-version": {PL, CTO},
    ".nvmrc": {PL, CTO},
    "dbt_project/.sqlfluff": {AE, CTO},
    "dbt_project/packages.yml": {AE, CTO},
    "dbt_project/package-lock.yml": {AE, CTO},
    # risk: CI and deploy
    "scripts/ci_local.py": {PL, CTO},
    "deploy/nightly/entrypoint.sh": {PL, CTO},
    "deploy/site/Dockerfile": {PL, CTO},
    "Dockerfile": {PL, CTO},
    ".dockerignore": {PL, CTO},
    ".gcloudignore": {PL, CTO},
    ".gitleaks.toml": {PL, CTO},
    ".pre-commit-config.yaml": {PL, CTO},
    ".githooks/post-commit": {PL, CTO},
    ".gitleaksignore": {PL, CTO},
    # risk: design gate inputs
    "docs/wireframes/block_standard.md": {BI, CTO},
    "docs/wireframes/approved_designs.yml": {BI, CTO},
    "design-mocks/check_handover.py": {BI, CTO},
    "design-mocks/check_mock_css.py": {BI, CTO},
    # risk: prod writes
    "scripts/drop_legacy_raw_tables.py": {PL, CTO},
    "scripts/diagnostics/drop_orphaned_coverage_table.py": {PL, CTO},
    "scripts/diagnostics/restore_from_time_travel.py": {PL, CTO},
    "scripts/cleanup_orphan_relations.py": {PL, CTO},
    "scripts/clear_apif_ingest_lock.py": {PL, CTO},
    "scripts/refetch_from_provider.py": {PL, CTO},
    "scripts/compare_fixture_statistics_live.py": {PL, CTO},
    "scripts/nightly_site_deploy.py": {PL, CTO},
    "scripts/sync_crests.py": {PL, CTO},
    "scripts/export_site_data.py": {AE, PL},
    "scripts/export_pages_data.py": {AE, PL},
    # risk: ingestion, cost, metric definitions
    "ingestion/__init__.py": {DE, CTO},
    "ingestion/api_football/main.py": {DE, CTO},
    "ingestion/api_football/loads/fixtures.py": {DE, CTO},
    "docs/competition_registry.yml": {DE, AE},
    "dbt_project/seeds/competition_registry.csv": {DE, AE},
    "dbt_project/seeds/metric_catalogue.csv": {AE, FA},
    # territory
    "site_v2/src/lib/metricRows.ts": {BI},
    "design-mocks/gen_home.py": {BI},
    "design-mocks/render.py": {BI},
    "dbt_project/models/5_marts/shared/mart_team_profile.sql": {AE},
    "dbt_project/seeds/fixture_goal_corrections.csv": {AE},
    "dbt_project/dbt_project.yml": {AE},
    "scripts/export_matchday_insights.ps1": {PL},
    "tests/test_governance_hooks.py": {PL},
    "tests/fixtures/apif/fixture_details_sample.json": {PL},
    "site_v2/astro.config.mjs": {PL},
    "site_v2/.gitignore": {PL},
    "site_v2/scripts/audit-seo.mjs": {PL},
    ".sqlfluff": {PL},
    ".gitattributes": {PL},
    ".gitignore": {PL},
    # text
    "docs/working_agreement.md": set(),
    "docs/data_contract.md": set(),
    "docs/wireframes/00_overview.md": set(),
    "docs/portable_guardrails/hooks/handover_in.py": set(),
    "site/i18n/de.json": set(),
    "design-mocks/README.md": set(),
    ".claude/skills/validate-local/SKILL.md": set(),
    ".claude/task/TEMPLATE.md": set(),
    ".claude/launch.json": set(),
    ".cursor/rules/dbt.mdc": set(),
    ".github/pull_request_template.md": set(),
    ".gitlab/issue_templates/Task.md": set(),
    ".vscode/settings.json": set(),
    ".env.example": set(),
    "README.md": set(),
    "CLAUDE.md": set(),
}

# A protected path with no tracked file today; routing must still cover it.
UNTRACKED = {".cursor/mcp.json", ".gitleaksignore"}


def _all_tracked() -> list[str]:
    return tracked(".")


def _reviewers(path: str, routing: dict) -> set:
    return _gd()._path_reviewers(path, routing)


def test_real_routing_declares_the_tiers():
    r = real_routing()
    assert r["always"] == [], "no reviewer runs on every MR: a text-only MR needs none"
    assert r["max_reviewers"] == 2
    assert r["tiers"]["risk"]["reviewers"] == 2
    assert r["tiers"]["territory"]["reviewers"] == 1


def test_every_tracked_file_matches_its_tier():
    r, files = real_routing(), _all_tracked()
    assert len(files) > 2000, f"only {len(files)} tracked files: the listing was cut short"
    wrong = {f: msg for f in files if (msg := _gd()._tier_gate([f], r))}
    assert not wrong, f"{len(wrong)} files whose reviewer count is not their tier's: {wrong}"


def test_no_tracked_file_needs_three_reviewers():
    r = real_routing()
    over = {f: sorted(_reviewers(f, r)) for f in _all_tracked() if len(_reviewers(f, r)) > 2}
    assert not over, f"files routed to more than two reviewers: {over}"


def test_the_risk_pairs_are_the_tier_map():
    r, files = real_routing(), set(_all_tracked())
    imagined = sorted(p for p in TIER_MAP if p not in files and p not in UNTRACKED)
    assert not imagined, f"tier map samples that are not tracked files: {imagined}"
    wrong = {p: (sorted(want), sorted(_reviewers(p, r)))
             for p, want in TIER_MAP.items() if _reviewers(p, r) != want}
    assert not wrong, f"path: (expected, routed): {wrong}"
    tiers = {p: msg for p in UNTRACKED if (msg := _gd()._tier_gate([p], r))}
    assert not tiers, f"untracked routed paths whose tier is wrong: {tiers}"


ROOT = Path(__file__).resolve().parent.parent
GATE_CODE = (".claude/hooks/*.py", "scripts/check_*.py", "design-mocks/check_*.py", ".gitlab-ci.yml")

# Files the gate code names that are not its inputs, each with the reason.
NOT_GATE_INPUTS = {
    ".claude/task/REVIEW_TEMPLATE.md": "named in a refusal message",
    ".claude/task/TEMPLATE.md": "named in a refusal message",
    "docs/agent_guardrails.md": "named in a docstring and a message",
    "docs/working_agreement.md": "named in messages; the sentence gate checks it as a subject",
    "docs/roles/platform_reliability.md": "named in a docstring",
    "docs/operations_guide.md": "named in a CI comment",
    "dbt_project/docs/engineering_standards.md": "named in refusal messages",
    "dbt_project/docs/layering.md": "named in refusal messages",
    "README.md": "a file name in a `find` command, not the root README",
    ".sqlfluff": "named in a CI comment about dbt_project/.sqlfluff; CI lints inside dbt_project",
    ".env.example": "in a CI `changes:` list: a change adds the setup check",
    "dbt_project/profiles.example.yml": "in a CI `changes:` list: a change adds the setup check",
    "scripts/bootstrap.py": "the setup script a CI job proves; a check runs it, never reads it",
    "scripts/list_mr_scratch.py": "named in a CI comment",
    "scripts/snapshot_tracker.py": "named in a refusal message",
    "scripts/build_match_preview_site.sh": "the frozen legacy site, in a CI `changes:` list",
    "scripts/build_match_preview_site.ps1": "the frozen legacy site, in a CI `changes:` list",
    "site/i18n/de.json": "the frozen legacy site, a subject of CI's JSON and i18n checks",
    "site/i18n/en.json": "the frozen legacy site, a subject of CI's JSON and i18n checks",
    "site/i18n/fi.json": "the frozen legacy site, a subject of CI's JSON and i18n checks",
    "site/match-preview/index.html": "the frozen legacy site, a subject of a CI check",
    "site/match-preview/metric_definitions.json": "the frozen legacy site, a subject of a CI check",
    "site/match-preview/metric_manifest.json": "the frozen legacy site, a subject of a CI check",
    "dbt_project/models/1_staging/api_football/sources.yml":
        "the dbt source list, the subject of the freshness check",
    "dbt_project/models/docs/metric_columns.md": "generated; the check compares it with its generator",
    "dbt_project/seeds/competition_types.csv": "the seed the check compares with the registry",
    "design-mocks/renders/competition-overview_2026-09-16_01.html": "an example in a docstring",
    "site_v2/src/lib/addressWords.mjs": "named in a docstring",
    "site_v2/src/lib/chartTheme.ts": "the subject the chart check checks",
    "site_v2/src/styles/system.css": "the site's stylesheet, page code; the mock checks compare with it",
    "tests/fixtures/component_registry/baseline.json": "a generated baseline, a companion",
    "tests/fixtures/design_inventory/baseline_quick.json": "a generated baseline, a companion",
    "tests/fixtures/design_inventory/baseline_quick_fi.json": "a generated baseline, a companion",
    "tests/fixtures/font_coverage/baseline.json": "a generated baseline, a companion",
}


# Exact paths only: a glob in gate code names the files the gate checks, not what it reads.
# A test a gate names is a companion, so it adds no reviewer.
def _gate_named_files() -> dict[str, set[str]]:
    files = _all_tracked()
    known = set(files)
    named: dict[str, set[str]] = {}
    for code in (f for f in files if any(fnmatch.fnmatch(f, g) for g in GATE_CODE)):
        text = (ROOT / code).read_text(encoding="utf-8", errors="replace")
        for token in re.findall(r"[\w.\-/]+", text):
            token = token.removeprefix("./").rstrip(".")
            if token in known and not token.startswith("tests/test_"):
                named.setdefault(token, set()).add(code)
    return named


def test_every_file_a_gate_names_is_a_risk_path():
    r, named = real_routing(), _gate_named_files()
    low = {p: sorted(c) for p, c in named.items()
           if _gd()._tier_of(p, r) < 2 and p not in NOT_GATE_INPUTS}
    assert not low, f"files a gate names that are below the risk tier: {low}"
    stale = sorted(p for p in NOT_GATE_INPUTS if p not in named or _gd()._tier_of(p, r) == 2)
    assert not stale, f"NOT_GATE_INPUTS entries no gate names, or already risk: {stale}"


@pytest.mark.parametrize("paths,want", [
    (["site_v2/src/pages/[lang]/index.astro", "tests/fixtures/design_inventory/baseline.json",
      "tests/test_x.py", "site_v2/src/lib/format.test.mjs"], {BI}),
    (["dbt_project/models/5_marts/x.sql", "dbt_project/tests/assert_x.sql", "tests/test_y.py"],
     {AE}),
    (["tests/test_x.py"], {PL}),
    (["docs/x.md", "tests/fixtures/x.json"], {PL}),
    (["site_v2/src/pages/[lang]/index.astro", "docs/design/components.yml",
      "tests/fixtures/component_registry/baseline.json"], {BI, CTO}),
    (["site_v2/src/pages/[lang]/index.astro", "tests/test_design_inventory.py"], {BI, CTO, PL}),
    (["site_v2/src/pages/[lang]/index.astro", "site_v2/scripts/check-built-pages.test.mjs"],
     {BI, CTO, PL}),
    (["tests/test_governance_hooks.py"], {PL}),
    (["design-mocks/check_mock_css.py", "tests/test_mock_css.py"], {BI, CTO}),
    ([".claude/skills/research-provider-errors/SKILL.md", "dbt_project/macros/x.sql",
      "tests/test_x.py"], {AE, CTO}),
])
def test_a_branch_s_own_tests_add_no_reviewer(paths, want):
    assert _gd()._required_reviewers(paths, real_routing()) == want


@pytest.mark.parametrize("drop", ["tiers", "max_reviewers"])
def test_a_routing_file_without_a_tier_key_skips_the_tier_check(drop):
    routing = {k: v for k, v in TIER_ROUTING.items() if k != drop}
    assert _gd()._tier_gate(["scripts/x.py"], routing) is None
    assert _gd()._tier_gate(["scripts/x.py"], TIER_ROUTING) is not None


def test_a_backslash_path_is_normalised():
    msg = _gd()._tier_gate(["scripts\\x.py"], TIER_ROUTING)
    assert msg and "scripts/x.py" in msg, msg


def test_a_contract_only_branch_needs_no_reviewer():
    paths = [".claude/task/348-one-reviewer/contract.md"]
    assert _gd()._required_reviewers(paths, real_routing()) == set()


# --- the commit gate and the CI backstop on a synthetic repo ---
TIER_ROUTING = dict(
    ROUTING,
    always=[],
    max_reviewers=2,
    tiers={"risk": {"reviewers": 2, "paths": [".claude/hooks/**"]},
           "territory": {"reviewers": 1, "paths": ["dbt_project/**", "scripts/**", "tests/**"]}},
    companion_paths=["tests/**"],
    paths={"dbt_project/**": [AE], ".claude/hooks/**": [CTO, PL], "tests/**": [PL]},
)

TIER_CONTRACT = CONTRACT.replace(
    "scope_paths:\n",
    "scope_paths:\n  - .claude/hooks/h.py\n  - scripts/x.py\n  - dbt_project/models/new.sql\n")


def _pass(name: str) -> str:
    return f"## {name}\nVERDICT: PASS\nrisks_checked:\n- checked the diff\n\n"


def _setup(repo) -> None:
    (repo / ".claude" / "review_routing.json").write_text(json.dumps(TIER_ROUTING))
    (repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(TIER_CONTRACT)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "routing+contract"], cwd=repo, check=True)


def _stage(repo, *rels: str) -> None:
    for rel in rels:
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("changed\n")
        subprocess.run(["git", "add", rel], cwd=repo, check=True)


def _commit_gate(repo) -> str:
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    return out


def test_a_text_only_branch_commits_without_review(repo):
    _setup(repo)
    _stage(repo, "docs/allowed_dir/x.md")
    out = _commit_gate(repo)
    assert not denied(out), out


def test_text_and_territory_need_only_the_owner(repo):
    _setup(repo)
    _stage(repo, "docs/allowed_dir/x.md", "dbt_project/models/allowed.sql")
    write_review(repo, staged_hash(repo), _pass(AE))
    out = _commit_gate(repo)
    assert not denied(out), out


def test_a_model_and_its_test_need_only_the_owner(repo):
    _setup(repo)
    _stage(repo, "dbt_project/models/allowed.sql", "tests/test_fix.py")
    write_review(repo, staged_hash(repo), _pass(AE))
    out = _commit_gate(repo)
    assert not denied(out), out


def test_a_tests_only_branch_needs_their_owner(repo):
    _setup(repo)
    _stage(repo, "tests/test_fix.py")
    out = _commit_gate(repo)
    assert denied(out) and "review" in out


def test_gate_refuses_a_path_without_its_reviewers(repo):
    _setup(repo)
    _stage(repo, "scripts/x.py")
    out = _commit_gate(repo)
    assert denied(out) and "scripts/x.py" in out and "tier" in out


def test_gate_refuses_three_reviewers(repo):
    _setup(repo)
    _stage(repo, "dbt_project/models/allowed.sql", ".claude/hooks/h.py")
    write_review(repo, staged_hash(repo), _pass(AE) + _pass(CTO) + _pass(PL))
    out = _commit_gate(repo)
    assert denied(out) and "split" in out.lower()


def test_a_staged_text_commit_on_a_reviewed_branch_needs_review(repo):
    _setup(repo)
    _stage(repo, ".claude/hooks/h.py")
    subprocess.run(["git", "commit", "-qm", "reviewed hook"], cwd=repo, check=True)
    _stage(repo, "docs/allowed_dir/x.md")
    out = _commit_gate(repo)
    assert denied(out) and "review" in out


def _ci_setup(ci_repo, base_files: tuple[str, ...] = ()) -> None:
    """Commits the tier routing (and `base_files`) on main, then returns to the feature branch."""
    subprocess.run(["git", "checkout", "-q", "main"], cwd=ci_repo, check=True)
    (ci_repo / ".claude" / "review_routing.json").write_text(json.dumps(TIER_ROUTING))
    for rel in base_files:
        (ci_repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (ci_repo / rel).write_text("base\n")
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "tier routing"], cwd=ci_repo, check=True)
    subprocess.run(["git", "checkout", "-q", "-B", "feature"], cwd=ci_repo, check=True)
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(TIER_CONTRACT)


def _ci_commit(ci_repo, *rels: str) -> None:
    for rel in rels:
        (ci_repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (ci_repo / rel).write_text("changed\n")
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "work"], cwd=ci_repo, check=True)


def test_ci_passes_a_text_only_branch(ci_repo):
    _ci_setup(ci_repo)
    _ci_commit(ci_repo, "docs/allowed_dir/x.md")
    code, out = run_ci_check(ci_repo)
    assert code == 0, out


def test_ci_refuses_three_reviewers(ci_repo):
    _ci_setup(ci_repo)
    _ci_commit(ci_repo, "dbt_project/models/allowed.sql", ".claude/hooks/h.py")
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "split" in out.lower()


def test_ci_passes_a_model_and_its_test_with_only_the_owner(ci_repo):
    _ci_setup(ci_repo)
    _ci_commit(ci_repo, "dbt_project/models/allowed.sql", "tests/test_fix.py")
    (ci_repo / ".claude" / "task" / TASK_ID / "review.md").write_text(
        "# Review\ndiff_sha256: " + branch_hash(ci_repo) + "\nrounds: 1\n\n" + _pass(AE))
    _ci_commit(ci_repo)
    code, out = run_ci_check(ci_repo)
    assert code == 0, out


def test_ci_refuses_a_path_outside_scope(ci_repo):
    _ci_setup(ci_repo)
    _ci_commit(ci_repo, "docs/elsewhere.md")
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "scope_paths" in out and "docs/elsewhere.md" in out


def test_ci_exempts_the_task_folder(ci_repo):
    _ci_setup(ci_repo)
    _ci_commit(ci_repo, f".claude/task/{TASK_ID}/notes.md", "docs/allowed_dir/x.md")
    code, out = run_ci_check(ci_repo)
    assert code == 0, out


def _ci_paths(ci_repo, monkeypatch) -> list[str]:
    sys.path.insert(0, SCRIPTS)
    import check_task_artifacts as ci
    monkeypatch.chdir(ci_repo)
    return ci.changed_paths("main")


def test_a_rename_keeps_its_reviewers(ci_repo, monkeypatch):
    _ci_setup(ci_repo, base_files=(".claude/hooks/h.py",))
    (ci_repo / "docs" / "allowed_dir").mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "mv", ".claude/hooks/h.py", "docs/allowed_dir/h.py"],
                   cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "move"], cwd=ci_repo, check=True)
    paths = _ci_paths(ci_repo, monkeypatch)
    assert ".claude/hooks/h.py" in paths, paths
    assert _gd()._required_reviewers(paths, TIER_ROUTING) == {CTO, PL}


def test_a_deleted_path_keeps_its_reviewers(ci_repo, monkeypatch):
    _ci_setup(ci_repo, base_files=(".claude/hooks/h.py",))
    subprocess.run(["git", "rm", "-q", ".claude/hooks/h.py"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "delete"], cwd=ci_repo, check=True)
    paths = _ci_paths(ci_repo, monkeypatch)
    assert _gd()._required_reviewers(paths, TIER_ROUTING) == {CTO, PL}


@pytest.mark.parametrize("path,tier", [
    ("scripts/security/check_no_secrets.py", 2),
    ("site_v2/scripts/check-built-pages.test.mjs", 2),
    ("ingestion/api_football/loads/fixtures.py", 2),
    ("deploy/site/Dockerfile", 2),
    ("site_v2/.gitignore", 1),
    ("dbt_project/.sqlfluff", 2),
    ("dbt_project/dbt_project.yml", 1),
    ("dbt_project/seeds/metric_catalogue.csv", 2),
    ("docs/data_contract.md", 0),
])
def test_a_path_takes_its_highest_tier(path, tier):
    assert _gd()._tier_of(path, real_routing()) == tier
