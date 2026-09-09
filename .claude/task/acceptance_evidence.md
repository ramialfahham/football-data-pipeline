# Evidence — ranking in the warehouse: the layering rule + `league_leader_order`

Measured in this session against PROD (`football-data-pipeline-gcp.marts.mart_leaderboards`,
189,986 rows) and the local toolchain. No acceptance_criteria block is required here — the diff
touches no `site_v2/src/` path — so this demonstrates the contract's `done_when` instead.

criteria_demonstrated:
  - THE DEFECT IS REAL AND MEASURED, NOT ARGUED. `rank` is a DENSE_RANK, so joint leaders share it.
    Of the 28 league-boards the Home block renders (4 boards x 7 elite leagues), 57 rows carry
    rank 1 — 29 surplus. 12 of the 28 league-boards hold a tie. 0 have a NULL `minutes`.
  - THE NEW COLUMN PICKS EXACTLY ONE ROW, AND THE RIGHT ONE. Running the ruled window over prod:
    28 league-boards produce 28 leaders; all 28 carry the board's best value, so minutes never
    outrank the metric; 12 of the 28 came from a tie and all 12 were won by fewest minutes played.
  - THE TEST IS MUTATION-PROVEN, TWO-SIDED, OVER THE WHOLE MART. With the ruled order
    (`sort_value desc, minutes asc nulls last, player_sk asc`) the test's two checks return
    **0 and 0**. With the `minutes` leg dropped it returns **443 rows** — a dbt singular test fails
    on any row, so it goes RED. The count check alone would NOT have caught that mutation: removing
    the minutes leg still yields exactly one leader per league-board, just the wrong player. That is
    why the test asserts the rule and not only the count.
  - NULLS LAST IS LOAD-BEARING, AND THE TEST NOW COVERS IT. BigQuery sorts NULLs FIRST ascending, so
    without it an unknown minutes total would beat every known one and win every tie it appeared in.
    Round 1 flagged — without failing — that the tie check was gated on the leader's own minutes
    being known, so a `nulls last` -> `nulls first` regression could not fire it. A flagged
    trade-off is still a trade-off, so a third clause was added rather than banking the pass.
    ⚠ IT IS NOT DEAD CODE: `minutes` carries NO `not_null` test on `mart_leaderboards` or on
    `int_player_season__metrics` (checked both ymls), so a NULL is permitted by the schema.
    ⚠ AND IT CANNOT BE MUTATION-TESTED ON PROD, WHICH IS SAID PLAINLY RATHER THAN GLOSSED: all
    189,986 mart rows have a non-NULL `minutes`, so flipping to `nulls first` against prod returns
    0 — because there is nothing to trigger it, not because the clause works. Proven on a synthetic
    three-row case instead: with `nulls first`, the NULL-minutes player takes the league over one
    with 900 minutes at the same value, and the new clause returns 1 row, so the test goes RED.
  - THE TOOLCHAIN IS GREEN. `dbt parse` clean apart from the pre-existing unused-snapshots warning.
    `check_layer_contract.py` exit 0. `check_description_hygiene.py` exit 0 — 1,643 descriptions,
    rendered lengths within BigQuery's 1,024/16,384 limits, which matters because `persist_docs` is
    on and an over-long column description fails the prod build.
    SQLFluff on the new test: `All Finished!`, exit 0, full rule set from the repo root.
    SQLFluff on the changed model: 4 findings, ALL on the pre-existing
    `dbt_utils.generate_surrogate_key` line, which is the templater noise CLAUDE.md documents
    (`dbt_utils` is unresolvable under the jinja templater). Zero findings on any added line.
  - NOTHING EXISTING MOVED. `rank` keeps its DENSE_RANK definition, so ties still share a rank and
    the top-10 cut stays inclusive of them — a documented consumer contract this MR deliberately
    leaves alone. One column is added; no column changes; no number changes.

## What is NOT demonstrated here, stated rather than implied

- The dbt test has not been RUN by dbt, because `dbt build` is banned in this repo and the column is
  not in prod until this merges. What is shown above is the test's own SQL executed against prod
  with the window inlined, both correct and mutated. `data:build:mr` runs it for real on the MR.
- The consumer side is not here. #40 MR B switches the export to `league_leader_order = 1` and
  re-exports `landing.json`; it is parked in stash `TEMP-40-mrB-block` on `feat/40-top-players-block`
  and rebases onto this once it merges and `data:build:main` recreates the view.
