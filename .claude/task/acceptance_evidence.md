# Verification — the Team page's Performance tab passes every registry rule the design check measures

criteria_demonstrated:
  - **Deserved points names:** 14px, weight 600. Table name cell failures: 0, against 612 on main, with the Performance tab open.
  - **Strip group headings:** 26.0px above the first line of the first row at every width and language, with the switch off and on. Metric group heading failures: 0, against 612 on main.
  - **Last-season head labels:** no overflow and no overlap in EN, DE or FI.
  - **Deserved points chart:** the team's name crosses no axis label. No overlap at 280, 320 or 360px on any page, against 6 on main at 280px.
  - **Measured:** the design check on a build whose Team pages open on the Performance tab, at 280, 320, 360, 375, 700 and 1010px in EN, DE and FI (rendered page evidence). As shipped, the Team page matches its baseline exactly.
  - **Gates:** `npm run build` with its audits, `check_component_registry.py` and `check_page_css.py` pass; whole `pytest tests` (1,736) and `npm test` (175) pass.
