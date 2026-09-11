#!/usr/bin/env python
"""Comment-history gate — a code comment says WHY, never who decided or when.

Denies an `Edit`, `Write` or `MultiEdit` whose written text adds, to a code file, a comment line
carrying decision history: a calendar date, the product owner's title, the word for a review
role, a numbered review round or a merge-request number (the exact patterns are MARKERS below).
That history has a home that survives the task without living next to
the line — the commit message, the merge request and the issue — and `git blame` reaches all three
from any line (dbt_project/docs/engineering_standards.md, section 1.2, has the recipe).

What counts as a comment line: a line with a comment marker (`#`, `--`, `//`, `/*`, `*`, `<!--`,
`{#`) at its start or after whitespace; every line inside a block comment of the file's language
(`/* … */`, `<!-- … -->`, `{# … #}`); and every line of a Python docstring — found by `ast` when
the text parses as a module, and by a line starting with a triple quote when it is a fragment.
A marker inside a quoted span of the line is a literal (a token, a usage example) and does not
count; a marker inside a code string literal that happens to follow whitespace does match —
accepted, rare, and the deny names the line.

The check reads only the text being written, not the whole file. So an edit that re-includes an
existing flagged line is denied until the marker is removed — every ordinary edit helps the sweep.
Markdown, docs, `.claude/task/` and any tree not listed below are not code and are never checked.

`tests/test_no_decision_history_in_code.py` imports the definitions below and pins the count of
flagged lines already in the tree, so the CI count and this deny cannot drift apart. Fails OPEN on
any unexpected error, like every hook in this directory.
"""

from __future__ import annotations

import ast
import os
import re
import sys
from collections.abc import Iterator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _command_utils import emit_deny, read_event  # noqa: E402

# Trees whose files are code. `.github/` is dormant and deliberately unedited; `docs/` is prose.
TREES = (
    "ingestion",
    "scripts",
    "dbt_project/models",
    "dbt_project/macros",
    "dbt_project/tests",
    "dbt_project/seeds",
    "site_v2/src",
    "site_v2/scripts",
    "site_v2/integrations",
    ".claude/hooks",
    "tests",
    "design-mocks",
    "deploy",
)
EXTS = frozenset({".py", ".sql", ".astro", ".ts", ".mjs", ".js", ".yml", ".yaml", ".css"})

# Block-comment delimiters per language. Python has none: its blocks are docstrings.
BLOCKS = {
    ".css": (("/*", "*/"),),
    ".js": (("/*", "*/"),),
    ".mjs": (("/*", "*/"),),
    ".ts": (("/*", "*/"),),
    ".astro": (("/*", "*/"), ("<!--", "-->")),
    ".sql": (("/*", "*/"), ("{#", "#}")),
    ".yml": (("{#", "#}"),),
    ".yaml": (("{#", "#}"),),
    ".py": (),
}

_COMMENT = re.compile(r"(^|\s)(#|--|//|/\*|\*|<!--|\{#)")
_DOCSTRING_OPEN = re.compile(r"^\s*(\"\"\"|''')")

# A review credit names a role, or narrates what an unnamed reviewer did — "a reviewer caught it",
# "two reviewers failed it", "caught by a reviewer". The bare word alone is this repo's own concept
# (the review gate describes what its readers see: "what a reviewer reads"), so it is no marker.
_ROLES = "cto|platform|analytics-engineer|bi-analyst|data-engineer|seo-expert|football-analytics-expert"
_FOUND = ("caught|found|flagged|spotted|noticed|pointed out|showed|produced|rejected|failed|asked|"
          "insisted|objected|raised|noted|reported")
MARKERS = {
    "date": re.compile(r"\b20\d\d-\d\d-\d\d\b"),
    "product owner": re.compile(r"\bCPO\b"),
    "reviewer": re.compile(
        rf"\b(?:(?:{_ROLES})-reviewer|scope-auditor)\b"
        rf"|\breviewers?\s+(?:{_FOUND})\b"
        rf"|\b(?:{_FOUND})\s+by\s+(?:a|the|one|another|every|each|both|two|three|all)\s+reviewers?\b",
        re.IGNORECASE),
    "review round": re.compile(r"\bround \d", re.IGNORECASE),
    "merge request": re.compile(r"(?<![\w!])!\d{1,4}\b"),
}

_SKIP_SEGMENTS = frozenset({"node_modules", "__pycache__", "target", ".venv"})


def is_code_path(rel: str) -> bool:
    """True when a repo-relative path is a code file under one of the guarded trees."""
    rel = rel.replace("\\", "/")
    if rel.startswith("./"):
        rel = rel[2:]
    if os.path.splitext(rel)[1].lower() not in EXTS:
        return False
    if _SKIP_SEGMENTS.intersection(rel.split("/")):
        return False
    return any(rel.startswith(t + "/") for t in TREES)


# A quoted span is a literal — a token the code parses, a value in a usage example — not prose
# about a decision, so it is blanked before the markers are matched. Only a quote that starts a
# token opens a span (an apostrophe inside a word does not), and a triple quote is a docstring
# delimiter, not a span, or a one-line docstring would vanish whole. Backticks are NOT a literal:
# measured over the tree, two in three backticked markers were credits, not identifiers.
_TRIPLE = re.compile(r"\"\"\"|'''")
_LITERAL = re.compile(r"(?<!\w)\"[^\"\n]*\"(?!\w)|(?<!\w)'[^'\n]*'(?!\w)")


