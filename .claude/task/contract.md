# Task contract — TASK 0 part 1 of 2: the 28 meanings + the 4 corrections (VALUES ONLY)

> Written on a CLEAN tree (branch `feat/metric-layer-meaning-gates`, rebuilt off main @ 5308b7a).
> Supersedes the single-commit TASK 0 contract. Same three CPO-ordered steps, now split across TWO
> merges because CI cannot validate a new test and the seed values it depends on in one pull request.
> See [[feedback-metric-catalogue-governance]] [[feedback-no-hacky-solutions]].

objective: >
  Land the metric layer's DATA half: fill the `interpretation` cell on the 28 player rows that are
  blank, and correct `lower_is_better` on the 4 rows that contradict `direction`. No test changes.

  WHY THE SPLIT. The first attempt landed the values and the two new guards together and CI went red
  while everything was correct. The PR-only singular-test step runs
  `dbt test --select test_type:singular --defer --favor-state --state /tmp/main-state`. dbt defers
  every node not in the current selection, and `dbt test` can only ever select TEST nodes, so the
  `metric_catalogue` seed is never selected there and `ref('metric_catalogue')` resolves to the state
  relation — a manifest compiled from MAIN with `--target prod`, i.e. `dbt_analytics.metric_catalogue`
  with the pre-PR values. The new guards were therefore run against main's catalogue and correctly
  reported main's defects. Measured, not inferred: `ci_analytics.metric_catalogue` (this branch's
  seed) has 0 blank-meaning rows; `dbt_analytics.metric_catalogue` has 28, which is exactly the CI
  failure count, and the lockstep guard's `FAIL 4` is exactly the 4 rows this branch corrects.

  Splitting dissolves the problem instead of engineering around it. THIS PR changes values only, so
  no test depends on data that is not yet on main, and it goes green. Once it merges, the main-push
  build runs `dbt seed --target prod` and main's catalogue becomes correct. PART 2 then adds the two
  guards, whose deferred reads now hit an already-correct main, and it goes green too. Both halves
  land, in the CPO's required order, with zero CI changes.

  REJECTED: editing `.github/workflows/ci-data-build.yml` to tag seed-only tests and run them in a
  new non-deferred step. It works and was fully designed and adversarially reviewed, but it edits a
  PROTECTED workflow, introduces a tagging convention whose omission fails silently-green, and then
  needs a further lint script to police that convention — three new moving parts to avoid ordering
  two merges. CPO 2026-07-21 on seeing it: *"I have the feeling that you don't know what you're doing
  and start overcomplicating things again."* The judgement was right. [[feedback-no-hacky-solutions]]

