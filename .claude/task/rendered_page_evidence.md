# Rendered page evidence — the played match page's year

No markup, CSS or layout change: the played match page's `<title>`, its visually hidden h1 and its
meta description gain the match's year. Read from the built HTML of the full-scale build, not the
Browser pane, because only the head and the hidden h1 change.

- EN `site_v2/dist/en/bundesliga/matches/2026-09-05-tsg-1899-hoffenheim-vs-borussia-dortmund/`:
  `<title>TSG 1899 Hoffenheim vs Borussia Dortmund, 5 Sept 2026</title>`,
  `<h1 class="vh">TSG 1899 Hoffenheim vs Borussia Dortmund, 5 Sept 2026`, description
  "Full time: TSG 1899 Hoffenheim 2–3 Borussia Dortmund · Matchday 2 · 5 Sept 2026."
- DE: `TSG 1899 Hoffenheim - Borussia Dortmund, 5. Sept. 2026`; FI:
  `TSG 1899 Hoffenheim–Borussia Dortmund, 5.9.2026`.
- The h1 has the `vh` class, so it is read by assistive technology and not drawn; the visible
  header is unchanged.
