# Task contract — MR4 of the description-drift programme

objective: >
  Clean the `description:` fields in `dbt_project/models/3_core/core.yml`,
  `dbt_project/models/2_base/api_football/base.yml` and
  `dbt_project/models/4_intermediate/shared/int_momentum.yml` against the standard in
  `dbt_project/docs/engineering_standards.md` §2. Same method as MR3: every description states
  what the data MEANS to someone who has never seen our code — business meaning, grain, where it
  comes from or how it is calculated, known limits. Decision history, dates, issue refs and
  downstream-consumer claims come out. No SQL logic, no test, no column, no model behaviour
  changes — this is prose.

refs: >
  Authority: `.claude/task/escalations.log`, 2026-08-20 entries. The first holds the CPO's
  diagnosis, the audit numbers, the definition of a good description, the three rulings and the
  six-MR split; the second is MR3's, whose method this repeats. Plan file:
  `C:\Users\Rami\.claude\plans\jazzy-greeting-teacup.md`. Standard:
  `dbt_project/docs/engineering_standards.md` §2 (MR1, `!82`). Shared docs blocks to reference
  rather than restate: `dbt_project/models/docs/shared_columns.md` (MR2, `!83`).
  MR3 merged as `!85`; branched from main `2d59320`, no open MRs at start.

impact_map: >
  PROSE ONLY, same blast radius as MR3 and verified the same way. `description:` is metadata dbt
  carries into the manifest; nothing reads it today (`persist_docs` absent, `dbt docs generate`
  runs nowhere — the root cause MR6 fixes). No `tests:`, `config:`, `meta:`, `columns:` list,
  model, macro or seed is touched, so compiled SQL and built tables are identical before and
  after.

  Proved rather than asserted, reusing MR3's check: parse each file at HEAD and in the working
  tree, strip every `description`, and diff the rest. Any change to a test, config, column or
  model name shows up. That check is itself verified to detect a real structural change, so it is
  not vacuous.

  THE ONE REAL RISK is a rewrite that states something FALSE — the defect the programme exists to
  fix, and one that got through in MR3 until a reviewer caught it (`mart_standings` zones).
  Mitigated by reading the model's SQL before rewriting its description, never by paraphrasing
  the old prose. Where a rewrite would make a vague old phrase into a specific claim, the claim
  must be checked against the code or not made.

  MR4 is the last content MR before the gate. After it, `check_description_hygiene.py` (MR5) must
  be green on day one, and no description anywhere may exceed 1,024 characters or MR6's
  `persist_docs` breaks the nightly build.

scope_paths:
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

decisions_taken: >
  CPO, in chat 2026-08-20, approving "the whole plan" — all six MRs. MR4's contents are fixed by
  the six-MR split recorded in `escalations.log`: `core.yml`, `base.yml`, `int_momentum.yml`.
  No scope widening is sought here. MR3 needed one and it was recorded as RULING 0 of its
  escalations entry; if MR4 turns out to need one, it is asked for and logged the same way rather
  than taken.

decisions_reserved:
  - The gate is MR5, not this MR. Nothing here is enforced by a check yet; that ordering is
    deliberate (gate green on day one, the `check_copy_gate.py` precedent).
  - `persist_docs` and `dbt docs generate` are MR6. Not touched here.
  - Rulings already recorded elsewhere are deleted from the description, not copied. Only a ruling
    that exists NOWHERE ELSE is rescued into `escalations.log`.
    ⚠ "ELSEWHERE" IS NOT ONLY `escalations.log`. A model's own SQL header carries its "why" by
    `engineering_standards.md` §1.2, and MR4 edits no `.sql` file, so a ruling written there
    survives this MR untouched. scope-auditor FAILed round 1 having searched only the log and
    concluded two rulings were destroyed; both are intact in `base_apif__teams_global.sql:1-10`.
    One of them had no home outside that comment and IS now rescued into the log; the other was
    already there as the 2026-08-19 team-name entries.
  - An open question displaced out of a description goes to a GitLab issue. Filing it is in
    scope; deciding it is not.
  - Nothing outside these three files is edited. The surviving "partition key" instances in five
    docs and in `.claude/hooks/dbt_layer_gate.py` are GitLab #79 and need `protected_override`.

done_when:
  - Every description in the three files satisfies §2: business meaning, grain where applicable,
    source or formula, known limits. No downstream-consumer claim survives.
  - No description carries an issue ref (`#N`, `GAP-N`, `!N`), an ISO date, a CPO ruling, an
    "UPDATED"/"CORRECTED"/"an earlier version said", or a severity emoji.
  - Zero descriptions exceed 600 characters (17 do today; the worst is 2,441).
  - Repeated shared columns reference MR2's docs blocks rather than restating them.
  - `dbt parse` succeeds and `dbt ls` returns the same model set as main.
  - `python -m pytest tests/` is green at the 829/1 baseline.
  - The five offline gates pass, read from their OUTPUT and not their exit code (#904).
  - The prose-only proof runs clean over all three files.
  - Handover updated in the SAME commit as the code it describes.

amendments:
  - none
