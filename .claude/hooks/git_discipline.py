#!/usr/bin/env python
"""PreToolUse(Bash) guardrail — git discipline (project-specific wording).

Checks, self-gated against the *actual* command (see _command_utils):
  1. Block `glab mr merge` unless the MR is one the agent may merge (see _agent_merge_denial).
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
    cwd_root,
    emit_context,
    emit_deny,
    read_event,
    simple_commands,
    strip_quoted_and_heredoc,
)
from task_contract_gate import CONTRACT_NAME, CONTRACT_REL, merge_heads, task_folder  # noqa: E402

_MR_MERGE = re.compile(r"glab\s+mr\s+(?:merge|accept)\b")
_BRANCH_CREATE = re.compile(r"git\s+(?:checkout\s+-b|switch\s+(?:-c|--create))\b")
_COMMIT_FORBIDDEN = re.compile(r"(?:^|\s)(--no-verify|--amend|-n)(?=\s|$)")
# Commit-flag ALLOWLIST: a denylist of the
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
REVIEW_NAME = "review.md"


def _commit_form_violation(raw: str) -> str | None:
    """Why this `git commit` command is form-denied, or None.

    Tokenizes the RAW command with shlex — the quote-stripped text erases a
    QUOTED pathspec (`git commit -m "x" "path.sql"`), which git commits as
    reviewer-unseen working-tree content.
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


_MERGE_ALLOWED_FLAGS = {"-y", "--yes", "-d", "--remove-source-branch"}
_REMOTE = "gitlab"
_READY_SCRIPT = os.path.join("scripts", "merge_ready.py")
_CORRECTION_SEEDS = "dbt_project/seeds/*_corrections.csv"
_RESEARCH_BRANCH = "research-fix/"
# Under the harness's hook timeout (600 s): a hook the harness cancels prints no deny, and the merge runs.
MERGE_DEADLINE_SECONDS = 480
_WATCHDOG_GRACE_SECONDS = 20
_SHA = re.compile(r"[0-9a-f]{40}")


def _matching(paths: list[str], patterns: list[str]) -> list[str]:
    """The paths that match a pattern of the list. fnmatch, so `*` crosses `/`."""
    import fnmatch

    return [p for p in paths if any(fnmatch.fnmatch(p, pat) for pat in patterns)]


def _outside_allowlist(paths: list[str], allowed: list[str], excluded: list[str]) -> list[str]:
    """The paths the allowlist does not clear: every path not listed, and every excluded path."""
    cleared = set(_matching(paths, allowed)) - set(_matching(paths, excluded))
    return [p for p in paths if p not in cleared]


def _agent_merge_form(cmd: str) -> tuple[str, str] | None:
    """(MR number, head commit) when `cmd` is exactly `glab mr merge <digits> --sha <40 hex>` plus
    only the allowed flags. The whole command is read, so an env prefix or wrapper fails the form."""
    try:
        tokens = shlex.split(cmd.strip())
    except ValueError:
        return None
    if len(tokens) < 6 or tokens[:2] != ["glab", "mr"] or tokens[2] not in ("merge", "accept"):
        return None
    if not tokens[3].isdigit():
        return None
    sha = None
    rest = tokens[4:]
    while rest:
        tok = rest.pop(0)
        if tok == "--sha" and rest and sha is None:
            sha = rest.pop(0)
        elif tok.startswith("--sha=") and sha is None:
            sha = tok[len("--sha="):]
        elif tok not in _MERGE_ALLOWED_FLAGS:
            return None
    if not sha or not _SHA.fullmatch(sha):
        return None
    return tokens[3], sha


