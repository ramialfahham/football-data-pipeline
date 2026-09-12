#!/usr/bin/env python
"""Memory budget gate — adding a note to the agent's memory means removing one.

The memory folder (`~/.claude/projects/<slug>/memory/`) is the one surface with no owner and no
gate: its index `MEMORY.md` is loaded into every session, its notes are what the agent trusts
instead of re-reading the repo, and every session adds while nothing removes. Three budgets hold
it, one per surface, each PINNED TO WHAT THE FOLDER MEASURED after the cut that introduced them
(the same shape as the pinned count in `tests/test_no_decision_history_in_code.py`) and moving
down only:

  MAX_FILES        the number of notes — every `.md` in the folder other than `MEMORY.md`
  INDEX_MAX_CHARS  `MEMORY.md`, the one file every session pays for
  FILE_MAX_CHARS   any other note — the rule, why, and how to apply it

Denies an `Edit`, `Write` or `MultiEdit` whose target is a memory file when the RESULTING file
would exceed its surface's budget, or when a `Write` to a path that does not exist yet would
exceed the cap. The result is what the file WILL be — `Write`: the `content`; `Edit`: the file on
disk with `old_string` replaced by `new_string` (`replace_all` honoured); `MultiEdit`: the edits
applied in order — measured in CHARACTERS with `len()` after newline normalisation, never bytes.
A result no larger than the file on disk always passes, so an over-budget file can always be cut. Every other path returns 0
with no output; `NotebookEdit` writes `new_source`, which is never read here. Fails OPEN on any
unexpected error, like every hook in this directory.

`--report [folder]` prints the three measurements (default: this project's memory folder) and
exits 1 when any exceeds its budget — the number the evidence and the tests read.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _command_utils import emit_deny, read_event  # noqa: E402

MAX_FILES = 50
INDEX_MAX_CHARS = 7669
FILE_MAX_CHARS = 4232

INDEX_NAME = "MEMORY.md"

# Any project's memory folder, on any machine: the slug segment is whatever Claude Code derived
# from the project path. Matched on the normalised, forward-slash form of the path.
_MEMORY_PATH = re.compile(r"(?:^|/)\.claude/projects/[^/]+/memory/[^/]+\.md$")


def is_memory_path(file_path: str) -> bool:
    return bool(_MEMORY_PATH.search(os.path.normpath(file_path).replace("\\", "/")))


def note_count(folder: str) -> int:
    return sum(1 for f in os.listdir(folder) if f.endswith(".md") and f != INDEX_NAME)


def measure(folder: str) -> dict:
    """The three surfaces of one memory folder, in characters."""
    index_path = os.path.join(folder, INDEX_NAME)
    index_chars = _read_chars(index_path) if os.path.isfile(index_path) else 0
    largest, largest_name = 0, ""
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".md") or name == INDEX_NAME:
            continue
        n = _read_chars(os.path.join(folder, name))
        if n > largest:
            largest, largest_name = n, name
    return {
        "files": note_count(folder),
        "index_chars": index_chars,
        "largest_chars": largest,
        "largest_name": largest_name,
    }


def _read_text(path: str) -> str:
    # Universal newlines, so a CRLF file on disk measures the same as the `\n` text a tool writes.
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def _read_chars(path: str) -> int:
    return len(_read_text(path))


def resulting_text(tool_input: dict, current: str | None) -> str | None:
    """What the file will contain after this tool call, or None when it cannot be known."""
    if isinstance(tool_input.get("content"), str):
        return tool_input["content"]
    edits = tool_input.get("edits")
    if not isinstance(edits, list):
        if isinstance(tool_input.get("new_string"), str):
            edits = [tool_input]
        else:
            return None
    if current is None:
        return None
    text = current
    for edit in edits:
        if not isinstance(edit, dict):
            return None
        old, new = edit.get("old_string"), edit.get("new_string")
        if not isinstance(old, str) or not isinstance(new, str) or old not in text:
            return None
        text = text.replace(old, new) if edit.get("replace_all") else text.replace(old, new, 1)
    return text


def check(file_path: str, tool_input: dict) -> str | None:
    """The deny reason for this write, or None when it passes."""
    folder = os.path.dirname(os.path.abspath(file_path))
    name = os.path.basename(file_path)
    exists = os.path.isfile(file_path)
    current = _read_text(file_path) if exists else None
    result = resulting_text(tool_input, current)
    if result is None:
        return None
    is_index = name == INDEX_NAME
    if not exists and not is_index and os.path.isdir(folder):
        count = note_count(folder)
        if count >= MAX_FILES:
            return (
                f"MEMORY BUDGET GATE: the folder already holds {count} notes and the cap is "
                f"{MAX_FILES}. Adding a note means removing one — delete or merge an existing "
                "note first, then write this one."
            )
    budget = INDEX_MAX_CHARS if is_index else FILE_MAX_CHARS
    size = len(result)
    if size <= budget:
        return None
    if current is not None and size <= len(current):
        return None
    surface = "the index `MEMORY.md`" if is_index else f"the note `{name}`"
    return (
        f"MEMORY BUDGET GATE: this write would make {surface} {size:,} characters; its budget "
        f"is {budget:,}. A note is the rule, why, and how to apply it — cut this one to fit, "
        "or shorten another note and move the budget down with it. The budget never moves up."
    )


def _default_folder() -> str:
    project = os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    slug = re.sub(r"[^A-Za-z0-9]", "-", project)
    return os.path.join(os.path.expanduser("~"), ".claude", "projects", slug, "memory")


def report(folder: str) -> int:
    if not os.path.isdir(folder):
        print(f"no memory folder at {folder}")
        return 1
    m = measure(folder)
    over = (
        m["files"] > MAX_FILES
        or m["index_chars"] > INDEX_MAX_CHARS
        or m["largest_chars"] > FILE_MAX_CHARS
    )
    print(
        f"files {m['files']}/{MAX_FILES}, index {m['index_chars']}/{INDEX_MAX_CHARS}, "
        f"largest {m['largest_chars']}/{FILE_MAX_CHARS} ({m['largest_name']})"
        + ("  OVER BUDGET" if over else "")
    )
    return 1 if over else 0


def main() -> int:
    if "--report" in sys.argv:
        folder = next((a for a in sys.argv[1:] if a != "--report"), None) or _default_folder()
        return report(folder)
    event = read_event()
    try:
        tool_input = event.get("tool_input") or {}
        file_path = tool_input.get("file_path") or ""
        if not file_path or not is_memory_path(file_path):
            return 0
        reason = check(file_path, tool_input)
        if reason:
            emit_deny(reason)
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
