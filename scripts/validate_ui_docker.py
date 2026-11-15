#!/usr/bin/env python3
"""Run the `validate:ui` job of .gitlab-ci.yml locally, inside the CI image, through Docker.

The merge-request pipeline renders the built site in the Playwright image on Linux. Two of its
checks (the chart screenshot pins and the pinned gap counts) are Linux-only, and the design check
does not run on every developer machine, so a local run outside the image cannot see what CI sees.
This script takes the job's image, variables, before_script and script from .gitlab-ci.yml at run
time (no step is written down here, so none can drift) and runs them in the image against the
working tree, in the merge-request scope, with every step run to the end.

    cd site_v2 && npm run build
    python scripts/validate_ui_docker.py

The working tree is mounted read-only and copied inside the container, so generators and pip never
write into the repository. The run's artifacts (failing-page screenshots, counts.json, the chart
pins' new images) land in `.cache/validate_ui_docker/out/artifacts`.

Exit 0: every step passed. Exit 1: a step failed. Exit 2: the run could not start.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
CI_FILE = REPO / ".gitlab-ci.yml"
JOB = "validate:ui"
OUT = REPO / ".cache" / "validate_ui_docker"
PIP_VOLUME = "fdp-validate-ui-pip"
CONTAINER = "fdp-validate-ui-" + hashlib.sha1(str(REPO).encode("utf-8")).hexdigest()[:8]
MR_SOURCE = "merge_request_event"

COPY_EXCLUDES = ("./.git", "./.cache", "./.venv", "./node_modules", "./site_v2/node_modules",
                 "./.claude/worktrees", "./dbt_project/target", "./dbt_project/dbt_packages")

RUNNER = r"""#!/bin/bash
mkdir -p /work /out
tar -C /src __EXCLUDES__ -cf - . | tar -C /work -xf -
cd /work
echo "gitdir: $GIT_DIR_IN" > .git
export PIP_CACHE_DIR=/cache/pip
failed=0
summary=""
echo "=== before_script"
. /steps/before.sh || { echo "before_script failed"; exit 2; }
for f in /steps/[0-9]*.sh; do
  label="$(grep -m1 -v '^[[:space:]]*$' "$f" | cut -c1-100)"
  echo
  echo "=== $(basename "$f" .sh): $label"
  start=$(date +%s)
  bash -e "$f"
  rc=$?
  secs=$(( $(date +%s) - start ))
  if [ $rc -eq 0 ]; then verdict=PASS; else verdict=FAIL; failed=$((failed + 1)); fi
  summary="$summary$verdict  ${secs}s  $(basename "$f" .sh)  $label"$'\n'
done
if [ -z "$MR_ONLY" ]; then
  echo
  echo "=== FULL SCOPE (as a push to main runs it): the steps that branch on CI_PIPELINE_SOURCE"
  for f in $(grep -l CI_PIPELINE_SOURCE /steps/[0-9]*.sh); do
    label="$(grep -m1 -v '^[[:space:]]*$' "$f" | cut -c1-100)"
    echo
    echo "=== full $(basename "$f" .sh): $label"
    start=$(date +%s)
    CI_PIPELINE_SOURCE=push bash -e "$f"
    rc=$?
    secs=$(( $(date +%s) - start ))
    if [ $rc -eq 0 ]; then verdict=PASS; else verdict=FAIL; failed=$((failed + 1)); fi
    summary="$summary$verdict  ${secs}s  full $(basename "$f" .sh)  $label"$'\n'
  done
