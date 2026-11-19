# Verification — a club name in a row never runs past its space

criteria_demonstrated:
  - **A club name never runs past its space (260, 280, 320px, EN, DE, FI):** the injected "Weston-super-Mare" row overflowed by 28px at 260px and 8px at 280px before the change and by 0px after, in all three languages (rendered_page_evidence.md).
  - **A hyphen-joined word that fits stays whole; a wider one breaks at its hyphens:** at 320px the 142px name sits whole on one line; at 280px and 260px, where its line is 134px and 114px, it breaks after "Weston-".
  - **A row whose names fit keeps its form and its look:** the sweep of the whole sample at 280 and 320px shows identical counts before and after; at 260px the only difference is one page per language with a hyphen-joined name wider than its line.
  - **The block standard states the rule, and the design check measures it:** the Result row has a part `club-name` (class `cn`, its `.club` box measured `fits`: in the defect state the `.club` box scrolls, 174px of content in 146px at 260px and 174px in 166px at 280px, where the `.cn` box inside it does not) with the rule; the generated element table of `docs/wireframes/block_standard.md` carries it; the Name in whole words rule no longer lists `.club .cn`.
  - **No pin rises:** `python scripts/check_component_registry.py` passes with 0 failures; the fix declares `display` and `white-space` only, both on the non-visual list, so no unchecked-property count changes. A first form with `max-width` and `vertical-align` raised two pins and was dropped.
  - **Test:** `tests/test_phone_fixes_231.py::test_a_hyphen_joined_club_name_wraps_inside_itself_only_where_its_line_is_too_narrow` pins the one rule and its two declarations.
