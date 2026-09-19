# Task contract — #109 step 3, MR B: range tests, the key graph, the sweep script

objective: >
  Every rate column carries its range backstop (engineering_standards.md §3.2), every foreign-key
  `_sk` column carries `relationships` to its parent or a declared soft link (§3.1), the one model
  with no test gets one, and `scripts/check_relationships_coverage.py` keeps the key graph covered
  (§3.5). Tests and yml only: no model SQL changes, no column added or removed, no number on the
  site moves.

refs: >
  #109, "Step 3 — the mechanisms and the sweep", the MR B line, expanded in chat 2026-09-19 and
  written to the issue with the soft-link decision. The rules are §3.1, §3.2, §3.5 of
  `dbt_project/docs/engineering_standards.md` (!201). Measured on `main` at `d8a4ab3c`, read-only:
  156 rate columns without a range test (3 signed differences get none); 80 foreign-key `_sk`
  columns without `relationships`, of which 76 have zero orphans on prod and 4 (two leaf core
  tables) have 7,502–134,025; 153 range conditions probed on prod with zero violations; 1,074 tests
  parsed today.

scope_paths:
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
  - dbt_project/models/4_intermediate/shared/int_player_season__team.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/4_intermediate/shared/int_team_profile.yml
  - dbt_project/models/4_intermediate/shared/team/int_team_market_value.yml
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/5_marts/shared/shared.yml
  - scripts/check_relationships_coverage.py
  - tests/test_check_relationships_coverage.py
  - dbt_project/docs/engineering_standards.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/active_work.md
  - docs/tracker/gitlab_snapshot.md

impact_map: >
  writers: none — no model SQL or seed changes; the 15 yml files gain tests and, on four columns,
  a `meta.soft_link` key. dbt's `state:modified+` treats a test change as a change to the tested
  node, so `data:build:mr` rebuilds the 37 touched models and everything downstream of them into
  `ci_mr<IID>_*`, once per pipeline.
  downstream: no column changes, so no downstream model's SQL or output changes; the only effect is
  new tests that can turn a build red. Every one was measured on prod first (2026-09-19): the 76
  `relationships` have zero orphans (one 286 MB query joining each child to its parent); the 153
  range conditions have zero violating rows (one 44 MB query). A red on the MR target is a real
  regression, not a stale count.
  layer_rules: none touched — `check_layer_contract.py` reads materialisation and the staging tree;
  tests are not in its scope.
  deploy_order: nothing to sequence — the nightly picks the tests up at the next `dbt build`; a
  test cannot break a table.
  blast_radius: none on data. On the test surface: +153 range assertions (as ~40 yml blocks, the
  intermediate models combining columns in one `expression_is_true` as they already do, the marts
  one per column as they already do), +76 `relationships` at `error`, +3 tests on
  `int_team__market_value_latest`, 4 soft links declared.

