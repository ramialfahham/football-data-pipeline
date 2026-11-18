# Rendered pages — before and after, every difference with its reason

"Before" is main at 56b550bc, "after" this branch, both served by the dev server from the same
committed local data. A Playwright capture loaded each page at 375px and 1280px, removed the dev
toolbar, checked each Team page tab's radio in turn, and saved a full-page screenshot, the rendered
DOM, every `href` and the visible text. The DOM comparison drops the dev server's source-location
attributes.

Pages:

- Every match page of the local data: 548 fixtures; EN for each, DE and FI as well for the 11
  played matches and one upcoming match. 572 pages, 1,144 screenshots.
- Every Team page of the local data: 34 teams in EN, DE and FI, three tabs each. 102 pages, 612
  screenshots.

## Links and text

- Match pages: 0 `href` differences over 24,056 links; the visible text of every page is the same.
- Team pages: 0 `href` differences over 25,488 links; the visible text of every page is the same.

## DOM

Every difference is one of these, and there is no other:

- Match header: `<div class="eyebrow">` is now `<div class="status-word">` (1,144 screenshots,
  every match page).
- Line-ups: the formation's `<span class="ps">` is now `<span class="formation">` (every played
  match with a line-up).
- Deserved points table (on all three Team page tabs, since the hidden panels are in the DOM):
  `<span class="nm">{name}<span class="dpm-sub">{sub}</span></span>` is now the table row's
  `<span class="ent"><span class="nm">{name}</span><span class="sub">{sub}</span></span>`; a row
  without a second line keeps `<span class="nm">` alone, as before.

## Pixels, match pages

- With every image shown, 48 of 1,144 screenshots differ. Every differing block sits on a team or
  competition crest served by the provider's image host, and two captures of the same branch differ
  in the same blocks, so the crests render unevenly between captures.
- To settle it, the 74 pages behind those 48 screenshots were captured again with every image
  loaded eagerly, decoded, and then hidden (`visibility: hidden`, layout kept), before and after:
  74 of 74 screenshots are pixel-identical.

## Pixels, Team pages

- Overview and Matches tabs: 408 of 408 screenshots are pixel-identical.
- Performance tab: 204 of 204 differ, the intended change. The Deserved points table's second line
  ("per match" under "Shots on target difference") is 13px muted at line height 1.2 (15.6px), the
  table row's form, where it was 1.25 (16.25px). The row is under 1px shorter, so everything below
  it sits up to 1px higher and the page is 1px shorter in EN and FI (4,913 to 4,912px at 375px);
  DE rounds to the same height.
- Checked with images hidden on Bayern München (EN, DE, FI) and SC Paderborn 07 (EN), both widths:
  the first differing row is the table's second line (y 676 at 375px, 601 at 1280px), and every
  row below differs only by the shift.
- The design check's chart screenshot pins (`tests/fixtures/chart_screenshots/`, taken in CI's
  Linux image) change for the 12 scatter and strip plot shots, the two charts below the Deserved
  table; the 6 comparison shots (match page) are unchanged. Each chart sits up to 1px higher at a
  fractional offset, so its text rasterises a pixel apart (one shot is 1px shorter or taller); old
  and new pins side by side show the same chart. The pins are the design check's own screenshots
  of this branch.
- One more difference on EN at 375px: rows 40 to 57 of the sticky site header differ by at most 1
  of 255 in a colour channel. The header is translucent over the page, and a page 1px shorter
  changes how that is composited; nothing in the header changed.
