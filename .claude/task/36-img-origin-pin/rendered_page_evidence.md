# Rendered evidence — player photos off

## Instrument

None. The Browser pane's dev server returns HTTP 500 in this checkout: esbuild stops on the comment
at the top of `site_v2/src/layouts/Layout.astro` ("Expected ';' but found '01'"), a file this change
does not touch. No page was rendered and no geometry was read.

## What stands in its place

The built HTML of the committed sample (`astro build`, 2,355 pages) shows each player row as
`<span class="pphoto"><span>XX</span></span>`, with no `<img>`, on a team page (28 slots) and a match
page (10 slots). The same slot, with the same class and the same CSS, is what a player without a
photo receives before this change. The CSS box (`.pphoto`, 34 px) and the registry slot `photo` are
unchanged.
