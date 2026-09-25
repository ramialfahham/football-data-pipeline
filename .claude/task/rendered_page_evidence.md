# Rendered page evidence — `fix/fixture-title-unique` (#155)

The change is the match page's `<title>` (and the `og:title` / `twitter:title` Layout derives from
it). No markup, style or block on the page changes, so no element of the block standard moves.

- Built HTML, committed sample: `dist/{en,de,fi}/bundesliga/{matches,spiele,ottelut}/2026-10-09-
  borussia-dortmund-vs-sv-werder-bremen/index.html` carry "Borussia Dortmund vs SV Werder Bremen,
  9 Oct", "Borussia Dortmund - SV Werder Bremen, 9. Okt.", "Borussia Dortmund–SV Werder Bremen,
  9.10.".
- Full scale (4,808 upcoming fixtures x 3 languages): audit-seo checks every title's uniqueness per
  locale, its width against the 660px hard cap and og:title equal to the title: 14,905 pages, 0
  violations. The widest title measured is 535px.
