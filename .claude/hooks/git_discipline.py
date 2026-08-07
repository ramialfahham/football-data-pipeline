#!/usr/bin/env python
"""PreToolUse(Bash) guardrail — git discipline (project-specific wording).

Checks, self-gated against the *actual* command (see _command_utils):
  1. Block agent-initiated `glab mr merge` — merging is the user's call.
  2. Block `git commit --amend` / `--no-verify` / `-n` — history integrity and
     the governance hash-chain depend on append-only, hook-verified commits
     (governance G2; flags matched on quote-stripped text so commit-message
     bodies cannot false-positive).
  3. Block `git config core.hooksPath` — repointing git hooks disables the
     repo's automation.
  4. Nudge the branch-consolidation questions on branch creation.

Fails open: any error or non-matching command exits 0 with no output.
"""

from __future__ import annotations

import os
import re
import shlex
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _command_utils import (  # noqa: E402
    bash_command,
    emit_context,
    emit_deny,
    read_event,
    simple_commands,
    strip_quoted_and_heredoc,
)

_MR_MERGE = re.compile(r"glab\s+mr\s+(?:merge|accept)\b")
_BRANCH_CREATE = re.compile(r"git\s+(?:checkout\s+-b|switch\s+(?:-c|--create))\b")
_COMMIT_FORBIDDEN = re.compile(r"(?:^|\s)(--no-verify|--amend|-n)(?=\s|$)")
# Commit-flag ALLOWLIST (CTO finding, G3 review round 2): a denylist of the
# self-staging forms (-a/-am/--include/...) is bypassable via POSIX
# short-option bundling (`-qam`) and long-option prefix abbreviation
# (`--inc`). Inverted: any flag outside this set — and any positional
# pathspec — is denied, so only `git add` + plain `git commit` can reach the
# review hash gate with reviewer-seen content.
_ALLOWED_COMMIT_FLAGS = {
    "-m", "--message", "-F", "--file",       # message (take a value)
    "-q", "--quiet", "-v", "--verbose",
    "-S", "--gpg-sign", "-s", "--signoff",
}
_COMMIT_VALUE_FLAGS = {"-m", "--message", "-F", "--file"}
_HOOKSPATH = re.compile(r"git\s+config\b.*core\.hookspath", re.IGNORECASE)

ROUTING_REL = ".claude/review_routing.json"
REVIEW_REL = ".claude/task/review.md"


def _commit_form_violation(raw: str) -> str | None:
    """Why this `git commit` command is form-denied, or None.

    Tokenizes the RAW command with shlex — the quote-stripped text erases a
    QUOTED pathspec (`git commit -m "x" "path.sql"`), which git commits as
    reviewer-unseen working-tree content (CTO finding, G3 review round 5).
    Walks the tokens after `commit`: `--` or any positional token is a
    pathspec (selects/stages content at commit time); any flag outside
    _ALLOWED_COMMIT_FLAGS is denied by default — covering -a/-am/--all,
    -i/--include, -o/--only, -p/--interactive, their bundled spellings
    (-qam) and prefix abbreviations (--inc) alike.
    """
    try:
        tokens = shlex.split(raw)
    except ValueError:
        return "unbalanced quoting"      # unparseable: fail toward deny
    try:
        i = tokens.index("commit") + 1
    except ValueError:
        return None
    while i < len(tokens):
        tok = tokens[i]
        if tok == "--":
            spec = tokens[i + 1] if i + 1 < len(tokens) else "--"
            return f"pathspec `{spec}`"
        base = tok.split("=", 1)[0]
        if base not in _ALLOWED_COMMIT_FLAGS:
            return f"flag `{tok}`" if tok.startswith("-") else f"pathspec `{tok}`"
        if base in _COMMIT_VALUE_FLAGS and "=" not in tok:
            i += 2                       # the next token is the flag's value
        else:
            i += 1
    return None


def _repo_root() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _staged_diff_bytes(root: str) -> bytes:
    import subprocess
    # F11 (#409): hash the staged diff EXCLUDING the bookkeeping artifacts, so the
    # review hash covers code + contract.md only and CI can recompute the same value
    # over `git diff base...HEAD` (it has no staging index). See _hash_exclude_pathspec.
    # --no-renames AND --no-abbrev pin the diff so the local staged hash and the CI
    # recompute (`git diff base...HEAD`) are byte-identical for identical content:
    # --no-renames removes endpoint-sensitive rename detection; --no-abbrev forces full
    # 40-hex blob SHAs in the `index` lines so the abbreviation length (which depends on
    # the repo's object count, and so differs pre- vs post-commit) cannot diverge them.
    return subprocess.run(
        ["git", "diff", "--staged", "--no-renames", "--no-abbrev"]
        + _hash_exclude_pathspec(_load_routing(root)),
        cwd=root, capture_output=True, timeout=30,
    ).stdout


