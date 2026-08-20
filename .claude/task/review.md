# Review — chore/description-cleanup-shared-and-seeds — 2026-08-20

> MR3 of the description-drift programme. Both required reviewers FAILed round 1 with one
> finding each; both findings were real, both were verified against the code before being
> accepted, both were fixed, and both reviewers PASSed on a narrow round-2 confirm.

diff_sha256: 991fb6b5789145b9af6354ac5427ad765f4c31ed5b4b89701e4ac47ba63ddf93

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- All 7 changed files match `scope_paths` exactly. No MR4 file (`core.yml`, `base.yml`,
  `int_momentum.yml`), no MR5 file (`check_description_hygiene.py`), no MR6 change
  (`persist_docs`, `dbt_project.yml`) is touched, so `decisions_reserved` holds.
- The six-MR split cited in `decisions_taken` matches `escalations.log` verbatim.
- The "four rulings rescued" claim was checked ruling by ruling against the whole log: none of
  the four exists elsewhere, and the four claimed-duplicate rulings genuinely do have prior
  entries, so deleting rather than rescuing those was correct. The rescue is not padding.
- ROUND 1 FAIL, now fixed: the AskUserQuestion ruling widening MR3 to three `.sql` files lived
  only in `contract.md`, which the next task overwrites — the repo's named unlogged-authority
  defect class, and the same error the programme exists to fix. It is now RULING 0 of this
  branch's `escalations.log` entry, and `contract.md` defers to it instead of standing alone.
  Confirmed durable and correctly deferred on round 2.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- ROUND 1 FAIL, now fixed: the rewritten `mart_standings` description claimed qualification and
  relegation zones are "deliberately not carried". FALSE — `mart_standings.sql:65` selects
  `group_description`, which `stg_apif__standings.sql:42-44` and the sibling column doc in the
  same file both identify as exactly that zone annotation. Verified independently before
  accepting. The text now says the annotation is carried verbatim but never interpreted, so
  there is no derived zone field; model-level and column-level text agree. Confirmed round 2.
- Lower-severity note, also applied: `competition_registry.sort_order` no longer asserts
  uniqueness within a `display_group`. That is true of today's data but pinned by no test, and
  an unenforced invariant in a description is the rot this programme is removing.
- The four replaced "partition key" claims check out: no dbt model declares `partition_by` or
  `cluster_by`, so `league_code` is a discriminator, matching `CLAUDE.md` and the `league_code`
  docs block.
- `mart_competition_index`'s stated composition matches its five `ref()` calls; `mart_roster`'s
  "no per-club stat columns" matches its select list; `competition_registry.tier` non-empty
  exactly when `domestic_league` is true and is pinned by `test_registry_seed_projection.py`.
- The coverage paragraph dropped from `mart_team_profile` really is documented at source on
  those columns in `int_team_season.yml`, so the deletion de-duplicates rather than loses it.
- Both new `is_featured_season` descriptions match the `row_number()` logic in the two models.
- Every `{{ doc() }}` reference still resolves against `shared_columns.md`.

## escalations
(none)
