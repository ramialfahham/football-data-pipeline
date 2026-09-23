#!/usr/bin/env python
"""SessionStart guardrail — inject the project's handover from its GitLab issue.

On every session start, read the handover issue's description through the `glab` login already
on this machine and inject it, so a fresh agent continues from the documented state instead of
re-deriving it from an issue title or a memory file, which is how scoped work gets silently
re-scoped.

WHY AN ISSUE AND NOT A FILE IN THE REPO: a tracked file rides whichever branch is checked out,
so the handover a session saw depended on the branch it started on, and one committed on a
feature branch went stale as soon as a sibling branch merged. The issue has one current copy for
every branch and keeps its own history. It is kept closed so it never shows up as work.

When GitLab or `glab` cannot be reached, the last copy this hook fetched is injected from the
gitignored cache beside it, labelled with the time it was saved.

WHY THIS FILE LIVES HERE and not in `docs/portable_guardrails/hooks/`: that path is not a
PROTECTED prefix and has no entry in `review_routing.json`, so a script that auto-executes at
every session start would be editable inside any ordinary task. Anything that auto-launches a
command every session is guard-level, the same class as `.claude/commands/` and `.mcp.json`
(`docs/agent_guardrails.md`).

The read-in half of the handover loop, and the ONLY leg of it that actually runs. The other two,
a plan-back gate before the first code edit and a push reminder to update the handover, sit in
the never-installed global set (`docs/portable_guardrails/`), so do not rely on them.

Fails open on any error (no output, exit 0).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone

# The numeric project id, so a move of the project to another group or path does not break it.
PROJECT_ID = "85168767"
HANDOVER_ISSUE = "157"
CACHE_REL = os.path.join(".claude", "handover.cache.md")
FETCH_TIMEOUT_S = 15
# Keep the injection bounded. The unit is CHARACTERS: counting bytes instead labels a complete
# handover truncated whenever it carries enough multibyte symbols.
MAX_CHARS = 16000


def fetch() -> str | None:
    """The issue's description, or None when GitLab or glab cannot be reached."""
    glab = shutil.which("glab")
    if not glab:
        return None
    try:
        r = subprocess.run(
            [glab, "api", "projects/%s/issues/%s" % (PROJECT_ID, HANDOVER_ISSUE)],
            capture_output=True, timeout=FETCH_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    try:
        # Bytes decoded here: text mode reads glab's UTF-8 as cp1252 on a Windows console.
        body = json.loads(r.stdout.decode("utf-8")).get("description")
    except (ValueError, AttributeError):
        return None
    return body if isinstance(body, str) and body.strip() else None


def main() -> int:
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    try:
        # `CLAUDE_PROJECT_DIR` first, like every sibling hook's `_repo_root()`, so a session
        # started from a subdirectory finds the same cache.
        cwd = event.get("cwd") if isinstance(event, dict) else None
        root = os.environ.get("CLAUDE_PROJECT_DIR") or cwd or os.getcwd()
        cache = os.path.join(root, CACHE_REL)
        content, note = fetch(), ""
        if content is not None:
            # Write beside it and rename, so an interrupted write never leaves a half copy.
            tmp = cache + ".tmp"
            try:
                with open(tmp, "w", encoding="utf-8") as f:
                    f.write(content)
                os.replace(tmp, cache)
            except OSError:
                pass
        elif os.path.isfile(cache):
            with open(cache, encoding="utf-8") as f:
                saved_copy = f.read()
            if saved_copy.strip():
                content = saved_copy
                saved = datetime.fromtimestamp(os.path.getmtime(cache), timezone.utc)
                note = (" ⚠️ GitLab could not be reached, so this is the copy saved on this machine "
                        "at %s UTC; the issue may have moved on since." % saved.strftime("%Y-%m-%d %H:%M"))
        if content is None:
            msg = (
                "No handover could be read: GitLab issue #%s was unreachable and no copy is saved "
                "on this machine. If you are continuing prior work, ask the user for the current "
                "state BEFORE writing any code." % HANDOVER_ISSUE
            )
        else:
            truncated = len(content) > MAX_CHARS
            msg = (
                "ACTIVE WORK HANDOVER (GitLab issue #%s) — read this before doing anything else. "
                "Continue from this documented state. Do NOT re-scope, and do NOT infer the task "
                "from an issue title, a memory file, or your own judgement when this says "
                "otherwise. If you are about to write code on the work described below, first "
                "restate this spec back to the user and get approval.%s"
                "\n\n----- BEGIN HANDOVER -----\n" % (HANDOVER_ISSUE, note)
                + content[:MAX_CHARS]
                + "\n----- END HANDOVER -----"
            )
            if truncated:
                # Silent truncation is how a handover looks complete while its tail is missing.
                msg += (
                    "\n\n⚠️ TRUNCATED at %d characters — the handover is longer than the "
                    "injection budget, so everything after the cut is MISSING from this context. "
                    "Read the issue directly before acting, and cut it back under the budget at "
                    "the next handover." % MAX_CHARS
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
