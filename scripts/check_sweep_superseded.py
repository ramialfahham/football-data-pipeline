"""Exit 0 when a newer main commit already has its own design sweep, so this older one can stop.

`validate:ui` on main runs in the `validate-ui-main` resource group, newest first. A newer push to
main whose changes match the job's main `changes:` list has its own `validate:ui`, and that sweep
checks a tree containing this commit. Each push to main is one first-parent commit, so the files of
each newer push are that commit's first-parent diff. Any other outcome, an error included, exits
non-zero and the full sweep runs.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
JOB = "validate:ui"


def main_changes(ci: dict) -> list[str]:
    """The `changes:` list of the job's rule that admits a push to the default branch."""
    for rule in ci[JOB]["rules"]:
        if "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH" in str(rule.get("if", "")) and "changes" in rule:
            return list(rule["changes"])
    raise LookupError(f"{JOB} has no default-branch rule with changes:")


def _glob_regex(pattern: str) -> re.Pattern[str]:
    """GitLab's `changes:` glob: `**/` spans any number of folders, `*` and `?` stay inside one."""
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def matches(path: str, patterns: list[str]) -> bool:
    return any(_glob_regex(p).match(path) for p in patterns)


def newer_pushes(git, this_sha: str, tip: str) -> list[tuple[str, list[str]]]:
    """(commit, files) for each first-parent commit after `this_sha` up to `tip`, newest first."""
    shas = git("rev-list", "--first-parent", f"{this_sha}..{tip}").split()
    return [
        (sha, git("diff-tree", "--no-commit-id", "--name-only", "-r", f"{sha}^1", sha).split())
        for sha in shas
    ]


def superseding_push(pushes: list[tuple[str, list[str]]], patterns: list[str]) -> str | None:
    for sha, files in pushes:
        if any(matches(f, patterns) for f in files):
            return sha
    return None


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-c", "safe.directory=*", *args], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout


def main() -> int:
    this_sha = os.environ["CI_COMMIT_SHA"]
    branch = os.environ["CI_DEFAULT_BRANCH"]
    _git("fetch", "--quiet", "--no-tags", "origin", branch)
    tip = _git("rev-parse", "FETCH_HEAD").strip()
    ci = yaml.safe_load((REPO / ".gitlab-ci.yml").read_text(encoding="utf-8"))
    newer = superseding_push(newer_pushes(_git, this_sha, tip), main_changes(ci))
    if newer is None:
        print(f"No newer {branch} commit has its own design sweep; running the full sweep.")
        return 1
    print(f"Superseded: {branch} commit {newer} has its own design sweep, which covers {this_sha}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
