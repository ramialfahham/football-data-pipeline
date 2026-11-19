# Verification — pages hold on narrow screens, in the shared parts

## How it was measured

- Two builds of the committed sample: main a54adfbf (before) and this branch (after), 786 pages per language each.
- Every page and every tab was loaded once and resized to 280, 320, 375, 768 and 1010px, in EN, DE and FI, in the validate:ui browser (Playwright Chromium).
- A count is one element breaking at one width, summed over EN, DE and FI.
- The branch was swept with the narrow Deserved points heads built (approved in chat, 2026-11-19). A second pass at 280–768px with the site's scripts removed ran on the same branch build: it finds 0 scrolls, splits, overflows, overlaps, cut-off text and small tap areas on any page type, so no break class appears without the script. Its only line counts are rows by their rule: without the script no block carries a fit mark and the stylesheet draws the narrow forms.
- A layout compare at 1010px of every page and tab of both builds: each element's box and text, before and after, with the no-break spans the build adds left out.

## Before → after

| Break | Part, rule | Before | After | Where |
|---|---|---|---|---|
| Team name and chevron run past the screen (page scrolls) | Match header; Name in whole words | 90 | 0 | upcoming match pages, 280px |
| Result row keeps one line while its name, home/away or meta wraps | Fitted block, Result row | 404 | 0 | match pages 375: 33, 768: 69, 1010: 298; player pages 768: 4 |
| Meeting row off its form | Meeting row (one line, or score / home / away / meta) | 11,624 | 0 | upcoming match pages, 280: 4,710, 320: 4,299, 375: 2,598, 768: 17 |
| Deserved points head split inside a word | Deserved points table | 19 | 0 | competition overview, 280–1010px |
| Score split at its dash | Unbreakable unit | 2 | 0 | played match pages, 320px |
| Filter button narrower than 44px | Filter bar | 2 | 0 | day page, nation page, 280–320px |
| Table name on 3 or more lines while its table keeps one line | Table (Last-season, Deserved per match) | 1,631 | 0 | player pages 280: 391, 320: 467, 375: 130; team pages 280: 226, 320: 321, 375: 96 |
| Any other split, overflow, overlap or cut-off text | — | 0 | 0 | — |
| Deserved points head word wider than its column (page scrolls 5–12px) | Deserved points table | 0 | 0 | competition overview, 280–768px, with the narrow heads below about 300px |

Rows by their rule, not breaks: a result row in its two-line form whose facts wrap whole (13,483 before, 13,503 after); the picker's Next tag on its own line under the title (16 before, 16 after).

## The 1010px compare

- 94 (EN), 69 (DE) and 72 (FI) match pages differ.
- One competition overview per language differs, the Deserved points table: its class list gains `heads-full` and two heads gain a wrapper span. Every box (the table, each head cell, each row) has the same position and size before and after.
- Two Team pages differ by one player age (23 to 24 in the squad row): ages are computed when the page is built, and the before build ran a day earlier.
- No page of another type differs.
- Every difference is inside a match page's Recent matches list. On main, each of those lists kept its one-line form while a row's name or meta wrapped onto a second line. Examples: "SpVgg Greuther Fürth AWAY" on the Dynamo Dresden v 1. FC Magdeburg page; "AFC Champions League Elite / 12 Oct" on Al Quwa Al Jawiya v Pakhtakor. Those lists now take their two-line form.
- No other element moved.

criteria_demonstrated:
  - **A team name never splits inside a word and never runs outside its space, 280–1010px, EN/DE/FI:** 0 name splits and 0 name overflows on every page type after; the match header's 90 sideways scrolls at 280px are 0, the names taking 18px or 15px only where 20px does not hold them (Borussia Mönchengladbach v TSG 1899 Hoffenheim: 15px at 280px, 20px at 375px).
  - **A table row that no longer fits on one line takes two lines; a row that fits keeps one:** 0 table rows beyond their form after; the 1,631 table names on 3 or more lines in a one-line table are 0, those tables taking their two-line form; the tracks equal the head in every table (0 misaligned).
  - **Fact rows side by side while the longest row fits, stacked below:** 0 fact rows over one line in a block marked fit-one, before and after, on Team and competition pages.
  - **Both switches measured per block and language by one shared script; without the script the narrow form:** every switch is `fitBlocks.mjs`, per block, in the page's language; without the script the stylesheet draws the narrow forms: the meeting row stacked below 420px, the header names at 15px below 700px, the tables' two-line rows below 600px.
  - **The site header fits at 280px:** 0 header overflow on 2,358 pages at 280px, before and after.
  - **At 1010px and wider every page is unchanged, except a row or head that breaks there today:** the layout compare differs only inside match pages' Recent matches lists that broke at 1010px on main; no other element of any page moved.
  - **The block standard states the rules, and the design check measures them:** the registry carries the rule texts and the generated element table carries them; the header team link is measured `fits`, the filter button `min-box=44px`, the head-to-head list `fit-marked`; `check_component_registry.py` 0 failures, `check_page_css.py` 0 counts off the baseline.
  - **A fresh sweep shows 0 breaks of B1, B2, B4, B6, B7 and B8, with before and after per page type and width:** the table above, measured on the branch with the narrow Deserved points heads built: every one is 0 after, at every page type and width, including the Deserved points head's scroll and split.
