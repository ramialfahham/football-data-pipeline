# Verification — the competition page's season label, served by the warehouse

Checked locally on the branch: dbt parse; SQLFluff on dim_competition_season (the same three
dbt_utils template lines main reports, and clean once the macro is taken out); the six offline
gates and `check_page_css.py`; `check-page-specs` (10 pages OK); the full pytest suite (1,602
passed, 2 skipped); the site's node tests (132 passed). A copy of the branch built with
`npm run build` on the committed sample, its BL1 payload given `season_label` "2026/27" in the copy
only: exit 0, audit-seo checks 2,269 pages OK, check-built-pages OK.

criteria_demonstrated:
  - dim_competition_season builds season_label from the registry seed's season_type: split_year as concat(year, '/', the next year's last two digits), calendar_year as the year; core.yml tests it not_null and, at model level, that it starts with its season_api_year and has the shape YYYY or YYYY/YY.
  - fetch_competition_payloads reads season_label from core.dim_competition_season keyed by (league_code, season_api_year) and shape_competition_payload emits it as served; pytest pins a split-year (2026/27) and a calendar-year (2026) label, None when not served, and that a payload takes its own season's label.
  - The local build's competition header reads "Germany · Season 2026/27 · Regular Season - 6" on the Bundesliga Overview, Matchdays and Rankings pages, "Saison 2026/27" in DE and "Kausi 2026/27" in FI; the header formats no year.
