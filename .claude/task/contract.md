# Task contract — docs blocks for the repeated shared columns

objective: >
  MR2 of six (description drift; plan and authority in `.claude/task/escalations.log`, 2026-08-20).
  The same columns are documented over and over in independently-drifting wordings: `league_code`
  76 times in 22 wordings, `team_sk` 49 in 13, `season_api_year` 31 in 9. Replace the repetition
  with dbt-native `{% docs %}` blocks referenced by `{{ doc() }}`, so each concept has ONE
  definition that is fixed in one place.
refs: >
  CPO ruling 2026-08-20, recorded in escalations.log: reuse mechanism is "Docs blocks" — dbt-native,
  explicitly NOT the third-party dbt-osmosis, so no new dependency enters the pipeline.
  `engineering_standards.md` §2 (rewritten in MR1) states the rule this implements: "A column
  documented in more than one model gets ONE docs block, referenced from each."

impact_map: >
  Documentation-only, but touching many files. New `.md` files under `dbt_project/models/docs/`
  (dbt resolves docs blocks from `model-paths`, and there is no `docs-paths` override in
  `dbt_project.yml`), plus `description:` edits across the model and seed YAML. No column, no
  `tests:` block, no seed CSV row, no model SQL, no config — zero warehouse blast radius.

  The real risk is not breakage, it is MEANING LOSS: replacing a bespoke description with a shared
  block silently changes what a column claims. `dbt parse` catches an unresolvable `doc()` but
  cannot catch a block that is merely wrong for one of its 76 call sites. Mitigation is the
  reconciliation recorded below, done by reading every distinct variant first.

  MEASURED before starting (`yaml.safe_load` over all `dbt_project/**/*.yml`):
    league_code 76 refs / 22 distinct · team_sk 49/13 · season_api_year 31/9 · season_sk 25/9 ·
    raw_ingested_at 25/3 · player_sk 23/5 · league_sk 15/7 · fixture_sk 15/3.

scope_paths:
  - dbt_project/models/docs/*.md
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/*/*.yml
  - dbt_project/models/4_intermediate/*/*/*.yml
  - dbt_project/models/5_marts/*/*.yml
  - dbt_project/seeds/schema.yml
  - .claude/task/contract.md
  - .claude/task/escalations.log

decisions_taken: >
  Reuse mechanism and the six-MR plan: CPO, escalations.log 2026-08-20. This MR implements MR2 of
  that plan and takes no new product decision.

  TWO ENGINEERING CALLS MADE HERE, both forced by what the variants actually say. Neither is a §10
  decision; both are recorded because they deviate from the plan's "8 columns, 8 blocks" shorthand:

  1. `league_code` needs TWO blocks, not one. The 22 variants carry two INCOMPATIBLE meanings.
     On most models it is the competition a row belongs to. On the transfer models it is ingest
     provenance — which tracked league's pull surfaced the row — and the existing text explicitly
     warns it is "NOT a semantic partition … don't filter affiliation by it expecting
     completeness". Collapsing those into one block would manufacture exactly the kind of false
     claim MR1 just removed. Two blocks: `league_code` and `league_code_ingest_provenance`.

  2. The blocks must NOT call it a "partition key". That phrase appears 16 times in
     `shared.yml` alone, and it is false: `grep -rn "partition_by\|cluster_by" dbt_project/models/
     dbt_project/dbt_project.yml` returns ZERO hits. `CLAUDE.md` states this directly and adds that
     the misconception "has misled cost work". Writing a shared block that repeats it would fix the
     duplication while entrenching the error 76 times over. This is not MR3 cleanup smuggled in
     early — it is the unavoidable content of the block being written now.

decisions_reserved:
  - Role qualifiers stay per-model and are NOT flattened into the blocks: "for the event's team",
    "the primary actor … nullable: VAR decisions may not carry one", "the UPCOMING fixture's
    competition", "must be a DOMESTIC LEAGUE in the registry". Where one exists, the description
    composes — `"{{ doc('team_sk') }} The event's team."` — rather than losing the qualifier.
  - The wider cleanup of the files these edits touch (bloat, rulings, dates) is MR3/MR4. This MR
    changes only the `description:` values of the eight named columns.
  - Whether more columns get blocks later. Eight is the plan's list, chosen by repetition count.

acceptance_criteria:
  - Each of the eight columns has exactly one shared definition; `league_code` has two, per the
    reconciliation above.
  - No docs block contains the phrase "partition key", or any claim about which models read a
    column, or any date/ruling/issue-ref/emoji.
  - Every per-model role qualifier present before this MR is still present after it, either in the
    block or composed alongside the `doc()` reference.
  - The transfer models' `league_code` resolves to the provenance block, never the ordinary one.
  - `.venv/Scripts/dbt.exe parse` resolves every `doc()` reference.
  - `python -m pytest tests/ -q` green.

done_when:
  - Blocks created under `dbt_project/models/docs/`; all eight columns' references updated.
  - A re-run of the distinct-description count shows one definition per concept, not 22.
  - Committed; MR opened by the post-commit hook.

amendments:
  - none
