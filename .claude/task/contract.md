# Task contract — the prod build's staging stage runs no test that reads a later layer

objective: >
  The prod build (data:build:main) builds in stages: `dbt build --selector staging`, then
  `dbt build --selector downstream` (base through marts), then every singular test. dbt selects a
  test for a stage when any of its parents is in it, so a test that reads a staging model AND a model
  built later runs in the staging stage, against the previous build's later-layer table. The player
  side of #185 made assert_base_player_stats_cleaned read stg_apif__fixture_players (for the
  provider's own values) as well as base_apif__fixture_players, and the first prod build after that
  merge failed in the staging stage on the base table's old column names, before base was rebuilt.
  The staging selector excludes every test with a parent in 2_base, 3_core, 4_intermediate or
  5_marts; such a test runs in the downstream stage, after its parents are built, and still blocks
  the writes after it.

refs: >
  #185, How step 3 (the player-side merge). The failing job: data:build:main of the merge's main
  pipeline, "Database Error in test assert_base_player_stats_cleaned: Name minutes not found inside
  p", in the `dbt build --selector staging --target prod` step. Measured offline with `dbt ls` on
  main: the staging selector selects 62 tests today; excluding the four later-layer paths drops
  exactly one, assert_base_player_stats_cleaned, which `dbt ls --selector downstream` selects. The
  two override checks that read staging and seeds (assert_country_name_overrides_still_needed,
  assert_league_name_overrides_are_corrections) stay in the staging stage.

scope_paths:
  - dbt_project/selectors.yml
  - tests/test_ci_data_job_invariants.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  writers: dbt_project/selectors.yml is read by `dbt build --selector` and `dbt ls --selector`
  only. readers: .gitlab-ci.yml data:build:main (`--selector staging`, then `--selector
  downstream`); `grep -rn -- "--selector" .gitlab-ci.yml deploy scripts` finds no other stage
  runner; the nightly (deploy/nightly/entrypoint.sh) runs `dbt build --target prod` with no
  selector, and data:build:mr selects `state:modified+`, so neither changes. blast_radius: the
  staging stage of the prod build drops one test (assert_base_player_stats_cleaned), which the
  downstream stage already runs after base is built; no model, test or value changes. deploy_order:
  merging this file is a dbt compile input (`dbt_project/*.yml`), so the merge's data:build:main
  rebuilds prod in stages with the player-side code; that build performs the one-time full
  re-merge of fct_fixture_player_stats the player-side merge's own prod build never reached.

decisions_taken: >
  The CPO approved this fix MR in chat after the player-side merge's prod build failed, on the
  recommendation to fix the stage selection and to check offline that every test leaving the
  staging stage still runs in a later stage. Builder reading: the rule covers every layer the
  downstream stage builds (base, core, intermediate, marts), not only base, since a test reading
  any of them fails or reads last night's table the same way.

decisions_reserved:
  - none

done_when:
  - "`dbt ls --selector staging --resource-type test` selects every test it selects on main except
    assert_base_player_stats_cleaned, and `dbt ls --selector downstream --resource-type test` still
    selects that test."
  - A test in tests/test_ci_data_job_invariants.py fails when the staging selector stops excluding a
    path the downstream selector builds; it is watched red against main's selectors.yml.
  - dbt parse, the offline governance gates and `pytest tests/` pass.
  - review.md binds the staged hash with every routed verdict PASS.
  - After the merge, data:build:main is green, with the full re-merge of fct_fixture_player_stats
    in its log.

amendments:
  - + tests/test_ci_data_job_invariants.py — authority: the CPO's go for this fix (decisions_taken)
    and the working agreement's §7 (every pipeline output is covered by an automated test); content:
    a test pinning the stage rule, since only a merge's prod build exercises the selectors and a
    revert would otherwise stay green until prod fails.
