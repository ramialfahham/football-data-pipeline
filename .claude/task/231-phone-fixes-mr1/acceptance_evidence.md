# Verification — phone fixes, the causes a written rule settles

Read from the built site (`npm run build` in site_v2 on this branch, sample data) against the
`gitlab/main` build before the branch, with the phone audit's sweep scripts (`sweep.py`,
`measure.js`, `measure_names.js`): every page loaded once, resized 280 to 768px in 52 widths, in
EN, DE and FI, 0 sweep errors. Counts are element-widths.

criteria_demonstrated:
  - **Breadcrumb:** `nav.crumb > a.lnk` 73,320 before, 0 after; no page but Home emits a nav.crumb that is not the component's nav.trail (pinned by `tests/test_phone_fixes_231.py`). The links of the Players hub and nation pages are the component's 44px links.
  - **Initial and surname:** 1,567 splits before (Player row 1,170 + 373, Result row 24), 0 after, in EN, DE and FI (`measure_names.js`).
  - **Venue:** `div.kick > span.nb` 66 before, 0 after; the venue is no no-break unit, so it breaks between words at 280-320px.
  - **Competitions list name:** `span.comp-meta > span.comp-name` 354 before, 0 after; the name wraps between words, no ellipsis.
  - **Chart axis label:** `svg > text` 1,224 before, 0 after; the axis title sits inside the drawing.
  - **No new break class:** no class is new. Rising: the player-row stat dot (`span.pstat > span.nb`, middle dot ends a line) 16,267 to 16,602 and the kick-off dot (`div.kick`, middle dot opens a line) 0 to 648, both cause 3, which MR 1b removes. The trail moves between `nav.crumb.trail` and `nav.crumb.trail.cut` with the same total (6,578). One new sweep row, `span.lvl > a.lnk` (Home, unit-alone, 176 in EN on the Competitions, Teams, Players and Matches pages, 280-690px), is the intended result of keeping Home on a two-level trail: the link is the only content of its nav, not a broken line. No pin baseline is raised; `banned_properties` for system.css is lowered 7 to 6.
