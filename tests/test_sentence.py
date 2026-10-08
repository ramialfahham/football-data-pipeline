"""The sentence generator and the match page's head-to-head intro, read from the real strings.ts."""
from __future__ import annotations

import re

import pytest

from scripts import export_site_data as ex

H2H_KEYS = ("h2hLastDrawn", "h2hLastWon", "h2hBothDrawn", "h2hAllDrawn", "h2hWonBoth", "h2hWonAll",
            "h2hWonSomeOneDrawn", "h2hWonSomeDrawn", "h2hSplit", "h2hSplitOneDrawn", "h2hSplitDrawn")
SERVED = {"n": "meetings_last5", "w": "wins_last5", "l": "losses_last5", "d": "draws_last5",
          "won": "wins_last5 or losses_last5", "club": "a team name", "home": "home team name",
          "away": "away team name"}
HOME, AWAY = "Borussia Dortmund", "SV Werder Bremen"


def _row(n, w, d, lost):
    return {"meetings_last5": n, "wins_last5": w, "draws_last5": d, "losses_last5": lost}


def _splits():
    return [(n, w, d, n - w - d) for n in range(1, 6) for w in range(n + 1) for d in range(n - w + 1)]


def test_every_split_of_one_to_five_meetings_gets_an_intro_in_every_language():
    splits = _splits()
    assert len(splits) == 55
    for split in splits:
        intro = ex.head_to_head_intro(_row(*split), HOME, AWAY)
        assert intro is not None, split
        assert set(intro) == set(ex.SENTENCE_LANGS)
        for lang, text in intro.items():
            assert "{" not in text and "None" not in text, (split, lang, text)


def test_every_template_placeholder_has_a_served_source_in_every_language():
    templates = ex.sentence_templates()
    for key in H2H_KEYS:
        en = set(re.findall(r"\{(\w+)\}", templates["en"][key]))
        assert en <= set(SERVED), (key, en)
        for lang in ex.SENTENCE_LANGS:
            assert set(re.findall(r"\{(\w+)\}", templates[lang][key])) == en, (key, lang)


WORDINGS = [
    ((1, 0, 1, 0), "The last meeting was drawn.",
     "Das letzte Duell endete unentschieden.",
     "Edellinen kohtaaminen päättyi tasan."),
    ((1, 0, 0, 1), "SV Werder Bremen won the last meeting.",
     "SV Werder Bremen gewann das letzte Duell.",
     "SV Werder Bremen voitti edellisen kohtaamisen."),
    ((2, 0, 2, 0), "Both of the last 2 meetings were drawn.",
     "Die letzten beiden Duelle endeten unentschieden.",
     "Kaksi edellistä kohtaamista päättyivät tasan."),
    ((4, 0, 4, 0), "All of the last 4 meetings were drawn.",
     "Die letzten 4 Duelle endeten alle unentschieden.",
     "Kaikki 4 edellistä kohtaamista päättyivät tasan."),
    ((2, 0, 0, 2), "SV Werder Bremen won both of the last 2 meetings.",
     "SV Werder Bremen gewann die letzten beiden Duelle.",
     "SV Werder Bremen voitti kaksi edellistä kohtaamista."),
    ((3, 3, 0, 0), "Borussia Dortmund won all of the last 3 meetings.",
     "Borussia Dortmund gewann alle letzten 3 Duelle.",
     "Borussia Dortmund voitti kaikki 3 edellistä kohtaamista."),
    ((3, 0, 1, 2), "SV Werder Bremen won 2 of the last 3 meetings, and 1 was drawn.",
     "SV Werder Bremen gewann 2 der letzten 3 Duelle, 1 endete unentschieden.",
     "SV Werder Bremen voitti 3 edellisestä kohtaamisesta 2, ja 1 päättyi tasan."),
    ((5, 3, 2, 0), "Borussia Dortmund won 3 of the last 5 meetings, and 2 were drawn.",
     "Borussia Dortmund gewann 3 der letzten 5 Duelle, 2 endeten unentschieden.",
     "Borussia Dortmund voitti 5 edellisestä kohtaamisesta 3, ja 2 päättyi tasan."),
    ((4, 3, 0, 1), "Borussia Dortmund won 3 and SV Werder Bremen 1 of the last 4 meetings.",
     "Von den letzten 4 Duellen gewann Borussia Dortmund 3 und SV Werder Bremen 1.",
     "4 edellisestä kohtaamisesta Borussia Dortmund voitti 3 ja SV Werder Bremen 1."),
    ((5, 1, 1, 3), "Borussia Dortmund won 1 and SV Werder Bremen 3 of the last 5 meetings, and 1 was drawn.",
     "Von den letzten 5 Duellen gewann Borussia Dortmund 1 und SV Werder Bremen 3, 1 endete unentschieden.",
     "5 edellisestä kohtaamisesta Borussia Dortmund voitti 1 ja SV Werder Bremen 3, ja 1 päättyi tasan."),
    ((5, 1, 2, 2), "Borussia Dortmund won 1 and SV Werder Bremen 2 of the last 5 meetings, and 2 were drawn.",
     "Von den letzten 5 Duellen gewann Borussia Dortmund 1 und SV Werder Bremen 2, 2 endeten unentschieden.",
     "5 edellisestä kohtaamisesta Borussia Dortmund voitti 1 ja SV Werder Bremen 2, ja 2 päättyi tasan."),
]


@pytest.mark.parametrize(("split", "en", "de", "fi"), WORDINGS)
def test_each_wording_is_chosen_for_its_split_in_every_language(split, en, de, fi):
    assert ex.head_to_head_intro(_row(*split), HOME, AWAY) == {"en": en, "de": de, "fi": fi}


def test_the_cases_cover_every_wording():
    templates = ex.sentence_templates()["en"]
    texts = [en for _, en, _, _ in WORDINGS]
    for key in H2H_KEYS:
        stem = re.split(r"\{\w+\}", templates[key])
        assert any(all(part in text for part in stem) for text in texts), key


@pytest.mark.parametrize("row", [
    _row(None, 3, 2, 0), _row(5, None, 2, 0), _row(5, 3, None, 0), _row(5, 3, 2, None), _row(0, 0, 0, 0),
])
def test_a_missing_count_gives_no_intro(row):
    assert ex.head_to_head_intro(row, HOME, AWAY) is None


@pytest.mark.parametrize("names", [(None, AWAY), (HOME, None)])
def test_a_missing_team_name_gives_no_intro(names):
    assert ex.head_to_head_intro(_row(2, 0, 2, 0), *names) is None


def test_no_row_gives_no_intro():
    assert ex.head_to_head_intro(None, HOME, AWAY) is None


def test_sentence_returns_nothing_for_a_missing_value():
    assert ex.sentence("h2hWonAll", "en", {"club": HOME, "n": None}) is None
    assert ex.sentence("h2hWonAll", "en", {"club": HOME, "n": 4}) == "Borussia Dortmund won all of the last 4 meetings."
