#!/usr/bin/env python3
"""Run jobs of .gitlab-ci.yml locally, in the job's own image, the way a merge-request pipeline runs them.

    python scripts/ci_local.py --mr                  # every offline job the MR pipeline runs for the changed files
    python scripts/ci_local.py --job validate:ui     # one job (repeat --job for more)
    python scripts/ci_local.py --mr --plan           # what would run and what is skipped, without Docker

The job's image, variables, before_script, script, needs: and rules: come from .gitlab-ci.yml at run
time, anchors and `extends` resolved, so no step is written down here and none can drift.

The tree a job runs on is a throwaway clone with LF line endings. A job that runs the `.merged_result`
step in CI gets the branch merged with the latest gitlab/main, made here by the same merge; any other
job gets the branch as it is. Uncommitted changes are part of the branch (as `git add -A` would stage
them), so the command can run before a commit. Only the artifacts named in a job's `needs:` reach it.

Data jobs run `dbt deps`, `dbt parse` and `sqlfluff lint` with the committed config. The container
holds no cloud credential, and nothing here runs `dbt build`, ingestion or a deploy; jobs that deploy
or write to a shared system are skipped and named.

Exit 0: every selected job passed. Exit 1: a job failed. Exit 2: the run could not start.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
CI_FILE = REPO / ".gitlab-ci.yml"
OUT = REPO / ".cache" / "ci_local"
CACHE_VOLUME = "fdp-ci-local-cache"
STALE_AFTER_SECONDS = 24 * 3600
WORKTREE = hashlib.sha1(str(REPO).encode("utf-8")).hexdigest()[:6]
MR_SOURCE = "merge_request_event"
TARGET_BRANCH = "main"
PROJECT_DIR = "/work"
RUN_AS = ("on_success", "always")
GLOBAL_KEYS = {"stages", "variables", "workflow", "default", "include"}
DBT_WRITES = re.compile(r"\bdbt\s+(build|run|seed|snapshot|test)\b")

RUNNER = r"""#!/bin/sh
set -u
mkdir -p /work /out /state
tar -C /src -cf - . | tar -C /work -xf -
if [ -d /needs ]; then cp -a /needs/. /work/; fi
cd /work
SH=$(command -v bash || command -v sh)
case "$SH" in */bash) FLAGS="-eo pipefail" ;; *) FLAGS="-e" ;; esac
export PIP_CACHE_DIR=/cache/pip npm_config_cache=/cache/npm PRE_COMMIT_HOME=/cache/pre-commit
pwd > /state/cwd
: > /state/env
: > /state/summary
failed=0

run_step() {
  "$SH" $FLAGS -c '
    . /state/env
    cd "$(cat /state/cwd)"
    if [ -n "$1" ]; then export "$1"; fi
    trap "pwd > /state/cwd; export -p > /state/env" EXIT
    . "$0"
  ' "$1" "${2:-}" < /dev/null
}

record() {
  label="$(grep -m1 -v '^[[:space:]]*$' "$1" | cut -c1-100)"
  echo
  echo "=== $3$(basename "$1" .sh): $label"
  start=$(date +%s)
  run_step "$1" "${2:-}"
  rc=$?
  secs=$(( $(date +%s) - start ))
  if [ $rc -eq 0 ]; then verdict=PASS; else verdict=FAIL; failed=$((failed + 1)); fi
  printf '%s  %ss  %s%s  %s\n' "$verdict" "$secs" "$3" "$(basename "$1" .sh)" "$label" >> /state/summary
  [ $rc -eq 0 ] || [ -z "${FAIL_FAST:-}" ]
}

if [ -s /steps/before.sh ]; then
  echo "=== before_script"
  run_step /steps/before.sh || { echo "before_script failed"; exit 2; }
fi
for f in /steps/[0-9]*.sh; do
  [ -e "$f" ] || break
  record "$f" "" "" || break
