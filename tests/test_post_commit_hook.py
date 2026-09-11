"""Pin what `.githooks/post-commit` decides: open an MR unless one is already OPEN (GitLab #29).

WHY THIS EXISTS
---------------
The hook auto-pushes and opens a merge request so that working agreement section 3 ("the task is
not done until you open the MR") cannot be forgotten. It asked whether an MR *existed* for the
branch and never whether it was still *open*. Once it printed "MR already open" for an MR that
was `state: merged`; two commits then sat on the branch with no MR, and `main` kept a handover
that had already been corrected. It was noticed because a CI timestamp read as older than the
commits, which is luck rather than a check.

The failure mode is not "no MR opens". It is "the tooling reports one is open when it is not", so
the builder reads a URL, believes step 4 is done, and stops looking. Until this file the hook had
no test of any kind.

WHY THE STUB MODELS THE API AND NOT THE IMPLEMENTATION
------------------------------------------------------
`tests/test_materialisation_policy.py` records the lesson: a guard that names its targets in prose
is nearly inert, because a reword defeats it silently. So this does not assert on the hook's text.
It puts stub `git` and `glab` executables on PATH, runs the hook under bash, and asserts on the
OUTCOME — was `glab mr create` reached.

The stub answers whichever lookup the hook chooses to make, `mr view` or `mr list`, with what the
REAL `glab` returns for that scenario. That is deliberate: the test states a requirement about the
branch's MR state, not about which CLI call satisfies it, so a future reimplementation that asks
correctly by some third route still passes.

MEASURED against the live project, not invented. Each cell is post-`--jq` stdout
and the process exit code:

  scenario                     `mr view <branch> --jq .web_url`   `mr list -s <branch> --jq .[0].web_url // empty`
  only a MERGED MR             exit 0, the real URL   <-- trap    exit 0, empty
  two MRs, both merged         exit 1, JSON error on STDOUT       exit 0, empty
  no MR at all                 exit 1, JSON error on STDOUT       exit 0, empty
  an OPEN MR                   exit 0, the real URL               exit 0, the real URL

Note the second column's error object goes to STDOUT, so a `2>/dev/null` redirect does not hide it
and a `-n "$OUT"` test passes on a failure. Only the exit code separated those rows.

WHICH CASE ACTUALLY DISCRIMINATES
---------------------------------
`test_merged_mr_is_not_treated_as_open` is the one that goes RED against the pre-#29 hook. The
others were already correct and are here so they stay correct; `test_main_branch_is_skipped_
entirely` pins the most expensive possible regression, a hook that pushes main.

`bash` is required. It is present in CI (`.gitlab-ci.yml` runs `python -m pytest tests/ -v` on
Linux), so the skip below never fires there.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOOK = ROOT / ".githooks" / "post-commit"

BASH = shutil.which("bash")

pytestmark = pytest.mark.skipif(BASH is None, reason="post-commit is a bash hook and bash is absent")

OPEN_URL = "https://gitlab.com/rami.al-fahham/football-data-pipeline/-/merge_requests/99"

# The JSON error object glab writes to STDOUT when it cannot resolve a single MR for a branch.
VIEW_ERROR = '{"error":{"message":"no open merge request available for \\"x\\""}}'

# scenario -> (mr view stdout, mr view exit, mr list stdout, mr list exit)
SCENARIOS = {
    "merged_only": (OPEN_URL, 0, "", 0),
    "two_merged": (VIEW_ERROR, 1, "", 0),
    "no_mr": (VIEW_ERROR, 1, "", 0),
    "open_mr": (OPEN_URL, 0, OPEN_URL, 0),
    "lookup_fails": ("", 1, "", 1),
}

GIT_STUB = """#!/bin/sh
if [ "$1" = "rev-parse" ]; then
  printf '%s\\n' "$STUB_BRANCH"
  exit 0
fi
if [ "$1" = "push" ]; then
  printf 'push %s\\n' "$*" > "$STUB_DIR/git_push_called"
  exit 0
fi
exit 0
"""

# Reproduces glab's post---jq stdout and exit code. It does NOT evaluate the jq expression: the
# hook only ever asks for the web_url, and no jq binary exists on this machine to evaluate one.
GLAB_STUB = """#!/bin/sh
if [ "$1" = "mr" ] && [ "$2" = "create" ]; then
  printf 'create %s\\n' "$*" > "$STUB_DIR/mr_create_called"
  exit 0
fi
if [ "$1" = "mr" ] && [ "$2" = "view" ]; then
  cat "$STUB_DIR/view_stdout"
  exit "$(cat "$STUB_DIR/view_exit")"
