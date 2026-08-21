# Acceptance evidence — cleanup script for orphaned warehouse relations (#84)

No `acceptance_criteria:` block is required here: the contract touches no `site_v2/src/` path. This
records the `done_when` evidence instead, read from OUTPUT rather than exit codes (#904).

criteria_demonstrated:

  - **The tests were seen RED before being trusted.** Seven mutations, one per guard, each applied
    to the script in isolation with the original restored byte-for-byte afterwards. All seven were
    caught. A guard nothing catches would have shown as STILL GREEN:

    ```
    mutation                                             verdict   caught by
    manifest floor removed                               RED       test_empty_manifest_aborts_instead_of_orphaning_everything,
                                                                   test_manifest_just_below_the_floor_aborts
    __dbt_tmp skip removed                               RED       test_dbt_tmp_relations_are_never_selected
    raw operational exclusion removed                    RED       test_raw_operational_tables_are_never_selected
    dry-run ignored (drops without --confirm)            RED       test_dry_run_is_the_default_and_deletes_nothing
    resolution made one-level instead of transitive      RED       test_brokenness_is_transitive
    dataset allowlist widened                            RED       test_only_allowed_datasets_are_ever_listed
    manifest sources ignored                             RED       test_declared_sources_protect_raw_tables
    7/7 mutations caught. Script restored byte-for-byte.
    ```

  - **Dry-run is the default and drops nothing.** `test_dry_run_is_the_default_and_deletes_nothing`
    asserts `delete_table` is never called without `--confirm`, and the mutation that ignores the
    flag turns it red.

  - **The manifest floor aborts rather than orphaning production.** Driven, not read: an empty
    manifest, a manifest one below the floor, a missing file and a corrupt file all return exit 2
    with `client.deleted == []`. `test_manifest_at_the_floor_is_accepted` pins the boundary from the
    other side so the floor cannot quietly become a moat.

  - **A live model can never be selected.** `test_a_model_in_the_manifest_is_never_an_orphan`,
    `test_a_node_with_no_custom_schema_maps_to_dbt_analytics` (base + seeds ride `target.schema`),
    `test_declared_sources_protect_raw_tables`, `test_ephemeral_models_are_not_expected_to_exist`.

  - **The dataset allowlist is a fence, not a comment.** `test_only_allowed_datasets_are_ever_listed`
    asserts the client is asked for exactly `ALLOWED_DATASETS` and never for `raw_archive`,
    `dbt_scratch`, `dev_scratch`, `ci_marts` or `snapshots`.

  - **The three phases are disjoint and cover every orphan.**
    `test_phases_are_disjoint_and_cover_every_orphan` asserts both directions plus `select(.., "all")`.

  - **Run against real production, dry, and it agrees with the independent investigation.** The
    investigation reached 310 / 250 / 26 / 34 through separate throwaway scripts. The committed
    script reproduces every number from the manifest, with no name hardcoded anywhere:

    ```
    $ python scripts/cleanup_orphan_relations.py
    Manifest expects 117 relation(s) across staging, core, intermediate, marts, dbt_analytics, raw.
    Warehouse holds 432 relation(s) in those datasets.
    -> broken:     250 - BROKEN views: already error on any query, so nothing can be reading them
    -> live-views:  26 - views that STILL RETURN DATA: retired SQL still answering queries
    -> tables:      34 - orphan TABLES: these hold bytes, unlike the views
    310 orphan relation(s) total; phase 'all' selects 310.
    DRY RUN: nothing was changed. Pass --confirm to drop these 310.
    ```

    No `WARNING: expected relation(s) are NOT in the warehouse` line appeared, so every relation the
    manifest expects exists. The pipeline itself is healthy.

  - **Nothing was dropped.** Every run in this task was a dry run. `bq rm` is independently blocked
    by `.claude/settings.json`'s deny list, and running with `--confirm` is reserved to the CPO in
    the contract.

  - **`ruff check . --config .ruff-ci.toml` — `All checks passed!`** (the exact CI invocation).

  - **The script's output is ASCII-only**, verified by scanning every character. The first draft
    printed em dashes, which mojibake to `?` on a cp1252 Windows console: a report the CPO cannot
    read on his own machine is a defect, not a style preference.