done
if [ -n "${FULL_SCOPE:-}" ] && [ -s /steps/fullscope.txt ]; then
  echo
  echo "=== FULL SCOPE (as a push to main runs it): the steps that branch on CI_PIPELINE_SOURCE"
  while IFS= read -r name; do
    record "/steps/$name" "CI_PIPELINE_SOURCE=push" "full " || break
  done < /steps/fullscope.txt
fi
rm -rf /out/artifacts
mkdir -p /out/artifacts
if [ -s /steps/artifacts.txt ]; then
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    for m in $p; do
      if [ -e "$m" ]; then tar -cf - "$m" | tar -C /out/artifacts -xf -; fi
    done
  done < /steps/artifacts.txt
fi
rm -f /out/dotenv.env
if [ -n "${CI_LOCAL_DOTENV:-}" ] && [ -f "$CI_LOCAL_DOTENV" ]; then cp "$CI_LOCAL_DOTENV" /out/dotenv.env; fi
echo
echo "=== SUMMARY"
cat /state/summary
echo "$failed step(s) failed"
[ $failed -eq 0 ]
"""


SQLFLUFF_OFFLINE = r"""cd "$CI_PROJECT_DIR"
skipped=$(grep -rl 'dbt_utils\.' dbt_project/models --include='*.sql' | wc -l)
echo "sqlfluff, jinja templater, the committed .sqlfluff; $skipped model(s) call dbt_utils, which only the dbt templater (BigQuery credentials) resolves, so CI lints those"
files=$(grep -rL 'dbt_utils\.' dbt_project/models --include='*.sql')
sqlfluff lint $files --templater jinja --dialect bigquery"""


class _CiLoader(yaml.SafeLoader):
    pass


_CiLoader.add_multi_constructor("!", lambda loader, suffix, node: None)


def load_ci(path: Path = CI_FILE) -> dict:
    """The CI file with anchors and `<<` resolved by YAML; `extends` is resolved by resolve_job."""
    return yaml.load(path.read_text(encoding="utf-8"), Loader=_CiLoader)


def deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def resolve_job(doc: dict, name: str, _seen: tuple[str, ...] = ()) -> dict:
    """The job as GitLab merges it: its `extends` parents merged in order, hashes deeply, the rest replaced."""
    if name not in doc or not isinstance(doc[name], dict):
        raise SystemExit("%s has no job %s" % (CI_FILE.name, name))
    if name in _seen:
        raise SystemExit("extends loop through %s" % name)
    job = doc[name]
    parents = job.get("extends") or []
    merged: dict = {}
    for parent in [parents] if isinstance(parents, str) else parents:
        merged = deep_merge(merged, resolve_job(doc, parent, _seen + (name,)))
    return deep_merge(merged, {k: v for k, v in job.items() if k != "extends"})


def job_names(doc: dict) -> list[str]:
    """Runnable jobs in file order: no hidden (`.x`) templates, no global keywords."""
    return [k for k, v in doc.items() if isinstance(v, dict) and not k.startswith(".") and k not in GLOBAL_KEYS]


def stage_rank(doc: dict, job: dict) -> int:
    stages = doc.get("stages") or []
    return stages.index(job.get("stage", "test")) if job.get("stage", "test") in stages else len(stages)


def image_of(job: dict) -> str:
    image = job.get("image")
    if not image:
        raise SystemExit("a job without an image cannot run here")
    return str(image["name"] if isinstance(image, dict) else image)


def expand(value: str, env: dict[str, str]) -> str:
    """GitLab's variable expansion: $NAME and ${NAME}, unknown names empty, $$ a literal $."""
    def sub(m: re.Match) -> str:
        if m.group(0) == "$$":
            return "$"
        return env.get(m.group(1) or m.group(2), "")
    return re.sub(r"\$\$|\$\{(\w+)\}|\$(\w+)", sub, value)


def job_env(doc: dict, job: dict, base: dict[str, str]) -> dict[str, str]:
    env = dict(base)
    for source in (doc.get("variables") or {}, job.get("variables") or {}):
        for key, value in source.items():
            env[str(key)] = expand(str(value), env)
    return env


