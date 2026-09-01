# Acceptance evidence — assert the player-season grain in its joinable spelling

Branch `test/player-season-grain-value-equivalence`, from main `fadd52f`.

**One dbt schema test added** to `int_player_season__metrics`: `(player_sk, league_code,
season_api_year)`. No model SQL, no column, no value changes. It asserts behaviour that already
exists, in the spelling a downstream join actually has to use.

criteria_demonstrated:

  - **The test compiles into a real node**, not just valid YAML. `dbt ls --resource-type test`
    returns **both** uniqueness tests on the model:
    `..._player_sk__league_code__season_api_year` (new) and `..._player_sk__season_sk` (existing,
    untouched). `dbt parse` EXIT=0.
  - **The assertion is TRUE in production, verified before committing** — not left for CI to find.
    `intermediate.int_player_season__metrics`: **185,421 rows**, and **185,421** distinct on
    `(player_sk, league_code, season_api_year)`.
  - **The two spellings are demonstrably equivalent on real data**: the existing
    `(player_sk, season_sk)` key also yields **185,421**. Same rule, two forms — which is the claim
    the MR is named for, now measured rather than reasoned.
    ⭐ **AND THE CLAIM IS SHARPER THAN "TWO SPELLINGS", per `analytics-engineer` at round 1.** It
    traced the derivation to source — `dim_competition_season.sql:8` and `fct_fixture.sql:11` both
    build `season_sk` as `generate_surrogate_key(['league_api_id', 'season_api_year'])` — and then
    found a case I had not considered: **if two different `league_api_id`s ever shared one
    `league_code` within a season, the new test would be STRICTLY STRONGER than the old, not a
    respelling.** That cannot be ruled out from static reads. The equal counts above rule it out
    *empirically for current data*. So the precise claim is: **the new test is equivalent to the
    existing one today, and structurally it is either equivalent or stronger — never weaker.**
    That is a better reason to add it than the one I started with.
  - **The test is NOT vacuous, and this is the number that matters**: **34,884 player-years span
    more than one `league_code`** (max **8** leagues for one player in one season), out of 139,139
    player-year pairs. So `league_code` is load-bearing in the key, not decoration. The identical
    34,884 appears for "player-years with multiple `season_sk`s" — exactly what
    `season_sk = f(league, year)` predicts, and a second confirmation of the equivalence.
  - **No NULL keys**: `league_code` and `season_api_year` are both non-null across all 185,421 rows,
    so the uniqueness claim has no NULL-grouping escape hatch.
  - **The existing test is byte-identical and no model SQL changed.**
  - **`stash@{0}` is still on the stack, untouched.**

## ⭐ THE TEST WAS BROKEN ON PURPOSE AND WATCHED GO RED — three ways

⚠ `dbt build` must never run locally, so a green local test run is not available and is not claimed.
Instead the test's own logic — `dbt_utils.unique_combination_of_columns` emits *group by the columns,
keep groups with `count(*) > 1`* — was run directly against production, as written and mutated:

| grain under test | result | |
|---|---|---|
| `(player_sk, league_code, season_api_year)` | **PASS** — 0 failing groups | the test as written |
| `(player_sk, season_sk)` | **PASS** — 0 failing groups | the existing test |
| drop `league_code` | **FAIL** — 34,884 failing groups | |
| drop `season_api_year` | **FAIL** — 41,256 failing groups | |
| `player_sk` alone | **FAIL** — 31,168 failing groups | |

**Every column in the key is load-bearing** — remove any one and the assertion collapses. A mutation
that still passed would have meant that column was decorative. This is
`feedback_verify_the_test_fails` adapted to a test that cannot be run locally: prove what it asserts,
then prove the assertion has content.

## The redundancy rule I should have checked myself

`dbt_project/docs/engineering_standards.md:195` says *"Do not repeat the same uniqueness assertion
downstream unless the grain changes."* I did not consult it before adding a second uniqueness test —
`analytics-engineer` did, and found it **inapplicable**: that rule targets re-testing an unchanged
grain **ACROSS LAYERS** (staging → base → later), whereas this is two assertions on **one model in
one layer**, each in the spelling a different consumer needs. ⭐ It also confirmed the precedent is
real rather than asserted: the sibling `int_team_season__metrics` already carries both forms — a
`team_season_sk` unique test plus a `(league_code, season_api_year, team_sk)` combination test.

## Gates

  - `dbt parse` — **EXIT=0**.
  - `check_layer_contract.py` — **EXIT=0**. `check_description_hygiene.py` — **EXIT=0**, 1604
    descriptions. `sync_metric_docs_blocks.py --check` — **EXIT=0**, 163 blocks.
    `check_registry_var_sync.py` — **EXIT=0**.
  - `pytest` / `npm test` / the site build are **not run and not claimed** — nothing Python,
    JavaScript or frontend changed, and a green suite for a YAML test addition would be noise
    dressed as rigour.
  - ⚠ **The authoritative run is CI's `data:build:mr`**, which executes the test against BigQuery.
    Everything above is the strongest evidence obtainable without it, stated as exactly that.

## Parked work resumed, not popped

The test came from `stash@{0}` — *"PARK: value-equivalence test, ships AFTER the catalogue rows."*
Those rows shipped in steps 4 and 5, so the precondition is met.
⚠ **The stash was READ, never popped.** It also carries a 304-line `contract.md` for the unrelated
task it was parked from, and its diff context references `pass_accuracy_pct` — a column the naming
programme has since renamed to `passes_accuracy_player_pct`, so the patch would not have applied
cleanly anyway. Only the twelve-line test was taken, by hand, against the current file. The stash
stack is repo-level and holds other parked work; it is left exactly as found.

## Not done, deliberately

  - **The comment on the test carries the measured numbers**, so the next reader does not have to
    re-derive whether the second spelling is redundant. That is the whole failure mode this test
    guards against being reintroduced by someone "simplifying" it away.
  - ⛔ If the assertion had been FALSE, this MR would have stopped and gone to the CPO rather than
    weakening the test — the model's stated grain would then be wrong, which is a data-model
    question, not a test question. It was true, so that path was not taken.
