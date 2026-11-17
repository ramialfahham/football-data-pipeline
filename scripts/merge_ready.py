"""Is a green MR still ready to merge after main moved?

    python scripts/merge_ready.py <MR IID>

Reads the MR and its pipeline with `glab`, and the history with `git`; it writes nothing to GitLab
or to this checkout (the merge test runs in a temporary worktree that is removed afterwards).

Exit 0: ready to merge. Exit 1: not ready, with the reason. Exit 2: cannot decide.

The pipeline tests the MR merged with the target branch, and its jobs print the target commit they
merged in. If main has not moved since, the green result stands. If it has, the move matters only
when it touches the MR's files or the dbt lineage of the models the MR changes, upstream or
downstream. A move that does not is ready; one that does means the pipeline re-runs, with no new
commit.

An MR that validate:ui's rules give the full design sweep (UI_FULL_SCOPE) is not ready until that
sweep ran in its pipeline with no count off `baseline.json`.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".claude", "hooks"))

REMOTE = "gitlab"
TESTED_RE = re.compile(r"Merged result [0-9a-f]{40}: branch [0-9a-f]{40} \+ \S+ ([0-9a-f]{40})")
CROSS_CUTTING = (".gitlab-ci.yml", "requirements.txt", "requirements-dev.txt", "requirements-ui.txt",
                 "site_v2/package-lock.json", ".sqlfluff", "dbt_project/dbt_project.yml",
                 "dbt_project/packages.yml")
DBT_RUN_FILES = ("dbt_project/macros/",)
UI_JOB = "validate:ui"
FULL_SCOPE_VAR = "UI_FULL_SCOPE"
SWEEP_RE = re.compile(r"gap counts: \d+ pages counted at (\S+) px · (.*?)(\d+) off the baseline\s*$", re.M)
OFF_RE = re.compile(r"· \(baseline\) · (count (?:rose|fell) · .*)$", re.M)
DBT_DIR = "dbt_project"
MODEL_PREFIXES = ("dbt_project/models/", "dbt_project/seeds/")


class Undecided(Exception):
    pass


def run(cmd: list[str], cwd: str | None = None, check: bool = True) -> str:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise Undecided(f"`{' '.join(cmd[:3])}...` failed: {(r.stderr or r.stdout).strip()[:300]}")
    return r.stdout


def glab_json(path: str):
    return json.loads(run(["glab", "api", path]))


def tested_target_sha(trace: str) -> str | None:
    m = TESTED_RE.search(trace)
    return m.group(1) if m else None


def model_names(files: list[str]) -> list[str]:
    """The dbt model and seed names among changed files: the file stem under models/ or seeds/."""
    names = []
    for f in files:
        if f.startswith(MODEL_PREFIXES) and f.endswith((".sql", ".csv")):
            names.append(os.path.splitext(os.path.basename(f))[0])
    return sorted(set(names))


def unmapped_dbt_files(files: list[str]) -> list[str]:
    """Changed dbt files that name no model or seed (a schema.yml, a macro, a singular test), whose
    lineage `dbt ls` cannot be asked for by name."""
    return [f for f in files if f.startswith(DBT_DIR + "/")
            and not (f.startswith(MODEL_PREFIXES) and f.endswith((".sql", ".csv")))]


def lineage_paths(ls_output: str) -> set[str]:
    """Repo paths from `dbt ls --output path` lines, which are relative to the dbt project."""
    out = set()
    for line in ls_output.splitlines():
        line = line.strip().replace("\\", "/")
        if line.startswith(("models/", "seeds/", "snapshots/", "tests/", "analyses/", "macros/")):
            out.add(f"{DBT_DIR}/{line}")
    return out


def overlaps(mr_files: set[str], lineage: set[str], moved: set[str], dbt_known: bool) -> list[str]:
    """The moved files that matter to this MR, each with why."""
    hits = []
    for f in sorted(moved):
        if f in mr_files:
            hits.append(f"{f} (also changed by the MR)")
        elif f in lineage:
            hits.append(f"{f} (in the dbt lineage of the MR's models)")
        elif f in CROSS_CUTTING:
            hits.append(f"{f} (every pipeline reads it)")
        elif f.startswith(DBT_RUN_FILES) and any(x.startswith(DBT_DIR + "/") for x in mr_files):
            hits.append(f"{f} (a macro, and the MR changes dbt files)")
        elif not dbt_known and f.startswith(DBT_DIR + "/") and any(x.startswith(DBT_DIR + "/") for x in mr_files):
            hits.append(f"{f} (dbt lineage could not be read, so any dbt file counts)")
    return hits


def find_in_checkouts(toplevel: str, *rels: str) -> str | None:
    """A path under this checkout or, for a linked worktree under .claude/worktrees, under the main
    checkout that holds the untracked files (.venv, profiles.yml, dbt_packages)."""
    for rel in rels:
        for base in (toplevel, os.path.join(toplevel, "..", "..", "..")):
            p = os.path.normpath(os.path.join(base, rel))
            if os.path.exists(p):
                return p
    return None


def dbt_executable(toplevel: str) -> str | None:
    return find_in_checkouts(toplevel, ".venv/Scripts/dbt.exe", ".venv/bin/dbt") or shutil.which("dbt")


def lineage_in(worktree: str, toplevel: str, models: list[str]) -> set[str] | None:
    """The paths of every model upstream and downstream of `models`, or None if dbt cannot say."""
    if not models:
        return set()
    dbt = dbt_executable(toplevel)
    if not dbt:
        return None
    packages = find_in_checkouts(toplevel, f"{DBT_DIR}/dbt_packages")
    if packages and not os.path.isdir(os.path.join(worktree, DBT_DIR, "dbt_packages")):
        shutil.copytree(packages, os.path.join(worktree, DBT_DIR, "dbt_packages"))
    profile = find_in_checkouts(toplevel, "profiles.yml")
    if profile and not os.path.isfile(os.path.join(worktree, "profiles.yml")):
        shutil.copy(profile, os.path.join(worktree, "profiles.yml"))
    found: set[str] = set()
    for pattern in ("{}+", "+{}"):
        sel = " ".join(pattern.format(m) for m in models)
        r = subprocess.run(
            [dbt, "ls", "--project-dir", DBT_DIR, "--output", "path", "--select", sel],
            cwd=worktree, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if r.returncode != 0:
            return None
        found |= lineage_paths(r.stdout)
    return found


def tested_sha_of(mr: dict, cwd: str | None = None) -> str:
    """The OLDEST target commit any successful job merged in: each job merges the target branch's
    latest commit when it starts, so jobs of one pipeline can have tested different ones."""
    pipeline = mr.get("head_pipeline") or {}
    if pipeline.get("status") != "success":
        raise Undecided(f"the pipeline of this MR is {pipeline.get('status') or 'missing'}, not green")
    jobs = glab_json(f"projects/:id/pipelines/{pipeline['id']}/jobs?per_page=100")
    shas: list[str] = []
    for job in jobs:
        if job.get("status") != "success":
            continue
        trace = run(["glab", "api", f"projects/:id/jobs/{job['id']}/trace"], check=False)
        sha = tested_target_sha(trace)
        if sha and sha not in shas:
            shas.append(sha)
    if not shas:
        raise Undecided("no job of the pipeline printed the target commit it tested; re-run the pipeline")
    return min(shas, key=lambda s: commit_time(s, cwd))


def needs_full_sweep(files: list[str]) -> bool:
    """Whether validate:ui's rules give an MR changing these files the full design sweep."""
    import ci_local as cl

    doc = cl.load_ci()
    env = {"CI_PIPELINE_SOURCE": "merge_request_event", "CI_DEFAULT_BRANCH": "main"}
    return bool(cl.rule_variables(cl.resolve_job(doc, UI_JOB), env, files).get(FULL_SCOPE_VAR))


