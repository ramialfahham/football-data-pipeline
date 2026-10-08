# Acceptance evidence — #145, the sentence generator, first used by the head-to-head intro

Read from `pytest tests/test_sentence.py` (23 passed), from the generator run over the 628 committed fixture
payloads, and from `astro build` of the committed sample with and without the change (2,538 pages; audit-seo and
check-built-pages OK in both).

criteria_demonstrated:
  - EVERY SPLIT GETS AN INTRO. The test enumerates the 55 splits of 1 to 5 meetings into wins, draws and losses.
    Each gets an intro in EN, DE and FI, with no placeholder left and no "None". A second test holds every
    template's placeholders to the served fields (meetings_last5, wins_last5, draws_last5, losses_last5, the two
    team names) and to the same set in all three languages. One case per wording (eleven) asserts the exact EN,
    DE and FI text chosen for its split, and a further test holds that the cases cover every wording.
  - A MISSING INPUT GIVES NO INTRO. The test gives no intro for a missing meetings, wins, draws or losses count,
    for zero meetings, for a missing home or away name, and for no head-to-head row. sentence() returns None when
    a placeholder's value is missing.
  - THE COMMITTED PAYLOADS. Of 628 fixture payloads, 456 carry a head-to-head row, and all 456 get an intro in all
    three languages. Philadelphia Union vs Orlando City SC reads: "Philadelphia Union won 1 and Orlando City SC 3
    of the last 5 meetings, and 1 was drawn." / "Von den letzten 5 Duellen gewann Philadelphia Union 1 und Orlando
    City SC 3, 1 endete unentschieden." / "5 edellisestä kohtaamisesta Philadelphia Union voitti 1 ja Orlando City
    SC 3, ja 1 päättyi tasan."
  - THE BUILT SITE IS UNCHANGED. diff -rq of a build of main and a build with the change reports 0 differing files
    out of 2,547. Nothing renders the intro until the page MR.
