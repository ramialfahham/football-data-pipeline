#!/usr/bin/env python
"""Context guard — hands a session off to a fresh one before its context grows too large.

Every step re-reads the whole context, so a long session spends the plan on re-reading. When the
agent tries to end its turn this reads the size of the context from the session's own transcript
and, past CONTEXT_TOKEN_THRESHOLD, blocks the turn end ONCE per session with a hand-off
instruction. After that it never blocks that session again.

The size is the last assistant message's `usage`: input_tokens + cache_creation_input_tokens +
cache_read_input_tokens. Entries of other types, sidechain entries, synthetic messages and
messages whose usage sums to zero are skipped, so the last real model call counts.

The marker that records the one block is a file per session id in the system temp folder, created
with exclusive create BEFORE the block is printed: two hooks racing, or a marker that cannot be
written, never produce a second block. Fails OPEN: a missing session id, a missing or unreadable
transcript, no usable usage, or any error ends the turn without a block.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _command_utils import read_event  # noqa: E402

CONTEXT_TOKEN_THRESHOLD = 300_000

_USAGE_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
_FIRST_READ_BYTES = 512 * 1024
_UNSAFE_ID = re.compile(r"[^A-Za-z0-9._-]")


def _int_or_none(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _context_tokens(line: str) -> int | None:
    """The context size a transcript line reports, or None when the line is not a usable assistant entry."""
    try:
        entry = json.loads(line)
    except ValueError:
        return None
    if not isinstance(entry, dict) or entry.get("type") != "assistant" or entry.get("isSidechain") is True:
        return None
    message = entry.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant" or message.get("model") == "<synthetic>":
        return None
    usage = message.get("usage")
    if not isinstance(usage, dict):
        return None
    total = 0
    for key in _USAGE_KEYS:
        raw = usage.get(key)
        if raw is None:
            continue
        number = _int_or_none(raw)
        if number is None:
            return None
        total += number
    return total or None


def _last_context_tokens(path: str) -> int | None:
    """Context size from the last usable assistant entry, reading the file from its tail."""
    size = os.path.getsize(path)
    window = _FIRST_READ_BYTES
    while True:
        start = max(0, size - window)
        with open(path, "rb") as handle:
            handle.seek(start)
            chunk = handle.read()
        lines = chunk.decode("utf-8", "replace").splitlines()
        if start > 0 and lines:
            lines = lines[1:]
        for line in reversed(lines):
            tokens = _context_tokens(line)
            if tokens is not None:
                return tokens
        if start == 0:
            return None
        window *= 4


def _marker_path(session_id: str) -> str:
    return os.path.join(tempfile.gettempdir(), "claude_context_guard", _UNSAFE_ID.sub("_", session_id))


def _claim_marker(session_id: str) -> bool:
    """True only for the one caller that creates the marker; False when it exists or cannot be made."""
    path = _marker_path(session_id)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except OSError:
        return False
    return True


def _reason(tokens: int) -> str:
    return (
        f"CONTEXT GUARD: this session's context is {tokens:,} tokens, past the {CONTEXT_TOKEN_THRESHOLD:,} "
        "limit. Every step re-reads all of it, so hand off to a fresh session now. "
        "1. Finish or abandon the step in hand; do not start a new one. Make no edit to the tree "
        "except the state file: the stop gate does not run again on this turn end. "
        "2. Write a state file: to the shared notes folder you were given, else to your task folder "
        "(.claude/task/<issue>-<slug>/). It holds what is done, what is open, the branch, the review "
        "round and verdicts, the rulings received, and the next steps. "
        "3. Send the coordinator one message saying you handed off, with the state file path. "
        "4. Stop. This guard blocks once per session and does not block again."
    )


def main() -> int:
    event = read_event()
    if event.get("stop_hook_active"):
        return 0
    try:
        session_id = event.get("session_id")
        transcript = event.get("transcript_path")
        if not isinstance(session_id, str) or not session_id or not isinstance(transcript, str) or not transcript:
            return 0
        tokens = _last_context_tokens(transcript)
        if tokens is None or tokens <= CONTEXT_TOKEN_THRESHOLD:
            return 0
        if not _claim_marker(session_id):
            return 0
        print(json.dumps({"decision": "block", "reason": _reason(tokens)}))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
