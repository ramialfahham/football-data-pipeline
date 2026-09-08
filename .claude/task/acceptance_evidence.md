# Acceptance evidence — a team id that did not play the match

Branch `fix/fixture-team-id-overrides-all-sources`, from main `448ef77`.

Everything below is measured against **LIVE PROD DATA** by compiling the changed models and running
them read-only. The ban is on `dbt build`, which writes and bills a materialisation; a SELECT over
the compiled SQL is neither.
⚠ The compiled SQL exceeds Windows' command-line limit, so every query is fed to `bq` on **stdin**.
⚠ `dbt compile` resolves refs against the DEV target, so each query rewrites `dev_staging` →
`staging` and `dev_scratch` → `dbt_analytics`. The renamed seed does not exist in prod at all, so
its relation is replaced with an inline four-row literal — the CSV's contents, transcribed.

criteria_demonstrated:

  - **Both mis-attributions move, and only they do.** Composed against prod:

        base_apif__fixture_players      21 moved   1,875,217 unmoved   0 added   0 removed
        base_apif__fixture_statistics    1 moved      99,139 unmoved   0 added   0 removed
        base_apif__teams                 2 keys removed   4,618 unchanged   0 added

    Row for row, the only movements in the entire warehouse:

        BSA   fixture 1492362   21 player rows   22722 -> 132   (Chapecoense-sc)
        WCQAS fixture 1100382    1 stats row      4767 -> 1544  (Macau)

  - **⭐ THE CONTROLLED BASELINE SAYS THE CODE MOVES NOTHING; THE SEED ROW DOES.** The same new SQL
    run with **main's seed contents** — the three rows that exist today, without the 22722 row —
    reports `0 moved, 1,875,238 unmoved`. Every one of the 21 moves is attributable to the seed row
    a human wrote, not to a side effect of wiring the override into a new model. The two totals
    reconcile exactly: 1,875,217 + 21 = 1,875,238.

  - **The second key removed was not predicted, and it is the same gap.** `base_apif__teams` drops
    `(BSA, 22722)` as intended and also `(UEL, 2263)` — Riga FC's duplicate provider id, an `alias`
    row that has been in the seed since **#526**. The alias was reaching events only, so the entity
    dimension has been minting a team key for a provider id the corrections retired years ago.
    Applying the override to the key union is what finally removes it. Mação **4767 stays** a team,
    correctly: it is a real club and only its rows in two WCQAS fixtures were mis-attributed, so
    only those rows move.

  - **⛔ ZERO ORPHANS, CHECKED ACROSS EVERY FACT — because this was the reason the approved fix
    could not be built as approved.** 41 error-severity `relationships` tests point at `dim_team`,
    none filtered. Every distinct `team_sk` in every fact, against the new key set:

        | fact                | distinct team keys | orphaned |
        |---------------------|--------------------|----------|
        | fct_fixture_event   | 2,653              | 0        |
        | fct_fixture (home)  | 3,165              | 0        |
        | fct_fixture (away)  | 2,846              | 0        |
        | fct_fixture_player_stats | 1,513         | 0        |
        | fct_fixture_team_stats   | 1,695         | 0        |
        | fct_standings       | 968                | 0        |

    Removing 22722 from `dim_team` **without** moving the 21 rows off it would have put 1 orphan in
    `fct_fixture_player_stats` and broken the build in a different place. That is measured, not
    argued.

  - **`dbt parse` exits 0. SQLFluff exits 0** on all three changed models and both new tests, run
    from the repo root under the full rule set, exit code read BARE. `check_layer_contract.py`,
    `check_registry_var_sync.py`, `check_description_hygiene.py` and `check_competition_type_seed.py`
    all exit 0.

  - **No team's slug moves.** The whole slug ladder in `base_apif__teams_global` recomputed over the
    corrected key set, compared against `dim_team` row by row: **0 slugs changed, 3,329 unchanged,
    0 rows added, 0 nameless rows**. The only two rows that disappear take their own slugs with
    them — `riga-fc` (2263) and `team-22722`. A slug is assigned once and is a URL (#852), so a key
    removal that reshuffled a surviving team's slug would be a much larger change than this MR is
    entitled to make. Checked because the removal of `(UEL, 2263)` was not predicted, not because
    anything suggested it had happened.
    ⭐ **Why nothing moves, rather than just the number.** "0 changed" invites the obvious objection:
    2263 owns `riga-fc` today, so when it disappears the canonical club should claim that slug at
    level 1. It does not, because the two rows do not share a name — the canonical 10124 is
    `Riga` / Latvia and already holds the uncontested slug `riga`; only the duplicate was ever
    called `Riga FC`. `riga-fc` is therefore freed and taken by nobody, which is the outcome #526's
    alias row was written to produce. Same shape on the other pair: 4767 is `Mação` / Portugal at
    `macao` and 1544 is `Macau` at `macau`, two different slugs for two different entities, and
    neither is removed — only one statistics row moves between them.

## ⛔ THE CORRECTION DOES NOT REACH PROD ON A BARE BUILD, AND A REVIEWER FOUND THAT, NOT I

Everything above is a read-only SELECT over the compiled model SQL. It proves what the corrected
LOGIC computes. It does not prove what the incremental TABLES will contain after a nightly run, and
those are different things:

  - `fct_fixture_player_stats` and `fct_fixture_team_stats` are **both** `materialized='incremental'`
    with a bare `raw_ingested_at > max(target)` filter and **no self-heal clause**. A finished
    fixture's stats never get a newer `raw_ingested_at`, so neither corrected fixture is
    re-processed on a bare `dbt build` — which is what the nightly runs.
  - The failure that produces is precisely the one this MR exists to remove: `base_apif__teams` is a
    table and drops 22722 every night, while the fact keeps 21 rows carrying it. Orphan, and
    `relationships` at `core.yml:725` stops the build. Both new guards go red too.
  - ⚠ **Copying the events self-heal would not have fixed it**, which is the part I would have got
    wrong on my own. `fixture_player_stat_sk` hashes `(fixture_id, league_code, team_id, player_id)`
    and `fixture_team_stat_sk` hashes `(fixture_id, league_code, team_id)`. Correcting `team_id`
    CHANGES the unique key, so a merge inserts the corrected row and strands the old one — dbt never
    deletes. `fct_fixture_event`'s self-heal works only because `event_sk` excludes `team_id`.

**The deploy therefore requires one command, once, at merge:**

    dbt build --full-refresh --select fct_fixture_player_stats fct_fixture_team_stats

**A full refresh of these two is safe, and that is measured, not assumed:**

    fct_fixture_player_stats  1,875,238   base_apif__fixture_players      1,875,238   equal
    fct_fixture_team_stats       99,140   base_apif__fixture_statistics      99,140   equal
    fct_fixture_event           858,032   base_apif__fixture_events         858,015   +17

Nothing has accumulated in the two target facts that their base tables do not still produce, so
rebuilding them loses nothing. ⭐ The third line is why they stay incremental rather than becoming
tables: the events fact **does** retain 17 rows base no longer produces, so a fanout fact genuinely
does accumulate, and dropping these two to tables would trade a loud one-off deploy step for silent
data loss the first time the provider stops returning a fixture. Combined rebuild size 0.39 GiB —
about 0.3% of one night's measured pipeline volume — so cost was never the argument either way.

⛔ **The contract asserted the opposite before this round.** Its `impact_map` said `fct_fixture_event`
was the only incremental model in the chain. I wrote that from memory instead of opening the two
files, and every offline gate, `dbt parse` and the whole prod verification above accepted it,
because none of them reads a `config()` block looking for a claim to contradict.

## ⛔ A SAFETY NET I ASSERTED DID NOT EXIST — so it was built

The contract claimed the seed already carried a `relationships` test from `correct_team_api_id` to
`dim_team.team_api_id`. It never did, under either name. I had misread a `relationships` block that
belongs to the NEXT seed in the same file, `team_name_overrides`, whose column is also an id
pointing at `dim_team`.

The hole that leaves is not cosmetic. `correct_team_api_id` is hand typed, this seed is explicitly
the registry for the NEXT mis-attribution, and a typo does not fail — it silently re-points a
fixture's rows at whichever real team the mistyped id happens to name. Neither participant guard
catches it: they ask whether the team played the fixture, not whether the id is the right team.

The test is now added, registered by dbt as
`relationships_fixture_team_id_overrides_correct_team_api_id__team_api_id__ref_dim_team_`, and
mutation-tested against the corrected key set:

| variant | rows returned |
|---|---|
| the four shipped `correct_team_api_id` values (132, 1544, 10124, 25274) | **0** |
| the same four plus one typo'd id | **1 RED** |

⚠ No cycle: the seed feeds `base_apif__teams` and the test points back at `dim_team`, but a dbt test
is a leaf node rather than part of the model DAG. `dbt parse` and `dbt ls --resource-type test`
both confirm it.

## ⛔ Mutation testing — both guards watched RED

Each cell is the number of rows the guard's own predicate returns, run against prod.

| variant | `player_stats_guard` | `team_stats_guard` |
|---|---|---|
| **shipped** (corrections applied) | **0** | **0** |
| corrections reverted | **21 RED** | **1 RED** |

The reverted variant is not a hypothetical: it is main, today. Both guards fail on the warehouse as
it currently stands, which is the whole point — `assert_team_stats_team_in_fixture_participants`
fails on a defect that was diagnosed and registered under **#53** and then left in prod, because the
override was wired to events and nobody checked the other two feeds.

⭐ **The guard found the second bug before the code did.** Running the existing event guard's
predicate against the other two facts was the first thing done after reading the bug report, and it
returned two offenders rather than one. Writing the fix for only the reported fixture would have
shipped a new error-severity test that fails on prod the night it lands.

## ⛔ What the approved plan could not have known, and why it changed

The CPO approved *"go with A"* — stop `base_apif__teams` admitting a key no source can name. It is
the natural reading of the defect and it does not work, for a reason only measurement shows: the
rows that carry the bad id are in a fact with an error-severity `relationships` test on that column.
A is not too small a fix, it is the wrong end of the pipe. The id has to stop being emitted, not
stop being resolvable.

⚠ There is also a trap in the ORDER of the correction that reading the SQL does not make obvious.
Both target models dedupe on a key containing `team_id`, and both carry a uniqueness test on that
grain. Correcting after the dedup emits two rows for one `(fixture, team)` whenever the correct id
already has one; correcting before it lets the model's existing latest-ingest-wins rule resolve the
collision. Neither live case collides today — fixture 1492362 has no rows for 132, fixture 1100382
none for 1544 — so the wrong order would have passed every test in this MR and broken on the next
mis-attribution. Checked, then written into the model as a comment rather than left as folklore.

## What this does NOT do

- **It does not touch `not_null` on `dim_team.team_name`.** The backstop caught this, loudly, at
  the worst possible moment — which is what a backstop is for. The new guards catch the class
  earlier and name the fixture; the last line stays where it is.
- **It does not re-attribute anything automatically.** A non-participant block is never reassigned
  to "whichever participant has no rows", which would have fixed both cases with no seed row at
  all. That is a derivation that invents attribution from an absence and fires silently.
- **It does not fix `base_apif__players`**, which has the identical latent exposure — three name
  sources, nobody dropped when all three are null, and the same error-severity `not_null` on
  `dim_player.player_name`. Recorded in `decisions_reserved`.
- **It does not fix the freshness guard.** That is the OTHER nightly failure, and it is what let
  this one hide for three nights: a permanently red test is not one broken check, it is cover.