_TOKEN = re.compile(r"""\s*(?:(\|\||&&|==|!=|=~|!~|\(|\))|\$(\w+)|"([^"]*)"|'([^']*)'|/((?:\\/|[^/])*)/(\w*)|(null))""")


def _tokens(expr: str) -> list[tuple[str, object]]:
    out, pos = [], 0
    while pos < len(expr):
        if not expr[pos:].strip():
            break
        m = _TOKEN.match(expr, pos)
        if not m:
            raise ValueError("cannot read rules:if near %r in %r" % (expr[pos:pos + 20], expr))
        op, var, dq, sq, rx, flags, null = m.groups()
        if op:
            out.append(("op", op))
        elif var:
            out.append(("var", var))
        elif dq is not None or sq is not None:
            out.append(("str", dq if dq is not None else sq))
        elif rx is not None:
            out.append(("re", re.compile(rx.replace("\\/", "/"), re.I if "i" in flags else 0)))
        else:
            out.append(("null", None))
        pos = m.end()
    return out


def eval_if(expr: str, env: dict[str, str]) -> bool:
    """A rules:if expression: variables, strings, null, regex, == != =~ !~, && ||, parentheses."""
    toks = _tokens(expr)
    pos = 0

    def peek():
        return toks[pos] if pos < len(toks) else (None, None)

    def take():
        nonlocal pos
        pos += 1
        return toks[pos - 1]

    def value(tok):
        kind, v = tok
        return env.get(v) if kind == "var" else v

    def atom():
        kind, v = peek()
        if (kind, v) == ("op", "("):
            take()
            res = or_expr()
            if take() != ("op", ")"):
                raise ValueError("missing ) in %r" % expr)
            return res
        take()
        return value((kind, v))

    def rel():
        left = atom()
        kind, op = peek()
        if kind == "op" and op in ("==", "!=", "=~", "!~"):
            take()
            right = atom()
            if op in ("==", "!="):
                same = left == right
                return same if op == "==" else not same
            hit = left is not None and right.search(left) is not None
            return hit if op == "=~" else not hit
        return bool(left) if not isinstance(left, bool) else left

    def and_expr():
        res = rel()
        while peek() == ("op", "&&"):
            take()
            res = rel() and res
        return res

    def or_expr():
        res = and_expr()
        while peek() == ("op", "||"):
            take()
            res = and_expr() or res
        return res

    result = or_expr()
    if pos != len(toks):
        raise ValueError("trailing tokens in rules:if %r" % expr)
    return bool(result)


def glob_regex(pattern: str) -> re.Pattern:
    """GitLab's changes: globs (Ruby fnmatch with FNM_PATHNAME, DOTMATCH, EXTGLOB): `*` stays inside a
    directory, `**/` spans any directories, a trailing `/**` takes everything below, `{a,b}` alternates."""
    out, i, depth = "", 0, 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("/**", i) and i + 3 == len(pattern):
            out += "/.*"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif c == "*":
            out += "[^/]*"
            i += 1
        elif c == "?":
            out += "[^/]"
            i += 1
        elif c == "{":
            out += "(?:"
            depth += 1
            i += 1
        elif c == "}" and depth:
            out += ")"
            depth -= 1
            i += 1
        elif c == "," and depth:
            out += "|"
            i += 1
        elif c == "[":
            j = pattern.find("]", i + 1)
            if j < 0:
                out += re.escape(c)
                i += 1
            else:
                out += pattern[i:j + 1]
                i = j + 1
        else:
            out += re.escape(c)
            i += 1
    return re.compile("^" + out + "$")


def changes_match(patterns, changed: list[str]) -> bool:
    paths = patterns.get("paths", []) if isinstance(patterns, dict) else patterns
    rx = [glob_regex(str(p)) for p in paths]
    return any(r.match(f) for r in rx for f in changed)


