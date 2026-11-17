# Rendered pages — 375px and 1280px, EN, DE and FI, then the difference list

Tool: Playwright (Chromium) against this branch's dev server with the full local data, reading
each page's DOM after load; every tab radio clicked in turn. The CI image's own runs
(`scripts/ci_local.py --mr`: design inventory at 280 to 1010px, the phone built-page checks at
260 to 768px, the chart checks at 280 to 1010px) were read for the sample-data build.

observed:
  - **/teams/bayern-munchen/, /teams/germany/, the played match Hoffenheim against Dortmund, the Bundesliga overview and Home, in EN, DE and FI, at 375px and 1280px, every tab (60 readings):** 0 "·" in the rendered text; the document never wider than the viewport; no element past the right edge; no unit wider than its box; every gap between two parts of a block 12px (36px between two groups, 24px between two boards); no explainer, chart name, card label, result line or page title ends on a single word.
  - **Tabs on the competition, team and player pages at 280, 320 and 375px in DE and FI:** the tab bar's last tab ends at the bar's edge or inside it.
  - **Played match line-up at 375px and 1280px:** each team's "Substitutes" head sits 12px under the last starter's row.
  - **Competitions, Teams and the Bundesliga overview at 280px in DE and FI:** the page is 280px wide; the index category heads keep their own case.
  - **Deserved points chart on all 34 club pages at 12 widths from 280 to 1010px (408 readings):** the difference label meets no line, dot, text or the drawing's edge.
  - **Phone screenshots (375px, EN, every tab) of both team pages, before (main at 752344df) and after:** the shared notes folder, `243-one-form-shots/`.

# What changes on the club page and the national team page

Both pages use one template, so every line applies to both: Bayern München (`/teams/bayern-munchen/`)
and Germany (`/teams/germany/`). Blocks, their order, the wording and every number stay as they are.
Phone screenshots, before and after, every tab: the shared notes folder, `243-one-form-shots/`.

## Header

- The breadcrumb's links are regular grey (were semi-bold); the page you are on is white, the links
  grey (was a lighter grey against grey).
- The team's name is 20px on a phone (was 22px) and 30px on a wide screen (was up to 28px).
- The bold venue in the line under the name is grey like the rest of the line (was a lighter grey).

## Tabs

- The tabs are 13px bold at every width (were 14px semi-bold, 13px on a phone).
- The tab you are on keeps the 2px line under it; the other tabs stay grey.

## Text

- Team, player and competition names in every row are 15px regular (some were 14px or 15px semi-bold).
- Every second line (meta line, position, note, club under a name, context under a value) is 13px grey
  (was 12px, 11.5px or 14px).
- Small labels are 11px bold: home or away ("H/A") in capitals; table column heads keep their case
  and lose their letter spacing, because capitals do not fit the number columns on a 280px screen.
- A crest or a player photo sits 8px from its name in every row and table (was 9, 10 or 8 to 20px).
- Weights are regular or bold only; semi-bold is gone. The third, lighter grey is gone: those texts
  are now the one grey.

## Competitions block

- The W, D and L counts are the result chip with the count beside it ("W 5"), where they were a wider
  chip with the count inside ("5 W"). The chip is the same chip as in the result list.
- Competition names are 15px regular (were 15px semi-bold); the note under them is 13px.
- In "Goals 25:6" and "Points 17" the words are 11px (were 12px), the numbers stay 15px bold; the
  player rows' goals and assists line takes the same form.

## Result rows and next matches

- The result chip is 11px with 4px corners (was 12px, 5px corners).
- The gap between chip, score and opponent is 12px where the row is 420px wide or more, 8px on a
  narrower row such as a phone's (was 8 to 20px, sliding with the width).
- The competition group head ("Bundesliga ›") is 18px (was 17px); 36px between two groups (was 34px).
- The date over a day's matches is 13px capitals (was 12px), the block heading's style.
- The kick-off is 15px bold (was 16px); the time zone under it is 11px bold.
- The "Next" tag is 11px with 4px corners (was 10px, round ends).

## Highs and lows (fact rows)

- Label and value are 15px (label was 14px); the context under the value is 13px (was 12px).
- On a phone the value stays right-aligned under its label (was left-aligned).
- Rows have 12px above and below (was 9px).

## Squad

- The column heads ("Goalkeepers", "Defenders") are in the block heading's style: 13px bold capitals
  (were 13px bold, not capitals).
- Player rows have 8px above and below (was 9px) and an 8px gap between photo, name and numbers
  (was 8 to 20px, sliding with the width).

## Performance tab

- Explainer sentences no longer end on a single word.
- Metric names in the league strips are 15px bold (were 14px regular), start-aligned.
- Tick labels under the strips are 11px; legend and notes 13px (were 12px).
- The "Compared with last season" table has a 1px line between rows instead of alternating stripes;
  last season's value is grey (was the lighter grey).
- In the deserved points chart the team's labels are 13px (were 12px); the difference label moves
  under the dot whenever its side of the drawing is too narrow, on either side (it checked the left
  side only), so it never runs into a tick label or off the drawing.
- "Show all metrics" is 13px bold grey (was 13px semi-bold, lighter grey).
- The deserved points table opens 12px under its explainer (was 0).

## Space

- Inside every block, 12px between any two parts: heading, explainer, list, switch, table, chart
  (was a mix of 0, 2, 8, 14, 15, 16, 18 and 26px).
- The page's side margin is 16px at every width (was 16 to 28px), the same as the site header's, so
  their edges line up.

## Site header and footer

- Menu items are 13px bold (were semi-bold); the brand is bold (was extra bold).
- Footer links and the data line are 13px (were 12.5px and 11.5px); "Imprint" is no longer italic.
