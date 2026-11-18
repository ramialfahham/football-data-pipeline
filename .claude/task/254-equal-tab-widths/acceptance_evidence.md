# Verification — equal tab widths on every tab bar

Read from this branch's dev server and from main at c1084493 with the same committed sample; the
method and every difference are in `rendered_page_evidence.md`.

The change: `.comp-tabs .tab` in `site_v2/src/styles/system.css` takes `flex: 1 1 0` (was
`1 1 auto`); its default `min-width: auto` stays, so a longer label widens its own tab. Every tab
bar on the site is `ui/TabBand.astro` with `nav.tabs.comp-tabs`.

criteria_demonstrated:
  - **Equal widths on every tab bar, Competition, Team and Player pages:** 981 of 981 tab bars on the Bundesliga pages, 34 Team pages and 72 Player pages, EN/DE/FI, at 320, 375 and 1010px have tabs equal to within 1px; at 280px 217 of 327.
  - **A label that needs more takes it, not cut off:** the 110 bars at 280px that are not equal each hold one label wider than its share (EN "Performance", DE "Nationalmannschaft", FI "Yleiskatsaus"); 0 labels cut and 0 pages scrolling sideways at any width.
  - **The registry's Tab bar rule:** `docs/design/components.yml` tabs.bar rule reads "the tabs share the row equally and fit in one row at 375px in EN, DE and FI, no sideways scrolling; a label that needs more than its share takes it", and `docs/wireframes/block_standard.md` carries it.
  - **The Player page under the Tab bar's used-on:** `docs/design/components.yml` tabs.used-on is [Competition pages, Team page, Player page].