decisions_taken: >
  §3.2 applied: a share is `null or between 0 and 1`, a per-match / per-90 count `null or >= 0`;
  `shots_on_goal_difference_per_match` (3 surfaces) is signed and gets none, as
  `int_team_season.yml`'s own comment already says. Year-over-year copies in `int_team_profile__yoy`
  and `mart_team_profile` take the bounds `int_team_profile.yml` already fixed for the same
  columns: structural ratios [0,1], the four provider-subset ratios >= 0 only (its comment says why:
  a single provider game with numerator > denominator is a data reality, not a model bug).

  §3.1 applied: `relationships` at `error` on the 76 foreign keys with zero orphans — a dangling
  key is a wrong page (§3.3). The parent is resolved by name: a `3_core` column with `unique` is a
  core key; a role prefix (`opponent_`, `home_`, `away_`, `upcoming_`, `leg_`, `biggest_margin_*`,
  `most_goals_*`) points at the entity; `team_in_sk` / `team_out_sk` are `team_sk`; an entity
  prefix (`team_season_sk`, `player_season_sk`, `player_club_season_sk`) is a composite key of its
  own, and a `_sk` that is `unique` in its model or in its `unique_combination_of_columns` and has
  no core parent is that model's own key.

  THE DECLARED SOFT LINK — decided with the plan (the CPO's approval of the MR B plan in chat,
  2026-09-19, recorded on #109): the four foreign keys that name clubs and players outside the
  tracked competitions by design (`fct_transfer.team_in_sk` / `.team_out_sk` / `.player_sk`,
  `dim_coach_team_mapping.team_sk`; 134,025 / 101,761 / 111,925 / 7,502 orphan rows on prod; both
  tables are leaves nothing downstream reads, and both descriptions already say the link is
  soft) carry `meta: soft_link: "<parent> — <why>"` instead of a `relationships` test. The
  sweep script accepts a declared soft link and prints it in its census. The alternative, a
  `relationships` at `warn`, was put with the plan and not taken: four warnings a night on rows
  that never change.

  NEW MECHANISM, declared for the CTO threshold: `scripts/check_relationships_coverage.py` is a
  new offline governance script of the `check_*.py` class, with its pytest. Its own
  `validate:governance` line is MR D's (a governance MR on `.gitlab-ci.yml`); until then the
  rule is enforced by `tests/test_check_relationships_coverage.py`, whose last test runs the gate
  on the real tree inside `test:python` on every merge request — the shape of
  `test_materialisation_policy.py` and `test_persist_docs_policy.py`. The `meta.soft_link` key is a
  new yml convention read only by that script, and `engineering_standards.md` §3.1 / §3.5 say so.
  No recurring cost beyond the tests themselves: 173 more generic tests in the nightly (1,074 →
  1,247), each a small query over columns of a table the build already scanned.

  `int_team__market_value_latest.team_sk`: `not_null`, `unique`, `relationships` to `dim_team` —
  one row per team is its stated grain; the model is empty today (its description says so), so
  the tests pass vacuously until the snapshot fact is fed.

decisions_reserved:
  - none: the plan on #109 names the ranges, the parents, the four soft links and the script's
    rule; the MR head carries the counts and his merge is the ruling.

done_when:
  - `python scripts/check_relationships_coverage.py` exits 1 on `main` (80 findings) and 0 on the branch, printing the census with 4 soft links.
  - `python -m pytest tests/test_check_relationships_coverage.py -q` green; each rule shown red once on a synthetic tree (foreign key without `relationships`; unresolved `_sk` that is not its model's own key; below the floor), green with `relationships` and green with a soft link.
  - Mutation: one `relationships` block removed from a yml → the script exits 1 naming the column; restored → 0.
  - `.venv/Scripts/dbt.exe parse` green with the scratchpad profile; `dbt ls --resource-type test` counts 1,074 + 153 range blocks' worth (reported as the exact number in the MR head) + 76 + 3.
  - The re-count script shows 3 rate columns without a range test (the signed differences) and 0 foreign keys without `relationships` or a soft link.
  - `data:build:mr` green: every new test PASS against the MR's own build.

amendments:
  - 2026-09-19: + dbt_project/docs/engineering_standards.md — authority: working_agreement.md §11,
    "a rule → the document that owns that rule, edited in the same MR"; the soft link is an
    exception to §3.1's "every foreign key carries relationships" and the plan approval put it
    on #109 (the requirement) but not in the rule's own document (scope-auditor, round 1).
    Content: §3.1 and §3.5 state the declared soft link in a few lines; nothing else moves.
  - 2026-09-19: two round-1 corrections, no scope change. (1) The three player provider-subset
    ratios (`passes_accuracy_player_pct`, `duels_won_player_pct`, `dribbles_success_player_pct`)
    are bounded >= 0 only on `int_player_season_position__metrics` and `mart_player_momentum`,
    not [0,1]: a position or a form window can be one game, and a provider game with numerator
    > denominator is genuine data — the split `int_team_season__metrics_cumulative` already
    makes (analytics-engineer-reviewer). `saves_player_pct` stays [0,1]. (2) The claim "not wired
    into CI" was false the moment the pytest's last test ran the gate on the real tree in
    `test:python`; the contract, the script's docstring and the test's say so now, and the script
    prints its soft links on a red run too, with a test for the mixed case (platform-reviewer).
