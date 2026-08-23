# Task contract — #82 MR2: declare the columns that exist but are written down nowhere

objective: >
  Close the half of #82 that no yml-based check can see. 979 columns exist in BigQuery across core,
  intermediate and marts and appear in no `.yml` at all, so `check_description_hygiene.py` has never
  been able to look at them. MR2 writes their NAMES down, with no descriptions, so the real surface
  becomes visible and MR3 can wire shared definitions into it.

  The names are added by a script that only ever appends. It never edits, reorders or reformats a
  line that is already there, and that is provable rather than claimed: its diff must contain zero
  deleted lines.

refs: >
  GitLab #82. Authority for the programme: `.claude/task/escalations.log`, the 2026-08-21
  `feat/description-coverage-objects` entry (four CPO rulings). Approved programme plan:
  `C:\Users\Rami\.claude\plans\cozy-orbiting-quail.md`, MR2. Approved plan for THIS MR, which is
  also the CPO's approval of the script as a new mechanism:
  `C:\Users\Rami\.claude\plans\serialized-enchanting-frost.md`.
  Standard: `dbt_project/docs/engineering_standards.md` §2. Branched from main `6df934f`, clean
  tree, no open MRs.

scope_paths:
  - scripts/declare_missing_columns.py
  - tests/test_declare_missing_columns.py
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/4_intermediate/shared/int_team_profile.yml
  - dbt_project/models/4_intermediate/shared/team/int_team_market_value.yml
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/5_marts/shared/shared.yml
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

# The 14 yml paths are listed one by one rather than globbed, deliberately. `dbt_project/models/**`
# would also cover 1_staging and 2_base, which the CPO ruled OUT of coverage scope on 2026-08-21
# ("core, intermediate and marts -> business meaning starts in core downstream"). A glob would let
# an accidental staging edit through the gate that is supposed to catch exactly that.

impact_map: >
  writers: NONE. No SQL changes, so no model computes anything differently. The diff is 14 yml files
    plus one new script and its tests. `git diff --stat` at commit time is the evidence, and the
    append-only proof below is stronger than a writer list: zero deleted lines means no existing
    declaration moved.

  downstream: NO lineage change. A column declaration does not create a dependency — `depends_on` is
    built from `ref()`/`source()` in the SQL, and no SQL is touched. Verified by comparing the
    parsed manifest before and after: the node set and every node's `depends_on` must be identical,
    which is a `done_when` step below rather than an assertion here.

  layer_rules: `check_layer_contract.py` polices per-competition staging subdirectories and the
    staging/base materialisation policy. This MR creates no model, no directory and no
    materialisation config, so nothing it checks moves. Run repo-wide as a `done_when` step.

  deploy_order: none. There is no DDL migration and nothing is sequenced around the nightly. A yml
    column entry takes effect the next time dbt builds the model, and the effect is the persist_docs
    one traced below.

  blast_radius: ONE real effect, traced to the adapter code and then MEASURED rather than reasoned
    about. `dbt/adapters/bigquery/impl.py:578` does
    `bq_column_dict["description"] = column_config.get("description")`, so a column that is DECLARED
    with no `description:` key resolves to None and BLANKS whatever BigQuery holds, while a column
    declared NOWHERE is left alone entirely. Declaring 979 bare names therefore carries a real risk
    of clearing existing text.
    MEASURED against production on 2026-08-23, from `INFORMATION_SCHEMA.COLUMN_FIELD_PATHS` across
    the `core`, `intermediate` and `marts` datasets:
      - columns holding a description in BigQuery today: 100
      - of the 979 this MR newly declares, ones holding a description today: **0**
      - sanity floor, so the zero above cannot be a key mismatch silently proving nothing:
        descriptions held on columns ALREADY declared: 100, i.e. all 100 are accounted for.
    So nothing is cleared. The same code path sets `policyTags` to an empty list on a declared
    column; `grep -rn "policy_tags\|policyTags" dbt_project/ scripts/` returns zero hits and no
    Data Catalog taxonomy is configured, so there are none to clear.
    ⚠ RAISED, NOT FIXED, and filed as GitLab #86: the column half of `persist_docs` only partly
    works today. All 66 relation descriptions are in BigQuery; only 100 of 458 column descriptions
    are (0 of 134 on views, 0 of 20 on incremental models, 58 of 304 on plain tables, and those 58
    sit in 13 `int_*` models). It does not block this MR, which writes no descriptions, but it
    matters to MR4, which writes ~249.

