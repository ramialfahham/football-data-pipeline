# Rendered page evidence — the site build's memory at full scale

No markup, CSS or copy changes: the pages read the same data at a different moment, and the
formatting reuses one formatter per locale and option set. The rendered proof is byte identity of
the built output, read from `dist/`:

- Committed sample: main's build and the branch's build, same day, 2,543 files each (2,539 HTML
  pages, the CSS, the sitemap, robots.txt): 0 files differ, 0 files on one side only.
- Full scale (62,800 match payloads, 3,348 team payloads): main's build and the branch's build,
  same day, 198,999 files each: 0 files differ, 0 files on one side only.

Identical bytes give identical rendering at every width. The design check
(`scripts/check_design_inventory.py --dist site_v2/dist`, Playwright, as CI's validate:ui runs it)
on the branch's sample build: 23 pages x 3 viewports (375, 700, 1010px) x 3 languages, 165 renders,
0 failures, 27 warnings (the header row at 700px, the same warnings main carries).
