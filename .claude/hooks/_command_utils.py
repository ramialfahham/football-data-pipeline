"""Shared helpers for self-gating Bash hooks.

Self-gating means: the hook matcher is just "Bash" (fires on every Bash call),
and the *script* decides whether the command actually matches. This avoids the
fragile `if: Bash(pattern*)` matcher, which in practice fires on unrelated
read-only commands (e.g. `git log --grep=merge`, `cat`) — a cry-wolf failure
that trains the agent to ignore the guardrail.

Every hook that uses these helpers must fail OPEN: on any unexpected error,
return without blocking, so a hook bug never breaks the user's workflow.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# Shell operators that separate one simple-command from the next.
_SEP = re.compile(r"\|\||&&|[;|\n]")
# Leading noise to strip before reading the command's first real token:
# env assignments (FOO=bar), and common wrappers.
_PREFIX = re.compile(r"^(?:\w+=\S*\s+|sudo\s+|command\s+|nohup\s+|time\s+|env\s+)+")


def read_event() -> dict:
    """Read and parse the hook event JSON from stdin. {} on any failure."""
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception:
        return {}


def bash_command(event: dict) -> str:
    """Extract the Bash command string from a hook event, or ''."""
    try:
        return (event.get("tool_input") or {}).get("command") or ""
    except Exception:
        return ""


def simple_commands(command: str):
    """Yield each simple-command in a (possibly compound) shell command,
    with leading env-assignments / wrappers stripped, so callers can match
    against the actual invocation rather than substrings anywhere in the line."""
    for part in _SEP.split(command or ""):
        part = part.strip()
        if not part:
            continue
        yield _PREFIX.sub("", part).strip()


_HEREDOC_MARK = re.compile(r"<<-?\s*'?\"?\w+")
_QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")


def strip_quoted_and_heredoc(command: str) -> str:
    """Command text with quoted substrings removed and everything from the first
    heredoc marker truncated. Lets callers scan for shell OPERATORS (redirects,
    flags) without false-positives on quoted SQL ("x > 0.5"), commit-message
    bodies, or heredoc content."""
    try:
        cut = _HEREDOC_MARK.search(command or "")
        head = command[: cut.start()] if cut else (command or "")
        return _QUOTED.sub(" ", head)
    except Exception:
        return command or ""


def _git_location(folder: str) -> tuple[int, list[str]]:
    r = subprocess.run(
        ["git", "-C", folder, "rev-parse", "--git-common-dir", "--show-toplevel"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
    )
    return r.returncode, r.stdout.splitlines()


def _same_path(a: str, b: str) -> bool:
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def _same_repo(common: str, fallback: str) -> bool:
    code, theirs = _git_location(fallback)
    return code == 0 and bool(theirs) and _same_path(common, os.path.join(fallback, theirs[0]))


def worktree_root(target: str, fallback: str) -> str | None:
    """Root of the worktree of `fallback`'s repository that holds `target`, a file or folder
    that need not exist yet.

    A nested foreign repository is judged by the worktree that holds it, so creating one never
    exempts a path. Any other target is judged by `fallback` when it lies inside it; outside it,
    None: this repo's hooks have nothing to judge there. The root is spelled like `target`, so a
    relpath from it stays inside.
    """
    folder = os.path.abspath(target)
    while not os.path.isdir(folder):
        parent = os.path.dirname(folder)
        if parent == folder:
            return None
        folder = parent
    try:
        while True:
            code, lines = _git_location(folder)
            if code != 0 or len(lines) < 2:
                break
            root = next((d for d in _ancestors(folder) if _same_path(d, lines[1])), None)
            if root is None:
                return fallback
            if _same_path(root, fallback) or _same_repo(os.path.join(folder, lines[0]), fallback):
                return root
            if os.path.dirname(root) == root:
                break
            folder = os.path.dirname(root)
    except (OSError, subprocess.SubprocessError, ValueError):
        return fallback
    return fallback if any(_same_path(d, fallback) for d in _ancestors(folder)) else None


def _ancestors(folder: str):
    while True:
        yield folder
        parent = os.path.dirname(folder)
        if parent == folder:
            return
        folder = parent


def cwd_root(event: dict, fallback: str) -> str:
    """Root of the worktree the event's working directory is in, else `fallback`."""
    cwd = event.get("cwd")
    if isinstance(cwd, str) and cwd:
        return worktree_root(cwd, fallback) or fallback
    return fallback


def emit_context(event_name: str, text: str) -> None:
    """Inject additional context for the model (non-blocking)."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": text,
        }
    }))


def emit_deny(reason: str) -> None:
    """Deny a PreToolUse tool call with a reason shown to the model."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
