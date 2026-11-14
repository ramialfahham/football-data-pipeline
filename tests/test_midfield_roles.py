"""The midfield roles on the site: their approved words, and the explainers without the page's own
player."""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
STRINGS = (REPO / "site_v2/src/i18n/strings.ts").read_text(encoding="utf-8")

APPROVED = {
    "en": {
        "DM": ("defensive midfielder", "defensive midfielders", "defensive midfielders", "Defensive midfielder"),
        "CM": ("central midfielder", "central midfielders", "central midfielders", "Central midfielder"),
        "AM": ("attacking midfielder", "attacking midfielders", "attacking midfielders", "Attacking midfielder"),
    },
    "de": {
        "DM": ("Defensiver Mittelfeldspieler", "defensiven Mittelfeldspieler", "defensive Mittelfeldspieler",
               "Defensiver Mittelfeldspieler"),
        "CM": ("Zentraler Mittelfeldspieler", "zentralen Mittelfeldspieler", "zentrale Mittelfeldspieler",
               "Zentraler Mittelfeldspieler"),
        "AM": ("Offensiver Mittelfeldspieler", "offensiven Mittelfeldspieler", "offensive Mittelfeldspieler",
               "Offensiver Mittelfeldspieler"),
    },
    "fi": {
        "DM": ("puolustava keskikenttäpelaaja", "puolustavaan keskikenttäpelaajaan",
               "puolustavat keskikenttäpelaajat", "Puolustava keskikenttäpelaaja"),
        "CM": ("keskikentän keskustan pelaaja", "keskikentän keskustan pelaajaan",
               "keskikentän keskustan pelaajat", "Keskikentän keskustan pelaaja"),
        "AM": ("hyökkäävä keskikenttäpelaaja", "hyökkäävään keskikenttäpelaajaan",
               "hyökkäävät keskikenttäpelaajat", "Hyökkäävä keskikenttäpelaaja"),
    },
}

INTROS = ("playerPeerIntro", "playerSquadClubIntro", "playerSquadNationalIntro", "playerLastSeasonIntro")


def _dict(lang: str) -> dict[str, str]:
    name = {"en": "EN", "de": "DE", "fi": "FI"}[lang]
    body = re.search(rf"^const {name}: Dict = \{{\n(.*?)^\}};", STRINGS, re.S | re.M).group(1)
    return dict(re.findall(r'(\w+): "((?:[^"\\]|\\.)*)"', body))


@pytest.mark.parametrize("lang", ["en", "de", "fi"])
@pytest.mark.parametrize("role", ["DM", "CM", "AM"])
def test_role_words_are_the_approved_ones(lang, role):
    words = _dict(lang)
    one, peers, others, label = APPROVED[lang][role]
    assert words[f"playerPosOne{role}"] == one
    assert words[f"playerPosPeers{role}"] == peers
    assert words[f"playerPosOthers{role}"] == others
    assert words[f"pos{role}"] == label


@pytest.mark.parametrize("lang", ["en", "de", "fi"])
@pytest.mark.parametrize("key", INTROS)
def test_explainers_do_not_name_the_pages_own_player(lang, key):
    assert "{player}" not in _dict(lang)[key]


def test_finnish_team_legend_takes_the_compound_form():
    assert _dict("fi")["playerOtherTeam"] == "Muut {team}pelaajat"
    comparison = (REPO / "site_v2/src/components/player/PlayerComparison.astro").read_text(encoding="utf-8")
    assert 't(lang, "playerOtherTeam", { team: teamBeforeCompound(lang, teamName) })' in comparison
