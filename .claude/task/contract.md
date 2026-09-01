# Task contract — assert the player-season grain in its JOINABLE spelling

objective: >
  **Add one uniqueness test to `int_player_season__metrics`: `(player_sk, league_code,
  season_api_year)`.**

  The model already asserts the same grain as **`(player_sk, season_sk)`**. `season_sk` is built from
  `(league_api_id, season_api_year)`, so the two are the SAME key in two spellings — this is not a
  second, weaker assertion. It is the surrogate form and the readable form of one rule.

  ⭐ **WHY THE SECOND SPELLING EARNS ITS KEEP.** Anything joining a LEG model has to group on
  `(player_sk, league_code, season_api_year)` — the readable columns — not on `season_sk`. Asserting
  that form directly is what lets a consumer know the join cannot fan out. Today nothing checks it,
  so a `league_code` split would surface downstream as **missing rows with no test naming the
  cause** — the worst shape of data defect, because the symptom appears far from the cause.

  ⭐ **AND IT CLOSES AN ASYMMETRY THAT ALREADY EXISTS.** The TEAM model beside it has carried
  **both** spellings since it was written; the player model carried only the `season_sk` form. This
  MR makes the pair symmetric.

  ⚠ **This is parked work, resumed — not new design.** It sat in `stash@{0}` labelled *"PARK:
  value-equivalence test, ships AFTER the catalogue rows"*. Those rows shipped in steps 4 and 5.

refs: >
  **CPO, verbatim, this session:** *"start the value-equivalence test"*.

  **`stash@{0}`**, *"PARK: value-equivalence test, ships AFTER the catalogue rows"* — the parked
  work, carried on branch `feat/metric-catalogue-value-equivalence`.
  ⚠ **The stash is NOT popped.** It also carries a 304-line `contract.md` for the unrelated task it
  was parked from, and its diff context references `pass_accuracy_pct`, a column the naming
  programme has since renamed to `passes_accuracy_player_pct`. **Only the twelve-line test is taken,
  applied by hand against the current file.** The stash stays on the stack untouched.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml

protected_override: >
  ⛔ **NO MODEL SQL CHANGES.** `int_player_season__metrics.sql` is not touched. This MR adds an
  ASSERTION about behaviour that already exists; if the assertion fails, the fix is upstream data or
  an upstream model, never weakening the test.

  ⛔ **NO EXISTING TEST IS REMOVED OR RELAXED.** The `(player_sk, season_sk)` test stays exactly as
  it is. Both spellings are asserted, which is the whole point — replacing one with the other would
  discard the surrogate-key guarantee that downstream `season_sk` joins rely on.

  ⛔ **`stash@{0}` IS NOT POPPED OR DROPPED.** The stash stack is repo-level and load-bearing; other
  parked work lives in it. Read from it, leave it alone.

impact_map: >
  A dbt schema test only. It adds one assertion to the nightly and to `data:build:mr`; it changes no
  table, no column and no value. ⚠ **The one real risk is that the assertion is FALSE in production
  data** — in which case CI goes red and the MR has surfaced a live defect rather than caused one.
  That is checked BEFORE committing by querying BigQuery directly (see `decisions_taken §2`).

acceptance_criteria:
  - The test compiles: `dbt parse` EXIT=0, and all three columns exist in the model's final
    projection (verified: `int_player_season__metrics.sql:70-75`).
  - **The assertion is TRUE in production data**, verified by direct query before commit — not
    assumed, and not left for CI to discover.
  - **The assertion is not VACUOUS**, verified in the same query: if no player ever appeared in more
    than one `league_code` within a season, the two spellings could not diverge and the test would
    be theatre. Whatever the answer, it is reported.
  - The existing `(player_sk, season_sk)` test is byte-identical, and no model SQL changes.

decisions_taken: >
  ⭐ **§1. HAND-APPLIED, NOT POPPED.** See `refs`. The stash's own diff no longer matches the file —
  the naming programme renamed a neighbouring column in its context lines — and it carries an
  unrelated contract. Taking the twelve lines by hand is the smaller, checkable operation.

  ⭐ **§2. THE TEST IS VERIFIED AGAINST REAL DATA BEFORE IT SHIPS, AND IN BOTH DIRECTIONS.**
  ⚠ `dbt build` must never run locally, so a green local run is not available and is not claimed.
  Instead the assertion is checked by querying `intermediate.int_player_season__metrics` directly:
    · **does it hold** — `count(*)` against `count(distinct (player_sk, league_code, season_api_year))`;
    · **is it equivalent** to the existing test — the same count against
      `count(distinct (player_sk, season_sk))`;
    · **is it non-vacuous** — how many players appear under more than one `league_code` in a season,
      which is the only situation in which the two spellings could ever disagree.
  This is the `feedback_verify_the_test_fails` discipline adapted to a test that cannot be run
  locally: prove the thing it asserts, and prove the assertion has content.

decisions_reserved:
  - ⚠ **If the assertion turns out to be FALSE**, this MR stops and the finding goes to the CPO.
    Adjusting the grain, or weakening the test to make it pass, would be exactly the
    `feedback_never_loosen_a_guard` failure — and the model's stated grain would then be wrong,
    which is a data-model question, not a test question.
  - ⚠ CARRIED, untouched: step 5's two follow-ups; `fdp-freshness`'s hourly cadence; the disabled
    GitLab schedule; the `__team`/`__player` split with no live instance; the resolver as a CI gate;
    **#99**, **#96**, **#87**, **#98**.

done_when: >
  - The test is present on `int_player_season__metrics`, with the comment explaining why a second
    spelling of one grain is not a second key.
  - `dbt parse` EXIT=0; the offline gates green.
  - The three measurements above are reported with their numbers, including the non-vacuity one.
  - `stash@{0}` still on the stack, untouched.
  - Blinded review; `review.md` bound with `--staged-hash`. **Round cap 3.**
