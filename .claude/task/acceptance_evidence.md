# Acceptance evidence — one order for every metric, from the catalogue

Read from the catalogue, from the export's functions, and from two `astro build`s of the committed sample payloads:
main's, and this branch's. On this branch the committed BL1 sample's two board lists are re-sorted by the export's
`_in_catalogue_order`, as the next export writes them; every value and every other key is unchanged. A script reads
every built page in both builds.

criteria_demonstrated:
  - EVERY SHOWN METRIC HAS A PLACE. Each shown metric carries a catalogue metric_order:
    - all 12 Rankings team boards and all 13 Rankings player boards;
    - the 4 + 4 Home boards;
    - the 36 Form comparison rows.
    No two metrics of one entity and group share an order. tests/test_catalogue_order.py holds this, and the export
    fails on a shown board without a place.
  - THE RANKINGS ORDER. On the built Bundesliga Rankings page the Passing player boards read Passes · Pass
    accuracy · Key passes (DE Pässe · Passquote · Schlüsselpässe, FI Syötöt · Syöttötarkkuus · Avainsyötöt). Every
    other board keeps its place. A fetch-level test feeds the warehouse's rows in the old order through
    fetch_competition_payloads and fetch_leaderboard_payloads and requires the catalogue's. With the ordering
    switched off, both payloads fail it.
  - HOME AND THE FORM COMPARISON UNCHANGED.
    - Home: the export's order is goals, assists, passes, key passes (player) and goals, shots on target, passes,
      duels (team), as before.
    - Form comparison: metric_rows.json keeps its 36 rows in the same order; only the numbers after the new places
      move (7 lines).
  - NO OTHER PAGE CHANGES. Of 2,539 pages, the three Bundesliga Rankings pages (EN, DE, FI) differ from main's
    build. Every other page shows the same text, and both builds hold the same pages.
  - GATES.
    - dbt parse clean; description hygiene ok.
    - npm test 117 pass.
    - check_copy_gate and check_page_css pass; check_design_inventory reports 0 failures in 165 renders.
    - pytest tests/: 1496 passed, 2 skipped.
  - COST. No query changes.
