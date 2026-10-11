# Verification — awarded results carry their kind and the score on the pitch

The change is three columns on `fixture_result_corrections` and 44 new rows. No model changes.
No BigQuery query was run for it; `data:build:mr` loads the seed and runs its tests.

- **Rows:** a script wrote every row from the research files and checked each against the test's
  rules before writing: unique ids, kind with award, on-pitch score only on played and abandoned
  awards, https sources, two different sites for match_reports, no Wikipedia page as a source.
  Result: 79 rows (35 + 44), 0 problems.
  - 42 not played: 28 Super Lig 2022 (TFF match page and TFF decision), 3 CAF 2020-21, La
    Passe-Volcan Club, Standard-Westerlo, Tours-Lorient, 5 UEFA COVID-19 forfeits, Cuba-Cayman
    Islands, 2 Dnipro-1-Puskas Akademia.
  - 1 played and awarded afterwards: Verona-Roma 2020, 0-0 on the pitch, awarded 3-0.
  - 1 score fix: Etoile Matoury-Le Geldar, 1-1 where the provider has 2-2.
  - The 9 existing rows: 4 played, 4 abandoned (Bastia-Lyon 0-0 at half-time, with a third
    source), 1 not played (Gaziantep-Trabzonspor, with its TFF match page added).
- **Sources read for the six rows first sourced to Wikipedia:** each now has a second site that
  states the award; CAF's own statement makes La Passe-Volcan Club official, with no score set.
  Al Hilal-Asante Kotoko 2-0 rests on a report that the match was not played and Al Hilal went
  through, and a results page with 2-0.
- **Checks:**
  - `dbt parse` passes.
  - sqlfluff (repo root, jinja, bigquery, full rules) reports 0 findings on the test.
  - Every offline gate passes.
  - pytest: 1496 passed, 2 skipped.
- **Seen by the reviewer, for #176:** `base_apif__fixture_players` checks player goals against
  the applied score, which for a played-then-awarded match is the awarded score, not the one on
  the pitch. This is unchanged by this MR (the provider already carries Verona-Roma as 3-0); the
  on-pitch columns are what #176 can read to fix it.
