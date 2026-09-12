#!/usr/bin/env python
"""Tracker-snapshot gate — the tracker's backup in the repo has exactly one writer.

`docs/tracker/` holds `gitlab_snapshot.md`, a generated copy of every GitLab milestone and
issue, written only by `scripts/snapshot_tracker.py` and read only when GitLab is unreachable.
A backup that anyone can edit becomes a second roadmap, so this hook denies every `Edit`,
`Write` and `MultiEdit` whose target is inside `docs/tracker/` in this repo. The script writes
with Python's own file write, which no edit-time hook sees — that is the one door, and
`tests/test_tracker_snapshot.py` checks the header checksum so a change that did not also
rewrite the header fails CI. A deliberate shell write that recomputes the header is not caught
by either half; it is forbidden by rule, like `--no-verify`. Every other path returns 0 with no
output. Fails OPEN on any unexpected error, like
every hook in this directory.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _command_utils import emit_deny, read_event  # noqa: E402

GOVERNED = "docs/tracker/"


def _repo_root() -> str:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return os.path.abspath(env)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def is_governed(file_path: str) -> bool:
    try:
        rel = os.path.relpath(os.path.abspath(file_path), _repo_root())
    except ValueError:
        return False
    # Case-folded: on Windows `Docs/Tracker/` is the same folder, and relpath keeps the caller's
    # spelling of the segments past the shared prefix.
    return rel.replace("\\", "/").lower().startswith(GOVERNED)


def main() -> int:
    event = read_event()
    try:
        tool_input = event.get("tool_input") or {}
        file_path = tool_input.get("file_path") or ""
        if not file_path or not is_governed(file_path):
            return 0
        emit_deny(
            f"TRACKER SNAPSHOT GATE: `{GOVERNED}` is the generated backup of the GitLab tracker "
            "and has one writer, `scripts/snapshot_tracker.py`. It is never edited by hand and "
            "never cited while GitLab is up — the GitLab issue is the source. To refresh it, run "
            "`python scripts/snapshot_tracker.py`."
        )
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
