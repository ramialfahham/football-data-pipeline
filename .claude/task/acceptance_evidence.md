# Verification — no word breaks at its hyphen, and the design check opens every tab

criteria_demonstrated:
  - **No break at a hyphen:** with every tab open, at 280–1010px in EN, DE and FI, split counts fall to 0 on the Team page (56), Home (13) and the Teams page (3), and to 2 on the Match page (223); the 2 and the Competition overview's 21 have no hyphen.
  - **Real hyphen kept:** the build wraps the word in the no-break span and changes no character; no span lands in an attribute, title, option, SVG text or script on any built page; `wholeWords.test.mjs` pins it.
  - **Top-match row:** its measure counts each name's longest word; the Team page's 3 Name in whole words failures fall to 0.
  - **Every tab:** the check opens every tab of a Tab bar and counts a shared defect once; `test_the_gap_counts_open_every_tab_and_count_a_shared_defect_once` and `test_a_page_is_judged_across_its_tabs_and_a_failure_in_every_tab_counts_once` pin it, and `test_a_tab_bar_with_no_tab_to_open_fails_instead_of_measuring_one_tab` pins that a Tab bar without tab inputs fails.
  - **Tokenizer:** a raw-text element's end is found in the page itself, so a letter that lengthens when lowercased (`İ`) cannot shift it; a word already in a no-break span is not wrapped again; both pinned in `wholeWords.test.mjs`.
  - **Registry:** the Unbreakable unit names the build step, every page and a hyphen-joined word; `check_component_registry.py` passes.
  - **No pin rises:** every page's count is at or below main's; the pins that fall are lowered from CI's measurement.
  - **Gates:** `npm run build` with its audits, `check_component_registry.py` and `check_page_css.py` pass; `pytest tests` and `npm test` pass.
