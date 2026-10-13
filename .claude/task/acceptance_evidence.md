# Verification — merge request build: rebuild a changed seed even when it is over 1 MB

- **The defect, from the MLS line-up merge request's data:build:mr log:** "Found a seed
  (football_data_pipeline.fixture_lineup_corrections) >1MB in size at the same path, dbt cannot
  tell if it has changed: assuming they are the same", then "The selection criterion
  'state:modified+' does not match any nodes"; assert_lineup_researched_matches_hold then read the
  branch's seed against prod's base_apif__lineups and returned 126 rows.
- **Red first:** the new test_the_mr_build_rebuilds_every_changed_seed failed on main's
  .gitlab-ci.yml ("data:build:mr no longer derives CHANGED_SEEDS exactly once"), and passes on the
  branch: tests/test_ci_data_job_invariants.py 8 passed.
- **The two CI lines, executed in bash from the parsed YAML:** with the MLS branch's merge base
  they yield `path:seeds/fixture_lineup_corrections.csv+`; with the base unset the job stops, exit
  1 ("parameter null or not set"); with a base not in history it stops, exit 1 ("bad object");
  with no changed seed the selection is empty.
- **The derivation on real history:** `dbt ls --select
  path:seeds/fixture_lineup_corrections.csv+` resolves that to the seed and 14 models, from
  base_apif__lineups to the player marts. A merge request changing no seed yields an empty string,
  so its selection is state:modified+ alone, as before.
- **Parsed YAML:** data:build:mr's script holds the derivation before the single `dbt build`, which
  keeps --defer --favor-state --state /tmp/main-state --target "$DBT_CI_TARGET".
- **Local gates:** the tier-1 gates pass; pytest 1,540 passed, 2 skipped.
- **Cost:** in #214: dry runs of 11 of the 14 models read 2.4 GB; the rebuild is estimated at
  4-5 GB per pipeline of a merge request that changes the line-up seed, nothing on a schedule.
