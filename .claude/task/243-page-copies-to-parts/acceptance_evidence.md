# Verification — the last page-local copies of library parts

Read from the dev server of this branch and of main at 56b550bc, with the same committed local
data; the capture method and every difference are in `rendered_page_evidence.md`.

## Where each part is drawn now

| Part | Was | Now |
|---|---|---|
| Deserved points table row | own `div.ctab-row` markup in `team/TeamDeserved.astro` | `ui/TableRow.astro`, the second line in the table row's `.ent .sub` |
| Match header status word | `div.eyebrow` in `fixture/Masthead.astro` (the block heading's class) | `div.status-word`, a match header part; `.eyebrow, .mast .status-word` share one declaration |
| Line-up formation | `span.ps` in `fixture/MatchLineups.astro` (the player row's class) | `span.formation`, a two-column head part |

The table row's second line is one rule for every table: `.ctab .tm .ent .sub`, 13px muted at line
height 1.2 (it was written for the ranking tables alone); the Deserved table's own `.dpm-sub` rule
and registry part are gone. In the registry the sub-line part moves from the board to the table
row ("Table sub-line", selector `.ctab .tm .sub`), so the design check measures it on every table;
the board keeps a part without text (`.board .ent .sub`) for its narrow rules, and the design
inventory's Pages table names "Table sub-line" where it named "Board sub-line".

## The registry check

`python scripts/check_component_registry.py`: 0 failures, 155 table rows. Pins lowered in
`tests/fixtures/component_registry/baseline.json`:

- markup outside its component: block 1 to 0, player-row 1 to 0, table-row 1 to 0;
- part gaps, mock-css: 34 to 33 (the `dpm-sub` part is gone).

criteria_demonstrated:
  - **0 markup outside block, player-row, table-row:** the registry check's count line reads `markup outside its component: board 5, breadcrumb 2, competition-index 4, header 2, last-season 2, page-shell 17, team-index 5`, with no block, player-row or table-row entry, and the baseline carries none of the three.
  - **Match pages pixel-identical, same links and text:** 1,144 screenshots of 572 match pages; 0 href and 0 text differences; the 48 screenshots that differ with images shown differ only on provider crests, and 74 of 74 of their pages are pixel-identical with images hidden (`rendered_page_evidence.md`).
  - **Team pages identical except the Deserved table's second line:** 612 screenshots of 102 Team pages; Overview and Matches 408 of 408 identical; the 204 Performance screenshots differ from the table's second line down, at line height 1.2 (15.6px, from 16.25px), and by at most 1 of 255 in the header band on EN at 375px; 0 href and 0 text differences.
  - **No block, wording, value or link change:** the visible text and the href list of all 674 captured pages are the same before and after.
