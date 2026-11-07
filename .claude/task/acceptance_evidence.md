# Verification — a table that opens with the name keeps it in the first column in its narrow form

criteria_demonstrated:
  - **Name in the first column:** in the narrow form (fit-two, or no mark below a 600px container), a row whose first cell is the name spans it from column 1. On the Team page at 280px, DE and FI, the names of Compared with last season moved from 79px to 0px from the row's left (rendered page evidence).
  - **Rank tables unchanged:** a row that opens with the rank keeps its name in column 2; the Bundesliga page's 36 rows at 280px in DE measure column 2.
  - **Every width and language:** Team page, Performance tab, 280, 320, 360, 375, 700 and 1010px in EN, DE and FI: every name starts at the row's left edge.
  - **Gates:** whole `pytest tests`, `npm test`, `npm run build` with its audits (175 node tests; 1,734 Python tests, the 2 chart-screenshot tests that ran during the build pass alone, 25 of 25), `check_component_registry.py` and `check_page_css.py` pass.
