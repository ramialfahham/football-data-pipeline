# Acceptance evidence — raw appends and never deletes (#75)

Not a `site_v2/` task, so the acceptance-criteria gate does not apply. This file exists because the
contract's `done_when` requires every rewritten test to be seen RED before it ships. A green test
that was never seen red is decoration, and this repo has shipped three of those (#63).

## criteria_demonstrated:

### 1. The new guards FAIL against the pre-change code

Method: `git worktree add --detach <scratch> gitlab/main` (the code with all three deletes still
present), the two new test files copied in, pytest run there. The working tree was never touched,
so there was no restore step to get wrong.

    8 failed, 22 passed

Of those 8, **five fail on the assertion itself**, naming the exact DELETE the ruling removes:

    test_a_clean_run_appends_and_issues_no_dml[transfers]
    E  Left contains one more item: 'delete from `...RAW_APIF_TRANSFERS` where league_code = @lc
                                     and ingested_at < @before'
    test_a_clean_run_appends_and_issues_no_dml[standings]
    E  ... `...RAW_APIF_STANDINGS` ...
    test_a_clean_run_appends_and_issues_no_dml[teams]
    E  ... `...RAW_APIF_TEAMS` ...

    test_the_players_loader_appends_and_deletes_nothing
    E  AssertionError: the players loader issued DML against raw: ["delete from
       `...RAW_APIF_PLAYERS` where league_code = @lc and ingested_at < @before and concat(
       ifnull(json_value(payload, '$.response[0].team_id'), 'x'), '-', ... ) in unnest(@keys)"]

    test_no_loader_module_carries_a_delete_helper
    E  Left contains 6 more items, first extra item:
       'loads.batch_fixtures._delete_fixtures'

### 2. The fixture-details guard, proven separately and honestly

The remaining 3 of the 8 failed on the OLD function signature (`_fetch_and_persist_batch` took a
fourth `retry_ids` argument), which is a `TypeError` and proves nothing about the guard. Stated
rather than counted as a pass.

Re-run in the worktree with the call adapted to the old 4-arg signature, so the only thing left to
fail on is the assertion:

    TestFixtureDetailsRetryKeepsBothVersions — 1 failed, 2 passed
    E  Left contains one more item:
       "DELETE FROM `p.raw.FIXTURE_DETAILS`
        WHERE CAST(JSON_VALUE(payload, '$.fixture.id') AS INT64) IN (111)
          AND league_code = 'CIT'"

That statement is the one that destroyed the penalty shootout on fixture 1564795.

The 2 that passed there are correct and worth naming: `test_incomplete_fetch_is_discarded_whole`
(the #896 guard already existed on main and is unchanged by this MR) and
`test_the_fixture_write_is_an_append` (WRITE_APPEND was already correct; the test pins that it
stays that way, since a flip to WRITE_TRUNCATE would erase the table while issuing no DELETE and
the no-DML tests would stay green).

### 3. Full suite, on this branch

    813 passed, 1 skipped, 14 subtests passed in 495.16s

### 4. The test-count change, reconciled by measurement rather than assertion

    gitlab/main (temp worktree):  818 collected
    this branch:                  814 collected

Net -4, and it accounts exactly:

  `tests/test_raw_merge_on_write.py` 18 -> 13 (-5)
    removed, subject no longer exists:
      test_the_delete_is_scoped_to_this_league          (x3) — no delete to scope
      test_the_delete_boundary_is_the_write_s_own_stamp (x3) — no boundary to get wrong
      test_a_failed_delete_is_reported_and_does_not_raise (x3) — no delete to fail
    re-pointed, NOT dropped:
      test_a_failed_delete_still_extends_team_ids -> test_an_incomplete_fetch_still_extends_team_ids
        The dead case was the failing DELETE; the live guarantee is that the id extension runs on a
        discarded snapshot, which `teams.py` states is deliberate. Dropping the test outright would
        have retired a guarantee along with a dead case.
      test_only_the_three_whole_league_loaders_merge -> test_coaches_was_never_a_merge_loader...
      test_the_merge_helper_is_imported_by_exactly_the_converted_loaders
        -> test_no_loader_module_carries_a_delete_helper (inverted, and widened to all three names
           plus the `bigquery` module)
    added:
      test_every_raw_write_is_an_append (x3)   — the append half of "keeps both versions"
      test_the_players_loader_appends_and_deletes_nothing

  `tests/test_incomplete_fetch_no_supersede.py` 16 -> 17 (+1)
      test_the_fixture_write_is_an_append added.

  `tests/test_squad_players_rows.py` 13 -> 13 — no test removed, only the delete assertions inside
  `test_one_row_per_team_season` and the two `_delete_superseded_player_rows` monkeypatches.

### 5. Lint

    ruff --config .ruff-ci.toml ingestion tests  ->  All checks passed!

### 6. No delete left in ingestion

    grep -rni "delete from|delete_superseded|_delete_fixtures" ingestion/
    -> 3 hits, all of them the REMOVED-2026-08-17 tombstone comments that say why it is not
       coming back. No executable DML.