fi
rm -rf /out/artifacts
[ -d /work/artifacts ] && cp -r /work/artifacts /out/artifacts
echo
echo "=== SUMMARY"
printf '%s' "$summary"
echo "$failed step(s) failed"
[ $failed -eq 0 ]
"""


class _CiLoader(yaml.SafeLoader):
    pass


_CiLoader.add_multi_constructor("!", lambda loader, suffix, node: None)


def load_job(path: Path = CI_FILE, job: str = JOB) -> dict:
    """The job as GitLab merges it: anchors and `<<` resolved."""
    doc = yaml.load(path.read_text(encoding="utf-8"), Loader=_CiLoader)
    if job not in doc:
        raise SystemExit("%s has no job %s" % (path.name, job))
    return doc[job]


def steps_of(job: dict) -> tuple[list[str], list[str]]:
    """(before_script, script) as the strings GitLab hands the shell."""
    return [str(s) for s in job.get("before_script", [])], [str(s) for s in job["script"]]


def write_steps(job: dict, folder: Path) -> list[Path]:
    """One file per script item, in order, and `before.sh` for the before_script; LF endings."""
    before, script = steps_of(job)
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.sh"):
        old.unlink()
    (folder / "before.sh").write_text("\n".join(before) + "\n", encoding="utf-8", newline="\n")
    files = []
    for i, step in enumerate(script, start=1):
        f = folder / ("%02d.sh" % i)
        f.write_text(step.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
        files.append(f)
    (folder / "runner.sh").write_text(
        RUNNER.replace("__EXCLUDES__", " ".join("--exclude=%s" % e for e in COPY_EXCLUDES)),
        encoding="utf-8", newline="\n")
    return files


def docker_command(job: dict, source: str, repo: Path, steps: Path, out: Path,
                   mr_only: bool = False) -> list[str]:
    cmd = ["docker", "run", "--rm", "--init", "--name", CONTAINER, "--ipc=host",
           "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "PYTHONIOENCODING=utf-8"]
    env = {str(k): str(v) for k, v in (job.get("variables") or {}).items()}
    env["CI_PIPELINE_SOURCE"] = source
    if mr_only:
        env["MR_ONLY"] = "1"
    for k, v in sorted(env.items()):
        cmd += ["-e", "%s=%s" % (k, v)]
    common, own = git_dirs(repo)
    cmd += ["-e", "GIT_DIR_IN=%s" % own,
            "-e", "GIT_CONFIG_COUNT=1", "-e", "GIT_CONFIG_KEY_0=safe.directory", "-e", "GIT_CONFIG_VALUE_0=*",
            "--mount", "type=bind,source=%s,target=/src,readonly" % repo,
            "--mount", "type=bind,source=%s,target=/gitcommon,readonly" % common,
            "--mount", "type=bind,source=%s,target=/steps,readonly" % steps,
            "--mount", "type=bind,source=%s,target=/out" % out,
            "--mount", "type=volume,source=%s,target=/cache" % PIP_VOLUME,
            job["image"], "bash", "/steps/runner.sh"]
    return cmd


def git_dirs(repo: Path) -> tuple[Path, str]:
    """(the repository's common git directory, the working tree's git directory as it will be
    named inside the container, where the common one is mounted at /gitcommon)."""
    def git(flag: str) -> Path:
        out = subprocess.run(["git", "rev-parse", flag], cwd=repo, capture_output=True, text=True,
                             encoding="utf-8", check=True).stdout.strip()
        return (repo / out).resolve()

    common, own = git("--git-common-dir"), git("--absolute-git-dir")
    return common, "/gitcommon/" + own.relative_to(common).as_posix() if own != common else "/gitcommon"


def dist_is_stale(dist: Path, src: Path) -> str | None:
    """Why the built site is not the one for this tree, or None."""
    if not (dist / "index.html").exists() and not any(dist.glob("*/index.html")):
        return "%s holds no built site" % dist
    built = max((p.stat().st_mtime for p in dist.rglob("*.html")), default=0.0)
    newest = max((p.stat().st_mtime for p in src.rglob("*") if p.is_file()), default=0.0)
    return "%s is older than the newest file under %s" % (dist, src) if newest > built else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--mr-only", action="store_true",
                    help="skip the second pass in main's full scope (every width and language, against the full baseline)")
    ap.add_argument("--allow-stale-dist", action="store_true",
                    help="run even when site_v2/dist is older than site_v2/src")
    args = ap.parse_args()

    if shutil.which("docker") is None:
        print("docker is not on PATH", file=sys.stderr)
        return 2
    if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        print("the Docker engine is not running (docker info fails)", file=sys.stderr)
        return 2
    dist = REPO / "site_v2" / "dist"
    why = dist_is_stale(dist, REPO / "site_v2" / "src")
    if why and not args.allow_stale_dist:
        print("%s: run `cd site_v2 && npm run build` first" % why, file=sys.stderr)
        return 2

    job = load_job()
    steps = OUT / "steps"
    out = OUT / "out"
    out.mkdir(parents=True, exist_ok=True)
    n = len(write_steps(job, steps))
    print("validate:ui, %d steps, image %s, as a merge request%s"
          % (n, job["image"], "" if args.mr_only else ", then main's full scope"), flush=True)
    env = dict(os.environ, MSYS_NO_PATHCONV="1")
    cmd = docker_command(job, MR_SOURCE, REPO, steps, out, args.mr_only)
    subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True)
    return subprocess.run(cmd, env=env).returncode


if __name__ == "__main__":
    sys.exit(main())