def _agent_merge_denial(iid: str, sha: str, root: str) -> str | None:
    """Why the agent may not merge this MR itself, or None when it may.

    A condition that cannot be checked counts as not met. The path list and merge_ready.py both
    come from the target branch, never from the MR, so an MR cannot change what judges it.
    """
    import json
    import shutil
    import subprocess
    import tempfile
    import threading
    import time

    deadline = time.monotonic() + MERGE_DEADLINE_SECONDS

    def expire() -> None:
        emit_deny("MERGE BLOCKED: the merge conditions were not all proven before the hook's deadline.")
        sys.stdout.flush()
        os._exit(0)

    # A child that outlives its kill can keep the hook past the harness timeout, which lets the merge run.
    watchdog = threading.Timer(MERGE_DEADLINE_SECONDS + _WATCHDOG_GRACE_SECONDS, expire)
    watchdog.daemon = True
    watchdog.start()

    def run(cmd: list[str], cap: int) -> subprocess.CompletedProcess:
        left = deadline - time.monotonic()
        if left <= 0:
            raise subprocess.TimeoutExpired(cmd, 0)
        return subprocess.run(cmd, cwd=root, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=min(cap, left))

    try:
        r = run(["glab", "api", f"projects/:id/merge_requests/{iid}"], 60)
        if r.returncode != 0:
            return f"the MR could not be read: {r.stderr.strip()[:200]}"
        mr = json.loads(r.stdout)
        if mr.get("state") != "opened" or mr.get("target_branch") != "main":
            return f"MR !{iid} is not an open MR into main"
        pipeline = mr.get("head_pipeline") or {}
        if pipeline.get("status") != "success" or pipeline.get("source") != "merge_request_event":
            return f"the head pipeline of MR !{iid} is not a green merge request pipeline"
        head = str(mr.get("sha", ""))
        if not _SHA.fullmatch(head):
            return f"MR !{iid} has no head commit"
        if head != sha:
            return f"--sha is not the head commit of MR !{iid}"
        r = run(["git", "fetch", "--quiet", _REMOTE, "main", f"refs/merge-requests/{iid}/head"], 120)
        if r.returncode != 0:
            return f"the MR head could not be fetched: {r.stderr.strip()[:200]}"
        r = run(["git", "show", f"{_REMOTE}/main:{ROUTING_REL}"], 30)
        if r.returncode != 0:
            return f"{ROUTING_REL} could not be read on {_REMOTE}/main"
        routing = json.loads(r.stdout)
        allowed, excluded = routing.get("agent_merge_paths"), routing.get("agent_merge_except")
        if not all(isinstance(v, list) and all(isinstance(p, str) and p for p in v) for v in (allowed, excluded)):
            return f"{ROUTING_REL} on {_REMOTE}/main holds no usable `agent_merge_paths` and `agent_merge_except`"
        if not allowed:
            return f"{ROUTING_REL} on {_REMOTE}/main lists no path the agent may merge"
        r = run(["git", "diff", "--name-only", "-z", "--no-renames", f"{_REMOTE}/main...{head}"], 60)
        if r.returncode != 0:
            return f"the diff of MR !{iid} could not be read: {r.stderr.strip()[:200]}"
        paths = [p for p in r.stdout.split("\0") if p]
        if not paths:
            return f"MR !{iid} changes nothing"
        outside = _outside_allowlist(paths, allowed, excluded)
        if outside:
            return f"MR !{iid} touches paths outside the agent-merge list, so the CPO merges it: {', '.join(outside[:5])}"
        seeds = _matching(paths, [_CORRECTION_SEEDS])
        if seeds and not str(mr.get("source_branch", "")).startswith(_RESEARCH_BRANCH):
            return (f"MR !{iid} changes correction seeds ({', '.join(seeds[:3])}) outside a "
                    f"`{_RESEARCH_BRANCH}*` branch, the only branch whose pipeline checks their rows")
        work = tempfile.mkdtemp(prefix="agent_merge_")
        tree = os.path.join(work, "main")
        try:
            r = run(["git", "worktree", "add", "--detach", "--quiet", tree, f"{_REMOTE}/main"], 120)
            if r.returncode != 0:
                return f"{_REMOTE}/main could not be checked out: {r.stderr.strip()[:200]}"
            r = run([sys.executable, os.path.join(tree, _READY_SCRIPT), iid], 420)
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", tree], cwd=root, capture_output=True, timeout=60)
            shutil.rmtree(work, ignore_errors=True)
        if r.returncode != 0:
            return f"MR !{iid} is not ready to merge:\n{(r.stdout + r.stderr).strip()[:800]}"
    except Exception as exc:
        return f"the merge conditions could not be checked ({type(exc).__name__}: {exc})"
    finally:
        watchdog.cancel()
    return None


def _staged_diff_bytes(root: str) -> bytes | None:
    """The bytes the review hash covers: CONTENT IDENTITY of the cumulative branch diff,
    excluding the bookkeeping artifacts (F11/#409, see _hash_exclude_pathspec).

    ⚠ `--raw`, NOT the rendered patch (#63). The old form hashed `git diff`'s human-readable
    output, which is a PRESENTATION format: its bytes depend on git version, platform and diff
    settings, so the same content hashed two ways on two machines and `validate:governance` could
    not pass at all — measured on one machine, identical commits, `-U3` -> 0c1ef8af and `-U0` ->
    ca1afb7d. `--raw` emits `:mode mode <blobA> <blobB> STATUS<TAB>path`; blob SHAs ARE content
    hashes, identical everywhere and forever. No discriminating power is lost — a rendered patch is
    DERIVED from those blobs and cannot differ unless a blob SHA does — and mode changes and
    add/delete/modify status are carried explicitly.

    ⚠ CUMULATIVE FROM THE BASE, not `--staged` alone (#63, second half). The CI twin recomputes
    `git diff base...HEAD`; a bare `--staged` is HEAD-vs-index, i.e. only the LAST increment, so on
    a multi-commit branch the two compared different diffs by construction. That was a documented
    trap ("on a SECOND commit, `--staged-hash` is the WRONG number") rather than a mystery, and it
    is now simply false. `_cumulative_diff` already resolves the base correctly — reused here so
    there is exactly one base resolver.

    ⚠ MUST NOT RAISE, and MUST NOT return b"" on failure. `_commit_gate`'s caller FAILS OPEN on
    exception by deliberate house rule (see the handler at the bottom of this file), so an escaping
    exception would wave a commit through unverified. But returning b"" is WORSE, not safer, and an
    earlier draft of this function did exactly that while claiming to be fail-closed:

      `--staged-hash` would print sha256(b"") = e3b0c442… with EXIT 0; the builder pastes that into
      `review.md`; the gate recomputes it from the same broken call, gets the same value, and the
      two AGREE. The commit passes with a binding that covers ZERO bytes — no code, not even
      `contract.md`. Deterministic, not a race: both calls run seconds apart in the same state.
      Reproduced before fixing.

    So failure returns **None**, which is distinguishable from a genuinely empty diff, and BOTH
    callers must handle it: the CLI refuses to emit a hash it could not compute (stderr, non-zero
    exit) and the gate denies with its own message. The states that reach it are the ones
    `_base_commit` already names — a `--single-branch` clone, a shallow checkout, two histories
    with no common ancestor — and these hooks travel to other repos by design.
    """
    try:
        return _cumulative_diff(root, _hash_exclude_pathspec(_load_routing(root)), raw=True)
    except Exception:
        return None


