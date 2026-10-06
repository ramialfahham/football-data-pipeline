#!/usr/bin/env python
"""Sentence-length gate — a document sentence stays within the ASD-STE100 limit.

Denies an `Edit`, `Write` or `MultiEdit` whose resulting Markdown document holds a sentence over
the limit that the document on disk did not hold. The limit is 20 words for a sentence inside a
numbered list item (a procedure step) and 25 words for every other sentence (a description),
as `docs/working_agreement.md` section 9 states.

What counts: paragraphs, list items, blockquotes and table cells are prose; headings, fenced code
blocks, HTML comments and front matter are not. An inline code span counts as one word and a link
counts its visible text. A sentence ends at a full stop, an exclamation or question mark, or a
semicolon, followed by whitespace.

A long sentence already in the document never blocks an edit to it; a changed one must meet the
limit. The documents covered are the ones `comment_history_gate.is_doc_path` covers.
`tests/test_sentence_length_in_docs.py` imports `count_docs` and pins each document's count of
long sentences, so the CI count and this deny cannot drift apart; the counts only go down.
Fails OPEN on any unexpected error, like every hook in this directory.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _command_utils import emit_deny, read_event  # noqa: E402
from comment_history_gate import is_doc_path  # noqa: E402
from memory_budget_gate import resulting_text  # noqa: E402

PROCEDURE_LIMIT = 20
DESCRIPTION_LIMIT = 25

_FENCE = re.compile(r"^\s*(```|~~~)")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
_HEADING = re.compile(r"^#{1,6}(\s|$)")
_BREAK = re.compile(r"^([-*_]\s*){3,}$")
_BLOCKQUOTE = re.compile(r"^(>\s?)+")
_NUMBERED = re.compile(r"^\d+[.)]\s+")
_BULLET = re.compile(r"^[-*+]\s+")
_TABLE_RULE = re.compile(r"^\|?[\s:|-]+\|?$")
_CODE_SPAN = re.compile(r"`[^`\n]+`")
_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_SENTENCE_END = re.compile(r"(?<=[.!?;])\s+")
_JOIN = "\x01"


def _prose_units(text: str) -> list[tuple[int, str]]:
    """(limit, prose) for every paragraph, list item and table cell of a Markdown text."""
    text = _HTML_COMMENT.sub(" ", text.replace("\r\n", "\n"))
    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        for end in range(1, len(lines)):
            if lines[end].strip() == "---":
                lines = lines[end + 1:]
                break
    units: list[tuple[int, str]] = []
    buf: list[str] = []
    limit = DESCRIPTION_LIMIT
    in_fence = False

    def flush() -> None:
        if buf:
            units.append((limit, " ".join(buf)))
            buf.clear()

    for line in lines:
        if _FENCE.match(line):
            flush()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        s = _BLOCKQUOTE.sub("", line.strip()).strip()
        if not s or _HEADING.match(s) or _BREAK.match(s):
            flush()
            continue
        if s.startswith("|"):
            flush()
            if not _TABLE_RULE.match(s):
                units.extend((DESCRIPTION_LIMIT, cell) for cell in s.strip("|").split("|"))
            continue
        numbered, bullet = _NUMBERED.match(s), _BULLET.match(s)
        if numbered or bullet:
            flush()
            limit = PROCEDURE_LIMIT if numbered else DESCRIPTION_LIMIT
            s = s[(numbered or bullet).end():]
        elif not buf:
            limit = DESCRIPTION_LIMIT
        buf.append(s)
    flush()
    return units


def long_sentences(text: str) -> list[tuple[int, int, str]]:
    """(limit, words, sentence) for every sentence of a Markdown text that is over its limit."""
    hits = []
    for limit, prose in _prose_units(text):
        prose = _LINK.sub(r"\1", prose)
        prose = _CODE_SPAN.sub(lambda m: re.sub(r"\s", _JOIN, m.group(0)), prose)
        for sentence in _SENTENCE_END.split(prose):
            words = sentence.split()
            if len(words) > limit:
                hits.append((limit, len(words), " ".join(words).replace(_JOIN, " ")))
    return hits


def added_long_sentences(before: str, after: str) -> list[tuple[int, int, str]]:
    """Long sentences in `after` that `before` did not hold."""
    existing = {s for _limit, _n, s in long_sentences(before)}
    return [hit for hit in long_sentences(after) if hit[2] not in existing]


def count_docs(root: str, paths: list[str]) -> dict[str, int]:
    """{document: long-sentence count} for the given repo-relative paths the gate covers."""
    counts = {}
    for rel in paths:
        if not is_doc_path(rel):
            continue
        try:
            with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as fh:
                n = len(long_sentences(fh.read()))
        except OSError:
            continue
        if n:
            counts[rel.replace("\\", "/")] = n
    return counts


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
        root = _repo_root()
        try:
            rel = os.path.relpath(os.path.abspath(file_path), root)
        except ValueError:
            return 0
        if rel.startswith("..") or not is_doc_path(rel):
            return 0
        try:
            with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as fh:
                before = fh.read().replace("\r\n", "\n")
        except OSError:
            before = ""
        after = resulting_text(tool_input, before)
        if after is None:
            return 0
        hits = added_long_sentences(before, after)
        if not hits:
            return 0
        shown = "; ".join(f"{n} words (limit {limit}): `{s[:100]}`" for limit, n, s in hits[:3])
        emit_deny(
            f"SENTENCE LENGTH GATE: this edit adds {len(hits)} sentence(s) over the limit to "
            f"{rel.replace(os.sep, '/')} — {shown}. A description sentence has at most "
            f"{DESCRIPTION_LIMIT} words and a numbered step at most {PROCEDURE_LIMIT} "
            "(working_agreement.md section 9, ASD-STE100). Split each into sentences of one topic."
        )
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
