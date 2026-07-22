#!/usr/bin/env python
"""Stop gate — plain language, enforced.

The CPO has asked for plain language repeatedly. It stayed a habit, and habits
here have a shelf life of about one session: the 2026-07-22 retrospective broke
the rule *while explaining why written rules do not change behaviour* — file
paths, section numbers and invented vocabulary throughout. A rule nothing checks
is a wish.

WHAT THIS CAN AND CANNOT DO (be honest about it). Stop fires AFTER the message
is committed and rendered, which is exactly why the hook has to go to the
transcript to find it. So it does NOT prevent a wall of text: the CPO reads the
wall, then reads the rewrite. On the check most likely to fire it doubles the
messages in that turn rather than halving them.

It was kept anyway, deliberately and provisionally (CPO, 2026-07-22, asked
directly and answering "yes" to keeping all four checks). The argument is that
the cost is front-loaded: a gate that works fires a few times and then stops,
because the behaviour changes. If it is still firing regularly after a handful
of turns it is NOT working, and the answer is to remove it, not to tune it
forever. That is a testable claim, which the alternatives were not.

Four checks, each one traceable to something he actually said:

  - em dashes            -> "Never use em dashes." Stated as an absolute.
  - section symbols (§)  -> jargon; he does not read the working agreement.
  - repo file paths      -> "no file paths or ticket numbers in chat unless
                            asked" (escalated 2026-07-21).
  - length               -> "Short answers. No walls of text, no books."

The 2,500-character cap is MEASURED, not guessed. Across the 35 messages of the
session that produced this hook the median was 166 characters, but the top 30%
ran 1,682 to 3,343 and four exceeded 3,000. Those four are the walls he objected
to. Change the constant if it proves wrong; do not delete the check.

Code fences and inline backticks are stripped before the path and symbol checks
run, so quoting a path as code is fine. Prose is what is policed.

Fails OPEN on any error (house rule, `_command_utils.py`): a hook bug must never
wedge the end of a turn.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _command_utils import read_event  # noqa: E402

MAX_CHARS = 2500
# Enough tail to hold the last few records of any turn without parsing a whole
# session. A single record is rarely over ~100 KB.
TAIL_BYTES = 512 * 1024

# Fenced blocks first, then inline spans, then markdown link targets — none of
# these are prose and none of them are what the CPO objected to.
_FENCE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`\n]*`")
_LINK_TARGET = re.compile(r"\]\([^)]*\)")

_EM_DASH = "—"
_SECTION = "§"

# A repo-relative path in prose: at least one directory segment, then a file
# extension we actually use. Deliberately narrow — "3 of 5" and "v2" must not
# trip it, and a false positive that blocks a good answer trains the agent to
# resent the guard (the cry-wolf failure named in `_command_utils.py`).
# The negative lookbehind keeps URLs out: citing api-sports.io/docs/v3.json is a
# source, not a repo path, and blocking a turn over it is the cry-wolf failure.
_REPO_PATH = re.compile(
    r"(?<!//)(?<![\w.:-])[\w.-]+(?:/[\w.-]+)+\.(?:py|sql|ya?ml|md|json|csv|astro|ts|js|css|toml|cfg)\b"
)
_URL = re.compile(r"\bhttps?://\S+|\b[\w-]+\.(?:com|org|net|io|dev|ai|co\.uk)/\S*")


def _transcript_path(event: dict) -> str | None:
    """The transcript for this session, found by session id rather than guessed.

    `transcript_path` is in the documented common payload, but its presence on
    Stop specifically is NOT documented, so it is used when offered and located
    otherwise.

    Locating it means finding `<session_id>.jsonl` under `~/.claude/projects/`.
    An earlier version derived the containing folder from `cwd` by replacing
    path separators with dashes; that was wrong twice over, because a `+`
    quantifier collapsed `D:\\` into one dash instead of two, and because the
    same code cannot handle a POSIX-style path from a bash shell. Globbing on
    the session id needs no slug scheme at all.

    There is deliberately NO newest-file fallback: reading some other session's
    transcript would block this turn over a message the CPO never saw. When the
    file cannot be found, the gate fails open, like every hook here.
    """
    direct = event.get("transcript_path")
    if direct and os.path.isfile(direct):
        return direct
    session = event.get("session_id")
    if not session:
        return None
    base = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    matches = glob.glob(os.path.join(base, "*", f"{session}.jsonl"))
    return matches[0] if matches else None


def final_assistant_text(path: str) -> str:
    """The text blocks of the last assistant message that had any.

    A turn's last record is often a tool call, so this walks backwards to the
    most recent record carrying prose. Sidechain records (subagent output) are
    skipped — a subagent's report is not what the CPO reads.
    """
    # Read the TAIL only. This runs at the end of every turn, alongside the stop
    # gate's `git status`, and a transcript grows all session — parsing the whole
    # file would make every turn end slower than the last.
    with open(path, "rb") as fh:
        fh.seek(0, os.SEEK_END)
        size = fh.tell()
        fh.seek(max(0, size - TAIL_BYTES))
        chunk = fh.read()
    if size > TAIL_BYTES:
        chunk = chunk.split(b"\n", 1)[-1]     # drop the partial first line
    rows = []
    for line in chunk.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    for row in reversed(rows):
        if row.get("type") != "assistant" or row.get("isSidechain"):
            continue
        blocks = (row.get("message") or {}).get("content") or []
        text = "\n".join(
            b.get("text", "")
            for b in blocks
            if isinstance(b, dict) and b.get("type") == "text"
        ).strip()
        if text:
            return text
    return ""


def _prose(text: str) -> str:
    """The message with code, link targets and URLs removed.

    Order matters: fences first (they can contain backticks), then inline spans,
    then link targets, then bare URLs. An odd number of fence markers leaves the
    block unstripped, which is deliberate — under-stripping risks a false block,
    but over-stripping would let a wall of text through by opening a fence.
    """
    text = _FENCE.sub(" ", text)
    text = _INLINE_CODE.sub(" ", text)
    text = _LINK_TARGET.sub(" ", text)
    return _URL.sub(" ", text)


def violations(text: str) -> list[str]:
    found = []
    prose = _prose(text)
    if _EM_DASH in prose:
        found.append(
            "EM DASH. The CPO asked for none, as an absolute. Use a comma, a full "
            "stop, or restructure the sentence."
        )
    if _SECTION in prose:
        found.append(
            "SECTION SYMBOL. Say what the rule IS, in words. He does not read the "
            "working agreement and a number is not an argument."
        )
    paths = sorted(set(_REPO_PATH.findall(prose)))
    if paths:
        found.append(
            "FILE PATH IN PROSE: " + ", ".join(paths[:5]) + ". Describe the thing, "
            "not its location. Paths belong in chat only when he asks for them."
        )
    # Measured on PROSE, not the raw message. The objection is walls of text, and
    # a code block or a table the CPO asked for is scannable, not a wall. Counting
    # the raw text would block a requested sample under advice about cutting
    # options he never asked for (cto-reviewer, 2026-07-22).
    if len(prose) > MAX_CHARS:
        found.append(
            f"TOO LONG: {len(prose)} characters of prose against a {MAX_CHARS} "
            "limit (code blocks are not counted). Lead with the decision, cut the "
            "survey of options he did not ask for, and delete every sentence that "
            "restates the previous one."
        )
    return found


def main() -> int:
    try:
        event = read_event()
        if not isinstance(event, dict):      # `null` / `[]`: valid JSON, not an event
            return 0
        if event.get("stop_hook_active"):    # already blocked once; no loops
            return 0
        path = _transcript_path(event)
        if not path:
            return 0                         # fail open
        text = final_assistant_text(path)
        if not text:
            return 0
        found = violations(text)
        if found:
            print(json.dumps({
                "decision": "block",
                "reason": (
                    "PLAIN LANGUAGE GATE: rewrite this message before it is sent.\n\n"
                    + "\n".join(f"- {v}" for v in found)
                    + "\n\nRewrite it and end the turn again. Do not explain the "
                    "rewrite to the CPO and do not apologise for it, just send the "
                    "better message.\n\n"
                    "TEXT ONLY: do not edit, write or move a file while rewriting. "
                    "`stop_hook_active` belongs to the continuation, not to one "
                    "hook, so this block stands the contract-vs-tree stop gate down "
                    "for the rest of this turn. Anything changed while rewording "
                    "would go unchecked at turn end."
                ),
            }))
    except Exception:
        return 0                             # fail open (house rule)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
