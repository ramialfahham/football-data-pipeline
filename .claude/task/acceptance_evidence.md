# Acceptance evidence — #82 MR1, object-level description coverage

> One line per declared criterion in `contract.md`, each read from an actually-executed command and
> from its OUTPUT rather than its exit code.
>
> ⚠ THE BULLETS BELOW ARE INDENTED 2sp ON PURPOSE. `_block()` in `git_discipline.py` collects lines
> under `criteria_demonstrated:` until the first NON-INDENTED non-empty line, so a bullet at column
> zero terminates the block immediately and the gate reads ZERO criteria.

criteria_demonstrated:

  - THE TWELVE GAPS ARE CLOSED, counted from dbt's manifest rather than by eye. After `dbt parse`:
    `models undescribed: 0`, `seeds undescribed: 0`, `sources undescribed: 0 of 11`. Before this
    MR the same measurement returned 1 model and 11 of 11 source tables.
  - THE SOURCE DESCRIPTIONS ARE DERIVED, NOT INVENTED, which is the CPO's "information upstream so
    we use it downstream" applied to prose. Each states what the payload holds, what ONE row is,
    and a known limit, taken from what the staging models and `docs/data_contract.md` already
    establish: the endpoint, whether a fetch covers a WHOLE league or a narrower slice, and
    append-only versus accumulating behaviour. Examples of limits carried through rather than
    glossed: transfers are fetched BY TEAM so an intra-league move returns twice; squads can list
    the same player twice; player profiles and player teams never refresh an existing row;
    fixture statistics are absent for competitions the provider does not cover to that depth, and
    absent is not zero.
  - `int_team__market_value_latest` IS DESCRIBED WITH ITS EMPTINESS AS A LIMIT, and the emptiness
    was VERIFIED not assumed: `select count(*) from core.fct_team_market_value_snapshot` returns
    **0** in production, which is the CPO's "we have not defined the process and pipeline to
    populate it", confirmed against the warehouse.
  - ⚠ THE MODEL WAS DECLARED IN NO YML AT ALL — that is WHY it had no description — so this MR
    creates `int_team_market_value.yml`. The path follows the existing subdirectory precedent
    (`domestic_league/matchday/int_matchday.yml`), not a new convention.
  - THE GATE WALKS FILES ON DISK, NOT YAML ENTRIES, and that is the load-bearing design choice.
    A check that read only yml entries would have found nothing to complain about for the model
    above and passed it green — the exact blind spot being closed. Model set comes from
    `models/**/*.sql`, seed set from `seeds/*.csv`; a missing yml entry is then just the extreme
    case of a missing description. Source tables are the deliberate exception, because a source is
    not a file and its declaration IS its existence.
  - THE COVERAGE RULE WAS SEEN RED ON THE REAL REPO, not only against tmp fixtures, because the
    claim is "this gate protects this repo" and a fixture cannot prove that. Three realistic
    regressions, each restored from a byte backup verified by sha256:
      `model's only yml deleted (the real defect)` RED ·
      `a source table description removed` RED ·
      `a seed description removed` RED.
    Baseline green before, green after.
  - THE DIAGNOSIS ORDER WAS WRONG AND A TEST CAUGHT IT. First version ran the coverage check after
    the `MIN_DESCRIPTIONS` floor, so a project with models but no descriptions reported "the walk
    has stopped matching" — blaming the extraction for what was actually an empty-description
    defect, and sending a reader after the wrong thing. Coverage now runs BEFORE the floor, the
    same ordering the unparseable-file check already uses for the same reason. The two checks read
    the yml independently, so a genuinely broken extraction still reaches the floor and is still
    diagnosed correctly.
  - THE COVERAGE DISCOVERY HAS ITS OWN ANTI-VACUOUS FLOOR, and it fires. `MIN_MODELS = 50` and
    `MIN_SOURCE_TABLES = 5`: without them, a moved directory or a changed suffix makes "every model
    is described" true by finding no models. `test_the_coverage_floor_fires_when_discovery_finds_
    nothing` runs both at their REAL values and asserts the output says `discovery looks broken`
    rather than reporting a content problem.
  - ⚠ FIVE EXISTING TESTS WENT RED AND THE FIX WAS NOT TO WEAKEN THEM. The tmp fixtures hold a
    schema file and no `.sql`, so the new floor tripped on every green-expecting test. The autouse
    fixture now lowers `MIN_MODELS`/`MIN_SOURCE_TABLES` for tmp projects exactly as it already did
    for `MIN_DESCRIPTIONS`, and both keep their real values in the floor's own test and against the
    real project. No assertion was deleted.
  - THE GATE IS GREEN REPO-WIDE, so main never goes red — the `check_copy_gate.py` precedent.
    Output: `DESCRIPTION HYGIENE ok: 630 descriptions across 20 files (507 column, 123 model/seed),
    6 rules, 9 docs blocks resolved, rendered lengths within 1024/16384; every one of 97 models and
    9 seeds on disk is described`. 630 is the previous 618 plus this MR's 12.
  - NO NEW WIRING AND NO PROTECTED-PATH EDIT WAS NEEDED. `validate:governance` and
    `stop_gate.py`'s FAST_GATES already invoke this script, so the new rule reaches CI and turn-end
    without touching `.gitlab-ci.yml` or any hook.
  - `dbt parse` is clean. The only warning is the pre-existing
    `unused configuration paths: snapshots.football_data_pipeline`, unrelated to this MR.
  - `python -m pytest tests/` — recorded below from the actual run, not predicted (#904).
  - The five offline gates pass, read from their OUTPUT and not their exit code.
  - Handover rides in this commit and fits its cap: 15,975 characters against 16,000, measured with
    Python `len()`.

## Corrected in round 2, both of them mine

  - A DESCRIPTION I WROTE WAS FALSE, and it is the worst kind: dangerous guidance stated as a known
    limit. `raw_apif_fixture_details` said "several rows can describe the same fixture and the
    newest is the fullest". `docs/data_contract.md:134` says the opposite — both versions are kept
    deliberately, "a retry chasing late statistics can come back richer in one section and poorer
    in another" — with fixture 1564795 yielding 27 events of which indices 17-26 come from the
    payload the retry would have replaced. `base_apif__fixture_events.sql:25` dedups per
    `(league_code, fixture_id, event_index)`, which only makes sense BECAUSE the newest row is not
    the fullest. A stranger following my sentence would take the newest row and silently lose
    events. Caught by analytics-engineer-reviewer's round-1 FAIL, verified against both the
    contract and the SQL before fixing. Now states that no single row is reliably fullest, that
    versions resolve per entity, and that `fixture_id` is not unique here.
  - A FLAG I RAISED WAS FALSE, WITHDRAWN. I claimed `RAW_APIF_LEAGUES` was absent from
    `docs/data_contract.md`. It is at line 65 ("Additional smaller table"), plus twice in the
    endpoint tables, and the file explains at 39-42 why it sits outside the grain table. I had
    grepped only the grain table's rows and reported the absence as a gap — trap 1, a too-narrow
    grep reported as a clean sweep. Surfaced by scope-auditor.
  - ONE REVIEWER NOTE ADOPTED. platform-reviewer passed but observed the success line globbed the
    trees a third time and dropped the `dbt_packages/` exclusion the enforcement path uses.
    Cosmetic today, but two definitions of "which files count" can drift, so both now use one
    `_on_disk()` helper.

## Raised, not fixed

  - `int_team__market_value_latest` has NO schema test, which §3 requires of every model. Not added
    here: the table has 0 rows, so any test would pass vacuously by construction, and this repo has
    shipped vacuous tests before. It needs data first, or a decision that the model goes.
  - The emptiness is not contained — `mart_team_market_value.sql` reads this model, so an empty
    fact reaches a MART.
