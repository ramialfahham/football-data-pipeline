# The block standard — the site's elements, their rules and their measurements

> The design chain's inventory of elements. **A page has no styling of its own; it composes
> elements from this table, and every element's CSS lives in `site_v2/src/styles/system.css` and
> nowhere else.** An element not listed here is a design decision: it is put to the CPO and
> rendered on every page it touches before it is ruled (#153). What a page SHOWS is the page's
> wireframe and its GitLab issue; what an element IS, and how it measures, is this file.
>
> The Elements table is generated from `docs/design/components.yml`, the component registry, by
> `scripts/check_component_registry.py --write`; the registry is edited, never the table.
> Two scripts read the two tables below and nothing else. `scripts/check_page_css.py` is the lint:
> a `<style>` block, a `style=` attribute or a mock's CSS string touching a Selector class fails.
> `scripts/check_design_inventory.py` is the measured check. It renders every built page and every
> page a `design-mocks/gen_*.py` writes, at 280, 320, 360, 375, 700 and 1010px. A built page is
> rendered in EN, DE and FI, and a mock in EN and, with its FI switch, in FI. Every element is
> measured as its `Measured as` column says.
> `scripts/design_inventory.py` parses both tables and fails closed on a column, key, token or
> status it does not know.
>
> Both scripts also count the site's design gaps, and `tests/fixtures/design_inventory/baseline.json`
> pins each count. The lint counts CSS outside `system.css`, width rules, banned line-break
> properties and literal text. The measured check counts sideways scroll, overflowing text, split
> words, overlapping text, classes the component registry does not list and element misses. It also counts four
> coverage gaps: a built page no row owns, a generator that fails, a generator page no row names,
> and a language a mock does not carry. A count that differs from its pin fails. A pin may not
> rise above main's, so a new page or mock arrives with no gaps. The rendered counts depend on the
> font, so they are compared only on the platform the baseline names. A merge request renders the
> narrowest and the widest width in EN and DE against `baseline_quick.json`; main renders every
> width against `baseline.json`. Text overflows when it runs
> more than 1px past its box. Two lines overlap when they still cross with a fifth of each line's
> height trimmed at the top and the bottom.

## How to read a row

- **Selector** — the CSS the element is found by, on the built pages and in the design mocks alike.
  The class names in it are the lint's guarded set.
- **Rule** — the ruling in words.
- **Measured as** — the assertions, `;`-separated: `font-size=13px` (a computed style);
  `gap(next)=14px` (this box's bottom to the next sibling's first line — its box top plus every
  padding and border down to its first text or image, so a padded date heading or fact row opening
  a block is caught); `gap(prev)=34px` (the previous sibling's box bottom to this element's box top);
  `left-edge=section` (starts where its section starts); `stripe=ink@5% from 2` (row 2, 4, …
  tinted, the rest plain); `tracks=head` (a row's grid tracks equal its table head's);
  `hover(background-color)=ink@11%` and `press(background-color)=sunk` (the pointer resting on,
  or pressing, the first visible match); `fits` (no sideways overflow); `one-line`; `visible=1`;
  `min-box=34px`. Colours are tokens read from the page (`ink`, `muted`, `accent`, `sunk`,
  `pill-ink`, …), `transparent`, or `token@pct` for a tint. Tolerances: ±0.5px on a style, ±1px on a gap, ±1/255 a colour channel.
  An assertion ending in `[>=1010px]` or `[<1010px]` is measured only at those widths, for an
  element the stylesheet shows from one width on.
- **Status** — `ruled`: the check fails on a miss. `proposed`: measured and reported, never fails.
- **Ruled on** — the issue (and date where it matters) that fixed the rule.

## Elements

| Element | Selector | Rule | Measured as | Status | Ruled on |
|---|---|---|---|---|---|
| Page shell parts | `.legacy-width, .mp` | the page shell's other parts: registered, no text of their own |  | ruled | the component registry |
| Search field | `.header-actions .searchbox` | the header's search field with its placeholder, one on every page from 1010px, where it replaces the search button; on one line in every language, nothing spilling out of it | `visible=1 [>=1010px]; visible=0 [<1010px]; one-line; fits` | ruled | `09_chrome.md` (≥ 1010px: the full field) |
| Search button | `.iconbtn.search-m` | the header's icon-only search button below 1010px, a 34px target; gone from 1010px | `visible=1 [<1010px]; visible=0 [>=1010px]; min-box=34px` | ruled | `09_chrome.md` (phone: the search icon) |
| Header row | `.header-in` | the header's brand, menu and controls fit its row; the menu stands in the row when it fits there, otherwise the menu button | `fits` | ruled | the narrow-screen fix |
| Site header brand | `.site-header .brand` | the site header's brand, in the 18-800-ink text style, never broken | `font-size=18px; font-weight=800; color=ink; one-line; fits` | ruled | the component registry |
| Site header brand iq | `.site-header .iq` | the site header's brand iq, in the 18-700-ink-2 text style, never broken | `font-size=18px; font-weight=700; color=ink-2; one-line; fits` | ruled | the component registry |
| Site header parts | `.site-header, .drawer, .hamburger, .ico, .on` | the site header's other parts: registered, no text of their own |  | ruled | the component registry |
| Site footer meta | `.fmeta` | the site footer's meta, in the 11.5-400-muted text style | `font-size=11.5px; font-weight=400; color=muted` | ruled | the component registry |
| Site footer imprint | `.imp` | the site footer's imprint, in the 12.5-400-muted text style | `font-size=12.5px; font-weight=400; color=muted` | ruled | the component registry |
| Site footer brand | `.site-footer .brand` | the site footer's brand, in the 15-800-ink text style, never broken | `font-size=15px; font-weight=800; color=ink; one-line; fits` | ruled | the component registry |
| Site footer parts | `.site-footer, .flinks` | the site footer's other parts: registered, no text of their own |  | ruled | the component registry |
| Navigation link | `nav.trail a.lnk` | a link known by its place: the logo, the menu, search, the breadcrumb, the tabs, the picker and the filters. A breadcrumb level has a 44px touch area | `min-box=44px` | ruled | the match page review |
| Breadcrumb current page | `.crumb .here` | the page you are on differs from the links at rest; the shipped site has the current page `ink-2` and the links muted, #52's mock had the two inverted | `color=ink-2` | proposed | put to the CPO on the #153 MR; measured, never fails, until ruled |
| Breadcrumb separator | `.sep` | the breadcrumb's separator, in the 13-400-muted text style, never broken | `font-size=13px; font-weight=400; color=muted; one-line; fits` | ruled | the component registry |
| Breadcrumb parts | `.lvl, .far` | the breadcrumb's other parts: registered, no text of their own |  | ruled | the component registry |
| Page heading | `.crumb + h1` | a menu page's heading under its breadcrumb, the menu item's word: the Competitions page's and the Matches page's, 30px bold ink | `font-size=30px; font-weight=700; color=ink` | ruled | #130 (the Competitions page's heading, as it ships) |
| Entity header parts | `.thead, .tid` | the entity header's other parts: registered, no text of their own |  | ruled | the component registry |
| Tab bar | `nav.tabs` | the tabs share the row and fit in one row at 375px in EN, DE and FI, no sideways scrolling | `fits` | ruled | #129 header |
| Tab | `nav.tabs .tab` | one line each, never wrapped; the side padding is what the label needs | `one-line` | ruled | #129 header |
| Tab bar parts | `.comp-tabs, .tab-in` | the tab bar's other parts: registered, no text of their own |  | ruled | the component registry |
| Block | `section` | 36px above each block; every content block has a name; a block with nothing to show is absent | `margin-top=36px` | ruled | #129 binding rules |
| Block heading | `.sechead .eyebrow` | the block's name: 13px capitals, bold, muted, over a 1px rule | `font-size=13px; font-weight=700; text-transform=uppercase; color=muted` | ruled | #129 binding rules (13px, from 11) |
| Block heading gap | `.sechead` | one distance from the block name's rule to the block's first line: 14px, nothing added by the content — a date heading, a fact row, a group or a table opening the block carries no space of its own; the name starts at the block's left edge | `gap(next)=14px; left-edge=section` | ruled | #129 binding rules; #127 correction 3 |
| Block explainer | `.bsub` | the one sentence under a block name, 13px muted | `font-size=13px; color=muted` | ruled | #129 Deserved points |
| Tab explainer | `.bsub.tab-intro` | a tab's opening sentence under the tab bar, in the block explainer's style: 13px muted | `font-size=13px; color=muted` | ruled | the Team page review |
| Competition group head | `.fxgroup:not(.rkgroup) > .gh` | the level-1 heading over a competition's match rows: crest · name · chevron, 17px bold, a 2px line under it, 34px above the group; on Home, inside the Next matches block, it keeps its line | `border-bottom-width=2px; left-edge=section` | ruled | #50; #129; 2026-09-17 ("Home with line") |
| Competition group name | `.fxgroup:not(.rkgroup) > .gh .nm` | 17px bold ink | `font-size=17px; font-weight=700; color=ink` | ruled | #50 |
| Group count | `.fxgroup > .gh .cnt` | the team count at the right of a group head: 13px semi-bold muted | `font-size=13px; font-weight=600; color=muted` | ruled | the Teams page review |
| Group spacing | `.fxgroup + .fxgroup` | 34px from one group's last row to the next group's heading | `gap(prev)=34px` | ruled | #50 |
| Metric group heading | `.rkgroup > .gh` | the level-1 heading over a metric group's boards on the Rankings tab: the competition group head's size and air, without its line; 26px to its first board | `border-bottom-width=0px; gap(next)=26px; left-edge=section` | ruled | #129 Rankings; 2026-09-17 ("Rankings without") |
| Metric group name | `.rkgroup > .gh .nm` | 17px bold ink, a clear step over the 14px board names | `font-size=17px; font-weight=700; color=ink` | ruled | #129 Rankings |
| Date heading | `.fxgroup .dh` | the date once per day, over its rows: 12px bold capitals, muted | `font-size=12px; font-weight=700; text-transform=uppercase; color=muted` | ruled | #127 (2026-09-14); #50 |
| Match row name | `.fxrow .side .nm` | a club's name, 15px ink, wraps and never truncates | `font-size=15px; color=ink; white-space=normal` | ruled | #50 |
| Match row kick-off | `.fxrow .when .t` | the kick-off in the venue's clock, 16px bold ink, on one line inside its column; "TBC" when no time | `font-size=16px; font-weight=700; color=ink; one-line; fits` | ruled | #50; #129 Matchdays; #146; the component registry |
| Match row zone | `.fxrow .when .rowtz` | the zone label under the kick-off, on every unplayed row, 10.5px muted | `font-size=10.5px; color=muted` | ruled | #50; #146 |
| Match row score | `.fxrow .side .g.winner` | a played row is the row plus the score; the winner by weight, never hue | `font-weight=700; color=ink` | ruled | #50; #129 Matchdays |
| Match row parts | `.sides, .played` | the match row's other parts: registered, no text of their own |  | ruled | the component registry |
| Table head | `.ctab-head` | the head row with the column labels (or, on a board, the board's name); its 1px rule is the table's only line; it starts at the block's left edge | `border-bottom-width=1px; left-edge=section` | ruled | #129 Table; 2026-09-17 ("head only") |
| Table head label | `.ctab-head .h:not(.rk)` | 11px bold muted | `font-size=11px; font-weight=700; color=muted` | ruled | #129 Table |
| Table row | `.ctab-row` | striped rows counted from the head, the first plain, the stripe ink at 5%; no line under a row; the row's tracks are the head's (one fixed track list per table kind) | `border-bottom-width=0px; stripe=ink@5% from 2; tracks=head` | ruled | #129 Table; 2026-09-17 ("head only") |
| Table name cell | `.ctab .tm .nm` | 14px semi-bold ink, wraps and never truncates | `font-size=14px; font-weight=600; color=ink; white-space=normal` | ruled | #129 Table |
| Table narrow row | `.ctab.fit-two .ctab-row` | a row that does not fit on one line takes two: rank, crest and name, then each number under its head | `tracks=head` | ruled | the narrow-screen fix |
| Ordered-by number | `.ctab .n.pts` | the number a table is ordered by: bold 15px accent, everywhere, no per-block colour | `font-size=15px; font-weight=700; color=accent` | ruled | #129 binding rules |
| Table parts | `.ctab` | the table's other parts: registered, no text of their own |  | ruled | the component registry |
| Board name | `.ctab.rkt .ctab-head .nmh .bt .nm` | a board is a single-value table; its name sits in the head row with the chevron, 14px bold ink, not capitals, at the block's left edge | `font-size=14px; font-weight=700; color=ink; text-transform=none` | ruled | #129 board rules; #127 correction 1 |
| Board name cell | `.ctab.rkt .ctab-head .nmh` | at the block's left edge | `left-edge=section` | ruled | #127 correction 3 |
| Board sub-line | `.ctab.rkt .tm .ent .sub` | a player's club under the name, 12px muted | `font-size=12px; color=muted` | ruled | #129 Rankings |
| Board spacing | `.board + .board` | 26px between boards | `gap(prev)=26px` | ruled | #40, #41 (the shipped board) |
| Table group heading | `.ctab-section > .gh` | the level-2 heading over one table of a group stage ("Group A"): 14px bold, a 1px line | `border-bottom-width=1px; left-edge=section` | ruled | #129 Table (rejected for Rankings, kept for tables) |
| Table group name | `.ctab-section > .gh .nm` | 14px bold ink | `font-size=14px; font-weight=700; color=ink` | ruled | #129 Table |
| Standings table goal difference | `.ctab .n.gd` | the standings table's goal difference, in the 13-400-ink-2 text style, never broken | `font-size=13px; font-weight=400; color=ink-2; one-line; fits` | ruled | the component registry |
| Standings table wdl head | `.ctab-head .h.wdl` | the standings table's wdl head, in the 11-700-muted text style, never broken | `font-size=11px; font-weight=700; color=muted; one-line; fits` | ruled | the component registry |
| Standings table wdl | `.ctab .n.wdl` | the standings table's wdl, in the 13-400-muted text style, never broken | `font-size=13px; font-weight=400; color=muted; one-line; fits` | ruled | the component registry |
| Deserved points table shots head | `.ctab-head .hs` | the deserved points table's shots head, in the 11-600-muted text style | `font-size=11px; font-weight=600; color=muted` | ruled | the component registry |
| Deserved points table parts | `.dpt` | the deserved points table's other parts: registered, no text of their own |  | ruled | the component registry |
| Trend | `.ctab.yoyt .n.tr` | ▲ in the accent when this season is better, ▼ in the loss red when worse, "–" when the shown values are equal | `font-size=13px` | ruled | the Team page review |
| Last-season table parts | `.yoy-list` | the last-season table's other parts: registered, no text of their own |  | ruled | the component registry |
| Fact row label | `.frow .fl` | label, 14px ink regular | `font-size=14px; color=ink; font-weight=400` | ruled | #129 the fact row |
| Fact row value | `.frow .fvv b` | the value, bold 15px accent — the number the row is about | `font-size=15px; font-weight=700; color=accent` | ruled | #129 binding rules, Block 3 |
| Fact row context | `.frow .sub` | the context under the value, 12px muted | `font-size=12px; color=muted` | ruled | #129 the fact row |
| Fact row block | `.frow` | label and value side by side while the block's longest row fits on one line; otherwise every row stacks its value under its label | `fits` | ruled | the narrow-screen fix |
| Fact row parts | `.facts, .fv` | the fact row's other parts: registered, no text of their own |  | ruled | the component registry |
| Chevron heading link | `a.cnm` | a heading that leads somewhere carries a chevron at rest and is never underlined | `text-decoration-line=none` | ruled | #52; #129 binding rules |
| Chevron | `a.cnm .chev` | 15px, muted at rest | `color=muted` | ruled | #52 |
| Header team link | `.mast a.team` | a team in the match header leads to its team page: one link with the chevron at rest, never underlined | `text-decoration-line=none` | ruled | the match page review |
| Match header competition head | `.mast .mcomp > .gh` | the competition group head opening the match header: a heading link to the competition's page, the 2px line under it | `border-bottom-width=2px` | ruled | the match page review |
| Match header score | `.mast .vs.score` | a played match's final score where "vs" stands, regular weight, ink; from 700px only, below which each team's goals close its line | `font-weight=400; color=ink` | ruled | the played match page review |
| Match header winner | `.mast .winner` | the winning side's goals by weight, never by hue | `font-weight=700` | ruled | the played match page review |
| Match header team goals | `.mast .team .sg` | under 700px a team's goals close its line, 24px ink, the winner's bold | `font-size=24px; color=ink` | ruled | the played match page review |
| Match header result line | `.mast .resline` | the line under the score, 13px muted: after penalties the score after extra time, its numbers bold; on an award, how it came about | `font-size=13px; color=muted` | ruled | the played match page review |
| Match header kick off | `.mast .kick` | the match header's kick off, in the 13-400-muted text style | `font-size=13px; font-weight=400; color=muted` | ruled | the component registry |
| Match header dash | `.mast .dash` | the match header's dash, in the 40-400-muted text style, never broken | `font-size=40px; font-weight=400; color=muted; one-line; fits` | ruled | the component registry |
| Match header parts | `.vh, .played` | the match header's other parts: registered, no text of their own |  | ruled | the component registry |
| List row | `.lrow` | one row of a list, a line between rows, nothing cut off. Its name is 15px, its second line 12px muted, its numbers 15px bold | `fits` | ruled | the match page review |
| Result chip | `.resrow .pill` | one match's W, D or L from a team's side, in the page's language, on the result colour | `font-size=12px; font-weight=700; color=pill-ink` | ruled | the match page review |
| Result row | `.resrow` | result chip · score · opponent (crest, name, home or away) · competition · date. One line where its list is 420px wide or more, two lines below | `fits` | ruled | the match page review |
| Result row score | `.resrow .rscore` | the score from the row's side, 15px bold ink | `font-size=15px; font-weight=700; color=ink` | ruled | the match page review |
| Result row name | `.resrow .ropp` | the club, 15px ink, wrapping, never cut off | `font-size=15px; color=ink; white-space=normal` | ruled | the match page review |
| Result row meta | `.resrow:not(.goal) .rmeta` | the competition's name and the date, 12px muted; the name wraps between words, the date never splits | `font-size=12px; color=muted` | ruled | the match page review; the component registry |
| Meeting row | `.resrow.meet` | a meeting of the two teams: the result row without its chip. The score is in the match's order, the home side first, the date with its year | `fits` | ruled | the match page review |
| Goal row | `.resrow.goal` | a goal: the score after it, then the scorer with the crest of the side it counts for. The second line holds the minute with the assist, own goal or penalty. Without minutes the row has no score | `fits` | ruled | the played match page review |
| Goal row meta | `.resrow.goal .rmeta` | the goal's minute and its assist, own goal or penalty: 14px ink-2, larger and lighter than a list row's second line | `font-size=14px; color=ink-2` | ruled | the played match page review |
| Result row home away | `.resrow .ha` | the result row's home away, in the 11-600-muted text style, never broken | `font-size=11px; font-weight=600; color=muted; one-line; fits` | ruled | the component registry |
| Result row parts | `.rlist, .scorer` | the result row's other parts: registered, no text of their own |  | ruled | the component registry |
| Form parts | `.W, .D, .L` | the form's other parts: registered, no text of their own |  | ruled | the component registry |
| Player row | `.plrow` | photo · name over position · goals and assists on the right at every width; two lines below 375px when the row is short of room; on a line-up, the minutes played | `fits` | ruled | the match page review; the component registry |
| Player row name | `.plrow .pname .nm` | 15px regular ink, wrapping, never cut off | `font-size=15px; font-weight=400; color=ink; white-space=normal` | ruled | the match page review |
| Player row position | `.plrow .pname .ps` | 12px muted. On a line-up the substitution follows after a middle dot. It is the minute a starter went off, or a substitute came on and for whom | `font-size=12px; color=muted` | ruled | the match page review |
| Player row number | `.plrow .pstat b` | 15px bold ink | `font-size=15px; font-weight=700; color=ink` | ruled | the match page review |
| Column head | `.rcol .colhead` | a list column's name, 13px bold muted; one fact may follow after a middle dot (a team's formation); a second head inside the column opens its second list | `font-size=13px; font-weight=700; color=muted` | ruled | the played match page review |
| Two columns parts | `.rsplit, .sheets, .off` | the two columns's other parts: registered, no text of their own |  | ruled | the component registry |
| Competition row | `.lrow.tc` | one competition of a team's season: crest, name and a muted note, with the standing or the cup's outcome on the right. A table's row adds the W, D and L counts, goals and points below. Narrow, the standing opens the second line | `fits` | ruled | the Team page review |
| Competition row name | `.tc .tc-name` | 15px semi-bold ink; the note after it 12px muted | `font-size=15px; font-weight=600; color=ink` | ruled | the Team page review |
| Competition row chip | `.cchip` | the competition row's chip, in the 12.5-700-pill-ink text style, never broken | `font-size=12.5px; font-weight=700; color=pill-ink` | ruled | the component registry |
| Squad grid | `.sqgrid` | the squad's player rows in two columns where each keeps 280px, otherwise one | `fits` | ruled | the Team page review |
| Strip plot row | `.rs-row` | a metric's name, the league's values with every team's mark, and the team's rank over its value; drawn by `team/TeamLeagueStrips.astro` | `fits` | ruled | the Team page review |
| Strip plot value | `.rs-val` | the team's rank over its value; drawn by `team/TeamLeagueStrips.astro` | `font-size=15px; font-weight=700; color=ink` | ruled | the Team page review |
| Strip plot band | `.rs-row .rs-band` | a strip plot row's strip: its line with every team's mark on it | `fits` | ruled | the chart theme |
| Scatter plot | `.dp-chart` | each team's shots on target difference per match against its points, with the deserved points line; drawn by `team/TeamDeserved.astro` | `fits` | ruled | the Team page review |
| Comparison element | `.cmp` | two teams' numbers on one metric list, each metric's two values, name and bar; drawn by `fixture/MetricComparison.astro` | `fits` | ruled | the played match page review |
| Comparison team name | `.cmp .formhead .h` | each team's name over its column, in the chart legend's style | `font-size=12px; font-weight=400; color=ink-2` | ruled | the chart theme |
| Comparison parts | `.cmp .cmp-team, .cmp-home, .cmp-away, .cmp-row, .cmp-val, .cmp-mid, .cmp-label` | the comparison element's parts, drawn by `fixture/MetricComparison.astro` and `fixture/MetricRow.astro` | `fits` | ruled | the match page review |
| Switched-off row | `.nonkey` | a row or group heading that Show all metrics hides while off | `fits` | ruled | the match page review |
| Comparison better value | `.cmp-val.chart-better` | the better team's value | `color=accent` | ruled | the match page review |
| Comparison better bar | `.cmp .chart-bar > .chart-better > span` | the better team's bar | `background-color=accent` | ruled | the match page review |
| Metric switch | `.tsw-lbl` | "Show all metrics" at the top right of a metric comparison: off by default, the key metrics only; on, every metric in its place, the order never changing; a group heading with no key row hidden while off; the track neutral grey when on | `font-size=13px; font-weight=600; color=ink-2` | ruled | the match page review |
| Chart | `.chart, .chart .chart-wide, .chart .chart-narrow` | every chart's box. Under 480px every chart takes its narrow form. The look is in `system.css` (Charts), the layout numbers in `lib/chartTheme.ts` | `fits` | ruled | the chart theme |
| Chart legend | `.chart-legend .chart-key` | above its chart, one key per mark: the mark, then its name; drawn by `ui/ChartLegend.astro` | `font-size=12px; color=ink-2` | ruled | the chart theme |
| Chart axis | `.chart-axis` | an axis line and its outward ticks; a strip plot's line | `fits` | ruled | the chart theme |
| Chart tick label | `.chart-tick, .chart-tick.chart-end` | a tick label, an axis title's second line, a strip plot's direction note | `font-size=11px` | ruled | the chart theme |
| Chart note | `.chart-note` | an axis title and the label of the team's difference | `font-size=12px` | ruled | the chart theme |
| Chart label | `.chart-label` | the team's name beside its mark | `font-size=12px` | ruled | the chart theme |
| Chart name | `.chart-name` | a strip plot row's metric name | `font-size=14px; color=ink` | ruled | the chart theme |
| Chart mark | `.chart-dot, .chart-dot.chart-me` | every other team's mark and the team's mark, the same in every chart and its legend | `fits` | ruled | the chart theme |
| Chart bar | `.chart-bar, .chart-bar > .chart-better` | two bars meeting at the centre, each its value's share of the larger | `fits` | ruled | the chart theme |
| Chart line | `.chart-line, .chart-ref, .chart-gap` | a reference line the values are read against, and the dotted line of the team's distance from it | `fits` | ruled | the chart theme |
| Chart parts | `.chart-dot:not(.chart-me), .chart-dot.chart-me` | the chart's other parts: registered, no text of their own |  | ruled | the component registry |
| Schedule block | `.md > section` | the Matchdays tab's only block, under its round's picker line: its name, then the date heading per day and the match rows; one round's block on screen at a time, no script | `visible=1; margin-top=36px` | ruled | #129 Matchdays |
| Matchday picker | `.mdnav .mdstep` | its own full-width line under the tab bar: ‹ MATCHDAY N › with the Next tag, the arrows pinned to the edges, the title centred, a 2px line under; one matchday on screen at a time; no script | `visible=1; border-bottom-width=2px` | ruled | #129 Matchdays |
| Picker title | `.mdstep .mdtitle .num` | 13px bold capitals ink | `font-size=13px; font-weight=700; text-transform=uppercase; color=ink` | ruled | #129 Matchdays |
| Picker arrow | `.mdstep .step` | a 34px target at each edge | `min-box=34px` | ruled | #129 Matchdays |
| Matchday picker parts | `.md-in, .next` | the matchday picker's other parts: registered, no text of their own |  | ruled | the component registry |
| Filter row | `.seg` | a filter by type and one by region on the Competitions and Matches pages, each a sunk ground holding its buttons or its dropdown | `background-color=sunk` | ruled | the Filter bar design |
| Filter button | `.seg .seg-btn` | 13px, each on one line | `font-size=13px; one-line` | ruled | the Filter bar design |
| Filter bar | `.fbar` | the buttons while each row of them fits on one line, otherwise a dropdown per filter. A filter offers only the choices its rows carry, and none that would leave no row | `fits` | ruled | the Filter bar design |
| Filter dropdown | `.seg.sel .sel-in` | 13px bold ink; side by side while each holds its longest choice, stacked full width below that | `font-size=13px; font-weight=700; color=ink; fits` | ruled | the Filter bar design |
| Filter bar parts | `.seg-in, .categories` | the filter bar's other parts: registered, no text of their own |  | ruled | the component registry |
| Fold | `.fold-ctl` | Under a list's shown rows: "Show all {n}" closed, "Show less" open, with the chevron down or up: 13px semi-bold ink-2 | `font-size=13px; font-weight=600; color=ink-2` | ruled | the shared fold review |
| Fold label | `.lbl` | the fold's label, in the 13-600-ink-2 text style, never broken | `font-size=13px; font-weight=600; color=ink-2; one-line; fits` | ruled | the component registry |
| Fold parts | `.closed, .opened, .fold-in, .fold-rest` | the fold's other parts: registered, no text of their own |  | ruled | the component registry |
| Competition list name | `.comp-row .comp-name` | the competition list's name, in the 14-600-ink text style | `font-size=14px; font-weight=600; color=ink` | ruled | the component registry |
| Competition list region | `.comp-row .comp-region` | the competition list's region, in the 12-400-muted text style | `font-size=12px; font-weight=400; color=muted` | ruled | the component registry |
| Competition list parts | `.compindex, .comp-grid, .comp-category, .comp-meta` | the competition list's other parts: registered, no text of their own |  | ruled | the component registry |
| Team list parts | `.teamindex, .tblock, .tgroups-region, .tview-all, .tview-region` | the team list's other parts: registered, no text of their own |  | ruled | the component registry |
| Fitted block parts | `.fit-one` | the fitted block's other parts: registered, no text of their own |  | ruled | the component registry |
| Unbreakable unit parts | `.nb` | the unbreakable unit's other parts: registered, no text of their own |  | ruled | the component registry |
| Name in whole words | `.ctab .tm .nm, .fxrow .side .nm, .club .cn` | a team name wraps only between words; no word splits or runs past the name's space | `whole-words` | ruled | the narrow-screen fix |
| Legacy board value | `.brow .v b` | the legacy Home mocks' boards: the value follows the ordered-by number | `font-size=15px; font-weight=700; color=accent` | ruled | #129 binding rules |
| Fitted block | `.header-in, .ctab, :has(> .frow), .fbar, .selbar, .fxrow:has(.topmatch)` | a block with a narrow form carries its measured form, fit-one or fit-two, once the page has loaded | `fit-marked` | ruled | the narrow-screen fix |
| Row link | `a.ctab-row, a.fxrow, a.frow, a.brow, a.comp-row` | a row that leads somewhere is one link, the whole row; one hover tint for every row link, ink at 11% (twice the stripe); the press tint `sunk`; no underline inside a row | `hover(background-color)=ink@11%; press(background-color)=sunk; text-decoration-line=none` | ruled | #129 binding rules; #52; #127 (2026-09-14) |
| Prose link | `p a, .lede a, .sub a, .bnote a` | the one place an underline stays: a link inside running text | `text-decoration-line=underline` | ruled | #52 |
| Tag | `.nexttag, .fxrow .topmatch` | Next (on the picker's title) and Top match (on the flagged row, before the kick-off): 10px bold capitals in an accent pill. Narrow, a row's tag takes its own line above the home team, left-aligned | `font-size=10px; font-weight=700; text-transform=uppercase; background-color=accent; color=pill-ink` | ruled | the competition Matchdays design; the Home design; the narrow-screen fix |
| Page width | `body:not(.legacy-width) :is(.header-in, .footer-in)` | the header row and the footer share the content column's one width, 960px; a page awaiting its new design keeps the earlier widths | `max-width=960px` | ruled | the page width review |

Not measured, still the rule: the header is identical on every tab (crest · name · meta line) and
there is no page title under the tab bar (#129); a board shows five rows on a competition page and
seven on Home, a zero is not a rank on a most-first board (#129 board rules); a board does not say
which way it ranks — its name and its top value do (CPO, #151 MR, replacing #129's "fewest first"
note); a name, a "Matchday N" and a date never break inside themselves
(#129 the fact row). Those are content rules, checked where the content is built.

Not measured, still the rule: a team's crest in the match header is 52px, and every other crest is
24px.

## Pages

Every built page type and every mock page. `Source` is `site_v2/dist` for a built page, or the
mock's generator, which the check runs as `gen_*.py --out DIR`, writing every page it draws into
DIR. `URL` is a glob under `site_v2/dist` that owns every file it matches (a literal URL wins over
a glob), or the file the generator writes. `FI` governs the
MOCKS only — it says how the check reaches a mock's Finnish (`toggle`: the mock's FI switch;
`none`: EN only) — while a built page's other locales come from its URL, so `path` on a built row
means every locale the site publishes, German included;
`Expect` names elements the page must show;
an entry ending in a width condition (`Search field [>=1010px]`) is required at those widths only.
The lint reads this table too: a mock generator listed here (and every module it imports) may
carry no CSS that touches an inventory class; a generator not listed is counted against the
baseline. A page no row names is still rendered and measured, and counted as a gap. The renders
of record in `design-mocks/renders/` are not pages; the generators that wrote them are.

| Page | Kind | Source | URL | FI | Expect |
|---|---|---|---|---|---|
| Home | built | `site_v2/dist` | `en/index.html` | path | Block heading, Block explainer, Competition group head, Date heading, Fold, Match row kick-off, Match row zone, Board name, Search field [>=1010px], Search button [<1010px] |
| Competitions index | built | `site_v2/dist` | `en/competitions/index.html` | path | Filter row, Row link, Search field [>=1010px], Search button [<1010px] |
| Competition overview | built | `site_v2/dist` | `en/bundesliga/index.html` | path | Block heading, Table head, Table row, Ordered-by number, Tab bar, Search field [>=1010px], Search button [<1010px] |
| Competition matchdays | built | `site_v2/dist` | `en/bundesliga/matches/index.html` | path | Block heading, Schedule block, Matchday picker, Tag, Date heading, Match row kick-off, Tab bar, Search field [>=1010px], Search button [<1010px] |
| Competition rankings | built | `site_v2/dist` | `en/bundesliga/stats/index.html` | path | Block heading, Metric group heading, Board name, Board sub-line, Ordered-by number, Tab bar, Search field [>=1010px], Search button [<1010px] |
| Match page | built | `site_v2/dist` | `en/*/matches/*/index.html` | path | Block heading, Match header competition head, Navigation link, Search field [>=1010px], Search button [<1010px] |
| Played match page | built | `site_v2/dist` | `en/bundesliga/matches/2026-09-05-tsg-1899-hoffenheim-vs-borussia-dortmund/index.html` | path | Match header winner, Goal row meta, Comparison element, Metric switch, Comparison team name, Column head, Search field [>=1010px], Search button [<1010px] |
| Team page | built | `site_v2/dist` | `en/teams/*/index.html` | path | Block heading, Tab bar, Competition row, Result row, Match row kick-off, Tag, Fact row value, Player row, Squad grid, Search field [>=1010px], Search button [<1010px] |
| Teams page | built | `site_v2/dist` | `en/teams/index.html` | path | Page heading, Filter row, Block heading, Competition group head, Group count, Fold, Row link, Search field [>=1010px], Search button [<1010px] |
| Matches page | built | `site_v2/dist` | `en/matches/index.html` | path | Page heading, Filter row, Matchday picker, Picker title, Picker arrow, Block heading, Competition group head, Competition group name, Fold, Match row kick-off, Match row score, Search field [>=1010px], Search button [<1010px] |
| Matches day page | built | `site_v2/dist` | `en/matches/*/index.html` | path | Page heading, Matchday picker, Picker title, Picker arrow, Block heading, Competition group head, Competition group name, Fold, Match row score, Search field [>=1010px], Search button [<1010px] |
| competition-overview | mock | `gen_overview_after_teams.py` | `competition_overview_after_teams_v2.html` | toggle | Block heading, Table head, Table row, Ordered-by number, Fact row value, Tab bar |
| competition-matchdays | mock | `gen_competition_matchdays.py` | `competition_matchdays_mock_v1.html` | toggle | Block heading, Matchday picker, Tag, Date heading, Match row kick-off, Tab bar |
| competition-rankings | mock | `gen_competition_teams.py` | `competition_teams_mock_v1.html` | toggle | Block heading, Metric group heading, Board name, Board sub-line, Tab bar |
| home | mock | `gen_home_with_rules.py` | `home_with_rules_v1.html` | toggle | Block heading, Competition group head, Board name, Date heading |
| competition-hub league | mock | `gen_competition_hub.py` | `competition_hub_mock_league.html` | toggle | Block heading, Table head, Table row, Tab bar |
| competition-hub groups | mock | `gen_competition_hub.py` | `competition_hub_mock_groups.html` | toggle | Table group heading, Table row |
| competition-hub cup | mock | `gen_competition_hub.py` | `competition_hub_mock_cup.html` | toggle | Block heading, Tab bar |
| competition-hub offseason | mock | `gen_competition_hub.py` | `competition_hub_mock_offseason.html` | toggle | Block heading, Tab bar |
| matches next | mock | `gen_matches.py` | `matches_next_mock.html` | toggle | Competition group head, Date heading, Match row kick-off |
| matches past | mock | `gen_matches.py` | `matches_past_mock.html` | toggle | Competition group head, Match row score |
| matches hub | mock | `gen_matches_hub.py` | `matches-hub_2026-09-19.html` | toggle | Block heading, Matchday picker, Competition group head, Match row kick-off |
| top players | mock | `gen_top_players.py` | `top_players_mock.html` | toggle | Legacy board value |
| top teams | mock | `gen_top_teams.py` | `top_teams_mock.html` | toggle | Legacy board value |
| home legacy | mock | `gen_home.py` | `home_mock.html` | toggle | Block heading, Competition group head, Legacy board value |
