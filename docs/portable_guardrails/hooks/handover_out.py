#!/usr/bin/env python
"""PreToolUse(Bash) guardrail — handover write-out reminder on push.

PORTABLE / generic. Self-gated to a real ``git push``. When a handover exists
(.claude/active_work.md), reminds the agent to update it to reflect the new state
(done / in-progress / next action) so the next session continues correctly.

Deliberately a reminder, not a hard block: this project's own guardrails note that
a hook which cries wolf gets ignored, and hard-blocking every code push is too
blunt. The hard enforcement lives in the read-in (handover_in.py) and the
plan-back gate (handover_plan_gate.py); this keeps the doc current.

Fails open on any error.
"""

from __future__ import annotations

import json
import os
import re
import sys

_SEP = re.compile(r"\|\||&&|[;|\n]")
_PREFIX = re.compile(r"^(?:\w+=\S*\s+|sudo\s+|command\s+|nohup\s+|time\s+|env\s+)+")
_GIT_PUSH = re.compile(r"git\s+push\b")
HANDOVER_REL = os.path.join(".claude", "active_work.md")

MESSAGE = (
    "HANDOVER WRITE-OUT: before you finish, update .claude/active_work.md so the next "
    "session can continue safely — set status (done / in-progress / next concrete action), "
    "record any decision locked this session, and keep the do-NOT list current. The next "
    "fresh chat will be handed exactly this file and nothing else."
)


def _simple_commands(command: str):
    for part in _SEP.split(command or ""):
        part = part.strip()
        if part:
            yield _PREFIX.sub("", part).strip()


def main() -> int:
    try:
        event = json.loads(sys.stdin.read() or "{}")
        cmd = (event.get("tool_input") or {}).get("command") or ""
    except Exception:
        return 0
    if not cmd:
        return 0
    try:
        root = event.get("cwd") or os.getcwd()
        if not os.path.isfile(os.path.join(root, HANDOVER_REL)):
            return 0  # no handover in this project → nothing to remind about
        for part in _simple_commands(cmd):
            if _GIT_PUSH.match(part):
                print(json.dumps({
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "additionalContext": MESSAGE,
                    }
                }))
                return 0
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
