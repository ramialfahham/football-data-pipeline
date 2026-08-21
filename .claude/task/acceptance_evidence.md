# Acceptance evidence — UDF calls read as missing tables (#84 follow-up)

No `acceptance_criteria:` block is required: no `site_v2/src/` path is in scope. This records the
`done_when` evidence, read from OUTPUT rather than exit codes (#904).

criteria_demonstrated:

  - **The defect is real and was proved before being fixed.** `marts.mart_fixture_index` calls
    `dbt_analytics.url_fixture_slug`. `bq ls --routines` shows three routines exist
    (`url_fixture_slug`, `url_entity_slug`, `url_kebab`), and a dry-run against the view returns
    `Query successfully validated ... will process 1558728 bytes`. It was never broken.

  - **The whole CLASS was measured, not just the instance.** Across every orphan view body, 183
    extracted referents are not tables: 182 genuinely absent per-competition raw tables, and
    exactly 1 routine. No `INFORMATION_SCHEMA` reference and no other routine call exists in the
    set, so routines were the entire false-positive class.

  - **Routines can never become droppable.** `find_orphans()` iterates the warehouse map, so
    folding routines into it to make `resolves()` work would select every UDF for deletion. They
    are held in a separate set, and `test_a_routine_is_never_returned_as_an_orphan` pins it.

  - **Every guard was mutation-tested, old and new, and each was seen RED:**

    ```
    mutation                                             verdict   caught by
    manifest floor removed                               RED       test_empty_manifest_aborts..., test_manifest_just_below_the_floor_aborts
    __dbt_tmp skip removed                               RED       test_dbt_tmp_relations_are_never_selected
    raw operational exclusion removed                    RED       test_raw_operational_tables_are_never_selected
    dry-run ignored (drops without --confirm)            RED       test_dry_run_is_the_default_and_deletes_nothing
    resolution made one-level instead of transitive      RED       test_brokenness_is_transitive, test_a_view_calling_a_udf_is_live_not_broken, +1
    dataset allowlist widened                            RED       test_only_allowed_datasets_are_ever_listed, test_list_routines_reads_every_allowed_dataset...
    snapshot keyed on config.schema                      RED       test_a_snapshot_is_keyed_on_target_schema_not_schema, +1
    routine recognition removed (the defect itself)      RED       test_a_view_calling_a_udf_is_live_not_broken, test_classify_passes_routines_through
    classify() stops passing routines through            RED       test_classify_passes_routines_through
    list_routines() returns nothing                      RED       test_list_routines_reads_every_allowed_dataset_and_nothing_else
    main() stops fetching/threading routines (WIRING)    RED       test_main_does_not_drop_a_udf_calling_view_in_phase_broken
    manifest sources ignored                             RED       test_declared_sources_protect_raw_tables
    12/12 mutations caught. Script restored byte-for-byte.
    ```

  - **The WIRING mutation was added because a reviewer found it, and it was STILL GREEN first.**
    platform-reviewer FAILed round 1 on this: `classify()` and `list_routines()` were each tested
    in isolation, but nothing drove `main()` with a populated routine set, so reverting the two
    lines in `main()` that fetch and thread routines left the entire suite green. I did not take
    that on trust — I added the mutation and ran it:

    ```
    main() stops fetching/threading routines   STILL GREEN     <- before the new test
    ...
    main() stops fetching/threading routines   RED             <- after it
    ```

    That is the finding proved and then closed. It matters because the production
    misclassification happened in `main()`, the thing the operator actually runs, not in a unit
    under test. `test_main_does_not_drop_a_udf_calling_view_in_phase_broken` asserts the
    consequence rather than the call: `--phase broken --confirm` deletes the genuinely broken view
    and leaves the UDF-calling one alive.

    ⚠ The first run of this pass reported **10/11 with one `SNIPPET NOT FOUND`**: adding the
    `routines` parameter changed the line the transitivity mutation targeted, so that guard went
    unverified. The harness asserts it found its snippet rather than scoring a miss as a pass, so
    the gap was visible. Fixed and re-run to 11/11. A mutation harness that silently matches
    nothing is the same false-green shape as a bulk-edit script that matches nothing.

  - **Two of the new tests guard against being vacuous from the inside.**
    `test_a_view_calling_a_udf_is_live_not_broken` first asserts the OLD wrong answer with an empty
    routine set, then the right one with routines. `test_classify_passes_routines_through` does the
    same. If the fix were a blanket "everything resolves", those first assertions would fail.

  - **`test_a_udf_reference_does_not_rescue_a_genuinely_broken_view`** proves recognising routines
    did not turn `resolves()` into a rubber stamp: a view referencing both a missing table and a
    real UDF is still BROKEN.

  - **Run dry against production, the classification moved exactly as predicted:**

    ```
    Manifest expects 117 relation(s) across staging, core, intermediate, marts, dbt_analytics, raw.
    Warehouse holds 432 relation(s) in those datasets.
    -> broken:     249   (was 250)
    -> live-views:  27   (was 26)
    -> tables:      34   (unchanged)
    310 orphan relation(s) total.
    DRY RUN: nothing was changed.
    ```

    `marts.mart_fixture_index` is now in `live-views` and absent from `broken`, confirmed by
    parsing the output rather than by eye. The total is unchanged, so nothing was gained or lost
    from the orphan set — one member moved phase, which is the whole intent.

  - **Nothing was dropped, at any point.** The phase-1 run was stopped by the CPO before execution
    and has never been run. `bq rm` remains denied by `.claude/settings.json`.

  - **`ruff check . --config .ruff-ci.toml` — `All checks passed!`**
