"""The reviewer standard: the briefs, working_agreement.md §2 and §10, and the gate's findings check."""
# ruff: noqa: F811  (the imported fixtures are requested by name as test parameters)

from __future__ import annotations

import glob
import os
import re
import subprocess

import pytest

from test_governance_hooks import (  # noqa: F401  (fixtures are used by name)
    COMMIT_CMD,
    CONTRACT,
    GOOD_BODY,
    TASK_ID,
    _repo_template,
    bash_event,
    branch_hash,
    ci_repo,
    denied,
    repo,
    run_ci_check,
    run_hook,
    setup_review_repo,
    staged_hash,
)

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
AGENTS = os.path.join(REPO, ".claude", "agents")
AGREEMENT = os.path.join(REPO, "docs", "working_agreement.md")
TEMPLATE = os.path.join(REPO, ".claude", "task", "REVIEW_TEMPLATE.md")
STANDARD_HEADER = "## Reviewer standard"


def _briefs() -> list[str]:
    return sorted(b for b in glob.glob(os.path.join(AGENTS, "*.md"))
                  if os.path.basename(b) != "README.md")


def _read(path: str) -> str:
    return open(path, encoding="utf-8").read()


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _section(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


def test_every_brief_ends_with_the_identical_standard():
    briefs = _briefs()
    assert len(briefs) == 8, f"expected the 8 reviewer briefs, found {len(briefs)}"
    tails = {}
    for b in briefs:
        text = _read(b)
        assert STANDARD_HEADER in text, f"{os.path.basename(b)} has no standard section"
        tails[os.path.basename(b)] = text.split(STANDARD_HEADER, 1)[1]
    assert len(set(tails.values())) == 1, f"standard sections differ: {sorted(tails)}"
    tail = _flat(next(iter(tails.values())))
    for phrase in ("§2", "Cross-Examination", "one pass", "every place", "[blocking]", "[nit]",
                   "A nit never fails a round", "only the fix diff and your own findings",
                   "unchanged since round 1", "concrete failing case", "follow-up issue",
                   "| proof:", "A finding without a proof is a nit"):
        assert phrase in tail, f"the standard section lacks {phrase!r}"


def test_no_brief_keeps_the_open_hunt():
    for b in _briefs():
        flat = _flat(_read(b))
        for phrase in ("Start from the assumption", "go looking", "Assume the primary agent",
                       "## Delta re-review"):
            assert phrase not in flat, f"{os.path.basename(b)} still says {phrase!r}"


def test_section_2_states_every_rule():
    text = _flat(_section(_read(AGREEMENT), "**Cross-Examination.**", "**Lock.**"))
    for phrase in (
        "the contract's acceptance criteria, its own checklist and Appendix A",
        "every finding in one pass",
        "names its class and every place in the change where that class occurs",
        "Blocking means wrong data, an acceptance criterion not met, security, "
        "a §10 decision or a guard regression",
        "A nit never fails a round",
        "fixes the whole class",
        "a test that fails before the fix",
        "After a FAIL, the re-review gets only the fix diff and the reviewer's own findings",
        "A new blocking finding on a line unchanged since round 1 carries a concrete failing case",
        "becomes a follow-up issue",
        "A blocking finding names its proof",
        "A finding without a proof is a nit",
        "The builder may close a finding it cannot reproduce",
        "`## closed`",
    ):
        assert phrase in text, f"§2 lacks {phrase!r}"


def test_section_2_states_the_tiers():
    text = _flat(_section(_read(AGREEMENT), "**Blinding.**", "**Reviewer models.**"))
    for phrase in (
        "A text path (text, copy and docs) gets no AI reviewer",
        "A territory path",
        "gets one reviewer, the owner of the territory",
        "A risk path (gates, hooks, CI, cost, prod writes, ingestion) gets the owner and one "
        "specialist",
        "never needs more than two reviewers",
        "A branch's own tests and baselines add no reviewer",
        "A test on a risk path keeps its reviewers; every other test adds none, a gate's own "
        "test included",
    ):
        assert phrase in text, f"§2 Blinding lacks {phrase!r}"
    assert "`scope-auditor` always" not in text


def test_section_2_states_the_size_rule():
    text = _flat(_section(_read(AGREEMENT), "### Review cycle", "**Blinding.**"))
    assert "at most about 400 lines, tests and generated files not counted" in text


def test_the_cap_is_one_rule():
    text = _flat(_read(AGREEMENT))
    split = ("the approach is rethought and the work is split. What passed lands; the rest is "
             "split off into its own issue. A further round is the CPO's call.")
    lock = _section(text, "**Lock.**", "### Commit gate")
    cap10 = _section(text, "**Review cap.**", "**Unclear cases.**")
    assert "The round cap is 2 reviewer rounds per issue, counted across sessions" in lock
    assert split in lock, "§2 does not state the split rule"
    assert split in cap10, "§10 does not state the same split rule as §2"
    assert "brings the open findings" not in text
    assert "cap of 2 without" in _section(text, "### Commit gate", "## 3.")
    assert _gd().ROUND_CAP == 2


def test_a_wording_breach_is_a_nit():
    text = _flat(_read(os.path.join(AGENTS, "scope-auditor.md")))
    item = _section(text, "**Writing standards**", "**Approved design")
    assert "A breach is a nit" in item
    assert "A breach is a FAIL" not in item


def _gate(repo, body: str, rounds: str = "rounds: 1\n") -> str:
    (repo / ".claude" / "task" / TASK_ID / "review.md").write_text(
        f"# Review\ndiff_sha256: {staged_hash(repo)}\n{rounds}\n{body}\n", encoding="utf-8")
    out, _ = run_hook("git_discipline.py", bash_event(COMMIT_CMD), repo)
    return out


def _with_scope_findings(lines: str, verdict: str = "PASS") -> str:
    return GOOD_BODY.replace(
        "## scope-auditor\nVERDICT: PASS\n",
        f"## scope-auditor\nVERDICT: {verdict}\nfindings:\n{lines}", 1)


NIT = "- [nit] wording: docs/x.md:3 — two topics in one sentence\n"
UNPROVEN = "- [blocking] guard regression: x.py:9, y.py:4 — the hook now fails closed"
BLOCKING = UNPROVEN + " | proof: `python x.py --bad-input`\n"


@pytest.mark.parametrize("line", [
    "- docs/x.md:3 — two topics in one sentence\n",
    "- [minor] wording: docs/x.md:3 — two topics\n",
    "- [nit] docs/x.md:3 two topics\n",
    "- [nit] wording: docs/x.md:3 two topics in one sentence\n",
])
def test_gate_refuses_a_finding_without_severity_and_class(repo, line):
    setup_review_repo(repo)
    out = _gate(repo, _with_scope_findings(line))
    assert denied(out) and "[blocking]" in out


def test_ci_backstop_refuses_the_same_review(ci_repo):
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code+contract"], cwd=ci_repo, check=True)
    body = _with_scope_findings("- docs/x.md:3 — two topics in one sentence\n")
    (ci_repo / ".claude" / "task" / TASK_ID / "review.md").write_text(
        "# Review\ndiff_sha256: " + branch_hash(ci_repo) + "\nrounds: 1\n\n" + body,
        encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "review"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 1 and "[blocking]" in out


def test_a_pass_with_nits_commits(repo):
    setup_review_repo(repo)
    assert not denied(_gate(repo, _with_scope_findings(NIT)))


def test_a_pass_with_a_blocking_finding_is_refused(repo):
    setup_review_repo(repo)
    out = _gate(repo, _with_scope_findings(BLOCKING))
    assert denied(out) and "blocking" in out and "PASS" in out


def test_a_fail_of_nits_is_refused_with_the_nit_rule(repo):
    setup_review_repo(repo)
    out = _gate(repo, _with_scope_findings(NIT, verdict="FAIL"))
    assert denied(out) and "nit never fails" in out


@pytest.mark.parametrize("tail", [
    "", " | proof:", " | proof: <test or command>", " | proof: none",
    " | proof: it fails on main", " | proof: docs/x.md::test_y",
    " | proof: tests/test_x.py::test_y fails on main",
    " | proof: `<command>`", " | proof: `tbd`", " | proof: ` `",
])
def test_a_blocking_finding_without_proof_is_refused(repo, tail):
    setup_review_repo(repo)
    out = _gate(repo, _with_scope_findings(UNPROVEN + tail + "\n", verdict="FAIL"))
    assert denied(out) and "proof" in out


@pytest.mark.parametrize("proof", [
    "tests/test_x.py::test_y", "tests/hooks/test_x.py", "dbt_project/tests/assert_x.sql",
    "site_v2/src/lib/x.test.mjs", "`python x.py --bad-input`",
])
def test_a_blocking_finding_with_proof_passes_the_format_check(tmp_path, proof):
    review = ("rounds: 1\n## platform-reviewer\nVERDICT: FAIL\nfindings:\n"
              f"{UNPROVEN} | proof: {proof}\n")
    assert _gd()._findings_gate(review, [], str(tmp_path)) is None


def test_a_nit_needs_no_proof(tmp_path):
    review = "rounds: 1\n## platform-reviewer\nVERDICT: PASS\nfindings:\n" + NIT
    assert _gd()._findings_gate(review, [], str(tmp_path)) is None


SECOND = "- [blocking] wrong data: m.sql:4 — rows double | proof: `pytest tests/test_m.py`\n"
CLOSES_IT = "scope-auditor | guard regression | the command exits 0 on this branch"


def _closed(*entries: str) -> str:
    return "\n## closed\n" + "".join(f"- {e}\n" for e in entries)


def test_a_closed_fail_commits(repo):
    setup_review_repo(repo)
    out = _gate(repo, _with_scope_findings(BLOCKING, verdict="FAIL") + _closed(CLOSES_IT))
    assert not denied(out), out


def test_a_closed_finding_needs_no_proof(repo):
    setup_review_repo(repo)
    body = _with_scope_findings(UNPROVEN + "\n", verdict="FAIL") + _closed(
        "scope-auditor | guard regression | the finding names no proof and none reproduces it")
    out = _gate(repo, body)
    assert not denied(out), out


def test_a_partly_closed_fail_is_refused(repo):
    setup_review_repo(repo)
    out = _gate(repo, _with_scope_findings(BLOCKING + SECOND, verdict="FAIL") + _closed(CLOSES_IT))
    assert denied(out) and "FAIL" in out


@pytest.mark.parametrize("entry,word", [
    ("scope-auditor | other class | the command exits 0", "closes no"),
    ("analytics-engineer-reviewer | guard regression | the command exits 0", "closes no"),
    ("scope-auditor | guard regression | tbd", "reason"),
    ("scope-auditor | guard regression | <reason>", "reason"),
    ("scope-auditor | guard regression |", "reason"),
    ("scope-auditor guard regression, it exits 0", "closed"),
])
def test_a_bad_closure_is_refused(repo, entry, word):
    setup_review_repo(repo)
    out = _gate(repo, _with_scope_findings(BLOCKING, verdict="FAIL") + _closed(entry))
    assert denied(out) and word in out


HIDDEN = "\n## scope-auditor\nVERDICT: PASS\nrisks_checked:\n- risk one checked\n"


def test_a_hidden_fail_is_refused(repo):
    setup_review_repo(repo)
    out = _gate(repo, _with_scope_findings(BLOCKING, verdict="FAIL") + HIDDEN)
    assert denied(out) and "FAIL" in out


@pytest.mark.parametrize("section", ["closed", "fixes"])
def test_a_fail_outside_a_reviewer_section_is_refused(repo, section):
    setup_review_repo(repo)
    out = _gate(repo, GOOD_BODY + f"\n## {section}\nVERDICT: FAIL\n")
    assert denied(out) and "FAIL" in out


def _ci_review(ci_repo, body: str) -> tuple[int, str]:
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code+contract"], cwd=ci_repo, check=True)
    (ci_repo / ".claude" / "task" / TASK_ID / "review.md").write_text(
        "# Review\ndiff_sha256: " + branch_hash(ci_repo) + "\nrounds: 1\n\n" + body,
        encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "review"], cwd=ci_repo, check=True)
    return run_ci_check(ci_repo)


@pytest.mark.parametrize("findings,tail,code", [
    (BLOCKING, _closed(CLOSES_IT), 0),
    (BLOCKING + SECOND, _closed(CLOSES_IT), 1),
    (BLOCKING, HIDDEN, 1),
], ids=["closed", "partly-closed", "hidden"])
def test_ci_backstop_agrees_on_closures(ci_repo, findings, tail, code):
    got, out = _ci_review(ci_repo, _with_scope_findings(findings, verdict="FAIL") + tail)
    assert got == code, out


def test_round_two_commits_and_round_three_needs_the_cpo(repo):
    setup_review_repo(repo)
    _stage_test_file(repo)
    fixes = "\n## fixes\n- a class | sweep: grep -rn x . | test: tests/test_fix.py::test_fix\n"
    assert not denied(_gate(repo, GOOD_BODY + fixes, rounds="rounds: 2\n"))
    out = _gate(repo, GOOD_BODY + fixes, rounds="rounds: 3\n")
    assert denied(out) and "cap of 2" in out and "rethought" in out
    override = "rounds: 3\nrounds_cap_override: approved in chat, 2026-11-24\n"
    assert not denied(_gate(repo, GOOD_BODY + fixes, rounds=override))


def _stage_test_file(repo, rel: str = "tests/test_fix.py") -> None:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("def test_fix():\n    assert True\n")
    subprocess.run(["git", "add", rel], cwd=repo, check=True)


def test_round_two_without_fixes_is_refused(repo):
    setup_review_repo(repo)
    _stage_test_file(repo)
    out = _gate(repo, GOOD_BODY, rounds="rounds: 2\n")
    assert denied(out) and "## fixes" in out


def test_a_fix_whose_test_is_not_in_the_branch_is_refused(repo):
    setup_review_repo(repo)
    fixes = ("\n## fixes\n- guard regression | sweep: grep -n fail_closed .claude/hooks"
             " | test: tests/test_other.py::test_fix\n")
    out = _gate(repo, GOOD_BODY + fixes, rounds="rounds: 2\n")
    assert denied(out) and "tests/test_other.py" in out


def test_round_two_with_a_tested_fix_commits(repo):
    setup_review_repo(repo)
    _stage_test_file(repo)
    fixes = ("\n## fixes\n- guard regression | sweep: grep -n fail_closed .claude/hooks"
             " | test: tests/test_fix.py::test_fix\n")
    out = _gate(repo, GOOD_BODY + fixes, rounds="rounds: 2\n")
    assert not denied(out), out


def _fix(test: str) -> str:
    return f"\n## fixes\n- guard regression | sweep: grep -rn x . | test: {test}\n"


@pytest.mark.parametrize("rel", ["docs/x.md", "dbt_project/models/allowed.sql"])
def test_a_fix_naming_a_file_that_is_not_a_test_is_refused(repo, rel):
    setup_review_repo(repo)
    _stage_test_file(repo, rel)
    out = _gate(repo, GOOD_BODY + _fix(rel), rounds="rounds: 2\n")
    assert denied(out) and "not a test" in out


def test_a_fix_test_the_branch_does_not_change_is_refused(repo):
    setup_review_repo(repo)
    (repo / "tests").mkdir(exist_ok=True)
    (repo / "tests" / "test_old.py").write_text("def test_old():\n    assert True\n")
    out = _gate(repo, GOOD_BODY + _fix("tests/test_old.py::test_old"), rounds="rounds: 2\n")
    assert denied(out) and "tests/test_old.py" in out


@pytest.mark.parametrize("rel", [
    "dbt_project/tests/assert_x.sql",
    "site_v2/src/lib/x.test.mjs",
    "site_v2/scripts/x.test.mjs",
])
def test_every_test_location_the_repo_runs_is_a_fix_test(repo, rel):
    setup_review_repo(repo)
    _stage_test_file(repo, rel)
    out = _gate(repo, GOOD_BODY + _fix(rel), rounds="rounds: 2\n")
    assert not denied(out), out


def test_a_round_after_a_pass_commits_with_a_none_entry(repo):
    setup_review_repo(repo)
    fixes = "\n## fixes\n- none: round 1 passed; a merge of main changed the hash\n"
    out = _gate(repo, GOOD_BODY + fixes, rounds="rounds: 2\n")
    assert not denied(out), out


@pytest.mark.parametrize("fixes", [
    "- none: round 1 passed\n- guard regression | sweep: grep -rn x . | test: tests/test_fix.py\n",
    "- none:\n",
])
def test_a_none_entry_beside_a_fix_is_refused(repo, fixes):
    setup_review_repo(repo)
    _stage_test_file(repo)
    out = _gate(repo, GOOD_BODY + "\n## fixes\n" + fixes, rounds="rounds: 2\n")
    assert denied(out) and "none" in out


def test_a_fixes_entry_without_its_sweep_is_refused(repo):
    setup_review_repo(repo)
    _stage_test_file(repo)
    fixes = "\n## fixes\n- guard regression | test: tests/test_fix.py::test_fix\n"
    out = _gate(repo, GOOD_BODY + fixes, rounds="rounds: 2\n")
    assert denied(out) and "sweep" in out


def _gd():
    import importlib
    import sys
    sys.path.insert(0, os.path.join(REPO, ".claude", "hooks"))
    return importlib.import_module("git_discipline")


def test_a_fix_test_missing_on_disk_is_refused(tmp_path):
    review = ("rounds: 2\n" + GOOD_BODY + "\n## fixes\n- a class | sweep: grep -rn x ."
              " | test: tests/test_gone.py::test_x\n")
    msg = _gd()._findings_gate(review, ["tests/test_gone.py"], str(tmp_path))
    assert msg and "tests/test_gone.py" in msg


def test_ci_backstop_accepts_a_tested_fix(ci_repo):
    (ci_repo / "dbt_project" / "models" / "new.sql").write_text("select 1")
    (ci_repo / "tests").mkdir(exist_ok=True)
    (ci_repo / "tests" / "test_fix.py").write_text("def test_fix():\n    assert True\n")
    (ci_repo / ".claude" / "task" / TASK_ID / "contract.md").write_text(CONTRACT)
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "code+contract"], cwd=ci_repo, check=True)
    fixes = "\n## fixes\n- a class | sweep: grep -rn x . | test: tests/test_fix.py::test_fix\n"
    (ci_repo / ".claude" / "task" / TASK_ID / "review.md").write_text(
        "# Review\ndiff_sha256: " + branch_hash(ci_repo) + "\nrounds: 2\n\n" + GOOD_BODY + fixes,
        encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=ci_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "review"], cwd=ci_repo, check=True)
    code, out = run_ci_check(ci_repo)
    assert code == 0, out


