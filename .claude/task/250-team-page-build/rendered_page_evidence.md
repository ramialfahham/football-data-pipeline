# Rendered pages — before and after, every difference with its reason

"Before" is main at de65e45a, served from a separate worktree; "after" is this branch. Both read
the same data: the 34 sample teams re-exported with this branch's export, plus three national
teams (Germany, Spain, Japan) copied into both trees for the capture and removed afterwards. A
Playwright capture loaded each page at 375px and 1280px with images hidden, checked each page tab
in turn, and saved a full-page screenshot, every `href`, the visible text, the block headings and
the sideways scroll. Main moved to 65663f3b during the build (!480, Masthead.astro only); this
branch was moved onto it with no conflict.

## Player pages — 666 screenshots (72 players, EN/DE/FI, every tab)

Pixel-identical, the same 15,486 links and the same text. The strip plot and the last-season table
are now the shared parts `ui/StripPlot.astro` and `ui/LastSeasonTable.astro`; their markup is
unchanged.

## Played match pages — 66 screenshots

Pixel-identical, the same links and text.

## National team pages — 54 screenshots (3 teams, EN/DE/FI, every tab)

- Overview and Matches: pixel-identical.
- Performance: the blocks, their order, every link and every explainer are the same. The one
  changed block is Compared with the league: its strip plot takes the part's standard form, the
  median ticked with its value and the Median key in the legend, and no "better →" or "← better"
  mark. The strips now sit in the one-choice panel the club page uses (a hidden radio and a
  panel wrapper), with no choice bar shown.

## Club Team pages — 612 screenshots (34 clubs, EN/DE/FI, every tab)

Every screenshot differs: the approved design. Checked on every page at 375px:

- This season stands above the tab band on 102 of 102 club pages, with six cards and the approved
  explainer listing the competitions; none of the 9 national team pages has it.
- Overview: Competitions one line each (no `.tc-extra` anywhere), Next matches before Recent
  matches, Recent matches and Results in the Player page's row (`.rlist.pm`).
- Performance: no tab explainer, no Standing; Deserved points opens with "{competition}
  {season} only." on 102 of 102 pages.
- Compared with other teams: 16 clubs offer a choice of two competitions (the league and a UEFA
  competition benchmarked over its league phase); on Bayern the explainers read 18 Bundesliga teams
  and 36 UEFA Champions League teams. Every strip row has its median; no card row on any page.
- Compared with last season: shown on 99 of 102 pages (one club played no match last season); no
  card row; one empty trend on Bayern where a season has no value.
- One match: on Cosenza (copied in for the check, then removed) the explainer reads "1 match",
  "1 Spiel", "1 ottelu".
- `href` lists differ on 522 club screenshots because Next matches now stands before Recent
  matches, so the same links come in a new order.

## Sideways scroll

Every Team page (club and national), EN/DE/FI, every tab, at 280, 320, 360, 375, 700 and 768px:
0 pages scroll sideways and no element runs past the right edge.