def _staged_paths(root: str) -> list[str]:
    import subprocess
    # -z (NUL-split): with core.quotePath, non-ASCII paths come out quoted
    # and escaped, match no routing pattern, and would silently drop a
    # required reviewer (CTO finding, G3 review round 5).
    out = subprocess.run(
        ["git", "diff", "--staged", "--name-only", "-z"], cwd=root,
        capture_output=True, text=True, timeout=30,
    ).stdout
    return [p.replace("\\", "/") for p in out.split("\0") if p]


# STDOUT IS TWO DIFFERENT CHANNELS in this file, and conflating them corrupts an
# artifact. As a HOOK, stdout carries the JSON protocol and a canary belongs there. As a
# CLI (`--review-patch`, `--staged-hash`), stdout IS the product — the patch reviewers
# read and that gets committed. Printing a canary in CLI mode appends a JSON blob to
# `review_input.patch`. Verified by running it: the blob landed at the end of the patch,
# after the last hunk, because `print()` buffers while `sys.stdout.buffer.write()` does
# not. Found by cto-reviewer at opus, routed to platform; reproduced before fixing.
_CLI_MODE = False


def _load_routing(root: str) -> dict | None:
    """The routing config, or None when it cannot be read.

    None disables the review requirement ENTIRELY (see `_commit_gate`), so the quiet
    failure here is the most consequential in the file: a stray comma in
    `review_routing.json` switches off the blinded review cycle and nothing says so.
    A MISSING file is a legitimate state (another repo, no governance) and stays silent;
    a file that EXISTS and will not parse is a defect and announces itself — but only in
    hook mode, see `_CLI_MODE`.
    """
    import json
    path = os.path.join(root, ROUTING_REL)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as exc:
        if _CLI_MODE:
            print(
                f"WARNING: {ROUTING_REL} did not parse ({type(exc).__name__}: {exc}); "
                "review exclusions were NOT applied to this patch.",
                file=sys.stderr,
            )
            return None
        emit_context(
            "PreToolUse",
            f"⚠ REVIEW ROUTING UNREADABLE — {ROUTING_REL} exists but did not parse "
            f"({type(exc).__name__}: {exc}). The review requirement is DISABLED while this "
            "holds: no reviewer is required, no verdict is checked, and commits pass the "
            "review gate unverified. Fix the file before committing anything you expect to "
            "have been reviewed."
        )
        return None


def _required_reviewers(paths: list[str], routing: dict) -> set[str]:
    import fnmatch
    required = set(routing.get("always") or [])
    for path in paths:
        for pattern, reviewers in (routing.get("paths") or {}).items():
            if fnmatch.fnmatch(path, pattern):
                required.update(reviewers)
    return required


def _hash_exclude_pathspec(routing: dict | None) -> list[str]:
    """Git pathspec excluding the bookkeeping artifacts from the review diff
    (F11/#409): `-- . :(exclude)<path>...`. contract.md is deliberately NOT in
    hash_exclude_paths, so the review hash binds code + the authorizing contract."""
    excludes = (routing or {}).get("hash_exclude_paths") or []
    if not excludes:
        return []
    return ["--", "."] + [f":(exclude){p}" for p in excludes]


def _review_patch_bytes(root: str) -> bytes:
    """The staged diff AS THE REVIEWERS SEE IT: code and contract.md, never the review's
    own paperwork. CPO 2026-08-01 — reviewers stopped being able to fail a commit over a
    defect in the notes about the commit. This is a SEPARATE exclusion list from
    `hash_exclude_paths`: what a reviewer reads and what invalidates their verdict are
    different questions, and conflating them is what made a typo fix cost a full round.
    Used by `--review-patch`, which is how `.claude/task/review_input.patch` must be
    generated; generating it by hand is how it came to re-embed its own history."""
    routing = _load_routing(root) or {}
    excludes = routing.get("review_exclude_paths") or []
    # Reviewed CONTENT that is not pasted. Excluded from the body like `excludes`, but
    # ANNOUNCED in a manifest, because hiding it outright would silently delete
    # bi-analyst-reviewer's field-existence hunt item. See `_doc_review_summarise_paths`.
    summarise = routing.get("review_summarise_paths") or []
    all_excluded = list(excludes) + list(summarise)
    spec = (["--", "."] + [f":(exclude){p}" for p in all_excluded]) if all_excluded else []
    # CUMULATIVE vs the base branch, not just the staged increment. Every brief's
    # first input line, working_agreement §2 and agent_guardrails all promise the
    # reviewers "the cumulative branch diff vs main", and two individually clean
    # commits can cumulatively drift. `--staged` alone gives index-vs-HEAD, so on a
    # branch that already has a commit — an explicitly documented flow (§3: re-stage
    # and re-run the review cycle after an amend) — reviewers would silently receive
    # only the last increment, and nothing could detect it because review_input.patch
    # is in both exclusion lists. `git diff --staged <base>` is base-to-index, which
    # is what CI recomputes as `git diff base...HEAD` after the commit.
    body = _cumulative_diff(root, spec)
    # TWO different silences, announced differently. `summarise` paths are reviewed content
    # kept out of the body; `excludes` are the review's own paperwork, which reviewers must
    # NOT judge — but their ABSENCE was indistinguishable from never having been edited, and
    # three reviewers drew the false inference (GitLab #25). Naming them removes the
    # inference without un-excluding anything.
    return (body
            + _summary_manifest(root, summarise)
            + _excluded_trailer(root, excludes))


