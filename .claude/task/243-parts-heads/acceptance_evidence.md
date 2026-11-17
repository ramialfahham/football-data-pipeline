# Verification — parts library, tab band, chip, group head and chevron heading link

Read from this branch's dev server (port 4327) and, for "before", from a checkout of main at
a10ee51f on port 4328, both with the same local data, national teams included.

## Where each part is drawn now

| Part | Component | Placed by |
|---|---|---|
| Tab band (links or radios) | `ui/TabBand.astro` | `competition/CompetitionTabs`, `team/Tabs`, the Player page |
| Result chip | `ui/ResultChip.astro` | `ui/ResultRow`, `ui/CompetitionRow`, `fixture/FormSegment` |
| Chevron | `ui/Chevron.astro` (moved from `fixture/`) | `ui/HeadingLink`, `ui/Fold`, `fixture/Masthead`, `player/PlayerComparison`, `player/PlayerIndex`, `competitions/FilterRows` |
| Chevron heading link | `ui/HeadingLink.astro` | `ui/GroupHead` |
| Group | `ui/Group.astro` | Home, Matches, match page next matches, a team's fixture groups, the Matchdays schedule, Rankings, the Teams and Players pages, every metric comparison and last-season table |
| Group head | `ui/GroupHead.astro` | the same, plus the standings' group names and the match header's competition head |
| Date heading | `ui/DateHeading.astro` | Home, the Matchdays schedule, match page next matches, a team's fixture groups |

## Parts page, forms per part

`python scripts/parts_page.py`, before (main's script and registry, port 4328) and after (port
4327), 15 pages at 375px and 1000px. Moved parts are compared under their new key.

- All 141 parts keep their number of forms. No part gains a form and no new form appears.
- Every kind keeps its count (Row 87, Group heading 7, Result badge 15, Tab bar 12, Chevron link
  10).

## The registry check

`python scripts/check_component_registry.py`: 0 failures. Pins lowered in
`tests/fixtures/component_registry/baseline.json`:

- markup outside its component, heading-link: 11 to 0;
- components in several files: 13 to 11.

The tab band, chip, chevron, heading link, group, group head and date heading each count 0. The
group head's `links-to` names the competition page and the nation page, and its file builds
exactly those two; the link check now tells a nation page (`players/{nation}`) from a player page.

criteria_demonstrated:
  - **One component per part, 0 outside:** the table above; the registry check counts 0 markup outside the tabs, chip, chevron, heading-link, group, group-head and date-heading components; `grep` for `class="tabs`, `class="gh`, `class="dh`, `"fxgroup"`, `class="chev`, `class="cnm` and `"pill"` over `site_v2/src` finds them only in `ui/`.
  - **Group head links:** `ui/GroupHead.astro` builds the competition page from `competition` and the nation page from `nation`, and nothing else; `links-to: [competition page, nation page]` passes the link check. A metric group heading passes `statistics` (its metric group's key) and renders no link.
  - **Parts page:** 141 parts the same, none more or new (above).
  - **Rendered pages:** 114 of 114 screenshots byte-identical; every DOM difference is listed in `rendered_page_evidence.md`.
  - **Same links:** 0 `href` differences over 14,868 links in the 271 captured files.
  - **No block, order, wording or value change:** the visible text of every captured page is the same before and after.
