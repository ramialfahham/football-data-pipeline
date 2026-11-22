"""The nightly site deploy, as the Cloud Run job `fdp-site` runs it.

Steps, each failing the job on error and stopping before the Firebase deploy:
  1. the warehouse nightly (`fdp-nightly`) must have finished successfully today (UTC);
  2. export every entity the built pages read (`export_site_data.py --entities deploy`);
  3. the export's counts must hold against the counts the live site's previous deploy published;
  4. replace the committed sample under site_v2/src/data with the export;
  5. copy the crest bucket into site_v2/public/crests, so the build serves crests from our domain;
  6. `npm run build`: the build, `audit-seo` and `check-built-pages`;
  7. publish the counts beside the site, then `firebase deploy --only hosting`.

The job runs as its service account, so Google clients and firebase-tools take application default
credentials with no key file.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

GCP_PROJECT_ID = "football-data-pipeline-gcp"
REGION = "europe-west1"
NIGHTLY_JOB = "fdp-nightly"
EXECUTIONS_URL = (
    f"https://run.googleapis.com/v2/projects/{GCP_PROJECT_ID}/locations/{REGION}/jobs/{NIGHTLY_JOB}/executions"
)
LIVE_MANIFEST_URL = f"https://{GCP_PROJECT_ID}.web.app/export-manifest.json"
PUBLISHED_MANIFEST = "export-manifest.json"

POLL_SECONDS = 60
MAX_WAIT_SECONDS = 45 * 60
REQUEST_TIMEOUT_SECONDS = 30

COMPARED_COUNTS = ("team", "fixture", "competition", "player", "player_peers")
MIN_SHARE = 0.9
MIN_BASELINE = 20
HEAP_MB = 8192
FIRST_DEPLOY_FLAG = "ALLOW_FIRST_DEPLOY"

REPO = Path(__file__).resolve().parents[1]
SITE_DIR = REPO / "site_v2"
EXPORT_DIR = Path(os.environ.get("TMPDIR", "/tmp")) / "site_export"
CRESTS_DIR = SITE_DIR / "public" / "crests"


def log(message: str) -> None:
    print(f"[nightly-site] {message}", flush=True)


def _parse_time(text: str) -> datetime:
    """An RFC 3339 time from the Cloud Run API; Python 3.11 reads a fraction of nine digits."""
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _succeeded(execution: dict) -> bool:
    for condition in execution.get("conditions", []):
        if condition.get("type") == "Completed":
            return condition.get("state") == "CONDITION_SUCCEEDED"
    return (
        execution.get("succeededCount", 0) >= 1
        and not execution.get("failedCount")
        and not execution.get("cancelledCount")
    )


def nightly_state(executions: list[dict], today: datetime) -> tuple[str, str]:
    """('ok' | 'wait' | 'refuse', why) for the newest nightly execution, which the API lists first."""
    if not executions:
        return "refuse", f"no {NIGHTLY_JOB} execution exists"
    newest = executions[0]
    name = newest["name"].rsplit("/", 1)[-1]
    created = _parse_time(newest["createTime"]).astimezone(timezone.utc)
    if created.date() != today.astimezone(timezone.utc).date():
        return "refuse", f"the newest nightly ({name}) was created {created:%Y-%m-%d %H:%M} UTC, not today"
    if not newest.get("completionTime"):
        return "wait", f"nightly {name} is still running"
    if not _succeeded(newest):
        return "refuse", f"nightly {name} did not succeed"
    return "ok", f"nightly {name} succeeded"


def wait_for_nightly(session, now=lambda: datetime.now(timezone.utc), sleep=time.sleep) -> None:
    waited = 0
    while True:
        response = session.get(EXECUTIONS_URL, params={"pageSize": 5}, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        state, why = nightly_state(response.json().get("executions", []), now())
        if state == "ok":
            log(why)
            return
        if state == "refuse" or waited >= MAX_WAIT_SECONDS:
            raise SystemExit(f"[nightly-site] refusing to deploy: {why}")
        log(f"{why}; checking again in {POLL_SECONDS} s")
        sleep(POLL_SECONDS)
        waited += POLL_SECONDS


def count_regressions(previous: dict | None, current: dict) -> list[str]:
    """What fell too far below the previous deploy's counts; None for previous is the first deploy."""
    if previous is None:
        return []
    issues = []
    before_counts = previous.get("counts", {})
    now_counts = current.get("counts", {})
    for key in COMPARED_COUNTS:
        before = before_counts.get(key, 0)
        if before < MIN_BASELINE:
            continue
        now = now_counts.get(key, 0)
        if now < before * MIN_SHARE:
            issues.append(f"{key}: {now} now, {before} on the live site (floor {math.ceil(before * MIN_SHARE)})")
    return issues


