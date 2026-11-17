# Verification — parts library, explainer, filter bar, block heading, stat card and crest

Read from this branch's dev server (port 4327) and, for "before", from a checkout of main at
6b80c12e on port 4328, both with the same local data, national teams included.

## Where each part is drawn now

| Part | Component | Placed by |
|---|---|---|
| Block explainer, tab explainer | `ui/Explainer.astro` | 16 block components and the Team page's Performance tab |
| Filter bar (radios, buttons, dropdown, the filtered rows' container) | `ui/FilterBar.astro` | `competitions/FilterRows` (Competitions, Matches, Teams, Players, nation page, the Team page's Matches tab) and `player/PlayerComparison` |
| Block heading | `ui/SectionHead.astro` (unchanged) | every block |
| Stat card | `ui/StatCards.astro` (unchanged) | the Player page |
| Crest | `ui/Crest.astro` (unchanged) | every crest |

## Parts page, forms per part

`python scripts/parts_page.py`, before (main's script and registry, port 4328) and after (port
4327), 15 pages at 375px and 1000px. Moved parts are compared under their new key.

- All 141 parts keep their number of forms. No part gains a form and no new form appears.

## The registry check

`python scripts/check_component_registry.py`: 0 failures. Pins lowered in
`tests/fixtures/component_registry/baseline.json`:

- markup outside its component, block: 23 to 1;
- markup outside its component, filter-bar: 12 to 0.

The explainer, filter bar, stat card and crest count 0 outside their components. The block counts
1, pinned: the match header's status word ("Match preview", or how a played match ended) is a `div.eyebrow` in
`fixture/Masthead.astro`, which reuses the block heading's class for its text style. It is the
match header's own part, not a block heading; it moves with the match header.

criteria_demonstrated:
  - **One component per part, 0 outside:** the table above; the registry check counts 0 markup outside the explainer, filter-bar, card and crest components and 1 outside block, named above; `grep` for `class="bsub`, `class="seg`, `class="fbar`, `class="categories` and `"seg-in"` over `site_v2/src` finds them only in `ui/Explainer.astro` and `ui/FilterBar.astro`.
  - **Nation page apart from player page:** `tests/test_check_component_registry.py::test_a_nation_page_link_is_not_a_player_page_link` fails a nation link named as a player page and a player link named as a nation page.
  - **Parts page:** 141 parts the same, none more or new (above).
  - **Rendered pages:** 111 of 114 screenshots byte-identical; the three others vary between two captures of main itself and their DOM is identical; every DOM difference is listed in `rendered_page_evidence.md`.
  - **Same links and filters:** 0 `href` differences over 14,868 links in the 271 captured files; the visible text of every captured page, every filter's choices included, is the same.
  - **No block, order, wording or value change:** the visible text of every captured page is the same before and after.
