"""Copy the crest bucket into the site's public folder, so the build serves crests from our own domain.

    python scripts/sync_crests.py [--dest site_v2/public/crests]

Astro copies `site_v2/public/` into `dist/`, and Firebase Hosting serves `dist/crests/` next to the
pages. A bucket that does not exist yet is a warning and no files: dim_team and dim_league publish no
crest path until an object is stored, so no page names a file that is missing. Any other failure
fails the run, and the built-pages check fails a full export whose crest paths are not files.
"""

from __future__ import annotations

import argparse
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_DEST = REPO / "site_v2" / "public" / "crests"
OBJECT_NAME = re.compile(r"^(teams|leagues)/\d+-(48|104)\.webp$")
WORKERS = 16


def bucket_name() -> str:
    sys.path.insert(0, str(REPO))
    from ingestion.api_football.settings import CREST_BUCKET

    return CREST_BUCKET


def sync(dest: Path, client=None, bucket: str | None = None) -> dict:
    from google.api_core.exceptions import NotFound

    if client is None:
        from google.cloud import storage

        client = storage.Client()
    name = bucket or bucket_name()
    try:
        blobs = [b for b in client.list_blobs(name) if OBJECT_NAME.match(b.name)]
    except NotFound:
        print(f"[sync-crests] the bucket {name} does not exist yet: no crest files", flush=True)
        return {"files": 0, "skipped": "no bucket"}

    def fetch(blob) -> None:
        target = dest / blob.name
        target.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(target))

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(fetch, blobs))
    print(f"[sync-crests] {len(blobs)} files from {name} into {dest}", flush=True)
    return {"files": len(blobs), "skipped": None}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    args = parser.parse_args(argv)
    sync(args.dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
