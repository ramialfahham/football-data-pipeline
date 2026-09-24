"""A document says WHAT and WHY, never who decided or when — the guard, both halves.

Half one is the edit-time hook `.claude/hooks/comment_history_gate.py`: for a Markdown document it
refuses an `Edit`, `Write` or `MultiEdit` that ADDS a line carrying history (a date, a reviewer
credit, a review round, an MR number; and in CLAUDE.md an issue number). Half two is the pin below:
each document's count of such lines, which may only move down, in the open.

Everything imports the hook's definitions, so the CI count and the edit-time refusal cannot drift
apart. Sample lines are built at runtime from pieces, so this file holds no flagged line itself.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
HOOKS = os.path.join(REPO, ".claude", "hooks")
sys.path.insert(0, HOOKS)
import comment_history_gate as gate  # noqa: E402

# The pin: flagged lines per document. A cleanup lowers a number or removes a row; nothing adds one.
PINNED = {
    ".claude/agents/analytics-engineer-reviewer.md": 2,
    ".claude/agents/bi-analyst-reviewer.md": 5,
    ".claude/agents/cto-reviewer.md": 8,
    ".claude/agents/data-engineer-reviewer.md": 3,
    ".claude/agents/football-analytics-expert-reviewer.md": 2,
    ".claude/agents/platform-reviewer.md": 2,
    ".claude/agents/scope-auditor.md": 5,
    ".claude/agents/seo-expert-reviewer.md": 2,
    ".claude/skills/onboard-competition/SKILL.md": 2,
    ".github/workflows/README.md": 6,
    "AGENTS.md": 1,
    "dbt_project/docs/engineering_standards.md": 5,
    "dbt_project/docs/layering.md": 14,
    "deploy/nightly/README.md": 1,
    "design-mocks/README.md": 6,
    "docs/agent_guardrails.md": 15,
    "docs/audits/2026-06_alignment_audit.md": 26,
    "docs/content_architecture.md": 8,
    "docs/cursor_dispatch_workflow.md": 1,
    "docs/data_contract.md": 12,
    "docs/metrics_context_model.md": 8,
    "docs/north_star.md": 7,
    "docs/operations_guide.md": 1,
    "docs/playoff_window_policy.md": 1,
    "docs/product_direction_threads.md": 7,
    "docs/project_status_sync.md": 1,
    "docs/roles/cto.md": 1,
    "docs/roles/data_engineer.md": 1,
    "docs/roles/platform_reliability.md": 2,
    "docs/roles/seo_expert.md": 1,
    "docs/site_architecture.md": 21,
    "docs/ui_design_brief.md": 7,
    "docs/wireframes/00_overview.md": 7,
    "docs/wireframes/01_fixture_page.md": 4,
    "docs/wireframes/02_team_profile.md": 1,
    "docs/wireframes/03_player_profile.md": 1,
    "docs/wireframes/08_browse.md": 6,
    "docs/wireframes/10_home.md": 115,
    "docs/wireframes/11_team_squad.md": 6,
    "docs/wireframes/12_player_stats.md": 2,
    "docs/wireframes/14_team_stats.md": 3,
    "docs/wireframes/99_gaps_register.md": 28,
    "docs/wireframes/block_standard.md": 6,
    "docs/wireframes/metrics_display.md": 34,
    "docs/working_agreement.md": 16,
    "site_v2/src/data/README.md": 12,
}

DATE = "-".join(["20" + "31", "01", "02"])
ISSUE = "#" + "4" + "2"


def _tracked_docs() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z", "*.md"], cwd=REPO, capture_output=True, check=True)
    return [p for p in out.stdout.decode("utf-8").split("\0") if p]


def run_hook(tool_input: dict, tool: str = "Edit") -> str:
    event = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input}
    env = dict(os.environ, CLAUDE_PROJECT_DIR=REPO)
    proc = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "comment_history_gate.py")],
        input=json.dumps(event), capture_output=True, text=True, env=env, timeout=60, check=False,
    )
    return proc.stdout


def denied(out: str) -> bool:
    return '"permissionDecision": "deny"' in out


def doc(rel: str) -> str:
    return os.path.join(REPO, rel)


# --- the pin -----------------------------------------------------------------------------------

def test_every_document_matches_the_pin_in_both_directions():
    counts = gate.count_docs(REPO, _tracked_docs())
    grown = {p: n for p, n in counts.items() if n > PINNED.get(p, 0)}
    assert not grown, (
        f"documents gained history lines: {grown}. A document says WHAT and WHY; dates, issue and "
        "MR numbers and who found or decided what live in the commit, the MR and the issue "
        "(engineering_standards.md section 1.2)."
    )
    shrunk = {p: (PINNED[p], counts.get(p, 0)) for p in PINNED if counts.get(p, 0) < PINNED[p]}
    assert not shrunk, (
        f"documents lost history lines (pinned, now): {shrunk}. Lower their numbers in PINNED "
        "(remove a row at zero) so the cleanup is recorded; the pin only moves down"
    )


def test_every_guarded_document_is_readable():
    """`count_docs` skips a file it cannot open; the pin must never pass because a path was skipped."""
    unreadable = [p for p in _tracked_docs()
                  if gate.is_doc_path(p) and not os.path.isfile(os.path.join(REPO, p))]
    assert not unreadable, f"tracked documents the pin cannot read: {unreadable}"


def test_claude_md_holds_no_history():
    text = pathlib.Path(REPO, "CLAUDE.md").read_text(encoding="utf-8")
    assert gate.doc_flagged_lines(text, "CLAUDE.md") == []
    assert "CLAUDE.md" not in PINNED


# --- one definition ----------------------------------------------------------------------------

def test_definition_is_imported_not_copied():
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert "re." + "compile(" not in src, "the marker patterns live in the hook; this file imports them"
    for name in ("DOC_MARKERS", "is_doc_path", "doc_flagged_lines", "doc_added_hits", "count_docs"):
        assert hasattr(gate, name), name


# --- the hook ----------------------------------------------------------------------------------

def test_hook_refuses_an_added_dated_line_in_a_document():
    out = run_hook({"file_path": doc("docs/north_star.md"), "old_string": "x",
                    "new_string": f"The rule changed on {DATE}."})
    assert denied(out)
    assert "COMMENT HISTORY GATE" in out and "document" in out


def test_hook_allows_an_edit_that_keeps_an_existing_dated_line():
    kept = f"An older paragraph dated {DATE}."
    out = run_hook({"file_path": doc("docs/north_star.md"),
                    "old_string": kept + "\nA typo here.", "new_string": kept + "\nA fix here."})
    assert out.strip() == ""


def test_hook_allows_a_clean_line_and_a_date_inside_code():
    assert run_hook({"file_path": doc("docs/north_star.md"), "old_string": "x",
                     "new_string": "A rule and its reason."}).strip() == ""
    assert run_hook({"file_path": doc("docs/site_architecture.md"), "old_string": "x",
                     "new_string": f"A match address looks like `/en/bl1/{DATE}/a-vs-b/`."}).strip() == ""
    fenced = f"```\n/en/bl1/{DATE}/a-vs-b/\n```"
    assert run_hook({"file_path": doc("docs/site_architecture.md"), "old_string": "x",
                     "new_string": fenced}).strip() == ""


def test_hook_allows_role_names_and_football_rounds_in_documents():
    text = "The " + "cto-" + "reviewer rules on authority. Round " + "5 is a matchday."
    assert run_hook({"file_path": doc("docs/working_agreement.md"), "old_string": "x",
                     "new_string": text}).strip() == ""


def test_hook_refuses_a_reviewer_credit_and_an_mr_number():
    credit = "The " + "platform-" + "reviewer caught this."
    assert denied(run_hook({"file_path": doc("docs/working_agreement.md"), "old_string": "x",
                            "new_string": credit}))
    mr = "Fixed in " + "!" + "132."
    assert denied(run_hook({"file_path": doc("docs/working_agreement.md"), "old_string": "x",
                            "new_string": mr}))


def test_issue_numbers_are_refused_in_claude_md_only():
    line = f"See {ISSUE} for the plan."
    assert denied(run_hook({"file_path": doc("CLAUDE.md"), "old_string": "x", "new_string": line}))
    assert run_hook({"file_path": doc("docs/site_architecture.md"), "old_string": "x",
                     "new_string": line}).strip() == ""


def test_write_compares_against_the_file_on_disk(tmp_path):
    existing = pathlib.Path(REPO, "docs/wireframes/10_home.md").read_text(encoding="utf-8")
    assert run_hook({"file_path": doc("docs/wireframes/10_home.md"), "content": existing},
                    tool="Write").strip() == ""
    assert denied(run_hook({"file_path": doc("docs/wireframes/10_home.md"),
                            "content": existing + f"\nAdded on {DATE}.\n"}, tool="Write"))


def test_multiedit_refuses_an_added_line_and_allows_a_kept_one():
    kept = f"An older paragraph dated {DATE}."
    refused = {"file_path": doc("docs/north_star.md"),
               "edits": [{"old_string": "a", "new_string": "b"},
                         {"old_string": "c", "new_string": f"Changed on {DATE}."}]}
    assert denied(run_hook(refused, tool="MultiEdit"))
    allowed = {"file_path": doc("docs/north_star.md"),
               "edits": [{"old_string": kept + "\nA typo.", "new_string": kept + "\nA fix."}]}
    assert run_hook(allowed, tool="MultiEdit").strip() == ""


def test_exempt_paths_are_not_checked():
    line = f"Recorded on {DATE}."
    for rel in (".claude/task/contract.md", "docs/tracker/gitlab_snapshot.md", "site/README.md"):
        assert run_hook({"file_path": doc(rel), "old_string": "x", "new_string": line}).strip() == "", rel