def first_rule(job: dict, env: dict[str, str], changed: list[str]) -> dict | None:
    """The first rule that matches this pipeline, None when no rule does. A job with no rules: runs
    (on_success) in every pipeline the workflow admits."""
    rules = job.get("rules")
    if rules is None:
        return {}
    for rule in rules:
        if "if" in rule and not eval_if(str(rule["if"]), env):
            continue
        if "changes" in rule and not changes_match(rule["changes"], changed):
            continue
        return rule
    return None


def rule_when(job: dict, env: dict[str, str], changed: list[str]) -> str | None:
    rule = first_rule(job, env, changed)
    return None if rule is None else str(rule.get("when", "on_success"))


def rule_variables(job: dict, env: dict[str, str], changed: list[str]) -> dict[str, str]:
    """The `variables:` of the first matching rule, which GitLab sets over the job's own."""
    rule = first_rule(job, env, changed) or {}
    return {str(k): expand(str(v), env) for k, v in (rule.get("variables") or {}).items()}


def artifact_needs(job: dict) -> list[str]:
    """The needed jobs whose artifacts the job receives: every need unless it says `artifacts: false`."""
    out = []
    for n in job.get("needs") or []:
        if isinstance(n, dict):
            if n.get("artifacts", True):
                out.append(n["job"])
        else:
            out.append(str(n))
    return out


def is_data_job(job: dict) -> bool:
    return job.get("stage") == "data" and any(DBT_WRITES.search(str(s)) for s in job.get("script", []))


def skip_reason(job: dict) -> str | None:
    """Why a job cannot run offline, or None. A data job is not skipped: it runs the offline checks."""
    if is_data_job(job):
        return None
    if job.get("id_tokens"):
        return "needs a cloud credential"
    if job.get("stage") in ("data", "deploy"):
        return "deploys or gates a shared system"
    return None


def merged_result_text(doc: dict) -> str:
    return str(doc.get(".merged_result", "")).strip()


def wants_merged_result(doc: dict, job: dict) -> bool:
    text = merged_result_text(doc)
    return bool(text) and any(str(i).strip() == text for i in list(job.get("before_script", [])) + list(job.get("script", [])))


def without(items: list, text: str) -> list[str]:
    return [str(i) for i in items if not (text and str(i).strip() == text)]


def plan_job(doc: dict, name: str) -> dict:
    """What runs for a job: image, variables, before_script and script items, artifacts, and which tree.
    A data job is replaced by its offline checks."""
    job = resolve_job(doc, name)
    merged = merged_result_text(doc)
    before = without(job.get("before_script", []), merged)
    script = without(job.get("script", []), merged)
    needs = artifact_needs(job)
    note = ""
    if is_data_job(job):
        gcp = str(doc.get(".gcp_auth", "")).strip()
        before = without(before, gcp)
        script = [
            str(doc[".dbt_profile"]),
            '(cd "$CI_PROJECT_DIR/dbt_project" && dbt deps && dbt parse)',
            SQLFLUFF_OFFLINE,
        ]
        needs = []
        note = "offline checks only: dbt parse and sqlfluff lint, no dbt build and no BigQuery"
    image = image_of(job)
    arts = job.get("artifacts") or {}
    return {
        "name": name, "job": job, "image": image, "before": before, "script": script, "needs": needs,
        "merged": wants_merged_result(doc, job), "artifact_paths": [str(p) for p in arts.get("paths", [])],
        "dotenv": (arts.get("reports") or {}).get("dotenv"), "note": note,
    }


def pipeline_env(branch_sha: str, target_sha: str, branch: str) -> dict[str, str]:
    return {
        "CI": "true", "CI_PROJECT_DIR": PROJECT_DIR, "CI_PIPELINE_SOURCE": MR_SOURCE,
        "CI_DEFAULT_BRANCH": TARGET_BRANCH, "CI_MERGE_REQUEST_TARGET_BRANCH_NAME": TARGET_BRANCH,
        "CI_MERGE_REQUEST_SOURCE_BRANCH_NAME": branch, "CI_MERGE_REQUEST_IID": "local",
        "CI_COMMIT_SHA": branch_sha, "CI_COMMIT_REF_NAME": branch,
        "CI_COMMIT_REF_SLUG": re.sub(r"[^a-z0-9]+", "-", branch.lower()).strip("-")[:63],
    }


