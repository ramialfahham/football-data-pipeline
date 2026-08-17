# Acceptance evidence — never record a gap as captured (#75 MR2)

Not a `site_v2/` task, so the acceptance-criteria gate does not apply. This exists because
`done_when` requires each of the four holes to be seen RED before the fix ships.

## criteria_demonstrated:

### 1. All 11 new tests FAIL against `gitlab/main`

Method: `git worktree add --detach <scratch> gitlab/main`, the new test file copied in, pytest run
there. The working tree was never touched.

    11 failed

**FIVE fail on the assertion itself, naming the live defect.** ⚠ This document first said THREE.
`platform-reviewer` traced the loader hunks and pointed out that the two player-entity tests fail on
the assertion too, not on the unpack: they monkeypatch the helper inside the loader's own namespace,
so the pre-fix loader receives the tuple and stores it whole as the payload, and the entry is
recorded. I re-ran them against `gitlab/main` rather than take that on trust:

    test_player_entity_incomplete_is_not_recorded[profiles]
    test_player_entity_incomplete_is_not_recorded[player_teams]
    E  AssertionError: player 7's rate-limited empty payload was recorded ([7, 8]);
       `_existing_player_ids` keys on player_id presence, so that player is never fetched again

Recorded as a correction rather than edited away: understating evidence is the same #904 class as
overstating it, and the number is the whole point of this section.

The other three:

    test_squads_incomplete_team_is_not_recorded
    E  AssertionError: team 10's rate-limited empty squad was recorded ([10, 11]);
       `captured_team_seasons` keys on team_id presence, so that team is now never re-fetched

    test_transfers_with_no_team_ids_writes_nothing
    E  AssertionError: an empty whole-league transfers snapshot was written; it becomes the
       latest row and hides every stored move for that competition.
       wrote=[{'as_json_payload': True, 'append': True, 'league_code': 'BL1'}]

    test_load_json_to_bq_requires_an_explicit_append
    E  AssertionError: `append` has a default again. It must stay required...
       assert False is <class 'inspect._empty'>
        +  where False = <Parameter "append: 'bool' = False">.default

**The remaining six fail on the unpack**, because the three helpers returned a bare list and
`rows, complete = helper(...)` cannot destructure it. Stated rather than counted as assertion
proofs — though the unpack failure IS the defect in this case: the completeness signal did not
exist to reach the caller at all. `platform-reviewer` checked whether they are therefore vacuous
and concluded not: they call the REAL helpers with only `fetch_merged_paged` mocked, so if the
tuple shape were restored with the boolean wrong (say hardcoded `True`), the explicit
`assert complete is False` / `is True` still fires.

### 2. The rule was not widened, only the write withheld

`test_empty_but_clean_response_is_still_complete` (×3) pins the CPO ruling of 2026-08-03: an empty
error-free answer is COMPLETE and is still written. Without it, a "fix" that simply refused every
empty response would satisfy every other test here and silently re-fetch 3,539 historical
team-seasons nightly.

### 3. `append` audit, enumerated not assumed

    grep -rn "load_json_to_bq(" ingestion/ scripts/   ->  11 callers
      9 pass append=True explicitly
      2 omitted it and relied on the False default, BOTH deliberately, both single-current-state
        operational tables: completeness.py:602 (INGEST_COMPLETENESS_SNAPSHOT) and
        fixture_scheduling.py:345 (INGEST_CURSOR)
Both now pass `append=False` explicitly with a comment saying why. Behaviour is unchanged
everywhere; the destructive mode is simply written down at the two call sites that choose it.

### 4. One pre-existing test needed a harness fix, found by RUNNING the suite

`tests/test_player_squads_catchup.py:176` held the repo's only double for
`squads_response_for_team` and still returned a bare list. Left alone it raised "not enough values
to unpack", which the loader's own `except` swallowed into an error string, so the suite went red
for a reason unrelated to the defect. The fake now returns `(rows, True)` — deliberately COMPLETE,
because that test is about a quota cut mid-competition, not a failed fetch, and the two paths must
stay separable. No assertion moved. Recorded as a contract amendment.

### 5. Full suite and lint

    824 passed, 1 skipped, 14 subtests passed in 464.35s
    ruff --config .ruff-ci.toml ingestion tests  ->  All checks passed!

Was 813 passed / 1 skipped before this branch: +11, exactly the new file, no test removed and none
displaced.
