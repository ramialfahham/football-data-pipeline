# Verification — one form per part, sitewide

Read from this branch's dev server (port 4325, the full local data with national teams) and, for
"before", from a checkout of main at 752344df on port 4326, with the same data.

## Parts page, distinct forms per kind

`python scripts/parts_page.py --base http://localhost:4325`, 15 pages at 375px and 1000px.
"Forms" counts every distinct form of every part in the kind, first and last rows and content
variants included; "by page" counts the parts that differ from page to page.

| Kind | Forms before | Forms after | By page before | By page after |
|---|---|---|---|---|
| Page heading | 5 | 5 | 2 | 2 |
| Section heading | 6 | 5 | 1 | 1 |
| Explainer | 4 | 4 | 1 | 1 |
| Group heading | 9 | 7 | 2 | 1 |
| Competition name | 3 | 3 | 0 | 0 |
| Team name | 13 | 13 | 3 | 3 |
| Player name | 1 | 1 | 0 | 0 |
| Date | 5 | 5 | 1 | 1 |
| Score | 10 | 9 | 1 | 1 |
| Result badge | 18 | 15 | 4 | 3 |
| Position / value | 28 | 25 | 5 | 3 |
| Meta line | 25 | 24 | 4 | 3 |
| Label | 16 | 14 | 3 | 1 |
| Tab bar | 12 | 12 | 1 | 0 |
| Matchday picker | 7 | 7 | 1 | 1 |
| Filter | 10 | 11 | 1 | 2 |
| Stat tile | 4 | 4 | 0 | 0 |
| Table head | 20 | 16 | 2 | 2 |
| Row | 88 | 87 | 8 | 8 |
| Chevron link | 10 | 10 | 3 | 3 |
| Crest | 8 | 8 | 1 | 1 |
| Player photo | 1 | 1 | 0 | 0 |
| Chart mark | 37 | 37 | 5 | 5 |
| Site chrome | 19 | 18 | 1 | 0 |
| Same text on one page in more than one style | 158 | 134 | | |

## Every remaining difference between forms of one part, after

Position in a list (first or last, or first after the block's heading):
- Column head, block explainer, filter bar: margin-top 0 as the first part of its container, 12px after another part (the block's rhythm).
- Date heading, result, meeting and goal rows, competition and fact rows: no top padding as the first line after a heading or explainer.
- Table rows, list rows, fact rows, the table's narrow row: no line under the last row.

State:
- Result chip, competition row chip, form chips: win, draw or loss colour.
- Tab: ink for the tab you are on, muted for the others. Filter button: ink on the surface when chosen.
- Trend: accent better, loss red worse, muted equal. Match header goals: bold for the winner.

Content:
- Result row column gap: 12px in a row 420px wide or more, 8px in a narrower row (the result row's registered narrow form, so a long word fits at 280px); the player row likewise below 280px.
- Result row score line-height 24px beside a chip, 22.5px in a meeting row, which has no chip.
- Player row position and result row meta are a units line where they hold a substitution or the player's line, a single line otherwise.
- Competition row: 12px above and below, the two-line row (name over note); list rows of one line carry their 8px inside the row.
- Fact row and table, narrow form: when a block's longest row does not fit, value under label (2px apart) and numbers under their heads (4px); the registered narrow form, chosen by content and language.
- Result row meta right or left: one line where every row of the list fits, two lines where it does not (the registered two-line form).
- Comparison team name, comparison value and form chips: the home side starts at the left edge, the away side ends at the right edge; the chip letters are centred either way.
- Table head label: left over the name column, right over number columns, centred over the trend column.
- Crest: the 24px list crest (11px initials) and the 52px header crest (15px initials, centred in the match header).
- Chart marks, lines, bars and axis: dots, lines and bars hold no text, so their font values are inherited and never drawn; an SVG line and a strip's span draw the axis in their own way; the two halves of a bar are rounded on their outer ends.

criteria_demonstrated:
  - **Parts page:** run before and after against the local dev server (table above). After the change the parts that differ from page to page fall from 50 to 42 and the same text in more than one style from 158 to 134; every remaining difference between forms of one part is listed above as position in a list, state or content, with the reason for each.
  - **Fixed values:** a scan of every declaration in `site_v2/src/styles/system.css` finds 0 font sizes outside 11, 13, 15, 18, 20 and 30px, 0 weights outside 400 and 700, 0 corner radii outside 4px, 8px, 50% and 0, and 0 spacing values outside 2, 4, 8, 12, 16, 24, 36 and 48px (negative margins -4px and -8px only); `docs/design/components.yml` holds exactly those values in its text and spacing sets.
  - **Registry and pins:** `python scripts/check_component_registry.py` reports 0 failures; its pins fell (stylesheet values 8 to 0, unlisted classes 36 to 34, the lines-unmeasured gap 1 to 0, the spacing set 39 to 11, the text set 35 to 19); `python scripts/check_page_css.py` reports 0 findings with the 430px width rule falling from 2 to 1 and the 520px rule from 1 to 0; the long-sentence pin of the generated block standard falls from 10 to 9; no count rose. The design inventory's own self-test still goes red on exactly its ten defects and green on the page as ruled.
  - **No dot, no sideways scroll:** Playwright on `/teams/bayern-munchen/`, `/teams/germany/`, the played match Hoffenheim against Dortmund, the Bundesliga overview and Home, in EN, DE and FI, at 375px and 1280px, every tab clicked: 0 "·" in the rendered text, the page never wider than the viewport, no element past the right edge, no unit wider than its box.
  - **Same form, no split unit, no orphan word:** on those 60 page and tab readings every gap between two parts of a block is 12px (36px between two groups, 24px between two boards), the tabs are 13px bold with only colour and the 2px line differing, and no explainer, chart name, card label, result line or page title ends its last line on a single word.
  - **No block, order, wording or value change:** the one markup change is the competition row's W, D and L counts, which show the same chip letter and the same count (the chip, then the count); every other change is in `system.css`; the club page's Bundesliga row reads chip W then 5, chip D then 2, chip L then 0, where main read 5 W, 2 D, 0 L: the same three letters and values.
