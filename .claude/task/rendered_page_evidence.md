# Rendered page evidence — the round in the competition header

What was checked, how, and at which widths:

- A local build of a copy of the branch on the committed sample, the copy's BL1 payload given the
  round name fields the warehouse serves for the Bundesliga (compFactMatchday with the matchday).
  The built HTML read on the Bundesliga Overview and Matchdays pages in EN, DE and FI: the header's
  meta line "Germany · Season 2026/27 · Matchday 6" / "Saison 2026/27 · 6. Spieltag" /
  "Kausi 2026/27 · 6. kierros", and the picker titles "Matchday 6" / "6. Spieltag" / "6. kierros",
  the number held to its word by a no-break space as compFactMatchday already does.
- `scripts/check_design_inventory.py --dist <local build>`: every built page and mock in the block
  standard's Pages table at 375, 700 and 1010px in EN, DE and FI: 174 renders, 0 failures and 0
  warnings.
- The longest names on the picker, written into copies of the built Matchdays page ("Second round ·
  Group A · Matchday 3", "2. Runde, Gruppe A, 3. Spieltag", "2. karsintakierros, A-lohko,
  3. kierros"), measured at 320, 375 and 1010px: no horizontal scroll in any language; a name too
  long for one line wraps to two at a normal space, each number held to its word, and the Next tag
  moves under it.
- Obtained: the built HTML and the inventory's DOM and style measurements. No screenshot (the
  pane's screenshot fails on this site).
