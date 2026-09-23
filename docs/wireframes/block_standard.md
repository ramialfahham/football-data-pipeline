# The block standard — the site's elements, their rules and their measurements

> The design chain's inventory of elements. **A page has no styling of its own; it composes
> elements from this table, and every element's CSS lives in `site_v2/src/styles/system.css` and
> nowhere else.** An element not listed here is a design decision: it is put to the CPO and
> rendered on every page it touches before it is ruled (#153). What a page SHOWS is the page's
> wireframe and its GitLab issue; what an element IS, and how it measures, is this file.
>
> Two scripts read the two tables below and nothing else: `scripts/check_page_css.py` (the lint:
> a `<style>` block, a `style=` attribute or a mock's CSS string touching a class named in the
> Selector column fails) and `scripts/check_design_inventory.py` (the measured check: every page in
> the Pages table rendered at 375px and 700px in every locale the site publishes — EN, DE and FI
> for a built page, EN and FI for a mock, which carries no German text — every element measured as its
> `Measured as` column says). `scripts/design_inventory.py` parses both tables and fails closed on
> a column, key, token or status it does not know. A rendered page that shows none of these elements
> fails too.

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
- **Status** — `ruled`: the check fails on a miss. `proposed`: measured and reported, never fails.
- **Ruled on** — the issue (and date where it matters) that fixed the rule.

## Elements

| Element | Selector | Rule | Measured as | Status | Ruled on |
|---|---|---|---|---|---|
| Block | `section` | 36px above each block; every content block has a name; a block with nothing to show is absent | `margin-top=36px` | ruled | #129 binding rules |
| Block heading | `.sechead .eyebrow` | the block's name: 13px capitals, bold, muted, over a 1px rule | `font-size=13px; font-weight=700; text-transform=uppercase; color=muted` | ruled | #129 binding rules (13px, from 11) |
| Block heading gap | `.sechead` | one distance from the block name's rule to the block's first line: 14px, nothing added by the content — a date heading, a fact row, a group or a table opening the block carries no space of its own; the name starts at the block's left edge | `gap(next)=14px; left-edge=section` | ruled | #129 binding rules; #127 correction 3 |
| Block explainer | `.bsub` | the one sentence under a block name, 13px muted | `font-size=13px; color=muted` | ruled | #129 Deserved points |
| Competition group head | `.fxgroup:not(.rkgroup) > .gh` | the level-1 heading over a competition's match rows: crest · name · chevron, 17px bold, a 2px line under it, 34px above the group; on Home, inside the Next matches block, it keeps its line | `border-bottom-width=2px; left-edge=section` | ruled | #50; #129; 2026-09-17 ("Home with line") |
| Competition group name | `.fxgroup:not(.rkgroup) > .gh .nm` | 17px bold ink | `font-size=17px; font-weight=700; color=ink` | ruled | #50 |
| Group spacing | `.fxgroup + .fxgroup` | 34px from one group's last row to the next group's heading | `gap(prev)=34px` | ruled | #50 |
| Metric group heading | `.rkgroup > .gh` | the level-1 heading over a metric group's boards on the Rankings tab: the competition group head's size and air, without its line; 26px to its first board | `border-bottom-width=0px; gap(next)=26px; left-edge=section` | ruled | #129 Rankings; 2026-09-17 ("Rankings without") |
| Metric group name | `.rkgroup > .gh .nm` | 17px bold ink, a clear step over the 14px board names | `font-size=17px; font-weight=700; color=ink` | ruled | #129 Rankings |
| Table group heading | `.ctab-section > .gh` | the level-2 heading over one table of a group stage ("Group A"): 14px bold, a 1px line | `border-bottom-width=1px; left-edge=section` | ruled | #129 Table (rejected for Rankings, kept for tables) |
| Table group name | `.ctab-section > .gh .nm` | 14px bold ink | `font-size=14px; font-weight=700; color=ink` | ruled | #129 Table |
| Table head | `.ctab-head` | the head row with the column labels (or, on a board, the board's name); its 1px rule is the table's only line; it starts at the block's left edge | `border-bottom-width=1px; left-edge=section` | ruled | #129 Table; 2026-09-17 ("head only") |
| Table head label | `.ctab-head .h:not(.rk)` | 11px bold muted | `font-size=11px; font-weight=700; color=muted` | ruled | #129 Table |
| Table row | `.ctab-row` | striped rows counted from the head, the first plain, the stripe ink at 5%; no line under a row; the row's tracks are the head's (one fixed track list per table kind) | `border-bottom-width=0px; stripe=ink@5% from 2; tracks=head` | ruled | #129 Table; 2026-09-17 ("head only") |
| Table name cell | `.ctab .tm .nm` | 14px semi-bold ink, wraps and never truncates | `font-size=14px; font-weight=600; color=ink; white-space=normal` | ruled | #129 Table |
| Board name | `.ctab.rkt .ctab-head .nmh .bt .nm` | a board is a single-value table; its name sits in the head row with the chevron, 14px bold ink, not capitals, at the block's left edge | `font-size=14px; font-weight=700; color=ink; text-transform=none` | ruled | #129 board rules; #127 correction 1 |
| Board name cell | `.ctab.rkt .ctab-head .nmh` | at the block's left edge | `left-edge=section` | ruled | #127 correction 3 |
| Board sub-line | `.ctab.rkt .tm .ent .sub` | a player's club under the name, 12px muted | `font-size=12px; color=muted` | ruled | #129 Rankings |
| Board spacing | `.board + .board` | 26px between boards | `gap(prev)=26px` | ruled | #40, #41 (the shipped board) |
| Legacy board value | `.brow .v b` | the built Home's boards until #127 rebuilds them as single-value tables: the value follows the ordered-by number | `font-size=15px; font-weight=700; color=accent` | ruled | #129 binding rules |
| Schedule block | `.md > section` | the Matchdays tab's only block, under its round's picker line: its name, then the date heading per day and the match rows; one round's block on screen at a time, no script | `visible=1; margin-top=36px` | ruled | #129 Matchdays |
| Match row name | `.fxrow .side .nm` | a club's name, 15px ink, wraps and never truncates | `font-size=15px; color=ink; white-space=normal` | ruled | #50 |
| Match row kick-off | `.fxrow .when .t` | the kick-off in the venue's clock, 16px bold ink; "TBC" when no time | `font-size=16px; font-weight=700; color=ink` | ruled | #50; #129 Matchdays; #146 |
| Match row zone | `.fxrow .when .rowtz` | the zone label under the kick-off, on every unplayed row, 10.5px muted | `font-size=10.5px; color=muted` | ruled | #50; #146 |
| Match row score | `.fxrow .side .g.winner` | a played row is the row plus the score; the winner by weight, never hue | `font-weight=700; color=ink` | ruled | #50; #129 Matchdays |
| Date heading | `.fxgroup .dh` | the date once per day, over its rows: 12px bold capitals, muted | `font-size=12px; font-weight=700; text-transform=uppercase; color=muted` | ruled | #127 (2026-09-14); #50 |
| Fact row label | `.frow .fl` | label, 14px ink regular | `font-size=14px; color=ink; font-weight=400` | ruled | #129 the fact row |
| Fact row value | `.frow .fvv b` | the value, bold 15px accent — the number the row is about | `font-size=15px; font-weight=700; color=accent` | ruled | #129 binding rules, Block 3 |
| Fact row context | `.frow .sub` | the context under the value, 12px muted | `font-size=12px; color=muted` | ruled | #129 the fact row |
| Ordered-by number | `.ctab .n.pts` | the number a table is ordered by: bold 15px accent, everywhere, no per-block colour | `font-size=15px; font-weight=700; color=accent` | ruled | #129 binding rules |
| Row link | `a.ctab-row, a.fxrow, a.frow, a.brow, a.comp-row` | a row that leads somewhere is one link, the whole row; one hover tint for every row link, ink at 11% (twice the stripe); the press tint `sunk`; no underline inside a row | `hover(background-color)=ink@11%; press(background-color)=sunk; text-decoration-line=none` | ruled | #129 binding rules; #52; #127 (2026-09-14) |
| Chevron heading link | `a.cnm` | a heading that leads somewhere carries a chevron at rest and is never underlined | `text-decoration-line=none` | ruled | #52; #129 binding rules |
| Chevron | `a.cnm .chev` | 15px, muted at rest | `color=muted` | ruled | #52 |
| Prose link | `p a, .lede a, .sub a, .bnote a` | the one place an underline stays: a link inside running text | `text-decoration-line=underline` | ruled | #52 |
| Tag | `.nexttag, .fxrow .topmatch` | Next (on the picker's title) and Top match (on the flagged row, before the kick-off): 10px bold capitals in an accent pill | `font-size=10px; font-weight=700; text-transform=uppercase; background-color=accent; color=pill-ink` | ruled | #129 Matchdays; #127 correction 2 |
| Matchday picker | `.mdnav .mdstep` | its own full-width line under the tab bar: ‹ MATCHDAY N › with the Next tag, the arrows pinned to the edges, the title centred, a 2px line under; one matchday on screen at a time; no script | `visible=1; border-bottom-width=2px` | ruled | #129 Matchdays |
| Picker title | `.mdstep .mdtitle .num` | 13px bold capitals ink | `font-size=13px; font-weight=700; text-transform=uppercase; color=ink` | ruled | #129 Matchdays |
| Picker arrow | `.mdstep .step` | a 34px target at each edge | `min-box=34px` | ruled | #129 Matchdays |
| Tab bar | `nav.tabs` | the tabs share the row and fit in one row at 375px in EN, DE and FI, no sideways scrolling | `fits` | ruled | #129 header |
| Tab | `nav.tabs .tab` | one line each, never wrapped; the side padding is what the label needs | `one-line` | ruled | #129 header |
| Breadcrumb current page | `.crumb .here` | the page you are on differs from the links at rest; the shipped site has the current page `ink-2` and the links muted, #52's mock had the two inverted | `color=ink-2` | proposed | put to the CPO on the #153 MR; measured, never fails, until ruled |

Not measured, still the rule: the header is identical on every tab (crest · name · meta line) and
there is no page title under the tab bar (#129); a board shows five rows on a competition page and
seven on Home, a zero is not a rank on a most-first board (#129 board rules); a board does not say
which way it ranks — its name and its top value do (CPO, #151 MR, replacing #129's "fewest first"
note); a name, a "Matchday N" and a date never break inside themselves
(#129 the fact row). Those are content rules, checked where the content is built.

## Pages

Every design-mock generator that renders a page, and every built page type. `Source` is the
command for a mock (`{out}` is where the check tells it to write; a generator with a fixed output
name lists it as `URL` and the check copies it) or `site_v2/dist` for a built page; `URL` is the
file the check opens (a glob for a built page: the first match in sorted order); `FI` governs the
MOCKS only — it says how the check reaches a mock's Finnish (`toggle`: the mock's FI switch;
`none`: EN only) — while a built page's other locales come from its URL, so `path` on a built row
means every locale the site publishes, German included;
`Expect` names elements the page must show — a page showing none of the inventory fails anyway.
The lint reads this table too: a mock generator listed here (and every module it imports) may
carry no CSS that touches an inventory class; a generator not listed is not a page.

Not listed, and why: `gen_block_standard.py` and `gen_interaction.py` are standards sheets that
show elements inside demo frames, not page compositions; `gen_competitions.py` (the competitions
index, #54) stops on the registry's `intercontinental_super_cup` type, which its proposed-taxonomy
map does not carry — it joins this table when it runs again. `gen_navmap.py`, `gen_sitemap.py`
and `gen_taxonomy.py` are diagrams.

| Page | Kind | Source | URL | FI | Expect |
|---|---|---|---|---|---|
| Home | built | `site_v2/dist` | `en/index.html` | path | Block heading, Competition group head, Legacy board value |
| Competitions index | built | `site_v2/dist` | `en/competitions/index.html` | path | Row link |
| Competition overview | built | `site_v2/dist` | `en/bundesliga/index.html` | path | Block heading, Table head, Table row, Ordered-by number, Tab bar |
| Competition matchdays | built | `site_v2/dist` | `en/bundesliga/fixtures/index.html` | path | Block heading, Schedule block, Matchday picker, Tag, Date heading, Match row kick-off, Tab bar |
| Competition rankings | built | `site_v2/dist` | `en/bundesliga/rankings/index.html` | path | Block heading, Metric group heading, Board name, Board sub-line, Ordered-by number, Tab bar |
| Match page | built | `site_v2/dist` | `en/*/matches/*/index.html` | path | Block heading |
| Team page | built | `site_v2/dist` | `en/teams/*/index.html` | path | Block heading, Tab bar |
| competition-overview | mock | `gen_overview_after_teams.py {out}` | `competition-overview.html` | toggle | Block heading, Table head, Table row, Ordered-by number, Fact row value, Tab bar |
| competition-matchdays | mock | `gen_competition_matchdays.py {out}` | `competition-matchdays.html` | toggle | Block heading, Matchday picker, Tag, Date heading, Match row kick-off, Tab bar |
| competition-rankings | mock | `gen_competition_teams.py {out}` | `competition-rankings.html` | toggle | Block heading, Metric group heading, Board name, Board sub-line, Tab bar |
| home | mock | `gen_home_with_rules.py {out}` | `home.html` | toggle | Block heading, Competition group head, Board name, Date heading |
| competition-hub league | mock | `gen_competition_hub.py league` | `competition_hub_mock_league.html` | toggle | Block heading, Table head, Table row, Tab bar |
| competition-hub groups | mock | `gen_competition_hub.py groups` | `competition_hub_mock_groups.html` | toggle | Table group heading, Table row |
| competition-hub cup | mock | `gen_competition_hub.py cup` | `competition_hub_mock_cup.html` | toggle | Block heading, Tab bar |
| competition-hub offseason | mock | `gen_competition_hub.py offseason` | `competition_hub_mock_offseason.html` | toggle | Block heading, Tab bar |
| matches next | mock | `gen_matches.py` | `matches_next_mock.html` | toggle | Competition group head, Date heading, Match row kick-off |
| matches past | mock | `gen_matches.py` | `matches_past_mock.html` | toggle | Competition group head, Match row score |
| top players | mock | `gen_top_players.py` | `top_players_mock.html` | toggle | Legacy board value |
| top teams | mock | `gen_top_teams.py` | `top_teams_mock.html` | toggle | Legacy board value |
| home legacy | mock | `gen_home.py` | `home_mock.html` | toggle | Block heading, Competition group head, Legacy board value |
