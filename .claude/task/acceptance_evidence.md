# Verification — matches after extra time carry their score after extra time

The fix is 26 rows in `fixture_result_corrections`. Each row gives the score after extra time and
two match reports on different sites (`source_kind` match_reports). A detector test catches a new
case. Read-only queries ran against prod's `core` tables, each dry-run first.

- **Sources:** each of the 26 scores was researched on the web, with two https sources on
  different sites per match, and all 26 confirm the corrected score.
  - Six rest their second source on a URL or title that states the score: Hearts' and Swansea's
    club reports, Newport County's club page, Kent Sports News, and the Sky Sports and Vavel pages
    for Newcastle v Bournemouth. The other source of each was read in full.
  - Sky Sports shows the two-leg aggregate in its header for ML Vitebsk v Borac and Ilves v
    Stjarnan; the match score was used.
- **The detector today (0.05 GB):** the compiled test on prod's `fct_fixture` returns exactly the
  26 matches. It flags none of the 15 shoot-outs the provider files as penalty goals after minute
  120, among them Villarreal v Manchester United in the 2021 Europa League final.
- **With the seed applied (0.05 GB):** the same test, with `fct_fixture`'s score replaced by the
  seed's official score as `base_apif__fixtures_next` applies it, returns 0 rows.
- **The score change:** 26 matches (8 this season), no result changes. The 41 the earlier rule
  changed included the 15 shoot-outs; that rule and every model and document change of it return
  to main's version.
- **Checks:** `dbt parse` passes, and so does every offline gate. sqlfluff (repo root, jinja,
  bigquery, full rules) reports 0 findings on the test. The seed's own test,
  `assert_result_corrections_applied`, and the new test run in `data:build:mr`.
