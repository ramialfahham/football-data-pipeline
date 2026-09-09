# Evidence — `board_leader_order`: the last ordering rule leaves the frontend

Measured against PROD (`football-data-pipeline-gcp.marts.mart_leaderboards`) and the local
toolchain. No acceptance_criteria block is required — the diff touches no `site_v2/src/` path — so
this demonstrates the contract's `done_when`.

criteria_demonstrated:
  - THE COLUMN IS A TOTAL ORDER, AND ALL THREE INVARIANTS HOLD OVER THE WHOLE MART. Running the new
    expression over prod's 3,395 league leaders: **0** duplicate positions within a board, **0** rows
    where it is defined on the wrong side of `league_leader_order = 1` (never NULL on a leader, always
    NULL on a non-leader), **0** consecutive pairs that contradict the ruled order.
  - THE TEST IS MUTATION-PROVEN, TWO-SIDED. With the ruled order the three checks return 0/0/0.
    Dropping the `minutes` leg from the ordinal returns **932 rows** — a dbt singular test fails on
    any row, so it goes RED.
    ⚠ The adjacency check is what catches that, and it is deliberately NOT a re-computation of the
    window: re-running `row_number()` inside the test and comparing would pass for ANY `ORDER BY`,
    because the test would be using the same one. It walks consecutive pairs with `lead()` instead
    and asserts the later row is not strictly better on the ruled keys.
  - IT REPRODUCES WHAT #40 MR B ALREADY RENDERS, SO THE PAYLOAD DOES NOT MOVE. Filtered to the elite
    pool and the current season, the ordinal gives:
        goals       PD, SA, LP, L1, ED, BL1, PL
        assists     PD, SA, ED, PL, LP, L1, BL1
        passes      LP, ED, PL, PD, SA, L1, BL1
        key passes  PD, ED, SA, LP, L1, PL, BL1
    identical to the committed `site_v2/src/data/landing.json`. So MR B's switch from a three-key
    ORDER BY to `order by board_leader_order` changes its code and not its bytes — which is the
    check that the column really encodes the rule the export was applying.
  - THE POOL NEVER ENTERS INTO IT, WHICH IS THE WHOLE CORRECTION. The ordinal is global across every
    league leader on a board; the elite filter above inherits the right sequence with no knowledge
    of it in the mart. Filtered, the values are sparse — 17, 18, 21, 31, 36, 40, 41 on the assists
    board — and sparse is the tell that the order is global rather than pool-shaped.
  - NOTHING EXISTING MOVED. `rank` keeps its DENSE_RANK definition (ties share a rank, top-10 cut
    inclusive of them) and `league_leader_order` is untouched. One column is added.
  - THE TOOLCHAIN IS GREEN. `dbt parse` clean apart from the pre-existing unused-snapshots warning.
    `check_layer_contract.py` and `check_description_hygiene.py` exit 0.
    SQLFluff on the new test: `All Finished!`, exit 0, full rule set from the repo root.
    SQLFluff on the changed model: 4 findings, ALL on the pre-existing
    `dbt_utils.generate_surrogate_key` line — the templater noise CLAUDE.md documents. Zero on any
    added line.

## ⛔ CI CAUGHT A SYNTAX ERROR THAT EVERY LOCAL GATE MISSED, AND THAT IS THE REUSABLE PART

Round 2 shipped and `data:build:mr` FAILED:

```
1 of 30 ERROR creating sql view model ci_mr165_marts.mart_leaderboards
  Database Error in model mart_leaderboards
  Syntax error: Trailing comma after the WITH clause before the main query is not allowed at [682:1]
```

Removing the abandoned `board_leaders` CTE left the comma after `ranked as (…)`. Why nothing local
saw it, which is the point worth keeping:

- **`dbt parse` does not compile SQL against BigQuery.** It parses Jinja and builds the manifest. A
  syntactically invalid query parses fine.
- **SQLFluff cannot catch a syntax error in THIS file at all.** It already reports `TMP`/`PRS` on the
  `dbt_utils.generate_surrogate_key` line — `dbt_utils` is unresolvable under the jinja templater —
  so the file is unparseable to it from line 197 onward, and a real error downstream hides inside
  noise that CLAUDE.md teaches you to ignore. "4 findings, all pre-existing" was true and useless.

**The check that does work, and that now backs this evidence:** compile the model, repoint its dev
schemas at prod, and let BigQuery parse it without running it —

```
dbt compile --select mart_leaderboards
sed 's/`dev_intermediate`/`intermediate`/g; s/`dev_core`/`core`/g' \
  target/compiled/.../mart_leaderboards.sql | bq query --use_legacy_sql=false --dry_run
```

`Query successfully validated. … will process 58945370 bytes of data.` It costs nothing (a dry run
bills zero) and it validates syntax AND every column reference against the real prod schema. Run
against the fix, it passes; run against the broken version it reproduces the CI error exactly.

## Why the implementation is shaped the way it is

The obvious form — rank the leaders in their own CTE and left join — was written first and
**rejected by the linter**, not by taste: SQLFluff's `ST07` forbids `USING`, and without it `RF02`
demands all forty-odd columns in the final select be qualified. Sorting leaders to the front of the
window (`case when league_leader_order = 1 then 0 else 1 end` as the first key) and discarding the
non-leaders' numbers with a `CASE` gives the identical positions with no join. Verified identical:
the numbers above come from the leaders-only formulation, and the shipped one matches them.

## What is NOT demonstrated here

- The dbt test has not been run BY dbt: `dbt build` is banned in this repo and the column is not in
  prod until this merges. What is shown is the test's own SQL executed against prod with the window
  inlined, both correct and mutated. `data:build:mr` runs it for real on the MR.
- The consumer is not here. #40 MR B swaps its three-key ORDER BY for `order by board_leader_order`
  once this merges and `data:build:main` recreates the view; it is parked in stash
  `TEMP-40-mrB-await-C`.