decisions_taken: >
  CPO, 2026-08-23, approving `serialized-enchanting-frost.md`, which states the ask in its own
  section: build `scripts/declare_missing_columns.py` and KEEP it in the repo. Recorded as the
  option approved and nothing more — the reasoning offered for it is the writer's, per the
  2026-08-21 lesson that reasoning wrapped around an answer hardens into a ruling never given.

  CPO, 2026-08-21, "every column, no exception" — no exemption list, so all 979 are declared.
  CPO, 2026-08-21, "thin fillers should not happen" — which is WHY this MR writes no descriptions at
  all. A name with no text is an honest empty slot; a name with invented text is the filler the
  ruling bans, and it would also be far harder to find and replace in MR4.

  THRESHOLD DECLARATION — NEW MECHANISM. `scripts/declare_missing_columns.py` is a new mechanism: a
  script that mutates 14 tracked files in bulk. It is declared here because no routing row can find
  a threshold crossing, and `cto-reviewer` is not gate-required on `scripts/**`. Its authority is
  the CPO approval quoted above.
  THRESHOLD DECLARATION — RECURRING COST: NONE. The script is run by hand. It adds no CI job, no
  schedule, no scheduled query and no new dependency; it uses only the standard library and PyYAML,
  which `requirements.txt` already pins for the existing gates.

decisions_reserved:
  - WHAT each of the 979 columns MEANS is not decided here and no text is written for any of them.
    That is MR3 (wire the shared definitions that already exist) and MR4 (author the ~249 that do
    not). Declaring a name is deliberately the smallest step that makes the gap visible.
  - COLUMN ORDER inside a yml now diverges from the physical column order for any model that
    already had entries, because new names are appended after the existing ones. This is forced by
    the append-only constraint rather than chosen: reordering to match the database would mean
    rewriting lines that are already there, which is the one thing the constraint forbids. Raised
    so a reader does not mistake it for carelessness.
  - GitLab #86, the persist_docs column gap, is RAISED and not chased. See `impact_map`.
  - GitLab #85, the outside bot commenting on merge requests, is filed and carries a visibility
    decision that is the CPO's. Unrelated to this MR, recorded because it was found in the same
    session.
  - The five extra columns over the approved plan's number (979 here, 974 there) are
    `int_team__market_value_latest`'s, which MR1 brought into a yml at object level but not at
    column level. Stated rather than silently absorbed; it needs no decision.

done_when:
  - The script adds all 979 missing names across 14 files and 40 models, and the count is MEASURED
    from the regenerated files, never predicted.
  - `git diff --numstat` over the 14 yml files shows **0 deleted lines**. This is the append-only
    proof and it is the acceptance test for the whole MR.
  - The parsed manifest before and after has an identical node set and identical `depends_on` for
    every node, so the lineage claim in `impact_map` is shown rather than asserted.
  - Re-running the coverage measurement reports undeclared columns **979 -> 0**.
  - A second run of the script reports that it found nothing to add and exits non-zero, so it can
    never report success while matching nothing (handover trap 2).
  - The script refuses a partial catalogue: pointed at one that does not cover every in-scope model
    it aborts and writes nothing. SEEN, using the stale dev catalogue that is actually on this
    machine, not a synthetic one.
  - Every new test is SEEN RED before it is trusted (#904): break the invariant, watch that specific
    test fail, restore. A passing test proves nothing.
  - `dbt parse` clean. `check_description_hygiene.py` and `check_layer_contract.py` green repo-wide.
  - `python -m pytest tests/` back at its measured baseline of 906 passed / 1 skipped, plus the new
    tests.
  - The five offline gates pass, read from their OUTPUT and not their exit code.
  - Handover updated in the SAME commit as the code.

amendments: (none)
