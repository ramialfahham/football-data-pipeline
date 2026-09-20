# Task contract — #109 step 3, MR C: every listed column described, and the rule that keeps it so

objective: >
  Every column listed in a model `.yml` under `dbt_project/models` carries a description that names
  its class (engineering_standards.md §3.1) and reads for a stranger (§2): the 359 blank ones get a
  reference to an existing block, a new shared block, or inline prose. Then
  `scripts/check_description_hygiene.py` gains the rule §3.5 names — a listed column with no
  description is a finding — with its tests, and §3.5 says the mechanism is in place. Descriptions
  and the gate only: no model SQL, no column added or removed, no number on the site moves.

refs: >
  #109, "Step 3 — the mechanisms and the sweep", the MR C line, expanded in chat 2026-09-19 and
  written to the issue. The rules: §2 (who a description is for, what it contains, the two bans,
  the form — one block per shared name, referenced never restated; 1,024 rendered chars per
  column) and §3.1 (the four classes) of `dbt_project/docs/engineering_standards.md`. Measured on
  `main` at `f0490c5a`: 359 blank listed columns, 116 names, 75 models, in 15 yml files;
  `league_code` is 49 of them and has two existing blocks; 30 repeated names have no inline text
  anywhere; 18 repeated names have inline text in other models.

scope_paths:
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/domestic_league/matchday/int_matchday.yml
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
  - dbt_project/models/4_intermediate/world_championship/wc/int_wc.yml
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/5_marts/world_championship/world_championship.yml
  - dbt_project/models/docs/shared_columns.md
  - scripts/check_description_hygiene.py
  - tests/test_description_hygiene.py
  - dbt_project/docs/engineering_standards.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/active_work.md
  - docs/tracker/gitlab_snapshot.md

impact_map: >
  writers: none — no model SQL or seed changes; yml descriptions and docs blocks only, plus the
  gate script and its tests. Under `persist_docs`, a description change is `state:modified`, so
  `data:build:mr` rebuilds every touched model and everything downstream of it into
  `ci_mr<IID>_*`, once per pipeline (this MR touches most of the warehouse's yml, so most of it).
  downstream: no column or value changes anywhere; the only consumers of a description are
  BigQuery's column metadata, the dbt docs page and `catalog.json` (§2 "Who reads these").
  layer_rules: none touched. deploy_order: nothing to sequence; the nightly pushes the new
  descriptions with its next build. blast_radius: none on data. On the gate surface:
  `check_description_hygiene.py` runs in `validate:governance` and in the stop gate's FAST_GATES,
  so the new column rule fires on every MR and every turn end from the moment it lands — which
  is why it lands last in the branch, after the tree is at zero blanks.

decisions_taken: >
  §2 and §3.1 applied as written. Three forms, chosen per name from the SQL: (1) `league_code`
  references one of its two existing blocks per site — `league_code` where the value is the
  competition the row belongs to, `league_code_ingest_provenance` where it is the pull that
  surfaced a row of a global entity (the same choice the 33 already-referenced sites made);
  (2) a NEW shared block in `shared_columns.md` for a repeated name only where its meaning is one
  thing at every site — read first — and where every existing inline site of that name converts
  to the reference in the same MR, because the hygiene gate forbids restating a block; (3) inline
  prose everywhere else. A `not_null` that a "NULL unless / when …" sentence contradicts comes
  off the column; no other test moves. The block list with the sites each reaches and the
  `league_code` split go on the MR head.

  The gate: a column-coverage check beside `_object_coverage` in `check_description_hygiene.py`
  — every entry under a model's `columns:` has a non-empty description, a `{{ doc() }}` reference
  counting as the existing walk resolves it; `MIN_LISTED_COLUMNS` as an anti-vacuous floor (the
  `MIN_DESCRIPTIONS` pattern); findings name model and column. No new mechanism: the script, its
  wiring in `validate:governance` and the stop gate, and its test file all exist; this is one
  more rule in them. No recurring cost: the check is offline, well under a second.

decisions_reserved:
  - none: the plan on #109 names this MR; the block-or-inline choice per name is decided from the
    SQL by the widest-call-site rule and listed on the MR head for his check; his merge is the
    ruling on any sentence.

done_when:
  - `python scripts/check_description_hygiene.py` exits 1 on `main` (359 column findings once the rule exists) and 0 on the branch.
  - `python -m pytest tests/test_description_hygiene.py -q` green; a synthetic blank column red, text green, a `{{ doc() }}` reference green, below `MIN_LISTED_COLUMNS` red.
  - Mutation: one description blanked in a yml → the script exits 1 naming model and column; restored → 0.
  - `python scripts/declare_missing_columns.py --wire-shared-docs --dry-run`: nothing to wire; withheld only `league_code` (its two blocks, by design).
  - `.venv/Scripts/dbt.exe parse` green with the scratchpad profile; no rendered description over 1,024 characters (the script measures it).
  - `data:build:mr` green.

amendments: (none)
