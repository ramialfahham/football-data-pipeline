# Review — test/player-season-grain-value-equivalence — 2026-09-01

> **One dbt schema test**: `(player_sk, league_code, season_api_year)` unique on
> `int_player_season__metrics`. The model already asserts the same grain as
> `(player_sk, season_sk)`; this adds the readable spelling that any leg-model join must use.
> No model SQL, no existing test touched. Branched from main `fadd52f`.

diff_sha256: 4a6b3e6a90173edb9cbcb19440ddd2b84655d385ffb30c54a6408d60481d8de0

rounds: 1

⭐ **VERIFIED BEFORE COMMITTING, NOT LEFT FOR CI.** `dbt build` never runs locally, so no green local
test run is claimed. Instead the test's own logic — `dbt_utils` emits *group by the columns, keep
groups with `count(*) > 1`* — was run against production, as written and mutated three ways:

    as written  (player_sk, league_code, season_api_year)   PASS   0 failing groups
    existing    (player_sk, season_sk)                      PASS   0 failing groups
    mutation    drop league_code                            FAIL   34,884 failing groups
    mutation    drop season_api_year                        FAIL   41,256 failing groups
    mutation    player_sk alone                             FAIL   31,168 failing groups

**Every column in the key is load-bearing.** 185,421 rows, both spellings distinct at 185,421, and
**34,884 player-years span more than one `league_code`** (max 8) — so the test is not vacuous, which
was the thing most worth disproving.

## analytics-engineer-reviewer
VERDICT: PASS

⭐ **It traced my central claim to source instead of accepting it, and sharpened it.**

risks_checked:
- **The value-equivalence claim verified at source**: `season_sk` really is
  `generate_surrogate_key(['league_api_id', 'season_api_year'])` — `dim_competition_season.sql:8`
  and `fct_fixture.sql:11`. Then traced `league_code` and `season_sk` end-to-end from `fct_fixture`
  through `int_player_club_season__metrics.sql:56-57` into the aggregation's group-by: **both come
  off the same fixture row**, so most divergence would trip the existing test as well.
- ⭐ **A case I had not considered, and it strengthens the MR**: if two different `league_api_id`s
  ever shared one `league_code` within a season, the new test would be **strictly stronger** than
  the old rather than a respelling. Not rulable out from static reads; ruled out *empirically* by
  the equal counts. So the precise claim is **equivalent today, and structurally either equivalent
  or stronger — never weaker.** The evidence now says that instead of "two spellings".
- ⭐ **The redundancy rule I should have checked myself**: `engineering_standards.md:195` forbids
  repeating a uniqueness assertion **across layers** unless the grain changes. Found **inapplicable**
  — this is two assertions on one model in one layer, each in the spelling a different consumer
  needs. It also confirmed the precedent is real: `int_team_season__metrics` already carries both a
  `team_season_sk` unique test and a `(league_code, season_api_year, team_sk)` combination test.
- Layer placement correct per `layering.md`; no model SQL touched; the existing
  `(player_sk, season_sk)` test byte-identical; no catalogue row, no hardcoded competition
  identifier, no consumption-layer change; A6 impact-map trigger does not apply (no grain change,
  no raw write, no `1_staging` model).
- ⚠ Its measurements were verified by code tracing, not re-queried — it has no BigQuery access. The
  numbers above are mine, and CI's `data:build:mr` is the only run that executes the test for real.

## scope-auditor
VERDICT: PASS

risks_checked:
- **Authority**: the CPO's *"start the value-equivalence test"* resumes parked work whose
  precondition (the catalogue rows, steps 4–5) is documented as shipped. The contract does not
  stretch it into new design; the column combination came from the stash, not from me.
- **Stash discipline**: confirmed from the diff that the new block uses the **current**
  post-rename column name, with no trace of the stale `pass_accuracy_pct` spelling the stash's
  context still carries, and nothing from that stash's unrelated 304-line contract leaked in.
  ⚠ It could not run `git stash list` — no shell in its harness — so it rested on my account.
  **Verified here instead: 17 entries, `stash@{0}` byte-identical at 2 files / 166 / 150.**
- **File-location sanity**: the test for `int_player_season__metrics` lives in `int_team_season.yml`
  because both model blocks share that one file — checked, not a scope mismatch.
- **Verification adequacy**: judged the substitute honest — disclosed as a substitute for
  `dbt build`, not misrepresented as a local green run.
- **Pre-commitment** in `decisions_reserved` — stop and escalate if the assertion were false, rather
  than weaken the test — checked against `feedback_never_loosen_a_guard` and found correct.
- `scope_paths` reconciled; no `.sql` in the diff; no new mechanism or recurring cost; no
  credential-shaped strings.

## escalations

**None raised.** Resuming parked work on the CPO's instruction, with its documented precondition met.

⛔ **Pre-committed and not needed**: had the assertion proved false, this MR would have stopped and
gone to the CPO rather than adjusting the grain or weakening the test — the model's stated grain
would then have been wrong, which is a data-model question, not a test question.

⚠ **CARRIED, untouched:** step 5's two follow-ups; `fdp-freshness`'s hourly cadence; the disabled
GitLab schedule `4379625`; the `__team`/`__player` split with no live instance; the resolver as a
committed CI gate; **#99**, **#96**, **#87**, **#98**.
