"""A document sentence stays within the ASD-STE100 limit — the guard, both halves.

Half one is the edit-time hook `.claude/hooks/sentence_length_gate.py`: it refuses an `Edit`,
`Write` or `MultiEdit` that adds a Markdown sentence over 25 words, or over 20 in a numbered step.
Half two is the pin below: each document's count of long sentences, which may only move down.

Everything imports the hook's definitions, so the CI count and the edit-time refusal cannot drift.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
HOOKS = os.path.join(REPO, ".claude", "hooks")
sys.path.insert(0, HOOKS)
import sentence_length_gate as gate  # noqa: E402

# The pin: long sentences per document. A cleanup lowers a number or removes a row; nothing adds one.
PINNED = {
    ".claude/agents/analytics-engineer-reviewer.md": 5,
    ".claude/agents/bi-analyst-reviewer.md": 16,
    ".claude/agents/cto-reviewer.md": 20,
    ".claude/agents/data-engineer-reviewer.md": 7,
    ".claude/agents/football-analytics-expert-reviewer.md": 5,
    ".claude/agents/platform-reviewer.md": 10,
    ".claude/agents/scope-auditor.md": 10,
    ".claude/agents/seo-expert-reviewer.md": 14,
    ".claude/skills/onboard-competition/SKILL.md": 10,
    ".claude/skills/onboard-endpoint/SKILL.md": 9,
    ".claude/skills/validate-local/SKILL.md": 7,
    ".claude/skills/verify-competition-ingest/SKILL.md": 4,
    ".github/workflows/README.md": 12,
    "AGENTS.md": 2,
    "CLAUDE.md": 27,
    "README.md": 9,
    "dbt_project/docs/engineering_standards.md": 34,
    "dbt_project/docs/layering.md": 44,
    "dbt_project/models/1_staging/api_football/README.md": 1,
    "dbt_project/models/docs/cleaning_rules.md": 5,
    "dbt_project/models/docs/metric_columns.md": 37,
    "dbt_project/models/docs/metric_rules.md": 2,
    "dbt_project/models/docs/shared_columns.md": 35,
    "deploy/nightly/README.md": 19,
    "design-mocks/README.md": 15,
    "docs/data_contract.md": 31,
    "docs/operations_guide.md": 19,
    "docs/roles/analytics_engineer.md": 5,
    "docs/roles/bi_analyst.md": 5,
    "docs/roles/cfo.md": 3,
    "docs/roles/cto.md": 4,
    "docs/roles/data_engineer.md": 2,
    "docs/roles/data_journalist.md": 5,
    "docs/roles/football_analytics_expert.md": 1,
    "docs/roles/legal_counsel.md": 5,
    "docs/roles/platform_reliability.md": 9,
    "docs/roles/product_analyst.md": 4,
    "docs/roles/seo_expert.md": 11,
    "docs/roles/ui_expert.md": 1,
    "docs/wireframes/00_overview.md": 13,
    "docs/wireframes/01_fixture_page.md": 4,
    "docs/wireframes/02_team_profile.md": 3,
    "docs/wireframes/03_player_profile.md": 3,
    "docs/wireframes/08_browse.md": 11,
    "docs/wireframes/09_chrome.md": 8,
    "docs/wireframes/10_home.md": 128,
    "docs/wireframes/11_team_squad.md": 7,
    "docs/wireframes/12_player_stats.md": 16,
    "docs/wireframes/13_player_career.md": 7,
    "docs/wireframes/14_team_stats.md": 19,
    "docs/wireframes/99_gaps_register.md": 66,
    "docs/wireframes/block_standard.md": 11,
    "docs/wireframes/metrics_display.md": 30,
    "site_v2/src/data/README.md": 24,
}


def words(n: int) -> str:
    return " ".join(["word"] * n) + "."


def _tracked_docs() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z", "*.md"], cwd=REPO, capture_output=True, check=True)
    return [p for p in out.stdout.decode("utf-8").split("\0") if p]


def run_hook(root: str, tool_input: dict, tool: str = "Edit") -> str:
    event = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input}
    env = dict(os.environ, CLAUDE_PROJECT_DIR=root)
    proc = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "sentence_length_gate.py")],
        input=json.dumps(event), capture_output=True, text=True, env=env, timeout=60, check=False,
    )
    return proc.stdout


def denied(out: str) -> bool:
    return '"permissionDecision": "deny"' in out


def doc_in(tmp_path, rel: str, text: str, newline: str = "\n") -> str:
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\n", newline).encode("utf-8"))
    return str(path)


# --- the pin -----------------------------------------------------------------------------------

def test_every_document_matches_the_pin_in_both_directions():
    counts = gate.count_docs(REPO, _tracked_docs())
    grown = {p: n for p, n in counts.items() if n > PINNED.get(p, 0)}
    assert not grown, (
        f"documents gained long sentences: {grown}. A description sentence has at most 25 words "
        "and a numbered step at most 20 (working_agreement.md section 9). Split them."
    )
    shrunk = {p: (PINNED[p], counts.get(p, 0)) for p in PINNED if counts.get(p, 0) < PINNED[p]}
    assert not shrunk, (
        f"documents lost long sentences (pinned, now): {shrunk}. Lower their numbers in PINNED "
        "(remove a row at zero) so the cleanup is recorded; the pin only moves down"
    )


# --- what counts --------------------------------------------------------------------------------

def test_the_limits_are_25_for_a_description_and_20_for_a_numbered_step():
    assert gate.long_sentences(words(25)) == []
    assert [n for _l, n, _s in gate.long_sentences(words(26))] == [26]
    assert gate.long_sentences("1. " + words(20)) == []
    assert [(lim, n) for lim, n, _s in gate.long_sentences("1. " + words(21))] == [(20, 21)]
    assert gate.long_sentences("- " + words(25)) == []


def test_a_paragraph_after_a_numbered_step_is_a_description_again():
    assert gate.long_sentences("1. " + words(5) + "\n\n" + words(24)) == []


def test_sentences_end_at_a_full_stop_a_question_mark_or_a_semicolon():
    assert gate.long_sentences(words(15) + " " + words(15)) == []
    assert gate.long_sentences(" ".join(["word"] * 15) + "; " + words(15)) == []
    assert gate.long_sentences(" ".join(["word"] * 15) + "? " + words(15)) == []


def test_a_code_span_is_one_word_and_a_link_counts_its_text():
    span = "`" + " ".join(["x"] * 40) + "`"
    assert gate.long_sentences(span + " " + words(24)) == []
    link = "[two words](https://example.org/" + "a/" * 30 + ")"
    assert gate.long_sentences(link + " " + words(23)) == []


def test_headings_code_blocks_comments_and_front_matter_are_not_prose():
    long = " ".join(["word"] * 40)
    text = f"---\ntitle: {long}\n---\n# {long}\n```\n{long}\n```\n<!-- {long} -->\n"
    assert gate.long_sentences(text) == []


def test_a_table_cell_is_prose_and_the_rule_row_is_not():
    table = "| a | b |\n|---|---|\n| " + words(26) + " | short |\n"
    assert [n for _l, n, _s in gate.long_sentences(table)] == [26]


# --- the hook -----------------------------------------------------------------------------------

def test_hook_refuses_an_added_long_sentence(tmp_path):
    path = doc_in(tmp_path, "docs/a.md", "Intro.\n")
    out = run_hook(str(tmp_path), {"file_path": path, "old_string": "Intro.", "new_string": words(26)})
    assert denied(out)
    assert "26 words" in out


def test_hook_allows_a_short_sentence_and_keeps_an_existing_long_one(tmp_path):
    path = doc_in(tmp_path, "docs/a.md", words(30) + "\n\nIntro.\n")
    out = run_hook(str(tmp_path), {"file_path": path, "old_string": "Intro.", "new_string": words(10)})
    assert out.strip() == ""


def test_hook_refuses_a_changed_long_sentence(tmp_path):
    path = doc_in(tmp_path, "docs/a.md", words(30) + "\n")
    out = run_hook(str(tmp_path), {"file_path": path, "old_string": "word.", "new_string": "words."})
    assert denied(out)


def test_hook_applies_an_edit_to_a_crlf_document(tmp_path):
    path = doc_in(tmp_path, "docs/a.md", "Intro.\nMore.\n", newline="\r\n")
    out = run_hook(str(tmp_path), {"file_path": path, "old_string": "Intro.\nMore.", "new_string": words(26)})
    assert denied(out)


def test_hook_refuses_a_write_of_a_new_document_with_a_long_sentence(tmp_path):
    path = str(tmp_path / "docs" / "new.md")
    out = run_hook(str(tmp_path), {"file_path": path, "content": words(26) + "\n"}, tool="Write")
    assert denied(out)


def test_hook_checks_every_edit_of_a_multiedit(tmp_path):
    path = doc_in(tmp_path, "docs/a.md", "One.\nTwo.\n")
    edits = [{"old_string": "One.", "new_string": "Uno."}, {"old_string": "Two.", "new_string": words(26)}]
    out = run_hook(str(tmp_path), {"file_path": path, "edits": edits}, tool="MultiEdit")
    assert denied(out)


def test_hook_ignores_code_files_and_exempt_documents(tmp_path):
    for rel in ("scripts/a.py", ".claude/task/contract.md", "docs/tracker/snapshot.md"):
        path = doc_in(tmp_path, rel, "Intro.\n")
        out = run_hook(str(tmp_path), {"file_path": path, "old_string": "Intro.", "new_string": words(30)})
        assert out.strip() == "", rel


def test_hook_ignores_a_document_outside_the_repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    path = doc_in(tmp_path, "memory/note.md", "Intro.\n")
    out = run_hook(str(root), {"file_path": path, "old_string": "Intro.", "new_string": words(30)})
    assert out.strip() == ""


def test_the_hook_is_wired_beside_the_other_edit_time_gates():
    with open(os.path.join(REPO, ".claude", "settings.json"), encoding="utf-8") as f:
        settings = json.load(f)
    groups = [g for g in settings["hooks"]["PreToolUse"]
              if any("sentence_length_gate.py" in h["command"] for h in g["hooks"])]
    assert len(groups) == 1
    assert set(groups[0]["matcher"].split("|")) >= {"Edit", "Write", "MultiEdit"}


def test_hook_fails_open_on_an_unreadable_event():
    proc = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "sentence_length_gate.py")],
        input="not json", capture_output=True, text=True, timeout=60, check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""