refs: >
  Verified live this session against the repo and against BigQuery — not recalled:
  - `dbt_project/seeds/metric_catalogue.csv` has 78 metric rows; exactly 28 carried a blank
    `interpretation` (all `entity=player`), and exactly 4 rows had `lower_is_better=false` beside
    `direction=lower_better` (`cards_yellow`, `cards_red`, `cards_total`, `shots_on_goal_against`).
    No hidden fifth: every row with `lower_is_better=true` already carried `direction=lower_better`.
  - `direction` is authoritative over `lower_is_better` — already stated in `seeds/schema.yml`
    ("where the two disagree, direction is the v2 authority"), and the CPO decided it in the brief.
  - INERT for the live MVP. `scripts/export_metric_definitions_json.py` composes the 13 live ids in
    `site/match-preview/metric_bindings.csv` with the catalogue; none of the 4 is bound and all 4 are
    `entity=player` while the live match preview is team-only. `metric_definitions.json` regenerates
    byte-identical and `tests/test_metric_bindings.py` passes.
  - `.github/workflows/ci-data-build.yml:132-134` — `dbt seed --target ci` is unconditional on PRs;
    `:136-138` — the non-PR path seeds PROD. `:216-223` is the deferred step that caused the red.
  - The seed content in THIS commit is BYTE-IDENTICAL to what all three reviewers already PASSed on
    the pre-split commit (analytics-engineer verified all 32 changed cells; football-analytics-expert
    FAILed r1 on three wordings, all fixed, then PASSed r2).

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - .claude/active_work.md
  - .claude/task/**

impact_map: >
  writers: `dbt_project/seeds/metric_catalogue.csv` ONLY — seed VALUES, two columns: `interpretation`
    on 28 player rows and `lower_is_better` on 4 player rows. No new column, no new row, no formula
    change, no `direction` change. No dbt model, no test, no export script, no workflow, no `site/`,
    no `site_v2/`.
  downstream — `interpretation`: read by nothing in code today. It is display copy for the v2 pages;
    `scripts/export_site_data.py` does not carry it and `export_metric_definitions_json.py` reads only
    `format` / `lower_is_better` / `label_i18n_key`. Filling 28 blanks moves zero numbers.
  downstream — `lower_is_better`: exactly one consumer, `export_metric_definitions_json.py`, which
    only looks up the 13 bound ids. None of the 4 is bound, so the live JSON is byte-identical.
  downstream — the EXISTING tests: `assert_team_metric_meaning_complete` is team-scoped and every
    team row was already populated, so it passes on both the old and the new seed. Nothing else in
    the singular suite reads a catalogue VALUE that this commit changes. That is precisely why this
    half is green on its own.
  layer_rules: seeds-as-configuration. The seed is the metric SSoT; values are edited here and
    nowhere else.
  deploy_order: THIS PR MERGES FIRST. Its main-push build must complete (running
    `dbt seed --target prod`) BEFORE part 2's CI runs, or part 2 hits the same stale-read red.
  blast_radius: zero row movement, zero number movement, zero live-site movement.

decisions_taken: >
  1. TASK 0 ships as TWO merges rather than one. The CPO's three steps and their required order are
     unchanged; only the commit boundary moves. Values first because the tests depend on the values
     being on main, never the reverse.
  2. `direction` is authoritative; `lower_is_better` is corrected to match on the 4 divergent rows.
     CPO-decided in the session brief. NOT re-asked.
  3. `interpretation` house style follows the existing TEAM rows: `<what it captures> - <plain
     definition>; high|low = <what a notable value signals>`, with any honest volume/style/role caveat
     last in parentheses. No comma inside an unquoted CSV cell; no em dash; no trailing period.
  4. `seeds/schema.yml` prose moves ENTIRELY to part 2. Every line of it names the renamed or the new
     test, so stating it here would publish a claim about tests that do not yet exist.

out_of_scope: >
  - The two guards, the test rename, and the `seeds/schema.yml` prose. All of it is PART 2, held
    ready on the local branch `feat/metric-layer-tests` and pushed once this merges.
  - Any change to `.github/workflows/ci-data-build.yml`. Explicitly abandoned (see objective).
  - Widening `assert_no_uncatalogued_season_metric` (issue #530).
  - Anything in `site/`, `site_v2/`, or any dbt model.
  - Two pre-existing holes found while tracing, LOGGED not fixed: (a)
    `assert_metric_catalogue_unique_by_entity` reads main's seed in the deferred PR step, so a PR
    adding a duplicate metric row would pass it; (b) `load_catalogue` in
    `export_metric_definitions_json.py` keys the catalogue by `metric_id` alone while the grain is
    `(metric_id, entity)`, so a player row overwrites the team row of the same id — 4 ids collide
    today, the 2 that are BOUND agree on all three fields read, and the 2 that differ on
    `label_i18n_key` are never looked up. Neither is introduced here.

decisions_reserved: >
  (none)

done_when:
  - The 28 `interpretation` cells are filled and all 78 rows carry both `direction` and
    `interpretation`.
  - Zero rows where `lower_is_better` and `direction` disagree, in either direction.
  - `site/match-preview/metric_definitions.json` regenerates byte-identical.
  - The data-build job is GREEN.
  - scope-auditor + analytics-engineer + football-analytics-expert PASS.
  - CPO merges; I never merge.

verification: >
  - Re-derive from the CSV: zero blank `direction` or `interpretation`, zero disagreements between
    `lower_is_better` and `direction`, still 78 rows x 14 columns, no comma / em dash / quote in any
    new cell.
  - `python scripts/export_metric_definitions_json.py` then `git diff` on
    `site/match-preview/metric_definitions.json` must be EMPTY. Plus `pytest tests/`.
  - Read the actual CI run and confirm data-build is green, rather than asserting it will be.

amendments: >
  r1 (2026-07-21) — the original single-commit contract authorized the values AND both guards AND
  `seeds/schema.yml` in one PR. That produced a red gate for the reasons in `objective`. This contract
  narrows the commit to values only and moves the rest to part 2. The seed content itself is
  unchanged from the reviewed version; nothing that three reviewers passed has been altered, only
  what ships in which merge.