def _staged_stat(root: str, paths: list[str], section: str, why: str) -> str:
    """`git diff --staged --stat <base> -- <paths>`, or "" when none of them changed.

    Shared by the two announce-what-is-not-pasted sections. Written once rather than twice
    deliberately: hand-copying a matcher into a second file is an open defect in this repo
    already (`docs/roles/platform_reliability.md:33`, the reviewer-matching loop duplicated
    into `check_task_artifacts.py`), and a third copy of the same git call in the same file
    would be the same mistake with none of its excuse.

    RAISES rather than returning a narrowed result, for the reason `_cumulative_diff` and
    `_base_commit` do: a quietly shortened patch is worse than no patch.

    `section` names which of the two went missing and is a STRUCTURAL field, not prose:
    both fail-loud tests assert on it, so the reason text below can be reworded without
    silently unpinning them. (platform-reviewer at opus: the manifest test's `"manifest" in
    ...` assertion had come to depend on a `why` string happening to end with that word.)
    """
    if not paths:
        return ""
    base = _base_commit(root)
    import subprocess
    proc = subprocess.run(
        ["git", "diff", "--staged", "--stat", base, "--"] + list(paths),
        cwd=root, capture_output=True, timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"review patch {section} failed for {paths}: git diff --stat exited "
            f"{proc.returncode}. {why} Refusing to emit a patch that silently under-reports."
        )
    return proc.stdout.decode("utf-8", "replace").strip()


def _excluded_trailer(root: str, excludes: list[str]) -> bytes:
    """Names the `review_exclude_paths` files that ARE edited on this branch (GitLab #25).

    THE DEFECT IT REMOVES. Exclusion deletes a file from the patch outright, so a reviewer
    cannot tell "never edited" from "edited and deliberately hidden". Both are absence. A
    reviewer that sees a path in `scope_paths` and not in the patch reasonably concludes the
    scope is wrong or an edit is missing; both conclusions are false and both cost a round.
    It fired three times — 2026-08-03 and 2026-08-07 on `.claude/active_work.md`, 2026-08-06
    on `.claude/task/TEMPLATE.md` — and every one was withdrawn on the evidence. The
    reviewers were reasoning correctly from what they were given. It is a missing affordance.

    THIS DOES NOT UN-EXCLUDE ANYTHING. Names and line counts only, never content, so the CPO
    ruling that reviewers do not judge the review's own paperwork (2026-08-01) is untouched.
    It also cannot move the review hash: that is `_staged_diff_bytes` over
    `hash_exclude_paths`, a different function over a different list. What a reviewer READS
    and what BINDS a verdict stay separate questions.

    WHY IT RAISES, when silence here is not a coverage loss the way it is in
    `_summary_manifest`. An absent trailer is ambiguous between "no excluded file changed"
    and "the trailer broke" — and that ambiguity is the exact defect this exists to remove.
    A trailer that can silently not appear re-creates it unpredictably.

    Emits nothing when nothing matched, for the reason the manifest does: an empty section
    every time trains the reader to skip the header, and then a real one gets skipped too.
    """
    # KEYWORDS, not positions: `section` and `why` are adjacent strings, so a positional
    # swap here would leave both fail-loud tests green while the error text read backwards
    # (platform-reviewer at opus, round 2).
    stat = _staged_stat(
        root, excludes,
        section="trailer",
        why="These paths are hidden from the patch body, so continuing would leave a reviewer "
            "unable to tell an edited file from an untouched one, which is the defect this "
            "trailer exists to remove.",
    )
    if not stat:
        return b""
    header = (
        "\n"
        "# " + "=" * 76 + "\n"
        "# NOT SHOWN (review_exclude_paths) — BUT THESE FILES *ARE* EDITED\n"
        "# " + "=" * 76 + "\n"
        "# The files below changed on this branch and are DELIBERATELY kept out of the\n"
        "# diff: they are the review's own paperwork or the handover, which reviewers do\n"
        "# not judge (CPO 2026-08-01).\n"
        "#\n"
        "# THEIR ABSENCE ABOVE IS THEREFORE NOT EVIDENCE THAT A FILE WAS LEFT UNEDITED,\n"
        "# and a path that appears in `scope_paths` but not in the diff is not, by itself,\n"
        "# a scope defect. Read them directly with Read/Grep if a claim in contract.md\n"
        "# depends on one.\n"
        "#\n"
    )
    body = "".join(f"#   {ln}\n" for ln in stat.splitlines())
    return (header + body + "# " + "=" * 76 + "\n").encode("utf-8")


