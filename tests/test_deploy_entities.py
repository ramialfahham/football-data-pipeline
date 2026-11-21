"""The deploy export takes exactly the entities the built pages read, and every page enumerates all of it.

The committed sample under site_v2/src/data is the pages' input, so the set of top-level names it holds is
the set the pages read. The deploy export must write that set and nothing a page ignores.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
DATA = "site_v2/src/data"
PAGES = REPO / "site_v2" / "src" / "pages"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import export_site_data as export  # noqa: E402

ALWAYS_WRITTEN = ("competitions.json",)
UNREAD_ENTITIES = {"nav", "leaderboards", "glossary"}


def _tracked_sample() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", DATA], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split()
    return [p[len(DATA) + 1:] for p in out if p != f"{DATA}/README.md"]


def _top_level(paths: list[str]) -> set[str]:
    return {p.split("/", 1)[0] + "/" if "/" in p else p for p in paths}


def _deploy_outputs() -> set[str]:
    names = set(ALWAYS_WRITTEN)
    for entity in export.DEPLOY_ENTITIES:
        names.update(export.ENTITY_OUTPUTS[entity])
    return names


def test_every_entity_declares_what_it_writes():
    assert set(export.ENTITY_OUTPUTS) == set(export.ENTITY_TYPES)


def test_the_deploy_entities_are_every_entity_but_the_three_no_page_reads():
    assert set(export.ENTITY_TYPES) - set(export.DEPLOY_ENTITIES) == UNREAD_ENTITIES
    assert len(set(export.DEPLOY_ENTITIES)) == len(export.DEPLOY_ENTITIES)


def test_the_deploy_export_writes_exactly_what_the_pages_read():
    read = _top_level(_tracked_sample())
    written = _deploy_outputs()
    assert not read - written, f"a page reads what the deploy export does not write: {sorted(read - written)}"
    assert not written - read, f"the deploy export writes what no page reads: {sorted(written - read)}"


def test_the_entities_no_page_reads_write_nothing_a_page_reads():
    read = _top_level(_tracked_sample())
    for entity in UNREAD_ENTITIES:
        assert not set(export.ENTITY_OUTPUTS[entity]) & read, entity


def _globs() -> list[tuple[Path, str]]:
    found = []
    for page in PAGES.rglob("*.astro"):
        for pattern in re.findall(r'import\.meta\.glob<[^>]*>\(\s*"/src/data/([^"]+)"', page.read_text(encoding="utf-8")):
            found.append((page, pattern))
    return found


def _glob_regex(pattern: str) -> re.Pattern[str]:
    return re.compile("^" + re.escape(pattern).replace(r"\*", "[^/]+") + "$")


def test_every_glob_a_page_reads_matches_every_payload_file_of_its_folder():
    sample = _tracked_sample()
    globs = _globs()
    assert globs, "no page reads a payload folder through a glob: this test has gone stale"
    for page, pattern in globs:
        folder = pattern.split("/", 1)[0] + "/"
        assert folder in _deploy_outputs(), f"{page.name} reads {pattern}, which the deploy export does not write"
        pattern_re = _glob_regex(pattern)
        files = [p for p in sample if p.startswith(folder)]
        assert files, f"{pattern} matches nothing in the committed sample"
        missed = [p for p in files if not pattern_re.match(p)]
        assert not missed, f"{page.name}: {pattern} skips {missed[:3]}, which the export writes"


def test_the_deploy_export_job_takes_the_shared_entity_list():
    ci = yaml.safe_load((REPO / ".gitlab-ci.yml").read_text(encoding="utf-8"))
    script = "\n".join(str(line) for line in ci["deploy:export"]["script"] if isinstance(line, str))
    match = re.search(r"export_site_data\.py\s+--entities\s+(\S+)", script)
    assert match, "deploy:export no longer runs export_site_data.py --entities"
    assert match.group(1) == "deploy"


def test_parse_entities_expands_deploy_and_drops_repeats():
    assert export.parse_entities("deploy") == export.DEPLOY_ENTITIES
    assert export.parse_entities("teams,deploy") == ("teams",) + tuple(e for e in export.DEPLOY_ENTITIES if e != "teams")
    assert export.parse_entities(" teams , nav ,") == ("teams", "nav")
