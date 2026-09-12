"""Adding a note to the agent's memory means removing one — the guard, both halves.

The hook `.claude/hooks/memory_budget_gate.py` denies an `Edit`, `Write` or `MultiEdit` to a
memory file when the RESULTING file would exceed its surface's budget, or when a new note would
exceed the file cap. The three budgets are pinned to what the real folder measured after the cut
that introduced them; a sweep may lower them, nothing else moves them.

Every test drives the hook as a subprocess on a temp folder of the real shape
(`<tmp>/.claude/projects/<slug>/memory/`), so the path test, the size arithmetic and the deny
text are exercised exactly as the harness exercises them. Each deny case has a passing twin one
character inside the budget: a one-sided test passes while broken.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
HOOKS = os.path.join(REPO, ".claude", "hooks")
sys.path.insert(0, HOOKS)
import memory_budget_gate as gate  # noqa: E402

HOOK = os.path.join(HOOKS, "memory_budget_gate.py")


def _run(event, cwd: str) -> str:
    r = subprocess.run(
        [sys.executable, HOOK],
        input=event if isinstance(event, str) else json.dumps(event),
        capture_output=True, text=True, cwd=cwd, timeout=60,
    )
    assert r.returncode == 0, r.stderr
    return r.stdout


def _denied(out: str) -> bool:
    return '"permissionDecision": "deny"' in out


def _reason(out: str) -> str:
    return json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]


def _write_event(path: str, content: str) -> dict:
    return {"hook_event_name": "PreToolUse", "tool_name": "Write",
            "tool_input": {"file_path": path, "content": content}}


def _edit_event(path: str, old: str, new: str, replace_all: bool = False) -> dict:
    return {"hook_event_name": "PreToolUse", "tool_name": "Edit",
            "tool_input": {"file_path": path, "old_string": old, "new_string": new,
                           "replace_all": replace_all}}


def _multi_event(path: str, edits: list[dict]) -> dict:
    return {"hook_event_name": "PreToolUse", "tool_name": "MultiEdit",
            "tool_input": {"file_path": path, "edits": edits}}


@pytest.fixture
def memory(tmp_path):
    folder = tmp_path / ".claude" / "projects" / "X--Projects-some-repo" / "memory"
    folder.mkdir(parents=True)
    (folder / gate.INDEX_NAME).write_text("# Memory index\n", encoding="utf-8")
    return folder


def _fill(folder, n: int) -> None:
    for i in range(n):
        (folder / f"feedback_note_{i:03d}.md").write_text(f"note {i}\n", encoding="utf-8")


# ---------------------------------------------------------------- the path test

def test_a_memory_path_is_recognised_on_both_slash_styles(memory):
    assert gate.is_memory_path(str(memory / "feedback_x.md"))
    assert gate.is_memory_path(str(memory / "feedback_x.md").replace("\\", "/"))
    assert gate.is_memory_path("C:\\Users\\u\\.claude\\projects\\D--P\\memory\\MEMORY.md")


@pytest.mark.parametrize("path", [
    "D:/Projects/repo/docs/notes.md",
    "D:/Projects/repo/.claude/task/contract.md",
    "C:/Users/u/.claude/plans/some-plan.md",
    "C:/Users/u/.claude/projects/D--P/memory/sub/deeper.md",
    "C:/Users/u/.claude/projects/D--P/memory/notes.txt",
])
def test_every_other_path_is_ignored(path, tmp_path):
    assert not gate.is_memory_path(path)
    out = _run(_write_event(path, "x" * (gate.FILE_MAX_CHARS + 1)), str(tmp_path))
    assert out == ""


# ---------------------------------------------------------------- a note's size

def test_write_within_budget_passes_and_one_over_is_denied(memory):
    path = str(memory / "feedback_new.md")
    assert _run(_write_event(path, "x" * gate.FILE_MAX_CHARS), str(memory)) == ""
    out = _run(_write_event(path, "x" * (gate.FILE_MAX_CHARS + 1)), str(memory))
    assert _denied(out)
    reason = _reason(out)
    assert "feedback_new.md" in reason
    assert f"{gate.FILE_MAX_CHARS + 1:,}" in reason and f"{gate.FILE_MAX_CHARS:,}" in reason


def test_edit_is_measured_on_the_resulting_file(memory):
    path = memory / "feedback_e.md"
    path.write_text("head\n" + "x" * (gate.FILE_MAX_CHARS - 10), encoding="utf-8")
    assert _run(_edit_event(str(path), "head", "head" + "y" * 5), str(memory)) == ""
    out = _run(_edit_event(str(path), "head", "head" + "y" * 6), str(memory))
    assert _denied(out)


def test_replace_all_counts_every_occurrence(memory):
    path = memory / "feedback_r.md"
    path.write_text("ab ab ab\n" + "x" * (gate.FILE_MAX_CHARS - 12), encoding="utf-8")
    assert _run(_edit_event(str(path), "ab", "abc"), str(memory)) == ""
    assert _denied(_run(_edit_event(str(path), "ab", "abcd", replace_all=True), str(memory)))


def test_multiedit_applies_the_edits_in_order(memory):
    path = memory / "feedback_m.md"
    path.write_text("one two\n" + "x" * (gate.FILE_MAX_CHARS - 10), encoding="utf-8")
    fits = [{"old_string": "one", "new_string": "one1"},
            {"old_string": "one1 two", "new_string": "one1 two2"}]
    assert _run(_multi_event(str(path), fits), str(memory)) == ""
    over = fits + [{"old_string": "two2", "new_string": "two2" + "z" * 3}]
    assert _denied(_run(_multi_event(str(path), over), str(memory)))


def test_shrinking_an_over_budget_note_always_passes(memory):
    path = memory / "feedback_big.md"
    path.write_text("x" * (gate.FILE_MAX_CHARS + 500), encoding="utf-8")
    assert _run(_write_event(str(path), "x" * (gate.FILE_MAX_CHARS + 499)), str(memory)) == ""
    assert _run(_edit_event(str(path), "x" * 10, "x" * 9), str(memory)) == ""
    assert _denied(_run(_write_event(str(path), "x" * (gate.FILE_MAX_CHARS + 501)), str(memory)))


def test_an_edit_that_cannot_apply_is_left_to_the_tool(memory):
    path = memory / "feedback_n.md"
    path.write_text("abc\n", encoding="utf-8")
    assert _run(_edit_event(str(path), "zzz", "y" * (gate.FILE_MAX_CHARS + 1)), str(memory)) == ""


# ---------------------------------------------------------------- the index

def test_the_index_has_its_own_budget(memory):
    path = str(memory / gate.INDEX_NAME)
    assert _run(_write_event(path, "x" * gate.INDEX_MAX_CHARS), str(memory)) == ""
    out = _run(_write_event(path, "x" * (gate.INDEX_MAX_CHARS + 1)), str(memory))
    assert _denied(out)
    assert "MEMORY.md" in _reason(out) and f"{gate.INDEX_MAX_CHARS:,}" in _reason(out)


def test_the_index_never_counts_as_a_note(memory):
    _fill(memory, gate.MAX_FILES)
    assert gate.note_count(str(memory)) == gate.MAX_FILES
    assert _run(_write_event(str(memory / gate.INDEX_NAME), "# rebuilt\n"), str(memory)) == ""


# ---------------------------------------------------------------- the file cap

def test_a_new_note_at_the_cap_is_denied_until_one_is_removed(memory):
    _fill(memory, gate.MAX_FILES)
    new = str(memory / "feedback_one_more.md")
    out = _run(_write_event(new, "small\n"), str(memory))
    assert _denied(out)
    assert f"{gate.MAX_FILES}" in _reason(out) and "removing one" in _reason(out)
    os.remove(memory / "feedback_note_000.md")
    assert _run(_write_event(new, "small\n"), str(memory)) == ""


def test_editing_an_existing_note_at_the_cap_passes(memory):
    _fill(memory, gate.MAX_FILES)
    existing = str(memory / "feedback_note_001.md")
    assert _run(_write_event(existing, "rewritten\n"), str(memory)) == ""
    assert _run(_edit_event(existing, "note 1", "note one"), str(memory)) == ""


def test_one_below_the_cap_admits_exactly_one(memory):
    _fill(memory, gate.MAX_FILES - 1)
    assert _run(_write_event(str(memory / "feedback_a.md"), "a\n"), str(memory)) == ""
    (memory / "feedback_a.md").write_text("a\n", encoding="utf-8")
    assert _denied(_run(_write_event(str(memory / "feedback_b.md"), "b\n"), str(memory)))


# ---------------------------------------------------------------- fail open, report

@pytest.mark.parametrize("junk", ["", "not json", "null", "[]", '{"tool_name": 5}',
                                  '{"tool_input": {"file_path": 3}}'])
def test_malformed_input_fails_open(junk, tmp_path):
    assert _run(junk, str(tmp_path)) == ""


def test_report_prints_the_three_measurements(memory):
    _fill(memory, 3)
    (memory / "feedback_note_000.md").write_text("x" * 40, encoding="utf-8")
    r = subprocess.run([sys.executable, HOOK, "--report", str(memory)],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0
    assert r.stdout.strip() == (
        f"files 3/{gate.MAX_FILES}, index 15/{gate.INDEX_MAX_CHARS}, "
        f"largest 40/{gate.FILE_MAX_CHARS} (feedback_note_000.md)"
    )


def test_report_exits_nonzero_over_budget(memory):
    (memory / "feedback_huge.md").write_text("x" * (gate.FILE_MAX_CHARS + 1), encoding="utf-8")
    r = subprocess.run([sys.executable, HOOK, "--report", str(memory)],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 1 and "OVER BUDGET" in r.stdout


def test_the_hook_is_wired_for_every_file_writing_tool():
    with open(os.path.join(REPO, ".claude", "settings.json"), encoding="utf-8") as f:
        settings = json.load(f)
    groups = [g for g in settings["hooks"]["PreToolUse"]
              if any("memory_budget_gate.py" in h["command"] for h in g["hooks"])]
    assert len(groups) == 1
    assert set(groups[0]["matcher"].split("|")) >= {"Edit", "Write", "MultiEdit"}


def test_budgets_only_ever_move_down():
    """The pin: these numbers are what the folder measured; a sweep lowers them, nothing raises
    them. Raising one here is the same act as raising the comment guard's pinned count. Three
    assertions, not one tuple comparison — a tuple compares lexicographically and stops at the
    first field that differs, so a lowered first budget would hide a raised third."""
    assert gate.MAX_FILES <= 50
    assert gate.INDEX_MAX_CHARS <= 7669
    assert gate.FILE_MAX_CHARS <= 4232


def test_a_crlf_file_measures_like_the_lf_text_a_tool_writes(memory):
    """Written as BYTES so the case exists on every platform: the note is FILE_MAX_CHARS long
    after newline normalisation and over it in raw bytes. Read raw, the hook would deny the
    no-op Edit below; read with universal newlines, it passes."""
    path = memory / "feedback_crlf.md"
    body = "x" * 9 + "\r\n"
    path.write_bytes((body * (gate.FILE_MAX_CHARS // 10)).encode("utf-8")
                     + b"y" * (gate.FILE_MAX_CHARS % 10))
    assert gate.measure(str(memory))["largest_chars"] == gate.FILE_MAX_CHARS
    assert _run(_edit_event(str(path), "x" * 9, "x" * 8 + "z"), str(memory)) == ""
    assert _denied(_run(_edit_event(str(path), "x" * 9, "x" * 10), str(memory)))


def test_report_on_a_missing_folder_says_so_without_a_traceback(tmp_path):
    r = subprocess.run([sys.executable, HOOK, "--report", str(tmp_path / "nowhere")],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 1
    assert "no memory folder" in r.stdout and "Traceback" not in r.stderr