def _summary_manifest(root: str, summarise: list[str]) -> bytes:
    """A stat-only header for paths kept OUT of the patch body but still reviewed.

    Silence would be the dangerous outcome here: a reviewer who is never told the sample
    data changed cannot know to check it, so the payload saving would quietly cost the
    field-existence check. This says what changed, by how much, and how to read it.

    Emits nothing when nothing matched — an empty section trains readers to skip the
    header, and then a real one gets skipped too.
    """
    # FAIL LOUD, not silent. `_cumulative_diff`/`_base_commit` raise rather than return a
    # narrowed diff, for the documented reason that a quietly-shortened patch is worse
    # than no patch. The same logic applies here in the opposite direction: these files
    # were REMOVED from the body on the promise that a manifest would announce them, so
    # swallowing an error here means they are hidden with nothing said — the exact
    # coverage loss `review_summarise_paths` exists to prevent. (cto-reviewer, opus.)
    # The git call itself now lives in `_staged_stat`; the reasoning above is why the
    # `why` string below is worded as a coverage loss rather than an ambiguity.
    stat = _staged_stat(
        root, summarise,
        section="manifest",
        why="These paths are excluded from the patch body, so continuing would hide them from "
            "reviewers with nothing said about them.",
    )
    if not stat:
        return b""
    header = (
        "\n"
        "# " + "=" * 76 + "\n"
        "# NOT PASTED ABOVE, BUT IN SCOPE FOR THIS REVIEW\n"
        "# " + "=" * 76 + "\n"
        "# The files below changed and are DELIBERATELY excluded from the diff body:\n"
        "# they are generated/sample data, and pasting them has measured at ~89% of the\n"
        "# review payload. They are still reviewed content and still bind your verdict.\n"
        "#\n"
        "# READ THEM DIRECTLY with Read/Grep if your hunt items touch them. In\n"
        "# particular: whether a field displayed by a component actually EXISTS in the\n"
        "# exported sample is checked by opening these files, not by reading a diff.\n"
        "#\n"
    )
    body = "".join(f"#   {ln}\n" for ln in stat.splitlines())
    return (header + body + "# " + "=" * 76 + "\n").encode("utf-8")


def _base_commit(root: str) -> str:
    """The commit the reviewers' patch is cumulative FROM. Raises rather than
    guessing, or returns the root commit — never a base that narrows the diff.

    An earlier version returned nothing when `git merge-base HEAD main` failed and
    fell through to a bare `git diff --staged`, i.e. index-vs-HEAD, which hands
    reviewers only the last increment of a multi-commit branch. Its comment claimed
    that was safe because "no `main` means HEAD is the whole history" — FALSE
    whenever the branch already has commits, which is the normal case in: a clone
    that has only `origin/main` (the CI twin spells the base that way), a repo whose
    default branch is `master`/`develop` (these guards are written to travel to other
    repos), a `--single-branch` clone, a shallow `fetch-depth: 1` checkout, or two
    histories with no common ancestor. All three reviewers caught it.
    """
    import subprocess

    def _git(*args: str) -> tuple[int, str]:
        r = subprocess.run(["git", *args], cwd=root, capture_output=True,
                           text=True, timeout=30)
        return r.returncode, r.stdout.strip()

    for ref in ("main", "origin/main"):
        if _git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")[0] != 0:
            continue
        code, base = _git("merge-base", "HEAD", ref)
        if code == 0 and base:
            return base
        # The ref exists but shares no history with HEAD. Do not guess — a silently
        # narrower patch is the one outcome this function must never produce.
        raise RuntimeError(
            f"`{ref}` exists but has no common ancestor with HEAD, so the cumulative "
            "branch diff cannot be determined. Refusing to hand the reviewers a "
            "partial patch."
        )
    # No base branch resolves at all. Fail LARGE: diff from the root commit, which is
    # the whole history and therefore cumulative by construction.
    code, root_commit = _git("rev-list", "--max-parents=0", "HEAD")
    if code != 0 or not root_commit:
        raise RuntimeError(
            "no `main`/`origin/main` and no root commit — cannot build a cumulative "
            "reviewers' patch."
        )
    return root_commit.split("\n")[0]


def _cumulative_diff(root: str, spec: list[str]) -> bytes:
    import subprocess
    rng = [_base_commit(root)]
    r = subprocess.run(
        ["git", "diff", "--staged", "--no-renames", "--no-abbrev"] + rng + spec,
        cwd=root, capture_output=True, timeout=30,
    )
    # FAIL LOUD, never silently smaller. The documented usage redirects stdout into
    # review_input.patch, and a redirect truncates its target BEFORE the process runs —
    # so returning empty bytes on a git error leaves a zero-byte patch that reads to a
    # reviewer as "nothing changed" rather than as a failure. Unlike the staged hash,
    # which CI recomputes and compares, nothing downstream can detect a truncated patch:
    # review_input.patch is in both hash_exclude_paths and review_exclude_paths.
    # Reviewer input may fail loud or fail LARGE (a malformed routing file yields no
    # exclusions and hands over the whole diff), never quietly narrower.
    if r.returncode != 0:
        raise RuntimeError(
            "git diff failed while building the reviewers' patch: "
            + (r.stderr.decode("utf-8", "replace").strip() or f"exit {r.returncode}")
        )
    return r.stdout