def full_widths() -> list[int]:
    import check_design_inventory as cdi

    baseline = cdi.di.load_baseline(cdi.di.BASELINE)
    return sorted(baseline.get("viewports", cdi.DEFAULT_VIEWPORTS))


def sweep_findings(trace: str, widths: list[int]) -> tuple[bool, list[str]]:
    """(the trace holds a compared sweep at every width, the counts it found off the baseline)."""
    full = [m for m in SWEEP_RE.finditer(trace)
            if sorted(int(v) for v in m.group(1).split(",")) == widths and "not compared" not in m.group(2)]
    if not full:
        return False, []
    total = sum(int(m.group(3)) for m in full)
    if not total:
        return True, []
    return True, OFF_RE.findall(trace) or [f"{total} off the baseline"]


def sweep_refusal(mr: dict, files: list[str]) -> list[str]:
    """Why an MR that needs the full design sweep is not ready, or nothing."""
    if not needs_full_sweep(files):
        return []
    pipeline = mr.get("head_pipeline") or {}
    if not pipeline.get("id"):
        return []
    jobs = [j for j in glab_json(f"projects/:id/pipelines/{pipeline['id']}/jobs?per_page=100") if j.get("name") == UI_JOB]
    if not jobs:
        return [f"NOT READY: the MR changes the rendered site and its pipeline has no {UI_JOB} job."]
    job = jobs[0]
    if job.get("status") not in ("success", "failed"):
        return []
    trace = run(["glab", "api", f"projects/:id/jobs/{job['id']}/trace"], check=False)
    ran, off = sweep_findings(trace, full_widths())
    if off:
        return [f"NOT READY: {UI_JOB} (job {job['id']}) has counts off baseline.json:"] + [f"- {o}" for o in off]
    if not ran and job["status"] == "success":
        return [f"NOT READY: {UI_JOB} (job {job['id']}) did not sweep every width against baseline.json; "
                "re-run the pipeline."]
    return []


def commit_time(ref: str, cwd: str | None) -> int:
    return int(run(["git", "log", "-1", "--format=%ct", ref], cwd=cwd, check=False).strip() or 0)