fi
if [ "$1" = "mr" ] && [ "$2" = "list" ]; then
  cat "$STUB_DIR/list_stdout"
  exit "$(cat "$STUB_DIR/list_exit")"
fi
exit 0
"""


def _write(path: pathlib.Path, text: str) -> None:
    """Write with LF endings. CRLF in a stub makes bash report `\\r: command not found`."""
    path.write_text(text, encoding="utf-8", newline="\n")
    path.chmod(0o755)


class HookRun:
    def __init__(self, proc: subprocess.CompletedProcess, stub: pathlib.Path):
        self.proc = proc
        self.stub = stub

    @property
    def stdout(self) -> str:
        return self.proc.stdout

    @property
    def created_mr(self) -> bool:
        return (self.stub / "mr_create_called").exists()

    @property
    def pushed(self) -> bool:
        return (self.stub / "git_push_called").exists()


def _run_hook(tmp_path: pathlib.Path, scenario: str, branch: str = "feat/example") -> HookRun:
    view_out, view_exit, list_out, list_exit = SCENARIOS[scenario]

    stub = tmp_path / "stub"
    stub.mkdir()
    _write(stub / "git", GIT_STUB)
    _write(stub / "glab", GLAB_STUB)
    for name, value in (
        ("view_stdout", view_out),
        ("view_exit", str(view_exit)),
        ("list_stdout", list_out),
        ("list_exit", str(list_exit)),
    ):
        (stub / name).write_text(value, encoding="utf-8", newline="\n")

    env = dict(os.environ)
    env["PATH"] = str(stub) + os.pathsep + env["PATH"]
    # POSIX form: a backslash in a Windows path is an escape character to sh.
    env["STUB_DIR"] = stub.as_posix()
    env["STUB_BRANCH"] = branch

    proc = subprocess.run(
        [BASH, HOOK.as_posix()],
        env=env,
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=60,
    )
    return HookRun(proc, stub)


def test_merged_mr_is_not_treated_as_open(tmp_path):
    """GitLab #29 itself. The branch's only MR is merged, so the hook must open a new one.

    This is the case that goes RED against the pre-#29 hook, which printed the merged MR's URL
    under `MR already open` and opened nothing.
    """
    run = _run_hook(tmp_path, "merged_only")

    assert run.created_mr, (
        "the branch's only MR is MERGED, so the hook must open a new one. stdout:\n" + run.stdout
    )
    assert "already open" not in run.stdout.lower(), (
        "the hook reported an MR as open when none is. stdout:\n" + run.stdout
    )


def test_open_mr_is_left_alone(tmp_path):
    """The whole point of the check: do not open a second MR when one is already open."""
    run = _run_hook(tmp_path, "open_mr")

    assert not run.created_mr, "an MR is already open; the hook must not open another"
    assert OPEN_URL in run.stdout, "the open MR's URL must be reported. stdout:\n" + run.stdout


def test_branch_with_no_mr_gets_one(tmp_path):
    run = _run_hook(tmp_path, "no_mr")
    assert run.created_mr, "no MR exists for the branch; the hook must open one"


def test_two_merged_mrs_still_opens_one(tmp_path):
    """`glab mr view` cannot resolve a branch carrying more than one MR and errors instead.

    Real state of `chore/handover-after-22-23-24` when #29 was written. Whatever the lookup does,
    none of those MRs is open, so the hook must open one.
    """
    run = _run_hook(tmp_path, "two_merged")
    assert run.created_mr, "no OPEN MR exists among the branch's MRs; the hook must open one"


def test_lookup_failure_opens_rather_than_claiming_open(tmp_path):
    """Fail toward opening. A duplicate MR is visible and cheap; a false 'already open' is neither."""
    run = _run_hook(tmp_path, "lookup_fails")

    assert run.created_mr, "the lookup failed, so the hook must not conclude an MR is open"
    assert "already open" not in run.stdout.lower(), (
        "a failed lookup must never be reported as an open MR. stdout:\n" + run.stdout
    )


@pytest.mark.parametrize("branch", ["main", "master"])
def test_main_branch_is_skipped_entirely(tmp_path, branch):
    """The most expensive regression this file can catch: a hook that pushes main."""
    run = _run_hook(tmp_path, "no_mr", branch=branch)

    assert not run.pushed, f"the hook must never push {branch}"
    assert not run.created_mr, f"the hook must never open an MR from {branch}"
    assert run.proc.returncode == 0