def _artifact_only(paths: list[str], routing: dict) -> bool:
    import fnmatch
    # F10 (#409): contract.md authorizes which code may be edited, so a commit that
    # touches it is NEVER review-exempt — even though it matches the artifact_only glob.
    never = routing.get("artifact_only_never") or []
    if any(fnmatch.fnmatch(p, pat) for p in paths for pat in never):
        return False
    pats = routing.get("artifact_only") or []
    return bool(paths) and all(
        any(fnmatch.fnmatch(p, pat) for pat in pats) for p in paths
    )


def _review_sections(text: str) -> dict[str, str]:
    """Map '## section' name -> section body. Text before the first header is
    kept as the `_preamble` pseudo-section so an ESCALATE written there cannot
    escape the per-section pairing (CTO finding, G3 review round 4)."""
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


ROUND_CAP = 3


def _rounds_gate(text: str) -> str | None:
    """Reason to deny on the review-round count, or None.

    Every review round used to re-run every reviewer over the whole diff with no
    bound on the loop; a nine-round PR was the result (CPO 2026-07-22: the process
    "has to be more economic"). `review.md` must declare `rounds: N`, and past the
    cap the builder STOPS and brings the open findings to the CPO instead of
    grinding a round 4, 5, 6. To proceed past the cap anyway (the CPO said keep
    going) the review must carry a `rounds_cap_override:` line with that reason —
    a real sentence, not a bare marker.
    """
    # `[^\S\n]*` = horizontal whitespace only, so a keyless `rounds:` cannot swallow
    # the NEXT line as its value (an empty `rounds_cap_override:` used to capture the
    # following `## header` and read as a real reason — cto-reviewer, 2026-07-22).
    m = re.search(r"^[^\S\n]*rounds:[^\S\n]*(.+)$", text, flags=re.MULTILINE)
    if not m:
        return (
            "REVIEW GATE: review.md has no `rounds:` line. Record how many review "
            "rounds this branch has taken (rounds: 1 on the first), so the loop is "
            "bounded. See .claude/task/REVIEW_TEMPLATE.md."
        )
    raw = m.group(1).strip()
    if not raw.isdigit() or int(raw) < 1:
        return (
            f"REVIEW GATE: `rounds: {raw}` is not a positive integer. It counts the "
            "review rounds this branch has taken (1 on the first)."
        )
    if int(raw) > ROUND_CAP:
        ov = re.search(r"^[^\S\n]*rounds_cap_override:[^\S\n]*(.+)$", text,
                       flags=re.MULTILINE)
        reason = ov.group(1).strip() if ov else ""
        if not reason or _is_placeholder(reason):
            return (
                f"REVIEW GATE: {raw} review rounds exceeds the cap of {ROUND_CAP}. "
                "STOP and bring the open findings to the CPO rather than looping. "
                "If the CPO says continue, record it as `rounds_cap_override: "
                "<their reason>` in review.md, then commit."
            )
    return None


# Kept EQUAL to task_contract_gate._NULLISH so the round-cap override and the
# contract fields reject the same nullish words — `(none)` was missing here and
# present there, the exact one-copy-got-the-fix drift the cto flagged. A parity
# test (test_governance_hooks) asserts the two sets are identical, so a future
# edit to one fails until the other matches.
_NULLISH_WORDS = frozenset(
    {"none", "(none)", "n/a", "na", "tbd", "-", "todo", "?"})


def _is_placeholder(s: str) -> bool:
    s = s.strip().lower()
    return (not s) or s in _NULLISH_WORDS or (
        s.startswith("<") and s.endswith(">"))


ACCEPTANCE_TRIGGER = "site_v2/src/"
CRITERIA_REL = ".claude/task/contract.md"
EVIDENCE_REL = ".claude/task/acceptance_evidence.md"


def _bullets(block: str) -> list[str]:
    """Non-placeholder `- ` items in a block.

    A STRICTER variant of the risks_checked counter below, not a mirror of it — an
    earlier comment claimed otherwise and was wrong (cto-reviewer, 2026-07-31).
    Two real differences: `[^\\S\\n]` is horizontal whitespace only, where the
    risks counter's `\\s` crosses newlines (the class already fixed once in
    `_rounds_gate`); and this rejects nullish words and `<placeholders>`, which the
    risks counter does not. Consequence, stated so nobody trips on it: `- none`
    satisfies the PASS risks quota but not the acceptance quota. Tightening the
    risks counter would change an existing gate's behaviour and belongs in its own
    task."""
    out = []
    for line in re.findall(r"^[^\S\n]*-[^\S\n]+(\S.*)$", block, flags=re.MULTILINE):
        item = line.strip()
        if item.lower() in _NULLISH_WORDS or (item.startswith("<") and item.endswith(">")):
            continue
        out.append(item)
    return out


