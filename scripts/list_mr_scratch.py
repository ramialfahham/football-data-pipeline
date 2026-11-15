"""List the merge-request scratch datasets nothing reads any more. Lists only; deletes nothing.

`data:build:mr` writes `ci_mr<IID>_<SHA>` and its layer datasets (`ci_mr<IID>_<SHA>_marts`, ...),
where <SHA> is the first 8 characters of the target commit its pipeline merged in. A set is listed
when its merge request is no longer open, when an open merge request has a newer set, or when its
name carries no target commit. Each open merge request keeps its newest set.

Reads the BigQuery dataset list (metadata, no query) and the open merge requests through `glab`.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime

PROJECT = "football-data-pipeline-gcp"
GITLAB_PROJECT = "85168767"

_NAME_RE = re.compile(r"^ci_mr(?P<iid>\d+)(?:_(?P<sha>[0-9a-f]{8})(?=_|$))?(?:_.+)?$")


def parse(name: str) -> tuple[int, str | None] | None:
    """Return (merge request IID, target SHA or None) for a scratch dataset name, else None."""
    m = _NAME_RE.match(name)
    if not m:
        return None
    return int(m["iid"]), m["sha"]


def classify(
    datasets: list[str], open_iids: set[int], created: Callable[[list[str]], datetime]
) -> list[tuple[str, str]]:
    """Return (dataset, reason) for every scratch dataset nothing reads any more, sorted by name.

    `created` gives the creation time of a set from its dataset names; it is called only for open
    merge requests with more than one set.
    """
    sets: dict[tuple[int, str | None], list[str]] = {}
    for name in datasets:
        key = parse(name)
        if key is not None:
            sets.setdefault(key, []).append(name)

    listed: list[tuple[str, str]] = []
    by_mr: dict[int, list[str]] = {}
    for (iid, sha), names in sets.items():
        if iid not in open_iids:
            listed += [(n, f"MR !{iid} is not open") for n in names]
        elif sha is None:
            listed += [(n, f"MR !{iid}: no target commit in the name") for n in names]
        else:
            by_mr.setdefault(iid, []).append(sha)

    for iid, shas in by_mr.items():
        if len(shas) < 2:
            continue
        newest = max(shas, key=lambda s: created(sets[(iid, s)]))
        for sha in shas:
            if sha != newest:
                listed += [(n, f"MR !{iid}: superseded by its {newest} set") for n in sets[(iid, sha)]]
    return sorted(listed)


def open_merge_request_iids(project: str = GITLAB_PROJECT) -> set[int]:
    iids: set[int] = set()
    page = 1
    while True:
        path = f"projects/{project}/merge_requests?state=opened&per_page=100&page={page}"
        r = subprocess.run(["glab", "api", path], capture_output=True)
        if r.returncode != 0:
            sys.exit(f"glab api {path} failed: {r.stderr.decode('utf-8', 'replace')[:300]}")
        batch = json.loads(r.stdout.decode("utf-8"))
        iids.update(mr["iid"] for mr in batch)
        if len(batch) < 100:
            return iids
        page += 1


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    from google.cloud import bigquery

    client = bigquery.Client(project=PROJECT)
    datasets = [d.dataset_id for d in client.list_datasets(PROJECT)]
    open_iids = open_merge_request_iids()

    def created(names: list[str]) -> datetime:
        return min(client.get_dataset(f"{PROJECT}.{n}").created for n in names)

    listed = classify(datasets, open_iids, created)
    for name, reason in listed:
        print(f"{name}\t{reason}")
    print(f"{len(listed)} datasets listed; nothing was deleted.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
