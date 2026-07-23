#!/usr/bin/env python
"""CI backstop for the governance artifacts (G3).

Local hooks can be bypassed by a misbehaving or misconfigured agent; this
check keeps the gate honest at the PR boundary. For the diff between the PR
branch and the base, it verifies:

  - artifact-only PRs (only bookkeeping paths) pass — but a PR touching
    .claude/task/contract.md is NEVER artifact-only (it authorizes scope; F10/#409);
  - otherwise .claude/task/contract.md and .claude/task/review.md must exist;
  - review.md carries a well-formed 64-hex diff_sha256 that MATCHES the recomputed
    hash of `git diff base...HEAD` excluding the bookkeeping artifacts — binding the
    review to this PR's code + contract (F11/#409);
  - every reviewer required by .claude/review_routing.json for the PR's
    changed paths has a verdict section;
  - no "VERDICT: FAIL"; every "VERDICT: ESCALATE" has a "CPO ANSWER:" in its
    OWN section (per-section pairing, mirroring the local commit gate — an
    answer elsewhere must not mask an unanswered escalation);
  - every "VERDICT: PASS" section names >= 2 risks.

Fails CLOSED (non-zero exit) — this is CI, not a guardrail hook.

Usage: python scripts/check_task_artifacts.py [--base origin/main]
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys

ROUTING = ".claude/review_routing.json"
CONTRACT = ".claude/task/contract.md"
REVIEW = ".claude/task/review.md"

# The CI backstop and the local hooks MUST agree, so CI IMPORTS the hooks' own
# logic rather than re-implementing it. Three hand-copied constant sets diverged
# once already (the round-cap placeholder set, the `(none)` nullish spelling, and
# the export regex) — the exact "the twin didn't get the fix" class this repo has
# been bitten by. Now there is one source: `git_discipline._rounds_gate` decides
# the round cap, and `task_contract_gate._read_contract` / `_is_structural` decide
# the consulted requirement. `test_governance_hooks` asserts CI reuses these.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".claude", "hooks"))
import git_discipline as _gd            # noqa: E402
import task_contract_gate as _tcg       # noqa: E402


def _rounds_error(text: str) -> str | None:
    """Round-cap rule — the SAME decision as the local commit gate, because it is
    literally that function. Non-None means deny."""
    return _gd._rounds_gate(text)


def _structural(paths: list[str]) -> bool:
    """True when any changed path is on the structural surface, by the edit gate's
    own `_is_structural` (which also covers protected paths)."""
    return any(_tcg._is_structural(p) for p in paths)


def _consulted_present(root: str) -> bool:
    """Whether contract.md carries a real `consulted:`, by the edit gate's parser."""
    c = _tcg._read_contract(root)
    return bool(c and c.get("consulted_present"))