# An evidence line shorter than this cannot carry a reading of built output. Not a
# quality bar, just a floor under "checked".
_MIN_EVIDENCE_CHARS = 15


def _block(text: str, key: str) -> str:
    """The indented body under a top-level `key:` in a contract-style file.
    Ends at the next non-indented, non-empty line — same rule the contract gate
    uses, so the two parsers cannot disagree about where a block stops."""
    lines, keep, buf = text.splitlines(), False, []
    for line in lines:
        if re.match(rf"^{re.escape(key)}[^\S\n]*:", line):
            keep = True
            continue
        if keep:
            if line.strip() and not line.startswith((" ", "\t")):
                break
            buf.append(line)
    return "\n".join(buf)


def _acceptance_gate(root: str, paths: list[str]) -> str | None:
    """Reason to deny on missing acceptance evidence, or None (#868, 2026-07-31).

    The CPO's ruling: Quality Assurance exists as a required EVIDENCE ARTIFACT
    with a gate, not as a reviewer agent — "this check needs proof, not
    judgement". Every reviewer reads the diff and asks whether the code is
    right; none asked whether the finished thing does what the ticket asked. The
    player Overview built, passed both reviewers, and still opened on the wrong
    season, because nobody was looking at that question.

    TRIGGER is narrow on purpose: only a diff touching `site_v2/src/` — the
    user-facing surface where that failure happened. A guard that cries wolf
    gets ignored (see review_routing.json's own _doc), so this does not fire on
    warehouse, ingestion or tooling work. Widening it is a CPO decision.

    The criteria live in the contract and the CPO approves them BEFORE any code;
    the lock is the mechanism, not the authorship (ruling 2). This gate cannot
    verify that they were approved in advance — that is the honest limit — but
    it CAN refuse a commit where a declared criterion was never demonstrated,
    which is what stops criteria being softened at round three.
    """
    if not any(p.startswith(ACCEPTANCE_TRIGGER) for p in paths):
        return None
    contract = os.path.join(root, CRITERIA_REL)
    if not os.path.isfile(contract):
        return None                      # no contract: the contract gate owns that
    criteria = _bullets(_block(
        open(contract, encoding="utf-8", errors="replace").read(), "acceptance_criteria"))
    if not criteria:
        return (
            "ACCEPTANCE GATE: this diff changes the user-facing surface "
            f"(`{ACCEPTANCE_TRIGGER}`) and the contract declares no "
            "`acceptance_criteria:`. Write them as testable statements, get the "
            "CPO's approval BEFORE building, and they are locked after that "
            "(CPO ruling 2026-07-31, #868). Reviewers check whether the code is "
            "right; nothing else checks whether it does what was asked."
        )
    evidence_path = os.path.join(root, EVIDENCE_REL)
    if not os.path.isfile(evidence_path):
        return (
            f"ACCEPTANCE GATE: {EVIDENCE_REL} is missing. Demonstrate each of the "
            f"{len(criteria)} acceptance criteria against the BUILT output (never "
            "source, never outerHTML — both have certified a defect as fixed while "
            "it was still shipping) under a `criteria_demonstrated:` marker."
        )
    shown = _bullets(_block(
        open(evidence_path, encoding="utf-8", errors="replace").read(),
        "criteria_demonstrated"))
    substantive = [s for s in shown if len(s) >= _MIN_EVIDENCE_CHARS]
    if len(substantive) < len(criteria):
        # Say WHY a line did not count. A gate that reports "1 demonstrated" when
        # the builder wrote 2 looks buggy and gets worked around rather than
        # answered (the _deny_missing_impact_map lesson, cto-reviewer 2026-07-22).
        dropped = len(shown) - len(substantive)
        detail = (f" {dropped} line(s) were too short to be a reading of built "
                  f"output (under {_MIN_EVIDENCE_CHARS} characters)." if dropped else "")
        return (
            f"ACCEPTANCE GATE: {len(criteria)} acceptance criteria declared, "
            f"{len(substantive)} demonstrated in {EVIDENCE_REL}.{detail} Every criterion "
            "needs its own evidence line read from the built output. An undemonstrated "
            "criterion is an unverified claim."
        )
    # A count is a floor, not proof: two bullets both reading "checked" satisfy it.
    # Identical lines mean one criterion was demonstrated twice and another not at
    # all (cto-reviewer, 2026-07-31: "read by a bullet counter").
    lowered = [s.lower() for s in substantive]
    if len(set(lowered)) < len(lowered):
        dupes = sorted({s for s in lowered if lowered.count(s) > 1})
        return (
            f"ACCEPTANCE GATE: {EVIDENCE_REL} repeats identical evidence lines "
            f"({dupes[:2]}). Each criterion needs its OWN reading of the built "
            "output; a repeated line means one criterion went undemonstrated."
        )
    return None


