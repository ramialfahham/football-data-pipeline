"""A code comment says WHY, never who decided or when — the guard, both halves.

Half one is the edit-time hook `.claude/hooks/comment_history_gate.py`: it denies an `Edit`,
`Write` or `MultiEdit` whose written text adds a comment line carrying decision history to a code
file. Half two is the pin below: the count of such lines already in the tree, which may only move
in the open — a sweep MR lowers the pin, and nothing else moves it.

Everything here imports the hook's own definition of a flagged line and of a code tree, so the CI
count and the edit-time deny cannot drift apart; `test_definition_is_imported_not_copied` pins
that. The rule these guard is in `dbt_project/docs/engineering_standards.md`, section 1.2.

The sample lines used in the tests are BUILT at runtime from pieces, never written as literals,
because a literal `"x = 1  <hash> <marker>"` in this file would itself be a flagged line — the
guard reads source text, not semantics, and this file is inside a guarded tree.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
HOOKS = os.path.join(REPO, ".claude", "hooks")
sys.path.insert(0, HOOKS)
import comment_history_gate as gate  # noqa: E402

# The pin. A sweep MR lowers these two numbers and nothing else may move them.
PINNED_LINES = 495
PINNED_FILES = 84

HASH = chr(35)


def history_line(marker_text: str) -> str:
    """A code line whose trailing comment carries `marker_text`, assembled so that THIS file holds
    no flagged line."""
    return f"x = 1  {HASH} {marker_text}"


SAMPLE_MARKERS = {
    "date": "changed on " + "2026" + "-08-20",
    "product owner": "the " + "CPO" + " ruled this",
    "reviewer": "the " + "platform-" + "reviewer" + " asked for it",
    "review round": "found in " + "round " + "3",
    "merge request": "see " + "!" + "132",
}


def run_hook(event: dict) -> str:
    env = dict(os.environ, CLAUDE_PROJECT_DIR=REPO)
    proc = subprocess.run(
        [sys.executable, os.path.join(HOOKS, "comment_history_gate.py")],
        input=json.dumps(event), capture_output=True, text=True, env=env, timeout=60, check=False,
    )
    return proc.stdout


def edit_event(rel_path: str, new_string: str, tool: str = "Edit") -> dict:
    return {"hook_event_name": "PreToolUse", "tool_name": tool,
            "tool_input": {"file_path": os.path.join(REPO, rel_path), "new_string": new_string}}


def denied(out: str) -> bool:
    return '"permissionDecision": "deny"' in out


# --- the pin -----------------------------------------------------------------------------------

def test_the_tree_matches_the_pin_in_both_directions():
    lines, files = gate.count_tree(REPO)
    assert lines <= PINNED_LINES, (
        f"{lines - PINNED_LINES} new comment line(s) carrying decision history were added. A "
        "comment says WHY; who decided, when, which reviewer, which round, which MR live in the "
        "commit message, the MR and the issue (engineering_standards.md section 1.2)."
    )
    assert lines == PINNED_LINES and files == PINNED_FILES, (
        f"the tree now holds {lines} flagged lines in {files} files against a pin of "
        f"{PINNED_LINES} in {PINNED_FILES}: lower PINNED_LINES / PINNED_FILES in this file so the "
        "sweep is recorded — the number moves only in the open"
    )


def test_count_tree_counts_what_the_hook_flags(tmp_path):
    root = tmp_path
    (root / "scripts").mkdir()
    (root / "docs").mkdir()
    body = "\n".join(["import os", history_line(SAMPLE_MARKERS["date"]),
                      "y = 2", history_line(SAMPLE_MARKERS["reviewer"])]) + "\n"
    (root / "scripts" / "a.py").write_text(body, encoding="utf-8")
    (root / "scripts" / "clean.py").write_text("z = 3\n", encoding="utf-8")
    (root / "docs" / "note.md").write_text(history_line(SAMPLE_MARKERS["date"]) + "\n", encoding="utf-8")
    assert gate.count_tree(str(root)) == (2, 1), "two flagged lines in one code file; markdown is not code"
    with open(root / "scripts" / "clean.py", "a", encoding="utf-8") as fh:
        fh.write(history_line(SAMPLE_MARKERS["product owner"]) + "\n")
    assert gate.count_tree(str(root)) == (3, 2), "adding one flagged line moves the count by one"


# --- one definition ----------------------------------------------------------------------------

def test_definition_is_imported_not_copied():
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    compile_call, trees_def, exts_def = "re." + "compile(", "TREES" + " = (", "EXTS" + " = "
    assert compile_call not in src, "the marker patterns live in the hook; this file imports them"
    assert trees_def not in src and exts_def not in src, "the tree list lives in the hook"
    for name in ("MARKERS", "TREES", "EXTS", "is_history_comment", "flagged_lines", "count_tree"):
        assert hasattr(gate, name), name


def test_block_comment_continuation_lines_are_comment_lines():
    """A wrapped `/* … */` block whose inner lines carry no marker character was invisible to a
    per-line check — `site_v2/src/styles/system.css` narrated what an MR shipped on such a line.
    Every line between the opener and its closer is a comment line, per language."""
    slash, star = chr(47), chr(42)
    opener, closer = slash + star, star + slash
    css = "\n".join([".a { color: red; }", opener + " the ring is drawn inside, and the reason is measured",
                     "   " + SAMPLE_MARKERS["merge request"] + " shipped exactly this",
                     "   " + closer, ".b { color: blue; }"]) + "\n"
    assert [(n, k) for n, k, _ in gate.flagged_lines(css, ".css")] == [(3, "merge request")]
    assert gate.flagged_lines(css, ".py") == [], "a slash-star block is not a comment in Python"
    jinja_open, jinja_close = "{" + HASH, HASH + "}"
    sql = "\n".join(["select 1", jinja_open + " why this reads all snapshots:",
                     "   " + SAMPLE_MARKERS["product owner"] + " " + jinja_close, "from t"]) + "\n"
    assert [(n, k) for n, k, _ in gate.flagged_lines(sql, ".sql")] == [(3, "product owner")]
    html_open, html_close = "<" + "!--", "--" + ">"
    astro = "\n".join(["---", "---", html_open + " layout note", "   " + SAMPLE_MARKERS["date"] + " " + html_close]) + "\n"
    assert [(n, k) for n, k, _ in gate.flagged_lines(astro, ".astro")] == [(4, "date")]


def test_a_line_that_closes_one_block_and_opens_another_keeps_the_state():
    """The state machine used to clear the block on any line containing a closer, so a line
    reading `*/ .b{} /* reopens` dropped the second block and hid its continuation lines from
    both the deny and the pin. Every opener is matched to its closer in order, on the line."""
    slash, star = chr(47), chr(42)
    opener, closer = slash + star, star + slash
    css = "\n".join([".a { color: red; }",
                     opener + " comment starts here",
                     closer + " .b{} " + opener + " comment reopens",
                     SAMPLE_MARKERS["date"] + " the " + "CPO" + " ruled this stays forever",
                     closer + " .c{}"]) + "\n"
    assert [(n, k) for n, k, _ in gate.flagged_lines(css, ".css")] == [(4, "date")]
    one_line = "x;" + opener + " a " + closer + " y " + opener + " dangling\n" + SAMPLE_MARKERS["reviewer"] + "\n" + closer + "\n"
    assert [(n, k) for n, k, _ in gate.flagged_lines(one_line, ".js")] == [(2, "reviewer")], \
        "the second opener on a line, left open, is the live one"
    glued = "a=1;" + opener + " no whitespace before the opener\n" + SAMPLE_MARKERS["product owner"] + "\n" + closer + "\n"
    assert [(n, k) for n, k, _ in gate.flagged_lines(glued, ".ts")] == [(2, "product owner")], \
        "an opener glued to code still opens a block"
    closed_same_line = "a=1; " + opener + " " + SAMPLE_MARKERS["date"] + " " + closer + "\n" + SAMPLE_MARKERS["reviewer"] + "\n"
    assert [(n, k) for n, k, _ in gate.flagged_lines(closed_same_line, ".css")] == [(1, "date")], \
        "a block closed on its own line does not leak into the next line"


def test_two_comment_syntaxes_on_one_line_pick_the_leftmost_open_block():
    """`.sql` carries `/* */` and `{# #}`, `.astro` carries `/* */` and `<!-- -->`. When both
    appear on one line the walk must pair each opener with its own closer, in position order —
    a walk that let the last-checked syntax win would leave the wrong block open."""
    slash, star = chr(47), chr(42)
    c_open, c_close = slash + star, star + slash
    j_open, j_close = "{" + HASH, HASH + "}"
    # a closed C block, then an open Jinja block: the next line is inside the Jinja block
    sql = "\n".join([c_open + " a " + c_close + " select 1 " + j_open + " why:",
                     SAMPLE_MARKERS["date"], j_close, "from t"]) + "\n"
    assert [(n, k) for n, k, _ in gate.flagged_lines(sql, ".sql")] == [(2, "date")]
    # the other order: a closed Jinja block, then an open C block, closed two lines later
    sql2 = "\n".join([j_open + " a " + j_close + " select 1 " + c_open + " why:",
                      SAMPLE_MARKERS["reviewer"], c_close + " from t", SAMPLE_MARKERS["date"]]) + "\n"
    assert [(n, k) for n, k, _ in gate.flagged_lines(sql2, ".sql")] == [(2, "reviewer")], \
        "line 4 is code again once the C block closed on line 3"
    # an unterminated C block whose text merely contains the other syntax's opener
    sql3 = "\n".join([c_open + " unterminated, and " + j_open + " is just text here",
                      SAMPLE_MARKERS["product owner"], j_close + " still inside the C block",
                      SAMPLE_MARKERS["date"], c_close]) + "\n"
    assert [(n, k) for n, k, _ in gate.flagged_lines(sql3, ".sql")] == [(2, "product owner"), (4, "date")], \
        "only the C closer ends the block; a Jinja closer inside it is text"
    h_open, h_close = "<" + "!--", "--" + ">"
    astro = "\n".join(["---", "---", h_open + " a " + h_close + " <p/> " + c_open + " why:",
                       SAMPLE_MARKERS["merge request"], c_close]) + "\n"
    assert [(n, k) for n, k, _ in gate.flagged_lines(astro, ".astro")] == [(4, "merge request")]


def test_python_docstrings_are_comment_lines_but_string_literals_are_not():
    q = '"' * 3
    module = "\n".join([q + "Module purpose.", "", "   " + SAMPLE_MARKERS["date"] + " and more", q, "",
                        "def f():", "    " + q + "Why f exists.", "    " + SAMPLE_MARKERS["reviewer"], "    " + q,
                        "    return 1", "", "FIXTURE = " + q + "not a docstring: " + SAMPLE_MARKERS["product owner"] + q]) + "\n"
    hits = [(n, k) for n, k, _ in gate.flagged_lines(module, ".py")]
    assert hits == [(3, "date"), (8, "reviewer")], hits
    fragment = "\n".join(["    " + q + "A docstring in an edit fragment that does not parse alone.",
                          "    " + SAMPLE_MARKERS["product owner"], "    " + q]) + "\n"
    assert [(n, k) for n, k, _ in gate.flagged_lines(fragment, ".py")] == [(2, "product owner")]


def test_every_marker_kind_is_flagged_and_a_why_is_not():
    for kind, text in SAMPLE_MARKERS.items():
        assert gate.is_history_comment(history_line(text)) == kind, kind
    assert gate.is_history_comment(history_line("the provider files a forfeit as FT with no stat line")) is None
    assert gate.is_history_comment("status = " + '"' + "reviewer" + '"') is None, "no comment marker, no flag"
    assert gate.is_history_comment(history_line("ground truth, not a review round")) is None, \
        "round without a digit is a word, not a round"
    assert gate.is_history_comment(history_line("what a reviewer sees in review.md")) is None, \
        "the bare word for the role is this repo's own concept, not a credit"
    assert gate.is_history_comment(history_line("every reviewer required by the routing table")) is None
    assert gate.is_history_comment(history_line("scope-" + "auditor" + " asked for it")) == "reviewer"
    for credit in ("an earlier version was wrong; a " + "reviewer" + " caught it",
                   "all three " + "reviewers" + " failed it",
                   "found by a " + "reviewer" + " reading the file",
                   "a " + "reviewer" + " pointed out the hole"):
        assert gate.is_history_comment(history_line(credit)) == "reviewer", credit


def test_a_quoted_span_is_a_literal_and_the_rest_of_the_line_is_prose():
    dq, sq = chr(34), chr(39)
    token = dq + "CPO" + " ANSWER:" + dq
    assert gate.is_history_comment(history_line("counts every " + token + " line")) is None, \
        "a quoted token the code parses is not prose about a decision"
    example = "--timestamp " + sq + "2026" + "-05-07 17:55:00" + sq
    assert gate.is_history_comment(history_line(example)) is None, "a quoted usage example"
    assert gate.is_history_comment(history_line("the " + "CPO" + " said " + dq + "drop it" + dq)) \
        == "product owner", "the marker outside the quotes still counts"
    assert gate.is_history_comment(history_line("he" + sq + "s sure " + "2026" + "-08-10 wasn" + sq + "t it")) \
        == "date", "an apostrophe inside a word opens no span, so the date between two is prose"
    assert gate.is_history_comment(history_line(sq + "tis the " + "CPO" + " ruling, rock " + sq + "n" + sq + " roll")) \
        == "product owner", "a quote that ends inside a word closes no span either"
    tick = chr(96)
    assert gate.is_history_comment(history_line("caught by " + tick + "platform-" + "reviewer" + tick)) \
        == "reviewer", "backticks are formatting, not a literal"
    q = dq * 3
    module = "def f():\n    " + q + "The " + "CPO" + " ruled this." + q + "\n    return 1\n"
    assert [(n, k) for n, k, _ in gate.flagged_lines(module, ".py")] == [(2, "product owner")], \
        "a one-line docstring is a comment line, not a quoted span"


# --- the hook, on real events ------------------------------------------------------------------

def test_hook_denies_a_history_comment_in_a_code_file():
    out = run_hook(edit_event("scripts/export_site_data.py", history_line(SAMPLE_MARKERS["product owner"])))
    assert denied(out)
    assert "COMMENT HISTORY GATE" in out and "section 1.2" in out


def test_hook_allows_the_same_text_in_markdown_and_in_task_artifacts():
    text = history_line(SAMPLE_MARKERS["product owner"])
    assert run_hook(edit_event("docs/working_agreement.md", text)).strip() == ""
    assert run_hook(edit_event(".claude/task/contract.md", text)).strip() == ""


def test_hook_allows_a_why_only_comment():
    out = run_hook(edit_event("scripts/export_site_data.py",
                              history_line("the export selects and renames; it never derives a fact")))
    assert out.strip() == ""


def test_hook_checks_write_content_and_multiedit_edits():
    write = {"hook_event_name": "PreToolUse", "tool_name": "Write",
             "tool_input": {"file_path": os.path.join(REPO, "ingestion", "new.py"),
                            "content": "import os\n" + history_line(SAMPLE_MARKERS["date"]) + "\n"}}
    assert denied(run_hook(write))
    multi = {"hook_event_name": "PreToolUse", "tool_name": "MultiEdit",
             "tool_input": {"file_path": os.path.join(REPO, "tests", "x.py"),
                            "edits": [{"old_string": "a", "new_string": "b"},
                                      {"old_string": "c", "new_string": history_line(SAMPLE_MARKERS["merge request"])}]}}
    assert denied(run_hook(multi))


def test_hook_ignores_paths_outside_the_repo_and_fails_open_on_garbage():
    outside = {"hook_event_name": "PreToolUse", "tool_name": "Edit",
               "tool_input": {"file_path": os.path.join(os.path.dirname(REPO), "elsewhere", "a.py"),
                              "new_string": history_line(SAMPLE_MARKERS["date"])}}
    assert run_hook(outside).strip() == ""
    env = dict(os.environ, CLAUDE_PROJECT_DIR=REPO)
    proc = subprocess.run([sys.executable, os.path.join(HOOKS, "comment_history_gate.py")],
                          input="not json", capture_output=True, text=True, env=env, timeout=60, check=False)
    assert proc.returncode == 0 and proc.stdout.strip() == ""


# --- the guard obeys its own rule --------------------------------------------------------------

@pytest.mark.parametrize("rel", [".claude/hooks/comment_history_gate.py", "tests/test_no_decision_history_in_code.py"])
def test_the_guard_files_hold_no_flagged_line(rel):
    text = pathlib.Path(REPO, rel).read_text(encoding="utf-8")
    assert gate.flagged_lines(text) == []
