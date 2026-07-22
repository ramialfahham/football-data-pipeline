#!/usr/bin/env python
"""SessionStart guardrail — inject the project's active-work handover.

On every session start, read `<project>/.claude/active_work.md` and inject it so
a fresh agent continues from the documented state instead of re-deriving it from
an issue title or a memory file, which is how scoped work gets silently
re-scoped. If the handover is missing, say so.

WHY THIS FILE LIVES HERE (2026-07-22). The wiring was first pointed at the copy
in `docs/portable_guardrails/hooks/`, and the cto-reviewer failed it: that path
is not a PROTECTED prefix and has no entry in `review_routing.json`, so a script
that auto-executes at every session start would have been editable inside any
ordinary task with no `protected_override`, no platform review and no opus
floor. That is the class the CPO ruled on for `.claude/commands/` (2026-06-14)
and `.mcp.json` (2026-06-18): anything that auto-launches a command every
session is guard-level, and an agent must never be able to self-grant it.
`docs/agent_guardrails.md` already said as much — project hooks live in
`.claude/hooks/`, and `docs/portable_guardrails/hooks/` is the copy-out archive
for other projects. The archive copy stays; this is the one that runs.

The read-in half of the handover loop, and as of 2026-07-22 the ONLY leg of it
that actually runs. The other two, a plan-back gate before the first code edit
and a push reminder to update the handover, sit in the never-installed global
set (`docs/portable_guardrails/`), so do not rely on them.

Fails open on any error (no output, exit 0).
"""

from __future__ import annotations

import json
import os
import sys

HANDOVER_REL = os.path.join(".claude", "active_work.md")
# Keep the injection bounded. `.claude/active_work.md` is required to stay under
# this — it was 112,233 characters until 2026-07-22, i.e. this hook would have
# delivered the first 14% and truncated in silence had it ever been wired.
#
# The unit is CHARACTERS, and that is stated here because it used to be both:
# the file was read with `f.read(MAX_CHARS)` on a text handle (characters) while
# truncation was decided by `os.path.getsize()` (bytes). Any handover under the
# character cap but over the byte cap — trivially reachable, this file is full of
# arrows and symbols — was injected complete AND labelled truncated, in the one
# hook that runs at every session start (cto-reviewer, 2026-07-22).
MAX_CHARS = 16000


def main() -> int:
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    try:
        # `CLAUDE_PROJECT_DIR` first, like every sibling hook's `_repo_root()`.
        # This one used `cwd` alone, so a session started from a subdirectory
        # reported "No .claude/active_work.md found" and invited writing a second
        # handover in the wrong place — in the one hook that runs at every
        # session start (cto-reviewer, 2026-07-22).
        root = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
        path = os.path.join(root, HANDOVER_REL)
        if os.path.isfile(path):
            # Read ONE past the cap so truncation is decided from what was
            # actually read, in the same unit, rather than from the file's size
            # on disk in a different one.
            with open(path, encoding="utf-8") as f:
                content = f.read(MAX_CHARS + 1)
            truncated = len(content) > MAX_CHARS
            content = content[:MAX_CHARS]
            msg = (
                "ACTIVE WORK HANDOVER (.claude/active_work.md) — read this before doing "
                "anything else. Continue from this documented state. Do NOT re-scope, "
                "and do NOT infer the task from an issue title, a memory file, or your "
                "own judgement when this says otherwise. If you are about to write code "
                "on the work described below, first restate this spec back to the user "
                "and get approval.\n\n----- BEGIN HANDOVER -----\n"
                + content
                + "\n----- END HANDOVER -----"
            )
            if truncated:
                # Silent truncation is how a handover looks complete while its
                # tail is missing. Say it out loud.
                msg += (
                    f"\n\n⚠️ TRUNCATED at {MAX_CHARS} characters — the handover is longer "
                    "than the injection budget, so everything after the cut is MISSING "
                    "from this context. Read the file directly before acting, and cut it "
                    "back under the budget as part of your next handover update."
                )
        else:
            msg = (
                "No .claude/active_work.md found in this project. If you are continuing "
                "prior work, ask the user for the current handover (or create "
                ".claude/active_work.md capturing it) BEFORE writing any code."
            )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": msg,
            }
        }))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