def _commit_gate(root: str) -> str | None:
    """Reason to deny the commit, or None when the gate passes (governance G3)."""
    import hashlib
    paths = _staged_paths(root)
    if not paths:
        return None                      # nothing staged: let git complain
    routing = _load_routing(root)
    if routing is None:
        return None                      # no routing file: gate not active (fail open)
    if _artifact_only(paths, routing):
        return None                      # bookkeeping commit: exempt
    acceptance_msg = _acceptance_gate(root, paths)
    if acceptance_msg:
        return acceptance_msg
    review_path = os.path.join(root, REVIEW_REL)
    if not os.path.isfile(review_path):
        return (
            "REVIEW GATE: no review artifact. Run the review cycle first "
            "(stage -> blinded reviewers -> write .claude/task/review.md per "
            ".claude/task/REVIEW_TEMPLATE.md), then commit."
        )
    text = open(review_path, encoding="utf-8", errors="replace").read()
    m = re.search(r"diff_sha256:\s*([0-9a-fA-F]{64})", text)
    live = hashlib.sha256(_staged_diff_bytes(root)).hexdigest()
    if not m or m.group(1).lower() != live:
        return (
            "REVIEW GATE: staged diff has changed since the reviewers ran "
            "(hash mismatch). Re-run the reviewers against the current staged "
            f"diff and update review.md (live hash: {live})."
        )
    rounds_msg = _rounds_gate(text)
    if rounds_msg:
        return rounds_msg
    if "VERDICT: FAIL" in text:
        return "REVIEW GATE: a reviewer verdict is FAIL. Fix the findings and re-run the cycle."
    if text.count("VERDICT: ESCALATE") > text.count("CPO ANSWER:"):
        return (
            "REVIEW GATE: an ESCALATE verdict has no recorded CPO ANSWER. "
            "Escalate blinded (working_agreement.md §11), record the answer "
            "in review.md, then commit."
        )
    sections = _review_sections(text)
    for name, body in sections.items():
        # per-section pairing: one CPO answer elsewhere must not mask another
        # unanswered escalation (scope-auditor boundary note, G3 first review)
        if "VERDICT: ESCALATE" in body and "CPO ANSWER:" not in body:
            return (
                f"REVIEW GATE: section `{name}` carries an ESCALATE without a "
                "CPO ANSWER in that section. Record the answer next to the "
                "question, then commit."
            )
    for reviewer in sorted(_required_reviewers(paths, routing)):
        body = sections.get(reviewer)
        if body is None or ("VERDICT:" not in body):
            return (
                f"REVIEW GATE: required reviewer `{reviewer}` has no verdict for "
                "the staged paths (see .claude/review_routing.json). Run it and "
                "record its section in review.md."
            )
        if "VERDICT: PASS" in body:
            # A PASS must say what was EXAMINED. It need not name a defect.
            #
            # This floor was 2 until 2026-08-01, on the theory that a reviewer with no
            # findings was not looking hard enough. The effect was the opposite: given a
            # correct diff, a reviewer REQUIRED to produce two findings produces two, and
            # what it finds is prose. #370 ran twelve rounds, of which 6-12 found nothing
            # a visitor would see. CPO ruling: "Of course, the reviewer needs to have the
            # critical attitude but it's allowed to approve and not invent some finding."
            #
            # The floor is 1, not 0, deliberately: 0 permits a bare `VERDICT: PASS` with
            # nothing behind it, which is the rubber stamp the original rule was written
            # to prevent. One entry keeps a reviewer accountable for having looked.
            # Count only entries after the marker — a stray bullet list above it must not
            # satisfy the floor (CTO, G3 round 3).
            _, _, risks_block = body.partition("risks_checked:")
            risks = re.findall(r"^\s*-\s+\S", risks_block, flags=re.MULTILINE)
            if len(risks) < 1:
                return (
                    f"REVIEW GATE: `{reviewer}` PASS with nothing under "
                    "`risks_checked:` — a pass must state what was examined, even "
                    "when it found nothing. Re-run the reviewer."
                )
    return None