def marker_kind(line: str) -> str | None:
    """The marker kind a line carries outside its literal spans, or None."""
    prose = _LITERAL.sub(" ", _TRIPLE.sub(" ", line))
    for kind, rx in MARKERS.items():
        if rx.search(prose):
            return kind
    return None


def is_history_comment(line: str) -> str | None:
    """The marker kind a single MARKER-BEARING comment line carries, or None when the line is
    clean or carries no comment marker. Block-comment and docstring lines are found by
    `comment_lines`, which has the context a single line does not."""
    if not _COMMENT.search(line):
        return None
    return marker_kind(line)


def _docstring_ranges(text: str) -> list[tuple[int, int]] | None:
    """(first, last) line numbers of every docstring, or None when the text is not a module."""
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return None
    ranges = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None) or []
        first = body[0] if body else None
        if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            ranges.append((first.lineno, first.end_lineno or first.lineno))
    return ranges


def _open_at_end(line: str, pairs: tuple, start: int = 0) -> str | None:
    """The closer of the block comment that is still open when `line` ends, scanning from
    `start`: every opener is matched to its closer on the same line, in order, so a line that
    closes one block and opens another leaves the second one open."""
    pos = start
    while True:
        first = None
        for opener, closer in pairs:
            at = line.find(opener, pos)
            if at != -1 and (first is None or at < first[0]):
                first = (at, opener, closer)
        if first is None:
            return None
        at, opener, closer = first
        end = line.find(closer, at + len(opener))
        if end == -1:
            return closer
        pos = end + len(closer)


def comment_lines(text: str, ext: str) -> Iterator[tuple[int, str]]:
    """(1-based line number, line) for every comment line in `text`, for a file of type `ext`."""
    ext = ext.lower()
    pairs = BLOCKS.get(ext, ())
    lines = text.splitlines()
    in_doc: set[int] = set()
    use_heuristic = False
    if ext == ".py":
        ranges = _docstring_ranges(text)
        if ranges is None:
            use_heuristic = True
        else:
            for a, b in ranges:
                in_doc.update(range(a, b + 1))
    closer: str | None = None
    doc_fragment = False
    for n, line in enumerate(lines, 1):
        if n in in_doc:
            yield n, line
            continue
        if closer:
            yield n, line
            end = line.find(closer)
            if end != -1:
                closer = _open_at_end(line, pairs, end + len(closer))
            continue
        if doc_fragment:
            yield n, line
            if '"""' in line or "'''" in line:
                doc_fragment = False
            continue
        has_opener = any(opener in line for opener, _ in pairs)
        if _COMMENT.search(line) or has_opener:
            yield n, line
            closer = _open_at_end(line, pairs)
            continue
        if use_heuristic and _DOCSTRING_OPEN.match(line):
            yield n, line
            quote = _DOCSTRING_OPEN.match(line).group(1)
            if line.count(quote) < 2:
                doc_fragment = True


def flagged_lines(text: str, ext: str = ".py") -> list[tuple[int, str, str]]:
    """(1-based line number, marker kind, line) for every comment line carrying history."""
    out = []
    for n, line in comment_lines(text, ext):
        kind = marker_kind(line)
        if kind:
            out.append((n, kind, line.strip()))
    return out


def count_tree(root: str) -> tuple[int, int]:
    """(flagged lines, files with at least one) across the guarded trees under `root`."""
    lines = files = 0
    for tree in TREES:
        for dirpath, _dirs, names in os.walk(os.path.join(root, tree)):
            for name in names:
                path = os.path.join(dirpath, name)
                rel = os.path.relpath(path, root).replace("\\", "/")
                if not is_code_path(rel):
                    continue
                try:
                    with open(path, encoding="utf-8", errors="replace") as fh:
                        hits = flagged_lines(fh.read(), os.path.splitext(rel)[1])
                except OSError:
                    continue
                if hits:
                    lines += len(hits)
                    files += 1
    return lines, files


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
        root = _repo_root()
        try:
            rel = os.path.relpath(os.path.abspath(file_path), root)
        except ValueError:
            return 0
        if rel.startswith(".."):
            return 0
        if not is_code_path(rel):
            return 0
        ext = os.path.splitext(rel)[1]
        hits = []
        for text in _written_texts(tool_input):
            hits.extend(flagged_lines(text, ext))
        if not hits:
            return 0
        shown = "; ".join(f"line {n} ({kind}): `{line[:120]}`" for n, kind, line in hits[:3])
        emit_deny(
            "COMMENT HISTORY GATE: this edit adds a comment carrying decision history to a code "
            f"file — {shown}. A comment says WHY in one line; who decided, when, which reviewer, "
            "which round, which MR — never in code. That lives in the commit message, the MR and "
            "the issue, and `git blame` reaches all three (engineering_standards.md section 1.2). "
            "Rewrite the comment as the why alone, or drop it."
        )
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
