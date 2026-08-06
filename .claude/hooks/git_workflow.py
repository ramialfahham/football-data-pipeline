#!/usr/bin/env python
"""PostToolUse(Bash) guardrail — finish the branch workflow after a commit.

Self-gated to a real `git commit` (not `git log`, not a quoted echo). Reminds
the agent to complete steps 3-4 of the working agreement: push with an explicit
refspec, then open the PR. Fails open.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _command_utils import (  # noqa: E402
    bash_command,
    emit_context,
    read_event,
    simple_commands,
)

_GIT_COMMIT = re.compile(r"git\s+commit\b")


def main() -> int:
    cmd = bash_command(read_event())
    if not cmd:
        return 0
    for part in simple_commands(cmd):
        if _GIT_COMMIT.match(part) and "--dry-run" not in part:
            emit_context(
                "PostToolUse",
                "WORKFLOW GATE: commit made. Per docs/working_agreement.md §3, the task is not "
                "done until: (3) you push with an explicit refspec — `git push gitlab "
                "<branch>:<branch>` — and verify the output says `-> <branch>` (NOT `-> main`); "
                "(4) you open the MR with `glab mr create`. Do not report the task complete until "
                "the MR URL is returned. (If a post-commit git hook already auto-pushed and "
                "opened the MR, just confirm the MR URL.)",
            )
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
