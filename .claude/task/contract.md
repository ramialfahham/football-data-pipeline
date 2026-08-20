# Task contract — MR3 of the description-drift programme

objective: >
  Clean the `description:` fields in `dbt_project/models/5_marts/shared/shared.yml` and
  `dbt_project/seeds/schema.yml` against the standard written in MR1
  (`dbt_project/docs/engineering_standards.md` §2). Every description states what the data MEANS
  to someone who has never seen our code: business meaning, grain, where it comes from or how it
  is calculated, and known limits. Decision history, issue refs, dates and downstream-consumer
  claims come out. No SQL logic, no test, no column, no model behaviour changes — this is prose.

refs: >
  Authority: `.claude/task/escalations.log`, 2026-08-20 entry (the CPO's diagnosis, the audit's
  numbers, the definition of a good description, the three rulings, the six-MR split and its
  ordering constraints). Plan file: `C:\Users\Rami\.claude\plans\jazzy-greeting-teacup.md`.
  Standard: `dbt_project/docs/engineering_standards.md` §2, written in MR1 (`!82`).
  Shared docs blocks to reference rather than restate: `dbt_project/models/docs/shared_columns.md`,
  written in MR2 (`!83`). Branched from main `d8c6635`; no open MRs at start.

impact_map: >
  PROSE ONLY, and that is the whole blast radius. `description:` is metadata dbt carries into the
  manifest; nothing reads it today (`persist_docs` absent, `dbt docs generate` runs nowhere —
  which is the root cause the programme exists to fix, and MR6's job). No `tests:`, `config:`,
  `meta:`, `columns:` list, model, macro or seed CSV is touched, so the compiled SQL and the built
  tables are byte-identical before and after.

  Verified by construction rather than asserted: the diff on the two YAML files is confined to
  `description:` values and the SQL files' opening `{# ... #}` doc comments. `dbt parse` must
  still succeed (it resolves the `{{ doc() }}` references MR2 added), and `dbt ls` must return the
  same model set.

  THE ONE REAL RISK is a rewrite that states something FALSE — the exact defect the programme
  exists to fix. Mitigated by reading the model's SQL before rewriting its description, not by
  paraphrasing the old text.

  Downstream of MR3: MR6 turns on `persist_docs`, and BigQuery hard-rejects a column description
  over 1,024 characters. Nine descriptions in these two files exceed it today. Clearing them here
  is a precondition for MR6, not a nicety.

scope_paths:
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/seeds/schema.yml
  - dbt_project/models/5_marts/shared/mart_roster.sql
  - dbt_project/models/5_marts/shared/mart_standings.sql
  - dbt_project/models/5_marts/shared/mart_team_fixtures.sql
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

decisions_taken: >
  CPO, in chat 2026-08-20, approving "the whole plan" — all six MRs. MR3's contents are fixed by
  the six-MR split recorded in `escalations.log`: `shared.yml` + `seeds/schema.yml`.

  CPO, in chat this session (AskUserQuestion, "Fix them in MR3"): the three surviving lowercase
  "partition key" claims in `mart_roster.sql`, `mart_standings.sql` and `mart_team_fixtures.sql`
  join `scope_paths` and are fixed HERE rather than left. Same false claim as `shared.yml`, same
  directory, and MR4's scope does not reach them.

  ⚠ READ THAT RULING FROM `escalations.log`, where it is RULING 0 of this branch's entry. It
  authorises files beyond the plan's MR3 row, and this contract is overwritten by the next task, so
  recording it only here would have destroyed it on merge — the same defect class the whole
  programme is about. scope-auditor FAILed round 1 on exactly that and was right; the log entry was
  written in response.

decisions_reserved:
  - The gate that makes this stick is MR5, not this MR. Nothing here is enforced by a check yet;
    that ordering is deliberate (gate green on day one, the `check_copy_gate.py` precedent).
  - `persist_docs` and `dbt docs generate` are MR6. Not touched here.
  - `core.yml`, `base.yml`, `int_momentum.yml` are MR4. Not touched here.
  - Any open question displaced out of a description goes to a GitLab issue as an issue, never
    into another description. Filing it is in scope; deciding it is not.
  - Rulings that already exist in `escalations.log` are simply deleted from the description.
    Only rulings that exist NOWHERE ELSE are rescued into it. Checked ruling by ruling, not
    assumed: the #69 country-naming rulings and the #54 ordering rulings ARE logged and are
    therefore deleted outright; four others are not and are rescued.

done_when:
  - Every description in both files satisfies §2: business meaning, grain where applicable, source
    or formula, known limits. No downstream-consumer claim survives in either file.
  - No description carries an issue ref (`#N`, `GAP-N`, `!N`), an ISO date, a CPO ruling, an
    "UPDATED"/"CORRECTED"/"an earlier version said", or a severity emoji.
  - Zero descriptions in either file exceed 600 characters, and therefore zero exceed BigQuery's
    1,024 (nine do today).
  - The four false "partition key" claims are gone — `shared.yml:1143` plus the three SQL headers.
  - Repeated shared columns reference MR2's docs blocks rather than restating them.
  - `.venv/Scripts/dbt.exe parse` succeeds and `dbt ls` returns the same model set as on main.
  - `python -m pytest tests/` is green.
  - The five offline gates pass, read from their OUTPUT and not their exit code (#904).
  - Handover updated in the SAME commit as the code it describes.

amendments:
  - none
