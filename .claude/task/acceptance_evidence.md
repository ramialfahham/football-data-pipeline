# Verification — Compared with last season follows the registry's table and group heading rules

criteria_demonstrated:
  - **A head row in each group's table:** every metric group's `.ctab.yoyt` now holds its own `.ctab-head`, and every visible row's grid tracks equal that head's, measured as the design check measures `tracks=head`.
  - **Stripes from the second row:** with the head inside the table, the existing rules stripe row 2, 4, … and leave row 1 plain, with the switch off (key rows only) and on (every row).
  - **Names 14px semi-bold ink:** the table's own weight rule is gone; every name measures 14px, 600, white-space normal.
  - **26px under each group heading:** the table sits 26px below its heading, the spacing the Rankings tab's boards use; the first head label measures 26px (rendered page evidence). A head whose labels wrap aligns them at the top, so a Finnish label on two lines beside one on one line keeps the gap.
  - **Every width and language:** the Team pages of Bayern München (EN, DE, FI), Borussia Dortmund (EN) and Inter (FI), Performance tab open, switch off and on, at 280, 320, 360, 375, 700 and 1010px: all four rules pass, no sideways scroll.
  - **Gates:** whole `pytest tests`, `npm test`, `npm run build` with its audits, `check_component_registry.py` (the dead `yoyt-head` part leaves the registry, a `mock-css` gap falls 35 → 34) and `check_page_css.py` pass. The design check on the Team page at every width and language matches the baseline except the unlisted-class count, which falls 30 → 29 with `yoyt-head`; both baselines take 29.
