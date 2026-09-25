"""The address words (docs/site_architecture.md "Address words") against the registry and the
design check.

`site_v2/src/i18n/address_words.json` is the one list of words; a competition slug sits in the same
address position as a top word, so rule 5 says no slug may equal a word. The site build refuses a
clash over the exported competitions; this refuses it at the registry, in the MR that adds the
league. The design check opens a built page's German and Finnish files through the same words, so
its translation is pinned to the cases `site_v2/src/lib/addressWords.test.mjs` pins for the site.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import check_design_inventory as cdi  # noqa: E402
import design_inventory as di  # noqa: E402

REGISTRY = REPO / "docs" / "competition_registry.yml"
WORDS = json.loads(cdi.ADDRESS_WORDS.read_text(encoding="utf-8"))


def _registry_slugs() -> list[str]:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    return [r["slug"] for r in data["competitions"] if isinstance(r, dict) and r.get("slug")]


def _clashes(slugs: list[str]) -> list[str]:
    words = {w: "%s (%s)" % (key, lang) for key, by_lang in WORDS.items() for lang, w in by_lang.items()}
    return sorted("%s = %s" % (s, words[s]) for s in set(slugs) if s in words)


def test_no_registry_slug_equals_an_address_word():
    slugs = _registry_slugs()
    assert len(slugs) >= 40, "the registry read found only %d slugs; the parse broke" % len(slugs)
    assert _clashes(slugs) == [], "a competition slug equals an address word: %s" % _clashes(slugs)


def test_the_clash_check_goes_red_on_a_word():
    assert _clashes(["bundesliga", "spiele", "tilastot"]) == ["spiele = matches (de)", "tilastot = stats (fi)"]


def test_every_word_is_named_in_every_published_language():
    for key, by_lang in WORDS.items():
        assert sorted(by_lang) == sorted(cdi.DEFAULT_LANGS), key


CASES = [
    ("teams/x/", {"de": "mannschaften/x/", "fi": "joukkueet/x/"}),
    ("players/p-1/", {"de": "spieler/p-1/", "fi": "pelaajat/p-1/"}),
    ("competitions/", {"de": "wettbewerbe/", "fi": "kilpailut/"}),
    ("matches/", {"de": "spiele/", "fi": "ottelut/"}),
    ("matches/2026-09-27/", {"de": "spiele/2026-09-27/", "fi": "ottelut/2026-09-27/"}),
    ("bundesliga/matches/", {"de": "bundesliga/spiele/", "fi": "bundesliga/ottelut/"}),
    ("bundesliga/stats/", {"de": "bundesliga/statistiken/", "fi": "bundesliga/tilastot/"}),
    ("bundesliga/matches/m-1/", {"de": "bundesliga/spiele/m-1/", "fi": "bundesliga/ottelut/m-1/"}),
    ("*/matches/*/index.html", {"de": "*/spiele/*/index.html", "fi": "*/ottelut/*/index.html"}),
    ("bundesliga/", {"de": "bundesliga/", "fi": "bundesliga/"}),
    ("", {"de": "", "fi": ""}),
]


@pytest.mark.parametrize("en,by_lang", CASES)
def test_translate_path_matches_the_site_both_ways(en, by_lang):
    for lang, localised in by_lang.items():
        assert cdi.translate_path(en, "en", lang) == localised
        assert cdi.translate_path(localised, lang, "en") == en


def test_only_the_position_decides():
    assert cdi.translate_path("teams/matches/", "en", "de") == "mannschaften/matches/"
    assert cdi.translate_path("bundesliga/x/stats/", "en", "de") == "bundesliga/x/stats/"


def test_resolve_built_opens_each_language_at_its_own_words(tmp_path):
    for rel in ("en/bundesliga/stats/index.html", "de/bundesliga/statistiken/index.html",
                "fi/bundesliga/tilastot/index.html", "de/bundesliga/stats/index.html"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("<html></html>", encoding="utf-8")
    page = di.Page("Competition rankings", "built", "site_v2/dist", "en/bundesliga/stats/index.html", "path", ())
    assert cdi.resolve_built(page, tmp_path, "en") == tmp_path / "en/bundesliga/stats/index.html"
    assert cdi.resolve_built(page, tmp_path, "de") == tmp_path / "de/bundesliga/statistiken/index.html"
    assert cdi.resolve_built(page, tmp_path, "fi") == tmp_path / "fi/bundesliga/tilastot/index.html"