def _staged_paths(root: str) -> list[str]:
    import subprocess
    # -z (NUL-split): with core.quotePath, non-ASCII paths come out quoted
    # and escaped, match no routing pattern, and would silently drop a
    # required reviewer.
    # During a merge, HEAD is the pre-merge tip, so the paths come from the merge result's base.
    base = []
    if merge_heads(root):
        try:
            base = [_base_commit(root)]
        except Exception:
            base = []
    out = subprocess.run(
        ["git", "diff", "--staged", "--name-only", "-z", *base], cwd=root,
        capture_output=True, text=True, timeout=30,
    ).stdout
    return [p.replace("\\", "/") for p in out.split("\0") if p]


# STDOUT IS TWO DIFFERENT CHANNELS in this file, and conflating them corrupts an
# artifact. As a HOOK, stdout carries the JSON protocol and a canary belongs there. As a
# CLI (`--review-patch`, `--staged-hash`), stdout IS the product — the patch reviewers
# read and that gets committed. Printing a canary in CLI mode appends a JSON blob to
# `review_input.patch`. Verified by running it: the blob landed at the end of the patch,
# after the last hunk, because `print()` buffers while `sys.stdout.buffer.write()` does
# not. Reproduced before fixing.
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


def _path_reviewers(path: str, routing: dict) -> set[str]:
    import fnmatch
    return {r for pattern, reviewers in (routing.get("paths") or {}).items()
            if fnmatch.fnmatch(path, pattern) for r in reviewers}


def _is_companion(path: str, routing: dict) -> bool:
    """A test or baseline outside the risk tier: it adds no reviewer to a branch that has one."""
    import fnmatch
    top = max((t.get("reviewers", 0) for t in (routing.get("tiers") or {}).values()), default=0)
    return (any(fnmatch.fnmatch(path, g) for g in routing.get("companion_paths") or [])
            and _tier_of(path, routing) < top)


def _required_reviewers(paths: list[str], routing: dict) -> set[str]:
    required = set(routing.get("always") or [])
    for path in paths:
        if not _is_companion(path, routing):
            required |= _path_reviewers(path, routing)
    if not required:
        for path in paths:
            required |= _path_reviewers(path, routing)
    return required


def _tier_of(path: str, routing: dict) -> int:
    """The reviewer count a path's tier needs: the highest matching tier, 0 for a text path."""
    import fnmatch
    return max((t.get("reviewers", 0) for t in (routing.get("tiers") or {}).values()
                if any(fnmatch.fnmatch(path, g) for g in t.get("paths") or [])), default=0)