def test_gate_refuses_when_the_branch_paths_cannot_be_listed(repo, monkeypatch):
    setup_review_repo(repo)
    (repo / ".claude" / "task" / TASK_ID / "review.md").write_text(
        f"# Review\ndiff_sha256: {staged_hash(repo)}\nrounds: 1\n{GOOD_BODY}\n", encoding="utf-8")
    gd = _gd()
    real = gd._cumulative_diff

    def failing(root, spec, raw=False):
        if "--name-only" in spec:
            raise RuntimeError("git diff failed")
        return real(root, spec, raw)

    monkeypatch.setattr(gd, "_cumulative_diff", failing)
    msg = gd._commit_gate(str(repo))
    assert msg and "could not be listed" in msg


def test_the_template_examples_pass_the_gate():
    import importlib
    import sys
    sys.path.insert(0, os.path.join(REPO, ".claude", "hooks"))
    gd = importlib.import_module("git_discipline")
    text = _read(TEMPLATE)
    findings = re.findall(r"^- (\[(?:blocking|nit)\].*)$", text, flags=re.MULTILINE)
    fixes = re.findall(r"^- (.+\| sweep: .*)$", text, flags=re.MULTILINE)
    assert findings and fixes, "the template shows no finding or no fixes entry"
    for line in findings:
        assert gd.FINDING_RE.match(line), line
        assert gd._proof_error(line) is None, line
    closures = gd._bullets(gd._review_sections(text).get("closed", ""))
    assert closures and all(gd.CLOSED_RE.match(c) for c in closures), closures
    for line in fixes:
        assert gd.FIX_RE.match(line), line
