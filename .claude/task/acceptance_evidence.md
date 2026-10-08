# Acceptance evidence — #177 part 3: the Form comparison takes its rows from the catalogue

Read from `astro build` of the committed sample (2,538 pages; audit-seo and check-built-pages OK), compared with a
build of main from the same sample, and from one build in which a sample match's last-5 rows carry two real prod
rows of `mart_team_momentum` (one read, 3.2 MB processed, 10 MB billed; the sample file restored after the build).

criteria_demonstrated:
  - THE CATALOGUE'S ROWS, IN THE CATALOGUE'S ORDER. The export writes `metric_rows.json` from the catalogue: the 36
    team metrics with a `metric_order`. A test holds that set equal to the metrics `metric_map.csv` places in
    `mart_team_momentum`, minus Results, and each group's order to 1..N. Across the 628 sample match pages, 1,174
    comparison blocks show 0 rows out of that order. With the prod rows, the Dortmund v Bremen page shows 35 rows in
    every locale: Goals (3), Shooting (9), Passing (5), One-on-one (6), Defending (4), Goalkeeping (2), Set pieces
    (3), Discipline (3). Offsides is blank on both sides in prod for that window, so the row is hidden. The other 35
    names are the approved list's (e.g. "Possession" / "Ballbesitz" / "Pallonhallinta", "Abgefangene Pässe",
    "Geblockte Bälle"). No site file lists the rows.
  - DISCIPLINE LAST. `metric_groups.json` is goals, shooting, passing, one_on_one, defending, goalkeeping,
    set_pieces, discipline, outcomes, playing_time. The Rankings page's player block goes from "... Defending >
    Discipline > Goalkeeping" to "... Defending > Goalkeeping > Discipline"; its team block has no Goalkeeping
    board, so Discipline was already last there. The Form comparison shows Discipline after Set pieces. The team
    page has no Discipline row.
  - A TEST FAILS WHEN THE COMPONENT SPELLS A METRIC. `check-metric-labels.test.mjs` follows MetricComparison.astro
    through every .astro/.ts/.mjs file it imports and fails on any catalogue metric id spelled in code. It is
    red on main's component, which imports metricRows.ts ("goals_per_match", "goals", ...), and green now.
  - THE TEAM PAGE IS UNCHANGED. The 108 built team pages are byte-identical to main's build; each shows its 16 rows
    (15 on 2 pages, as on main). Only the match pages and the three Rankings pages differ between the two builds.
    pytest tests/: 1,465 passed; npm test: 0 failed; dbt parse clean; sync_metric_docs_blocks --check,
    check_copy_gate and check_description_hygiene OK.