def main() -> int:
    global _CLI_MODE
    # Set BEFORE any branch that can reach `_load_routing`, so stdout stays pure for
    # whichever CLI product follows.
    _CLI_MODE = "--staged-hash" in sys.argv or "--review-patch" in sys.argv
    if "--staged-hash" in sys.argv:
        import hashlib
        print(hashlib.sha256(_staged_diff_bytes(_repo_root())).hexdigest())
        return 0
    if "--review-patch" in sys.argv:
        sys.stdout.buffer.write(_review_patch_bytes(_repo_root()))
        return 0
    cmd = bash_command(read_event())
    if not cmd:
        return 0
    stripped = strip_quoted_and_heredoc(cmd)
    parts = list(simple_commands(cmd))
    stripped_parts = list(simple_commands(stripped))

    for part in parts:
        if _MR_MERGE.match(part):
            emit_deny(
                "MERGE BLOCKED: `glab mr merge` is the user's action, not the agent's. "
                "Open the MR, get CI green, and stop — the user merges. "
                "(Only proceed if the user explicitly typed 'merge it' in this thread.) "
                "See docs/working_agreement.md §3."
            )
            return 0

    for part in stripped_parts:
        # Commit detection is token-exact and deliberately LOOSE (CTO finding,
        # G3 review round 3): enumerating git's global options (-p, -C, -c,
        # --git-dir <x>, ...) under-matches, and an unmatched spelling skips
        # the whole gate. Any `git ... commit ...` invocation enters here;
        # the form check below then requires the spelling to be exactly
        # `git commit ...` — over-triggering is fail-closed, under-triggering
        # is a gate bypass.
        tokens = part.split()
        if len(tokens) >= 2 and tokens[0] == "git" and "commit" in tokens[1:]:
            if len(stripped_parts) > 1:
                # The staged-diff hash is verified at PreToolUse time; a
                # sibling command in the same call (`git add x && git commit`)
                # would mutate the index AFTER the check and commit
                # reviewer-unseen content (CTO finding, G3 review round 4).
                emit_deny(
                    "COMMIT FORM BLOCKED: `git commit` must be the SOLE "
                    "command in the Bash call — a chained sibling command "
                    "(e.g. `git add x && git commit`) can restage content "
                    "after the review hash was verified. Run staging, review "
                    "and commit as separate calls. See "
                    "docs/working_agreement.md §2."
                )
                return 0
            flag = _COMMIT_FORBIDDEN.search(part)
            if flag:
                emit_deny(
                    f"COMMIT FLAG BLOCKED: `{flag.group(1)}` is not allowed. "
                    "`--amend` rewrites a reviewed commit (history must stay "
                    "append-only for the governance hash-chain); `--no-verify`/`-n` "
                    "skips the repo's git hooks. Make a NEW, hook-verified commit "
                    "instead. See docs/working_agreement.md §2/§3."
                )
                return 0
            if tokens[1] != "commit":
                emit_deny(
                    f"COMMIT FORM BLOCKED: `{tokens[1]}` between `git` and "
                    "`commit` — git global options can repoint or repage the "
                    "invocation past the review gate, so the only allowed "
                    "spelling is exactly `git commit ...`. (If this was not a "
                    "commit command, quote the word 'commit' or use the "
                    "`--flag=value` form.) See docs/working_agreement.md §2."
                )
                return 0
            # sole-command rule above guarantees this part IS the whole call,
            # so the un-stripped `cmd` is safe to tokenize for the flag walk
            violation = _commit_form_violation(cmd)
            if violation:
                emit_deny(
                    f"COMMIT FORM BLOCKED: {violation} is outside the allowed "
                    "commit form — pathspecs and flags beyond the message/"
                    "quiet/verbose/sign set select or stage content AT COMMIT "
                    "TIME, after the review hash was computed, so the commit "
                    "would carry reviewer-unseen changes. Stage with `git add "
                    "<files>`, run the review cycle, then plain `git commit -m "
                    "...` (quoted message). See docs/working_agreement.md §2."
                )
                return 0
            try:
                reason = _commit_gate(_repo_root())
            except Exception as exc:
                # STILL FAILS OPEN — the house rule is unchanged and deliberate: a hook
                # bug must never block the user's workflow.
                #
                # What changes is the SILENCE. Before this, an exception here let the
                # commit through with NO review verification and produced a session that
                # looked completely normal — the gate's evidence is "it blocked
                # something", so a dead gate and a satisfied gate are indistinguishable.
                # Enforcement could be off for weeks and the only symptom would be the
                # absence of a message nobody was watching for.
                #
                # The risk is not hypothetical on this repo: it runs on Windows with a
                # cp1252 console default over copy full of multi-byte characters, and
                # `_load_routing` returning None on a JSON syntax error disables the
                # review requirement outright.
                reason = None
                emit_context(
                    "PreToolUse",
                    "⚠ COMMIT GATE ERRORED — THIS COMMIT WAS NOT REVIEW-VERIFIED. "
                    f"{type(exc).__name__}: {exc}. The gate failed OPEN by design, so the "
                    "commit proceeds, but NOTHING checked the reviewer verdicts or the "
                    "staged-diff hash. Do not treat this commit as reviewed. Fix the hook, "
                    "then re-run the review cycle and re-commit. CI still recomputes the "
                    "hash (scripts/check_task_artifacts.py), so this is caught on the MR."
                )
            if reason:
                emit_deny(reason)
                return 0
        if _HOOKSPATH.search(part):
            emit_deny(
                "HOOKS-PATH BLOCKED: repointing `core.hooksPath` disables the "
                "repo's git automation. Not permitted."
            )
            return 0

    for part in parts:
        if _BRANCH_CREATE.match(part):
            emit_context(
                "PreToolUse",
                "BRANCH DISCIPLINE: before branching, run `glab mr list` and ask "
                "(1) is this a hard dependency of an open MR? (2) does a separate branch buy "
                "independent reviewability or an earlier merge path? If hard-dependency AND no "
                "benefit → commit to that branch instead; otherwise a new branch is fine. "
                "Branch from `main` (never with origin/main as the tracking target, which sends "
                "pushes to main). See docs/working_agreement.md §3a.",
            )
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
