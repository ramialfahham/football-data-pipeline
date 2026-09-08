# Acceptance evidence — a suspended match is information, not an alarm

Branch `fix/freshness-guard-severity-by-cause`, from main `4bef954`.

⚠ **CI CANNOT EXERCISE THE FRESHNESS TEST.** It carries `tags=['freshness_check']`, excluded by
`selectors.yml`'s `downstream` selector, by `data:build:mr`, and by `data:build:main`'s final
`dbt test`. It runs only in `fdp-nightly`'s unselected `dbt build`. A green MR pipeline says nothing
about that file. ⭐ The new reconciliation test carries no such tag, so CI **does** run it — and it
is `severity: warn`, so it reports rather than blocks.

criteria_demonstrated:

  - **`SUSP` and `INT` are gone from the guard, and no replacement carries them.**
    `dbt ls --select tag:freshness_check` returns two tests: the live guard and the pre-existing `NS`
    sibling. The warn test the first design added is deleted. The only occurrence of those statuses
    in the file is the paragraph explaining why they are not there.

  - **⚠ The freshness predicate returns 0 rows against prod, and that proves almost nothing** — no
    fixture is in ANY in-play status right now (0 of 64,437; 5,152 are `NS`, 59,285 terminal), so a
    nonsense WHERE clause would also return zero. Hence the synthetic test:

        id  status  hours after kickoff   caught
         3  2H          7                 YES
         4  P           7                 YES
         5  LIVE       24                 YES
         2  2H          5                 no    <- inside the 6h headroom, correctly ignored
         7  INT       720 (30 days)       no    <- excluded by STATUS, at any age
         8  SUSP      720 (30 days)       no
         9  FT         48                 no
        10  NS         -3 (future)        no

  - **⭐ THE NEW RECONCILIATION IS RED ON REAL DATA, AND EVERY ROW IS A FINDING.** Compiled and run
    against prod:

        team_sk  league   season  ours  standings  missing
        2937     AFCCL     2021      1          6        5   Al Wehda Club
        998      TSL       2022     35         36        1   Trabzonspor
        3573     TSL       2022     35         36        1   Gaziantep FK

    ⭐ **Those two Süper Lig rows ARE fixture 884568** — the Gaziantep 0-3 Trabzonspor earthquake
    forfeit filed as `CANC`, which I found this morning only by reading a status label and then
    searching the web for what happened. **The test finds it with no status list and no external
    research.**
    ⭐ **And the third row has a COMPLETELY DIFFERENT CAUSE, which is the case for the test rather
    than a wrinkle.** I first wrote that Al Wehda was "not previously known" and left it at that;
    `analytics-engineer-reviewer` refused to let it be cited as a GitLab #110 instance without a
    check, and it was right. Measured: `fct_fixture` holds **exactly ONE** AFCCL 2021 fixture for
    Al Wehda — a `PEN` tie on 2021-04-07 — against standings of 6. Those five games were never
    INGESTED; they are not matches we mishandled. So one detector surfaces a mislabelled forfeit and
    an ingest coverage gap in the same three rows, which is precisely what "reconcile the symptom
    instead of enumerating causes" is supposed to buy. ⛔ Al Wehda is NOT a #110 instance.

  - **⚠ THE STANDINGS COLLAPSE HAD TO CHANGE, and only a measurement showed it.** `fct_standings` is
    grained on `(league_code, season, team_id, group_name)`, so a team-season can carry several rows.
    Al Wehda AFCCL 2021 carries two — *"Ranking of second-placed teams"* and *"Promotion - AFC
    Champions League (Play Offs)"* — with an **identical `raw_ingested_at`**, so my original
    `qualify row_number() ... order by raw_ingested_at desc` was choosing between them on an unstable
    tiebreak. Across the warehouse:

        team-seasons with one standings row      3,960
        with more than one                         299
          of those, `played` AGREES                 95
          of those, `played` DISAGREES             204   <- spread up to 13 games

    For a numeric reconciliation that is unsound in both directions — it can invent a shortfall or
    hide one. Replaced with `max(played)`: deterministic, and it errs toward silence (if any
    authoritative table says N were played, we should hold at least N). **It returns the same 3 rows
    today**, so no current result changes; the test is now correct by construction rather than by
    luck. ⚠ The pattern I copied from `int_team_season__standings_primary` is fine for the DISPLAY
    fields it selects there and wrong for a number — copying a collapse without checking what it is
    collapsing for is the actual mistake.

  - **The one-directional choice is measured, not assumed.** Over 4,082 team-seasons joined to the
    standings:

        direction          rows    delta range   leagues
        equal             2,515    0             33
        ours HIGHER       1,564    +1 to +30     29
        ours LOWER            3    -1 to -5       2

    The "higher" population is a stale standings snapshot — standings are ingested at a point in
    time and we keep counting fixtures afterwards — so being ahead of them is the normal mid-season
    state. **A two-sided test would be red on 1,567 rows, 38% of the population, and would be
    switched off within a week.** The one-sided test is red on 3.

  - **`dbt parse` exits 0** (982 tests — UNCHANGED from main: one test is deleted
    and one added). **SQLFluff exits 0** on both changed files from the repo root, exit code read
    BARE and UNREDIRECTED. `check_layer_contract.py` and `check_description_hygiene.py` pass.

