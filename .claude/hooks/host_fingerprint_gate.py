#!/usr/bin/env python
"""Host-fingerprint gate — a live host's network address has no place in a public repo.

Denies an `Edit`, `Write` or `MultiEdit` whose written text puts a public network address into
ANY file inside the repo — any tree, any extension, the committed task artifacts under
`.claude/task/**` included, because that is where it slipped: a reviewer's grep pattern, copied
into `review.md` as proof that an address was gone, carried the address. A public address is one
of:

  IPv4 — four bounded octets, outside the loopback, private, link-local, multicast and reserved
         ranges (`127.x`, `10.x`, `172.16-31.x`, `192.168.x`, `169.254.x`, `224+.x`, the
         unspecified and broadcast addresses pass — they identify no host of ours)
  IPv6 — a global-unicast literal: a leading `2xxx`/`3xxx` group and at least three more colon
         groups (a time or a date has fewer; a hash has no colons)

What the rule can recognise is the address. A hostname, a provider, a city, a hardware size or a
port list has no pattern and stays judgment — the deny text names them, so the moment of writing
is the moment of the reminder. Such facts live in the provider's console; a doc says where, not
what. Accepted false positive: a four-part version string reads as an IPv4 (none in the tree).

The check reads only the text being written, not the whole file, and never echoes the value in
the deny. Paths outside the repo (memory, plans, scratchpad) pass. `NotebookEdit` writes
`new_source`, never read here. `tests/test_no_host_fingerprint_in_tree.py` imports the patterns
and the range test below and pins the tracked tree at zero. Fails OPEN on any unexpected error,
like every hook in this directory.
"""

from __future__ import annotations

import os
import re
import sys
from collections.abc import Iterator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _command_utils import emit_deny, read_event  # noqa: E402

_OCTET = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
# Four octets not glued to a word character, and not one part of a longer dotted number
# (`1.2.3.4.5`): a dot before or after counts only when a digit sits on its other side, so an
# address at the end of a sentence still matches.
IPV4 = re.compile(rf"(?<!\w)(?<!\d\.){_OCTET}(?:\.{_OCTET}){{3}}(?!\w)(?!\.\d)")
IPV6 = re.compile(r"(?<![\w:])[23][0-9a-fA-F]{3}(?::[0-9a-fA-F]{0,4}){3,7}(?![\w:])")


def ipv4_is_public(literal: str) -> bool:
    """True when the four octets name a host on the public internet."""
    a, b, c, d = (int(x) for x in literal.split("."))
    if a in (0, 10, 127) or a >= 224:
        return False
    if a == 172 and 16 <= b <= 31:
        return False
    if a == 192 and b == 168:
        return False
    if a == 169 and b == 254:
        return False
    if (a, b, c, d) == (255, 255, 255, 255):
        return False
    return True


def flagged_lines(text: str) -> Iterator[tuple[int, str]]:
    """(1-based line number, kind) for every line carrying a public address literal."""
    for n, line in enumerate(text.splitlines(), 1):
        if any(ipv4_is_public(m.group(0)) for m in IPV4.finditer(line)):
            yield n, "IPv4"
        elif IPV6.search(line):
            yield n, "IPv6"


def _written_texts(tool_input: dict) -> list[str]:
    texts = []
    if isinstance(tool_input.get("new_string"), str):
        texts.append(tool_input["new_string"])
    if isinstance(tool_input.get("content"), str):
        texts.append(tool_input["content"])
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict) and isinstance(edit.get("new_string"), str):
            texts.append(edit["new_string"])
    return texts


def _repo_root() -> str:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return os.path.abspath(env)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main() -> int:
    event = read_event()
    try:
        tool_input = event.get("tool_input") or {}
        file_path = tool_input.get("file_path") or ""
        if not file_path:
            return 0
        try:
            rel = os.path.relpath(os.path.abspath(file_path), _repo_root())
        except ValueError:
            return 0
        if rel.startswith(".."):
            return 0
        rel = rel.replace("\\", "/")
        hits = []
        for text in _written_texts(tool_input):
            hits.extend(flagged_lines(text))
        if not hits:
            return 0
        shown = ", ".join(f"line {n} ({kind})" for n, kind in hits[:3])
        emit_deny(
            f"HOST FINGERPRINT GATE: this write puts a public network address into `{rel}` at "
            f"{shown}. A live host's address has no place in a public repo — not in a doc, not in "
            "a task artifact, not as a grep pattern proving it is gone. Describe the host and say "
            "where its address lives (the provider's console); the same goes for its size, its "
            "city and its open ports, which no pattern can catch. If this is a version string, "
            "spell it another way."
        )
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
