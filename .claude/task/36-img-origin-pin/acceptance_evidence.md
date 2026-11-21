# Verification — player photos off and the image-origin pin

Read from `npm run build`'s inputs: `astro build` of the committed sample on this branch (2,355
pages), then `node scripts/check-built-pages.mjs` and `node --test` in `site_v2` (230 tests, 0
failures).

criteria_demonstrated:
  - **No built page names a provider player or coach photo:** `check-built-pages.mjs` with the player-photo pin at 0 exits 0 on the build and prints `56079 provider crest/logo image(s), 0 player photo(s), 0 other foreign image(s)`. A search of `dist/` for `api-sports.io/football/players` and `/football/coachs` in any `.html` returns 0 files. Before this change the same check counted 17,484 player photos in `img` addresses.
  - **A player row shows the initials and holds no image:** `dist/en/teams/1-fc-koln/index.html` carries 28 `class="pphoto"` slots and 0 `<span class="pphoto"><img`; `dist/en/2-bundesliga/matches/2026-10-18-arminia-bielefeld-vs-vfl-osnabruck/index.html` carries 10 and 0. A slot reads `<span class="pphoto"><span>JG</span>`. The Players page, the nation pages and Players to watch render through the same `PlayerRow.astro`, whose only photo markup is removed.
  - **The Player page header shows the initials in its crest circle and holds no image:** `dist/en/players/a-pavlovic-328033/index.html` names no `api-sports.io/football/players` address and its header `Crest` receives no address, so it renders the `<span>` initials.
  - **The Player page carries no image meta from the photo:** the same page has no `og:image` and no `twitter:image` meta, and its JSON-LD Person has no `image`. Its only provider addresses are 21 team crests and 4 league logos, in `img` tags.
  - **A provider player-photo address fails the check on every build:** `scripts/check-built-pages.test.mjs`, "a pin at 0 fails any image of its kind on every build" and "main holds a pin above 0 on a sample build and only reports it on a full export; a pin at 0 holds on both" pass.
  - **A crest/logo count that differs from its pin fails a sample build and is only reported on a full export, with the manifest branch of `main` covered:** the second test above writes `data/manifest.json` and asserts exit 1 for a sample build above and below the pin, exit 0 for a full export at 5 against a pin of 2, and exit 1 for a photo on a full export.

Not measured in a browser: the dev server returns HTTP 500 on `Layout.astro` in this checkout (an esbuild
error in a comment at the file's top, a file this change does not touch), so no geometry was read.
The initials slot is the markup a player without a photo already receives.