def select_mr_jobs(doc: dict, env: dict[str, str], changed: list[str]) -> tuple[list[str], dict[str, str]]:
    """(jobs an MR pipeline runs for these changed files that can run offline, {skipped job: why})."""
    run, skipped = [], {}
    for name in job_names(doc):
        job = resolve_job(doc, name)
        if rule_when(job, env, changed) not in RUN_AS:
            continue
        why = skip_reason(job)
        if why:
            skipped[name] = why
        else:
            run.append(name)
    return run, skipped


def order_jobs(doc: dict, names: list[str]) -> list[str]:
    """The jobs and the jobs they need, a need always before its dependant, otherwise stage then file order."""
    file_order = {n: i for i, n in enumerate(job_names(doc))}
    out: list[str] = []

    def visit(n: str) -> None:
        if n in out:
            return
        for dep in plan_job(doc, n)["needs"]:
            if dep in file_order and skip_reason(resolve_job(doc, dep)) is None:
                visit(dep)
        out.append(n)

    for n in sorted(names, key=lambda x: (stage_rank(doc, resolve_job(doc, x)), file_order[x])):
        visit(n)
    return out


def write_steps(p: dict, folder: Path, full_scope: bool) -> list[Path]:
    """One file per script item, in order, `before.sh` for the before_script, LF endings; plus the list
    of artifact paths and of the steps that branch on CI_PIPELINE_SOURCE."""
    folder.mkdir(parents=True, exist_ok=True)
    for old in list(folder.glob("*.sh")) + list(folder.glob("*.txt")):
        old.unlink()
    (folder / "before.sh").write_text("".join(s.rstrip("\n") + "\n" for s in p["before"]), encoding="utf-8", newline="\n")
    files = []
    for i, step in enumerate(p["script"], start=1):
        f = folder / ("%02d.sh" % i)
        f.write_text(step.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
        files.append(f)
    (folder / "artifacts.txt").write_text("".join(a + "\n" for a in p["artifact_paths"]), encoding="utf-8", newline="\n")
    scoped = [f.name for f in files if "CI_PIPELINE_SOURCE" in f.read_text(encoding="utf-8")] if full_scope else []
    (folder / "fullscope.txt").write_text("".join(n + "\n" for n in scoped), encoding="utf-8", newline="\n")
    (folder / "runner.sh").write_text(RUNNER, encoding="utf-8", newline="\n")
    return files


def read_dotenv(path: Path) -> dict[str, str]:
    out = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    return out


def docker_command(p: dict, env: dict[str, str], tree: Path, steps: Path, out: Path, container: str,
                   needs_dir: Path | None, fail_fast: bool, full_scope: bool) -> list[str]:
    cmd = ["docker", "run", "--rm", "--init", "--name", container, "--ipc=host", "--entrypoint", "sh",
           "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "PYTHONIOENCODING=utf-8"]
    env = dict(env)
    if fail_fast:
        env["FAIL_FAST"] = "1"
    if full_scope:
        env["FULL_SCOPE"] = "1"
    if p["dotenv"]:
        env["CI_LOCAL_DOTENV"] = str(p["dotenv"])
    for k, v in sorted(env.items()):
        cmd += ["-e", "%s=%s" % (k, v)]
    cmd += ["-e", "GIT_CONFIG_COUNT=1", "-e", "GIT_CONFIG_KEY_0=safe.directory", "-e", "GIT_CONFIG_VALUE_0=*",
            "--mount", "type=bind,source=%s,target=/src,readonly" % tree,
            "--mount", "type=bind,source=%s,target=/steps,readonly" % steps,
            "--mount", "type=bind,source=%s,target=/out" % out,
            "--mount", "type=volume,source=%s,target=/cache" % CACHE_VOLUME]
    if needs_dir is not None:
        cmd += ["--mount", "type=bind,source=%s,target=/needs,readonly" % needs_dir]
    return cmd + [p["image"], "/steps/runner.sh"]


def git(repo: Path, *args: str, env: dict | None = None, check: bool = True) -> str:
    res = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8",
                         env=dict(os.environ, **(env or {})))
    if check and res.returncode != 0:
        raise SystemExit("git %s failed: %s" % (" ".join(args), (res.stderr or res.stdout).strip()))
    return res.stdout.strip()


IDENTITY = ("-c", "user.name=ci_local", "-c", "user.email=ci_local@example.invalid")


def snapshot_commit(repo: Path, scratch: Path) -> str:
    """HEAD, or when the working tree differs from it a commit of the tree as `git add -A` would stage it
    (so LF blobs, ignored files left out). The index file is a scratch one; the repository's is untouched."""
    if not git(repo, "status", "--porcelain"):
        return git(repo, "rev-parse", "HEAD")
    index = {"GIT_INDEX_FILE": str(scratch / "index")}
    git(repo, "read-tree", "HEAD", env=index)
    git(repo, "add", "-A", env=index)
    tree = git(repo, "write-tree", env=index)
    return git(repo, *IDENTITY, "commit-tree", tree, "-p", "HEAD", "-m", "ci_local snapshot")


def remote_for(repo: Path) -> str:
    remotes = git(repo, "remote").split()
    for r in remotes:
        if "gitlab" in git(repo, "remote", "get-url", r):
            return r
    if not remotes:
        raise SystemExit("this repository has no remote to take %s from" % TARGET_BRANCH)
    return remotes[0]


def changed_files(repo: Path, target_sha: str, branch_sha: str) -> list[str]:
    """The files an MR changes: old and new path of a rename both, names unquoted (NUL separated)."""
    raw = git(repo, "diff", "--name-only", "--no-renames", "-z", "%s...%s" % (target_sha, branch_sha))
    return [p for p in raw.split("\0") if p]


def long_path(path: Path | str) -> str:
    """The path in the extended-length form Windows needs past 260 characters; unchanged elsewhere."""
    if os.name != "nt":
        return str(path)
    return extended(os.path.abspath(str(path)))


def extended(absolute: str) -> str:
    prefix = "\\\\?\\"
    if absolute.startswith(prefix):
        return absolute
    if absolute.startswith("\\\\"):
        return prefix + "UNC\\" + absolute[2:]
    return prefix + absolute


def rm_tree(path: Path) -> None:
    def onerror(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    if os.path.exists(long_path(path)):
        try:
            shutil.rmtree(long_path(path), onerror=onerror)
        except OSError as exc:
            print("could not remove %s: %s" % (path, exc), file=sys.stderr)


def run_is_stale(run_id: str, now: float | None = None) -> bool:
    """A run id starts with its start time; no run lasts a day, so an older one was killed. A name that
    does not parse is not ours to judge and is left alone."""
    try:
        started = time.mktime(time.strptime(run_id[:15], "%Y%m%d-%H%M%S"))
    except ValueError:
        return False
    return (now if now is not None else time.time()) - started > STALE_AFTER_SECONDS


def prune_stale(repo: Path) -> None:
    """Trees, run folders and refs of this worktree that a killed run left behind. A run that is still
    going, including another one started in this worktree, is never touched."""
    for folder in (OUT / "trees", OUT / "runs"):
        if folder.is_dir():
            for old in folder.iterdir():
                if run_is_stale(old.name):
                    rm_tree(old)
    for line in git(repo, "for-each-ref", "--format=%(refname)", "refs/ci_local/%s/" % WORKTREE, check=False).splitlines():
        if run_is_stale(line.rsplit("/", 1)[-1]):
            git(repo, "update-ref", "-d", line, check=False)


class Trees:
    """Throwaway clones of the repository at the branch and at the merged result, built on demand."""

    def __init__(self, repo: Path, run_dir: Path, branch_sha: str, target_sha: str, ref: str):
        self.repo, self.run_dir, self.branch_sha, self.target_sha, self.ref = repo, run_dir, branch_sha, target_sha, ref
        self.made: dict[str, Path] = {}

    def get(self, merged: bool) -> Path:
        kind = "merged" if merged else "branch"
        if kind not in self.made:
            dest = self.run_dir / kind
            git(self.repo, "-c", "core.autocrlf=false", "clone", "--local", "--no-checkout", "-q", str(self.repo), str(dest))
            git(dest, "config", "core.autocrlf", "false")
            git(dest, "config", "core.eol", "lf")
            git(dest, "fetch", "-q", str(self.repo), "+%s:refs/heads/ci-branch" % self.ref,
                "+%s:refs/remotes/origin/%s" % (self.target_sha, TARGET_BRANCH))
            git(dest, "checkout", "-q", "-f", "--detach", "refs/heads/ci-branch")
            if merged:
                res = subprocess.run(["git", *IDENTITY, "merge", "--no-edit", "-q", self.target_sha], cwd=dest,
                                     capture_output=True, text=True, encoding="utf-8")
                if res.returncode != 0:
                    raise SystemExit("the branch does not merge with %s, so an MR pipeline would fail too:\n%s"
                                     % (TARGET_BRANCH, (res.stdout + res.stderr).strip()))
            self.made[kind] = dest
        return self.made[kind]


def docker_ready() -> str | None:
    if shutil.which("docker") is None:
        return "docker is not on PATH"
    if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        return "the Docker engine is not running (docker info fails)"
    return None


def container_name(run_id: str, job: str) -> str:
    return "fdp-ci-local-%s-%s-%s" % (WORKTREE, run_id, re.sub(r"[^a-z0-9]+", "-", job.lower()).strip("-"))


def collect_needs(plans: dict[str, dict], p: dict, runs: Path) -> tuple[Path | None, dict[str, str]]:
    """The artifacts (and dotenv variables) of the jobs `p` needs, assembled in one folder."""
    deps = [d for d in p["needs"] if d in plans]
    if not deps:
        return None, {}
    folder = runs / "needs" / re.sub(r"[^a-z0-9]+", "-", p["name"].lower())
    rm_tree(folder)
    folder.mkdir(parents=True)
    env: dict[str, str] = {}
    for d in deps:
        src = runs / re.sub(r"[^a-z0-9]+", "-", d.lower()) / "out"
        if (src / "artifacts").is_dir():
            shutil.copytree(long_path(src / "artifacts"), long_path(folder), dirs_exist_ok=True)
        env.update(read_dotenv(src / "dotenv.env"))
    return folder, env


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--job", action="append", default=[], metavar="NAME", help="run this job (repeatable)")
    ap.add_argument("--mr", action="store_true", help="run every offline job a merge-request pipeline runs for the changed files")
    ap.add_argument("--plan", action="store_true", help="print what would run and what is skipped; start nothing")
    ap.add_argument("--full-scope", action="store_true",
                    help="also re-run the steps that branch on CI_PIPELINE_SOURCE as a push to main runs them")
    ap.add_argument("--fail-fast", action="store_true", help="stop a job at its first failing step, as CI does (default: run every step)")
    ap.add_argument("--no-fetch", action="store_true", help="use the gitlab/main already fetched")
    ap.add_argument("--keep", action="store_true", help="keep the throwaway trees")
    args = ap.parse_args()
    if bool(args.job) == args.mr:
        ap.error("give --mr or one or more --job")

    if not args.plan and (why := docker_ready()):
        print(why, file=sys.stderr)
        return 2
    doc = load_ci()
    remote = remote_for(REPO)
    if not args.no_fetch:
        git(REPO, "fetch", "-q", remote, "+refs/heads/%s:refs/remotes/%s/%s" % (TARGET_BRANCH, remote, TARGET_BRANCH))
    target_sha = git(REPO, "rev-parse", "refs/remotes/%s/%s" % (remote, TARGET_BRANCH))

    run_id = "%s-%d" % (time.strftime("%Y%m%d-%H%M%S"), os.getpid())
    run_dir = OUT / "trees" / run_id
    if not args.plan:
        prune_stale(REPO)
    run_dir.mkdir(parents=True, exist_ok=True)
    ref = "refs/ci_local/%s/%s" % (WORKTREE, run_id)
    try:
        branch_sha = snapshot_commit(REPO, run_dir)
        git(REPO, "update-ref", ref, branch_sha)
        branch = git(REPO, "branch", "--show-current") or "detached"
        changed = changed_files(REPO, target_sha, branch_sha)
        base_env = pipeline_env(branch_sha, target_sha, branch)
        dirty = branch_sha != git(REPO, "rev-parse", "HEAD")
        print("branch %s at %s%s, merged with %s/%s at %s, %d changed file(s)"
              % (branch, branch_sha[:8], " (with uncommitted changes)" if dirty else "", remote, TARGET_BRANCH,
                 target_sha[:8], len(changed)), flush=True)

        if args.mr:
            names, skipped = select_mr_jobs(doc, base_env, changed)
        else:
            names, skipped = [], {}
            for n in args.job:
                why = skip_reason(resolve_job(doc, n))
                if why:
                    print("%s %s here" % (n, why), file=sys.stderr)
                    return 2
                names.append(n)
        order = order_jobs(doc, names)
        plans = {n: plan_job(doc, n) for n in order}
        set_by_rule = {n: rule_variables(plans[n]["job"], base_env, changed) for n in order}
        for n in order:
            p = plans[n]
            print("  run   %-24s %s%s%s%s" % (n, p["image"], "  [merged result]" if p["merged"] else "",
                                            ("  (needed by another job)" if n not in names else "")
                                            + ("  " + p["note"] if p["note"] else ""),
                                            "".join("  %s=%s" % kv for kv in sorted(set_by_rule[n].items()))))
        for n, why in skipped.items():
            print("  skip  %-24s %s" % (n, why))
        if args.plan or not order:
            return 0

        trees = Trees(REPO, run_dir, branch_sha, target_sha, ref)
        runs = OUT / "runs" / run_id
        results: list[tuple[str, str, int]] = []
        failed = set()
        for n in order:
            p = plans[n]
            bad = [d for d in p["needs"] if d in failed]
            if bad:
                results.append((n, "NOT RUN (needs failed job %s)" % bad[0], 0))
                failed.add(n)
                continue
            slug = re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")
            steps, out = runs / slug / "steps", runs / slug / "out"
            out.mkdir(parents=True, exist_ok=True)
            write_steps(p, steps, args.full_scope)
            needs_dir, extra = collect_needs(plans, p, runs)
            env = job_env(doc, p["job"], base_env)
            env.update(set_by_rule[n])
            env.update(extra)
            if p["merged"]:
                env["MR_TARGET_SHA"] = target_sha
                env["MR_TARGET_SHORT_SHA"] = target_sha[:8]
            tree = trees.get(p["merged"])
            cname = container_name(run_id, n)
            cmd = docker_command(p, env, tree, steps, out, cname, needs_dir, args.fail_fast, args.full_scope)
            print("\n########## %s (%s)" % (n, p["image"]), flush=True)
            subprocess.run(["docker", "rm", "-f", cname], capture_output=True)
            t0 = time.time()
            rc = subprocess.run(cmd, env=dict(os.environ, MSYS_NO_PATHCONV="1")).returncode
            results.append((n, "PASS" if rc == 0 else "FAIL", int(time.time() - t0)))
            if rc != 0:
                failed.add(n)

        print("\n########## ci_local summary")
        for n, verdict, secs in results:
            print("%-30s %s  %ds" % (n, verdict, secs))
        for n, why in skipped.items():
            print("%-30s SKIPPED (%s)" % (n, why))
        if failed:
            print("%d job(s) failed; output of a job's artifacts is under %s" % (len(failed), runs))
        return 1 if failed else 0
    finally:
        git(REPO, "update-ref", "-d", ref, check=False)
        if not args.keep:
            rm_tree(run_dir)


def run() -> int:
    try:
        return main()
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            return 2
        raise


if __name__ == "__main__":
    sys.exit(run())