def _tier_gate(paths: list[str], routing: dict) -> str | None:
    """Reason to deny on the review tiers (docs/working_agreement.md §2 Blinding), or None."""
    cap = routing.get("max_reviewers")
    if not routing.get("tiers") or cap is None:
        return None
    paths = [p.replace("\\", "/") for p in paths]
    for path in paths:
        want, got = _tier_of(path, routing), _path_reviewers(path, routing)
        if len(got) != want:
            return (f"REVIEW GATE: `{path}` needs {want} reviewer(s) by its tier in {ROUTING_REL}, "
                    f"and its `paths` rows give {len(got)} ({', '.join(sorted(got)) or 'none'}). "
                    "Fix its row in a governance task.")
    need = _required_reviewers(paths, routing)
    if len(need) > cap:
        return (f"REVIEW GATE: this branch needs {len(need)} reviewers ({', '.join(sorted(need))}) "
                f"and the most a branch may need is {cap}. Split it into MRs that merge one after "
                "another (docs/working_agreement.md §2).")
    return None


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
    own paperwork, so a reviewer cannot fail a commit over a defect in the notes about the
    commit. This is a SEPARATE exclusion list from
    `hash_exclude_paths`: what a reviewer reads and what invalidates their verdict are
    different questions, and conflating them is what made a typo fix cost a full round.
    Used by `--review-patch`, which is how the task folder's `review_input.patch` must be
    generated; generating it by hand is how it came to re-embed its own history."""
    routing = _load_routing(root) or {}
    excludes = routing.get("review_exclude_paths") or []
    # Reviewed CONTENT that is not pasted. Excluded from the body like `excludes`, but
    # ANNOUNCED in a manifest, because hiding it outright would silently delete
    # the display-contract review's field-existence hunt item. See `_doc_review_summarise_paths`.
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
    silently unpinning them. (The manifest test's `"manifest" in ...` assertion had once come
    to depend on a `why` string happening to end with that word.)
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
    It fired three times on this repo's own handover and template edits, and every one was
    withdrawn on the evidence. The reviewers were reasoning correctly from what they were
    given. It is a missing affordance.

    THIS DOES NOT UN-EXCLUDE ANYTHING. Names and line counts only, never content, so the rule
    that reviewers do not judge the review's own paperwork is untouched.
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
    # swap here would leave both fail-loud tests green while the error text read backwards.
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
    # coverage loss `review_summarise_paths` exists to prevent.
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
    histories with no common ancestor.
    """
    import subprocess

    def _git(*args: str) -> tuple[int, str]:
        r = subprocess.run(["git", *args], cwd=root, capture_output=True,
                           text=True, timeout=30)
        return r.returncode, r.stdout.strip()

    # During a merge, the base of the merge result: what CI diffs from once the merge is committed.
    heads = merge_heads(root)

    # ⚠ GOVERNANCE_BASE FIRST — the escape hatch, and it must exist because the gate now DENIES
    # when the base cannot be resolved (#63). An earlier draft's deny message told the operator to
    # "set GOVERNANCE_BASE" while this function read no environment variable at all: half the
    # stated remedy was fictional, and for two histories with no common ancestor the other half
    # (fetch the base branch) does not help either, because the ref already resolves and it is the
    # missing ancestor that fails. That left `git commit` locked with no way out — exactly the
    # workflow lock the fail-open house rule exists to prevent.
    # `scripts/check_task_artifacts.py:106` already honours it, so this also closes a local/CI
    # asymmetry rather than only unblocking the operator.
    env_base = os.environ.get("GOVERNANCE_BASE")
    if env_base:
        code, resolved = _git("rev-parse", "--verify", "--quiet", f"{env_base}^{{commit}}")
        if code != 0 or not resolved:
            raise RuntimeError(
                f"GOVERNANCE_BASE={env_base!r} does not resolve to a commit. It is an explicit "
                "override, so a bad value is an error rather than something to fall back from — "
                "falling back would silently hash a different diff than the one asked for."
            )
        # ⚠ MERGE-BASE, NOT THE TIP. The CI twin spells this `f"{args.base}...HEAD"` — three-dot,
        # i.e. the common ancestor — so resolving the override to a branch TIP makes the two halves
        # hash different things the moment that branch has moved on, which is the documented use of
        # the variable. The local diff would then carry the branch's own changes PLUS a reverse
        # delta for everything merged upstream since the branch was cut: a red pipeline on a
        # correct branch, and a reviewers' patch full of already-merged work. That is precisely the
        # defect the merge-base logic exists to remove, and an escape hatch that reads the ref
        # directly reintroduces it. Every other base path in the repo is merge-based, including
        # the ref loop below.
        code, base = _git("merge-base", resolved, "HEAD", *heads)
        if code == 0 and base:
            return base
        raise RuntimeError(
            f"GOVERNANCE_BASE={env_base!r} resolves to {resolved[:12]} but shares no history with "
            "HEAD, so there is no common ancestor to diff from. Do not guess — a silently "
            "different base is the failure this override exists to prevent."
        )

    # ⚠ REMOTE-TRACKING REFS FIRST, LOCAL `main` LAST (#63). A local `main` branch is a cached
    # copy that goes stale the moment someone branches from `gitlab/main` without checking main
    # out — which is the normal flow here. Found by this task: local `main` sat at 57175fc while
    # `gitlab/main` was a2b4184 (two merges newer), so the hook resolved a base two commits behind
    # CI's, the reviewers' patch showed files from an ALREADY-MERGED task, and the hash could not
    # possibly match the CI recompute. `scripts/check_task_artifacts.py::default_base` already
    # prefers the live remote for exactly this reason and explains that `origin` is the dormant
    # GitHub one here; this is the same ordering, so the two halves agree on the base as well as
    # on the bytes. Both must hold or the pair is still broken.
    for ref in ("gitlab/main", "origin/main", "main"):
        if _git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")[0] != 0:
            continue
        code, base = _git("merge-base", ref, "HEAD", *heads)
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


