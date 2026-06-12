#!/usr/bin/env python
"""CI backstop for the governance artifacts (G3).

Local hooks can be bypassed by a misbehaving or misconfigured agent; this
check keeps the gate honest at the PR boundary. For the diff between the PR
branch and the base, it verifies (plausibility, not local-only facts — CI
cannot recompute a STAGED hash):

  - artifact-only PRs (only .claude/task/** / .claude/active_work.md) pass;
  - otherwise .claude/task/contract.md and .claude/task/review.md must exist;
  - review.md carries a well-formed 64-hex diff_sha256;
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
import json
import os
import re
import subprocess
import sys

ROUTING = ".claude/review_routing.json"
CONTRACT = ".claude/task/contract.md"
REVIEW = ".claude/task/review.md"


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
    if all(any(fnmatch.fnmatch(p, pat) for pat in artifact_pats) for p in paths):
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
    if not re.search(r"diff_sha256:\s*[0-9a-fA-F]{64}", text):
        errors.append("review.md has no well-formed diff_sha256")
    if "VERDICT: FAIL" in text:
        errors.append("review.md contains VERDICT: FAIL — unresolved findings")
    if text.count("VERDICT: ESCALATE") > text.count("CPO ANSWER:"):
        errors.append("an ESCALATE verdict lacks a recorded CPO ANSWER")
    sections = review_sections(text)
    for name, body in sections.items():
        # per-section pairing, same rule as the local commit gate: one
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
