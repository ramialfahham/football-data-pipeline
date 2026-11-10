"""Wait while a run of the nightly is in progress, so the main prod build never writes prod with it.

The API lists executions newest first and every finished one, a failed one too, carries
completionTime, so a run in progress is one of the latest few without it. An API error raises so the
job fails before any prod write; the deadline stays inside the job's 2-hour timeout for the same reason.
"""

from __future__ import annotations

import sys
import time

import google.auth
from google.auth.transport.requests import AuthorizedSession

GCP_PROJECT_ID = "football-data-pipeline-gcp"
REGION = "europe-west1"
JOB = "fdp-nightly"
EXECUTIONS_URL = (
    f"https://run.googleapis.com/v2/projects/{GCP_PROJECT_ID}/locations/{REGION}/jobs/{JOB}/executions"
)
POLL_SECONDS = 60
MAX_WAIT_SECONDS = 90 * 60
REQUEST_TIMEOUT_SECONDS = 30


def runs_in_progress(executions: list[dict]) -> list[str]:
    """Return the short names of the executions that have not completed."""
    return [e["name"].rsplit("/", 1)[-1] for e in executions if not e.get("completionTime")]


def main() -> int:
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    session = AuthorizedSession(credentials)
    waited = 0
    while True:
        response = session.get(EXECUTIONS_URL, params={"pageSize": 5}, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        in_progress = runs_in_progress(response.json().get("executions", []))
        if not in_progress:
            print("No nightly run in progress.")
            return 0
        if waited >= MAX_WAIT_SECONDS:
            print(
                f"Nightly run still in progress after {waited // 60} min ({', '.join(in_progress)}); "
                "stopping before any prod write. Retry this job once the nightly has finished.",
                file=sys.stderr,
            )
            return 1
        print(f"Nightly run in progress ({', '.join(in_progress)}); checking again in {POLL_SECONDS} s.", flush=True)
        time.sleep(POLL_SECONDS)
        waited += POLL_SECONDS


if __name__ == "__main__":
    sys.exit(main())