def _cumulative_diff(root: str, spec: list[str], raw: bool = False) -> bytes:
    """The branch's cumulative staged diff, from the base.

    `raw=True` asks for `--raw` (mode, blob SHAs, status, path) instead of the rendered patch —
    used by `_staged_diff_bytes` for the review hash, where a PRESENTATION format cannot be
    hashed (#63). The reviewers' patch keeps the rendered form, because a reviewer reads it.
    One function builds the command either way, so the base resolution and the fail-loud
    behaviour cannot drift between the two callers.
    """
    import subprocess
    rng = [_base_commit(root)]
    r = subprocess.run(
        ["git", "diff", "--staged", "--no-renames", "--no-abbrev"]
        + (["--raw"] if raw else []) + rng + spec,
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
    escape the per-section pairing."""
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


ROUND_CAP = 2


def _rounds_gate(text: str) -> str | None:
    """Reason to deny on the review-round count, or None.

    An unbounded review loop re-runs every reviewer over the whole diff until
    somebody stops it; a nine-round PR was the result once, and that costs too
    much. `review.md` must declare `rounds: N`, and at the cap the work is split
    (docs/working_agreement.md §2). A further round needs a
    `rounds_cap_override:` line recording the product owner's approval
    — a real sentence, not a bare marker.
    """
    # `[^\S\n]*` = horizontal whitespace only, so a keyless `rounds:` cannot swallow
    # the NEXT line as its value (an empty `rounds_cap_override:` used to capture the
    # following `## header` and read as a real reason).
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
                f"REVIEW GATE: {raw} review rounds exceeds the cap of {ROUND_CAP}. At the cap "
                "the approach is rethought and the work is split: what passed lands, and the "
                "rest is split off into its own issue. A further round is the CPO's call; "
                "record it as `rounds_cap_override: approved in chat, <date>` in review.md, "
                "then commit."
            )
    return None


FINDING_RE = re.compile(
    r"^\[(blocking|nit)\][^\S\n]+([^:\n]+?):[^\S\n]+\S.*?[^\S\n](?:—|--|-)[^\S\n]+\S")
FIX_RE = re.compile(
    r"^\S[^|\n]*?[^\S\n]*\|[^\S\n]*sweep:[^\S\n]*\S[^|\n]*?[^\S\n]*\|"
    r"[^\S\n]*test:[^\S\n]*([^\s:|]+)(?:::\S+)?[^\S\n]*$")
TEST_PATH_RE = re.compile(
    r"^(?:tests/(?:[^/]+/)*test_[^/]+\.py|dbt_project/tests/.+\.sql"
    r"|site_v2/(?:[^/]+/)*[^/]+\.test\.mjs)$")
PROOF_RE = re.compile(r"[^\S\n]\|[^\S\n]*proof:[^\S\n]*(.*?)[^\S\n]*$")
CLOSED_RE = re.compile(
    r"^(\S+)[^\S\n]*\|[^\S\n]*([^|\n]*?)[^\S\n]*\|[^\S\n]*(.*?)[^\S\n]*$")


def _proof_error(item: str) -> str | None:
    """Why a blocking finding does not name its proof, or None (§2 Cross-Examination)."""
    if not item.startswith("[blocking]"):
        return None
    m = PROOF_RE.search(item)
    proof = m.group(1) if m else ""
    cmd = re.fullmatch(r"`([^`]+)`", proof)
    if cmd and not _is_placeholder(cmd.group(1)):
        return None
    if re.fullmatch(r"\S+", proof) and TEST_PATH_RE.match(proof.split("::", 1)[0]):
        return None
    return ("names no proof: it ends with `| proof: <test file>::<test>` or a reproduction "
            "command in backticks")


def _blocking_classes(body: str) -> set[str]:
    return {m.group(2).strip() for f in _bullets(_findings_block(body))
            if f.startswith("[blocking]") and (m := FINDING_RE.match(f))}


def _closed_pairs(text: str) -> set[tuple[str, str]]:
    """The (reviewer, class) pairs that `## closed` closes, well-formed entries only."""
    return {(m.group(1), m.group(2)) for e in _bullets(_review_sections(text).get("closed", ""))
            if (m := CLOSED_RE.match(e))}


def _closure_gate(text: str) -> str | None:
    """Reason to deny on `## closed` or on a FAIL it leaves open, or None (§2 Fix and re-review)."""
    sections = _review_sections(text)
    if text.count("VERDICT: FAIL") > sum(b.count("VERDICT: FAIL") for b in sections.values()):
        return ("REVIEW GATE: a FAIL is hidden by a second section of the same name. Give each "
                "reviewer one section.")
    for n, entry in enumerate(_bullets(sections.get("closed", "")), 1):
        m = CLOSED_RE.match(entry)
        if not m or not m.group(2):
            return (f"REVIEW GATE: `## closed` entry {n} is not "
                    "`- <reviewer> | <class> | <reason>`.")
        if _is_placeholder(m.group(3)):
            return (f"REVIEW GATE: `## closed` entry {n} gives no reason: say why the finding "
                    "does not reproduce.")
        if m.group(2) not in _blocking_classes(sections.get(m.group(1), "")):
            return (f"REVIEW GATE: `## closed` entry {n} closes no blocking finding: "
                    f"`{m.group(1)}` reports none of class `{m.group(2)}`.")
    closed = _closed_pairs(text)
    for name, body in sections.items():
        if "VERDICT: FAIL" not in body:
            continue
        found = _blocking_classes(body)
        if not found or {c for c in found if (name, c) not in closed}:
            return (f"REVIEW GATE: `{name}` is a FAIL with an open blocking finding. Fix the "
                    "findings and re-run the cycle, or close one that does not reproduce under "
                    "`## closed`.")
    return None


def _findings_block(body: str) -> str:
    """The lines under `findings:` up to the next unindented `key:` line such as `risks_checked:`."""
    lines, keep = [], False
    for line in body.splitlines():
        if re.match(r"^[^\S\n]*findings[^\S\n]*:", line):
            keep = True
        elif keep and re.match(r"^[A-Za-z_][A-Za-z_ ]*:", line):
            break
        elif keep:
            lines.append(line)
    return "\n".join(lines)


def _findings_gate(text: str, branch_paths: list[str], root: str) -> str | None:
    """Reason to deny on the findings and fixes in review.md, or None (§2 Cross-Examination)."""
    closed = _closed_pairs(text)
    for name, body in _review_sections(text).items():
        if name in ("fixes", "closed"):
            continue
        found = _bullets(_findings_block(body))
        for n, item in enumerate(found, 1):
            m = FINDING_RE.match(item)
            if not m:
                return (
                    f"REVIEW GATE: finding {n} in `{name}` is not `[blocking] <class>: <every "
                    "place> - <what goes wrong>` or the same with `[nit]`.")
            why = None if (name, m.group(2).strip()) in closed else _proof_error(item)
            if why:
                return (f"REVIEW GATE: finding {n} in `{name}` {why}. A finding without a proof "
                        "is a nit.")
        blocking = [f for f in found if f.startswith("[blocking]")]
        if "VERDICT: PASS" in body and blocking:
            return (f"REVIEW GATE: `{name}` is a PASS with a blocking finding. "
                    "A blocking finding is a FAIL.")
        if "VERDICT: FAIL" in body and not blocking:
            return (f"REVIEW GATE: `{name}` is a FAIL with no blocking finding. A nit never "
                    "fails a round: record the verdict as PASS with its nits.")
    m = re.search(r"^[^\S\n]*rounds:[^\S\n]*(\d+)[^\S\n]*$", text, flags=re.MULTILINE)
    if not m or int(m.group(1)) < 2:
        return None
    fixes = _bullets(_review_sections(text).get("fixes", ""))
    if not fixes:
        return ("REVIEW GATE: rounds: above 1 needs a `## fixes` section in review.md: "
                "`- <class> | sweep: <how every place was found> | test: <test file>::<test>`, "
                "or `- none: <why>` for a round that followed only PASS verdicts.")
    nones = [f for f in fixes if re.match(r"^none[^\S\n]*:", f, flags=re.IGNORECASE)]
    if nones:
        reason = nones[0].split(":", 1)[1]
        if len(fixes) > 1 or _is_placeholder(reason):
            return ("REVIEW GATE: a `## fixes` entry `none: <why>` stands alone and says why "
                    "the round followed only PASS verdicts.")
        return None
    for n, item in enumerate(fixes, 1):
        fm = FIX_RE.match(item)
        if not fm:
            return f"REVIEW GATE: `## fixes` entry {n} lacks its class, sweep or test."
        test = fm.group(1)
        if not TEST_PATH_RE.match(test):
            return (f"REVIEW GATE: the fix test `{test}` is not a test: it lives in "
                    "`tests/**/test_*.py`, `dbt_project/tests/**.sql` or "
                    "`site_v2/**/*.test.mjs`.")
        if test not in branch_paths or not os.path.isfile(os.path.join(root, test)):
            return (f"REVIEW GATE: the fix test `{test}` is not a file this branch changes. "
                    "Each fix comes with a test that fails before the fix.")
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
EVIDENCE_NAME = "acceptance_evidence.md"


def _bullets(block: str) -> list[str]:
    """Non-placeholder `- ` items in a block.

    A STRICTER variant of the risks_checked counter below, not a mirror of it.
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


def _acceptance_gate(root: str, paths: list[str], folder: str | None = None) -> str | None:
    """Reason to deny on missing acceptance evidence, or None.

    Quality Assurance exists as a required EVIDENCE ARTIFACT with a gate, not as
    a reviewer agent — this check needs proof, not judgement. Every reviewer
    reads the diff and asks whether the code is
    right; none asked whether the finished thing does what the ticket asked. The
    player Overview built, passed both reviewers, and still opened on the wrong
    season, because nobody was looking at that question.

    TRIGGER is narrow on purpose: only a diff touching `site_v2/src/` — the
    user-facing surface where that failure happened. A guard that cries wolf
    gets ignored (see review_routing.json's own _doc), so this does not fire on
    warehouse, ingestion or tooling work. Widening it is a product decision.

    The criteria live in the contract and the product owner approves them BEFORE
    any code; the lock is the mechanism, not the authorship. This gate cannot
    verify that they were approved in advance — that is the honest limit — but
    it CAN refuse a commit where a declared criterion was never demonstrated,
    which is what stops criteria being softened at round three.
    """
    if not any(p.startswith(ACCEPTANCE_TRIGGER) for p in paths):
        return None
    folder = folder or task_folder(root)["folder"]
    if folder is None:
        return None                      # no task folder: the contract gate owns that
    contract = os.path.join(root, folder + CONTRACT_NAME)
    if not os.path.isfile(contract):
        return None                      # no contract: the contract gate owns that
    criteria = _bullets(_block(
        open(contract, encoding="utf-8", errors="replace").read(), "acceptance_criteria"))
    if not criteria:
        return (
            "ACCEPTANCE GATE: this diff changes the user-facing surface "
            f"(`{ACCEPTANCE_TRIGGER}`) and the contract declares no "
            "`acceptance_criteria:`. Write them as testable statements, get the "
            "CPO's approval BEFORE building, and they are locked after that. "
            "Reviewers check whether the code is right; nothing else checks "
            "whether it does what was asked."
        )
    evidence_rel = folder + EVIDENCE_NAME
    evidence_path = os.path.join(root, evidence_rel)
    if not os.path.isfile(evidence_path):
        return (
            f"ACCEPTANCE GATE: {evidence_rel} is missing. Demonstrate each of the "
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
        # answered (the _deny_missing_impact_map lesson).
        dropped = len(shown) - len(substantive)
        detail = (f" {dropped} line(s) were too short to be a reading of built "
                  f"output (under {_MIN_EVIDENCE_CHARS} characters)." if dropped else "")
        return (
            f"ACCEPTANCE GATE: {len(criteria)} acceptance criteria declared, "
            f"{len(substantive)} demonstrated in {evidence_rel}.{detail} Every criterion "
            "needs its own evidence line read from the built output. An undemonstrated "
            "criterion is an unverified claim."
        )
    # A count is a floor, not proof: two bullets both reading "checked" satisfy it.
    # Identical lines mean one criterion was demonstrated twice and another not at
    # all — evidence written for a bullet counter, not a reader.
    lowered = [s.lower() for s in substantive]
    if len(set(lowered)) < len(lowered):
        dupes = sorted({s for s in lowered if lowered.count(s) > 1})
        return (
            f"ACCEPTANCE GATE: {evidence_rel} repeats identical evidence lines "
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
    state = task_folder(root)
    if state["errors"]:
        return ("TASK FOLDER GATE: " + "; ".join(state["errors"])
                + ". See docs/working_agreement.md §2.")
    if _artifact_only(paths, routing):
        return None                      # bookkeeping commit: exempt
    folder = state["folder"]
    if folder is None:
        return (
            "REVIEW GATE: this branch has no task folder, so there is no contract or review "
            f"to commit against. Write {CONTRACT_REL} first. See docs/working_agreement.md §2."
        )
    acceptance_msg = _acceptance_gate(root, paths, folder)
    if acceptance_msg:
        return acceptance_msg
    try:
        names = _cumulative_diff(root, ["--name-only", "-z"]).decode("utf-8", "replace")
    except Exception:
        return ("REVIEW GATE: the branch's changed paths could not be listed and the review hash "
                "could not be computed: the base commit did not resolve, or git diff failed. "
                "Fetch the base branch (or set GOVERNANCE_BASE) and retry.")
    branch_paths = [p.replace("\\", "/") for p in names.split("\0") if p]
    tier_msg = _tier_gate(branch_paths, routing)
    if tier_msg:
        return tier_msg
    required = _required_reviewers(branch_paths + paths, routing)
    if not required:
        return None                      # text only: no reviewer is required
    review_rel = folder + REVIEW_NAME
    review_path = os.path.join(root, review_rel)
    if not os.path.isfile(review_path):
        return (
            "REVIEW GATE: no review artifact. Run the review cycle first "
            f"(stage -> blinded reviewers -> write {review_rel} per "
            ".claude/task/REVIEW_TEMPLATE.md), then commit."
        )
    text = open(review_path, encoding="utf-8", errors="replace").read()
    m = re.search(r"diff_sha256:\s*([0-9a-fA-F]{64})", text)
    blob = _staged_diff_bytes(root)
    # ⚠ DENY EXPLICITLY when the hash could not be computed, rather than relying on a mismatch.
    # Letting this fall through to the comparison is what allowed sha256(b"") to match itself and
    # bind a review to zero bytes — reproduced, then fixed.
    #
    # ⚠ `is None`, NOT `not blob`. The two are different states and conflating them re-creates the
    # bug one level up: `None` means the diff could not be computed, while `b""` is a LEGITIMATE
    # empty cumulative diff — reachable because `_staged_paths` is HEAD-vs-index while this is
    # base-vs-index, so staging a revert of an earlier commit on the same branch arrives here with
    # staged paths and no net change. Reporting that as "the base did not resolve" names a cause
    # that was not observed. An empty diff falls through to the normal comparison, where CI
    # computes the same empty value and agrees — an honest binding to a net-zero branch.
    if blob is None:
        return (
            "REVIEW GATE: the review hash could not be computed — the base commit did not "
            "resolve, or git failed. review.md cannot be bound to a diff that does not exist. "
            "Fetch the base branch (or set GOVERNANCE_BASE), re-run "
            "`python .claude/hooks/git_discipline.py --staged-hash`, and update review.md."
        )
    live = hashlib.sha256(blob).hexdigest()
    if not m or m.group(1).lower() != live:
        return (
            "REVIEW GATE: staged diff has changed since the reviewers ran "
            "(hash mismatch). Re-run the reviewers against the current staged "
            f"diff and update review.md (live hash: {live})."
        )
    rounds_msg = _rounds_gate(text)
    if rounds_msg:
        return rounds_msg
    findings_msg = _findings_gate(text, branch_paths, root) or _closure_gate(text)
    if findings_msg:
        return findings_msg
    if text.count("VERDICT: ESCALATE") > text.count("CPO ANSWER:"):
        return (
            "REVIEW GATE: an ESCALATE verdict has no recorded CPO ANSWER. "
            "Escalate blinded (working_agreement.md §11), record the answer "
            "in review.md, then commit."
        )
    sections = _review_sections(text)
    for name, body in sections.items():
        # per-section pairing: one answered escalation elsewhere must not mask
        # another unanswered one
        if "VERDICT: ESCALATE" in body and "CPO ANSWER:" not in body:
            return (
                f"REVIEW GATE: section `{name}` carries an ESCALATE without a "
                "CPO ANSWER in that section. Record the answer next to the "
                "question, then commit."
            )
    for reviewer in sorted(required):
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
            # A floor of 2 — on the theory that a reviewer with no findings is not
            # looking hard enough — has the opposite effect: given a correct diff, a
            # reviewer REQUIRED to produce two findings produces two, and what it finds
            # is prose. One MR ran twelve rounds, of which the last seven found nothing a
            # visitor would see. A reviewer keeps a critical attitude and may approve
            # without inventing a finding.
            #
            # The floor is 1, not 0, deliberately: 0 permits a bare `VERDICT: PASS` with
            # nothing behind it, which is the rubber stamp the original rule was written
            # to prevent. One entry keeps a reviewer accountable for having looked.
            # Count only entries after the marker — a stray bullet list above it must not
            # satisfy the floor.
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
        blob = _staged_diff_bytes(cwd_root({"cwd": os.getcwd()}, _repo_root()))
        # ⚠ REFUSE TO EMIT A HASH THAT WAS NOT COMPUTED. Printing sha256(b"") here is what made
        # the earlier draft's "fail-closed" claim false: the number would be pasted into
        # review.md, the gate would recompute the same empty value, the two would agree, and the
        # commit would pass bound to nothing. A hash nobody can compute must stop the workflow
        # loudly, not resolve to a constant that always matches itself.
        # ⚠ `is None`, not `not blob` — see `_commit_gate`. A legitimately EMPTY cumulative diff
        # is a real state with a real hash, and must not be reported as a failure to compute one.
        if blob is None:
            print(
                "ERROR: could not compute the review hash. The base commit did not resolve, or "
                "git failed — so there is no diff to bind review.md to. Fetch the base branch "
                "(or set GOVERNANCE_BASE) and try again. Refusing to print a hash that would "
                "bind the review to nothing.",
                file=sys.stderr,
            )
            return 1
        print(hashlib.sha256(blob).hexdigest())
        return 0
    if "--review-patch" in sys.argv:
        sys.stdout.buffer.write(_review_patch_bytes(cwd_root({"cwd": os.getcwd()}, _repo_root())))
        return 0
    event = read_event()
    cmd = bash_command(event)
    if not cmd:
        return 0
    stripped = strip_quoted_and_heredoc(cmd)
    parts = list(simple_commands(cmd))
    stripped_parts = list(simple_commands(stripped))

    for part in parts:
        if _MR_MERGE.match(part):
            form = _agent_merge_form(cmd) if len(parts) == 1 else None
            why = _agent_merge_denial(*form, cwd_root(event, _repo_root())) if form else None
            if form and why is None:
                continue
            emit_deny(
                "MERGE BLOCKED: `glab mr merge` waits for the user, unless the MR is one the agent may merge. "
                "(Proceed if the user explicitly typed 'merge it' in this thread.) "
                "The agent may merge an MR as the sole command, in the form "
                "`glab mr merge <number> --sha <head commit> [--yes] [--remove-source-branch]`, "
                "when its pipeline is green, `scripts/merge_ready.py` says ready, and its diff "
                "touches only paths in `agent_merge_paths` of `.claude/review_routing.json` on `gitlab/main`."
                + (f" Not allowed: {why}" if why else "")
                + " See docs/working_agreement.md §3."
            )
            return 0

    for part in stripped_parts:
        # Commit detection is token-exact and deliberately LOOSE:
        # enumerating git's global options (-p, -C, -c,
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
                # reviewer-unseen content.
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
                reason = _commit_gate(cwd_root(event, _repo_root()))
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
