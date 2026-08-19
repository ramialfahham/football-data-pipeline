# Rendered-page evidence — chore/drop-browse-section

> Required by #827 for any `site_v2/src/**` diff. Read from the BUILT output (`site_v2/dist/`) and
> the running page, never from source. Replaces the previous file wholesale (it documented
> `feat/shared-competition-order`, a different branch and change).

Build: `npm run build` in `site_v2` -> **60 pages**, `audit-seo: 61 built page(s) checked. OK.`
Zero errors, zero dead-link failures (the class of defect the prior evidence file's build caught —
this build had none).

## 1. What changed on the page

The home page's LAST block is gone, not swapped. Before this branch, `[lang]/index.astro` rendered
`HeroFixtures` then `BrowseGrid` (chips for competition groups + countries). After, it renders
`HeroFixtures` alone.

## 2. Dev-server accessibility tree, before commit

Read via the Browser pane against the live dev server (`site_v2` on :4321), `/en/`:

```
region [ref_22]            <- Next matches (HeroFixtures)
 ...fixtures...
contentinfo [ref_46]        <- site footer, immediately after
 link "Matchday" ...
 generic "Competitions" / "Teams" / "Players" / "Stats" / "About" / "Imprint (pending)"
```

`region` (the fixtures hero) is followed directly by `contentinfo` (the footer) — no intervening
node of any kind. No orphaned wrapper `<div>`, no empty section, no leftover margin-only element.
Console: `read_console_messages` (`onlyErrors: true`) returned no logs. Server logs
(`preview_logs`, `level: error`): "No server errors found."

`get_page_text` on the same page returned, verbatim, the fixture rows followed immediately by
`MatchdayPilot / Competitions / Teams / Players / Stats / About / Imprint (pending) / EN · DE · FI
· Data: API-Football` — the footer's own content, confirming no text content sits between the hero
and the footer either.

## 3. Built output, grepped directly (not from source)

`site_v2/dist/en/index.html`, after `npm run build`:
- `grep -i "browse|linkchip"` — **zero matches**. The old block's marker classes are gone from the
  emitted HTML, not just deprioritized or hidden.
- File is well-formed: contains a `site-footer` node (the `contentinfo` region confirmed above) and
  the same 3 `<script>` tags every locale root carries (timezone progressive-enhancement + theme
  toggle + search), unrelated to this change and unaffected by it.
- Page count and SEO audit both green (see Build line above) — no internal link to a Browse-chip
  destination was ever emitted, so there is nothing for `audit-seo.mjs` to catch here (contrast
  with the prior evidence file, where a stale sample DID produce a dead link the audit caught).

## 4. Not covered here

Geometry/scrollHeight was not re-measured at a fixed viewport (unlike the prior evidence file) —
there is no new content whose height needs pinning; the block was deleted, not resized or
reordered, so the page is simply shorter by however tall Browse was. de/fi were spot-read via
`get_page_text`/accessibility tree on `/en/` only; the built HTML for `/de/` and `/fi/` was not
independently grepped, though the same `shape_landing_payload` output feeds all three locales and
the i18n keys removed (`homeBrowse`/`homeByCountry`/`group*`) were removed from all three locale
blocks in `strings.ts` (checked directly, not assumed). Top players and Top teams remain unbuilt,
unaffected by this change, out of scope.