def own_contract(files: list[str], ref: str, cwd: str | None = None) -> str | None:
    """The contract in the MR's one task folder."""
    found = [f for f in files if re.match(r"^\.claude/task/[^/]+/contract\.md$", f)]
    if not found:
        return None
    return run(["git", "show", f"{ref}:{found[0]}"], cwd=cwd, check=False)


def paged(path: str) -> list[dict]:
    out: list[dict] = []
    page = 1
    while True:
        batch = glab_json(f"{path}{'&' if '?' in path else '?'}per_page=100&page={page}")
        out += batch
        if len(batch) < 100:
            return out
        page += 1


def blockers(mr: dict, head: str, mr_files: list[str]) -> list[str]:
    """Another open MR changing a shared file this MR's contract lists: at most one open MR may."""
    import task_contract_gate as gate

    text = own_contract(mr_files, head)
    if text is None:
        return []
    out = []
    shared = gate.list_field(gate.top_level_block(text, "shared_files"))["items"]
    if shared:
        patterns = [s.split()[0] for s in shared]
        for other in paged("projects/:id/merge_requests?state=opened"):
            if other["iid"] == mr["iid"]:
                continue
            diffs = paged(f"projects/:id/merge_requests/{other['iid']}/diffs")
            clash = sorted({d["new_path"] for d in diffs for p in patterns
                            if fnmatch.fnmatch(d["new_path"], p)})
            if clash:
                out.append(f"open MR !{other['iid']} also changes the shared file {', '.join(clash)}")
    return out


def decide(iid: str) -> tuple[int, list[str]]:
    mr = glab_json(f"projects/:id/merge_requests/{iid}")
    if mr.get("state") != "opened":
        raise Undecided(f"MR !{iid} is {mr.get('state')}, not open")
    target = mr["target_branch"]
    head = mr["sha"]
    toplevel = run(["git", "rev-parse", "--show-toplevel"]).strip()
    run(["git", "fetch", "--quiet", REMOTE, target, f"refs/merge-requests/{iid}/head"], cwd=toplevel)
    refusal = sweep_refusal(mr, run(["git", "diff", "--name-only", f"{REMOTE}/{target}...{head}"], cwd=toplevel).split())
    if refusal:
        return 1, refusal
    tested = tested_sha_of(mr)
    current = run(["git", "rev-parse", f"{REMOTE}/{target}"], cwd=toplevel).strip()
    mr_files = run(["git", "diff", "--name-only", f"{tested}...{head}"], cwd=toplevel).split()
    lines: list[str] = []
    stop = blockers(mr, head, mr_files)
    if stop:
        return 1, ["BLOCKED"] + [f"- {s}" for s in stop]
    if tested == current:
        return 0, [f"ready: {target} has not moved since the pipeline tested {tested[:8]}"]
    moved = set(run(["git", "diff", "--name-only", tested, current], cwd=toplevel).split())
    lines.append(f"{target} moved {tested[:8]} -> {current[:8]}: {len(moved)} files")
    work = tempfile.mkdtemp(prefix="merge_ready_")
    wt = os.path.join(work, "wt")
    try:
        run(["git", "worktree", "add", "--detach", "--quiet", wt, current], cwd=toplevel)
        merged = subprocess.run(["git", "merge", "--no-commit", "--no-ff", head], cwd=wt,
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        if merged.returncode != 0:
            conflicts = run(["git", "diff", "--name-only", "--diff-filter=U"], cwd=wt, check=False).split()
            return 1, lines + ["OVERLAP: the MR no longer merges cleanly: " + ", ".join(conflicts or ["?"]),
                               "Re-run the pipeline after merging the target branch into the branch."]
        lineage = lineage_in(wt, toplevel, model_names(mr_files))
    finally:
        run(["git", "worktree", "remove", "--force", wt], cwd=toplevel, check=False)
        shutil.rmtree(work, ignore_errors=True)
    lineage_known = lineage is not None and not unmapped_dbt_files(mr_files)
    hits = overlaps(set(mr_files), lineage or set(), moved, lineage_known)
    if not hits:
        return 0, lines + ["ready: nothing that moved touches the MR's files or their dbt lineage"]
    return 1, lines + ["OVERLAP: re-run the pipeline without a new commit."] + [f"- {h}" for h in hits]


def repo_python() -> str | None:
    """The repo's .venv Python, which carries PyYAML for reading .gitlab-ci.yml."""
    toplevel = run(["git", "rev-parse", "--show-toplevel"], check=False).strip()
    return find_in_checkouts(toplevel, ".venv/Scripts/python.exe", ".venv/bin/python") if toplevel else None


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not argv[1].isdigit():
        print(__doc__, file=sys.stderr)
        return 2
    try:
        import yaml  # noqa: F401
    except ImportError:
        venv = repo_python()
        if venv and os.path.normcase(os.path.abspath(venv)) != os.path.normcase(os.path.abspath(sys.executable)):
            return subprocess.call([venv, os.path.abspath(__file__), argv[1]])
        print("cannot decide: PyYAML is missing; run with the repo's .venv Python", file=sys.stderr)
        return 2
    try:
        code, lines = decide(argv[1])
    except Undecided as e:
        print(f"cannot decide: {e}", file=sys.stderr)
        return 2
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
