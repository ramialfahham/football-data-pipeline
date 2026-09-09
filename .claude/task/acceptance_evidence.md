# Evidence — the three served columns the Top teams block needs

Measured against PROD (`football-data-pipeline-gcp.marts.mart_team_leaderboards`) and the local
toolchain. No acceptance_criteria block is required — the diff touches no `site_v2/src/` path — so
this demonstrates the contract's `done_when`.

criteria_demonstrated:
  - THE MART WAS MISSING ALL THREE, READ NOT ASSUMED. `INFORMATION_SCHEMA.COLUMNS` on prod returns
    13 columns for this mart: no `is_current_season`, no `league_leader_order`, no
    `board_leader_order`. Without them the Top teams export would have to pick a season and compute
    an order for itself, which is the pair of defects that cost the player block four failed rounds.
  - ALL FOUR INVARIANTS HOLD OVER PROD. Running the new expressions across the whole mart, 877
    league leaders: **0** league-board-seasons with other than exactly one leader, **0** duplicate
    board positions, **0** rows where `board_leader_order` is defined on the wrong side of the
    leader flag, **0** consecutive pairs contradicting the ruled order.
  - THE TEST IS MUTATION-PROVEN, TWO-SIDED, ON EVERY INVARIANT. With the ruled order the checks
    return 0/0/0/0. Dropping the `team_sk` leg from the board order returns **89 rows** — a dbt
    singular test fails on any row, so it goes RED.
  - ⛔ THE `is_current_season` CHECK WAS TOO WEAK AND REVIEW CAUGHT IT. I shipped a cardinality-only
    guard — "exactly one distinct season flagged per league" — on the identical column whose player
    mart sibling (`assert_one_current_season_per_league.sql`) already carries three checks, its
    header recording why the first alone is insufficient. That is the already-rejected shape,
    repeated in the mirror mart. Now strengthened to cardinality AND recency AND row completeness,
    and mutation-proven three ways against prod:
        correct                                      ->  0 leagues failing
        ORDER BY season_api_year ASC (oldest flagged) -> 33 leagues failing
        rank() reverted to row_number() (one row)     -> 44 leagues failing
    Both mutations are ones the cardinality-only version passes green: the first still flags exactly
    one season, the second still flags one season that is still the latest.
    ⚠ The adjacency check is what catches that, and it is deliberately NOT a re-computation of the
    window: re-running `row_number()` inside the test with the same ORDER BY would pass for any
    ordering. It walks consecutive pairs with `lead()` and asserts the later row is not strictly
    better on the ruled keys.
  - ⭐ THE COMPILED MODEL WAS DRY-RUN AGAINST PROD BEFORE PUSHING, which is the lesson `!165` paid
    for. `dbt compile --select mart_team_leaderboards`, dev dataset identifiers rewritten to the
    prod ones, piped to `bq query --dry_run`: **Query successfully validated … 1508922 bytes**.
    A dry run bills zero and checks syntax AND every column reference against the real schema.
    On `!165` a trailing comma reached CI precisely because this step did not exist: `dbt parse`
    does not compile SQL, and SQLFluff cannot see past this file's `dbt_utils` line.
  - THE TOOLCHAIN IS GREEN. `dbt parse` clean apart from the pre-existing unused-snapshots warning.
    `check_layer_contract.py` exit 0. `check_description_hygiene.py` exit 0 over 1,647 descriptions.
    SQLFluff on the new test: `All Finished!`, exit 0, full rule set from the repo root. SQLFluff on
    the changed model: 4 findings, ALL on the pre-existing `dbt_utils.generate_surrogate_key` line —
    the templater noise CLAUDE.md documents. Zero on any added line.
    ⚠ `check_description_hygiene.py` FAILED first, on two real findings in my own text: an issue
    reference (`#114`) and a severity emoji inside a column description. Both are banned because a
    description states what the data means rather than arguing a case. Rewritten plainly; the
    argument stays in the model comment, where it belongs.
  - NOTHING EXISTING MOVED. `rank` keeps its DENSE_RANK definition and every other column is
    untouched. Three columns are ADDED, and NOTHING reads this mart yet —
    `scripts/export_site_data.py` does not query it at all today — so the blast radius outside the
    model is empty.

## The ruling this implements, and what it is not

The CPO ruled on 2026-09-09 that there is NO sporting tie-break for the team boards. The player
rule — fewer minutes played — does not transfer, because teams have no minutes, and the analogue I
proposed (`season_games_played`) was rejected: *"will not work most of the time"*. Measured, he is
right twice over: it barely discriminates (3.6 distinct game counts per league-season on average; in
72 of 235 every team is level), and for a RATE fewer games is less evidence rather than better
performance. So `team_sk` is the whole tie-break and the model says plainly that it means nothing.
GitLab #114 is open at LOW priority to find something better.

## What is NOT demonstrated here

- The dbt test has not been run BY dbt: `dbt build` is banned and the columns are not in prod until
  this merges. What is shown is the test's own logic executed against prod with the windows inlined,
  both correct and mutated. `data:build:mr` runs it for real on the MR.
- The consumer is not here. The Top teams block follows in its own MR once this merges and
  `data:build:main` recreates the view.
