# Verification — parts library, the rows

Read from this branch's dev server (port 4327) and, for "before", from a checkout of main at
e6f7f6fb on port 4328, both with the same local data, national teams included.

## Where each row is drawn now

| Row | Component | Placed by |
|---|---|---|
| List row (the link wrapper) | `ui/ListRow.astro` | the result, player and competition rows |
| Result, meeting, goal and scorer row | `ui/ResultRow.astro` | `fixture/RecentMatch`, `fixture/HeadToHead`, `fixture/MatchGoals`, `player/PlayerRecent` |
| Player row | `ui/PlayerRow.astro` | `fixture/PlayerToWatch`, `fixture/MatchLineups`, `player/PlayerIndexRow`, `team/TeamSquad` |
| Competition row | `ui/CompetitionRow.astro` | `team/TeamCompetitions` |
| Fact rows | `ui/FactRows.astro` | `competition/SeasonFacts`, `team/TeamHighsLows`, `team/TeamStanding` |
| Table row | `ui/TableRow.astro` | `competition/StandingsTable`, `competition/DeservedTable`, `competition/RankingBoard`, `team/TeamLastSeason`, `player/PlayerLastSeason` |
| Index row | `ui/IndexRow.astro` | `competitions/CompetitionIndexGrid`, `teams/TeamIndex` |
| Row list | `ui/RowList.astro` | the five result lists and the competition list |
| Match row | `ui/MatchRow.astro` (unchanged) | every list of matches |

## Parts page, forms per part

`python scripts/parts_page.py`, before (main's script and registry, port 4328) and after (port
4327), 15 pages at 375px and 1000px. Moved parts are compared under their new key.

- 138 parts keep their number of forms; 3 have fewer: list row 28 to 26, player row 3 to 2, player
  row position 3 to 2. No part gains a form and no new form appears.
- By kind: Row 90 to 87, Position / value 25 to 24; every other kind is unchanged.

## The registry check

`python scripts/check_component_registry.py`: 0 failures. Its new counts, pinned in
`tests/fixtures/component_registry/baseline.json`:

- Markup outside its component, per component: 0 for the list, result, competition, fact, index,
  row-list and match row. Two row counts stay at 1, each pinned:
  - **player-row 1:** a line-up's column head writes `ps` for the team's formation under its name
    (`fixture/MatchLineups.astro`), styled by `.colhead .ps`. It is the column head's second line,
    not a player row; it moves with the column head.
  - **table-row 1:** the deserved-points table beside the chart (`team/TeamDeserved.astro`) puts
    the team's sub-line inside the name (`.nm .dpm-sub`, line height 1.25) where every other table
    row stacks it under the name (`.ent .sub`, 1.2). Moving it onto the table row changes how it
    draws, so it waits for that form to be chosen.
- Components still spread over several files: 13.
- `links-to` on the match, result, player, competition, table and index rows: each file builds
  links to exactly the page types it names.

criteria_demonstrated:
  - **One component per row:** the table above; `grep` for `class="resrow`, `class="plrow"`, `class="frow"`, `class="ctab-row"`, `class="comp-row"`, `class="lrow` and `class="tc"` over `site_v2/src` finds them only in `ui/` (and `ctab-row` once in `team/TeamDeserved.astro`, named above); the registry check's markup count is 0 for every row component but the two named above.
  - **The check counts and fails:** `markup_counts` counts a component's own classes in any other `.astro` file and the count is pinned both ways (`tests/test_check_component_registry.py::test_markup_of_a_part_outside_its_component_is_counted`, `::test_the_real_tree_is_on_its_pins`); a rise fails `compare`.
  - **The link check:** `link_failures` fails a file that links to a page type its `links-to` does not name, or never links to one it names (`::test_a_link_to_a_page_type_the_registry_does_not_name_fails`); the real registry passes it.
  - **Parts page:** 138 parts the same, 3 fewer, none more or new (above).
  - **Rendered pages:** 102 of 108 screenshots byte-identical; the six that differ and every DOM difference are listed with their reason in `rendered_page_evidence.md`.
  - **Same links:** 0 `href` differences over 14,661 links in the 256 captured files.
  - **No block, order, wording or value change:** the rendered text of every captured page is the same before and after; the only text-node change is whitespace (listed in `rendered_page_evidence.md`).
