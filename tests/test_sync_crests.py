"""The crest sync: what lands in the site's public folder and what a missing bucket does."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from google.api_core.exceptions import Forbidden, NotFound

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync_crests.py"
spec = importlib.util.spec_from_file_location("sync_crests", SCRIPT)
sync_crests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_crests)


class Blob:
    def __init__(self, name: str, data: bytes = b"webp"):
        self.name = name
        self.data = data

    def download_to_filename(self, path: str) -> None:
        Path(path).write_bytes(self.data)


class Client:
    def __init__(self, blobs=None, error: Exception | None = None):
        self.blobs = blobs or []
        self.error = error

    def list_blobs(self, bucket: str):
        if self.error:
            raise self.error
        return iter(self.blobs)


def test_the_objects_land_under_their_own_names(tmp_path):
    client = Client([Blob("teams/1-48.webp", b"a"), Blob("leagues/9-104.webp", b"b")])
    result = sync_crests.sync(tmp_path, client=client, bucket="b")
    assert result == {"files": 2, "skipped": None}
    assert (tmp_path / "teams" / "1-48.webp").read_bytes() == b"a"
    assert (tmp_path / "leagues" / "9-104.webp").read_bytes() == b"b"


def test_a_name_outside_the_layout_is_not_copied(tmp_path):
    client = Client([Blob("teams/1-48.webp"), Blob("teams/1-48.png"), Blob("../escape.webp"), Blob("other/1-48.webp")])
    assert sync_crests.sync(tmp_path, client=client, bucket="b")["files"] == 1
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*.*")) == ["teams/1-48.webp"]


def test_a_missing_bucket_is_a_warning_with_no_files(tmp_path, capsys):
    result = sync_crests.sync(tmp_path, client=Client(error=NotFound("no bucket")), bucket="b")
    assert result == {"files": 0, "skipped": "no bucket"}
    assert "does not exist yet" in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []


def test_any_other_error_fails_the_run(tmp_path):
    with pytest.raises(Forbidden):
        sync_crests.sync(tmp_path, client=Client(error=Forbidden("no access")), bucket="b")


def test_the_default_destination_is_the_sites_public_folder_and_the_bucket_is_the_ingest_constant():
    assert sync_crests.DEFAULT_DEST.as_posix().endswith("site_v2/public/crests")
    assert sync_crests.bucket_name() == "football-data-pipeline-gcp-crests"