def fetch_live_manifest(url: str = LIVE_MANIFEST_URL, opener=urllib.request.urlopen) -> dict | None:
    """The counts the live site's previous deploy published; None on a 404, which is the first deploy."""
    try:
        with opener(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def published_manifest(manifest: dict) -> dict:
    """Counts only: no file index, no checksums."""
    return {
        "generated_at": manifest["generated_at"],
        "counts": manifest["counts"],
        "source_counts": manifest.get("source_counts", {}),
    }


def replace_sample_with_export(site_dir: Path, export_dir: Path) -> None:
    """The deployed site is built from the export alone, so the committed sample leaves the folder first.

    The export is moved, not copied: the job's disk is memory, and a second copy would stay resident."""
    data = site_dir / "src" / "data"
    for child in data.iterdir():
        if child.name == "README.md":
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    for child in list(export_dir.iterdir()):
        shutil.move(str(child), str(data / child.name))


def folder_size(path: Path) -> tuple[int, int]:
    files = [p for p in path.rglob("*") if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)


def step(name: str, command: list[str], cwd: Path = REPO, env: dict | None = None) -> None:
    log(f"{name}: {' '.join(command)}")
    started = time.monotonic()
    subprocess.run(command, cwd=cwd, env=env, check=True)
    log(f"{name}: done in {time.monotonic() - started:.0f} s")


def floor_issues(previous: dict | None, current: dict, allow_first: bool) -> list[str]:
    """Why the export may not replace the live site; a live site with no counts file needs the first-deploy flag."""
    if previous is None:
        if allow_first:
            log(f"the live site publishes no counts file; {FIRST_DEPLOY_FLAG} is set, so the count floor is skipped")
            return []
        return [
            f"the live site publishes no counts file, so the count floor cannot run; set {FIRST_DEPLOY_FLAG}=1 on "
            "the execution for the first deploy, or after a manual deploy"
        ]
    return count_regressions(previous, current)


def main() -> int:
    import google.auth
    from google.auth.transport.requests import AuthorizedSession

    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    return deploy(AuthorizedSession(credentials))


def deploy(session) -> int:
    wait_for_nightly(session)

    if EXPORT_DIR.exists():
        shutil.rmtree(EXPORT_DIR)
    env = dict(os.environ, PYTHONPATH=str(REPO))
    step(
        "export",
        [sys.executable, "scripts/export_site_data.py", "--entities", "deploy", "--out", str(EXPORT_DIR)],
        env=env,
    )

    manifest = json.loads((EXPORT_DIR / "manifest.json").read_text(encoding="utf-8"))
    log(f"export counts: {manifest['counts']}; source counts: {manifest.get('source_counts', {})}")
    issues = floor_issues(fetch_live_manifest(), manifest, os.environ.get(FIRST_DEPLOY_FLAG) == "1")
    if issues:
        raise SystemExit("[nightly-site] refusing to deploy: " + "; ".join(issues))

    replace_sample_with_export(SITE_DIR, EXPORT_DIR)
    step("crests", [sys.executable, "scripts/sync_crests.py", "--dest", str(CRESTS_DIR)], env=env)
    step(
        "build and gates",
        ["npm", "run", "build"],
        cwd=SITE_DIR,
        env=dict(os.environ, NODE_OPTIONS=f"--max-old-space-size={HEAP_MB}"),
    )

    dist = SITE_DIR / "dist"
    (dist / PUBLISHED_MANIFEST).write_text(json.dumps(published_manifest(manifest), indent=2), encoding="utf-8")
    files, size = folder_size(dist)
    log(f"dist: {files} files, {size / 1e9:.2f} GB")
    step(
        "deploy",
        ["firebase", "deploy", "--only", "hosting", "--project", GCP_PROJECT_ID, "--non-interactive"],
        cwd=SITE_DIR,
    )
    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
