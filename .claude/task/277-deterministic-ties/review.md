# Review — claude/277-deterministic-ties — 2026-11-09

diff_sha256: 6231f1a98ed170b0a28baad0d2ff9afa3f2c7c922e3e08b4832f8dda53d5c65d

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every file in the diff is inside scope_paths; the three amendments name their authority (approved in chat, 2026-11-09, for the macro and the two doc lines; acceptance criteria 2 and 5 for the two rule tests).
- The ban regex matches the two ruled names only, any_value and approx_quantiles.
- decisions_taken names the one_value macro as the one new mechanism and agrees with amendment 1; no recurring cost.
- The rules taken match the ruled text: standings by latest load then section order, position by most frequent then most recent match then code, board order ending season desc then league_code, exact percentile_disc quartiles and bignumeric means, reached tie by opponent else latest.
- The round-names fault stays reserved for #278; approved_design is none and no site or export file changes.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Every one_value site sits on a group whose key fixes the value, so the guard cannot raise on valid data; each guarded model ran read-only against prod without raising.
- assert_player_position_follows_the_rule recomputes the position rule at its three pick sites, and assert_cup_status_follows_the_reached_tie recomputes the reached and previous ties; both return 0 rows on the new models and fail on main's picks.
- base_apif__standings orders by raw_ingested_at desc, standing_section_order asc, a total order within its partition.
- layering.md no longer names any_value; engineering_standards.md §1.1 owns the ban.
- No hardcoded competition identifier, no seed, dbt_project.yml or export change.

## platform-reviewer
VERDICT: PASS
risks_checked:
- test_main_fails_on_a_planted_banned_aggregate plants a banned call under a patched DBT_PROJECT and asserts main() == 1, so dropping the check's registration fails a test.
- test_a_banned_aggregate_fails is parametrized over both banned names in models, tests and macros.
- test_one_value_macro pins the guard's shape and keeps the error message free of quotes; jinja2 comes with the pinned dbt-core.
- The ban runs in validate:governance and the stop gate, exits 1 on a hit, and is read-only.
- No workflow, requirements or hook file changes.

## escalations
(none)
