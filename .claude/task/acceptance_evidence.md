# Acceptance evidence — #190 How step 3, plain catalogue descriptions and lower_is_better gone

Read from the files on disk, the diff against gitlab/main, the parsed manifest and exit codes read
bare. No warehouse query was run.

criteria_demonstrated:
  - EVERY DESCRIPTION IS ONE PLAIN SENTENCE, HELD BY A CHECK. All 89 rows of metric_catalogue.csv
    carry a new description, and description is the only column whose values change. Longest 149
    characters, shortest 22, mean 64; on main the longest was 997 and 12 were over 200. Each
    follows engineering_standards.md section 2's forms (a count, "Average number of ... per
    match", "... per 90 minutes played", "... as a share of ..."), and twins read alike where
    their formulas match (passes accuracy, duels won, key passes, goals per 90). The check in
    scripts/sync_metric_docs_blocks.py refuses a description over 200 characters, with a
    snake_case name (any case, digits included) or with a listed word:
    test_a_description_that_breaks_the_standard_is_refused passes for 13 cases, one per listed
    word among them; test_a_description_within_the_standard_is_accepted passes for a
    200-character text and for "annulled", "rapid" and a hyphenated term, so a listed word is
    refused only as a whole word; `sync_metric_docs_blocks.py --check` on the real catalogue
    exits 0. The goalkeeper rows say "in goal" for the goals conceded they count.
  - LOWER_IS_BETTER IS GONE. The column is dropped from metric_catalogue.csv and its entry from
    seeds/schema.yml; assert_metric_direction_lower_is_better_agree is deleted and its companion's
    pointer removed. scripts/export_metric_definitions_json.py derives the legacy JSON flag from
    direction, and tests/test_metric_bindings.py regenerates the retired site's file and finds it
    byte-identical. `git grep lower_is_better` outside site/ finds only that export's output key
    and a comment in site_v2/src/lib/metricRows.ts that says the page never reads it.
  - THE CPO'S DOCUMENTS POINT TO DIRECTION. CLAUDE.md, north_star.md and metrics_display.md lines
    249-253 changed in !243, merged. Here: ui_design_brief.md line 52, wireframes/00_overview.md
    line 98, wireframes/01_fixture_page.md line 152 and wireframes/02_team_profile.md line 119
    name `direction` where they named `lower_is_better`; nothing else in them changes.
  - CHECKS. `dbt parse` 0; the offline gates and check_description_hygiene 0;
    `sync_metric_docs_blocks.py --check` and `generate_metric_sql.py --check` 0; ruff with
    `.ruff-ci.toml` "All checks passed!"; pytest "1367 passed, 2 skipped".