def changed_paths(base: str) -> list[str]:
    # -z (NUL-split) mirrors the local gate: quotePath-escaped non-ASCII
    # paths would match no routing pattern and drop a required reviewer
    out = subprocess.run(
        ["git", "diff", "--name-only", "-z", f"{base}...HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [p.replace("\\", "/") for p in out.split("\0") if p]


def review_sections(text: str) -> dict[str, str]:
    """Text before the first `##` header is kept as the `_preamble`
    pseudo-section, mirroring the local gate — an ESCALATE written there must
    not escape the per-section pairing."""
    sections, name, buf = {}, "_preamble", []
    for line in text.splitlines():
        m = re.match(r"^##\s+(\S+)", line)
        if m:
            sections[name] = "\n".join(buf)
            name, buf = m.group(1), []
        else:
            buf.append(line)
    sections[name] = "\n".join(buf)
    return sections


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("GOVERNANCE_BASE", "origin/main"))
    args = ap.parse_args()

    paths = changed_paths(args.base)
    if not paths:
        print("check_task_artifacts: empty diff — OK")
        return 0

    with open(ROUTING, encoding="utf-8") as f:
        routing = json.load(f)

    artifact_pats = routing.get("artifact_only") or []
    # F10 (#409): a PR touching contract.md is never artifact-exempt (it authorizes scope).
    never = routing.get("artifact_only_never") or []
    is_never = any(fnmatch.fnmatch(p, pat) for p in paths for pat in never)
    if not is_never and all(
        any(fnmatch.fnmatch(p, pat) for pat in artifact_pats) for p in paths
    ):
        print("check_task_artifacts: artifact-only PR — OK")
        return 0

    errors: list[str] = []
    if not os.path.isfile(CONTRACT):
        errors.append(f"missing {CONTRACT} (every code PR carries its task contract)")
    if not os.path.isfile(REVIEW):
        errors.append(f"missing {REVIEW} (every code PR carries its review verdicts)")
    if errors:
        print("check_task_artifacts: FAIL\n  - " + "\n  - ".join(errors))
        return 1

    text = open(REVIEW, encoding="utf-8", errors="replace").read()
    m = re.search(r"diff_sha256:\s*([0-9a-fA-F]{64})", text)
    if not m:
        errors.append("review.md has no well-formed diff_sha256")
    else:
        # F11 (#409): bind review.md to THIS PR's code. Recompute the hash over the
        # branch diff EXCLUDING the bookkeeping artifacts — the same diff the local gate
        # hashes. --no-renames + --no-abbrev so the two invocations are byte-identical for
        # identical content (rename detection off; full 40-hex blob SHAs in index lines so
        # the abbreviation length cannot diverge pre- vs post-commit). A code-then-stale-
        # review ordering (the #405 false-green) now fails here.
        excludes = routing.get("hash_exclude_paths") or []
        pathspec = (["--", "."] + [f":(exclude){p}" for p in excludes]) if excludes else []
        diff = subprocess.run(
            ["git", "diff", "--no-renames", "--no-abbrev", f"{args.base}...HEAD"] + pathspec,
            capture_output=True, check=True,
        ).stdout
        recomputed = hashlib.sha256(diff).hexdigest()
        if m.group(1).lower() != recomputed:
            errors.append(
                "review.md diff_sha256 does not match this PR's code+contract diff "
                f"(recomputed {recomputed}) — the review is not bound to this PR (F11)")
    rounds_err = _rounds_error(text)
    if rounds_err:
        errors.append(rounds_err)
    # consulted: required when the PR touches the structural surface — the same
    # surface (and the same parser) the edit gate demands it on. impact_map stays
    # an edit-gate concern; consulted is backstopped here because a domain finding
    # surfacing in review instead of before the build is the cost this rule cuts.
    if _structural(paths) and not _consulted_present("."):
        errors.append(
            "PR touches the structural surface but contract.md has no "
            "non-placeholder `consulted:` (who was consulted before building, "
            "or 'nobody, because ...')")
    if "VERDICT: FAIL" in text:
        errors.append("review.md contains VERDICT: FAIL — unresolved findings")
    # SECONDARY (coarse) backstop only — F12/#421. The per-section loop below is the
    # AUTHORITATIVE check for unanswered escalations (it can't be fooled by an answer in a
    # different section). This global count is a cheap sanity net; keep it adjacent to the
    # per-section loop and never rely on it alone.
    if text.count("VERDICT: ESCALATE") > text.count("CPO ANSWER:"):
        errors.append("an ESCALATE verdict lacks a recorded CPO ANSWER (global backstop)")
    sections = review_sections(text)
    for name, body in sections.items():
        # per-section pairing (AUTHORITATIVE), same rule as the local commit gate: one
        # section's answer must not mask another's unanswered escalation
        if "VERDICT: ESCALATE" in body and "CPO ANSWER:" not in body:
            errors.append(
                f"section `{name}` has an ESCALATE without a CPO ANSWER in that section")

    required = set(routing.get("always") or [])
    for path in paths:
        for pattern, reviewers in (routing.get("paths") or {}).items():
            if fnmatch.fnmatch(path, pattern):
                required.update(reviewers)
    for reviewer in sorted(required):
        body = sections.get(reviewer)
        if body is None or "VERDICT:" not in body:
            errors.append(f"required reviewer `{reviewer}` has no verdict section")
        elif "VERDICT: PASS" in body:
            # bullets count only after the risks_checked: marker, mirroring
            # the local gate — stray bullets must not satisfy the quota
            _, _, risks_block = body.partition("risks_checked:")
            if len(re.findall(r"^\s*-\s+\S", risks_block, flags=re.MULTILINE)) < 2:
                errors.append(f"`{reviewer}` PASS without two named risks (no free passes)")

    if errors:
        print("check_task_artifacts: FAIL\n  - " + "\n  - ".join(errors))
        return 1
    print(f"check_task_artifacts: OK ({len(paths)} changed paths, "
          f"{len(required)} required reviewers)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
