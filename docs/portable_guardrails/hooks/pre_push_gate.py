#!/usr/bin/env python
"""PreToolUse(Bash) guardrail — pre-push checklist.

PORTABLE / generic: no project-specific paths. Self-gated to a real `git push`
(inspects the actual command, so `git log`, quoted echoes, etc. never trigger
it). Reminds the agent to run local validation before incurring a CI round trip,
and to confirm the push targets a feature branch rather than main/master.

Fails open on any error.
"""

from __future__ import annotations

import json
import re
import sys

_SEP = re.compile(r"\|\||&&|[;|\n]")
_PREFIX = re.compile(r"^(?:\w+=\S*\s+|sudo\s+|command\s+|nohup\s+|time\s+|env\s+)+")
_GIT_PUSH = re.compile(r"git\s+push\b")

MESSAGE = (
    "PRE-PUSH CHECK: "
    "(1) CI runs remotely and a red check means a fix-after-CI round trip — run this project's "
    "local validation first (linters, unit tests, build/parse, contract checks; e.g. a "
    "validate-local skill or the commands your CI workflow runs). "
    "(2) Confirm the push targets your feature branch, not main/master: check the refspec and the "
    "`-> <branch>` line in the push output. "
    "(3) Never force-push a shared branch."
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
    for part in _simple_commands(cmd):
        if _GIT_PUSH.match(part):
            try:
                print(json.dumps({
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "additionalContext": MESSAGE,
                    }
                }))
            except Exception:
                return 0
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