## ⛔ TWO REVIEWER FAILS, BOTH MINE, AND THE SECOND WAS THE WORST ERROR OF THE BRANCH

**Round 1 — `scope-auditor`:** I classified the SUSP/INT severity against `engineering_standards.md`
§3's "source data quality issue" row, which is literally about GRAIN violations. Extending a written
rule to a domain it does not cover is §10, and `!155` had already established this class is the
CPO's. Moot now — there is no severity to classify, because those statuses are simply not in the
test.

**Round 2 — `scope-auditor`:** the CPO's rulings were quoted in `contract.md` and recorded nowhere
checkable. `escalations.log` had no entry for this branch, and its last word on the subject was two
older entries saying the freshness guard was *unruled*. Fixed by logging it: all four quotes now
resolve verbatim in the file, `grep -cF` = 1 each.

**⛔ Round 2 — `analytics-engineer-reviewer`: my widened reconciliation was a TAUTOLOGY.**
I widened `assert_mart_team_season_insights_games_match_played` from BL1 to 46 leagues and reported
"0 mismatches over 1,826 rows" as proof of reconciliation against an independent authority. It is
zero **by construction**:

    mart_team_season.sql:34        m.season_games_played as played     <- an ALIAS of our own count
    mart_team_season_insights.sql  joins mart_team_season on team_season_sk

Both operands resolve to the same row of `int_team_season__metrics`. The predicate could not fail on
any data, ever. **I read the column name `played` and asserted its provenance instead of reading the
SQL** — and then removed `SUSP`/`INT` from the freshness guard on the strength of it, which would
have left the failure mode with no detector at all.

⭐ The genuine count existed the whole time and was being dropped: `fct_standings.sql:30` carries
`cs.played_all as played` from the provider's standings feed, and
`int_team_season__standings_primary.sql` reads `fct_standings` but projects only `standing_rank`,
`form` and `group_description`. The new test joins `fct_standings` directly.

⛔ **The tautology test is DELETED, not kept alongside.** A test that is provably incapable of
failing is not caution — it appears in every green run as evidence of a check that never happened.

## What this does NOT do

- **It does not fix the three rows it reports.** Their correction is GitLab **#110**'s open rule on
  awarded results filed under the wrong status. That is why severity is `warn` and not `error` — CPO
  ruling, *"do it that way, warn severity for now"*.
- **It does not weaken detection of our own failures.** A match genuinely playing 6 hours after
  kickoff is still an error, and a stuck `NS` is still an error at 30 hours in its own test.
- **It does not touch the tag mechanism, the selectors, or any CI job.**
