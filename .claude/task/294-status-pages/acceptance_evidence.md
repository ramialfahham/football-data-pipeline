# Verification — every Matchdays match has a page, each status its word

## The page set on live data

Prod `marts.mart_competition_fixtures`, 17 Nov 2026 (3.5 MB read):

| rows | played | not played | `is_played` null | `fixture_slug` null | not played and not future NS/TBD |
|---|---|---|---|---|---|
| 65,199 | 61,575 | 3,624 | 0 | 0 | 182 |

The competition payload's Matchdays rows are every row of the mart for its competition-season
(`fetch_competition_payloads`, no filter). The match payloads are now `not is_played`
(`fetch_fixture_payloads`) plus `is_played` (`fetch_played_fixture_payloads`): 3,624 + 61,575 =
65,199, every row, each with a slug for its page. The old filter missed 182 of them today.

## A local build with real status matches

The branch's export functions run against prod marts with the branch's `unplayed_state` expression
inlined (prod's mart gets the column at the merge's data build), 0.82 GB read. They wrote 3,624
not-played payloads, of which the status ones were cancelled 161, postponed 10, awaiting result 9,
abandoned 2. The payloads and competition payloads of La Liga 2026, AFC Champions League 2026,
Coupe de France 2026 and FA Cup 2025 went into the dev server's data, beside the committed sample,
and out again afterwards.

| Status | Matchdays page | Row words EN / DE / FI | Rows linked | Match page | Head words |
|---|---|---|---|---|---|
| Awaiting result | Coupe de France | Awaiting result / Ergebnis ausstehend / Tulosta odotetaan, 8 rows | 8 of 8 | `2026-11-14-stade-bordelais-vs-mazeres`, 200 in each language | same words, in the kick-off line |
| Abandoned | La Liga | Abandoned / Abgebrochen / Keskeytetty | 1 of 1 | `2026-10-10-rayo-vallecano-vs-athletic-club`, 200 | same |
| Postponed | AFC Champions League | Postponed / Verlegt / Siirretty | 1 of 1 | `2026-03-09-al-ahli-jeddah-vs-al-duhail-sc`, 200 | same |
| Cancelled | FA Cup | Cancelled / Abgesagt / Peruttu, 3 rows | 3 of 3 | `2025-08-05-welwyn-vs-ware`, 200 | same |

The head reads, for example, "Matchday 8 · Sat, 10 Oct 2026 · ABANDONED · Campo de Futbol de
Vallecas": the tag takes the time's unit. A status match's page has head, head to head and next
matches, the form a match further out has.

The tag measured 11px, 700, uppercase, 4px corners, on the accent colour, the Tag rule's form.

Narrow sweep, those 24 pages (4 Matchdays pages and 4 match pages in 3 languages), each status
tag's round opened, 45 tags per width: tag inside its row, no name past its space, no name under
the tag, the tag one line, no page wider than the screen.

| Width | Inline | Own line above the home team | Head | Defects |
|---|---|---|---|---|
| 280px | 18 | 15 | 12 | 0 |
| 320px | 33 | 0 | 12 | 0 |
| 375px | 33 | 0 | 12 | 0 |
| 768px | 33 | 0 | 12 | 0 |

## The payload-per-row test

`node --test site_v2/scripts/check-built-pages.test.mjs`: 26 of 26 pass. "main fails a full export
whose fixtures page lists a match with no payload, and passes once it has one" builds a three-language
tree with a manifest: with match 8's payload missing, `main` returns 1 and says "the row of match 8
has no match payload" (and "an unplayed row is not a link"); with the payload and its pages, 0.

criteria_demonstrated:
  - **Every Matchdays match has a page in EN, DE and FI:** the page set is `not is_played` plus `is_played`, 65,199 of 65,199 mart rows, 0 without a slug; on the local build every status row on four Matchdays pages links, and each status's match page answers 200 in EN, DE and FI.
  - **An approved display for each status, on the page and the row:** the four words of #294 note 4255394677 (approved in chat, 17 Nov 2026) in all three languages, in the Tag rule's form, in the row's kick-off column and in the head's kick-off line, at 280 to 768px with 0 defects.
  - **A full build from live data has no "an unplayed row is not a link" finding:** every Matchdays row of the live data has a payload (65,199 = 3,624 + 61,575), and a row is a link exactly when its payload exists (`checkMatchRowLinks`); the full build itself runs in deploy:site-v2.
  - **A test fails the build on a Matchdays row with no payload:** `checkFixturesPayloads`, run by `main` on a full export, and its two tests above.
